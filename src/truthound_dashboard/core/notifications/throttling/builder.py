"""Dashboard-specific throttler builder using truthound.

This module provides adapters that integrate truthound's throttling
system with the Dashboard's database configuration.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from truthound.checkpoint.throttling import (
    ThrottlerBuilder,
    NotificationThrottler,
    ThrottlingConfig,
    RateLimitScope,
    RateLimit,
)

if TYPE_CHECKING:
    from typing import Self


class DashboardThrottlerBuilder:
    """Dashboard-specific throttler builder.

    Wraps truthound's ThrottlerBuilder and provides integration
    with the Dashboard's database configuration.

    Example:
        builder = DashboardThrottlerBuilder()
        throttler = (
            builder
            .with_per_minute_limit(10)
            .with_per_hour_limit(100)
            .with_action_limit("pagerduty", per_minute=5)
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize the builder."""
        self._builder = ThrottlerBuilder()

    def with_per_minute_limit(self, limit: int) -> "Self":
        """Set per-minute rate limit."""
        self._builder.with_per_minute_limit(limit)
        return self

    def with_per_hour_limit(self, limit: int) -> "Self":
        """Set per-hour rate limit."""
        self._builder.with_per_hour_limit(limit)
        return self

    def with_per_day_limit(self, limit: int) -> "Self":
        """Set per-day rate limit."""
        self._builder.with_per_day_limit(limit)
        return self

    def with_burst_allowance(self, multiplier: float) -> "Self":
        """Set burst allowance multiplier."""
        self._builder.with_burst_allowance(multiplier)
        return self

    def with_algorithm(self, algorithm: str) -> "Self":
        """Set throttling algorithm (token_bucket, sliding_window, fixed_window)."""
        self._builder.with_algorithm(algorithm)
        return self

    def with_scope(self, scope: str) -> "Self":
        """Set rate limit scope."""
        scope_map = {
            "global": RateLimitScope.GLOBAL,
            "per_action": RateLimitScope.PER_ACTION,
            "per_checkpoint": RateLimitScope.PER_CHECKPOINT,
            "per_action_checkpoint": RateLimitScope.PER_ACTION_CHECKPOINT,
            "per_severity": RateLimitScope.PER_SEVERITY,
            "per_data_asset": RateLimitScope.PER_DATA_ASSET,
        }
        self._builder.with_scope(scope_map.get(scope.lower(), RateLimitScope.GLOBAL))
        return self

    def with_priority_bypass(self, threshold: str) -> "Self":
        """Enable priority bypass for notifications above threshold."""
        self._builder.with_priority_bypass(threshold)
        return self

    def with_action_limit(
        self,
        action_type: str,
        *,
        per_minute: int | None = None,
        per_hour: int | None = None,
        per_day: int | None = None,
    ) -> "Self":
        """Set custom limits for a specific action type."""
        self._builder.with_action_limit(
            action_type,
            per_minute=per_minute,
            per_hour=per_hour,
        )
        return self

    def with_severity_limit(
        self,
        severity: str,
        *,
        per_minute: int | None = None,
        per_hour: int | None = None,
    ) -> "Self":
        """Set custom limits for a severity level."""
        self._builder.with_severity_limit(
            severity,
            per_minute=per_minute,
            per_hour=per_hour,
        )
        return self

    def build(self) -> NotificationThrottler:
        """Build the throttler."""
        return self._builder.build()


def create_throttler_from_db_config(
    db_config: dict[str, Any],
) -> NotificationThrottler:
    """Create a NotificationThrottler from database configuration.

    Args:
        db_config: Configuration dictionary from database.

    Returns:
        NotificationThrottler instance.
    """
    builder = DashboardThrottlerBuilder()

    if db_config.get("per_minute_limit"):
        builder.with_per_minute_limit(db_config["per_minute_limit"])

    if db_config.get("per_hour_limit"):
        builder.with_per_hour_limit(db_config["per_hour_limit"])

    if db_config.get("per_day_limit"):
        builder.with_per_day_limit(db_config["per_day_limit"])

    if db_config.get("burst_multiplier"):
        builder.with_burst_allowance(db_config["burst_multiplier"])

    if db_config.get("algorithm"):
        builder.with_algorithm(db_config["algorithm"])

    if db_config.get("scope"):
        builder.with_scope(db_config["scope"])

    if db_config.get("priority_bypass") and db_config.get("priority_threshold"):
        builder.with_priority_bypass(db_config["priority_threshold"])

    # Action-specific limits
    for action_type, limits in db_config.get("action_limits", {}).items():
        builder.with_action_limit(
            action_type,
            per_minute=limits.get("per_minute"),
            per_hour=limits.get("per_hour"),
        )

    # Severity-specific limits
    for severity, limits in db_config.get("severity_limits", {}).items():
        builder.with_severity_limit(
            severity,
            per_minute=limits.get("per_minute"),
            per_hour=limits.get("per_hour"),
        )

    return builder.build()
