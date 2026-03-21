"""Unified alert aggregation for active dashboard signals."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import AnomalyDetection, Source, Validation
from ..schemas.unified_alerts import (
    AlertCorrelation,
    AlertCountBySource,
    AlertCountBySeverity,
    AlertCountByStatus,
    AlertSeverity,
    AlertSource,
    AlertStatus,
    AlertSummary,
    AlertTrendPoint,
    UnifiedAlertResponse,
)


def _generate_alert_id(source: AlertSource, source_id: str) -> str:
    return f"{source.value}:{source_id}"


def _parse_alert_id(unified_id: str) -> tuple[AlertSource, str]:
    parts = unified_id.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid unified alert ID: {unified_id}")
    return AlertSource(parts[0]), parts[1]


class UnifiedAlertsService:
    """Read-only aggregation service for anomaly and validation alerts."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_alerts(
        self,
        *,
        source: AlertSource | None = None,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        source_name: str | None = None,
        time_range_hours: int | None = 24,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[UnifiedAlertResponse], int]:
        alerts: list[UnifiedAlertResponse] = []
        cutoff = None
        if time_range_hours:
            cutoff = datetime.utcnow() - timedelta(hours=time_range_hours)

        if source is None or source == AlertSource.ANOMALY:
            alerts.extend(
                await self._get_anomaly_alerts(
                    severity=severity,
                    status=status,
                    cutoff=cutoff,
                )
            )

        if source is None or source == AlertSource.VALIDATION:
            alerts.extend(
                await self._get_validation_alerts(
                    severity=severity,
                    status=status,
                    cutoff=cutoff,
                )
            )

        if source_name:
            needle = source_name.lower()
            alerts = [alert for alert in alerts if needle in alert.source_name.lower()]

        alerts.sort(key=lambda alert: alert.created_at, reverse=True)
        total = len(alerts)
        return alerts[offset : offset + limit], total

    async def get_alert_by_id(self, alert_id: str) -> UnifiedAlertResponse | None:
        try:
            source, source_id = _parse_alert_id(alert_id)
        except ValueError:
            return None

        if source == AlertSource.ANOMALY:
            return await self._get_single_anomaly_alert(source_id)
        if source == AlertSource.VALIDATION:
            return await self._get_single_validation_alert(source_id)
        return None

    async def get_alert_summary(self, time_range_hours: int = 24) -> AlertSummary:
        alerts, total = await self.get_all_alerts(
            time_range_hours=time_range_hours,
            limit=10_000,
        )

        by_severity = AlertCountBySeverity()
        by_source = AlertCountBySource()
        by_status = AlertCountByStatus()

        active_count = 0
        for alert in alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                by_severity.critical += 1
            elif alert.severity == AlertSeverity.HIGH:
                by_severity.high += 1
            elif alert.severity == AlertSeverity.MEDIUM:
                by_severity.medium += 1
            elif alert.severity == AlertSeverity.LOW:
                by_severity.low += 1
            elif alert.severity == AlertSeverity.INFO:
                by_severity.info += 1

            if alert.source == AlertSource.ANOMALY:
                by_source.anomaly += 1
            elif alert.source == AlertSource.VALIDATION:
                by_source.validation += 1

            if alert.status == AlertStatus.OPEN:
                by_status.open += 1
                active_count += 1
            elif alert.status == AlertStatus.ACKNOWLEDGED:
                by_status.acknowledged += 1
                active_count += 1
            elif alert.status == AlertStatus.RESOLVED:
                by_status.resolved += 1
            elif alert.status == AlertStatus.IGNORED:
                by_status.ignored += 1

        trend = []
        now = datetime.utcnow()
        for hours_ago in range(24, -1, -1):
            point_time = now - timedelta(hours=hours_ago)
            point_start = point_time.replace(minute=0, second=0, microsecond=0)
            point_end = point_start + timedelta(hours=1)
            count = sum(1 for alert in alerts if point_start <= alert.created_at < point_end)
            trend.append(AlertTrendPoint(timestamp=point_start, count=count))

        source_counts: dict[str, int] = {}
        for alert in alerts:
            source_counts[alert.source_name] = source_counts.get(alert.source_name, 0) + 1

        top_sources = sorted(
            ({"name": name, "count": count} for name, count in source_counts.items()),
            key=lambda item: item["count"],
            reverse=True,
        )[:5]

        return AlertSummary(
            total_alerts=total,
            active_alerts=active_count,
            by_severity=by_severity,
            by_source=by_source,
            by_status=by_status,
            trend_24h=trend,
            top_sources=top_sources,
        )

    async def acknowledge_alert(
        self,
        alert_id: str,
        actor: str,
        message: str = "",
    ) -> UnifiedAlertResponse | None:
        del alert_id, actor, message
        return None

    async def resolve_alert(
        self,
        alert_id: str,
        actor: str = "",
        message: str = "",
    ) -> UnifiedAlertResponse | None:
        del alert_id, actor, message
        return None

    async def bulk_acknowledge(
        self,
        alert_ids: list[str],
        actor: str,
        message: str = "",
    ) -> tuple[int, int, list[str]]:
        del actor, message
        return 0, len(alert_ids), list(alert_ids)

    async def bulk_resolve(
        self,
        alert_ids: list[str],
        actor: str,
        message: str = "",
    ) -> tuple[int, int, list[str]]:
        del actor, message
        return 0, len(alert_ids), list(alert_ids)

    async def get_alert_correlations(
        self,
        alert_id: str,
        time_window_hours: int = 1,
    ) -> list[AlertCorrelation]:
        alert = await self.get_alert_by_id(alert_id)
        if not alert:
            return []

        time_start = alert.created_at - timedelta(hours=time_window_hours)
        time_end = alert.created_at + timedelta(hours=time_window_hours)

        all_alerts, _ = await self.get_all_alerts(
            time_range_hours=time_window_hours * 2 + 24,
            limit=1000,
        )
        window_alerts = [
            candidate
            for candidate in all_alerts
            if time_start <= candidate.created_at <= time_end and candidate.id != alert_id
        ]

        correlations: list[AlertCorrelation] = []
        same_source_alerts = [
            candidate for candidate in window_alerts if candidate.source_name == alert.source_name
        ]
        if same_source_alerts:
            correlations.append(
                AlertCorrelation(
                    alert_id=alert_id,
                    related_alerts=same_source_alerts[:10],
                    correlation_type="same_source",
                    correlation_score=0.9,
                    common_factors=[f"Same source: {alert.source_name}"],
                )
            )

        same_severity_alerts = [
            candidate
            for candidate in window_alerts
            if candidate.severity == alert.severity and candidate not in same_source_alerts
        ]
        if same_severity_alerts:
            correlations.append(
                AlertCorrelation(
                    alert_id=alert_id,
                    related_alerts=same_severity_alerts[:10],
                    correlation_type="temporal_severity",
                    correlation_score=0.6,
                    common_factors=[
                        f"Same severity: {alert.severity.value}",
                        f"Within {time_window_hours}h window",
                    ],
                )
            )

        return correlations

    async def _load_source_names(self, source_ids: Sequence[str]) -> dict[str, str]:
        if not source_ids:
            return {}
        result = await self.session.execute(select(Source).where(Source.id.in_(set(source_ids))))
        return {source.id: source.name for source in result.scalars()}

    async def _get_anomaly_alerts(
        self,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        cutoff: datetime | None = None,
    ) -> list[UnifiedAlertResponse]:
        filters = [AnomalyDetection.status == "success"]
        if cutoff:
            filters.append(AnomalyDetection.created_at >= cutoff)

        result = await self.session.execute(select(AnomalyDetection).where(and_(*filters)))
        detections = result.scalars().all()
        source_names = await self._load_source_names([d.source_id for d in detections])

        unified: list[UnifiedAlertResponse] = []
        for detection in detections:
            if not detection.anomaly_rate or detection.anomaly_rate < 0.1:
                continue

            if detection.anomaly_rate >= 0.3:
                alert_severity = AlertSeverity.CRITICAL
            elif detection.anomaly_rate >= 0.2:
                alert_severity = AlertSeverity.HIGH
            else:
                alert_severity = AlertSeverity.MEDIUM

            if severity and alert_severity != severity:
                continue
            if status and status != AlertStatus.OPEN:
                continue

            pct = detection.anomaly_rate * 100
            unified.append(
                UnifiedAlertResponse(
                    id=_generate_alert_id(AlertSource.ANOMALY, detection.id),
                    source=AlertSource.ANOMALY,
                    source_id=detection.id,
                    source_name=source_names.get(detection.source_id, "Unknown Source"),
                    severity=alert_severity,
                    status=AlertStatus.OPEN,
                    title=f"High Anomaly Rate: {pct:.1f}%",
                    message=(
                        f"Anomaly detection found {detection.anomaly_count} anomalies "
                        f"out of {detection.total_rows} rows ({pct:.1f}% rate) "
                        f"using {detection.algorithm} algorithm."
                    ),
                    details={
                        "algorithm": detection.algorithm,
                        "anomaly_count": detection.anomaly_count,
                        "total_rows": detection.total_rows,
                        "anomaly_rate": detection.anomaly_rate,
                        "columns_analyzed": detection.columns_analyzed,
                        "read_only": True,
                    },
                    created_at=detection.created_at,
                    updated_at=detection.created_at,
                )
            )

        return unified

    async def _get_validation_alerts(
        self,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        cutoff: datetime | None = None,
    ) -> list[UnifiedAlertResponse]:
        filters = [Validation.status == "failed"]
        if cutoff:
            filters.append(Validation.created_at >= cutoff)

        result = await self.session.execute(select(Validation).where(and_(*filters)))
        validations = result.scalars().all()
        source_names = await self._load_source_names([v.source_id for v in validations])

        unified: list[UnifiedAlertResponse] = []
        for validation in validations:
            critical_count = validation.critical_issues or 0
            high_count = validation.high_issues or 0
            total_issues = validation.total_issues or 0

            if critical_count > 0:
                alert_severity = AlertSeverity.CRITICAL
            elif high_count > 0:
                alert_severity = AlertSeverity.HIGH
            else:
                alert_severity = AlertSeverity.MEDIUM

            if severity and alert_severity != severity:
                continue
            if status and status != AlertStatus.OPEN:
                continue

            unified.append(
                UnifiedAlertResponse(
                    id=_generate_alert_id(AlertSource.VALIDATION, validation.id),
                    source=AlertSource.VALIDATION,
                    source_id=validation.id,
                    source_name=source_names.get(validation.source_id, "Unknown Source"),
                    severity=alert_severity,
                    status=AlertStatus.OPEN,
                    title=f"Validation Failed: {total_issues} issues",
                    message=(
                        f"Validation failed with {critical_count} critical, "
                        f"{high_count} high severity issues."
                    ),
                    details={
                        "total_issues": total_issues,
                        "critical_issues": critical_count,
                        "high_issues": high_count,
                        "medium_issues": validation.medium_issues or 0,
                        "low_issues": validation.low_issues or 0,
                        "read_only": True,
                    },
                    created_at=validation.created_at,
                    updated_at=validation.created_at,
                )
            )

        return unified

    async def _get_single_anomaly_alert(self, source_id: str) -> UnifiedAlertResponse | None:
        for alert in await self._get_anomaly_alerts():
            if alert.source_id == source_id:
                return alert
        return None

    async def _get_single_validation_alert(self, source_id: str) -> UnifiedAlertResponse | None:
        for alert in await self._get_validation_alerts():
            if alert.source_id == source_id:
                return alert
        return None
