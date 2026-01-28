"""Dashboard-specific routing adapters using truthound.checkpoint.routing.

This module provides adapters that convert Dashboard notification events
into truthound RouteContext objects for use with truthound's routing system.

The main purpose is to bridge the Dashboard's event system with truthound's
routing infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from truthound.checkpoint.routing.base import RouteContext

if TYPE_CHECKING:
    from truthound_dashboard.core.notifications.base import NotificationEvent


@dataclass
class DashboardRouteContext:
    """Dashboard-specific context that wraps truthound's RouteContext.

    This provides helper methods for extracting data from Dashboard
    notification events.

    Attributes:
        event: The notification event being routed.
        metadata: Additional context metadata.
        timestamp: When routing is being evaluated.
    """

    event: "NotificationEvent"
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def get_severity(self) -> str | None:
        """Get event severity if available."""
        if hasattr(self.event, "severity"):
            return self.event.severity
        if hasattr(self.event, "has_critical") and self.event.has_critical:
            return "critical"
        if hasattr(self.event, "has_high") and self.event.has_high:
            return "high"
        return self.metadata.get("severity")

    def get_issue_count(self) -> int:
        """Get issue count if available."""
        if hasattr(self.event, "total_issues"):
            return self.event.total_issues
        return self.metadata.get("issue_count", 0)

    def get_pass_rate(self) -> float:
        """Get validation pass rate if available."""
        if hasattr(self.event, "pass_rate"):
            return self.event.pass_rate
        return self.metadata.get("pass_rate", 100.0)

    def get_tags(self) -> dict[str, str]:
        """Get context tags as dict."""
        tags = dict(self.metadata.get("tags", {}))
        if self.event.source_name:
            tags["source"] = self.event.source_name
        tags["event_type"] = self.event.event_type
        return tags

    def to_truthound_context(self) -> RouteContext:
        """Convert to truthound RouteContext.

        Creates a RouteContext object that can be used with truthound's
        ActionRouter for rule evaluation.
        """
        # Determine severity counts
        severity = self.get_severity()
        critical_issues = 1 if severity == "critical" else 0
        high_issues = 1 if severity == "high" else 0
        medium_issues = 1 if severity == "medium" else 0
        low_issues = 1 if severity == "low" else 0
        info_issues = 1 if severity == "info" else 0

        # Determine status
        status = "success"
        if hasattr(self.event, "event_type"):
            if "failed" in self.event.event_type.lower():
                status = "failure"
            elif "error" in self.event.event_type.lower():
                status = "error"
            elif "warning" in self.event.event_type.lower():
                status = "warning"

        return RouteContext(
            checkpoint_name=self.event.source_name or "dashboard_event",
            run_id=self.metadata.get("run_id", "dashboard"),
            status=status,
            data_asset=self.event.source_name or "unknown",
            run_time=self.timestamp,
            total_issues=self.get_issue_count(),
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            info_issues=info_issues,
            pass_rate=self.get_pass_rate(),
            tags=self.get_tags(),
            metadata=self.metadata,
            error=self.metadata.get("error"),
        )


@dataclass
class DashboardRoutingResult:
    """Result of routing evaluation for Dashboard notifications.

    Attributes:
        matched_routes: List of route names that matched.
        channel_ids: Set of channel IDs to send notifications to.
        timestamp: When routing was evaluated.
        context: The context that was evaluated.
    """

    matched_routes: list[str] = field(default_factory=list)
    channel_ids: set[str] = field(default_factory=set)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: DashboardRouteContext | None = None


def create_route_context_from_event(
    event: "NotificationEvent",
    metadata: dict[str, Any] | None = None,
) -> RouteContext:
    """Create a truthound RouteContext from a Dashboard notification event.

    This is a convenience function for converting Dashboard events into
    truthound's routing context.

    Args:
        event: The notification event.
        metadata: Optional additional metadata.

    Returns:
        RouteContext for use with truthound's ActionRouter.

    Example:
        from truthound.checkpoint.routing import ActionRouter

        context = create_route_context_from_event(event, {"env": "prod"})
        matched = router.route(context)
    """
    dashboard_context = DashboardRouteContext(
        event=event,
        metadata=metadata or {},
    )
    return dashboard_context.to_truthound_context()
