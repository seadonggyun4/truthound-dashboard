"""Trigger interfaces for checkpoint-based validation pipelines.

Triggers initiate validation runs. They can be time-based, event-based,
or manually invoked.

This module defines abstract interfaces for triggers that are loosely
coupled from truthound's checkpoint.triggers module.

Supported trigger types:
- Schedule/Cron: Time-based triggers
- FileWatch: File system event triggers
- Webhook: HTTP webhook triggers
- Event: Pub/sub event triggers
- Manual: Manual invocation
- Pipeline: Integration with data pipelines (Airflow, Dagster, etc.)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass


class TriggerStatus(str, Enum):
    """Status of a trigger execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    DISABLED = "disabled"


class TriggerType(str, Enum):
    """Types of triggers."""

    CRON = "cron"
    SCHEDULE = "schedule"
    FILE_WATCH = "file_watch"
    WEBHOOK = "webhook"
    EVENT = "event"
    MANUAL = "manual"
    PIPELINE = "pipeline"
    DATA_ARRIVAL = "data_arrival"


@dataclass
class TriggerConfig:
    """Base configuration for all triggers.

    Attributes:
        name: Trigger name for identification.
        trigger_type: Type of trigger.
        enabled: Whether this trigger is enabled.
        description: Human-readable description.
        metadata: Additional metadata.
        checkpoint_id: ID of checkpoint to run.
        checkpoint_name: Name of checkpoint to run.
    """

    name: str = ""
    trigger_type: TriggerType = TriggerType.MANUAL
    enabled: bool = True
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    checkpoint_id: str | None = None
    checkpoint_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "trigger_type": self.trigger_type.value,
            "enabled": self.enabled,
            "description": self.description,
            "metadata": self.metadata,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_name": self.checkpoint_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TriggerConfig":
        """Create from dictionary."""
        trigger_type = data.get("trigger_type", "manual")
        if isinstance(trigger_type, str):
            trigger_type = TriggerType(trigger_type)
        return cls(
            name=data.get("name", ""),
            trigger_type=trigger_type,
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            checkpoint_id=data.get("checkpoint_id"),
            checkpoint_name=data.get("checkpoint_name"),
        )


@dataclass
class CronTriggerConfig(TriggerConfig):
    """Configuration for cron-based triggers.

    Attributes:
        cron_expression: Cron expression (e.g., "0 * * * *" for hourly).
        timezone: Timezone for cron evaluation.
        start_date: Earliest date to start running.
        end_date: Latest date to stop running.
        max_runs: Maximum number of runs (None for unlimited).
        catchup: Whether to catch up missed runs.
    """

    cron_expression: str = "0 * * * *"  # Hourly
    timezone: str = "UTC"
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_runs: int | None = None
    catchup: bool = False

    def __post_init__(self):
        self.trigger_type = TriggerType.CRON

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "max_runs": self.max_runs,
            "catchup": self.catchup,
        })
        return data


@dataclass
class FileWatchTriggerConfig(TriggerConfig):
    """Configuration for file watch triggers.

    Attributes:
        path: Path to watch (can be glob pattern).
        events: File events to watch for.
        debounce_seconds: Debounce time to avoid rapid triggers.
        recursive: Whether to watch subdirectories.
        include_patterns: Patterns to include.
        exclude_patterns: Patterns to exclude.
    """

    path: str = ""
    events: list[str] = field(default_factory=lambda: ["created", "modified"])
    debounce_seconds: float = 5.0
    recursive: bool = False
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.trigger_type = TriggerType.FILE_WATCH

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "path": self.path,
            "events": self.events,
            "debounce_seconds": self.debounce_seconds,
            "recursive": self.recursive,
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
        })
        return data


@dataclass
class WebhookTriggerConfig(TriggerConfig):
    """Configuration for webhook triggers.

    Attributes:
        path: Webhook endpoint path.
        methods: HTTP methods to accept.
        require_auth: Whether authentication is required.
        auth_header: Header name for authentication.
        secret: Secret for HMAC validation.
        payload_schema: JSON schema for payload validation.
    """

    path: str = "/triggers/webhook"
    methods: list[str] = field(default_factory=lambda: ["POST"])
    require_auth: bool = False
    auth_header: str = "X-Trigger-Secret"
    secret: str = ""
    payload_schema: dict[str, Any] | None = None

    def __post_init__(self):
        self.trigger_type = TriggerType.WEBHOOK

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "path": self.path,
            "methods": self.methods,
            "require_auth": self.require_auth,
            "auth_header": self.auth_header,
            # Don't expose secret
            "payload_schema": self.payload_schema,
        })
        return data


