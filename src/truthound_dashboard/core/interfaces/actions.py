"""Action interfaces for checkpoint-based validation pipelines.

Actions are executed after validation completes. They can store results,
send notifications, or integrate with external systems.

This module defines abstract interfaces for actions that are loosely
coupled from truthound's checkpoint.actions module.

Supported action types:
- Storage: Store validation results to filesystem, S3, GCS
- Notifications: Slack, Email, Teams, Discord, Telegram, PagerDuty
- Webhook: Call any HTTP endpoint
- Custom: Execute Python callbacks or shell commands
- DataDocs: Generate HTML/Markdown documentation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    from truthound_dashboard.core.interfaces.checkpoint import CheckpointResult


class NotifyCondition(str, Enum):
    """Conditions under which actions are triggered.

    Maps to truthound's notify_on parameter for actions.
    """

    ALWAYS = "always"  # Every run
    SUCCESS = "success"  # Validation passed
    FAILURE = "failure"  # Validation failed
    ERROR = "error"  # System error occurred
    FAILURE_OR_ERROR = "failure_or_error"  # Failure or error
    NOT_SUCCESS = "not_success"  # Any non-success status
    WARNING = "warning"  # Warning status


class ActionStatus(str, Enum):
    """Status of an action execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"  # Skipped due to notify_on condition
    COMPENSATED = "compensated"  # Rolled back (for transactional actions)


@dataclass
class ActionConfig:
    """Base configuration for all actions.

    Attributes:
        name: Action name for identification.
        notify_on: When to execute this action.
        enabled: Whether this action is enabled.
        timeout_seconds: Maximum execution time.
        retry_count: Number of retries on failure.
        retry_delay_seconds: Delay between retries.
        metadata: Additional metadata for the action.
    """

    name: str = ""
    notify_on: NotifyCondition = NotifyCondition.FAILURE
    enabled: bool = True
    timeout_seconds: int = 30
    retry_count: int = 0
    retry_delay_seconds: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "notify_on": self.notify_on.value,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionConfig":
        """Create from dictionary."""
        notify_on = data.get("notify_on", "failure")
        if isinstance(notify_on, str):
            notify_on = NotifyCondition(notify_on)
        return cls(
            name=data.get("name", ""),
            notify_on=notify_on,
            enabled=data.get("enabled", True),
            timeout_seconds=data.get("timeout_seconds", 30),
            retry_count=data.get("retry_count", 0),
            retry_delay_seconds=data.get("retry_delay_seconds", 5),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ActionResult:
    """Result of an action execution.

    Attributes:
        action_name: Name of the action.
        action_type: Type of action (notification, storage, etc.).
        status: Execution status.
        message: Human-readable message.
        started_at: When execution started.
        completed_at: When execution completed.
        duration_ms: Execution duration in milliseconds.
        details: Additional result details.
        error: Error message if failed.
    """

    action_name: str
    action_type: str
    status: ActionStatus
    message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_name": self.action_name,
            "action_type": self.action_type,
            "status": self.status.value,
            "message": self.message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "details": self.details,
            "error": self.error,
        }


@dataclass
class ActionContext:
    """Context passed to action execution.

    Contains all information needed for an action to execute,
    including the checkpoint result and environment variables.

    Attributes:
        checkpoint_result: The validation result.
        run_id: Unique run identifier.
        checkpoint_name: Name of the checkpoint.
        tags: Tags from the checkpoint.
        metadata: Additional metadata.
        environment: Environment variables (may contain secrets).
    """

    checkpoint_result: "CheckpointResult"
    run_id: str
    checkpoint_name: str
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class ActionProtocol(Protocol):
    """Protocol for synchronous action implementations.

    Actions are executed after validation completes. Each action
    must implement the execute method.

    Example:
        class SlackNotification:
            def execute(self, context: ActionContext) -> ActionResult:
                # Send Slack message
                return ActionResult(
                    action_name="slack",
                    action_type="notification",
                    status=ActionStatus.SUCCESS,
                )
    """

    @property
    def name(self) -> str:
        """Get action name."""
        ...

    @property
    def action_type(self) -> str:
        """Get action type (notification, storage, webhook, custom)."""
        ...

    @property
    def config(self) -> ActionConfig:
        """Get action configuration."""
        ...

    def should_execute(self, context: ActionContext) -> bool:
        """Check if action should execute based on notify_on condition.

        Args:
            context: Execution context with checkpoint result.

        Returns:
            True if action should execute.
        """
        ...

    def execute(self, context: ActionContext) -> ActionResult:
        """Execute the action synchronously.

        Args:
            context: Execution context.

        Returns:
            Action result.
        """
        ...


