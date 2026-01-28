"""Notification deduplication using truthound.checkpoint.deduplication.

This module provides deduplication functionality to prevent sending
duplicate notifications, using truthound's deduplication infrastructure.

Key Components from truthound.checkpoint.deduplication:
    - NotificationDeduplicator: Main deduplication service
    - DeduplicationConfig: Configuration for deduplication
    - DeduplicationPolicy: Policy types (NONE, BASIC, SEVERITY, ISSUE_BASED, STRICT, CUSTOM)
    - TimeWindow: Time window configuration
    - WindowUnit: Time unit enumeration

Window Strategies from truthound:
    - SlidingWindowStrategy: Fixed time window
    - TumblingWindowStrategy: Non-overlapping fixed buckets
    - SessionWindowStrategy: Event-based sessions

Storage Backends from truthound:
    - InMemoryDeduplicationStore: Single-process storage
    - RedisStreamsDeduplicationStore: Distributed storage

Example:
    from truthound.checkpoint.deduplication import (
        NotificationDeduplicator,
        DeduplicationConfig,
        InMemoryDeduplicationStore,
        TimeWindow,
        DeduplicationPolicy,
    )

    # Configure deduplication
    config = DeduplicationConfig(
        policy=DeduplicationPolicy.SEVERITY,
        default_window=TimeWindow(minutes=5),
        action_windows={
            "pagerduty": TimeWindow(hours=1),
            "slack": TimeWindow(minutes=5),
        },
    )

    # Create deduplicator
    deduplicator = NotificationDeduplicator(
        store=InMemoryDeduplicationStore(),
        config=config,
    )

    # Check for duplicates
    result = deduplicator.check(checkpoint_result, "slack", severity="high")
    if result.should_send:
        await action.execute(checkpoint_result)
        deduplicator.mark_sent(result.fingerprint)
"""

# Re-export from truthound.checkpoint.deduplication
from truthound.checkpoint.deduplication import (
    NotificationDeduplicator,
    DeduplicationConfig,
    InMemoryDeduplicationStore,
    TimeWindow,
    WindowUnit,
    DeduplicationPolicy,
    NotificationFingerprint,
    DeduplicationMiddleware,
    deduplicated,
)

# Window strategies
from truthound.checkpoint.deduplication import (
    SlidingWindowStrategy,
    TumblingWindowStrategy,
    SessionWindowStrategy,
)

# Redis store (optional)
try:
    from truthound.checkpoint.deduplication import RedisStreamsDeduplicationStore
    REDIS_AVAILABLE = True
except ImportError:
    RedisStreamsDeduplicationStore = None  # type: ignore
    REDIS_AVAILABLE = False

# Dashboard-specific adapters
from .service import (
    DashboardDeduplicationService,
    create_deduplication_config_from_db,
)

__all__ = [
    # truthound core
    "NotificationDeduplicator",
    "DeduplicationConfig",
    "InMemoryDeduplicationStore",
    "TimeWindow",
    "WindowUnit",
    "DeduplicationPolicy",
    "NotificationFingerprint",
    "DeduplicationMiddleware",
    "deduplicated",
    # Window strategies
    "SlidingWindowStrategy",
    "TumblingWindowStrategy",
    "SessionWindowStrategy",
    # Redis (optional)
    "RedisStreamsDeduplicationStore",
    "REDIS_AVAILABLE",
    # Dashboard adapters
    "DashboardDeduplicationService",
    "create_deduplication_config_from_db",
]
