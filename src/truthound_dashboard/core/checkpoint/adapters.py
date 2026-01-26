"""Adapters for integrating truthound checkpoint API with dashboard abstractions.

Provides adapter classes that bridge between truthound's checkpoint module
and the dashboard's abstraction layer, enabling loose coupling while
supporting the full truthound checkpoint functionality.

Key features supported:
- Checkpoint execution (sync and async)
- Action orchestration (12 action types)
- CI/CD reporter integration (12 platforms)
- Trigger management (cron, schedule, event, file watch)
- Transaction management (saga pattern, idempotency)
- Advanced notifications (routing, deduplication, throttling, escalation)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from truthound_dashboard.core.interfaces.actions import (
    ActionContext,
    ActionResult,
    ActionStatus,
    BaseAction,
)
from truthound_dashboard.core.interfaces.checkpoint import (
    CheckpointConfig,
    CheckpointResult,
    CheckpointStatus,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TruthoundCheckpointAdapter:
    """Adapter for truthound checkpoint API integration.

    This adapter provides a bridge between truthound's native checkpoint
    module and the dashboard's abstraction layer. It allows using truthound
    checkpoints while maintaining the dashboard's loose coupling.

    Features:
    - Convert truthound checkpoint results to dashboard format
    - Map truthound actions to dashboard actions
    - Support truthound's routing and trigger systems
    - Maintain backward compatibility with existing dashboard code

    Example:
        from truthound.checkpoint import Checkpoint as TruthoundCheckpoint

        # Create a truthound checkpoint
        th_checkpoint = TruthoundCheckpoint(
            datasource=source,
            actions=[SlackAction(webhook_url="...")],
        )

        # Wrap with adapter
        adapter = TruthoundCheckpointAdapter(th_checkpoint)

        # Use through dashboard interfaces
        result = await adapter.run()
    """

    def __init__(self, truthound_checkpoint: Any) -> None:
        """Initialize adapter.

        Args:
            truthound_checkpoint: Native truthound Checkpoint instance.
        """
        self._checkpoint = truthound_checkpoint

    @property
    def name(self) -> str:
        """Get checkpoint name."""
        return getattr(self._checkpoint, "name", "unnamed")

    @property
    def config(self) -> CheckpointConfig:
        """Get checkpoint configuration as dashboard format."""
        cp = self._checkpoint

        return CheckpointConfig(
            name=getattr(cp, "name", ""),
            description=getattr(cp, "description", ""),
            source_name=getattr(cp, "datasource_name", ""),
            validators=list(getattr(cp, "validators", [])),
            validator_config=dict(getattr(cp, "validator_config", {})),
            tags=dict(getattr(cp, "tags", {})),
            enabled=getattr(cp, "enabled", True),
            timeout_seconds=getattr(cp, "timeout", 300),
        )

    async def run(
        self,
        trigger_context: dict[str, Any] | None = None,
    ) -> CheckpointResult:
        """Run the truthound checkpoint and convert result.

        Args:
            trigger_context: Optional trigger context.

        Returns:
            Dashboard-format checkpoint result.
        """
        try:
            # Run truthound checkpoint
            th_result = await self._run_truthound()

            # Convert to dashboard format
            return self._convert_result(th_result, trigger_context)

        except Exception as e:
            logger.error(f"Truthound checkpoint failed: {str(e)}")
            return CheckpointResult(
                checkpoint_name=self.name,
                run_id=str(getattr(self._checkpoint, "run_id", "")),
                status=CheckpointStatus.ERROR,
                error_message=str(e),
                trigger_context=trigger_context or {},
            )

    async def _run_truthound(self) -> Any:
        """Run the native truthound checkpoint.

        Returns:
            Truthound checkpoint result.
        """
        import asyncio

        # Check if checkpoint has async run method
        if hasattr(self._checkpoint, "run_async"):
            return await self._checkpoint.run_async()
        elif hasattr(self._checkpoint, "run"):
            # Run sync method in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._checkpoint.run)
        else:
            raise AttributeError("Checkpoint has no run method")

    def _convert_result(
        self,
        th_result: Any,
        trigger_context: dict[str, Any] | None,
    ) -> CheckpointResult:
        """Convert truthound result to dashboard format.

        Args:
            th_result: Truthound checkpoint result.
            trigger_context: Trigger context.

        Returns:
            Dashboard-format result.
        """
        # Extract status
        status_str = getattr(th_result, "status", "error")
        status_map = {
            "success": CheckpointStatus.SUCCESS,
            "failure": CheckpointStatus.FAILURE,
            "error": CheckpointStatus.ERROR,
            "warning": CheckpointStatus.WARNING,
            "pending": CheckpointStatus.PENDING,
            "running": CheckpointStatus.RUNNING,
        }
        status = status_map.get(status_str.lower(), CheckpointStatus.ERROR)

        # Extract validation result
        validation_result = getattr(th_result, "validation_result", None)

        # Build checkpoint result
        result = CheckpointResult(
            checkpoint_name=self.name,
            run_id=str(getattr(th_result, "run_id", "")),
            status=status,
            started_at=getattr(th_result, "started_at", None),
            completed_at=getattr(th_result, "completed_at", None),
            duration_ms=getattr(th_result, "duration_ms", 0.0),
            source_name=getattr(th_result, "source_name", ""),
            trigger_context=trigger_context or {},
        )

        # Extract issue counts from validation result
        if validation_result:
            result.row_count = getattr(validation_result, "row_count", 0)
            result.column_count = getattr(validation_result, "column_count", 0)
            result.issue_count = getattr(validation_result, "total_issues", 0)
            result.critical_count = getattr(validation_result, "critical_issues", 0)
            result.high_count = getattr(validation_result, "high_issues", 0)
            result.medium_count = getattr(validation_result, "medium_issues", 0)
            result.low_count = getattr(validation_result, "low_issues", 0)
            result.has_critical = getattr(validation_result, "has_critical", False)
            result.has_high = getattr(validation_result, "has_high", False)
            result.issues = getattr(validation_result, "issues", [])

        # Convert action results
        th_action_results = getattr(th_result, "action_results", [])
        result.action_results = [
            self._convert_action_result(ar) for ar in th_action_results
        ]

        return result

    def _convert_action_result(self, th_result: Any) -> ActionResult:
        """Convert truthound action result to dashboard format.

        Args:
            th_result: Truthound action result.

        Returns:
            Dashboard-format action result.
        """
        status_str = getattr(th_result, "status", "failure")
        status_map = {
            "success": ActionStatus.SUCCESS,
            "failure": ActionStatus.FAILURE,
            "skipped": ActionStatus.SKIPPED,
            "pending": ActionStatus.PENDING,
            "running": ActionStatus.RUNNING,
        }
        status = status_map.get(status_str.lower(), ActionStatus.FAILURE)

        return ActionResult(
            action_name=getattr(th_result, "action_name", "unknown"),
            action_type=getattr(th_result, "action_type", "unknown"),
            status=status,
            message=getattr(th_result, "message", ""),
            started_at=getattr(th_result, "started_at", None),
            completed_at=getattr(th_result, "completed_at", None),
            duration_ms=getattr(th_result, "duration_ms", 0.0),
            details=getattr(th_result, "details", {}),
            error=getattr(th_result, "error", None),
        )


class TruthoundActionAdapter(BaseAction):
    """Adapter for wrapping truthound actions as dashboard actions.

    Allows using truthound's native action implementations within
    the dashboard's action framework.

    Example:
        from truthound.checkpoint.actions import SlackAction

        th_action = SlackAction(webhook_url="...")
        dashboard_action = TruthoundActionAdapter(th_action)

        # Use in checkpoint
        checkpoint.add_action(dashboard_action)
    """

    def __init__(self, truthound_action: Any) -> None:
        """Initialize adapter.

        Args:
            truthound_action: Native truthound action instance.
        """
        from truthound_dashboard.core.interfaces.actions import ActionConfig

        super().__init__(ActionConfig())
        self._action = truthound_action

    @property
    def name(self) -> str:
        """Get action name."""
        return getattr(self._action, "name", "truthound_action")

    @property
    def action_type(self) -> str:
        """Get action type."""
        return getattr(self._action, "action_type", "external")

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Execute the truthound action.

        Args:
            context: Action context.

        Returns:
            Action result.
        """
        try:
            # Build truthound context if needed
            th_context = self._build_truthound_context(context)

            # Execute truthound action
            if hasattr(self._action, "execute"):
                th_result = self._action.execute(th_context)
            elif hasattr(self._action, "__call__"):
                th_result = self._action(th_context)
            else:
                raise AttributeError("Action has no execute method")

            # Convert result
            return self._convert_result(th_result)

        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Truthound action failed: {str(e)}",
                error=str(e),
            )

    def _build_truthound_context(self, context: ActionContext) -> Any:
        """Build truthound action context from dashboard context.

        Args:
            context: Dashboard action context.

        Returns:
            Truthound-compatible context.
        """
        # Try to import truthound context class
        try:
            from truthound.checkpoint.actions import ActionContext as TruthoundActionContext
            return TruthoundActionContext(
                checkpoint_result=context.checkpoint_result,
                run_id=context.run_id,
                checkpoint_name=context.checkpoint_name,
                tags=context.tags,
                metadata=context.metadata,
            )
        except ImportError:
            # Return a dict-like context
            return {
                "checkpoint_result": context.checkpoint_result,
                "run_id": context.run_id,
                "checkpoint_name": context.checkpoint_name,
                "tags": context.tags,
                "metadata": context.metadata,
            }

    def _convert_result(self, th_result: Any) -> ActionResult:
        """Convert truthound action result.

        Args:
            th_result: Truthound result.

        Returns:
            Dashboard action result.
        """
        if th_result is None:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message="Action completed",
            )

        status_str = getattr(th_result, "status", "success")
        status_map = {
            "success": ActionStatus.SUCCESS,
            "failure": ActionStatus.FAILURE,
            "skipped": ActionStatus.SKIPPED,
        }
        status = status_map.get(status_str.lower(), ActionStatus.SUCCESS)

        return ActionResult(
            action_name=self.name,
            action_type=self.action_type,
            status=status,
            message=getattr(th_result, "message", ""),
            details=getattr(th_result, "details", {}),
            error=getattr(th_result, "error", None),
        )