@dataclass
class EventTriggerConfig(TriggerConfig):
    """Configuration for event-based triggers (pub/sub).

    Attributes:
        event_type: Type of event to listen for.
        event_source: Source of events.
        filter_expression: Expression to filter events.
    """

    event_type: str = ""
    event_source: str = ""
    filter_expression: str = ""

    def __post_init__(self):
        self.trigger_type = TriggerType.EVENT

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "event_type": self.event_type,
            "event_source": self.event_source,
            "filter_expression": self.filter_expression,
        })
        return data


@dataclass
class DataArrivalTriggerConfig(TriggerConfig):
    """Configuration for data arrival triggers.

    Triggers when new data arrives at a source.

    Attributes:
        source_id: Data source to monitor.
        check_interval_seconds: How often to check for new data.
        min_rows: Minimum rows to trigger.
        max_wait_seconds: Maximum time to wait for data.
        watermark_column: Column to track data arrival.
    """

    source_id: str = ""
    check_interval_seconds: int = 60
    min_rows: int = 1
    max_wait_seconds: int = 3600
    watermark_column: str | None = None

    def __post_init__(self):
        self.trigger_type = TriggerType.DATA_ARRIVAL

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "source_id": self.source_id,
            "check_interval_seconds": self.check_interval_seconds,
            "min_rows": self.min_rows,
            "max_wait_seconds": self.max_wait_seconds,
            "watermark_column": self.watermark_column,
        })
        return data


@dataclass
class TriggerResult:
    """Result of a trigger execution.

    Attributes:
        trigger_name: Name of the trigger.
        trigger_type: Type of trigger.
        status: Execution status.
        message: Human-readable message.
        triggered_at: When the trigger fired.
        run_id: ID of the initiated run (if any).
        context: Additional context from the trigger.
        error: Error message if failed.
    """

    trigger_name: str
    trigger_type: str
    status: TriggerStatus
    message: str = ""
    triggered_at: datetime | None = None
    run_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trigger_name": self.trigger_name,
            "trigger_type": self.trigger_type,
            "status": self.status.value,
            "message": self.message,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "run_id": self.run_id,
            "context": self.context,
            "error": self.error,
        }


@runtime_checkable
class TriggerProtocol(Protocol):
    """Protocol for trigger implementations.

    Triggers monitor for conditions and initiate checkpoint runs
    when conditions are met.

    Example:
        class CronTrigger:
            def is_due(self) -> bool:
                return cron_is_due(self.expression)

            def trigger(self) -> TriggerResult:
                if self.is_due():
                    run_id = run_checkpoint(self.checkpoint_id)
                    return TriggerResult(status=TriggerStatus.SUCCESS, run_id=run_id)
    """

    @property
    def name(self) -> str:
        """Get trigger name."""
        ...

    @property
    def trigger_type(self) -> str:
        """Get trigger type."""
        ...

    @property
    def config(self) -> TriggerConfig:
        """Get trigger configuration."""
        ...

    def is_enabled(self) -> bool:
        """Check if trigger is enabled."""
        ...

    def is_due(self) -> bool:
        """Check if trigger should fire.

        Returns:
            True if trigger conditions are met.
        """
        ...

    def trigger(self, context: dict[str, Any] | None = None) -> TriggerResult:
        """Fire the trigger and initiate a checkpoint run.

        Args:
            context: Optional context to pass to the checkpoint.

        Returns:
            Trigger result.
        """
        ...

    def get_next_run_time(self) -> datetime | None:
        """Get the next scheduled run time.

        Returns:
            Next run time or None if not applicable.
        """
        ...


