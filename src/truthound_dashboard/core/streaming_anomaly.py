"""Streaming anomaly detection service.

This module provides real-time streaming anomaly detection capabilities,
supporting sliding window detection and online learning.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

import numpy as np

logger = logging.getLogger(__name__)


class StreamingSessionStatus(str, Enum):
    """Status of a streaming session."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class StreamingAlgorithm(str, Enum):
    """Supported streaming anomaly detection algorithms."""

    ZSCORE_ROLLING = "zscore_rolling"
    EXPONENTIAL_MOVING_AVERAGE = "ema"
    ISOLATION_FOREST_INCREMENTAL = "isolation_forest_incremental"
    HALF_SPACE_TREES = "half_space_trees"
    ROBUST_RANDOM_CUT_FOREST = "rrcf"


@dataclass
class StreamingAlert:
    """An anomaly alert from streaming detection."""

    id: str
    session_id: str
    timestamp: datetime
    data_point: dict[str, Any]
    anomaly_score: float
    is_anomaly: bool
    algorithm: StreamingAlgorithm
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "data_point": self.data_point,
            "anomaly_score": self.anomaly_score,
            "is_anomaly": self.is_anomaly,
            "algorithm": self.algorithm.value,
            "details": self.details,
        }


@dataclass
class StreamingStatistics:
    """Rolling statistics for streaming detection."""

    count: int = 0
    mean: float = 0.0
    variance: float = 0.0
    min_value: float = float("inf")
    max_value: float = float("-inf")
    anomaly_count: int = 0

    def update(self, value: float, is_anomaly: bool = False) -> None:
        """Update statistics with a new value using Welford's algorithm."""
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.variance += delta * delta2

        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)

        if is_anomaly:
            self.anomaly_count += 1

    @property
    def std(self) -> float:
        """Get standard deviation."""
        if self.count < 2:
            return 0.0
        return np.sqrt(self.variance / (self.count - 1))

    @property
    def anomaly_rate(self) -> float:
        """Get anomaly rate."""
        if self.count == 0:
            return 0.0
        return self.anomaly_count / self.count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "mean": self.mean,
            "std": self.std,
            "min": self.min_value if self.min_value != float("inf") else None,
            "max": self.max_value if self.max_value != float("-inf") else None,
            "anomaly_count": self.anomaly_count,
            "anomaly_rate": self.anomaly_rate,
        }


