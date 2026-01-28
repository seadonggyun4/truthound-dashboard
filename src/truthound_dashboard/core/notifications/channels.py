"""Notification channel implementations using truthound library.

This module provides channel implementations that wrap truthound's
checkpoint.actions module for notification delivery.

Available channels (from truthound.checkpoint.actions):
- Slack: SlackNotification
- Email: EmailNotification
- Teams: TeamsNotification
- Discord: DiscordNotification
- Telegram: TelegramNotification
- PagerDuty: PagerDutyAction
- Webhook: WebhookAction

Each channel is registered with the ChannelRegistry and delegates
actual notification delivery to the corresponding truthound action.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from truthound.checkpoint.actions import (
    SlackNotification,
    EmailNotification,
    TeamsNotification,
    DiscordNotification,
    TelegramNotification,
    PagerDutyAction,
    OpsGenieAction,
    WebhookAction,
    GitHubAction,
)

from .base import (
    BaseNotificationChannel,
    ChannelRegistry,
    NotificationEvent,
)
from .events import (
    DriftDetectedEvent,
    SchemaChangedEvent,
    ScheduleFailedEvent,
    TestNotificationEvent,
    ValidationFailedEvent,
)

logger = logging.getLogger(__name__)


def _build_checkpoint_result_mock(event: NotificationEvent | None) -> Any:
    """Build a mock CheckpointResult for truthound actions.

    truthound actions expect a CheckpointResult object. We create a
    minimal mock that provides the necessary attributes.
    """
    @dataclass
    class MockStatistics:
        total_issues: int = 0
        critical_issues: int = 0
        high_issues: int = 0
        medium_issues: int = 0
        low_issues: int = 0
        info_issues: int = 0
        pass_rate: float = 100.0

    @dataclass
    class MockValidationResult:
        statistics: MockStatistics
        error: str | None = None

    @dataclass
    class MockCheckpointResult:
        checkpoint_name: str
        run_id: str
        status: str
        data_asset: str
        validation_result: MockValidationResult
        duration_ms: float = 0.0

        def summary(self) -> str:
            return f"{self.checkpoint_name}: {self.status}"

    if event is None:
        return MockCheckpointResult(
            checkpoint_name="test",
            run_id="test-run",
            status="success",
            data_asset="test",
            validation_result=MockValidationResult(statistics=MockStatistics()),
        )

    # Extract data from event
    data = event.data or {}

    if isinstance(event, ValidationFailedEvent):
        return MockCheckpointResult(
            checkpoint_name=event.source_name or "validation",
            run_id=data.get("validation_id", "unknown"),
            status="failure",
            data_asset=event.source_name or "unknown",
            validation_result=MockValidationResult(
                statistics=MockStatistics(
                    total_issues=data.get("total_issues", 0),
                    critical_issues=1 if data.get("has_critical") else 0,
                    high_issues=1 if data.get("has_high") else 0,
                )
            ),
        )
    elif isinstance(event, DriftDetectedEvent):
        return MockCheckpointResult(
            checkpoint_name=f"drift_{event.source_name or 'unknown'}",
            run_id=data.get("comparison_id", "unknown"),
            status="warning",
            data_asset=event.source_name or "unknown",
            validation_result=MockValidationResult(statistics=MockStatistics()),
        )
    elif isinstance(event, ScheduleFailedEvent):
        return MockCheckpointResult(
            checkpoint_name=data.get("schedule_name", "schedule"),
            run_id=data.get("run_id", "unknown"),
            status="error",
            data_asset=event.source_name or "unknown",
            validation_result=MockValidationResult(
                statistics=MockStatistics(),
                error=data.get("error_message"),
            ),
        )
    else:
        return MockCheckpointResult(
            checkpoint_name=event.event_type,
            run_id="dashboard-event",
            status="info",
            data_asset=event.source_name or "unknown",
            validation_result=MockValidationResult(statistics=MockStatistics()),
        )


@ChannelRegistry.register("slack")
class SlackChannel(BaseNotificationChannel):
    """Slack notification channel using truthound.checkpoint.actions.SlackNotification.

    Configuration:
        webhook_url: Slack incoming webhook URL (required)
        channel: Optional channel override
        username: Optional username override
        icon_emoji: Optional emoji icon (e.g., ":robot:")
        mention_on_failure: List of user IDs to mention on failure

    Example config:
        {
            "webhook_url": "https://hooks.slack.com/services/...",
            "username": "Truthound Bot",
            "icon_emoji": ":bar_chart:",
            "channel": "#data-quality"
        }
    """

    channel_type = "slack"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Slack channel configuration schema."""
        return {
            "webhook_url": {
                "type": "string",
                "required": True,
                "description": "Slack incoming webhook URL",
            },
            "channel": {
                "type": "string",
                "required": False,
                "description": "Channel override (e.g., #alerts)",
            },
            "username": {
                "type": "string",
                "required": False,
                "description": "Bot username override",
            },
            "icon_emoji": {
                "type": "string",
                "required": False,
                "description": "Emoji icon (e.g., :robot:)",
            },
            "mention_on_failure": {
                "type": "array",
                "required": False,
                "description": "User IDs to mention on failure",
            },
        }

    def _create_action(self) -> SlackNotification:
        """Create truthound SlackNotification action."""
        return SlackNotification(
            webhook_url=self.config["webhook_url"],
            channel=self.config.get("channel"),
            username=self.config.get("username", "Truthound Dashboard"),
            icon_emoji=self.config.get("icon_emoji", ":bar_chart:"),
            mention_on_failure=self.config.get("mention_on_failure", []),
            include_details=True,
            notify_on="always",  # Dashboard handles when to send
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to Slack using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            # truthound actions are sync, run in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False

    def format_message(self, event: NotificationEvent) -> str:
        """Format message for Slack."""
        if isinstance(event, TestNotificationEvent):
            return f"✅ *Test Notification* from truthound-dashboard\nChannel: {event.channel_name}"
        return super().format_message(event)


@ChannelRegistry.register("email")
class EmailChannel(BaseNotificationChannel):
    """Email notification channel using truthound.checkpoint.actions.EmailNotification.

    Configuration:
        smtp_host: SMTP server host (required)
        smtp_port: SMTP server port (default: 587)
        smtp_user: SMTP authentication user
        smtp_password: SMTP authentication password
        use_tls: Use TLS (default: true)
        use_ssl: Use SSL (default: false)
        from_address: Sender email address (required)
        to_addresses: List of recipient addresses (required)
        cc_addresses: List of CC addresses
        provider: Email provider (smtp, sendgrid, ses)
        api_key: API key for SendGrid/SES
    """

    channel_type = "email"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Email channel configuration schema."""
        return {
            "smtp_host": {
                "type": "string",
                "required": False,
                "description": "SMTP server host",
            },
            "smtp_port": {
                "type": "integer",
                "required": False,
                "description": "SMTP server port (default: 587)",
            },
            "smtp_user": {
                "type": "string",
                "required": False,
                "description": "SMTP authentication user",
            },
            "smtp_password": {
                "type": "string",
                "required": False,
                "description": "SMTP authentication password",
            },
            "use_tls": {
                "type": "boolean",
                "required": False,
                "description": "Use TLS encryption",
            },
            "use_ssl": {
                "type": "boolean",
                "required": False,
                "description": "Use SSL encryption",
            },
            "from_address": {
                "type": "string",
                "required": True,
                "description": "Sender email address",
            },
            "to_addresses": {
                "type": "array",
                "required": True,
                "description": "List of recipient email addresses",
            },
            "cc_addresses": {
                "type": "array",
                "required": False,
                "description": "List of CC email addresses",
            },
            "provider": {
                "type": "string",
                "required": False,
                "description": "Email provider: smtp, sendgrid, ses",
            },
            "api_key": {
                "type": "string",
                "required": False,
                "description": "API key for SendGrid/SES",
            },
        }

    def _create_action(self) -> EmailNotification:
        """Create truthound EmailNotification action."""
        return EmailNotification(
            smtp_host=self.config.get("smtp_host", "localhost"),
            smtp_port=self.config.get("smtp_port", 587),
            smtp_user=self.config.get("smtp_user"),
            smtp_password=self.config.get("smtp_password"),
            use_tls=self.config.get("use_tls", True),
            use_ssl=self.config.get("use_ssl", False),
            from_address=self.config["from_address"],
            to_addresses=self.config["to_addresses"],
            cc_addresses=self.config.get("cc_addresses", []),
            provider=self.config.get("provider", "smtp"),
            api_key=self.config.get("api_key"),
            include_html=True,
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification via Email using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False


@ChannelRegistry.register("teams")
class TeamsChannel(BaseNotificationChannel):
    """Microsoft Teams notification channel using truthound.checkpoint.actions.TeamsNotification.

    Configuration:
        webhook_url: Teams incoming webhook URL (required)
        channel: Channel name for display
        include_details: Include detailed information
    """

    channel_type = "teams"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Teams channel configuration schema."""
        return {
            "webhook_url": {
                "type": "string",
                "required": True,
                "description": "Teams incoming webhook URL",
            },
            "channel": {
                "type": "string",
                "required": False,
                "description": "Channel name for display",
            },
            "include_details": {
                "type": "boolean",
                "required": False,
                "description": "Include detailed statistics",
            },
        }

    def _create_action(self) -> TeamsNotification:
        """Create truthound TeamsNotification action."""
        return TeamsNotification(
            webhook_url=self.config["webhook_url"],
            channel=self.config.get("channel"),
            include_details=self.config.get("include_details", True),
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to Teams using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"Teams notification failed: {e}")
            return False


@ChannelRegistry.register("discord")
class DiscordChannel(BaseNotificationChannel):
    """Discord notification channel using truthound.checkpoint.actions.DiscordNotification.

    Configuration:
        webhook_url: Discord webhook URL (required)
        username: Bot display name
        avatar_url: Bot avatar URL
        embed_color: Embed color (hex integer)
        include_mentions: List of mentions (@here, role IDs, etc.)
    """

    channel_type = "discord"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Discord channel configuration schema."""
        return {
            "webhook_url": {
                "type": "string",
                "required": True,
                "description": "Discord webhook URL",
            },
            "username": {
                "type": "string",
                "required": False,
                "description": "Bot display name",
            },
            "avatar_url": {
                "type": "string",
                "required": False,
                "description": "Bot avatar URL",
            },
            "embed_color": {
                "type": "integer",
                "required": False,
                "description": "Embed color (hex integer)",
            },
            "include_mentions": {
                "type": "array",
                "required": False,
                "description": "List of mentions (@here, role IDs, etc.)",
            },
        }

    def _create_action(self) -> DiscordNotification:
        """Create truthound DiscordNotification action."""
        return DiscordNotification(
            webhook_url=self.config["webhook_url"],
            username=self.config.get("username", "Truthound Bot"),
            avatar_url=self.config.get("avatar_url"),
            embed_color=self.config.get("embed_color"),
            include_mentions=self.config.get("include_mentions", []),
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to Discord using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            return False


@ChannelRegistry.register("telegram")
class TelegramChannel(BaseNotificationChannel):
    """Telegram notification channel using truthound.checkpoint.actions.TelegramNotification.

    Configuration:
        bot_token: Telegram Bot Token (required)
        chat_id: Channel/Group ID (required)
        parse_mode: Parse mode (Markdown or HTML)
        disable_notification: Silent notification
    """

    channel_type = "telegram"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Telegram channel configuration schema."""
        return {
            "bot_token": {
                "type": "string",
                "required": True,
                "description": "Telegram Bot Token",
            },
            "chat_id": {
                "type": "string",
                "required": True,
                "description": "Channel/Group ID",
            },
            "parse_mode": {
                "type": "string",
                "required": False,
                "description": "Parse mode: Markdown or HTML",
            },
            "disable_notification": {
                "type": "boolean",
                "required": False,
                "description": "Silent notification",
            },
        }

    def _create_action(self) -> TelegramNotification:
        """Create truthound TelegramNotification action."""
        return TelegramNotification(
            bot_token=self.config["bot_token"],
            chat_id=self.config["chat_id"],
            parse_mode=self.config.get("parse_mode", "Markdown"),
            disable_notification=self.config.get("disable_notification", False),
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to Telegram using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False


@ChannelRegistry.register("pagerduty")
class PagerDutyChannel(BaseNotificationChannel):
    """PagerDuty notification channel using truthound.checkpoint.actions.PagerDutyAction.

    Configuration:
        routing_key: PagerDuty Events API v2 routing key (required)
        severity: Alert severity (critical, error, warning, info)
        component: Affected component name
        group: Alert grouping key
        class_type: Alert class
        custom_details: Additional details to include
    """

    channel_type = "pagerduty"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get PagerDuty channel configuration schema."""
        return {
            "routing_key": {
                "type": "string",
                "required": True,
                "description": "PagerDuty Events API v2 routing key",
            },
            "severity": {
                "type": "string",
                "required": False,
                "description": "Alert severity: critical, error, warning, info",
            },
            "component": {
                "type": "string",
                "required": False,
                "description": "Affected component name",
            },
            "group": {
                "type": "string",
                "required": False,
                "description": "Alert grouping key",
            },
            "class_type": {
                "type": "string",
                "required": False,
                "description": "Alert class/type",
            },
            "custom_details": {
                "type": "object",
                "required": False,
                "description": "Additional custom details",
            },
        }

    def _create_action(self) -> PagerDutyAction:
        """Create truthound PagerDutyAction."""
        return PagerDutyAction(
            routing_key=self.config["routing_key"],
            severity=self.config.get("severity", "error"),
            component=self.config.get("component"),
            group=self.config.get("group"),
            class_type=self.config.get("class_type"),
            custom_details=self.config.get("custom_details", {}),
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to PagerDuty using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"PagerDuty notification failed: {e}")
            return False


@ChannelRegistry.register("webhook")
class WebhookChannel(BaseNotificationChannel):
    """Generic webhook notification channel using truthound.checkpoint.actions.WebhookAction.

    Configuration:
        url: Webhook URL (required)
        method: HTTP method (GET, POST, PUT, PATCH)
        headers: Custom HTTP headers
        timeout: Request timeout in seconds
        include_result: Include full result in payload
    """

    channel_type = "webhook"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get Webhook channel configuration schema."""
        return {
            "url": {
                "type": "string",
                "required": True,
                "description": "Webhook URL",
            },
            "method": {
                "type": "string",
                "required": False,
                "description": "HTTP method: GET, POST, PUT, PATCH",
            },
            "headers": {
                "type": "object",
                "required": False,
                "description": "Custom HTTP headers",
            },
            "timeout": {
                "type": "integer",
                "required": False,
                "description": "Request timeout in seconds",
            },
            "include_result": {
                "type": "boolean",
                "required": False,
                "description": "Include full result in payload",
            },
        }

    def _create_action(self) -> WebhookAction:
        """Create truthound WebhookAction."""
        return WebhookAction(
            url=self.config["url"],
            method=self.config.get("method", "POST"),
            headers=self.config.get("headers", {}),
            timeout=self.config.get("timeout", 30),
            include_result=self.config.get("include_result", True),
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification via Webhook using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False


@ChannelRegistry.register("opsgenie")
class OpsGenieChannel(BaseNotificationChannel):
    """OpsGenie notification channel using truthound.checkpoint.actions.OpsGenieAction.

    Configuration:
        api_key: OpsGenie API key (required)
        region: OpsGenie region (us or eu)
        priority: Alert priority (P1-P5)
        auto_priority: Automatic priority mapping
        tags: Alert tags
        auto_close_on_success: Automatically close on success
    """

    channel_type = "opsgenie"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get OpsGenie channel configuration schema."""
        return {
            "api_key": {
                "type": "string",
                "required": True,
                "description": "OpsGenie API key",
            },
            "region": {
                "type": "string",
                "required": False,
                "description": "OpsGenie region: us or eu",
            },
            "priority": {
                "type": "string",
                "required": False,
                "description": "Alert priority: P1, P2, P3, P4, P5",
            },
            "auto_priority": {
                "type": "boolean",
                "required": False,
                "description": "Automatic priority mapping based on validation results",
            },
            "tags": {
                "type": "array",
                "required": False,
                "description": "Alert tags",
            },
            "auto_close_on_success": {
                "type": "boolean",
                "required": False,
                "description": "Automatically close on success",
            },
        }

    def _create_action(self) -> OpsGenieAction:
        """Create truthound OpsGenieAction."""
        return OpsGenieAction(
            api_key=self.config["api_key"],
            region=self.config.get("region", "us"),
            priority=self.config.get("priority", "P3"),
            auto_priority=self.config.get("auto_priority", True),
            tags=self.config.get("tags", []),
            auto_close_on_success=self.config.get("auto_close_on_success", True),
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to OpsGenie using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"OpsGenie notification failed: {e}")
            return False


@ChannelRegistry.register("github")
class GitHubChannel(BaseNotificationChannel):
    """GitHub notification channel using truthound.checkpoint.actions.GitHubAction.

    Creates GitHub issues or check runs for notifications.

    Configuration:
        token: GitHub personal access token (required)
        owner: Repository owner (required)
        repo: Repository name (required)
        labels: Issue labels
        assignees: Issue assignees
        create_check_run: Create check run instead of issue
    """

    channel_type = "github"

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get GitHub channel configuration schema."""
        return {
            "token": {
                "type": "string",
                "required": True,
                "description": "GitHub personal access token",
            },
            "owner": {
                "type": "string",
                "required": True,
                "description": "Repository owner",
            },
            "repo": {
                "type": "string",
                "required": True,
                "description": "Repository name",
            },
            "labels": {
                "type": "array",
                "required": False,
                "description": "Issue labels",
            },
            "assignees": {
                "type": "array",
                "required": False,
                "description": "Issue assignees",
            },
            "create_check_run": {
                "type": "boolean",
                "required": False,
                "description": "Create check run instead of issue",
            },
        }

    def _create_action(self) -> GitHubAction:
        """Create truthound GitHubAction."""
        return GitHubAction(
            token=self.config["token"],
            repo=f"{self.config['owner']}/{self.config['repo']}",
            create_check_run=self.config.get("create_check_run", False),
            labels=self.config.get("labels", ["data-quality"]),
            assignees=self.config.get("assignees", []),
            notify_on="always",
        )

    async def send(
        self,
        message: str,
        event: NotificationEvent | None = None,
        **kwargs: Any,
    ) -> bool:
        """Send notification to GitHub using truthound library."""
        try:
            action = self._create_action()
            mock_result = _build_checkpoint_result_mock(event)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, action.execute, mock_result)
            return True
        except Exception as e:
            logger.error(f"GitHub notification failed: {e}")
            return False
