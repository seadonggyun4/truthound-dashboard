"""Fleet overview aggregates for the dashboard homepage."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from truthound_dashboard.db import ArtifactRecord, IncidentQueue, SavedView, SourceOwnership, Workspace
from truthound_dashboard.db.models import EscalationIncidentModel, Source
from truthound_dashboard.time import utc_now


class OverviewService:
    """Fleet overview aggregates for the dashboard homepage."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_overview(self, *, workspace_id: str) -> dict[str, Any]:
        workspace_result = await self.session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = workspace_result.scalar_one_or_none()

        source_result = await self.session.execute(
            select(Source)
            .options(
                selectinload(Source.ownership).selectinload(SourceOwnership.owner_user),
                selectinload(Source.ownership).selectinload(SourceOwnership.team),
                selectinload(Source.ownership).selectinload(SourceOwnership.domain),
            )
            .where(or_(Source.workspace_id == workspace_id, Source.workspace_id.is_(None)))
        )
        sources = list(source_result.scalars().all())

        incidents_result = await self.session.execute(
            select(EscalationIncidentModel)
            .options(
                selectinload(EscalationIncidentModel.queue),
                selectinload(EscalationIncidentModel.assignee_user),
            )
            .where(
                or_(
                    EscalationIncidentModel.workspace_id == workspace_id,
                    EscalationIncidentModel.workspace_id.is_(None),
                )
            )
            .order_by(EscalationIncidentModel.created_at.desc())
        )
        incidents = list(incidents_result.scalars().all())

        artifacts_result = await self.session.execute(
            select(ArtifactRecord)
            .options(
                selectinload(ArtifactRecord.source)
                .selectinload(Source.ownership)
                .selectinload(SourceOwnership.owner_user),
                selectinload(ArtifactRecord.source)
                .selectinload(Source.ownership)
                .selectinload(SourceOwnership.team),
                selectinload(ArtifactRecord.source)
                .selectinload(Source.ownership)
                .selectinload(SourceOwnership.domain),
            )
            .where(or_(ArtifactRecord.workspace_id == workspace_id, ArtifactRecord.workspace_id.is_(None)))
            .order_by(ArtifactRecord.created_at.desc())
        )
        artifacts = list(artifacts_result.scalars().all())

        views_result = await self.session.execute(
            select(SavedView)
            .options(selectinload(SavedView.owner))
            .where(SavedView.workspace_id == workspace_id)
            .order_by(SavedView.scope.asc(), SavedView.name.asc())
        )
        views = list(views_result.scalars().all())

        queues_result = await self.session.execute(
            select(IncidentQueue)
            .where(IncidentQueue.workspace_id == workspace_id)
            .order_by(IncidentQueue.name.asc())
        )
        queues = list(queues_result.scalars().all())

        healthy_sources = len(
            [source for source in sources if source.latest_validation and source.latest_validation.status == "success"]
        )
        unhealthy_sources = len(
            [
                source
                for source in sources
                if source.latest_validation and source.latest_validation.status in {"failed", "error"}
            ]
        )
        active_incidents = [incident for incident in incidents if incident.state != "resolved"]
        now = utc_now()
        freshness_cutoff = now - timedelta(hours=24)
        stale_cutoff = now - timedelta(days=7)

        by_queue: list[dict[str, Any]] = []
        for queue in queues:
            queue_active = [incident for incident in active_incidents if incident.queue_id == queue.id]
            by_queue.append(
                {
                    "queue_id": queue.id,
                    "queue_name": queue.name,
                    "count": len(queue_active),
                }
            )

        assignee_counts: dict[str, dict[str, Any]] = {}
        for incident in active_incidents:
            assignee_id = incident.assignee_user_id or "unassigned"
            assignee_name = (
                incident.assignee_user.display_name
                if getattr(incident, "assignee_user", None) is not None
                else "Unassigned"
            )
            if assignee_id not in assignee_counts:
                assignee_counts[assignee_id] = {
                    "user_id": None if assignee_id == "unassigned" else assignee_id,
                    "user_name": assignee_name,
                    "count": 0,
                }
            assignee_counts[assignee_id]["count"] += 1

        by_type_map: dict[str, int] = {}
        for artifact in artifacts:
            by_type_map[artifact.artifact_type] = by_type_map.get(artifact.artifact_type, 0) + 1

        owner_counts: dict[str, dict[str, Any]] = {}
        team_counts: dict[str, dict[str, Any]] = {}
        domain_counts: dict[str, dict[str, Any]] = {}
        unowned_sources = 0
        for source in sources:
            ownership = getattr(source, "ownership", None)
            if ownership is None or (
                ownership.owner_user_id is None and ownership.team_id is None and ownership.domain_id is None
            ):
                unowned_sources += 1
                continue
            if ownership.owner_user is not None:
                owner_counts.setdefault(
                    ownership.owner_user.id,
                    {"id": ownership.owner_user.id, "name": ownership.owner_user.display_name, "count": 0},
                )["count"] += 1
            if ownership.team is not None:
                team_counts.setdefault(
                    ownership.team.id,
                    {"id": ownership.team.id, "name": ownership.team.name, "count": 0},
                )["count"] += 1
            if ownership.domain is not None:
                domain_counts.setdefault(
                    ownership.domain.id,
                    {"id": ownership.domain.id, "name": ownership.domain.name, "count": 0},
                )["count"] += 1

        artifact_freshness_by_ownership: dict[tuple[str, str | None], dict[str, Any]] = {}
        for artifact in artifacts:
            ownership = getattr(getattr(artifact, "source", None), "ownership", None)
            if ownership is None or ownership.owner_user is None:
                key = ("owner", None)
                entry = artifact_freshness_by_ownership.setdefault(
                    key,
                    {
                        "ownership_type": "owner",
                        "ownership_id": None,
                        "ownership_name": "Unowned",
                        "fresh_24h": 0,
                        "stale": 0,
                    },
                )
            else:
                key = ("owner", ownership.owner_user.id)
                entry = artifact_freshness_by_ownership.setdefault(
                    key,
                    {
                        "ownership_type": "owner",
                        "ownership_id": ownership.owner_user.id,
                        "ownership_name": ownership.owner_user.display_name,
                        "fresh_24h": 0,
                        "stale": 0,
                    },
                )
            if artifact.created_at >= freshness_cutoff:
                entry["fresh_24h"] += 1
            if artifact.created_at < stale_cutoff:
                entry["stale"] += 1

        return {
            "workspace": {
                "id": workspace_id,
                "name": workspace.name if workspace is not None else "Workspace",
                "slug": workspace.slug if workspace is not None else "workspace",
            },
            "sources": {
                "total": len(sources),
                "active": len([source for source in sources if source.is_active]),
                "healthy": healthy_sources,
                "unhealthy": unhealthy_sources,
                "unowned": unowned_sources,
            },
            "incidents": {
                "total": len(incidents),
                "active": len(active_incidents),
            },
            "artifacts": {
                "total": len(artifacts),
                "failed": len([artifact for artifact in artifacts if artifact.status == "failed"]),
                "fresh_24h": len([artifact for artifact in artifacts if artifact.created_at >= freshness_cutoff]),
                "stale": len([artifact for artifact in artifacts if artifact.created_at < stale_cutoff]),
            },
            "incident_backlog": by_queue,
            "assignee_workload": list(assignee_counts.values()),
            "artifact_types": [
                {"artifact_type": artifact_type, "count": count}
                for artifact_type, count in sorted(by_type_map.items())
            ],
            "sources_by_owner": list(owner_counts.values()),
            "sources_by_team": list(team_counts.values()),
            "sources_by_domain": list(domain_counts.values()),
            "artifact_freshness_by_ownership": list(artifact_freshness_by_ownership.values()),
            "saved_views": [
                {
                    "id": view.id,
                    "name": view.name,
                    "scope": view.scope,
                    "description": view.description,
                    "is_default": view.is_default,
                    "owner_name": view.owner.display_name if view.owner else None,
                }
                for view in views[:8]
            ],
        }
