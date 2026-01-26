"""Custom action implementations.

Provides flexible action types for custom integrations:
- Callback action: Execute Python callables
- Shell command action: Execute shell commands
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from truthound_dashboard.core.interfaces.actions import (
    ActionConfig,
    ActionContext,
    ActionResult,
    ActionStatus,
    AsyncBaseAction,
    BaseAction,
    NotifyCondition,
    register_action,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Callback Action
# =============================================================================


@dataclass
class CallbackConfig(ActionConfig):
    """Configuration for callback action.

    Attributes:
        callback: Python callable to execute.
        pass_context: Pass full context to callback.
        pass_result_only: Pass only checkpoint result to callback.
    """

    callback: Callable[..., Any] | None = None
    pass_context: bool = True
    pass_result_only: bool = False

    def __post_init__(self):
        self.name = self.name or "callback"


@register_action("callback")
class CallbackAction(BaseAction):
    """Execute a Python callback function.

    Provides maximum flexibility for custom actions by executing
    arbitrary Python callables.

    Example:
        def my_handler(context):
            print(f"Validation completed: {context.checkpoint_result.status}")
            return {"custom_key": "custom_value"}

        action = CallbackAction(callback=my_handler)

    The callback receives the ActionContext and should return:
    - None: Uses default success result
    - dict: Merged into result details
    - ActionResult: Used directly as the result
    """

    def __init__(
        self,
        callback: Callable[..., Any] | None = None,
        notify_on: NotifyCondition = NotifyCondition.ALWAYS,
        config: CallbackConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = CallbackConfig(
                callback=callback,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            callback = config.pop("callback", callback)
            config = CallbackConfig(callback=callback, **config)

        super().__init__(config)
        self._callback_config: CallbackConfig = config
        self._callback = callback or self._callback_config.callback

    @property
    def action_type(self) -> str:
        return "custom"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Execute the callback."""
        if self._callback is None:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message="No callback function provided",
                error="callback is None",
            )

        try:
            # Determine what to pass to callback
            if self._callback_config.pass_result_only:
                callback_result = self._callback(context.checkpoint_result)
            elif self._callback_config.pass_context:
                callback_result = self._callback(context)
            else:
                callback_result = self._callback()

            # Process callback result
            if callback_result is None:
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.SUCCESS,
                    message="Callback executed successfully",
                )
            elif isinstance(callback_result, ActionResult):
                return callback_result
            elif isinstance(callback_result, dict):
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.SUCCESS,
                    message="Callback executed successfully",
                    details=callback_result,
                )
            else:
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.SUCCESS,
                    message="Callback executed successfully",
                    details={"return_value": str(callback_result)},
                )
        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Callback failed: {str(e)}",
                error=str(e),
            )


# =============================================================================
# Async Callback Action
# =============================================================================


@dataclass
class AsyncCallbackConfig(ActionConfig):
    """Configuration for async callback action."""

    callback: Callable[..., Any] | None = None
    pass_context: bool = True

    def __post_init__(self):
        self.name = self.name or "async_callback"


@register_action("async_callback")
class AsyncCallbackAction(AsyncBaseAction):
    """Execute an async Python callback function.

    Similar to CallbackAction but for async/await patterns.

    Example:
        async def my_async_handler(context):
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=data)
            return {"status": "posted"}

        action = AsyncCallbackAction(callback=my_async_handler)
    """

    def __init__(
        self,
        callback: Callable[..., Any] | None = None,
        notify_on: NotifyCondition = NotifyCondition.ALWAYS,
        config: AsyncCallbackConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = AsyncCallbackConfig(
                callback=callback,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            callback = config.pop("callback", callback)
            config = AsyncCallbackConfig(callback=callback, **config)

        super().__init__(config)
        self._callback_config: AsyncCallbackConfig = config
        self._callback = callback or self._callback_config.callback

    @property
    def action_type(self) -> str:
        return "custom"

    async def _do_execute_async(self, context: ActionContext) -> ActionResult:
        """Execute the async callback."""
        if self._callback is None:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message="No callback function provided",
                error="callback is None",
            )

        try:
            if self._callback_config.pass_context:
                callback_result = await self._callback(context)
            else:
                callback_result = await self._callback()

            if callback_result is None:
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.SUCCESS,
                    message="Async callback executed successfully",
                )
            elif isinstance(callback_result, ActionResult):
                return callback_result
            elif isinstance(callback_result, dict):
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.SUCCESS,
                    message="Async callback executed successfully",
                    details=callback_result,
                )
            else:
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.SUCCESS,
                    message="Async callback executed successfully",
                    details={"return_value": str(callback_result)},
                )
        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Async callback failed: {str(e)}",
                error=str(e),
            )


