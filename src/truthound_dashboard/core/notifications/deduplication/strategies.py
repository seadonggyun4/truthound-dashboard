"""Window strategies for deduplication.

This module provides different windowing strategies that determine
how the deduplication time window is calculated.

Strategies:
    - SlidingWindowStrategy: Rolling time window from last occurrence
    - TumblingWindowStrategy: Fixed non-overlapping time windows
    - SessionWindowStrategy: Gap-based windows for event bursts
    - AdaptiveWindowStrategy: Dynamic window sizing based on load

Each strategy can be configured with different parameters to
suit various use cases.
"""

from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar


class StrategyRegistry:
    """Registry for window strategies.

    Provides plugin architecture for custom strategy implementations.
    """

    _strategies: ClassVar[dict[str, type["BaseWindowStrategy"]]] = {}

    @classmethod
    def register(cls, strategy_type: str):
        """Decorator to register a strategy type."""

        def decorator(strategy_class: type["BaseWindowStrategy"]) -> type["BaseWindowStrategy"]:
            strategy_class.strategy_type = strategy_type
            cls._strategies[strategy_type] = strategy_class
            return strategy_class

        return decorator

    @classmethod
    def get(cls, strategy_type: str) -> type["BaseWindowStrategy"] | None:
        """Get a registered strategy class by type."""
        return cls._strategies.get(strategy_type)

    @classmethod
    def create(cls, strategy_type: str, **params: Any) -> "BaseWindowStrategy | None":
        """Create a strategy instance by type."""
        strategy_class = cls.get(strategy_type)
        if strategy_class is None:
            return None
        return strategy_class(**params)

    @classmethod
    def list_types(cls) -> list[str]:
        """Get list of registered strategy types."""
        return list(cls._strategies.keys())