def create_checkpoint_from_truthound(th_checkpoint: Any) -> TruthoundCheckpointAdapter:
    """Factory function to create a dashboard checkpoint from truthound checkpoint.

    Args:
        th_checkpoint: Truthound checkpoint instance.

    Returns:
        Wrapped checkpoint adapter.
    """
    return TruthoundCheckpointAdapter(th_checkpoint)


def wrap_truthound_action(th_action: Any) -> TruthoundActionAdapter:
    """Factory function to wrap a truthound action for dashboard use.

    Args:
        th_action: Truthound action instance.

    Returns:
        Wrapped action adapter.
    """
    return TruthoundActionAdapter(th_action)


# =============================================================================
# Factory Functions for Truthound Checkpoints
# =============================================================================


def create_truthound_checkpoint(
    name: str,
    data_source: Any,
    validators: list[str] | None = None,
    actions: list[Any] | None = None,
    triggers: list[Any] | None = None,
    **config_options: Any,
) -> TruthoundCheckpointAdapter | None:
    """Create a truthound checkpoint with the new 2.x API.

    This factory function creates a checkpoint using truthound's native
    checkpoint API and wraps it with the dashboard adapter.

    Args:
        name: Checkpoint name.
        data_source: Data source (file path, DataSource, or config dict).
        validators: List of validator names to run.
        actions: List of action instances.
        triggers: List of trigger instances.
        **config_options: Additional checkpoint configuration options.

    Returns:
        TruthoundCheckpointAdapter or None if truthound unavailable.

    Example:
        from truthound.checkpoint.actions import SlackNotification

        checkpoint = create_truthound_checkpoint(
            name="daily_validation",
            data_source="data.csv",
            validators=["null", "duplicate", "range"],
            actions=[
                SlackNotification(
                    webhook_url="https://hooks.slack.com/...",
                    notify_on="failure",
                ),
            ],
        )

        if checkpoint:
            result = await checkpoint.run()
    """
    try:
        from truthound.checkpoint import Checkpoint

        # Create truthound checkpoint
        th_checkpoint = Checkpoint(
            name=name,
            data_source=data_source,
            validators=validators or [],
            actions=actions or [],
            **config_options,
        )

        # Add triggers
        if triggers:
            for trigger in triggers:
                th_checkpoint.add_trigger(trigger)

        # Wrap with adapter
        return TruthoundCheckpointAdapter(th_checkpoint)

    except ImportError:
        logger.warning("truthound.checkpoint not available")
        return None