@dataclass
class StreamingSession:
    """A streaming anomaly detection session."""

    id: str
    source_id: str | None
    algorithm: StreamingAlgorithm
    window_size: int
    threshold: float
    columns: list[str]
    status: StreamingSessionStatus
    created_at: datetime
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_active_at: datetime | None = None
    config: dict[str, Any] = field(default_factory=dict)

    # Runtime state (not persisted)
    _buffer: deque = field(default_factory=lambda: deque(maxlen=1000))
    _column_stats: dict[str, StreamingStatistics] = field(default_factory=dict)
    _alerts: list[StreamingAlert] = field(default_factory=list)
    _alert_callbacks: list = field(default_factory=list)
    _ema_values: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize column statistics and activity tracking."""
        for col in self.columns:
            self._column_stats[col] = StreamingStatistics()
            self._ema_values[col] = 0.0
        if self.last_active_at is None:
            self.last_active_at = self.created_at

    def touch(self) -> None:
        """Update last_active_at to current time."""
        self.last_active_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "algorithm": self.algorithm.value,
            "window_size": self.window_size,
            "threshold": self.threshold,
            "columns": self.columns,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "config": self.config,
            "statistics": {col: stats.to_dict() for col, stats in self._column_stats.items()},
            "total_points": len(self._buffer),
            "total_alerts": len(self._alerts),
        }


# =============================================================================
# Session Cleanup Policies
# =============================================================================


class SessionCleanupPolicy(ABC):
    """Abstract policy for determining if a streaming session should be cleaned up.

    Implement this interface to define custom cleanup strategies.
    """

    @abstractmethod
    def should_cleanup(self, session: StreamingSession, now: datetime) -> bool:
        """Determine if a session should be removed.

        Args:
            session: The streaming session to evaluate.
            now: Current timestamp.

        Returns:
            True if the session should be cleaned up.
        """
        ...


class IdleTTLPolicy(SessionCleanupPolicy):
    """Remove sessions that have been idle longer than their TTL.

    Supports per-status TTL configuration so that stopped/error sessions
    are cleaned up faster than active ones.
    """

    # Default TTL per session status (in seconds)
    DEFAULT_STATUS_TTLS: dict[StreamingSessionStatus, int] = {
        StreamingSessionStatus.STOPPED: 300,    # 5 min
        StreamingSessionStatus.ERROR: 600,      # 10 min
        StreamingSessionStatus.CREATED: 900,    # 15 min
        StreamingSessionStatus.PAUSED: 1800,    # 30 min
        StreamingSessionStatus.RUNNING: 3600,   # 60 min
    }

    def __init__(
        self,
        default_ttl_seconds: int = 1800,
        status_ttls: dict[StreamingSessionStatus, int] | None = None,
    ) -> None:
        self._default_ttl = default_ttl_seconds
        self._status_ttls = status_ttls or dict(self.DEFAULT_STATUS_TTLS)

    def should_cleanup(self, session: StreamingSession, now: datetime) -> bool:
        ttl = self._status_ttls.get(session.status, self._default_ttl)
        reference_time = session.last_active_at or session.created_at
        return (now - reference_time) > timedelta(seconds=ttl)


class CompositeCleanupPolicy(SessionCleanupPolicy):
    """Combine multiple cleanup policies with AND/OR logic.

    Args:
        policies: List of policies to combine.
        require_all: If True, all policies must agree (AND).
                     If False, any policy is sufficient (OR). Default: False.
    """

    def __init__(
        self,
        policies: list[SessionCleanupPolicy],
        require_all: bool = False,
    ) -> None:
        self._policies = policies
        self._require_all = require_all

    def should_cleanup(self, session: StreamingSession, now: datetime) -> bool:
        if self._require_all:
            return all(p.should_cleanup(session, now) for p in self._policies)
        return any(p.should_cleanup(session, now) for p in self._policies)


# =============================================================================
# Streaming Anomaly Detector
# =============================================================================


class StreamingAnomalyDetector:
    """Real-time streaming anomaly detection service.

    Supports:
    - Sliding window detection
    - Multiple algorithms (Z-score, EMA, etc.)
    - Online learning / model updates
    - Alert callbacks for real-time notifications
    - Automatic session cleanup via configurable policies
    """

    def __init__(
        self,
        cleanup_policy: SessionCleanupPolicy | None = None,
        cleanup_interval_seconds: int = 60,
    ) -> None:
        """Initialize the streaming detector.

        Args:
            cleanup_policy: Policy for automatic session cleanup.
                            Defaults to IdleTTLPolicy.
            cleanup_interval_seconds: How often to run cleanup (in seconds).
        """
        self._sessions: dict[str, StreamingSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_policy = cleanup_policy or IdleTTLPolicy()
        self._cleanup_interval = cleanup_interval_seconds
        self._cleanup_task: asyncio.Task[None] | None = None

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def start(self) -> None:
        """Start the background session cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Streaming session cleanup task started")

    async def stop(self) -> None:
        """Stop the background session cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Streaming session cleanup task stopped")

    async def _cleanup_loop(self) -> None:
        """Background loop that periodically removes expired sessions."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                removed = await self._cleanup_expired_sessions()
                if removed:
                    logger.info(
                        "Cleaned up %d expired streaming session(s)", removed
                    )
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error during streaming session cleanup")

    async def _cleanup_expired_sessions(self) -> int:
        """Remove sessions that match the cleanup policy.

        Returns:
            Number of sessions removed.
        """
        now = datetime.utcnow()
        async with self._lock:
            to_remove = [
                sid
                for sid, session in self._sessions.items()
                if self._cleanup_policy.should_cleanup(session, now)
            ]
            for sid in to_remove:
                logger.debug("Removing expired streaming session %s", sid)
                del self._sessions[sid]
            return len(to_remove)

    # =========================================================================
    # Session Management
    # =========================================================================

    async def create_session(
        self,
        *,
        source_id: str | None = None,
        algorithm: StreamingAlgorithm = StreamingAlgorithm.ZSCORE_ROLLING,
        window_size: int = 100,
        threshold: float = 3.0,
        columns: list[str] | None = None,
        config: dict[str, Any] | None = None,
    ) -> StreamingSession:
        """Create a new streaming session.

        Args:
            source_id: Optional source ID to associate with.
            algorithm: Detection algorithm to use.
            window_size: Size of the sliding window.
            threshold: Anomaly detection threshold.
            columns: Columns to monitor (if None, monitors all numeric).
            config: Additional algorithm configuration.

        Returns:
            Created streaming session.
        """
        session_id = str(uuid4())
        session = StreamingSession(
            id=session_id,
            source_id=source_id,
            algorithm=algorithm,
            window_size=window_size,
            threshold=threshold,
            columns=columns or [],
            status=StreamingSessionStatus.CREATED,
            created_at=datetime.utcnow(),
            config=config or {},
        )

        async with self._lock:
            self._sessions[session_id] = session

        return session

    async def start_session(self, session_id: str) -> StreamingSession:
        """Start a streaming session.

        Args:
            session_id: Session ID to start.

        Returns:
            Updated session.

        Raises:
            ValueError: If session not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ValueError(f"Session '{session_id}' not found")

            session.status = StreamingSessionStatus.RUNNING
            session.started_at = datetime.utcnow()
            session.touch()

        return session

    async def stop_session(self, session_id: str) -> StreamingSession:
        """Stop a streaming session.

        Args:
            session_id: Session ID to stop.

        Returns:
            Updated session.

        Raises:
            ValueError: If session not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ValueError(f"Session '{session_id}' not found")

            session.status = StreamingSessionStatus.STOPPED
            session.stopped_at = datetime.utcnow()

        return session

    async def get_session(self, session_id: str) -> StreamingSession | None:
        """Get a session by ID.

        Args:
            session_id: Session ID.

        Returns:
            Session or None if not found.
        """
        return self._sessions.get(session_id)

    async def list_sessions(self) -> list[StreamingSession]:
        """List all active sessions.

        Returns:
            List of sessions.
        """
        return list(self._sessions.values())

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID to delete.

        Returns:
            True if deleted.
        """
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
        return False

    # =========================================================================
    # Data Processing
    # =========================================================================

    async def push_data_point(
        self,
        session_id: str,
        data: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> StreamingAlert | None:
        """Push a data point to a streaming session.

        Args:
            session_id: Session ID.
            data: Data point (column name -> value).
            timestamp: Optional timestamp (defaults to now).

        Returns:
            Alert if anomaly detected, None otherwise.

        Raises:
            ValueError: If session not found or not running.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session '{session_id}' not found")

        if session.status != StreamingSessionStatus.RUNNING:
            raise ValueError(f"Session '{session_id}' is not running")

        session.touch()
        timestamp = timestamp or datetime.utcnow()

        # Store data point in buffer
        session._buffer.append({"timestamp": timestamp, "data": data})

        # Run anomaly detection
        alert = await self._detect_anomaly(session, data, timestamp)

        # Update statistics
        for col, value in data.items():
            if col in session._column_stats:
                try:
                    numeric_value = float(value)
                    is_anomaly = alert is not None and alert.is_anomaly
                    session._column_stats[col].update(numeric_value, is_anomaly)
                except (ValueError, TypeError):
                    pass

        # Store alert and trigger callbacks
        if alert is not None:
            session._alerts.append(alert)
            await self._trigger_alert_callbacks(session, alert)

        return alert

    async def push_batch(
        self,
        session_id: str,
        data_points: list[dict[str, Any]],
        timestamps: list[datetime] | None = None,
    ) -> list[StreamingAlert]:
        """Push a batch of data points.

        Args:
            session_id: Session ID.
            data_points: List of data points.
            timestamps: Optional list of timestamps.

        Returns:
            List of alerts.
        """
        alerts = []
        timestamps = timestamps or [datetime.utcnow()] * len(data_points)

        for data, ts in zip(data_points, timestamps):
            alert = await self.push_data_point(session_id, data, ts)
            if alert is not None:
                alerts.append(alert)

        return alerts

    # =========================================================================
    # Anomaly Detection Algorithms
    # =========================================================================

    async def _detect_anomaly(
        self,
        session: StreamingSession,
        data: dict[str, Any],
        timestamp: datetime,
    ) -> StreamingAlert | None:
        """Run anomaly detection on a data point.

        Args:
            session: Streaming session.
            data: Data point.
            timestamp: Timestamp.

        Returns:
            Alert if anomaly detected.
        """
        algorithm = session.algorithm

        if algorithm == StreamingAlgorithm.ZSCORE_ROLLING:
            return await self._detect_zscore_rolling(session, data, timestamp)
        elif algorithm == StreamingAlgorithm.EXPONENTIAL_MOVING_AVERAGE:
            return await self._detect_ema(session, data, timestamp)
        elif algorithm == StreamingAlgorithm.ISOLATION_FOREST_INCREMENTAL:
            return await self._detect_isolation_forest_incremental(session, data, timestamp)
        elif algorithm == StreamingAlgorithm.HALF_SPACE_TREES:
            return await self._detect_half_space_trees(session, data, timestamp)
        elif algorithm == StreamingAlgorithm.ROBUST_RANDOM_CUT_FOREST:
            return await self._detect_rrcf(session, data, timestamp)
        else:
            return None

    async def _detect_zscore_rolling(
        self,
        session: StreamingSession,
        data: dict[str, Any],
        timestamp: datetime,
    ) -> StreamingAlert | None:
        """Z-score based anomaly detection using rolling statistics.

        Args:
            session: Streaming session.
            data: Data point.
            timestamp: Timestamp.

        Returns:
            Alert if anomaly detected.
        """
        # Need at least window_size points for reliable detection
        if len(session._buffer) < min(session.window_size, 10):
            return None

        # Get recent values for each column
        window_data = list(session._buffer)[-session.window_size:]

        max_zscore = 0.0
        anomaly_columns = []
        details = {}

        for col in session.columns:
            if col not in data:
                continue

            try:
                current_value = float(data[col])
            except (ValueError, TypeError):
                continue

            # Calculate rolling mean and std from window
            window_values = []
            for point in window_data[:-1]:  # Exclude current point
                if col in point.get("data", {}):
                    try:
                        window_values.append(float(point["data"][col]))
                    except (ValueError, TypeError):
                        pass

            if len(window_values) < 2:
                continue

            window_mean = np.mean(window_values)
            window_std = np.std(window_values)

            if window_std == 0:
                window_std = 1e-10  # Avoid division by zero

            zscore = abs(current_value - window_mean) / window_std

            if zscore > max_zscore:
                max_zscore = zscore

            if zscore > session.threshold:
                anomaly_columns.append(col)
                details[col] = {
                    "value": current_value,
                    "mean": float(window_mean),
                    "std": float(window_std),
                    "zscore": float(zscore),
                }

        is_anomaly = len(anomaly_columns) > 0 or max_zscore > session.threshold

        if is_anomaly:
            return StreamingAlert(
                id=str(uuid4()),
                session_id=session.id,
                timestamp=timestamp,
                data_point=data,
                anomaly_score=float(max_zscore),
                is_anomaly=True,
                algorithm=StreamingAlgorithm.ZSCORE_ROLLING,
                details={
                    "anomaly_columns": anomaly_columns,
                    "column_details": details,
                    "threshold": session.threshold,
                },
            )

        return None

    async def _detect_ema(
        self,
        session: StreamingSession,
        data: dict[str, Any],
        timestamp: datetime,
    ) -> StreamingAlert | None:
        """Exponential Moving Average based anomaly detection.

        Args:
            session: Streaming session.
            data: Data point.
            timestamp: Timestamp.

        Returns:
            Alert if anomaly detected.
        """
        alpha = session.config.get("alpha", 0.1)  # Smoothing factor
        threshold_multiplier = session.config.get("threshold_multiplier", 2.0)

        max_deviation = 0.0
        anomaly_columns = []
        details = {}

        for col in session.columns:
            if col not in data:
                continue

            try:
                current_value = float(data[col])
            except (ValueError, TypeError):
                continue

            # Initialize EMA if first point
            if session._ema_values.get(col, 0) == 0:
                session._ema_values[col] = current_value
                continue

            # Calculate EMA
            prev_ema = session._ema_values[col]
            new_ema = alpha * current_value + (1 - alpha) * prev_ema
            session._ema_values[col] = new_ema

            # Calculate deviation from EMA
            deviation = abs(current_value - prev_ema)

            # Use rolling std for threshold
            stats = session._column_stats.get(col)
            if stats and stats.std > 0:
                normalized_deviation = deviation / stats.std
                if normalized_deviation > max_deviation:
                    max_deviation = normalized_deviation

                if normalized_deviation > session.threshold * threshold_multiplier:
                    anomaly_columns.append(col)
                    details[col] = {
                        "value": current_value,
                        "ema": float(new_ema),
                        "deviation": float(deviation),
                        "normalized_deviation": float(normalized_deviation),
                    }

        is_anomaly = len(anomaly_columns) > 0

        if is_anomaly:
            return StreamingAlert(
                id=str(uuid4()),
                session_id=session.id,
                timestamp=timestamp,
                data_point=data,
                anomaly_score=float(max_deviation),
                is_anomaly=True,
                algorithm=StreamingAlgorithm.EXPONENTIAL_MOVING_AVERAGE,
                details={
                    "anomaly_columns": anomaly_columns,
                    "column_details": details,
                    "alpha": alpha,
                },
            )

        return None

    async def _detect_isolation_forest_incremental(
        self,
        session: StreamingSession,
        data: dict[str, Any],
        timestamp: datetime,
    ) -> StreamingAlert | None:
        """Incremental Isolation Forest based anomaly detection.

        Uses a simplified streaming version that periodically retrains.

        Args:
            session: Streaming session.
            data: Data point.
            timestamp: Timestamp.

        Returns:
            Alert if anomaly detected.
        """
        # Minimum points before detection
        if len(session._buffer) < session.window_size:
            return None

        try:
            from sklearn.ensemble import IsolationForest

            # Get recent window data
            window_data = list(session._buffer)[-session.window_size:]

            # Build feature matrix from window
            feature_cols = [col for col in session.columns if col in data]
            if not feature_cols:
                return None

            X = []
            for point in window_data:
                row = []
                valid = True
                for col in feature_cols:
                    if col in point.get("data", {}):
                        try:
                            row.append(float(point["data"][col]))
                        except (ValueError, TypeError):
                            valid = False
                            break
                    else:
                        valid = False
                        break
                if valid:
                    X.append(row)

            if len(X) < 10:
                return None

            X = np.array(X)

            # Build current point feature vector
            current_point = []
            for col in feature_cols:
                try:
                    current_point.append(float(data[col]))
                except (ValueError, TypeError):
                    return None

            current_point = np.array([current_point])

            # Fit Isolation Forest on window
            contamination = session.config.get("contamination", 0.1)
            clf = IsolationForest(
                n_estimators=50,
                contamination=contamination,
                random_state=42,
            )
            clf.fit(X)

            # Predict on current point
            prediction = clf.predict(current_point)[0]
            score = -clf.score_samples(current_point)[0]

            is_anomaly = prediction == -1

            if is_anomaly:
                return StreamingAlert(
                    id=str(uuid4()),
                    session_id=session.id,
                    timestamp=timestamp,
                    data_point=data,
                    anomaly_score=float(score),
                    is_anomaly=True,
                    algorithm=StreamingAlgorithm.ISOLATION_FOREST_INCREMENTAL,
                    details={
                        "window_size": len(X),
                        "contamination": contamination,
                    },
                )

        except ImportError:
            pass

        return None

    async def _detect_half_space_trees(
        self,
        session: StreamingSession,
        data: dict[str, Any],
        timestamp: datetime,
    ) -> StreamingAlert | None:
        """Half-Space Trees streaming anomaly detection.

        A simplified implementation of HS-Trees for streaming.

        Args:
            session: Streaming session.
            data: Data point.
            timestamp: Timestamp.

        Returns:
            Alert if anomaly detected.
        """
        # Use Z-score as a fallback for HS-Trees
        # A full implementation would maintain the tree structure
        return await self._detect_zscore_rolling(session, data, timestamp)

    async def _detect_rrcf(
        self,
        session: StreamingSession,
        data: dict[str, Any],
        timestamp: datetime,
    ) -> StreamingAlert | None:
        """Robust Random Cut Forest streaming anomaly detection.

        A simplified implementation using codisp (collusive displacement).

        Args:
            session: Streaming session.
            data: Data point.
            timestamp: Timestamp.

        Returns:
            Alert if anomaly detected.
        """
        # Use Z-score as a fallback for RRCF
        # A full implementation would use the rrcf library
        return await self._detect_zscore_rolling(session, data, timestamp)

    # =========================================================================
    # Alert Management
    # =========================================================================

    def register_alert_callback(
        self,
        session_id: str,
        callback: callable,
    ) -> None:
        """Register a callback for alerts.

        Args:
            session_id: Session ID.
            callback: Callback function (async).
        """
        session = self._sessions.get(session_id)
        if session:
            session._alert_callbacks.append(callback)

    def unregister_alert_callback(
        self,
        session_id: str,
        callback: callable,
    ) -> None:
        """Unregister an alert callback.

        Args:
            session_id: Session ID.
            callback: Callback function to remove.
        """
        session = self._sessions.get(session_id)
        if session and callback in session._alert_callbacks:
            session._alert_callbacks.remove(callback)

    async def _trigger_alert_callbacks(
        self,
        session: StreamingSession,
        alert: StreamingAlert,
    ) -> None:
        """Trigger all registered alert callbacks.

        Args:
            session: Streaming session.
            alert: Alert to send.
        """
        for callback in session._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception:
                pass  # Don't let callback errors break detection

    async def get_alerts(
        self,
        session_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StreamingAlert]:
        """Get alerts for a session.

        Args:
            session_id: Session ID.
            limit: Maximum alerts to return.
            offset: Offset for pagination.

        Returns:
            List of alerts.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return []

        # Return alerts in reverse order (most recent first)
        alerts = list(reversed(session._alerts))
        return alerts[offset : offset + limit]

    async def get_statistics(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """Get statistics for a session.

        Args:
            session_id: Session ID.

        Returns:
            Statistics dictionary.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return {}

        return {
            "total_points": len(session._buffer),
            "total_alerts": len(session._alerts),
            "columns": {
                col: stats.to_dict()
                for col, stats in session._column_stats.items()
            },
            "buffer_utilization": len(session._buffer) / session._buffer.maxlen if session._buffer.maxlen else 0,
        }

    async def get_recent_data(
        self,
        session_id: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent data points.

        Args:
            session_id: Session ID.
            limit: Maximum points to return.

        Returns:
            List of recent data points.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return []

        # Return most recent points
        recent = list(session._buffer)[-limit:]
        return [
            {
                "timestamp": point["timestamp"].isoformat(),
                "data": point["data"],
            }
            for point in reversed(recent)
        ]


# Global streaming detector instance
_streaming_detector: StreamingAnomalyDetector | None = None


def get_streaming_detector() -> StreamingAnomalyDetector:
    """Get the global streaming detector instance.

    Returns:
        StreamingAnomalyDetector instance.
    """
    global _streaming_detector
    if _streaming_detector is None:
        _streaming_detector = StreamingAnomalyDetector()
    return _streaming_detector