@dataclass
class BaseWindowStrategy(ABC):
    """Abstract base class for window strategies.

    Strategies determine how the deduplication window is calculated
    for a given fingerprint and context.
    """

    strategy_type: ClassVar[str] = "base"

    @abstractmethod
    def get_window_seconds(
        self,
        fingerprint: str,
        context: dict[str, Any] | None = None,
    ) -> int:
        """Calculate the window duration in seconds.

        Args:
            fingerprint: The notification fingerprint.
            context: Optional context for window calculation.

        Returns:
            Window duration in seconds.
        """
        ...

    @abstractmethod
    def get_window_key(
        self,
        fingerprint: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Generate a window-specific key for the fingerprint.

        Used by tumbling windows to align entries to window boundaries.

        Args:
            fingerprint: The notification fingerprint.
            timestamp: Optional timestamp (defaults to now).

        Returns:
            Window-aligned key.
        """
        ...


@StrategyRegistry.register("sliding")
@dataclass
class SlidingWindowStrategy(BaseWindowStrategy):
    """Sliding window strategy.

    The window slides with each occurrence - duplicates are suppressed
    if they occur within `window_seconds` of the last occurrence.

    This is the most common strategy for real-time deduplication.

    Attributes:
        window_seconds: Base window duration in seconds.
    """

    window_seconds: int = 300

    def get_window_seconds(
        self,
        fingerprint: str,
        context: dict[str, Any] | None = None,
    ) -> int:
        """Return the configured window duration."""
        return self.window_seconds

    def get_window_key(
        self,
        fingerprint: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Return the fingerprint unchanged (no window alignment)."""
        return fingerprint


@StrategyRegistry.register("tumbling")
@dataclass
class TumblingWindowStrategy(BaseWindowStrategy):
    """Tumbling window strategy.

    The window is divided into fixed, non-overlapping periods.
    All events within the same period share the same window.

    Useful for batch-style deduplication where you want at most
    one notification per time period.

    Attributes:
        window_seconds: Duration of each tumbling window.
        align_to: What to align windows to ('minute', 'hour', 'day').
    """

    window_seconds: int = 300
    align_to: str = "minute"

    def get_window_seconds(
        self,
        fingerprint: str,
        context: dict[str, Any] | None = None,
    ) -> int:
        """Return the configured window duration."""
        return self.window_seconds

    def get_window_key(
        self,
        fingerprint: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Generate window-aligned key.

        Aligns the fingerprint to the start of its tumbling window.
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Calculate window start
        ts = timestamp.timestamp()
        window_start = int(ts // self.window_seconds) * self.window_seconds

        return f"{fingerprint}:{window_start}"


@StrategyRegistry.register("session")
@dataclass
class SessionWindowStrategy(BaseWindowStrategy):
    """Session window strategy.

    Groups events into sessions based on gaps between occurrences.
    A new session starts if no event occurs within `gap_seconds`.

    Useful for handling event bursts where you want to deduplicate
    within a burst but allow new notifications after quiet periods.

    Attributes:
        gap_seconds: Maximum gap between events in same session.
        max_session_seconds: Maximum session duration.
    """

    gap_seconds: int = 60
    max_session_seconds: int = 3600

    _session_starts: dict[str, float] = field(default_factory=dict)
    _last_events: dict[str, float] = field(default_factory=dict)

    def get_window_seconds(
        self,
        fingerprint: str,
        context: dict[str, Any] | None = None,
    ) -> int:
        """Calculate remaining session window."""
        now = time.time()
        last_event = self._last_events.get(fingerprint, 0)

        # Check if session is still active
        if now - last_event > self.gap_seconds:
            # New session
            return 0

        # Return remaining session time
        session_start = self._session_starts.get(fingerprint, now)
        elapsed = now - session_start
        remaining = self.max_session_seconds - elapsed

        return max(0, int(remaining))

    def get_window_key(
        self,
        fingerprint: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Generate session-aligned key."""
        now = time.time() if timestamp is None else timestamp.timestamp()
        last_event = self._last_events.get(fingerprint, 0)

        # Check if this is a new session
        if now - last_event > self.gap_seconds:
            self._session_starts[fingerprint] = now
            self._last_events[fingerprint] = now
            return f"{fingerprint}:session:{int(now)}"

        # Same session
        self._last_events[fingerprint] = now
        session_start = self._session_starts.get(fingerprint, now)
        return f"{fingerprint}:session:{int(session_start)}"


@StrategyRegistry.register("adaptive")
@dataclass
class AdaptiveWindowStrategy(BaseWindowStrategy):
    """Adaptive window strategy.

    Dynamically adjusts window size based on event frequency.
    High-frequency events get longer windows, low-frequency get shorter.

    This helps prevent notification fatigue during incidents while
    maintaining responsiveness during normal operations.

    Attributes:
        min_window_seconds: Minimum window duration.
        max_window_seconds: Maximum window duration.
        scale_factor: How quickly window grows with frequency.
        decay_seconds: Time for window to decay back to minimum.
    """

    min_window_seconds: int = 60
    max_window_seconds: int = 3600
    scale_factor: float = 2.0
    decay_seconds: int = 1800

    _event_counts: dict[str, int] = field(default_factory=dict)
    _last_events: dict[str, float] = field(default_factory=dict)

    def get_window_seconds(
        self,
        fingerprint: str,
        context: dict[str, Any] | None = None,
    ) -> int:
        """Calculate adaptive window based on event frequency."""
        now = time.time()
        last_event = self._last_events.get(fingerprint, 0)
        count = self._event_counts.get(fingerprint, 0)

        # Decay count over time
        if last_event > 0:
            elapsed = now - last_event
            decay_factor = max(0, 1 - (elapsed / self.decay_seconds))
            count = int(count * decay_factor)

        # Calculate window based on count
        if count == 0:
            window = self.min_window_seconds
        else:
            # Logarithmic scaling
            scale = 1 + math.log(1 + count) * self.scale_factor
            window = int(self.min_window_seconds * scale)

        # Clamp to bounds
        return min(self.max_window_seconds, max(self.min_window_seconds, window))

    def get_window_key(
        self,
        fingerprint: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Return fingerprint and update counts."""
        now = time.time() if timestamp is None else timestamp.timestamp()

        # Update event tracking
        count = self._event_counts.get(fingerprint, 0)
        self._event_counts[fingerprint] = count + 1
        self._last_events[fingerprint] = now

        return fingerprint

    def reset(self, fingerprint: str) -> None:
        """Reset tracking for a fingerprint."""
        self._event_counts.pop(fingerprint, None)
        self._last_events.pop(fingerprint, None)
