"""API endpoints for Unified Alerts.

Provides REST API for:
- Listing aggregated anomaly and validation alerts
- Alert summary and statistics
- Alert correlation queries
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.unified_alerts import UnifiedAlertsService
from ..db import SavedView, get_db_session
from ..schemas.unified_alerts import (
    AcknowledgeAlertRequest,
    AssignAlertRequest,
    AlertCorrelation,
    AlertCorrelationResponse,
    AlertCountResponse,
    AlertSeverity,
    AlertSource,
    AlertStatus,
    AlertSummary,
    BulkAlertActionRequest,
    BulkAlertActionResponse,
    ResolveAlertRequest,
    UnifiedAlertListResponse,
    UnifiedAlertResponse,
)
from .deps import require_permission

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_service(session: AsyncSession = Depends(get_db_session)) -> UnifiedAlertsService:
    """Get unified alerts service instance."""
    return UnifiedAlertsService(session)


async def _resolve_saved_view_filters(
    *,
    service: UnifiedAlertsService,
    workspace_id: str,
    saved_view_id: str | None,
) -> dict[str, object]:
    if not saved_view_id:
        return {}
    result = await service.session.execute(
        select(SavedView).where(
            SavedView.id == saved_view_id,
            SavedView.workspace_id == workspace_id,
            SavedView.scope == "alerts",
        )
    )
    view = result.scalar_one_or_none()
    if view is None:
        return {}
    return dict(view.filters or {})


# =============================================================================
# Alert List Endpoints
# =============================================================================


@router.get("", response_model=UnifiedAlertListResponse)
async def list_alerts(
    context = Depends(require_permission("incidents:read")),
    workspace_id: str | None = None,
    saved_view_id: str | None = None,
    source: AlertSource | None = None,
    severity: AlertSeverity | None = None,
    status: AlertStatus | None = None,
    queue_id: str | None = Query(None, description="Filter by queue ID"),
    assignee_user_id: str | None = Query(None, description="Filter by assignee user ID"),
    search: str | None = Query(None, description="Text search across title/source"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: UnifiedAlertsService = Depends(get_service),
) -> UnifiedAlertListResponse:
    """List queue-aware operational alerts."""
    saved_filters = await _resolve_saved_view_filters(
        service=service,
        workspace_id=workspace_id or context.workspace.id,
        saved_view_id=saved_view_id,
    )
    alerts = await service.list_incidents(
        workspace_id=workspace_id or context.workspace.id,
        source=source or saved_filters.get("source"),
        severity=severity or saved_filters.get("severity"),
        status=status or saved_filters.get("status"),
        queue_id=queue_id or saved_filters.get("queue_id"),
        assignee_user_id=assignee_user_id or saved_filters.get("assignee_user_id"),
        search=search or saved_filters.get("search"),
    )
    total = len(alerts)

    return UnifiedAlertListResponse(
        items=alerts[offset : offset + limit],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/summary", response_model=AlertSummary)
async def get_alert_summary(
    context = Depends(require_permission("incidents:read")),
    time_range_hours: int = Query(24, ge=1, le=720, description="Time range for summary"),
    service: UnifiedAlertsService = Depends(get_service),
) -> AlertSummary:
    """Get alert summary statistics."""
    return await service.summary(
        workspace_id=context.workspace.id,
        time_range_hours=time_range_hours,
    )


@router.get("/count", response_model=AlertCountResponse)
async def get_alert_count(
    context = Depends(require_permission("incidents:read")),
    status: AlertStatus | None = Query(None, description="Filter by status"),
    service: UnifiedAlertsService = Depends(get_service),
) -> AlertCountResponse:
    """Get quick alert count."""
    alerts = await service.list_incidents(
        workspace_id=context.workspace.id,
        status=status,
    )

    return AlertCountResponse(
        count=len(alerts),
        status_filter=status.value if status else "all",
    )


@router.get("/{alert_id}", response_model=UnifiedAlertResponse)
async def get_alert(
    alert_id: str,
    context = Depends(require_permission("incidents:read")),
    service: UnifiedAlertsService = Depends(get_service),
) -> UnifiedAlertResponse:
    """Get a specific alert by unified ID."""
    alert = await service.get_incident(
        incident_id=alert_id,
        workspace_id=context.workspace.id,
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


# =============================================================================
# Bulk Action Endpoints (must be before /{alert_id} routes to avoid path conflict)
# =============================================================================


@router.post("/bulk/acknowledge", response_model=BulkAlertActionResponse)
async def bulk_acknowledge_alerts(
    request: BulkAlertActionRequest,
    context = Depends(require_permission("incidents:write")),
    service: UnifiedAlertsService = Depends(get_service),
) -> BulkAlertActionResponse:
    """Bulk acknowledge multiple alerts."""
    actor = context.user.display_name or context.user.email
    success = 0
    failed_ids: list[str] = []
    for alert_id in request.alert_ids:
        alert = await service.acknowledge_incident(
            incident_id=alert_id,
            workspace_id=context.workspace.id,
            actor=actor,
            message=request.message,
        )
        if alert is None:
            failed_ids.append(alert_id)
        else:
            success += 1

    return BulkAlertActionResponse(
        success_count=success,
        failed_count=len(failed_ids),
        failed_ids=failed_ids,
    )


@router.post("/bulk/resolve", response_model=BulkAlertActionResponse)
async def bulk_resolve_alerts(
    request: BulkAlertActionRequest,
    context = Depends(require_permission("incidents:write")),
    service: UnifiedAlertsService = Depends(get_service),
) -> BulkAlertActionResponse:
    """Bulk resolve multiple alerts."""
    actor = context.user.display_name or context.user.email
    success = 0
    failed_ids: list[str] = []
    for alert_id in request.alert_ids:
        alert = await service.resolve_incident(
            incident_id=alert_id,
            workspace_id=context.workspace.id,
            actor=actor,
            message=request.message,
        )
        if alert is None:
            failed_ids.append(alert_id)
        else:
            success += 1

    return BulkAlertActionResponse(
        success_count=success,
        failed_count=len(failed_ids),
        failed_ids=failed_ids,
    )


# =============================================================================
# Alert Action Endpoints
# =============================================================================


@router.post("/{alert_id}/acknowledge", response_model=UnifiedAlertResponse)
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    context = Depends(require_permission("incidents:write")),
    service: UnifiedAlertsService = Depends(get_service),
) -> UnifiedAlertResponse:
    """Acknowledge an alert."""
    actor = context.user.display_name or context.user.email
    alert = await service.acknowledge_incident(
        incident_id=alert_id,
        workspace_id=context.workspace.id,
        actor=actor,
        message=request.message,
    )
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found or not eligible for acknowledgement",
        )

    return alert


@router.post("/{alert_id}/resolve", response_model=UnifiedAlertResponse)
async def resolve_alert(
    alert_id: str,
    request: ResolveAlertRequest,
    context = Depends(require_permission("incidents:write")),
    service: UnifiedAlertsService = Depends(get_service),
) -> UnifiedAlertResponse:
    """Resolve an alert."""
    actor = context.user.display_name or context.user.email
    alert = await service.resolve_incident(
        incident_id=alert_id,
        workspace_id=context.workspace.id,
        actor=actor,
        message=request.message,
    )
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found or not eligible for resolution",
        )

    return alert


@router.post("/{alert_id}/assign", response_model=UnifiedAlertResponse)
async def assign_alert(
    alert_id: str,
    request: AssignAlertRequest,
    context = Depends(require_permission("incidents:write")),
    service: UnifiedAlertsService = Depends(get_service),
) -> UnifiedAlertResponse:
    """Assign or requeue an alert."""
    actor = context.user.display_name or context.user.email
    alert = await service.assign_incident(
        incident_id=alert_id,
        workspace_id=context.workspace.id,
        actor_user_id=context.user.id,
        actor_name=actor,
        assignee_user_id=request.assignee_user_id,
        queue_id=request.queue_id,
        message=request.message,
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


# =============================================================================
# Correlation Endpoints
# =============================================================================


@router.get("/{alert_id}/correlations", response_model=AlertCorrelationResponse)
async def get_alert_correlations(
    alert_id: str,
    context = Depends(require_permission("incidents:read")),
    time_window_hours: int = Query(1, ge=1, le=24, description="Correlation time window"),
    service: UnifiedAlertsService = Depends(get_service),
) -> AlertCorrelationResponse:
    """Get correlated alerts for a given alert."""
    correlations = await service.correlations(
        incident_id=alert_id,
        workspace_id=context.workspace.id,
        time_window_hours=time_window_hours,
    )

    total_correlated = sum(len(c.related_alerts) for c in correlations)

    return AlertCorrelationResponse(
        correlations=correlations,
        total_correlated=total_correlated,
    )