# =============================================================================
# Shell Command Action
# =============================================================================


@dataclass
class ShellCommandConfig(ActionConfig):
    """Configuration for shell command action.

    Attributes:
        command: Shell command to execute.
        shell: Use shell execution.
        cwd: Working directory.
        env: Environment variables.
        capture_output: Capture stdout/stderr.
        check: Raise exception on non-zero exit.
        pass_env_vars: Environment variable names to set from context.
    """

    command: str = ""
    shell: bool = True
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    capture_output: bool = True
    check: bool = False
    pass_env_vars: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.name = self.name or "shell"


@register_action("shell")
class ShellCommandAction(BaseAction):
    """Execute a shell command.

    Runs a shell command after validation completes.
    Can pass validation context as environment variables.

    Example:
        action = ShellCommandAction(
            command="./notify.sh",
            pass_env_vars=["CHECKPOINT_NAME", "STATUS", "ISSUE_COUNT"],
        )

    Available environment variables:
    - TRUTHOUND_CHECKPOINT_NAME
    - TRUTHOUND_RUN_ID
    - TRUTHOUND_STATUS
    - TRUTHOUND_SOURCE_NAME
    - TRUTHOUND_ROW_COUNT
    - TRUTHOUND_ISSUE_COUNT
    - TRUTHOUND_CRITICAL_COUNT
    - TRUTHOUND_HIGH_COUNT
    """

    def __init__(
        self,
        command: str = "",
        notify_on: NotifyCondition = NotifyCondition.ALWAYS,
        config: ShellCommandConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = ShellCommandConfig(
                command=command,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = ShellCommandConfig(**config)

        super().__init__(config)
        self._shell_config: ShellCommandConfig = config

    @property
    def action_type(self) -> str:
        return "custom"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Execute shell command."""
        if not self._shell_config.command:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message="No command provided",
                error="command is empty",
            )

        # Build environment with validation context
        env = {**self._shell_config.env}
        result = context.checkpoint_result

        # Add standard environment variables
        env.update({
            "TRUTHOUND_CHECKPOINT_NAME": result.checkpoint_name,
            "TRUTHOUND_RUN_ID": result.run_id,
            "TRUTHOUND_STATUS": result.status.value,
            "TRUTHOUND_SOURCE_NAME": result.source_name,
            "TRUTHOUND_ROW_COUNT": str(result.row_count),
            "TRUTHOUND_COLUMN_COUNT": str(result.column_count),
            "TRUTHOUND_ISSUE_COUNT": str(result.issue_count),
            "TRUTHOUND_CRITICAL_COUNT": str(result.critical_count),
            "TRUTHOUND_HIGH_COUNT": str(result.high_count),
            "TRUTHOUND_MEDIUM_COUNT": str(result.medium_count),
            "TRUTHOUND_LOW_COUNT": str(result.low_count),
            "TRUTHOUND_HAS_CRITICAL": str(result.has_critical).lower(),
            "TRUTHOUND_HAS_HIGH": str(result.has_high).lower(),
            "TRUTHOUND_DURATION_MS": str(result.duration_ms),
        })

        try:
            proc = subprocess.run(
                self._shell_config.command,
                shell=self._shell_config.shell,
                cwd=self._shell_config.cwd,
                env=env,
                capture_output=self._shell_config.capture_output,
                check=self._shell_config.check,
                timeout=self._config.timeout_seconds,
            )

            details: dict[str, Any] = {
                "command": self._shell_config.command,
                "exit_code": proc.returncode,
            }

            if self._shell_config.capture_output:
                details["stdout"] = proc.stdout.decode("utf-8", errors="replace")
                details["stderr"] = proc.stderr.decode("utf-8", errors="replace")

            if proc.returncode == 0:
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.SUCCESS,
                    message=f"Command executed successfully (exit code: {proc.returncode})",
                    details=details,
                )
            else:
                return ActionResult(
                    action_name=self.name,
                    action_type=self.action_type,
                    status=ActionStatus.FAILURE,
                    message=f"Command failed with exit code: {proc.returncode}",
                    details=details,
                    error=details.get("stderr", ""),
                )
        except subprocess.TimeoutExpired:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Command timed out after {self._config.timeout_seconds}s",
                error="TimeoutExpired",
            )
        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Command failed: {str(e)}",
                error=str(e),
            )
