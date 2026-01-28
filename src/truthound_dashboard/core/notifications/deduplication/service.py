"""Dashboard-specific deduplication service using truthound.

This module provides adapters that integrate truthound's deduplication
system with the Dashboard's database configuration.
"""

from __future__ import annotations

from typing import Any

from truthound.checkpoint.deduplication import (
    NotificationDeduplicator,
    DeduplicationConfig,
    InMemoryDeduplicationStore,
    TimeWindow,
    DeduplicationPolicy,
)


class DashboardDeduplicationService:
    """Dashboard-specific deduplication service.

    Wraps truthound's NotificationDeduplicator and provides integration
    with the Dashboard's database configuration.

    Example:
        service = DashboardDeduplicationService()
        await service.initialize_from_db(session)

        if not service.is_duplicate(checkpoint_result, "slack"):
            await send_notification()
    """

    def __init__(self) -> None:
        """Initialize the service with default configuration."""
        self._deduplicator: NotificationDeduplicator | None = None
        self._config: DeduplicationConfig | None = None

    @property
    def deduplicator(self) -> NotificationDeduplicator:
        """Get the underlying truthound deduplicator."""
        if self._deduplicator is None:
            # Create with default config
            self._config = DeduplicationConfig(
                enabled=True,
                policy=DeduplicationPolicy.SEVERITY,
                default_window=TimeWindow(minutes=5),
            )
            self._deduplicator = NotificationDeduplicator(
                store=InMemoryDeduplicationStore(),
                config=self._config,
            )
        return self._deduplicator

    def configure(
        self,
        *,
        enabled: bool = True,
        policy: str = "severity",
        default_window_seconds: int = 300,
        action_windows: dict[str, int] | None = None,
        severity_windows: dict[str, int] | None = None,
    ) -> None:
        """Configure the deduplication service.

        Args:
            enabled: Whether deduplication is enabled.
            policy: Policy name (none, basic, severity, issue_based, strict).
            default_window_seconds: Default window in seconds.
            action_windows: Per-action windows in seconds.
            severity_windows: Per-severity windows in seconds.
        """
        # Map policy string to enum
        policy_map = {
            "none": DeduplicationPolicy.NONE,
            "basic": DeduplicationPolicy.BASIC,
            "severity": DeduplicationPolicy.SEVERITY,
            "issue_based": DeduplicationPolicy.ISSUE_BASED,
            "strict": DeduplicationPolicy.STRICT,
        }
        policy_enum = policy_map.get(policy.lower(), DeduplicationPolicy.SEVERITY)

        # Convert action windows
        action_window_map = {}
        if action_windows:
            for action_type, seconds in action_windows.items():
                action_window_map[action_type] = TimeWindow(seconds=seconds)

        # Convert severity windows
        severity_window_map = {}
        if severity_windows:
            for severity, seconds in severity_windows.items():
                severity_window_map[severity] = TimeWindow(seconds=seconds)

        self._config = DeduplicationConfig(
            enabled=enabled,
            policy=policy_enum,
            default_window=TimeWindow(seconds=default_window_seconds),
            action_windows=action_window_map,
            severity_windows=severity_window_map,
        )

        self._deduplicator = NotificationDeduplicator(
            store=InMemoryDeduplicationStore(),
            config=self._config,
        )

    def is_duplicate(
        self,
        checkpoint_result: Any,
        action_type: str,
        severity: str | None = None,
    ) -> bool:
        """Check if a notification would be a duplicate.

        Args:
            checkpoint_result: The checkpoint result object.
            action_type: The action type (slack, email, etc.).
            severity: Optional severity level.

        Returns:
            True if this would be a duplicate notification.
        """
        return self.deduplicator.is_duplicate(
            checkpoint_result,
            action_type,
            severity=severity,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get deduplication statistics.

        Returns:
            Dictionary with statistics.
        """
        stats = self.deduplicator.get_stats()
        return {
            "total_evaluated": stats.total_evaluated,
            "suppressed": stats.suppressed,
            "suppression_ratio": stats.suppression_ratio,
            "active_fingerprints": stats.active_fingerprints,
        }


def create_deduplication_config_from_db(
    db_config: dict[str, Any],
) -> DeduplicationConfig:
    """Create a DeduplicationConfig from database configuration.

    Args:
        db_config: Configuration dictionary from database.

    Returns:
        DeduplicationConfig for truthound's deduplicator.
    """
    policy_map = {
        "none": DeduplicationPolicy.NONE,
        "basic": DeduplicationPolicy.BASIC,
        "severity": DeduplicationPolicy.SEVERITY,
        "issue_based": DeduplicationPolicy.ISSUE_BASED,
        "strict": DeduplicationPolicy.STRICT,
    }

    policy = db_config.get("policy", "severity")
    policy_enum = policy_map.get(policy.lower(), DeduplicationPolicy.SEVERITY)

    # Build action windows
    action_windows = {}
    for action_type, seconds in db_config.get("action_windows", {}).items():
        action_windows[action_type] = TimeWindow(seconds=seconds)

    # Build severity windows
    severity_windows = {}
    for severity, seconds in db_config.get("severity_windows", {}).items():
        severity_windows[severity] = TimeWindow(seconds=seconds)

    return DeduplicationConfig(
        enabled=db_config.get("enabled", True),
        policy=policy_enum,
        default_window=TimeWindow(seconds=db_config.get("window_seconds", 300)),
        action_windows=action_windows,
        severity_windows=severity_windows,
    )
