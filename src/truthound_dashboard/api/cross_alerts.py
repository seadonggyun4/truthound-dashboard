"""Cross-alert correlation API endpoints.

This module provides REST API endpoints for cross-feature integration
between Anomaly Detection and Drift Monitoring alerts.

API Design: Direct Response Style
- Single resources return the resource directly
- List endpoints return PaginatedResponse with data, total, offset, limit
- Errors are handled via HTTPException
- Success is indicated by HTTP status codes (200, 201, 204)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from truthound_dashboard.core.cross_alerts import CrossAlertService
from truthound_dashboard.schemas.cross_alerts import (
    CrossAlertCorrelation,
    CrossAlertCorrelationListResponse,
    CorrelationSearchResult,
    AutoTriggerConfig,
    AutoTriggerConfigCreate,
    AutoTriggerConfigUpdate,
    AutoTriggerEvent,
    AutoTriggerEventListResponse,
    CrossAlertSummary,
)
from .deps import SessionDep

router = APIRouter()


# Dependency
async def get_cross_alert_service(session: SessionDep) -> CrossAlertService:
    """Get cross-alert service dependency."""
    return CrossAlertService(session)


CrossAlertServiceDep = Annotated[CrossAlertService, Depends(get_cross_alert_service)]


# =============================================================================
# Correlation Endpoints
# =============================================================================


@router.get(
    "/cross-alerts/correlations",
    response_model=CrossAlertCorrelationListResponse,
    summary="Get correlated alerts",
    description="Get correlations between anomaly and drift alerts.",
)
async def get_correlations(
    service: CrossAlertServiceDep,
    source_id: str | None = Query(None, description="Filter by source ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> CrossAlertCorrelationListResponse:
    """Get correlated alerts.

    Args:
        service: Injected cross-alert service.
        source_id: Optional source ID filter.
        limit: Maximum items to return.
        offset: Number of items to skip.

    Returns:
        Paginated list of correlations.
    """
    correlations, total = await service.get_correlations(
        source_id=source_id,
        limit=limit,
        offset=offset,
    )

    return CrossAlertCorrelationListResponse(
        data=[CrossAlertCorrelation(**c) for c in correlations],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/cross-alerts/correlations/{source_id}",
    response_model=CorrelationSearchResult,
    summary="Find correlations for source",
    description="Find correlated anomaly and drift alerts for a specific source.",
)
async def find_correlations_for_source(
    source_id: str,
    service: CrossAlertServiceDep,
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
) -> CorrelationSearchResult:
    """Find correlations for a specific source.

    This actively searches for correlations between recent anomaly
    detections and drift alerts for the given source.

    Args:
        source_id: Source ID to analyze.
        service: Injected cross-alert service.
        time_window_hours: Time window to search (1-168 hours).
        limit: Maximum correlations to return.

    Returns:
        Search result with found correlations.
    """
    correlations = await service.correlate_anomaly_drift(
        source_id=source_id,
        time_window_hours=time_window_hours,
        limit=limit,
    )

    return CorrelationSearchResult(
        correlations=[CrossAlertCorrelation(**c) for c in correlations],
        total=len(correlations),
    )


# =============================================================================
# Auto-Trigger Configuration Endpoints
# =============================================================================


@router.get(
    "/cross-alerts/config",
    response_model=AutoTriggerConfig,
    summary="Get auto-trigger config",
    description="Get auto-trigger configuration (global or source-specific).",
)
async def get_config(
    service: CrossAlertServiceDep,
    source_id: str | None = Query(None, description="Source ID for source-specific config"),
) -> AutoTriggerConfig:
    """Get auto-trigger configuration.

    Args:
        service: Injected cross-alert service.
        source_id: Optional source ID for source-specific config.

    Returns:
        Configuration object.
    """
    config = await service.get_config(source_id)
    return AutoTriggerConfig(**config)


@router.post(
    "/cross-alerts/config",
    response_model=AutoTriggerConfig,
    status_code=201,
    summary="Create/update auto-trigger config",
    description="Create or update auto-trigger configuration.",
)
async def update_config(
    request: AutoTriggerConfigCreate,
    service: CrossAlertServiceDep,
) -> AutoTriggerConfig:
    """Create or update auto-trigger configuration.

    Args:
        request: Configuration data.
        service: Injected cross-alert service.

    Returns:
        Updated configuration.
    """
    update_data = request.model_dump(exclude_unset=True)
    source_id = update_data.pop("source_id", None)

    config = await service.update_config(source_id, **update_data)

    return AutoTriggerConfig(**config)


@router.put(
    "/cross-alerts/config",
    response_model=AutoTriggerConfig,
    summary="Update auto-trigger config",
    description="Update existing auto-trigger configuration.",
)
async def patch_config(
    request: AutoTriggerConfigUpdate,
    service: CrossAlertServiceDep,
    source_id: str | None = Query(None, description="Source ID for source-specific config"),
) -> AutoTriggerConfig:
    """Update auto-trigger configuration.

    Args:
        request: Configuration update data.
        service: Injected cross-alert service.
        source_id: Optional source ID for source-specific config.

    Returns:
        Updated configuration.
    """
    update_data = request.model_dump(exclude_unset=True)
    config = await service.update_config(source_id, **update_data)

    return AutoTriggerConfig(**config)


# =============================================================================
# Auto-Trigger Event Endpoints
# =============================================================================


@router.get(
    "/cross-alerts/events",
    response_model=AutoTriggerEventListResponse,
    summary="List auto-trigger events",
    description="Get history of auto-triggered checks.",
)
async def list_events(
    service: CrossAlertServiceDep,
    source_id: str | None = Query(None, description="Filter by source ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> AutoTriggerEventListResponse:
    """List auto-trigger events.

    Args:
        service: Injected cross-alert service.
        source_id: Optional source ID filter.
        limit: Maximum items to return.
        offset: Number of items to skip.

    Returns:
        Paginated list of events.
    """
    events, total = await service.get_auto_trigger_events(
        source_id=source_id,
        limit=limit,
        offset=offset,
    )

    return AutoTriggerEventListResponse(
        data=[AutoTriggerEvent(**e) for e in events],
        total=total,
        offset=offset,
        limit=limit,
    )


# =============================================================================
# Manual Trigger Endpoints
# =============================================================================


@router.post(
    "/cross-alerts/trigger/drift-on-anomaly/{detection_id}",
    response_model=AutoTriggerEvent,
    summary="Trigger drift check on anomaly",
    description="Manually trigger a drift check based on an anomaly detection result.",
)
async def trigger_drift_on_anomaly(
    detection_id: str,
    service: CrossAlertServiceDep,
) -> AutoTriggerEvent:
    """Manually trigger drift check after anomaly detection.

    Args:
        detection_id: Anomaly detection ID.
        service: Injected cross-alert service.

    Returns:
        Trigger event result.

    Raises:
        HTTPException: 404 if detection not found.
    """
    event = await service.auto_trigger_drift_on_anomaly(detection_id)

    if not event:
        raise HTTPException(status_code=404, detail="Detection not found")

    return AutoTriggerEvent(**event)


@router.post(
    "/cross-alerts/trigger/anomaly-on-drift/{monitor_id}",
    response_model=AutoTriggerEvent,
    summary="Trigger anomaly check on drift",
    description="Manually trigger an anomaly check based on drift detection.",
)
async def trigger_anomaly_on_drift(
    monitor_id: str,
    service: CrossAlertServiceDep,
) -> AutoTriggerEvent:
    """Manually trigger anomaly check after drift detection.

    Args:
        monitor_id: Drift monitor ID.
        service: Injected cross-alert service.

    Returns:
        Trigger event result.

    Raises:
        HTTPException: 404 if monitor not found.
    """
    event = await service.auto_trigger_anomaly_on_drift(monitor_id)

    if not event:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return AutoTriggerEvent(**event)


# =============================================================================
# Summary Endpoint
# =============================================================================


@router.get(
    "/cross-alerts/summary",
    response_model=CrossAlertSummary,
    summary="Get cross-alert summary",
    description="Get summary statistics for cross-alert correlations.",
)
async def get_summary(
    service: CrossAlertServiceDep,
) -> CrossAlertSummary:
    """Get cross-alert summary statistics.

    Args:
        service: Injected cross-alert service.

    Returns:
        Summary statistics.
    """
    summary = await service.get_summary()
    return CrossAlertSummary(**summary)