def create_checkpoint_from_config(
    config: dict[str, Any] | "CheckpointConfig",
) -> TruthoundCheckpointAdapter | None:
    """Create a truthound checkpoint from configuration.

    This factory function creates a checkpoint from a configuration
    dictionary or CheckpointConfig object.

    Args:
        config: Configuration dict or CheckpointConfig.

    Returns:
        TruthoundCheckpointAdapter or None if truthound unavailable.

    Example:
        config = {
            "name": "daily_validation",
            "data_source": "data.csv",
            "validators": ["null", "duplicate"],
            "actions": [
                {
                    "type": "slack",
                    "webhook_url": "https://hooks.slack.com/...",
                    "notify_on": "failure",
                }
            ],
        }
        checkpoint = create_checkpoint_from_config(config)
    """
    try:
        from truthound.checkpoint import Checkpoint, CheckpointConfig as TruthoundConfig

        # Convert to dict if needed
        if isinstance(config, CheckpointConfig):
            config_dict = config.to_dict()
        else:
            config_dict = config

        # Build truthound config
        th_config = TruthoundConfig(
            name=config_dict.get("name", ""),
            data_source=config_dict.get("data_source") or config_dict.get("source_name"),
            validators=config_dict.get("validators", []),
            validator_config=config_dict.get("validator_config", {}),
            schema=config_dict.get("schema_path"),
            auto_schema=config_dict.get("auto_schema", False),
            tags=config_dict.get("tags", {}),
            timeout_seconds=config_dict.get("timeout_seconds", 300),
        )

        # Create checkpoint
        th_checkpoint = Checkpoint(config=th_config)

        # Create actions from config
        actions_config = config_dict.get("actions", [])
        for action_config in actions_config:
            action = _create_action_from_config(action_config)
            if action:
                th_checkpoint.add_action(action)

        # Create triggers from config
        triggers_config = config_dict.get("triggers", [])
        for trigger_config in triggers_config:
            trigger = _create_trigger_from_config(trigger_config)
            if trigger:
                th_checkpoint.add_trigger(trigger)

        return TruthoundCheckpointAdapter(th_checkpoint)

    except ImportError:
        logger.warning("truthound.checkpoint not available")
        return None