@runtime_checkable
class AsyncActionProtocol(Protocol):
    """Protocol for asynchronous action implementations.

    For high-throughput scenarios, use async actions that don't
    block the event loop.

    Example:
        class AsyncSlackNotification:
            async def execute_async(self, context: ActionContext) -> ActionResult:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json=payload)
                return ActionResult(...)
    """

    @property
    def name(self) -> str:
        """Get action name."""
        ...

    @property
    def action_type(self) -> str:
        """Get action type."""
        ...

    @property
    def config(self) -> ActionConfig:
        """Get action configuration."""
        ...

    def should_execute(self, context: ActionContext) -> bool:
        """Check if action should execute."""
        ...

    async def execute_async(self, context: ActionContext) -> ActionResult:
        """Execute the action asynchronously.

        Args:
            context: Execution context.

        Returns:
            Action result.
        """
        ...


class CompensatableActionProtocol(Protocol):
    """Protocol for actions that support rollback (compensation).

    Compensatable actions can be rolled back if a subsequent action
    fails, supporting the Saga pattern for distributed transactions.

    Example:
        class DatabaseUpdateAction:
            def execute(self, context):
                self.backup_id = create_backup()
                update_database(context.checkpoint_result)
                return ActionResult(status=ActionStatus.SUCCESS)

            def compensate(self, context, execute_result):
                restore_from_backup(self.backup_id)
                return ActionResult(status=ActionStatus.COMPENSATED)
    """

    def execute(self, context: ActionContext) -> ActionResult:
        """Execute the forward action."""
        ...

    def compensate(
        self, context: ActionContext, execute_result: ActionResult
    ) -> ActionResult:
        """Compensate (rollback) the action.

        Args:
            context: Original execution context.
            execute_result: Result from the execute() call.

        Returns:
            Compensation result.
        """
        ...


