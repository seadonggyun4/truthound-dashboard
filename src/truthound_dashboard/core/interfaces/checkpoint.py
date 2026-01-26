"""Checkpoint interfaces for validation pipeline orchestration.

A Checkpoint represents a complete data validation pipeline that
combines data sources, validators, actions, triggers, and routing.

This module defines abstract interfaces for checkpoints that are
loosely coupled from truthound's checkpoint module.

Checkpoint features:
- Data source binding
- Validator configuration
- Action orchestration
- Trigger management
- Result routing
- Run history tracking
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    from truthound_dashboard.core.interfaces.actions import (
        ActionConfig,
        ActionContext,
        ActionResult,
    )
    from truthound_dashboard.core.interfaces.routing import Route, RouteContext, Router
    from truthound_dashboard.core.interfaces.triggers import TriggerConfig, TriggerResult


class CheckpointStatus(str, Enum):
    """Status of a checkpoint run."""

    PENDING = "pending"  # Not yet started
    RUNNING = "running"  # Currently executing
    SUCCESS = "success"  # Validation passed
    FAILURE = "failure"  # Validation failed (issues found)
    ERROR = "error"  # System error occurred
    WARNING = "warning"  # Passed with warnings
    SKIPPED = "skipped"  # Skipped (e.g., no data)
    TIMEOUT = "timeout"  # Execution timed out


@dataclass
class CheckpointConfig:
    """Configuration for a checkpoint.

    Attributes:
        name: Checkpoint name for identification.
        description: Human-readable description.
        source_id: ID of the data source to validate.
        source_name: Name of the data source.
        validators: List of validator names to run.
        validator_config: Per-validator configuration.
        schema_path: Path to schema file for validation.
        auto_schema: Auto-learn schema for validation.
        tags: Tags for categorization and routing.
        enabled: Whether this checkpoint is enabled.
        timeout_seconds: Maximum execution time.
        retry_on_error: Retry on system errors.
        retry_count: Number of retries.
        metadata: Additional metadata.
        success_threshold: Minimum pass rate for success.
        warning_threshold: Pass rate below which is warning.
    """

    name: str = ""
    description: str = ""
    source_id: str | None = None
    source_name: str | None = None
    validators: list[str] = field(default_factory=list)
    validator_config: dict[str, dict[str, Any]] = field(default_factory=dict)
    schema_path: str | None = None
    auto_schema: bool = False
    tags: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout_seconds: int = 300
    retry_on_error: bool = False
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    success_threshold: float = 1.0  # 100% pass = success
    warning_threshold: float = 0.9  # 90% pass = warning

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "validators": self.validators,
            "validator_config": self.validator_config,
            "schema_path": self.schema_path,
            "auto_schema": self.auto_schema,
            "tags": self.tags,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
            "retry_on_error": self.retry_on_error,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
            "success_threshold": self.success_threshold,
            "warning_threshold": self.warning_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointConfig":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            source_id=data.get("source_id"),
            source_name=data.get("source_name"),
            validators=data.get("validators", []),
            validator_config=data.get("validator_config", {}),
            schema_path=data.get("schema_path"),
            auto_schema=data.get("auto_schema", False),
            tags=data.get("tags", {}),
            enabled=data.get("enabled", True),
            timeout_seconds=data.get("timeout_seconds", 300),
            retry_on_error=data.get("retry_on_error", False),
            retry_count=data.get("retry_count", 0),
            metadata=data.get("metadata", {}),
            success_threshold=data.get("success_threshold", 1.0),
            warning_threshold=data.get("warning_threshold", 0.9),
        )


@dataclass
class CheckpointResult:
    """Result of a checkpoint run.

    Attributes:
        checkpoint_name: Name of the checkpoint.
        run_id: Unique run identifier.
        status: Execution status.
        started_at: When execution started.
        completed_at: When execution completed.
        duration_ms: Execution duration in milliseconds.
        source_name: Data source name.
        row_count: Number of rows validated.
        column_count: Number of columns.
        issue_count: Total number of issues.
        critical_count: Number of critical issues.
        high_count: Number of high severity issues.
        medium_count: Number of medium severity issues.
        low_count: Number of low severity issues.
        has_critical: Whether critical issues were found.
        has_high: Whether high severity issues were found.
        issues: List of validation issues.
        action_results: Results from action execution.
        trigger_context: Context from the trigger (if any).
        error_message: Error message if status is ERROR.
        metadata: Additional result metadata.
    """

    checkpoint_name: str
    run_id: str
    status: CheckpointStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    source_name: str = ""
    row_count: int = 0
    column_count: int = 0
    issue_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    has_critical: bool = False
    has_high: bool = False
    issues: list[dict[str, Any]] = field(default_factory=list)
    action_results: list["ActionResult"] = field(default_factory=list)
    trigger_context: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_name": self.checkpoint_name,
            "run_id": self.run_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "source_name": self.source_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "issue_count": self.issue_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "has_critical": self.has_critical,
            "has_high": self.has_high,
            "issues": self.issues,
            "action_results": [r.to_dict() for r in self.action_results],
            "trigger_context": self.trigger_context,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_check_result(
        cls,
        check_result: Any,
        checkpoint_name: str,
        run_id: str,
        config: CheckpointConfig,
    ) -> "CheckpointResult":
        """Create from a check result (validation result).

        Args:
            check_result: Validation result from backend.
            checkpoint_name: Checkpoint name.
            run_id: Run identifier.
            config: Checkpoint configuration.

        Returns:
            CheckpointResult instance.
        """
        # Determine status based on result
        passed = getattr(check_result, "passed", True)
        has_critical = getattr(check_result, "has_critical", False)
        has_high = getattr(check_result, "has_high", False)
        issue_count = getattr(check_result, "total_issues", 0)

        if has_critical or has_high:
            status = CheckpointStatus.FAILURE
        elif not passed:
            # Check if warning threshold
            row_count = getattr(check_result, "row_count", 0)
            if row_count > 0:
                pass_rate = 1 - (issue_count / row_count)
                if pass_rate >= config.warning_threshold:
                    status = CheckpointStatus.WARNING
                else:
                    status = CheckpointStatus.FAILURE
            else:
                status = CheckpointStatus.FAILURE
        else:
            status = CheckpointStatus.SUCCESS

        # Extract issue counts
        critical_count = getattr(check_result, "critical_issues", 0)
        high_count = getattr(check_result, "high_issues", 0)
        medium_count = getattr(check_result, "medium_issues", 0)
        low_count = getattr(check_result, "low_issues", 0)

        # Get issues list
        issues = []
        if hasattr(check_result, "issues"):
            issues = check_result.issues
            if not isinstance(issues, list):
                issues = list(issues)

        return cls(
            checkpoint_name=checkpoint_name,
            run_id=run_id,
            status=status,
            source_name=getattr(check_result, "source", ""),
            row_count=getattr(check_result, "row_count", 0),
            column_count=getattr(check_result, "column_count", 0),
            issue_count=issue_count,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            has_critical=has_critical,
            has_high=has_high,
            issues=issues,
        )


@runtime_checkable
class CheckpointProtocol(Protocol):
    """Protocol for checkpoint implementations.

    A checkpoint orchestrates the complete validation pipeline:
    1. Load data from source
    2. Run validators
    3. Evaluate routing rules
    4. Execute matched actions
    5. Record results

    Example:
        checkpoint = Checkpoint(
            config=CheckpointConfig(
                name="daily_orders",
                source_id="orders_db",
                validators=["null", "uniqueness", "range"],
            ),
            actions=[slack_action, email_action],
            routes=[critical_route, daily_summary_route],
        )

        result = await checkpoint.run()
    """

    @property
    def name(self) -> str:
        """Get checkpoint name."""
        ...

    @property
    def config(self) -> CheckpointConfig:
        """Get checkpoint configuration."""
        ...

    @property
    def actions(self) -> list[Any]:
        """Get configured actions."""
        ...

    @property
    def triggers(self) -> list[Any]:
        """Get configured triggers."""
        ...

    @property
    def router(self) -> "Router | None":
        """Get the router for action routing."""
        ...

    async def run(
        self,
        trigger_context: dict[str, Any] | None = None,
    ) -> CheckpointResult:
        """Run the checkpoint.

        Args:
            trigger_context: Optional context from the trigger.

        Returns:
            Checkpoint result.
        """
        ...

    def add_action(self, action: Any) -> None:
        """Add an action to the checkpoint.

        Args:
            action: Action to add.
        """
        ...

    def remove_action(self, name: str) -> bool:
        """Remove an action by name.

        Args:
            name: Action name.

        Returns:
            True if action was removed.
        """
        ...

    def add_trigger(self, trigger: Any) -> None:
        """Add a trigger to the checkpoint.

        Args:
            trigger: Trigger to add.
        """
        ...

    def set_router(self, router: "Router") -> None:
        """Set the router for action routing.

        Args:
            router: Router to use.
        """
        ...


class CheckpointRunnerProtocol(Protocol):
    """Protocol for checkpoint runners.

    Runners execute checkpoints, handling lifecycle, error recovery,
    and result persistence.

    Example:
        runner = CheckpointRunner()
        runner.register(checkpoint)

        # Run by name
        result = await runner.run("daily_orders")

        # Run all enabled checkpoints
        results = await runner.run_all()
    """

    def register(self, checkpoint: CheckpointProtocol) -> None:
        """Register a checkpoint.

        Args:
            checkpoint: Checkpoint to register.
        """
        ...

    def unregister(self, name: str) -> bool:
        """Unregister a checkpoint by name.

        Args:
            name: Checkpoint name.

        Returns:
            True if checkpoint was unregistered.
        """
        ...

    def get(self, name: str) -> CheckpointProtocol | None:
        """Get a checkpoint by name.

        Args:
            name: Checkpoint name.

        Returns:
            Checkpoint or None if not found.
        """
        ...

    def list_checkpoints(self) -> list[str]:
        """List all registered checkpoint names.

        Returns:
            List of checkpoint names.
        """
        ...

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
        ...

    async def run_all(
        self,
        parallel: bool = False,
        max_workers: int = 4,
    ) -> list[CheckpointResult]:
        """Run all enabled checkpoints.

        Args:
            parallel: Run checkpoints in parallel.
            max_workers: Max parallel workers.

        Returns:
            List of checkpoint results.
        """
        ...


# =============================================================================
# Checkpoint Registry
# =============================================================================


class CheckpointRegistry:
    """Registry for checkpoint types and instances.

    Manages checkpoint registration, lifecycle, and access.

    Example:
        registry = CheckpointRegistry()
        registry.register(checkpoint)

        result = await registry.run("daily_orders")
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._checkpoints: dict[str, CheckpointProtocol] = {}
        self._factories: dict[str, Callable[..., CheckpointProtocol]] = {}

    def register(self, checkpoint: CheckpointProtocol) -> None:
        """Register a checkpoint instance.

        Args:
            checkpoint: Checkpoint to register.
        """
        self._checkpoints[checkpoint.name] = checkpoint

    def register_factory(
        self,
        name: str,
        factory: Callable[..., CheckpointProtocol],
    ) -> None:
        """Register a checkpoint factory.

        Args:
            name: Checkpoint type name.
            factory: Factory function.
        """
        self._factories[name] = factory

    def unregister(self, name: str) -> bool:
        """Unregister a checkpoint by name.

        Args:
            name: Checkpoint name.

        Returns:
            True if checkpoint was unregistered.
        """
        if name in self._checkpoints:
            del self._checkpoints[name]
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

    def create(
        self,
        type_name: str,
        config: CheckpointConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> CheckpointProtocol:
        """Create a checkpoint using a factory.

        Args:
            type_name: Checkpoint type name.
            config: Checkpoint configuration.
            **kwargs: Additional arguments.

        Returns:
            Checkpoint instance.

        Raises:
            KeyError: If factory not found.
        """
        if type_name not in self._factories:
            raise KeyError(f"Checkpoint factory not found: {type_name}")
        return self._factories[type_name](config=config, **kwargs)

    def list_checkpoints(self) -> list[str]:
        """List all registered checkpoint names.

        Returns:
            List of checkpoint names.
        """
        return list(self._checkpoints.keys())

    def list_factories(self) -> list[str]:
        """List all registered factory names.

        Returns:
            List of factory names.
        """
        return list(self._factories.keys())

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
        max_workers: int = 4,
    ) -> list[CheckpointResult]:
        """Run all enabled checkpoints.

        Args:
            parallel: Run in parallel.
            max_workers: Max parallel workers.

        Returns:
            List of checkpoint results.
        """
        import asyncio

        results: list[CheckpointResult] = []
        enabled_checkpoints = [
            cp for cp in self._checkpoints.values()
            if cp.config.enabled
        ]

        if not enabled_checkpoints:
            return results

        if parallel:
            # Run in parallel with semaphore
            semaphore = asyncio.Semaphore(max_workers)

            async def run_with_semaphore(cp: CheckpointProtocol) -> CheckpointResult:
                async with semaphore:
                    return await cp.run()

            results = await asyncio.gather(
                *[run_with_semaphore(cp) for cp in enabled_checkpoints]
            )
        else:
            # Run sequentially
            for checkpoint in enabled_checkpoints:
                result = await checkpoint.run()
                results.append(result)

        return results


# Global checkpoint registry
_checkpoint_registry: CheckpointRegistry | None = None


def get_checkpoint_registry() -> CheckpointRegistry:
    """Get the global checkpoint registry.

    Returns:
        Global CheckpointRegistry instance.
    """
    global _checkpoint_registry
    if _checkpoint_registry is None:
        _checkpoint_registry = CheckpointRegistry()
    return _checkpoint_registry


def register_checkpoint(name: str | None = None) -> Callable[[type], type]:
    """Decorator to register a checkpoint factory.

    Example:
        @register_checkpoint("custom")
        class CustomCheckpoint:
            ...
    """

    def decorator(cls: type) -> type:
        factory_name = name or cls.__name__
        get_checkpoint_registry().register_factory(factory_name, cls)
        return cls

    return decorator