def _create_action_from_config(config: dict[str, Any]) -> Any:
    """Create an action from configuration dict.

    Supports all 12 action types from truthound.

    Args:
        config: Action configuration.

    Returns:
        Action instance or None.
    """
    action_type = config.get("type", "").lower()

    try:
        if action_type == "store_result":
            from truthound.checkpoint.actions import StoreValidationResult

            return StoreValidationResult(
                store_path=config.get("store_path", "./results"),
                store_type=config.get("store_type", "file"),
                format=config.get("format", "json"),
                partition_by=config.get("partition_by"),
                retention_days=config.get("retention_days"),
                compress=config.get("compress", False),
            )

        elif action_type == "update_docs":
            from truthound.checkpoint.actions import UpdateDataDocs

            return UpdateDataDocs(
                site_path=config.get("site_path", "./docs"),
                format=config.get("format", "html"),
                include_history=config.get("include_history", True),
            )

        elif action_type == "slack":
            from truthound.checkpoint.actions import SlackNotification

            return SlackNotification(
                webhook_url=config["webhook_url"],
                channel=config.get("channel"),
                notify_on=config.get("notify_on", "failure"),
                include_details=config.get("include_details", True),
            )

        elif action_type == "email":
            from truthound.checkpoint.actions import EmailNotification

            return EmailNotification(
                to=config.get("to", []),
                subject=config.get("subject"),
                notify_on=config.get("notify_on", "failure"),
                smtp_host=config.get("smtp_host"),
                smtp_port=config.get("smtp_port"),
            )

        elif action_type == "webhook":
            from truthound.checkpoint.actions import WebhookAction

            return WebhookAction(
                url=config["url"],
                method=config.get("method", "POST"),
                auth_type=config.get("auth_type", "none"),
                auth_credentials=config.get("auth_credentials"),
                headers=config.get("headers"),
            )

        elif action_type == "pagerduty":
            from truthound.checkpoint.actions import PagerDutyAction

            return PagerDutyAction(
                service_key=config["service_key"],
                notify_on=config.get("notify_on", "failure"),
            )

        elif action_type == "github":
            from truthound.checkpoint.actions import GitHubAction

            return GitHubAction()

        elif action_type == "teams":
            from truthound.checkpoint.actions import TeamsNotification

            return TeamsNotification(
                webhook_url=config["webhook_url"],
                notify_on=config.get("notify_on", "failure"),
            )

        elif action_type == "opsgenie":
            from truthound.checkpoint.actions import OpsGenieAction

            return OpsGenieAction(
                api_key=config["api_key"],
                notify_on=config.get("notify_on", "failure"),
            )

        elif action_type == "discord":
            from truthound.checkpoint.actions import DiscordNotification

            return DiscordNotification(
                webhook_url=config["webhook_url"],
                notify_on=config.get("notify_on", "failure"),
            )

        elif action_type == "telegram":
            from truthound.checkpoint.actions import TelegramNotification

            return TelegramNotification(
                bot_token=config["bot_token"],
                chat_id=config["chat_id"],
                notify_on=config.get("notify_on", "failure"),
            )

        elif action_type == "custom":
            from truthound.checkpoint.actions import CustomAction

            return CustomAction(
                callback=config.get("callback"),
                shell_command=config.get("shell_command"),
            )

        else:
            logger.warning(f"Unknown action type: {action_type}")
            return None

    except (ImportError, KeyError) as e:
        logger.warning(f"Failed to create action {action_type}: {e}")
        return None


