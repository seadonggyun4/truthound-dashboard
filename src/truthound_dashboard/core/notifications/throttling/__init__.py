"""Notification throttling using truthound.checkpoint.throttling.

This module provides rate limiting for notifications using truthound's
throttling infrastructure.

Key Components from truthound.checkpoint.throttling:
    - NotificationThrottler: High-level throttling service
    - ThrottlingConfig: Configuration for throttling
    - ThrottlerBuilder: Fluent builder API
    - RateLimit: Rate limit configuration
    - RateLimitScope: Scope of rate limit application
    - ThrottleStatus: Throttle result status

Throttler Types from truthound (5 types):
    - TokenBucketThrottler: Token bucket algorithm (allows bursts)
    - SlidingWindowThrottler: Sliding window algorithm (more accurate)
    - FixedWindowThrottler: Fixed window algorithm (simple)
    - CompositeThrottler: Multi-level rate limits
    - NoOpThrottler: Pass-through (for testing)

Example:
    from truthound.checkpoint.throttling import (
        ThrottlerBuilder,
        RateLimitScope,
    )

    # Build throttler with fluent API
    throttler = (
        ThrottlerBuilder()
        .with_per_minute_limit(10)
        .with_per_hour_limit(100)
        .with_per_day_limit(500)
        .with_burst_allowance(1.5)
        .with_scope(RateLimitScope.PER_ACTION)
        .with_priority_bypass("critical")
        .build()
    )

    # Check if allowed
    result = throttler.acquire(action_type="slack", checkpoint_name="my_check")
    if result.allowed:
        send_notification()
    else:
        print(f"Retry after {result.retry_after:.1f}s")
"""

# Re-export from truthound.checkpoint.throttling
from truthound.checkpoint.throttling import (
    NotificationThrottler,
    ThrottlingConfig,
    ThrottlerBuilder,
    ThrottlingMiddleware,
    throttled,
    RateLimit,
    RateLimitScope,
    TimeUnit,
    ThrottleStatus,
    ThrottleResult,
    ThrottlingKey,
)

# Throttler implementations
from truthound.checkpoint.throttling import (
    TokenBucketThrottler,
    SlidingWindowThrottler,
    FixedWindowThrottler,
    CompositeThrottler,
    NoOpThrottler,
)

# Storage
from truthound.checkpoint.throttling import InMemoryThrottlingStore

# Dashboard-specific adapters
from .builder import DashboardThrottlerBuilder

__all__ = [
    # truthound core
    "NotificationThrottler",
    "ThrottlingConfig",
    "ThrottlerBuilder",
    "ThrottlingMiddleware",
    "throttled",
    "RateLimit",
    "RateLimitScope",
    "TimeUnit",
    "ThrottleStatus",
    "ThrottleResult",
    "ThrottlingKey",
    # Throttler implementations
    "TokenBucketThrottler",
    "SlidingWindowThrottler",
    "FixedWindowThrottler",
    "CompositeThrottler",
    "NoOpThrottler",
    # Storage
    "InMemoryThrottlingStore",
    # Dashboard adapters
    "DashboardThrottlerBuilder",
]