class BaseAction(ABC):
    """Abstract base class for actions.

    Provides common functionality for all actions including
    notify_on condition checking and configuration management.

    Subclasses must implement:
    - action_type property
    - _do_execute method
    """

    def __init__(self, config: ActionConfig | dict[str, Any] | None = None) -> None:
        """Initialize action.

        Args:
            config: Action configuration or dict.
        """
        if config is None:
            self._config = ActionConfig()
        elif isinstance(config, dict):
            self._config = ActionConfig.from_dict(config)
        else:
            self._config = config

    @property
    def name(self) -> str:
        """Get action name."""
        return self._config.name or self.__class__.__name__

    @property
    @abstractmethod
    def action_type(self) -> str:
        """Get action type."""
        ...

    @property
    def config(self) -> ActionConfig:
        """Get action configuration."""
        return self._config

    def should_execute(self, context: ActionContext) -> bool:
        """Check if action should execute based on notify_on condition.

        Args:
            context: Execution context.

        Returns:
            True if action should execute.
        """
        if not self._config.enabled:
            return False

        result = context.checkpoint_result
        condition = self._config.notify_on

        if condition == NotifyCondition.ALWAYS:
            return True
        elif condition == NotifyCondition.SUCCESS:
            return result.status.value == "success"
        elif condition == NotifyCondition.FAILURE:
            return result.status.value == "failure"
        elif condition == NotifyCondition.ERROR:
            return result.status.value == "error"
        elif condition == NotifyCondition.FAILURE_OR_ERROR:
            return result.status.value in ("failure", "error")
        elif condition == NotifyCondition.NOT_SUCCESS:
            return result.status.value != "success"
        elif condition == NotifyCondition.WARNING:
            return result.status.value == "warning"

        return True

    def execute(self, context: ActionContext) -> ActionResult:
        """Execute the action.

        Args:
            context: Execution context.

        Returns:
            Action result.
        """
        if not self.should_execute(context):
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SKIPPED,
                message=f"Skipped due to notify_on={self._config.notify_on.value}",
            )

        started_at = datetime.now()
        try:
            result = self._do_execute(context)
            completed_at = datetime.now()
            result.started_at = started_at
            result.completed_at = completed_at
            result.duration_ms = (completed_at - started_at).total_seconds() * 1000
            return result
        except Exception as e:
            completed_at = datetime.now()
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Action failed: {str(e)}",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=(completed_at - started_at).total_seconds() * 1000,
                error=str(e),
            )

    @abstractmethod
    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Perform the actual action execution.

        Subclasses must implement this method.

        Args:
            context: Execution context.

        Returns:
            Action result.
        """
        ...


class AsyncBaseAction(ABC):
    """Abstract base class for async actions.

    Similar to BaseAction but for asynchronous execution.
    """

    def __init__(self, config: ActionConfig | dict[str, Any] | None = None) -> None:
        """Initialize action."""
        if config is None:
            self._config = ActionConfig()
        elif isinstance(config, dict):
            self._config = ActionConfig.from_dict(config)
        else:
            self._config = config

    @property
    def name(self) -> str:
        """Get action name."""
        return self._config.name or self.__class__.__name__

    @property
    @abstractmethod
    def action_type(self) -> str:
        """Get action type."""
        ...

    @property
    def config(self) -> ActionConfig:
        """Get action configuration."""
        return self._config

    def should_execute(self, context: ActionContext) -> bool:
        """Check if action should execute."""
        if not self._config.enabled:
            return False

        result = context.checkpoint_result
        condition = self._config.notify_on

        if condition == NotifyCondition.ALWAYS:
            return True
        elif condition == NotifyCondition.SUCCESS:
            return result.status.value == "success"
        elif condition == NotifyCondition.FAILURE:
            return result.status.value == "failure"
        elif condition == NotifyCondition.ERROR:
            return result.status.value == "error"
        elif condition == NotifyCondition.FAILURE_OR_ERROR:
            return result.status.value in ("failure", "error")
        elif condition == NotifyCondition.NOT_SUCCESS:
            return result.status.value != "success"

        return True

    async def execute_async(self, context: ActionContext) -> ActionResult:
        """Execute the action asynchronously."""
        if not self.should_execute(context):
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SKIPPED,
                message=f"Skipped due to notify_on={self._config.notify_on.value}",
            )

        started_at = datetime.now()
        try:
            result = await self._do_execute_async(context)
            completed_at = datetime.now()
            result.started_at = started_at
            result.completed_at = completed_at
            result.duration_ms = (completed_at - started_at).total_seconds() * 1000
            return result
        except Exception as e:
            completed_at = datetime.now()
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Action failed: {str(e)}",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=(completed_at - started_at).total_seconds() * 1000,
                error=str(e),
            )

    @abstractmethod
    async def _do_execute_async(self, context: ActionContext) -> ActionResult:
        """Perform the actual async action execution."""
        ...


# =============================================================================
# Action Registry
# =============================================================================


class ActionRegistry:
    """Registry for action types.

    Allows registering and retrieving action implementations by name.
    Supports both built-in and custom action types.

    Example:
        registry = ActionRegistry()
        registry.register("slack", SlackNotificationAction)
        registry.register("email", EmailNotificationAction)

        action = registry.create("slack", config={"webhook_url": "..."})
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._actions: dict[str, type[BaseAction | AsyncBaseAction]] = {}
        self._factories: dict[str, Callable[..., BaseAction | AsyncBaseAction]] = {}

    def register(
        self,
        name: str,
        action_class: type[BaseAction | AsyncBaseAction],
    ) -> None:
        """Register an action class.

        Args:
            name: Action type name.
            action_class: Action class to register.
        """
        self._actions[name] = action_class

    def register_factory(
        self,
        name: str,
        factory: Callable[..., BaseAction | AsyncBaseAction],
    ) -> None:
        """Register an action factory function.

        Args:
            name: Action type name.
            factory: Factory function that creates actions.
        """
        self._factories[name] = factory

    def create(
        self,
        name: str,
        config: ActionConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> BaseAction | AsyncBaseAction:
        """Create an action instance.

        Args:
            name: Action type name.
            config: Action configuration.
            **kwargs: Additional arguments for the action.

        Returns:
            Action instance.

        Raises:
            KeyError: If action type is not registered.
        """
        if name in self._factories:
            return self._factories[name](config=config, **kwargs)

        if name in self._actions:
            return self._actions[name](config=config, **kwargs)

        raise KeyError(f"Action type not found: {name}")

    def list_actions(self) -> list[str]:
        """List all registered action types.

        Returns:
            List of action type names.
        """
        return list(set(self._actions.keys()) | set(self._factories.keys()))

    def has_action(self, name: str) -> bool:
        """Check if an action type is registered.

        Args:
            name: Action type name.

        Returns:
            True if action type is registered.
        """
        return name in self._actions or name in self._factories


# Global action registry
_action_registry: ActionRegistry | None = None


def get_action_registry() -> ActionRegistry:
    """Get the global action registry.

    Returns:
        Global ActionRegistry instance.
    """
    global _action_registry
    if _action_registry is None:
        _action_registry = ActionRegistry()
    return _action_registry


def register_action(name: str) -> Callable[[type], type]:
    """Decorator to register an action class.

    Example:
        @register_action("my_custom")
        class MyCustomAction(BaseAction):
            ...
    """

    def decorator(cls: type) -> type:
        get_action_registry().register(name, cls)
        return cls

    return decorator
