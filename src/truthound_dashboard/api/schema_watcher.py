"""Schema Watcher API endpoints.

This module provides REST API endpoints for schema watcher management,
including continuous schema monitoring, alerts, and run history.

All schema watcher features use truthound's schema evolution module:
- SchemaEvolutionDetector for change detection
- SchemaHistory for version management
- ColumnRenameDetector for rename detection
- BreakingChangeAlertManager for alerts
- ImpactAnalyzer for impact analysis

API Design: Direct Response Style
- Single resources return the resource directly
- List endpoints return PaginatedResponse with data, total, offset, limit
- Errors are handled via HTTPException
- Success is indicated by HTTP status codes (200, 201, 204)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from truthound_dashboard.core.schema_watcher import SchemaWatcherService
from truthound_dashboard.schemas.schema_watcher import (
    SchemaWatcherCreate,
    SchemaWatcherUpdate,
    SchemaWatcherResponse,
    SchemaWatcherSummary,
    SchemaWatcherStatistics,
    SchemaWatcherStatus,
    SchemaWatcherStatusAction,
    SchemaWatcherCheckNowResponse,
    SchemaWatcherAlertResponse,
    SchemaWatcherAlertSummary,
    SchemaWatcherAlertAcknowledge,
    SchemaWatcherAlertResolve,
    SchemaWatcherAlertStatus,
    SchemaWatcherAlertSeverity,
    SchemaWatcherRunResponse,
    SchemaWatcherRunSummary,
    SchemaWatcherRunStatus,
    SchemaWatcherSchedulerStatus,
    # Schema Detection types
    SchemaDetectionRequest,
    SchemaDetectionResponse,
    RenameDetectionRequest,
    RenameDetectionResponse,
    # Version History types
    SchemaVersionCreate,
    SchemaVersionResponse,
    SchemaVersionSummary,
    SchemaDiffRequest,
    SchemaDiffResponse,
    SchemaRollbackRequest,
)
from truthound_dashboard.schemas.base import MessageResponse, PaginatedResponse
from .deps import SessionDep

router = APIRouter(prefix="/schema-watchers", tags=["Schema Watchers"])


# =============================================================================
# Dependencies
# =============================================================================


async def get_schema_watcher_service(session: SessionDep) -> SchemaWatcherService:
    """Get schema watcher service dependency."""
    return SchemaWatcherService(session)


SchemaWatcherServiceDep = Annotated[
    SchemaWatcherService, Depends(get_schema_watcher_service)
]


# =============================================================================
# Watcher CRUD Endpoints
# =============================================================================


@router.post(
    "",
    response_model=SchemaWatcherResponse,
    status_code=201,
    summary="Create schema watcher",
    description="""
    Create a new schema watcher for continuous schema monitoring.

    Uses truthound's SchemaWatcher with:
    - SchemaEvolutionDetector for change detection
    - SchemaHistory for version management
    - ColumnRenameDetector for rename detection (configurable)
    """,
)
async def create_watcher(
    request: SchemaWatcherCreate,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherResponse:
    """Create a new schema watcher."""
    try:
        return await service.create_watcher(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=PaginatedResponse[SchemaWatcherSummary],
    summary="List schema watchers",
    description="List all schema watchers with optional filtering.",
)
async def list_watchers(
    service: SchemaWatcherServiceDep,
    status: SchemaWatcherStatus | None = Query(None, description="Filter by status"),
    source_id: str | None = Query(None, description="Filter by source ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SchemaWatcherSummary]:
    """List schema watchers."""
    watchers, total = await service.list_watchers(
        status=status,
        source_id=source_id,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse(
        data=watchers,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/statistics",
    response_model=SchemaWatcherStatistics,
    summary="Get watcher statistics",
    description="Get aggregate statistics for all schema watchers.",
)
async def get_statistics(
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherStatistics:
    """Get schema watcher statistics."""
    return await service.get_statistics()


@router.get(
    "/scheduler/status",
    response_model=SchemaWatcherSchedulerStatus,
    summary="Get scheduler status",
    description="Get the status of the schema watcher scheduler job.",
)
async def get_scheduler_status(
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherSchedulerStatus:
    """Get schema watcher scheduler status."""
    return await service.get_scheduler_status()


@router.get(
    "/{watcher_id}",
    response_model=SchemaWatcherResponse,
    summary="Get schema watcher",
    description="Get a specific schema watcher by ID.",
)
async def get_watcher(
    watcher_id: str,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherResponse:
    """Get a schema watcher by ID."""
    watcher = await service.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")
    return watcher


@router.put(
    "/{watcher_id}",
    response_model=SchemaWatcherResponse,
    summary="Update schema watcher",
    description="Update a schema watcher's configuration.",
)
async def update_watcher(
    watcher_id: str,
    request: SchemaWatcherUpdate,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherResponse:
    """Update a schema watcher."""
    watcher = await service.update_watcher(watcher_id, request)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")
    return watcher


@router.delete(
    "/{watcher_id}",
    response_model=MessageResponse,
    summary="Delete schema watcher",
    description="Delete a schema watcher and all its alerts and runs.",
)
async def delete_watcher(
    watcher_id: str,
    service: SchemaWatcherServiceDep,
) -> MessageResponse:
    """Delete a schema watcher."""
    deleted = await service.delete_watcher(watcher_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schema watcher not found")
    return MessageResponse(message="Schema watcher deleted successfully")


@router.post(
    "/{watcher_id}/status",
    response_model=SchemaWatcherResponse,
    summary="Set watcher status",
    description="Change the status of a schema watcher (active, paused, stopped).",
)
async def set_watcher_status(
    watcher_id: str,
    request: SchemaWatcherStatusAction,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherResponse:
    """Set schema watcher status."""
    watcher = await service.set_watcher_status(watcher_id, request.status)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")
    return watcher


@router.post(
    "/{watcher_id}/check",
    response_model=SchemaWatcherCheckNowResponse,
    summary="Check schema now",
    description="""
    Trigger an immediate schema check for a watcher.

    This performs:
    1. Learn current schema from source using truthound
    2. Compare with previous version using SchemaEvolutionDetector
    3. Detect renames using ColumnRenameDetector (if enabled)
    4. Save new version to SchemaHistory
    5. Create alert if breaking changes detected
    """,
)
async def check_now(
    watcher_id: str,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherCheckNowResponse:
    """Execute schema check immediately."""
    try:
        return await service.check_now(watcher_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Schema Detection Endpoints (truthound integration)
# =============================================================================


@router.post(
    "/detect-changes",
    response_model=SchemaDetectionResponse,
    summary="Detect schema changes",
    description="""
    Detect changes between two schemas using truthound's SchemaEvolutionDetector.

    Detects:
    - Column additions/removals
    - Type changes
    - Nullable changes
    - Constraint changes
    - Column renames (with similarity algorithms)
    """,
)
async def detect_schema_changes(
    request: SchemaDetectionRequest,
    service: SchemaWatcherServiceDep,
) -> SchemaDetectionResponse:
    """Detect schema changes between two schemas."""
    return await service.detect_changes(
        current_schema=request.current_schema,
        baseline_schema=request.baseline_schema,
        detect_renames=request.detect_renames,
        rename_similarity_threshold=request.rename_similarity_threshold,
    )


@router.post(
    "/detect-renames",
    response_model=RenameDetectionResponse,
    summary="Detect column renames",
    description="""
    Detect column renames using truthound's ColumnRenameDetector.

    Supports multiple similarity algorithms:
    - composite: Weighted combination (default)
    - levenshtein: Edit distance
    - jaro_winkler: Short strings, prefixes
    - ngram: Partial matches
    - token: snake_case/camelCase names
    """,
)
async def detect_column_renames(
    request: RenameDetectionRequest,
    service: SchemaWatcherServiceDep,
) -> RenameDetectionResponse:
    """Detect column renames between added and removed columns."""
    return await service.detect_renames(
        added_columns=request.added_columns,
        removed_columns=request.removed_columns,
        similarity_threshold=request.similarity_threshold,
        require_type_match=request.require_type_match,
        allow_compatible_types=request.allow_compatible_types,
        algorithm=request.algorithm.value,
    )


# =============================================================================
# Version History Endpoints (truthound integration)
# =============================================================================


@router.get(
    "/{watcher_id}/versions",
    response_model=list[SchemaVersionSummary],
    summary="List schema versions",
    description="List schema versions tracked by this watcher using truthound's SchemaHistory.",
)
async def list_schema_versions(
    watcher_id: str,
    service: SchemaWatcherServiceDep,
    limit: int = Query(50, ge=1, le=100),
) -> list[SchemaVersionSummary]:
    """List schema versions for a watcher."""
    # Verify watcher exists
    watcher = await service.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")

    return await service.list_schema_versions(watcher_id, limit=limit)


@router.get(
    "/{watcher_id}/versions/{version}",
    response_model=SchemaVersionResponse,
    summary="Get schema version",
    description="Get a specific schema version by version string or ID.",
)
async def get_schema_version(
    watcher_id: str,
    version: str,
    service: SchemaWatcherServiceDep,
) -> SchemaVersionResponse:
    """Get a specific schema version."""
    result = await service.get_schema_version(watcher_id, version)
    if not result:
        raise HTTPException(status_code=404, detail="Schema version not found")
    return result


@router.post(
    "/{watcher_id}/versions",
    response_model=SchemaVersionResponse,
    status_code=201,
    summary="Save schema version",
    description="Manually save a schema version to history.",
)
async def save_schema_version(
    watcher_id: str,
    request: SchemaVersionCreate,
    service: SchemaWatcherServiceDep,
) -> SchemaVersionResponse:
    """Save a schema version."""
    # Verify watcher exists
    watcher = await service.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")

    try:
        return await service.save_schema_version(
            watcher_id,
            request.schema,
            version=request.version,
            metadata=request.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{watcher_id}/versions/diff",
    response_model=SchemaDiffResponse,
    summary="Diff schema versions",
    description="Get the diff between two schema versions.",
)
async def diff_schema_versions(
    watcher_id: str,
    request: SchemaDiffRequest,
    service: SchemaWatcherServiceDep,
) -> SchemaDiffResponse:
    """Get diff between schema versions."""
    # Verify watcher exists
    watcher = await service.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")

    try:
        return await service.diff_versions(
            watcher_id,
            request.from_version,
            request.to_version,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{watcher_id}/versions/rollback",
    response_model=SchemaVersionResponse,
    summary="Rollback schema version",
    description="Rollback to a previous schema version (creates a new version matching the target).",
)
async def rollback_schema_version(
    watcher_id: str,
    request: SchemaRollbackRequest,
    service: SchemaWatcherServiceDep,
) -> SchemaVersionResponse:
    """Rollback to a previous schema version."""
    # Verify watcher exists
    watcher = await service.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")

    try:
        return await service.rollback_version(
            watcher_id,
            request.to_version,
            reason=request.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Alert Endpoints
# =============================================================================


@router.get(
    "/alerts",
    response_model=PaginatedResponse[SchemaWatcherAlertSummary],
    summary="List alerts",
    description="List all schema watcher alerts with optional filtering.",
)
async def list_alerts(
    service: SchemaWatcherServiceDep,
    watcher_id: str | None = Query(None, description="Filter by watcher ID"),
    status: SchemaWatcherAlertStatus | None = Query(None, description="Filter by status"),
    severity: SchemaWatcherAlertSeverity | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SchemaWatcherAlertSummary]:
    """List schema watcher alerts."""
    alerts, total = await service.list_alerts(
        watcher_id=watcher_id,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse(
        data=alerts,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/alerts/{alert_id}",
    response_model=SchemaWatcherAlertResponse,
    summary="Get alert",
    description="Get a specific schema watcher alert by ID.",
)
async def get_alert(
    alert_id: str,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherAlertResponse:
    """Get a schema watcher alert by ID."""
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=SchemaWatcherAlertResponse,
    summary="Acknowledge alert",
    description="Acknowledge a schema watcher alert.",
)
async def acknowledge_alert(
    alert_id: str,
    request: SchemaWatcherAlertAcknowledge,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherAlertResponse:
    """Acknowledge an alert."""
    alert = await service.acknowledge_alert(
        alert_id,
        acknowledged_by=request.acknowledged_by,
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=SchemaWatcherAlertResponse,
    summary="Resolve alert",
    description="Resolve a schema watcher alert.",
)
async def resolve_alert(
    alert_id: str,
    request: SchemaWatcherAlertResolve,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherAlertResponse:
    """Resolve an alert."""
    alert = await service.resolve_alert(
        alert_id,
        resolved_by=request.resolved_by,
        resolution_notes=request.resolution_notes,
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


# =============================================================================
# Run Endpoints
# =============================================================================


@router.get(
    "/runs",
    response_model=PaginatedResponse[SchemaWatcherRunSummary],
    summary="List runs",
    description="List all schema watcher runs with optional filtering.",
)
async def list_runs(
    service: SchemaWatcherServiceDep,
    watcher_id: str | None = Query(None, description="Filter by watcher ID"),
    status: SchemaWatcherRunStatus | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SchemaWatcherRunSummary]:
    """List schema watcher runs."""
    runs, total = await service.list_runs(
        watcher_id=watcher_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse(
        data=runs,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/runs/{run_id}",
    response_model=SchemaWatcherRunResponse,
    summary="Get run",
    description="Get a specific schema watcher run by ID.",
)
async def get_run(
    run_id: str,
    service: SchemaWatcherServiceDep,
) -> SchemaWatcherRunResponse:
    """Get a schema watcher run by ID."""
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# =============================================================================
# Watcher-specific Alert and Run Endpoints
# =============================================================================


@router.get(
    "/{watcher_id}/alerts",
    response_model=PaginatedResponse[SchemaWatcherAlertSummary],
    summary="List watcher alerts",
    description="List alerts for a specific schema watcher.",
)
async def list_watcher_alerts(
    watcher_id: str,
    service: SchemaWatcherServiceDep,
    status: SchemaWatcherAlertStatus | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SchemaWatcherAlertSummary]:
    """List alerts for a specific watcher."""
    # Verify watcher exists
    watcher = await service.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")

    alerts, total = await service.list_alerts(
        watcher_id=watcher_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse(
        data=alerts,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{watcher_id}/runs",
    response_model=PaginatedResponse[SchemaWatcherRunSummary],
    summary="List watcher runs",
    description="List runs for a specific schema watcher.",
)
async def list_watcher_runs(
    watcher_id: str,
    service: SchemaWatcherServiceDep,
    status: SchemaWatcherRunStatus | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SchemaWatcherRunSummary]:
    """List runs for a specific watcher."""
    # Verify watcher exists
    watcher = await service.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Schema watcher not found")

    runs, total = await service.list_runs(
        watcher_id=watcher_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse(
        data=runs,
        total=total,
        offset=offset,
        limit=limit,
    )