class BaseTrigger(ABC):
    """Abstract base class for triggers.

    Provides common functionality for all triggers.
    Subclasses must implement is_due and _do_trigger methods.
    """

    def __init__(self, config: TriggerConfig | dict[str, Any] | None = None) -> None:
        """Initialize trigger.

        Args:
            config: Trigger configuration or dict.
        """
        if config is None:
            self._config = TriggerConfig()
        elif isinstance(config, dict):
            self._config = TriggerConfig.from_dict(config)
        else:
            self._config = config

        self._last_triggered: datetime | None = None
        self._trigger_count: int = 0

    @property
    def name(self) -> str:
        """Get trigger name."""
        return self._config.name or self.__class__.__name__

    @property
    @abstractmethod
    def trigger_type(self) -> str:
        """Get trigger type."""
        ...

    @property
    def config(self) -> TriggerConfig:
        """Get trigger configuration."""
        return self._config

    def is_enabled(self) -> bool:
        """Check if trigger is enabled."""
        return self._config.enabled

    @abstractmethod
    def is_due(self) -> bool:
        """Check if trigger should fire."""
        ...

    def trigger(self, context: dict[str, Any] | None = None) -> TriggerResult:
        """Fire the trigger.

        Args:
            context: Optional context.

        Returns:
            Trigger result.
        """
        if not self.is_enabled():
            return TriggerResult(
                trigger_name=self.name,
                trigger_type=self.trigger_type,
                status=TriggerStatus.DISABLED,
                message="Trigger is disabled",
                triggered_at=datetime.now(),
            )

        if not self.is_due():
            return TriggerResult(
                trigger_name=self.name,
                trigger_type=self.trigger_type,
                status=TriggerStatus.SKIPPED,
                message="Trigger conditions not met",
                triggered_at=datetime.now(),
            )

        try:
            result = self._do_trigger(context)
            self._last_triggered = datetime.now()
            self._trigger_count += 1
            return result
        except Exception as e:
            return TriggerResult(
                trigger_name=self.name,
                trigger_type=self.trigger_type,
                status=TriggerStatus.FAILURE,
                message=f"Trigger failed: {str(e)}",
                triggered_at=datetime.now(),
                error=str(e),
            )

    @abstractmethod
    def _do_trigger(self, context: dict[str, Any] | None) -> TriggerResult:
        """Perform the actual trigger execution.

        Subclasses must implement this method.

        Args:
            context: Optional context.

        Returns:
            Trigger result.
        """
        ...

    def get_next_run_time(self) -> datetime | None:
        """Get the next scheduled run time.

        Override in subclasses for scheduled triggers.

        Returns:
            Next run time or None.
        """
        return None


# =============================================================================
# Trigger Registry
# =============================================================================


class TriggerRegistry:
    """Registry for trigger types.

    Allows registering and retrieving trigger implementations by name.

    Example:
        registry = TriggerRegistry()
        registry.register("cron", CronTrigger)
        registry.register("file_watch", FileWatchTrigger)

        trigger = registry.create("cron", config={"cron_expression": "0 * * * *"})
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._triggers: dict[str, type[BaseTrigger]] = {}
        self._factories: dict[str, Callable[..., BaseTrigger]] = {}

    def register(self, name: str, trigger_class: type[BaseTrigger]) -> None:
        """Register a trigger class.

        Args:
            name: Trigger type name.
            trigger_class: Trigger class to register.
        """
        self._triggers[name] = trigger_class

    def register_factory(
        self,
        name: str,
        factory: Callable[..., BaseTrigger],
    ) -> None:
        """Register a trigger factory function.

        Args:
            name: Trigger type name.
            factory: Factory function that creates triggers.
        """
        self._factories[name] = factory

    def create(
        self,
        name: str,
        config: TriggerConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> BaseTrigger:
        """Create a trigger instance.

        Args:
            name: Trigger type name.
            config: Trigger configuration.
            **kwargs: Additional arguments for the trigger.

        Returns:
            Trigger instance.

        Raises:
            KeyError: If trigger type is not registered.
        """
        if name in self._factories:
            return self._factories[name](config=config, **kwargs)

        if name in self._triggers:
            return self._triggers[name](config=config, **kwargs)

        raise KeyError(f"Trigger type not found: {name}")

    def list_triggers(self) -> list[str]:
        """List all registered trigger types.

        Returns:
            List of trigger type names.
        """
        return list(set(self._triggers.keys()) | set(self._factories.keys()))

    def has_trigger(self, name: str) -> bool:
        """Check if a trigger type is registered.

        Args:
            name: Trigger type name.

        Returns:
            True if trigger type is registered.
        """
        return name in self._triggers or name in self._factories


# Global trigger registry
_trigger_registry: TriggerRegistry | None = None


def get_trigger_registry() -> TriggerRegistry:
    """Get the global trigger registry.

    Returns:
        Global TriggerRegistry instance.
    """
    global _trigger_registry
    if _trigger_registry is None:
        _trigger_registry = TriggerRegistry()
    return _trigger_registry


def register_trigger(name: str) -> Callable[[type], type]:
    """Decorator to register a trigger class.

    Example:
        @register_trigger("my_custom")
        class MyCustomTrigger(BaseTrigger):
            ...
    """

    def decorator(cls: type) -> type:
        get_trigger_registry().register(name, cls)
        return cls

    return decorator