def _create_trigger_from_config(config: dict[str, Any]) -> Any:
    """Create a trigger from configuration dict.

    Args:
        config: Trigger configuration.

    Returns:
        Trigger instance or None.
    """
    trigger_type = config.get("type", "").lower()

    try:
        if trigger_type == "schedule":
            from truthound.checkpoint.triggers import ScheduleTrigger

            return ScheduleTrigger(
                interval_hours=config.get("interval_hours"),
                interval_minutes=config.get("interval_minutes"),
                run_on_weekdays=config.get("run_on_weekdays"),
            )

        elif trigger_type == "cron":
            from truthound.checkpoint.triggers import CronTrigger

            return CronTrigger(expression=config["expression"])

        elif trigger_type == "event":
            from truthound.checkpoint.triggers import EventTrigger

            return EventTrigger(
                event_type=config["event_type"],
                event_filter=config.get("event_filter"),
                debounce_seconds=config.get("debounce_seconds"),
            )

        elif trigger_type == "file_watch":
            from truthound.checkpoint.triggers import FileWatchTrigger

            return FileWatchTrigger(
                paths=config.get("paths", []),
                patterns=config.get("patterns", ["*"]),
                recursive=config.get("recursive", False),
            )

        else:
            logger.warning(f"Unknown trigger type: {trigger_type}")
            return None

    except (ImportError, KeyError) as e:
        logger.warning(f"Failed to create trigger {trigger_type}: {e}")
        return None


# =============================================================================
# CI/CD Integration Helpers
# =============================================================================


def get_ci_reporter_for_checkpoint(checkpoint_result: CheckpointResult) -> Any:
    """Get a CI reporter for the checkpoint result.

    Auto-detects the CI environment and returns an appropriate reporter.

    Args:
        checkpoint_result: Checkpoint result to report.

    Returns:
        CI reporter or None if not in CI environment.
    """
    from truthound_dashboard.core.reporters import (
        create_ci_reporter,
        is_ci_environment,
    )

    if not is_ci_environment():
        return None

    return create_ci_reporter()


async def report_checkpoint_to_ci(checkpoint_result: CheckpointResult) -> bool:
    """Report checkpoint result to CI platform.

    This function detects the CI environment and reports the result
    appropriately (e.g., GitHub step summary, annotations, etc.).

    Args:
        checkpoint_result: Result to report.

    Returns:
        True if reported successfully.
    """
    from truthound_dashboard.core.reporters import (
        create_ci_reporter,
        is_ci_environment,
        get_detected_ci_platform,
    )
    from truthound_dashboard.core.reporters.interfaces import ReportData

    if not is_ci_environment():
        return False

    reporter = create_ci_reporter()
    if not reporter:
        return False

    try:
        # Convert checkpoint result to report data
        report_data = ReportData(
            validation_id=checkpoint_result.run_id,
            source_id=checkpoint_result.source_name,
            source_name=checkpoint_result.source_name,
            status=checkpoint_result.status.value,
        )

        # Generate and output report
        output = await reporter.generate(report_data)

        # Print to stdout for CI
        if isinstance(output.content, str):
            print(output.content)
        else:
            print(output.content.decode())

        return True

    except Exception as e:
        logger.error(f"Failed to report to CI: {e}")
        return False


def is_truthound_checkpoint_available() -> bool:
    """Check if truthound checkpoint module is available.

    Returns:
        True if truthound.checkpoint can be imported.
    """
    try:
        from truthound.checkpoint import Checkpoint  # noqa: F401

        return True
    except ImportError:
        return False
