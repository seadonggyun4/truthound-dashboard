"""Notification action implementations.

Provides actions for sending notifications to various platforms:
- Slack (via webhook or Bot API)
- Email (via SMTP or API services)
- Microsoft Teams
- Discord
- Telegram
- PagerDuty

These actions are loosely coupled from truthound and can be used
independently of the checkpoint system.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from truthound_dashboard.core.interfaces.actions import (
    ActionConfig,
    ActionContext,
    ActionResult,
    ActionStatus,
    BaseAction,
    NotifyCondition,
    register_action,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Slack Notification
# =============================================================================


@dataclass
class SlackNotificationConfig(ActionConfig):
    """Configuration for Slack notifications.

    Attributes:
        webhook_url: Slack webhook URL.
        channel: Override channel (optional).
        username: Bot username.
        icon_emoji: Bot icon emoji.
        mention_users: Users to mention on failure.
        mention_groups: Groups to mention on failure.
        include_summary: Include issue summary.
        include_details: Include detailed issues.
        max_issues_shown: Max issues to show in message.
    """

    webhook_url: str = ""
    channel: str | None = None
    username: str = "Truthound Bot"
    icon_emoji: str = ":bar_chart:"
    mention_users: list[str] = field(default_factory=list)
    mention_groups: list[str] = field(default_factory=list)
    include_summary: bool = True
    include_details: bool = True
    max_issues_shown: int = 5

    def __post_init__(self):
        self.name = self.name or "slack"


@register_action("slack")
class SlackNotificationAction(BaseAction):
    """Slack notification action via webhook.

    Sends formatted messages to Slack when validation completes.
    Supports mentions, custom formatting, and rich block layouts.

    Example:
        action = SlackNotificationAction(
            webhook_url="https://hooks.slack.com/services/...",
            notify_on=NotifyCondition.FAILURE,
        )
    """

    def __init__(
        self,
        webhook_url: str = "",
        channel: str | None = None,
        username: str = "Truthound Bot",
        notify_on: NotifyCondition = NotifyCondition.FAILURE,
        config: SlackNotificationConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Slack action.

        Args:
            webhook_url: Slack webhook URL.
            channel: Override channel.
            username: Bot username.
            notify_on: When to send notifications.
            config: Full configuration object.
            **kwargs: Additional configuration.
        """
        if config is None:
            config = SlackNotificationConfig(
                webhook_url=webhook_url,
                channel=channel,
                username=username,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = SlackNotificationConfig(**config)

        super().__init__(config)
        self._slack_config: SlackNotificationConfig = config

    @property
    def action_type(self) -> str:
        return "notification"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Send Slack notification."""
        import httpx

        result = context.checkpoint_result
        payload = self._build_payload(context)

        try:
            with httpx.Client(timeout=self._config.timeout_seconds) as client:
                response = client.post(
                    self._slack_config.webhook_url,
                    json=payload,
                )
                response.raise_for_status()

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Slack notification sent for {result.checkpoint_name}",
                details={"channel": self._slack_config.channel},
            )
        except httpx.HTTPError as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to send Slack notification: {str(e)}",
                error=str(e),
            )

    def _build_payload(self, context: ActionContext) -> dict[str, Any]:
        """Build Slack webhook payload with blocks."""
        result = context.checkpoint_result
        status = result.status.value

        # Determine color and emoji based on status
        if status == "success":
            color = "#36a64f"
            emoji = ":white_check_mark:"
        elif status in ("failure", "error"):
            color = "#dc3545"
            emoji = ":x:"
        elif status == "warning":
            color = "#ffc107"
            emoji = ":warning:"
        else:
            color = "#6c757d"
            emoji = ":grey_question:"

        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Validation {status.title()}: {result.checkpoint_name}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Source:*\n{result.source_name}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{status.title()}"},
                    {"type": "mrkdwn", "text": f"*Rows:*\n{result.row_count:,}"},
                    {"type": "mrkdwn", "text": f"*Issues:*\n{result.issue_count:,}"},
                ],
            },
        ]

        # Add summary if enabled
        if self._slack_config.include_summary and result.issue_count > 0:
            summary_text = (
                f":red_circle: Critical: {result.critical_count}  "
                f":orange_circle: High: {result.high_count}  "
                f":yellow_circle: Medium: {result.medium_count}  "
                f":white_circle: Low: {result.low_count}"
            )
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": summary_text},
            })

        # Add issue details if enabled
        if (
            self._slack_config.include_details
            and result.issues
            and result.issue_count > 0
        ):
            issues_text = "*Top Issues:*\n"
            for issue in result.issues[: self._slack_config.max_issues_shown]:
                col = issue.get("column", "N/A")
                issue_type = issue.get("issue_type", "unknown")
                count = issue.get("count", 0)
                issues_text += f"• `{col}`: {issue_type} ({count:,} rows)\n"

            if result.issue_count > self._slack_config.max_issues_shown:
                issues_text += f"_...and {result.issue_count - self._slack_config.max_issues_shown} more_"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": issues_text},
            })

        # Add mentions for failures
        if status in ("failure", "error") and (
            self._slack_config.mention_users or self._slack_config.mention_groups
        ):
            mentions = []
            for user in self._slack_config.mention_users:
                mentions.append(f"<@{user}>")
            for group in self._slack_config.mention_groups:
                mentions.append(f"<!subteam^{group}>")

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": " ".join(mentions)},
            })

        # Add timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Run ID: `{result.run_id}` | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                }
            ],
        })

        payload = {
            "username": self._slack_config.username,
            "icon_emoji": self._slack_config.icon_emoji,
            "attachments": [{"color": color, "blocks": blocks}],
        }

        if self._slack_config.channel:
            payload["channel"] = self._slack_config.channel

        return payload


# =============================================================================
# Email Notification
# =============================================================================


@dataclass
class EmailNotificationConfig(ActionConfig):
    """Configuration for email notifications.

    Attributes:
        smtp_host: SMTP server host.
        smtp_port: SMTP server port.
        smtp_username: SMTP username.
        smtp_password: SMTP password.
        smtp_use_tls: Use TLS encryption.
        from_email: Sender email address.
        to_emails: Recipient email addresses.
        cc_emails: CC email addresses.
        subject_template: Email subject template.
        body_template: Email body template (HTML).
        include_attachment: Attach detailed report.
    """

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = ""
    to_emails: list[str] = field(default_factory=list)
    cc_emails: list[str] = field(default_factory=list)
    subject_template: str = "[{status}] Validation: {checkpoint_name}"
    body_template: str = ""
    include_attachment: bool = False

    def __post_init__(self):
        self.name = self.name or "email"


@register_action("email")
class EmailNotificationAction(BaseAction):
    """Email notification action via SMTP.

    Sends formatted HTML emails when validation completes.
    Supports templates, attachments, and CC recipients.
    """

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        from_email: str = "",
        to_emails: list[str] | None = None,
        notify_on: NotifyCondition = NotifyCondition.FAILURE,
        config: EmailNotificationConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize email action."""
        if config is None:
            config = EmailNotificationConfig(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                from_email=from_email,
                to_emails=to_emails or [],
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = EmailNotificationConfig(**config)

        super().__init__(config)
        self._email_config: EmailNotificationConfig = config

    @property
    def action_type(self) -> str:
        return "notification"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Send email notification."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        result = context.checkpoint_result

        # Build subject
        subject = self._email_config.subject_template.format(
            status=result.status.value.upper(),
            checkpoint_name=result.checkpoint_name,
            source_name=result.source_name,
        )

        # Build body
        body = self._build_html_body(context)

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._email_config.from_email
            msg["To"] = ", ".join(self._email_config.to_emails)
            if self._email_config.cc_emails:
                msg["Cc"] = ", ".join(self._email_config.cc_emails)

            msg.attach(MIMEText(body, "html"))

            # Connect and send
            with smtplib.SMTP(
                self._email_config.smtp_host,
                self._email_config.smtp_port,
            ) as server:
                if self._email_config.smtp_use_tls:
                    server.starttls()
                if self._email_config.smtp_username:
                    server.login(
                        self._email_config.smtp_username,
                        self._email_config.smtp_password,
                    )

                recipients = (
                    self._email_config.to_emails + self._email_config.cc_emails
                )
                server.sendmail(
                    self._email_config.from_email,
                    recipients,
                    msg.as_string(),
                )

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Email sent to {len(self._email_config.to_emails)} recipients",
                details={"recipients": self._email_config.to_emails},
            )
        except Exception as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to send email: {str(e)}",
                error=str(e),
            )

    def _build_html_body(self, context: ActionContext) -> str:
        """Build HTML email body."""
        result = context.checkpoint_result
        status = result.status.value

        # Determine color
        if status == "success":
            status_color = "#28a745"
        elif status in ("failure", "error"):
            status_color = "#dc3545"
        else:
            status_color = "#ffc107"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: {status_color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Validation {status.title()}</h1>
                <p>{result.checkpoint_name}</p>
            </div>
            <div class="content">
                <div class="summary">
                    <h3>Summary</h3>
                    <p><strong>Source:</strong> {result.source_name}</p>
                    <p><strong>Rows:</strong> {result.row_count:,}</p>
                    <p><strong>Columns:</strong> {result.column_count}</p>
                    <p><strong>Total Issues:</strong> {result.issue_count:,}</p>
                </div>

                <h3>Issue Breakdown</h3>
                <table>
                    <tr>
                        <th>Severity</th>
                        <th>Count</th>
                    </tr>
                    <tr><td>Critical</td><td>{result.critical_count}</td></tr>
                    <tr><td>High</td><td>{result.high_count}</td></tr>
                    <tr><td>Medium</td><td>{result.medium_count}</td></tr>
                    <tr><td>Low</td><td>{result.low_count}</td></tr>
                </table>

                <p style="margin-top: 20px; color: #6c757d;">
                    Run ID: {result.run_id}<br>
                    Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        return html


# =============================================================================
# Microsoft Teams Notification
# =============================================================================


@dataclass
class TeamsNotificationConfig(ActionConfig):
    """Configuration for Microsoft Teams notifications."""

    webhook_url: str = ""
    mention_users: list[str] = field(default_factory=list)
    include_summary: bool = True

    def __post_init__(self):
        self.name = self.name or "teams"


@register_action("teams")
class TeamsNotificationAction(BaseAction):
    """Microsoft Teams notification action via webhook."""

    def __init__(
        self,
        webhook_url: str = "",
        notify_on: NotifyCondition = NotifyCondition.FAILURE,
        config: TeamsNotificationConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = TeamsNotificationConfig(
                webhook_url=webhook_url,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = TeamsNotificationConfig(**config)

        super().__init__(config)
        self._teams_config: TeamsNotificationConfig = config

    @property
    def action_type(self) -> str:
        return "notification"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Send Teams notification."""
        import httpx

        result = context.checkpoint_result
        payload = self._build_adaptive_card(context)

        try:
            with httpx.Client(timeout=self._config.timeout_seconds) as client:
                response = client.post(
                    self._teams_config.webhook_url,
                    json=payload,
                )
                response.raise_for_status()

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Teams notification sent for {result.checkpoint_name}",
            )
        except httpx.HTTPError as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to send Teams notification: {str(e)}",
                error=str(e),
            )

    def _build_adaptive_card(self, context: ActionContext) -> dict[str, Any]:
        """Build Teams Adaptive Card payload."""
        result = context.checkpoint_result
        status = result.status.value

        if status == "success":
            theme_color = "00FF00"
        elif status in ("failure", "error"):
            theme_color = "FF0000"
        else:
            theme_color = "FFA500"

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": f"Validation {status}: {result.checkpoint_name}",
            "sections": [
                {
                    "activityTitle": f"Validation {status.title()}: {result.checkpoint_name}",
                    "facts": [
                        {"name": "Source", "value": result.source_name},
                        {"name": "Status", "value": status.title()},
                        {"name": "Rows", "value": f"{result.row_count:,}"},
                        {"name": "Issues", "value": f"{result.issue_count:,}"},
                        {"name": "Critical", "value": str(result.critical_count)},
                        {"name": "High", "value": str(result.high_count)},
                    ],
                }
            ],
        }


# =============================================================================
# Discord Notification
# =============================================================================


@dataclass
class DiscordNotificationConfig(ActionConfig):
    """Configuration for Discord notifications."""

    webhook_url: str = ""
    username: str = "Truthound Bot"
    avatar_url: str = ""
    mention_roles: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.name = self.name or "discord"


@register_action("discord")
class DiscordNotificationAction(BaseAction):
    """Discord notification action via webhook."""

    def __init__(
        self,
        webhook_url: str = "",
        notify_on: NotifyCondition = NotifyCondition.FAILURE,
        config: DiscordNotificationConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = DiscordNotificationConfig(
                webhook_url=webhook_url,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = DiscordNotificationConfig(**config)

        super().__init__(config)
        self._discord_config: DiscordNotificationConfig = config

    @property
    def action_type(self) -> str:
        return "notification"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Send Discord notification."""
        import httpx

        result = context.checkpoint_result
        payload = self._build_embed(context)

        try:
            with httpx.Client(timeout=self._config.timeout_seconds) as client:
                response = client.post(
                    self._discord_config.webhook_url,
                    json=payload,
                )
                response.raise_for_status()

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Discord notification sent for {result.checkpoint_name}",
            )
        except httpx.HTTPError as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to send Discord notification: {str(e)}",
                error=str(e),
            )

    def _build_embed(self, context: ActionContext) -> dict[str, Any]:
        """Build Discord embed payload."""
        result = context.checkpoint_result
        status = result.status.value

        if status == "success":
            color = 0x28A745
        elif status in ("failure", "error"):
            color = 0xDC3545
        else:
            color = 0xFFC107

        embed = {
            "title": f"Validation {status.title()}: {result.checkpoint_name}",
            "color": color,
            "fields": [
                {"name": "Source", "value": result.source_name, "inline": True},
                {"name": "Status", "value": status.title(), "inline": True},
                {"name": "Rows", "value": f"{result.row_count:,}", "inline": True},
                {"name": "Issues", "value": f"{result.issue_count:,}", "inline": True},
                {"name": "Critical", "value": str(result.critical_count), "inline": True},
                {"name": "High", "value": str(result.high_count), "inline": True},
            ],
            "footer": {"text": f"Run ID: {result.run_id}"},
            "timestamp": datetime.now().isoformat(),
        }

        payload = {
            "username": self._discord_config.username,
            "embeds": [embed],
        }

        if self._discord_config.avatar_url:
            payload["avatar_url"] = self._discord_config.avatar_url

        # Add role mentions
        if self._discord_config.mention_roles and status in ("failure", "error"):
            mentions = " ".join(f"<@&{role}>" for role in self._discord_config.mention_roles)
            payload["content"] = mentions

        return payload


# =============================================================================
# Telegram Notification
# =============================================================================


@dataclass
class TelegramNotificationConfig(ActionConfig):
    """Configuration for Telegram notifications."""

    bot_token: str = ""
    chat_id: str = ""
    parse_mode: str = "HTML"

    def __post_init__(self):
        self.name = self.name or "telegram"


@register_action("telegram")
class TelegramNotificationAction(BaseAction):
    """Telegram notification action via Bot API."""

    def __init__(
        self,
        bot_token: str = "",
        chat_id: str = "",
        notify_on: NotifyCondition = NotifyCondition.FAILURE,
        config: TelegramNotificationConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = TelegramNotificationConfig(
                bot_token=bot_token,
                chat_id=chat_id,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = TelegramNotificationConfig(**config)

        super().__init__(config)
        self._telegram_config: TelegramNotificationConfig = config

    @property
    def action_type(self) -> str:
        return "notification"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Send Telegram notification."""
        import httpx

        result = context.checkpoint_result
        message = self._build_message(context)

        url = f"https://api.telegram.org/bot{self._telegram_config.bot_token}/sendMessage"
        payload = {
            "chat_id": self._telegram_config.chat_id,
            "text": message,
            "parse_mode": self._telegram_config.parse_mode,
        }

        try:
            with httpx.Client(timeout=self._config.timeout_seconds) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Telegram notification sent for {result.checkpoint_name}",
            )
        except httpx.HTTPError as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to send Telegram notification: {str(e)}",
                error=str(e),
            )

    def _build_message(self, context: ActionContext) -> str:
        """Build Telegram message."""
        result = context.checkpoint_result
        status = result.status.value

        if status == "success":
            emoji = "✅"
        elif status in ("failure", "error"):
            emoji = "❌"
        else:
            emoji = "⚠️"

        return f"""
{emoji} <b>Validation {status.title()}</b>

<b>Checkpoint:</b> {result.checkpoint_name}
<b>Source:</b> {result.source_name}
<b>Status:</b> {status}

<b>Summary:</b>
• Rows: {result.row_count:,}
• Issues: {result.issue_count:,}
  - Critical: {result.critical_count}
  - High: {result.high_count}
  - Medium: {result.medium_count}
  - Low: {result.low_count}

<code>Run ID: {result.run_id}</code>
""".strip()


# =============================================================================
# PagerDuty Notification
# =============================================================================


@dataclass
class PagerDutyNotificationConfig(ActionConfig):
    """Configuration for PagerDuty notifications."""

    routing_key: str = ""  # Events API v2 routing key
    severity: str = "critical"  # critical, error, warning, info
    dedup_key_prefix: str = "truthound"

    def __post_init__(self):
        self.name = self.name or "pagerduty"


@register_action("pagerduty")
class PagerDutyNotificationAction(BaseAction):
    """PagerDuty notification action via Events API v2.

    Creates incidents in PagerDuty for validation failures.
    """

    def __init__(
        self,
        routing_key: str = "",
        severity: str = "critical",
        notify_on: NotifyCondition = NotifyCondition.FAILURE,
        config: PagerDutyNotificationConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = PagerDutyNotificationConfig(
                routing_key=routing_key,
                severity=severity,
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = PagerDutyNotificationConfig(**config)

        super().__init__(config)
        self._pagerduty_config: PagerDutyNotificationConfig = config

    @property
    def action_type(self) -> str:
        return "notification"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Send PagerDuty alert."""
        import httpx

        result = context.checkpoint_result
        payload = self._build_event(context)

        try:
            with httpx.Client(timeout=self._config.timeout_seconds) as client:
                response = client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                )
                response.raise_for_status()

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"PagerDuty alert created for {result.checkpoint_name}",
            )
        except httpx.HTTPError as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Failed to create PagerDuty alert: {str(e)}",
                error=str(e),
            )

    def _build_event(self, context: ActionContext) -> dict[str, Any]:
        """Build PagerDuty Events API v2 payload."""
        result = context.checkpoint_result

        return {
            "routing_key": self._pagerduty_config.routing_key,
            "event_action": "trigger",
            "dedup_key": f"{self._pagerduty_config.dedup_key_prefix}-{result.checkpoint_name}-{result.source_name}",
            "payload": {
                "summary": f"Data validation failed: {result.checkpoint_name}",
                "severity": self._pagerduty_config.severity,
                "source": result.source_name,
                "timestamp": datetime.now().isoformat(),
                "custom_details": {
                    "checkpoint": result.checkpoint_name,
                    "source": result.source_name,
                    "status": result.status.value,
                    "rows": result.row_count,
                    "total_issues": result.issue_count,
                    "critical_issues": result.critical_count,
                    "high_issues": result.high_count,
                    "run_id": result.run_id,
                },
            },
        }
