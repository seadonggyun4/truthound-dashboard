"""Webhook action implementation.

Provides a generic HTTP webhook action for integrating with
external systems via HTTP POST requests.
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


@dataclass
class WebhookConfig(ActionConfig):
    """Configuration for webhook action.

    Attributes:
        url: Webhook URL.
        method: HTTP method (POST, PUT, PATCH).
        headers: Additional HTTP headers.
        auth_type: Authentication type (none, basic, bearer, api_key).
        auth_username: Basic auth username.
        auth_password: Basic auth password.
        auth_token: Bearer token or API key.
        auth_header: Header name for API key auth.
        payload_template: Custom payload template (Jinja2).
        include_issues: Include issues in payload.
        max_issues: Maximum issues to include.
        verify_ssl: Verify SSL certificates.
        retry_on_5xx: Retry on 5xx errors.
    """

    url: str = ""
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    auth_type: str = "none"  # none, basic, bearer, api_key
    auth_username: str = ""
    auth_password: str = ""
    auth_token: str = ""
    auth_header: str = "X-API-Key"
    payload_template: str | None = None
    include_issues: bool = True
    max_issues: int = 100
    verify_ssl: bool = True
    retry_on_5xx: bool = True

    def __post_init__(self):
        self.name = self.name or "webhook"


@register_action("webhook")
class WebhookAction(BaseAction):
    """Generic HTTP webhook action.

    Sends validation results to external systems via HTTP POST.
    Supports various authentication methods and custom payloads.

    Example:
        action = WebhookAction(
            url="https://api.example.com/validations",
            auth_type="bearer",
            auth_token="secret-token",
        )
    """

    def __init__(
        self,
        url: str = "",
        method: str = "POST",
        headers: dict[str, str] | None = None,
        notify_on: NotifyCondition = NotifyCondition.ALWAYS,
        config: WebhookConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = WebhookConfig(
                url=url,
                method=method,
                headers=headers or {},
                notify_on=notify_on,
                **kwargs,
            )
        elif isinstance(config, dict):
            config = WebhookConfig(**config)

        super().__init__(config)
        self._webhook_config: WebhookConfig = config

    @property
    def action_type(self) -> str:
        return "webhook"

    def _do_execute(self, context: ActionContext) -> ActionResult:
        """Send webhook request."""
        import httpx

        result = context.checkpoint_result
        payload = self._build_payload(context)
        headers = self._build_headers()

        try:
            with httpx.Client(
                timeout=self._config.timeout_seconds,
                verify=self._webhook_config.verify_ssl,
            ) as client:
                # Build auth
                auth = None
                if self._webhook_config.auth_type == "basic":
                    auth = (
                        self._webhook_config.auth_username,
                        self._webhook_config.auth_password,
                    )

                response = client.request(
                    method=self._webhook_config.method,
                    url=self._webhook_config.url,
                    json=payload,
                    headers=headers,
                    auth=auth,
                )

                # Check for retry on 5xx
                if (
                    response.status_code >= 500
                    and self._webhook_config.retry_on_5xx
                    and self._config.retry_count > 0
                ):
                    # Simple retry logic
                    for i in range(self._config.retry_count):
                        response = client.request(
                            method=self._webhook_config.method,
                            url=self._webhook_config.url,
                            json=payload,
                            headers=headers,
                            auth=auth,
                        )
                        if response.status_code < 500:
                            break

                response.raise_for_status()

            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.SUCCESS,
                message=f"Webhook sent to {self._webhook_config.url}",
                details={
                    "url": self._webhook_config.url,
                    "status_code": response.status_code,
                },
            )
        except httpx.HTTPError as e:
            return ActionResult(
                action_name=self.name,
                action_type=self.action_type,
                status=ActionStatus.FAILURE,
                message=f"Webhook failed: {str(e)}",
                error=str(e),
            )

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers including authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Truthound-Dashboard/1.0",
            **self._webhook_config.headers,
        }

        # Add authentication headers
        if self._webhook_config.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self._webhook_config.auth_token}"
        elif self._webhook_config.auth_type == "api_key":
            headers[self._webhook_config.auth_header] = self._webhook_config.auth_token

        return headers

    def _build_payload(self, context: ActionContext) -> dict[str, Any]:
        """Build webhook payload."""
        result = context.checkpoint_result

        # Use custom template if provided
        if self._webhook_config.payload_template:
            return self._render_template(context)

        # Default payload structure
        payload = {
            "event": "validation_completed",
            "timestamp": datetime.now().isoformat(),
            "checkpoint": {
                "name": result.checkpoint_name,
                "run_id": result.run_id,
                "status": result.status.value,
            },
            "source": {
                "name": result.source_name,
                "row_count": result.row_count,
                "column_count": result.column_count,
            },
            "summary": {
                "total_issues": result.issue_count,
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
                "has_critical": result.has_critical,
                "has_high": result.has_high,
            },
            "timing": {
                "started_at": result.started_at.isoformat() if result.started_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "duration_ms": result.duration_ms,
            },
            "metadata": result.metadata,
        }

        # Include issues if configured
        if self._webhook_config.include_issues and result.issues:
            payload["issues"] = result.issues[: self._webhook_config.max_issues]
            if len(result.issues) > self._webhook_config.max_issues:
                payload["issues_truncated"] = True
                payload["total_issues_count"] = len(result.issues)

        return payload

    def _render_template(self, context: ActionContext) -> dict[str, Any]:
        """Render custom payload template using Jinja2."""
        try:
            from jinja2 import Environment
        except ImportError:
            logger.warning("Jinja2 not available, using default payload")
            return self._build_payload(context)

        result = context.checkpoint_result

        # Build template context
        template_context = {
            "result": result,
            "checkpoint_name": result.checkpoint_name,
            "run_id": result.run_id,
            "status": result.status.value,
            "source_name": result.source_name,
            "row_count": result.row_count,
            "column_count": result.column_count,
            "issue_count": result.issue_count,
            "critical_count": result.critical_count,
            "high_count": result.high_count,
            "medium_count": result.medium_count,
            "low_count": result.low_count,
            "has_critical": result.has_critical,
            "has_high": result.has_high,
            "issues": result.issues,
            "metadata": result.metadata,
            "tags": context.tags,
            "timestamp": datetime.now().isoformat(),
        }

        env = Environment()
        template = env.from_string(self._webhook_config.payload_template)
        rendered = template.render(**template_context)

        # Parse as JSON
        try:
            return json.loads(rendered)
        except json.JSONDecodeError:
            # Return as wrapped string
            return {"payload": rendered}
