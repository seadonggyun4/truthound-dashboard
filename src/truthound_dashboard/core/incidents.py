"""Incident queues and workbench services."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.db import IncidentQueue, IncidentQueueMembership, User
from truthound_dashboard.db.models import EscalationIncidentModel, EscalationStateEnum
from truthound_dashboard.schemas.unified_alerts import (
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
from truthound_dashboard.time import utc_now


def _slugify(value: str) -> str:
    return "-".join(part for part in value.strip().lower().replace("_", "-").split() if part)


def _status_from_state(state: str) -> AlertStatus:
    if state == EscalationStateEnum.RESOLVED.value:
        return AlertStatus.RESOLVED
    if state == EscalationStateEnum.ACKNOWLEDGED.value:
        return AlertStatus.ACKNOWLEDGED
    return AlertStatus.OPEN


class IncidentQueueService:
    """Workspace-scoped queue management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_default_queue(self, *, workspace_id: str) -> IncidentQueue:
        result = await self.session.execute(
            select(IncidentQueue)
            .where(IncidentQueue.workspace_id == workspace_id)
            .where(or_(IncidentQueue.is_default == True, IncidentQueue.slug == "unassigned"))  # noqa: E712
            .order_by(IncidentQueue.is_default.desc(), IncidentQueue.created_at.asc())
        )
        queue = result.scalar_one_or_none()
        if queue is not None:
            return queue

        queue = IncidentQueue(
            workspace_id=workspace_id,
            name="Unassigned",
            slug="unassigned",
            description="Default queue for new incidents",
            is_default=True,
            is_active=True,
            routing_metadata={"routing": "default"},
        )
        self.session.add(queue)
        await self.session.flush()
        await self.session.refresh(queue)
        return queue

    async def list_queues(self, *, workspace_id: str) -> list[IncidentQueue]:
        await self.ensure_default_queue(workspace_id=workspace_id)
        result = await self.session.execute(
            select(IncidentQueue)
            .options(selectinload(IncidentQueue.memberships).selectinload(IncidentQueueMembership.user))
            .where(IncidentQueue.workspace_id == workspace_id)
            .order_by(IncidentQueue.is_default.desc(), IncidentQueue.name.asc())
        )
        return list(result.scalars().all())

    async def get_queue(self, *, queue_id: str, workspace_id: str) -> IncidentQueue | None:
        result = await self.session.execute(
            select(IncidentQueue)
            .options(selectinload(IncidentQueue.memberships).selectinload(IncidentQueueMembership.user))
            .where(IncidentQueue.id == queue_id, IncidentQueue.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def create_queue(
        self,
        *,
        workspace_id: str,
        name: str,
        description: str | None = None,
        slug: str | None = None,
        is_default: bool = False,
        is_active: bool = True,
        member_ids: list[str] | None = None,
    ) -> IncidentQueue:
        if is_default:
            await self._unset_default_queue(workspace_id=workspace_id)
        queue = IncidentQueue(
            workspace_id=workspace_id,
            name=name,
            slug=slug or _slugify(name),
            description=description,
            is_default=is_default,
            is_active=is_active,
            routing_metadata={},
        )
        self.session.add(queue)
        await self.session.flush()
        if member_ids is not None:
            await self._replace_members(queue=queue, member_ids=member_ids)
        await self.session.refresh(queue)
        return queue

    async def update_queue(
        self,
        *,
        queue_id: str,
        workspace_id: str,
        name: str | None = None,
        description: str | None = None,
        is_default: bool | None = None,
        is_active: bool | None = None,
        member_ids: list[str] | None = None,
    ) -> IncidentQueue | None:
        queue = await self.get_queue(queue_id=queue_id, workspace_id=workspace_id)
        if queue is None:
            return None
        if name is not None:
            queue.name = name
            if not queue.is_default:
                queue.slug = _slugify(name)
        if description is not None:
            queue.description = description
        if is_default is not None:
            if is_default:
                await self._unset_default_queue(workspace_id=workspace_id)
            queue.is_default = is_default
        if is_active is not None:
            queue.is_active = is_active
        if member_ids is not None:
            await self._replace_members(queue=queue, member_ids=member_ids)
        await self.session.flush()
        await self.session.refresh(queue)
        return queue

    async def delete_queue(self, *, queue_id: str, workspace_id: str) -> bool:
        queue = await self.get_queue(queue_id=queue_id, workspace_id=workspace_id)
        if queue is None or queue.is_default:
            return False
        default_queue = await self.ensure_default_queue(workspace_id=workspace_id)
        incidents_result = await self.session.execute(
            select(EscalationIncidentModel).where(EscalationIncidentModel.queue_id == queue.id)
        )
        for incident in incidents_result.scalars().all():
            incident.queue_id = default_queue.id
        await self.session.delete(queue)
        return True

    async def _unset_default_queue(self, *, workspace_id: str) -> None:
        result = await self.session.execute(
            select(IncidentQueue).where(IncidentQueue.workspace_id == workspace_id, IncidentQueue.is_default == True)  # noqa: E712
        )
        for queue in result.scalars().all():
            queue.is_default = False

    async def _replace_members(self, *, queue: IncidentQueue, member_ids: list[str]) -> None:
        memberships_result = await self.session.execute(
            select(IncidentQueueMembership).where(IncidentQueueMembership.queue_id == queue.id)
        )
        existing = {
            membership.user_id: membership
            for membership in memberships_result.scalars().all()
        }
        desired = set(member_ids)
        for user_id, membership in list(existing.items()):
            if user_id not in desired:
                await self.session.delete(membership)
        for user_id in desired:
            if user_id in existing:
                continue
            self.session.add(
                IncidentQueueMembership(
                    queue_id=queue.id,
                    user_id=user_id,
                )
            )


class IncidentService:
    """Queue-aware incident workbench."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_incidents(
        self,
        *,
        workspace_id: str,
        queue_id: str | None = None,
        assignee_user_id: str | None = None,
        status: AlertStatus | None = None,
        search: str | None = None,
        source: AlertSource | None = None,
        severity: AlertSeverity | None = None,
    ) -> list[UnifiedAlertResponse]:
        result = await self.session.execute(
            select(EscalationIncidentModel)
            .options(
                selectinload(EscalationIncidentModel.queue),
                selectinload(EscalationIncidentModel.assignee_user),
                selectinload(EscalationIncidentModel.assigned_by_user),
            )
            .where(
                or_(EscalationIncidentModel.workspace_id == workspace_id, EscalationIncidentModel.workspace_id.is_(None))
            )
            .order_by(EscalationIncidentModel.created_at.desc())
        )
        incidents = list(result.scalars().all())
        alerts = [self._incident_to_alert(incident) for incident in incidents]

        if queue_id:
            alerts = [alert for alert in alerts if alert.queue_id == queue_id]
        if assignee_user_id:
            alerts = [alert for alert in alerts if alert.assignee_user_id == assignee_user_id]
        if status:
            alerts = [alert for alert in alerts if alert.status == status]
        if source:
            alerts = [alert for alert in alerts if alert.source == source]
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        if search:
            needle = search.lower()
            alerts = [
                alert
                for alert in alerts
                if needle in alert.title.lower()
                or needle in alert.message.lower()
                or needle in alert.source_name.lower()
                or needle in alert.source_id.lower()
            ]
        return alerts

    async def get_incident(self, *, incident_id: str, workspace_id: str) -> UnifiedAlertResponse | None:
        incident = await self._load_incident(incident_id=incident_id, workspace_id=workspace_id)
        if incident is None:
            return None
        return self._incident_to_alert(incident)

    async def acknowledge_incident(
        self,
        *,
        incident_id: str,
        workspace_id: str,
        actor: str,
        message: str = "",
    ) -> UnifiedAlertResponse | None:
        incident = await self._load_incident(incident_id=incident_id, workspace_id=workspace_id)
        if incident is None:
            return None
        if incident.state == EscalationStateEnum.RESOLVED.value:
            return None
        previous_state = incident.state
        incident.state = EscalationStateEnum.ACKNOWLEDGED.value
        incident.acknowledged_by = actor
        incident.acknowledged_at = utc_now()
        incident.events = [
            *(incident.events or []),
            self._event(previous_state, incident.state, actor, message),
        ]
        await self.session.flush()
        await self.session.refresh(incident)
        return self._incident_to_alert(incident)

    async def resolve_incident(
        self,
        *,
        incident_id: str,
        workspace_id: str,
        actor: str,
        message: str = "",
    ) -> UnifiedAlertResponse | None:
        incident = await self._load_incident(incident_id=incident_id, workspace_id=workspace_id)
        if incident is None:
            return None
        previous_state = incident.state
        incident.state = EscalationStateEnum.RESOLVED.value
        incident.resolved_by = actor
        incident.resolved_at = utc_now()
        incident.events = [
            *(incident.events or []),
            self._event(previous_state, incident.state, actor, message),
        ]
        await self.session.flush()
        await self.session.refresh(incident)
        return self._incident_to_alert(incident)

    async def assign_incident(
        self,
        *,
        incident_id: str,
        workspace_id: str,
        actor_user_id: str,
        actor_name: str,
        assignee_user_id: str | None = None,
        queue_id: str | None = None,
        message: str = "",
    ) -> UnifiedAlertResponse | None:
        incident = await self._load_incident(incident_id=incident_id, workspace_id=workspace_id)
        if incident is None:
            return None
        if queue_id is not None:
            incident.queue_id = queue_id
        incident.assignee_user_id = assignee_user_id
        incident.assigned_by = actor_user_id
        incident.assigned_at = utc_now()
        incident.events = [
            *(incident.events or []),
            self._event(
                incident.state,
                incident.state,
                actor_name,
                message or "Assignment updated",
                event_type="assignment",
                extra={
                    "queue_id": incident.queue_id,
                    "assignee_user_id": incident.assignee_user_id,
                },
            ),
        ]
        await self.session.flush()
        await self.session.refresh(incident)
        return self._incident_to_alert(incident)

    async def summary(self, *, workspace_id: str, time_range_hours: int = 24) -> AlertSummary:
        alerts = await self.list_incidents(workspace_id=workspace_id)
        cutoff = utc_now() - timedelta(hours=time_range_hours)
        alerts = [alert for alert in alerts if alert.created_at >= cutoff]

        by_severity = AlertCountBySeverity()
        by_source = AlertCountBySource()
        by_status = AlertCountByStatus()

        for alert in alerts:
            setattr(by_severity, alert.severity.value, getattr(by_severity, alert.severity.value) + 1)
            setattr(by_source, alert.source.value, getattr(by_source, alert.source.value) + 1)
            if alert.status == AlertStatus.OPEN:
                by_status.open += 1
            elif alert.status == AlertStatus.ACKNOWLEDGED:
                by_status.acknowledged += 1
            elif alert.status == AlertStatus.RESOLVED:
                by_status.resolved += 1
            elif alert.status == AlertStatus.IGNORED:
                by_status.ignored += 1

        trend = []
        now = utc_now()
        for hours_ago in range(24, -1, -1):
            point_time = now - timedelta(hours=hours_ago)
            point_start = point_time.replace(minute=0, second=0, microsecond=0)
            point_end = point_start + timedelta(hours=1)
            count = sum(1 for alert in alerts if point_start <= alert.created_at < point_end)
            trend.append(AlertTrendPoint(timestamp=point_start, count=count))

        top_sources: dict[str, int] = {}
        for alert in alerts:
            top_sources[alert.source_name] = top_sources.get(alert.source_name, 0) + 1

        return AlertSummary(
            total_alerts=len(alerts),
            active_alerts=len([alert for alert in alerts if alert.status != AlertStatus.RESOLVED]),
            by_severity=by_severity,
            by_source=by_source,
            by_status=by_status,
            trend_24h=trend,
            top_sources=[
                {"name": name, "count": count}
                for name, count in sorted(top_sources.items(), key=lambda item: item[1], reverse=True)[:5]
            ],
        )

    async def correlations(
        self,
        *,
        incident_id: str,
        workspace_id: str,
        time_window_hours: int = 1,
    ) -> list[AlertCorrelation]:
        alert = await self.get_incident(incident_id=incident_id, workspace_id=workspace_id)
        if alert is None:
            return []
        alerts = await self.list_incidents(workspace_id=workspace_id)
        window_start = alert.created_at - timedelta(hours=time_window_hours)
        window_end = alert.created_at + timedelta(hours=time_window_hours)
        related = [
            candidate
            for candidate in alerts
            if candidate.id != alert.id and window_start <= candidate.created_at <= window_end
        ]

        same_queue = [candidate for candidate in related if candidate.queue_id == alert.queue_id and alert.queue_id]
        same_source = [
            candidate for candidate in related if candidate.source_name == alert.source_name and candidate not in same_queue
        ]
        correlations: list[AlertCorrelation] = []
        if same_queue:
            correlations.append(
                AlertCorrelation(
                    alert_id=alert.id,
                    related_alerts=same_queue[:10],
                    correlation_type="same_queue",
                    correlation_score=0.9,
                    common_factors=[f"Same queue: {alert.queue_name or 'Unassigned'}"],
                )
            )
        if same_source:
            correlations.append(
                AlertCorrelation(
                    alert_id=alert.id,
                    related_alerts=same_source[:10],
                    correlation_type="same_source",
                    correlation_score=0.7,
                    common_factors=[f"Same source: {alert.source_name}"],
                )
            )
        return correlations

    async def _load_incident(self, *, incident_id: str, workspace_id: str) -> EscalationIncidentModel | None:
        result = await self.session.execute(
            select(EscalationIncidentModel)
            .options(
                selectinload(EscalationIncidentModel.queue),
                selectinload(EscalationIncidentModel.assignee_user),
                selectinload(EscalationIncidentModel.assigned_by_user),
            )
            .where(
                EscalationIncidentModel.id == incident_id,
                or_(EscalationIncidentModel.workspace_id == workspace_id, EscalationIncidentModel.workspace_id.is_(None)),
            )
        )
        return result.scalar_one_or_none()

    def _incident_to_alert(self, incident: EscalationIncidentModel) -> UnifiedAlertResponse:
        context = incident.context or {}
        source_value = context.get("source", AlertSource.VALIDATION.value)
        try:
            source = AlertSource(source_value)
        except ValueError:
            source = AlertSource.VALIDATION

        severity_value = context.get("severity", AlertSeverity.MEDIUM.value)
        try:
            severity = AlertSeverity(severity_value)
        except ValueError:
            severity = AlertSeverity.MEDIUM

        return UnifiedAlertResponse(
            id=incident.id,
            source=source,
            source_id=incident.incident_ref,
            source_name=str(context.get("source_name") or context.get("source_label") or "Incident"),
            severity=severity,
            status=_status_from_state(incident.state),
            title=str(context.get("title") or f"Incident {incident.incident_ref}"),
            message=str(context.get("message") or "Escalation incident requires attention"),
            details=context,
            workspace_id=incident.workspace_id,
            queue_id=incident.queue_id,
            queue_name=incident.queue.name if getattr(incident, "queue", None) else None,
            assignee_user_id=incident.assignee_user_id,
            assignee_name=incident.assignee_user.display_name if getattr(incident, "assignee_user", None) else None,
            assigned_at=incident.assigned_at,
            assigned_by=incident.assigned_by_user.display_name if getattr(incident, "assigned_by_user", None) else None,
            timeline=incident.events or [],
            acknowledged_at=incident.acknowledged_at,
            acknowledged_by=incident.acknowledged_by,
            resolved_at=incident.resolved_at,
            resolved_by=incident.resolved_by,
            related_alert_ids=[],
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )

    def _event(
        self,
        from_state: str,
        to_state: str,
        actor: str,
        message: str,
        *,
        event_type: str = "transition",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "type": event_type,
            "from_state": from_state,
            "to_state": to_state,
            "actor": actor,
            "message": message,
            "timestamp": utc_now().isoformat(),
            **(extra or {}),
        }
