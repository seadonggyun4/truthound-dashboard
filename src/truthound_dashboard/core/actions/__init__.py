"""Concrete action implementations for checkpoint pipelines.

This module provides built-in action implementations for common use cases:
- Notification actions: Slack, Email, Teams, Discord, PagerDuty
- Storage actions: Filesystem, S3, GCS
- Webhook actions: HTTP POST to external endpoints
- Custom actions: Python callbacks and shell commands

All actions are loosely coupled from truthound and implement the
ActionProtocol interface defined in interfaces.actions.

Usage:
    from truthound_dashboard.core.actions import SlackNotificationAction

    action = SlackNotificationAction(
        webhook_url="https://hooks.slack.com/services/...",
        channel="#data-quality-alerts",
    )

    # Execute with context
    result = action.execute(context)
"""

from truthound_dashboard.core.actions.notifications import (
    DiscordNotificationAction,
    EmailNotificationAction,
    PagerDutyNotificationAction,
    SlackNotificationAction,
    TeamsNotificationAction,
    TelegramNotificationAction,
)
from truthound_dashboard.core.actions.storage import (
    FileStorageAction,
    GCSStorageAction,
    S3StorageAction,
)
from truthound_dashboard.core.actions.webhook import (
    WebhookAction,
)
from truthound_dashboard.core.actions.custom import (
    CallbackAction,
    ShellCommandAction,
)

__all__ = [
    # Notification actions
    "SlackNotificationAction",
    "EmailNotificationAction",
    "TeamsNotificationAction",
    "DiscordNotificationAction",
    "TelegramNotificationAction",
    "PagerDutyNotificationAction",
    # Storage actions
    "FileStorageAction",
    "S3StorageAction",
    "GCSStorageAction",
    # Webhook action
    "WebhookAction",
    # Custom actions
    "CallbackAction",
    "ShellCommandAction",
]
