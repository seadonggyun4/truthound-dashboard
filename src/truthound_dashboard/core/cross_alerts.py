"""Cross-alert correlation service.

This module provides services for cross-feature integration between
Anomaly Detection and Drift Monitoring alerts.

When anomaly rates spike, it automatically checks for drift and vice versa.

NOTE: This module has been updated to use persistent DB storage instead of
in-memory storage for configurations, correlations, and trigger events.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from truthound_dashboard.db.models import (
        AnomalyDetection,
        CrossAlertConfig,
        CrossAlertCorrelation,
        CrossAlertTriggerEvent,
        DriftAlert,
        DriftComparison,
        Source,
    )

logger = logging.getLogger(__name__)


# Default thresholds for new configs
DEFAULT_THRESHOLDS = {
    "anomaly_rate_threshold": 0.1,
    "anomaly_count_threshold": 10,
    "drift_percentage_threshold": 10.0,
    "drift_columns_threshold": 2,
}


class CrossAlertService:
    """Service for cross-alert correlation between anomaly and drift detection.

    Provides functionality for:
    - Finding correlated alerts between anomaly and drift detection
    - Auto-triggering drift checks when anomalies spike
    - Auto-triggering anomaly checks when drift is detected
    - Managing auto-trigger configuration

    All data is persisted to database using CrossAlertConfig,
    CrossAlertCorrelation, and CrossAlertTriggerEvent models.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session

    # =========================================================================
    # Configuration Management (DB-backed)
    # =========================================================================

    async def get_config(self, source_id: str | None = None) -> dict[str, Any]:
        """Get auto-trigger configuration from database.

        Args:
            source_id: Source ID for source-specific config, None for global.

        Returns:
            Configuration dictionary.
        """
        from truthound_dashboard.db.models import CrossAlertConfig

        # Try to get source-specific config
        if source_id:
            result = await self.session.execute(
                select(CrossAlertConfig).where(
                    CrossAlertConfig.source_id == source_id
                )
            )
            config = result.scalar_one_or_none()
            if config:
                return self._config_to_dict(config)

        # Fall back to global config (source_id is None)
        result = await self.session.execute(
            select(CrossAlertConfig).where(CrossAlertConfig.source_id.is_(None))
        )
        config = result.scalar_one_or_none()

        if config:
            return self._config_to_dict(config)

        # Return defaults if no config exists
        return {
            "id": None,
            "source_id": source_id,
            "enabled": True,
            "trigger_drift_on_anomaly": True,
            "trigger_anomaly_on_drift": True,
            "thresholds": DEFAULT_THRESHOLDS.copy(),
            "notify_on_correlation": True,
            "notification_channel_ids": None,
            "cooldown_seconds": 300,
            "last_anomaly_trigger_at": None,
            "last_drift_trigger_at": None,
            "created_at": None,
            "updated_at": None,
        }

    def _config_to_dict(self, config: "CrossAlertConfig") -> dict[str, Any]:
        """Convert CrossAlertConfig model to dictionary."""
        return {
            "id": config.id,
            "source_id": config.source_id,
            "enabled": config.enabled,
            "trigger_drift_on_anomaly": config.trigger_drift_on_anomaly,
            "trigger_anomaly_on_drift": config.trigger_anomaly_on_drift,
            "thresholds": config.thresholds or DEFAULT_THRESHOLDS.copy(),
            "notify_on_correlation": config.notify_on_correlation,
            "notification_channel_ids": config.notification_channel_ids,
            "cooldown_seconds": config.cooldown_seconds,
            "last_anomaly_trigger_at": (
                config.last_anomaly_trigger_at.isoformat()
                if config.last_anomaly_trigger_at
                else None
            ),
            "last_drift_trigger_at": (
                config.last_drift_trigger_at.isoformat()
                if config.last_drift_trigger_at
                else None
            ),
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }

    async def update_config(
        self,
        source_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Update auto-trigger configuration in database.

        Args:
            source_id: Source ID for source-specific config, None for global.
            **kwargs: Configuration fields to update.

        Returns:
            Updated configuration dictionary.
        """
        from truthound_dashboard.db.models import CrossAlertConfig

        # Try to find existing config
        if source_id:
            result = await self.session.execute(
                select(CrossAlertConfig).where(
                    CrossAlertConfig.source_id == source_id
                )
            )
        else:
            result = await self.session.execute(
                select(CrossAlertConfig).where(CrossAlertConfig.source_id.is_(None))
            )
        config = result.scalar_one_or_none()

        if config:
            # Update existing config
            for key, value in kwargs.items():
                if value is not None and hasattr(config, key):
                    setattr(config, key, value)
            config.updated_at = datetime.utcnow()
        else:
            # Create new config
            config = CrossAlertConfig(
                source_id=source_id,
                enabled=kwargs.get("enabled", True),
                trigger_drift_on_anomaly=kwargs.get("trigger_drift_on_anomaly", True),
                trigger_anomaly_on_drift=kwargs.get("trigger_anomaly_on_drift", True),
                thresholds=kwargs.get("thresholds", DEFAULT_THRESHOLDS.copy()),
                notify_on_correlation=kwargs.get("notify_on_correlation", True),
                notification_channel_ids=kwargs.get("notification_channel_ids"),
                cooldown_seconds=kwargs.get("cooldown_seconds", 300),
            )
            self.session.add(config)

        await self.session.flush()
        return self._config_to_dict(config)

    async def _update_last_trigger_time(
        self,
        source_id: str,
        trigger_type: str,
    ) -> None:
        """Update the last trigger time for a source.

        Args:
            source_id: Source ID.
            trigger_type: Either 'anomaly' or 'drift'.
        """
        from truthound_dashboard.db.models import CrossAlertConfig

        result = await self.session.execute(
            select(CrossAlertConfig).where(
                CrossAlertConfig.source_id == source_id
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            # Create source-specific config with just the trigger time
            config = CrossAlertConfig(
                source_id=source_id,
                thresholds=DEFAULT_THRESHOLDS.copy(),
            )
            self.session.add(config)

        if trigger_type == "anomaly":
            config.last_anomaly_trigger_at = datetime.utcnow()
        else:
            config.last_drift_trigger_at = datetime.utcnow()

        await self.session.flush()

    # =========================================================================
    # Correlation Analysis
    # =========================================================================

    async def correlate_anomaly_drift(
        self,
        source_id: str,
        *,
        time_window_hours: int = 24,
        limit: int = 50,
        save_correlations: bool = True,
    ) -> list[dict[str, Any]]:
        """Find correlated anomaly and drift alerts for a source.

        Args:
            source_id: Data source ID.
            time_window_hours: Time window to look for correlations.
            limit: Maximum correlations to return.
            save_correlations: Whether to save found correlations to DB.

        Returns:
            List of correlation dictionaries.
        """
        from truthound_dashboard.db.models import (
            AnomalyDetection,
            CrossAlertCorrelation,
            DriftAlert,
            DriftComparison,
            Source,
        )

        # Get source info
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        source = result.scalar_one_or_none()
        source_name = source.name if source else None

        # Time window
        since = datetime.utcnow() - timedelta(hours=time_window_hours)

        # Get recent anomaly detections
        anomaly_result = await self.session.execute(
            select(AnomalyDetection)
            .where(
                and_(
                    AnomalyDetection.source_id == source_id,
                    AnomalyDetection.created_at >= since,
                    AnomalyDetection.status == "success",
                )
            )
            .order_by(AnomalyDetection.created_at.desc())
            .limit(100)
        )
        anomaly_detections = list(anomaly_result.scalars().all())

        # Get recent drift alerts for this source
        drift_result = await self.session.execute(
            select(DriftAlert)
            .where(DriftAlert.created_at >= since)
            .order_by(DriftAlert.created_at.desc())
            .limit(100)
        )
        drift_alerts = list(drift_result.scalars().all())

        # Filter drift alerts related to this source
        related_drift_alerts = []
        for alert in drift_alerts:
            # Get the comparison to check source IDs
            comp_result = await self.session.execute(
                select(DriftComparison).where(DriftComparison.id == alert.comparison_id)
            )
            comparison = comp_result.scalar_one_or_none()
            if comparison and (
                comparison.baseline_source_id == source_id
                or comparison.current_source_id == source_id
            ):
                related_drift_alerts.append((alert, comparison))

        # Find correlations
        correlations = []
        for detection in anomaly_detections:
            if detection.anomaly_rate is None or detection.anomaly_rate < 0.01:
                continue

            for alert, comparison in related_drift_alerts:
                # Check time proximity
                time_delta = abs(
                    (detection.created_at - alert.created_at).total_seconds()
                )

                # Only correlate if within 2 hours of each other
                if time_delta > 7200:
                    continue

                # Calculate correlation strength
                strength = self._calculate_correlation_strength(
                    detection, alert, time_delta
                )

                if strength == "none":
                    continue

                # Find common columns
                anomaly_cols = detection.columns_analyzed or []
                drift_cols = alert.drifted_columns_json or []
                common_cols = list(set(anomaly_cols) & set(drift_cols))

                correlation_id = str(uuid.uuid4())
                confidence = self._calculate_confidence(
                    detection, alert, common_cols, time_delta
                )

                anomaly_data = {
                    "alert_id": detection.id,
                    "alert_type": "anomaly",
                    "source_id": source_id,
                    "source_name": source_name,
                    "severity": self._anomaly_severity(detection.anomaly_rate),
                    "message": f"Detected {detection.anomaly_count} anomalies ({detection.anomaly_rate * 100:.1f}% rate)",
                    "created_at": detection.created_at.isoformat(),
                    "anomaly_rate": detection.anomaly_rate,
                    "anomaly_count": detection.anomaly_count,
                }

                drift_data = {
                    "alert_id": alert.id,
                    "alert_type": "drift",
                    "source_id": source_id,
                    "source_name": source_name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "created_at": alert.created_at.isoformat(),
                    "drift_percentage": alert.drift_percentage,
                    "drifted_columns": alert.drifted_columns_json,
                }

                correlation = {
                    "id": correlation_id,
                    "source_id": source_id,
                    "source_name": source_name,
                    "correlation_strength": strength,
                    "confidence_score": confidence,
                    "time_delta_seconds": int(time_delta),
                    "anomaly_alert": anomaly_data,
                    "drift_alert": drift_data,
                    "common_columns": common_cols,
                    "suggested_action": self._suggest_action(strength, common_cols),
                    "notes": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }

                # Save to database
                if save_correlations:
                    db_correlation = CrossAlertCorrelation(
                        id=correlation_id,
                        source_id=source_id,
                        correlation_strength=strength,
                        confidence_score=confidence,
                        time_delta_seconds=int(time_delta),
                        anomaly_alert_id=detection.id,
                        drift_alert_id=alert.id,
                        anomaly_data=anomaly_data,
                        drift_data=drift_data,
                        common_columns=common_cols,
                        suggested_action=self._suggest_action(strength, common_cols),
                    )
                    self.session.add(db_correlation)

                correlations.append(correlation)

        if save_correlations and correlations:
            await self.session.flush()

        # Sort by confidence score and limit
        correlations.sort(key=lambda x: x["confidence_score"], reverse=True)
        return correlations[:limit]

    def _calculate_correlation_strength(
        self,
        detection: "AnomalyDetection",
        alert: "DriftAlert",
        time_delta: float,
    ) -> str:
        """Calculate correlation strength between anomaly and drift."""
        score = 0

        # Time proximity (closer = stronger)
        if time_delta < 600:  # 10 minutes
            score += 3
        elif time_delta < 1800:  # 30 minutes
            score += 2
        elif time_delta < 3600:  # 1 hour
            score += 1

        # Anomaly severity
        rate = detection.anomaly_rate or 0
        if rate > 0.2:
            score += 3
        elif rate > 0.1:
            score += 2
        elif rate > 0.05:
            score += 1

        # Drift severity
        if alert.severity == "critical":
            score += 3
        elif alert.severity == "high":
            score += 2
        elif alert.severity == "medium":
            score += 1

        # Drift percentage
        drift_pct = alert.drift_percentage or 0
        if drift_pct > 30:
            score += 2
        elif drift_pct > 15:
            score += 1

        # Determine strength
        if score >= 8:
            return "strong"
        elif score >= 5:
            return "moderate"
        elif score >= 2:
            return "weak"
        return "none"

    def _calculate_confidence(
        self,
        detection: "AnomalyDetection",
        alert: "DriftAlert",
        common_cols: list[str],
        time_delta: float,
    ) -> float:
        """Calculate confidence score for correlation."""
        confidence = 0.5  # Base confidence

        # Time proximity bonus
        if time_delta < 300:
            confidence += 0.2
        elif time_delta < 1800:
            confidence += 0.1

        # Common columns bonus
        if len(common_cols) > 3:
            confidence += 0.2
        elif len(common_cols) > 0:
            confidence += 0.1

        # Severity bonus
        rate = detection.anomaly_rate or 0
        if rate > 0.15 and alert.severity in ("critical", "high"):
            confidence += 0.15

        return min(confidence, 1.0)

    def _anomaly_severity(self, rate: float | None) -> str:
        """Determine anomaly severity from rate."""
        if rate is None:
            return "low"
        if rate > 0.2:
            return "critical"
        if rate > 0.1:
            return "high"
        if rate > 0.05:
            return "medium"
        return "low"

    def _suggest_action(self, strength: str, common_cols: list[str]) -> str:
        """Suggest action based on correlation."""
        if strength == "strong":
            if common_cols:
                cols = ", ".join(common_cols[:3])
                return f"Investigate upstream changes affecting columns: {cols}"
            return "Investigate upstream data pipeline for recent changes"
        elif strength == "moderate":
            return "Review data quality and consider updating baseline"
        else:
            return "Monitor for recurring patterns"

    # =========================================================================
    # Auto-Trigger Operations
    # =========================================================================

    async def auto_trigger_drift_on_anomaly(
        self,
        detection_id: str,
    ) -> dict[str, Any] | None:
        """Auto-trigger drift check when anomaly detection shows high rate."""
        from truthound_dashboard.db.models import (
            AnomalyDetection,
            CrossAlertTriggerEvent,
            DriftMonitor,
        )
        from truthound_dashboard.core.drift_monitor import DriftMonitorService

        # Get detection
        result = await self.session.execute(
            select(AnomalyDetection).where(AnomalyDetection.id == detection_id)
        )
        detection = result.scalar_one_or_none()

        if not detection:
            return None

        # Get config
        config = await self.get_config(detection.source_id)
        if not config.get("enabled") or not config.get("trigger_drift_on_anomaly"):
            return await self._create_skip_event(
                detection.source_id,
                "anomaly_to_drift",
                detection_id,
                "anomaly",
                "Auto-trigger disabled",
            )

        # Check thresholds
        thresholds = config.get("thresholds", {})
        rate_threshold = thresholds.get("anomaly_rate_threshold", 0.1)
        count_threshold = thresholds.get("anomaly_count_threshold", 10)

        rate = detection.anomaly_rate or 0
        count = detection.anomaly_count or 0

        if rate < rate_threshold and count < count_threshold:
            return await self._create_skip_event(
                detection.source_id,
                "anomaly_to_drift",
                detection_id,
                "anomaly",
                f"Below thresholds (rate: {rate:.2f} < {rate_threshold}, count: {count} < {count_threshold})",
            )

        # Check cooldown
        cooldown = config.get("cooldown_seconds", 300)
        last_trigger_str = config.get("last_anomaly_trigger_at")
        if last_trigger_str:
            last_trigger = datetime.fromisoformat(last_trigger_str)
            elapsed = (datetime.utcnow() - last_trigger).total_seconds()
            if elapsed < cooldown:
                return await self._create_skip_event(
                    detection.source_id,
                    "anomaly_to_drift",
                    detection_id,
                    "anomaly",
                    f"Cooldown active ({int(cooldown - elapsed)}s remaining)",
                )

        # Find a drift monitor for this source
        monitor_result = await self.session.execute(
            select(DriftMonitor)
            .where(
                or_(
                    DriftMonitor.baseline_source_id == detection.source_id,
                    DriftMonitor.current_source_id == detection.source_id,
                )
            )
            .limit(1)
        )
        monitor = monitor_result.scalar_one_or_none()

        # Create event record
        event_id = str(uuid.uuid4())
        event = CrossAlertTriggerEvent(
            id=event_id,
            source_id=detection.source_id,
            trigger_type="anomaly_to_drift",
            trigger_alert_id=detection_id,
            trigger_alert_type="anomaly",
            status="pending",
        )
        self.session.add(event)

        if not monitor:
            event.status = "skipped"
            event.skipped_reason = "No drift monitor configured for this source"
            await self.session.flush()
            return self._event_to_dict(event)

        try:
            # Run the drift monitor
            event.status = "running"
            await self.session.flush()

            drift_service = DriftMonitorService(self.session)
            comparison = await drift_service.run_monitor(monitor.id)

            if comparison:
                event.status = "completed"
                event.result_id = comparison.id

                # Check for correlation
                if comparison.has_drift:
                    correlations = await self.correlate_anomaly_drift(
                        detection.source_id, time_window_hours=1
                    )
                    if correlations:
                        event.correlation_found = True
                        event.correlation_id = correlations[0]["id"]
            else:
                event.status = "failed"
                event.error_message = "Drift monitor run failed"

        except Exception as e:
            event.status = "failed"
            event.error_message = str(e)
            logger.error(f"Auto-trigger drift check failed: {e}")

        # Update last trigger time
        await self._update_last_trigger_time(detection.source_id, "anomaly")
        await self.session.flush()

        return self._event_to_dict(event)

    async def auto_trigger_anomaly_on_drift(
        self,
        monitor_id: str,
    ) -> dict[str, Any] | None:
        """Auto-trigger anomaly check when drift is detected."""
        from truthound_dashboard.db.models import (
            CrossAlertTriggerEvent,
            DriftAlert,
            DriftMonitor,
        )
        from truthound_dashboard.core.anomaly import AnomalyDetectionService

        # Get monitor
        result = await self.session.execute(
            select(DriftMonitor).where(DriftMonitor.id == monitor_id)
        )
        monitor = result.scalar_one_or_none()

        if not monitor:
            return None

        source_id = monitor.current_source_id

        # Get latest alert for this monitor
        alert_result = await self.session.execute(
            select(DriftAlert)
            .where(DriftAlert.monitor_id == monitor_id)
            .order_by(DriftAlert.created_at.desc())
            .limit(1)
        )
        alert = alert_result.scalar_one_or_none()

        if not alert:
            return None

        # Get config
        config = await self.get_config(source_id)
        if not config.get("enabled") or not config.get("trigger_anomaly_on_drift"):
            return await self._create_skip_event(
                source_id,
                "drift_to_anomaly",
                alert.id,
                "drift",
                "Auto-trigger disabled",
            )

        # Check thresholds
        thresholds = config.get("thresholds", {})
        drift_threshold = thresholds.get("drift_percentage_threshold", 10.0)
        cols_threshold = thresholds.get("drift_columns_threshold", 2)

        drift_pct = alert.drift_percentage or 0
        cols_count = len(alert.drifted_columns_json or [])

        if drift_pct < drift_threshold and cols_count < cols_threshold:
            return await self._create_skip_event(
                source_id,
                "drift_to_anomaly",
                alert.id,
                "drift",
                f"Below thresholds (drift: {drift_pct:.1f}% < {drift_threshold}%, cols: {cols_count} < {cols_threshold})",
            )

        # Check cooldown
        cooldown = config.get("cooldown_seconds", 300)
        last_trigger_str = config.get("last_drift_trigger_at")
        if last_trigger_str:
            last_trigger = datetime.fromisoformat(last_trigger_str)
            elapsed = (datetime.utcnow() - last_trigger).total_seconds()
            if elapsed < cooldown:
                return await self._create_skip_event(
                    source_id,
                    "drift_to_anomaly",
                    alert.id,
                    "drift",
                    f"Cooldown active ({int(cooldown - elapsed)}s remaining)",
                )

        # Create event record
        event_id = str(uuid.uuid4())
        event = CrossAlertTriggerEvent(
            id=event_id,
            source_id=source_id,
            trigger_type="drift_to_anomaly",
            trigger_alert_id=alert.id,
            trigger_alert_type="drift",
            status="pending",
        )
        self.session.add(event)

        try:
            # Run anomaly detection
            event.status = "running"
            await self.session.flush()

            anomaly_service = AnomalyDetectionService(self.session)

            detection = await anomaly_service.create_detection(
                source_id=source_id,
                algorithm="isolation_forest",
                columns=alert.drifted_columns_json,
            )
            detection = await anomaly_service.run_detection(detection.id)

            event.status = "completed"
            event.result_id = detection.id

            # Check for correlation
            if detection.anomaly_count and detection.anomaly_count > 0:
                correlations = await self.correlate_anomaly_drift(
                    source_id, time_window_hours=1
                )
                if correlations:
                    event.correlation_found = True
                    event.correlation_id = correlations[0]["id"]

        except Exception as e:
            event.status = "failed"
            event.error_message = str(e)
            logger.error(f"Auto-trigger anomaly check failed: {e}")

        # Update last trigger time
        await self._update_last_trigger_time(source_id, "drift")
        await self.session.flush()

        return self._event_to_dict(event)

    async def _create_skip_event(
        self,
        source_id: str,
        trigger_type: str,
        alert_id: str,
        alert_type: str,
        reason: str,
    ) -> dict[str, Any]:
        """Create a skipped trigger event and save to DB."""
        from truthound_dashboard.db.models import CrossAlertTriggerEvent

        event = CrossAlertTriggerEvent(
            source_id=source_id,
            trigger_type=trigger_type,
            trigger_alert_id=alert_id,
            trigger_alert_type=alert_type,
            status="skipped",
            skipped_reason=reason,
        )
        self.session.add(event)
        await self.session.flush()

        return self._event_to_dict(event)

    def _event_to_dict(self, event: "CrossAlertTriggerEvent") -> dict[str, Any]:
        """Convert CrossAlertTriggerEvent model to dictionary."""
        return {
            "id": event.id,
            "source_id": event.source_id,
            "trigger_type": event.trigger_type,
            "trigger_alert_id": event.trigger_alert_id,
            "trigger_alert_type": event.trigger_alert_type,
            "result_id": event.result_id,
            "correlation_found": event.correlation_found,
            "correlation_id": event.correlation_id,
            "status": event.status,
            "error_message": event.error_message,
            "skipped_reason": event.skipped_reason,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    # =========================================================================
    # Query Operations (DB-backed)
    # =========================================================================

    async def get_correlations(
        self,
        source_id: str | None = None,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get correlation records from database.

        Args:
            source_id: Filter by source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Tuple of (correlations, total_count).
        """
        from truthound_dashboard.db.models import CrossAlertCorrelation, Source

        # Build query
        query = select(CrossAlertCorrelation)
        count_query = select(func.count(CrossAlertCorrelation.id))

        if source_id:
            query = query.where(CrossAlertCorrelation.source_id == source_id)
            count_query = count_query.where(
                CrossAlertCorrelation.source_id == source_id
            )

        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results
        query = (
            query.order_by(CrossAlertCorrelation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        correlations = result.scalars().all()

        # Convert to dicts with source names
        items = []
        for corr in correlations:
            # Get source name
            source_result = await self.session.execute(
                select(Source).where(Source.id == corr.source_id)
            )
            source = source_result.scalar_one_or_none()
            source_name = source.name if source else None

            items.append({
                "id": corr.id,
                "source_id": corr.source_id,
                "source_name": source_name,
                "correlation_strength": corr.correlation_strength,
                "confidence_score": corr.confidence_score,
                "time_delta_seconds": corr.time_delta_seconds,
                "anomaly_alert": corr.anomaly_data or {
                    "alert_id": corr.anomaly_alert_id,
                    "alert_type": "anomaly",
                },
                "drift_alert": corr.drift_data or {
                    "alert_id": corr.drift_alert_id,
                    "alert_type": "drift",
                },
                "common_columns": corr.common_columns,
                "suggested_action": corr.suggested_action,
                "notes": corr.notes,
                "created_at": corr.created_at.isoformat() if corr.created_at else None,
            })

        return items, total

    async def get_auto_trigger_events(
        self,
        source_id: str | None = None,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get auto-trigger event records from database.

        Args:
            source_id: Filter by source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Tuple of (events, total_count).
        """
        from truthound_dashboard.db.models import CrossAlertTriggerEvent

        # Build query
        query = select(CrossAlertTriggerEvent)
        count_query = select(func.count(CrossAlertTriggerEvent.id))

        if source_id:
            query = query.where(CrossAlertTriggerEvent.source_id == source_id)
            count_query = count_query.where(
                CrossAlertTriggerEvent.source_id == source_id
            )

        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results
        query = (
            query.order_by(CrossAlertTriggerEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        events = result.scalars().all()

        items = [self._event_to_dict(event) for event in events]
        return items, total

    async def get_summary(self) -> dict[str, Any]:
        """Get cross-alert summary statistics from database.

        Returns:
            Summary dictionary.
        """
        from truthound_dashboard.db.models import (
            CrossAlertConfig,
            CrossAlertCorrelation,
            CrossAlertTriggerEvent,
            Source,
        )

        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)

        # Count correlations by strength
        strong_result = await self.session.execute(
            select(func.count(CrossAlertCorrelation.id)).where(
                CrossAlertCorrelation.correlation_strength == "strong"
            )
        )
        strong = strong_result.scalar() or 0

        moderate_result = await self.session.execute(
            select(func.count(CrossAlertCorrelation.id)).where(
                CrossAlertCorrelation.correlation_strength == "moderate"
            )
        )
        moderate = moderate_result.scalar() or 0

        weak_result = await self.session.execute(
            select(func.count(CrossAlertCorrelation.id)).where(
                CrossAlertCorrelation.correlation_strength == "weak"
            )
        )
        weak = weak_result.scalar() or 0

        total_correlations = strong + moderate + weak

        # Recent activity
        recent_corr_result = await self.session.execute(
            select(func.count(CrossAlertCorrelation.id)).where(
                CrossAlertCorrelation.created_at >= last_24h
            )
        )
        recent_correlations = recent_corr_result.scalar() or 0

        recent_trigger_result = await self.session.execute(
            select(func.count(CrossAlertTriggerEvent.id)).where(
                CrossAlertTriggerEvent.created_at >= last_24h
            )
        )
        recent_triggers = recent_trigger_result.scalar() or 0

        # Trigger counts by type
        anomaly_to_drift_result = await self.session.execute(
            select(func.count(CrossAlertTriggerEvent.id)).where(
                CrossAlertTriggerEvent.trigger_type == "anomaly_to_drift"
            )
        )
        anomaly_to_drift = anomaly_to_drift_result.scalar() or 0

        drift_to_anomaly_result = await self.session.execute(
            select(func.count(CrossAlertTriggerEvent.id)).where(
                CrossAlertTriggerEvent.trigger_type == "drift_to_anomaly"
            )
        )
        drift_to_anomaly = drift_to_anomaly_result.scalar() or 0

        # Top affected sources
        top_sources_result = await self.session.execute(
            select(
                CrossAlertCorrelation.source_id,
                func.count(CrossAlertCorrelation.id).label("count"),
            )
            .group_by(CrossAlertCorrelation.source_id)
            .order_by(func.count(CrossAlertCorrelation.id).desc())
            .limit(5)
        )
        top_sources_raw = top_sources_result.all()

        top_sources = []
        for source_id, count in top_sources_raw:
            source_result = await self.session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = source_result.scalar_one_or_none()
            top_sources.append({
                "source_id": source_id,
                "source_name": source.name if source else None,
                "count": count,
            })

        # Get global config for enabled status
        global_config = await self.get_config(None)

        return {
            "total_correlations": total_correlations,
            "strong_correlations": strong,
            "moderate_correlations": moderate,
            "weak_correlations": weak,
            "recent_correlations_24h": recent_correlations,
            "recent_auto_triggers_24h": recent_triggers,
            "top_affected_sources": top_sources,
            "auto_trigger_enabled": global_config.get("enabled", True),
            "anomaly_to_drift_triggers": anomaly_to_drift,
            "drift_to_anomaly_triggers": drift_to_anomaly,
        }
