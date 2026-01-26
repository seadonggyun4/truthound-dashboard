"""Checkpoint runner for managing and executing checkpoints.

Provides the CheckpointRunner class for registering, managing,
and executing multiple checkpoints.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from truthound_dashboard.core.interfaces.checkpoint import (
    CheckpointProtocol,
    CheckpointResult,
    CheckpointRunnerProtocol,
    CheckpointStatus,
)

logger = logging.getLogger(__name__)


class CheckpointRunner(CheckpointRunnerProtocol):
    """Runner for managing and executing checkpoints.

    Provides a central registry for checkpoints and methods for
    running them individually or in batch.

    Example:
        runner = CheckpointRunner()

        # Register checkpoints
        runner.register(orders_checkpoint)
        runner.register(customers_checkpoint)

        # Run a specific checkpoint
        result = await runner.run("daily_orders")

        # Run all enabled checkpoints
        results = await runner.run_all(parallel=True)
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize runner.

        Args:
            max_workers: Max parallel workers for run_all.
        """
        self._checkpoints: dict[str, CheckpointProtocol] = {}
        self._max_workers = max_workers

    def register(self, checkpoint: CheckpointProtocol) -> None:
        """Register a checkpoint.

        Args:
            checkpoint: Checkpoint to register.
        """
        self._checkpoints[checkpoint.name] = checkpoint
        logger.info(f"Registered checkpoint: {checkpoint.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a checkpoint by name.

        Args:
            name: Checkpoint name.

        Returns:
            True if checkpoint was unregistered.
        """
        if name in self._checkpoints:
            del self._checkpoints[name]
            logger.info(f"Unregistered checkpoint: {name}")
            return True
        return False

    def get(self, name: str) -> CheckpointProtocol | None:
        """Get a checkpoint by name.

        Args:
            name: Checkpoint name.

        Returns:
            Checkpoint or None if not found.
        """
        return self._checkpoints.get(name)

    def list_checkpoints(self) -> list[str]:
        """List all registered checkpoint names.

        Returns:
            List of checkpoint names.
        """
        return list(self._checkpoints.keys())

    def get_all(self) -> list[CheckpointProtocol]:
        """Get all registered checkpoints.

        Returns:
            List of checkpoints.
        """
        return list(self._checkpoints.values())

    async def run(
        self,
        name: str,
        trigger_context: dict[str, Any] | None = None,
    ) -> CheckpointResult:
        """Run a checkpoint by name.

        Args:
            name: Checkpoint name.
            trigger_context: Optional trigger context.

        Returns:
            Checkpoint result.

        Raises:
            KeyError: If checkpoint not found.
        """
        checkpoint = self.get(name)
        if checkpoint is None:
            raise KeyError(f"Checkpoint not found: {name}")

        return await checkpoint.run(trigger_context=trigger_context)

    async def run_all(
        self,
        parallel: bool = False,
        max_workers: int | None = None,
        filter_enabled: bool = True,
    ) -> list[CheckpointResult]:
        """Run all registered checkpoints.

        Args:
            parallel: Run in parallel.
            max_workers: Max parallel workers (uses instance default if None).
            filter_enabled: Only run enabled checkpoints.

        Returns:
            List of checkpoint results.
        """
        max_workers = max_workers or self._max_workers

        # Filter checkpoints
        checkpoints = self.get_all()
        if filter_enabled:
            checkpoints = [cp for cp in checkpoints if cp.config.enabled]

        if not checkpoints:
            logger.info("No checkpoints to run")
            return []

        logger.info(f"Running {len(checkpoints)} checkpoints (parallel={parallel})")

        if parallel:
            return await self._run_parallel(checkpoints, max_workers)
        else:
            return await self._run_sequential(checkpoints)

    async def _run_sequential(
        self, checkpoints: list[CheckpointProtocol]
    ) -> list[CheckpointResult]:
        """Run checkpoints sequentially.

        Args:
            checkpoints: Checkpoints to run.

        Returns:
            List of results.
        """
        results: list[CheckpointResult] = []
        for checkpoint in checkpoints:
            try:
                result = await checkpoint.run()
                results.append(result)
            except Exception as e:
                logger.error(f"Checkpoint failed: {checkpoint.name} error={str(e)}")
                results.append(CheckpointResult(
                    checkpoint_name=checkpoint.name,
                    run_id="",
                    status=CheckpointStatus.ERROR,
                    error_message=str(e),
                ))
        return results

    async def _run_parallel(
        self,
        checkpoints: list[CheckpointProtocol],
        max_workers: int,
    ) -> list[CheckpointResult]:
        """Run checkpoints in parallel with semaphore.

        Args:
            checkpoints: Checkpoints to run.
            max_workers: Max concurrent executions.

        Returns:
            List of results.
        """
        semaphore = asyncio.Semaphore(max_workers)

        async def run_with_semaphore(cp: CheckpointProtocol) -> CheckpointResult:
            async with semaphore:
                try:
                    return await cp.run()
                except Exception as e:
                    logger.error(f"Checkpoint failed: {cp.name} error={str(e)}")
                    return CheckpointResult(
                        checkpoint_name=cp.name,
                        run_id="",
                        status=CheckpointStatus.ERROR,
                        error_message=str(e),
                    )

        results = await asyncio.gather(
            *[run_with_semaphore(cp) for cp in checkpoints]
        )
        return list(results)

    async def run_by_tag(
        self,
        tag_key: str,
        tag_value: str,
        parallel: bool = False,
    ) -> list[CheckpointResult]:
        """Run checkpoints matching a tag.

        Args:
            tag_key: Tag key to match.
            tag_value: Tag value to match.
            parallel: Run in parallel.

        Returns:
            List of checkpoint results.
        """
        checkpoints = [
            cp for cp in self.get_all()
            if cp.config.tags.get(tag_key) == tag_value and cp.config.enabled
        ]

        if not checkpoints:
            logger.info(f"No checkpoints found with tag {tag_key}={tag_value}")
            return []

        if parallel:
            return await self._run_parallel(checkpoints, self._max_workers)
        else:
            return await self._run_sequential(checkpoints)


# Global runner instance
_runner: CheckpointRunner | None = None


def get_checkpoint_runner() -> CheckpointRunner:
    """Get the global checkpoint runner.

    Returns:
        Global CheckpointRunner instance.
    """
    global _runner
    if _runner is None:
        _runner = CheckpointRunner()
    return _runner


def reset_checkpoint_runner() -> None:
    """Reset the global checkpoint runner (for testing)."""
    global _runner
    _runner = None
