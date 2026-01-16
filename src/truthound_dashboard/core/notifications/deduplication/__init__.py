"""Notification deduplication system.

This module provides a flexible deduplication system to prevent
sending duplicate notifications within configurable time windows.

Features:
    - 4 window strategies (sliding, tumbling, session, adaptive)
    - 6 deduplication policies (none, basic, severity, issue_based, strict, custom)
    - Pluggable storage backends (in-memory, SQLite)
    - Fingerprint-based duplicate detection

Example:
    from truthound_dashboard.core.notifications.deduplication import (
        NotificationDeduplicator,
        InMemoryDeduplicationStore,
        DeduplicationPolicy,
        TimeWindow,
    )

    # Create deduplicator
    deduplicator = NotificationDeduplicator(
        store=InMemoryDeduplicationStore(),
        default_window=TimeWindow(seconds=300),
        policy=DeduplicationPolicy.SEVERITY,
    )

    # Generate fingerprint and check
    fingerprint = deduplicator.generate_fingerprint(
        checkpoint_name="daily_check",
        action_type="slack",
        severity="high",
    )

    if not deduplicator.is_duplicate(fingerprint):
        await send_notification()
        deduplicator.mark_sent(fingerprint)
"""

from .policies import DeduplicationPolicy, FingerprintGenerator
from .service import NotificationDeduplicator, TimeWindow
from .stores import (
    BaseDeduplicationStore,
    InMemoryDeduplicationStore,
    SQLiteDeduplicationStore,
)
from .strategies import (
    AdaptiveWindowStrategy,
    BaseWindowStrategy,
    SessionWindowStrategy,
    SlidingWindowStrategy,
    StrategyRegistry,
    TumblingWindowStrategy,
)

__all__ = [
    # Stores
    "BaseDeduplicationStore",
    "InMemoryDeduplicationStore",
    "SQLiteDeduplicationStore",
    # Strategies
    "BaseWindowStrategy",
    "SlidingWindowStrategy",
    "TumblingWindowStrategy",
    "SessionWindowStrategy",
    "AdaptiveWindowStrategy",
    "StrategyRegistry",
    # Policies
    "DeduplicationPolicy",
    "FingerprintGenerator",
    # Service
    "NotificationDeduplicator",
    "TimeWindow",
]
