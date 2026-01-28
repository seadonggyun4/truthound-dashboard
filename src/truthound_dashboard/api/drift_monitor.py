"""Drift monitoring API endpoints.

This module provides REST API endpoints for drift monitoring management.

API Design: Direct Response Style
- Single resources return the resource directly
- List endpoints return PaginatedResponse with data, total, offset, limit
- Errors are handled via HTTPException
- Success is indicated by HTTP status codes (200, 201, 204)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from truthound_dashboard.core.drift_monitor import DriftMonitorService
from truthound_dashboard.schemas.drift_monitor import (
    DriftMonitorCreate,
    DriftMonitorUpdate,
    DriftMonitorResponse,
    DriftMonitorListResponse,
    DriftMonitorSummary,
    DriftAlertResponse,
    DriftAlertListResponse,
    DriftAlertUpdate,
    DriftTrendResponse,
    DriftPreviewRequest,
    DriftPreviewData,
    RootCauseAnalysis,
    SampleSizeEstimateResponse,
    JobProgressResponse,
    SampledComparisonResult,
    MonitorRunResult,
)
from truthound_dashboard.schemas.base import MessageResponse
from .deps import SessionDep

router = APIRouter()


# Dependency
async def get_drift_monitor_service(session: SessionDep) -> DriftMonitorService:
    """Get drift monitor service dependency."""
    return DriftMonitorService(session)


DriftMonitorServiceDep = Annotated[DriftMonitorService, Depends(get_drift_monitor_service)]


# Monitor Endpoints


@router.post(
    "/drift/monitors",
    response_model=DriftMonitorResponse,
    status_code=201,
    summary="Create drift monitor",
    description="Create a new drift monitor for automatic drift detection.",
)
async def create_monitor(
    request: DriftMonitorCreate,
    service: DriftMonitorServiceDep,
) -> DriftMonitorResponse:
    """Create a new drift monitor."""
    monitor = await service.create_monitor(
        name=request.name,
        baseline_source_id=request.baseline_source_id,
        current_source_id=request.current_source_id,
        cron_expression=request.cron_expression,
        method=request.method,
        threshold=request.threshold,
        columns=request.columns,
        alert_on_drift=request.alert_on_drift,
        alert_threshold_critical=request.alert_threshold_critical,
        alert_threshold_high=request.alert_threshold_high,
        notification_channel_ids=request.notification_channel_ids,
    )

    return DriftMonitorResponse(**_monitor_to_dict(monitor))


@router.get(
    "/drift/monitors",
    response_model=DriftMonitorListResponse,
    summary="List drift monitors",
    description="List all drift monitors with optional filtering.",
)
async def list_monitors(
    service: DriftMonitorServiceDep,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DriftMonitorListResponse:
    """List drift monitors."""
    monitors, total = await service.list_monitors(
        status=status,
        limit=limit,
        offset=offset,
    )

    return DriftMonitorListResponse(
        data=[DriftMonitorResponse(**_monitor_to_dict(m)) for m in monitors],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/drift/monitors/summary",
    response_model=DriftMonitorSummary,
    summary="Get monitors summary",
    description="Get summary statistics for all drift monitors.",
)
async def get_monitors_summary(
    service: DriftMonitorServiceDep,
) -> DriftMonitorSummary:
    """Get summary of all drift monitors."""
    summary = await service.get_summary()
    return DriftMonitorSummary(**summary)


@router.post(
    "/drift/preview",
    response_model=DriftPreviewData,
    summary="Preview drift comparison",
    description="Preview drift comparison results without creating a monitor or saving results.",
)
async def preview_drift(
    request: DriftPreviewRequest,
    service: DriftMonitorServiceDep,
) -> DriftPreviewData:
    """Preview drift comparison without persisting results.

    This endpoint allows users to see drift comparison results before
    creating a monitor. The results are not saved to the database.
    """
    try:
        preview_result = await service.preview_drift(
            baseline_source_id=request.baseline_source_id,
            current_source_id=request.current_source_id,
            columns=request.columns,
            method=request.method,
            threshold=request.threshold,
        )
        return DriftPreviewData(**preview_result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/drift/monitors/{monitor_id}",
    response_model=DriftMonitorResponse,
    summary="Get drift monitor",
    description="Get a drift monitor by ID.",
)
async def get_monitor(
    monitor_id: str,
    service: DriftMonitorServiceDep,
) -> DriftMonitorResponse:
    """Get a drift monitor by ID."""
    monitor = await service.get_monitor(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return DriftMonitorResponse(**_monitor_to_dict(monitor))


@router.put(
    "/drift/monitors/{monitor_id}",
    response_model=DriftMonitorResponse,
    summary="Update drift monitor",
    description="Update a drift monitor configuration.",
)
async def update_monitor(
    monitor_id: str,
    request: DriftMonitorUpdate,
    service: DriftMonitorServiceDep,
) -> DriftMonitorResponse:
    """Update a drift monitor."""
    update_data = request.model_dump(exclude_unset=True)
    monitor = await service.update_monitor(monitor_id, **update_data)

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return DriftMonitorResponse(**_monitor_to_dict(monitor))


@router.delete(
    "/drift/monitors/{monitor_id}",
    response_model=MessageResponse,
    summary="Delete drift monitor",
    description="Delete a drift monitor.",
)
async def delete_monitor(
    monitor_id: str,
    service: DriftMonitorServiceDep,
) -> MessageResponse:
    """Delete a drift monitor."""
    deleted = await service.delete_monitor(monitor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return MessageResponse(message="Monitor deleted")


@router.post(
    "/drift/monitors/{monitor_id}/run",
    response_model=MonitorRunResult,
    summary="Run drift monitor",
    description="Manually trigger a drift monitoring run.",
)
async def run_monitor(
    monitor_id: str,
    service: DriftMonitorServiceDep,
) -> MonitorRunResult:
    """Manually run a drift monitor."""
    # force=True allows running paused monitors manually
    comparison = await service.run_monitor(monitor_id, force=True)
    if not comparison:
        raise HTTPException(status_code=400, detail="Monitor run failed")

    # Extract drifted column names from result_json
    drifted_column_names: list[str] = []
    if comparison.result_json and "columns" in comparison.result_json:
        drifted_column_names = [
            col["column"]
            for col in comparison.result_json["columns"]
            if col.get("drifted", False)
        ]

    return MonitorRunResult(
        comparison_id=comparison.id,
        has_drift=comparison.has_drift,
        drift_percentage=comparison.drift_percentage or 0.0,
        drifted_columns=drifted_column_names,
    )


@router.get(
    "/drift/monitors/{monitor_id}/trend",
    response_model=DriftTrendResponse,
    summary="Get drift trend",
    description="Get drift trend data for a monitor over time.",
)
async def get_monitor_trend(
    monitor_id: str,
    service: DriftMonitorServiceDep,
    days: int = Query(30, ge=1, le=365),
) -> DriftTrendResponse:
    """Get drift trend for a monitor."""
    trend = await service.get_trend(monitor_id, days=days)
    if not trend:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return DriftTrendResponse(**trend)


# Run History Endpoints

from truthound_dashboard.schemas.drift_monitor import (
    DriftMonitorRunResponse,
    DriftMonitorRunListResponse,
    DriftMonitorRunStatistics,
)


@router.get(
    "/drift/monitors/{monitor_id}/runs",
    response_model=DriftMonitorRunListResponse,
    summary="List monitor runs",
    description="Get execution history for a drift monitor.",
)
async def list_monitor_runs(
    monitor_id: str,
    service: DriftMonitorServiceDep,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DriftMonitorRunListResponse:
    """List runs for a drift monitor."""
    runs, total = await service.list_runs(
        monitor_id=monitor_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return DriftMonitorRunListResponse(
        data=[
            DriftMonitorRunResponse(
                id=run.id,
                monitor_id=run.monitor_id,
                status=run.status,
                has_drift=run.has_drift,
                max_drift_score=run.max_drift_score,
                total_columns=run.total_columns,
                drifted_columns=run.drifted_columns,
                column_results=run.column_results,
                root_cause_analysis=run.root_cause_analysis,
                duration_ms=run.duration_ms,
                error_message=run.error_message,
                created_at=run.created_at,
                completed_at=run.completed_at,
            )
            for run in runs
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/drift/monitors/{monitor_id}/runs/latest",
    response_model=DriftMonitorRunResponse | None,
    summary="Get latest run",
    description="Get the most recent run for a drift monitor.",
)
async def get_latest_run(
    monitor_id: str,
    service: DriftMonitorServiceDep,
) -> DriftMonitorRunResponse | None:
    """Get the latest run for a monitor."""
    run = await service.get_latest_run(monitor_id)
    if not run:
        return None

    return DriftMonitorRunResponse(
        id=run.id,
        monitor_id=run.monitor_id,
        status=run.status,
        has_drift=run.has_drift,
        max_drift_score=run.max_drift_score,
        total_columns=run.total_columns,
        drifted_columns=run.drifted_columns,
        column_results=run.column_results,
        root_cause_analysis=run.root_cause_analysis,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


@router.get(
    "/drift/monitors/{monitor_id}/runs/statistics",
    response_model=DriftMonitorRunStatistics,
    summary="Get run statistics",
    description="Get aggregated statistics for drift monitor runs.",
)
async def get_run_statistics(
    monitor_id: str,
    service: DriftMonitorServiceDep,
) -> DriftMonitorRunStatistics:
    """Get run statistics for a monitor."""
    stats = await service.get_run_statistics(monitor_id)
    return DriftMonitorRunStatistics(**stats)


@router.get(
    "/drift/monitors/{monitor_id}/runs/{run_id}",
    response_model=DriftMonitorRunResponse,
    summary="Get run details",
    description="Get detailed information about a specific run.",
)
async def get_run(
    monitor_id: str,
    run_id: str,
    service: DriftMonitorServiceDep,
) -> DriftMonitorRunResponse:
    """Get a specific run."""
    run = await service.get_run(run_id)
    if not run or run.monitor_id != monitor_id:
        raise HTTPException(status_code=404, detail="Run not found")

    return DriftMonitorRunResponse(
        id=run.id,
        monitor_id=run.monitor_id,
        status=run.status,
        has_drift=run.has_drift,
        max_drift_score=run.max_drift_score,
        total_columns=run.total_columns,
        drifted_columns=run.drifted_columns,
        column_results=run.column_results,
        root_cause_analysis=run.root_cause_analysis,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


@router.get(
    "/drift/monitors/{monitor_id}/runs/{run_id}/root-cause",
    response_model=RootCauseAnalysis,
    summary="Analyze drift root cause",
    description="Analyze root causes of drift for a specific comparison run.",
)
async def get_root_cause_analysis(
    monitor_id: str,
    run_id: str,
    service: DriftMonitorServiceDep,
) -> RootCauseAnalysis:
    """Get root cause analysis for a drift run.

    Analyzes a drift comparison to identify why drift is occurring,
    including statistical distribution changes, new/missing categories,
    outlier introduction, data volume changes, and temporal patterns.
    """
    analysis = await service.analyze_root_cause(run_id=run_id, monitor_id=monitor_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Drift run not found")

    return RootCauseAnalysis(**analysis)


@router.get(
    "/drift/comparisons/{run_id}/root-cause",
    response_model=RootCauseAnalysis,
    summary="Analyze drift root cause (standalone)",
    description="Analyze root causes for a drift comparison without a monitor.",
)
async def get_comparison_root_cause_analysis(
    run_id: str,
    service: DriftMonitorServiceDep,
) -> RootCauseAnalysis:
    """Get root cause analysis for a standalone drift comparison.

    Similar to the monitor-based endpoint but for one-off comparisons.
    """
    analysis = await service.analyze_root_cause(run_id=run_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Drift comparison not found")

    return RootCauseAnalysis(**analysis)


# Alert Endpoints


@router.get(
    "/drift/alerts",
    response_model=DriftAlertListResponse,
    summary="List drift alerts",
    description="List drift alerts with optional filtering.",
)
async def list_alerts(
    service: DriftMonitorServiceDep,
    monitor_id: str | None = Query(None, description="Filter by monitor"),
    status: str | None = Query(None, description="Filter by status"),
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DriftAlertListResponse:
    """List drift alerts."""
    alerts, total = await service.list_alerts(
        monitor_id=monitor_id,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )

    return DriftAlertListResponse(
        data=[DriftAlertResponse(**_alert_to_dict(a)) for a in alerts],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/drift/alerts/{alert_id}",
    response_model=DriftAlertResponse,
    summary="Get drift alert",
    description="Get a drift alert by ID.",
)
async def get_alert(
    alert_id: str,
    service: DriftMonitorServiceDep,
) -> DriftAlertResponse:
    """Get a drift alert by ID."""
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return DriftAlertResponse(**_alert_to_dict(alert))


@router.put(
    "/drift/alerts/{alert_id}",
    response_model=DriftAlertResponse,
    summary="Update drift alert",
    description="Update a drift alert status or notes.",
)
async def update_alert(
    alert_id: str,
    request: DriftAlertUpdate,
    service: DriftMonitorServiceDep,
) -> DriftAlertResponse:
    """Update a drift alert."""
    alert = await service.update_alert(
        alert_id,
        status=request.status,
        notes=request.notes,
    )

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return DriftAlertResponse(**_alert_to_dict(alert))


# Large-Scale Dataset Optimization Endpoints


@router.post(
    "/drift/monitors/{monitor_id}/run-sampled",
    response_model=SampledComparisonResult,
    summary="Run sampled drift comparison",
    description="Run drift comparison with sampling for large datasets (100M+ rows).",
)
async def run_sampled_comparison(
    monitor_id: str,
    service: DriftMonitorServiceDep,
    sample_size: int | None = Query(None, description="Custom sample size (auto-estimated if null)"),
    sampling_method: str = Query("random", description="Sampling method"),
    confidence_level: float = Query(0.95, ge=0.80, le=0.99, description="Target confidence level"),
    early_stop_threshold: float = Query(0.5, ge=0.1, le=1.0, description="Early stop threshold"),
    max_workers: int = Query(4, ge=1, le=16, description="Max parallel workers"),
) -> SampledComparisonResult:
    """Run a sampled drift comparison for large datasets.

    Optimized for 100M+ row datasets with:
    - Statistical sampling to reduce data volume
    - Chunked processing for memory efficiency
    - Parallel column comparisons
    - Early stopping when drift is obvious
    """
    try:
        result = await service.run_sampled_comparison(
            monitor_id=monitor_id,
            sample_size=sample_size,
            sampling_method=sampling_method,
            confidence_level=confidence_level,
            early_stop_threshold=early_stop_threshold,
            max_workers=max_workers,
        )
        return SampledComparisonResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/drift/estimate-sample-size",
    response_model=SampleSizeEstimateResponse,
    summary="Estimate optimal sample size",
    description="Estimate optimal sample size for drift comparison between two sources.",
)
async def estimate_sample_size(
    service: DriftMonitorServiceDep,
    baseline_source_id: str = Query(..., description="Baseline source ID"),
    current_source_id: str = Query(..., description="Current source ID"),
    confidence_level: float = Query(0.95, ge=0.80, le=0.99, description="Target confidence level"),
    margin_of_error: float = Query(0.03, ge=0.01, le=0.10, description="Acceptable margin of error"),
) -> SampleSizeEstimateResponse:
    """Estimate optimal sample size for a drift comparison.

    Returns recommended sample size based on dataset sizes and
    desired confidence level. Also provides performance estimates
    and sampling method recommendations.
    """
    try:
        estimate = await service.estimate_comparison_size(
            baseline_source_id=baseline_source_id,
            current_source_id=current_source_id,
            confidence_level=confidence_level,
            margin_of_error=margin_of_error,
        )
        return SampleSizeEstimateResponse(**estimate)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/drift/jobs/{job_id}/progress",
    response_model=JobProgressResponse,
    summary="Get job progress",
    description="Get progress for an active sampled comparison job.",
)
async def get_job_progress(
    job_id: str,
    service: DriftMonitorServiceDep,
) -> JobProgressResponse:
    """Get progress for an active comparison job.

    Returns current progress including:
    - Chunks processed
    - Rows processed
    - Elapsed and estimated remaining time
    - Interim drift detection results
    """
    progress = await service.get_job_progress(job_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Job not found or completed")

    return JobProgressResponse(**progress)


@router.post(
    "/drift/jobs/{job_id}/cancel",
    response_model=MessageResponse,
    summary="Cancel comparison job",
    description="Cancel an active sampled comparison job.",
)
async def cancel_job(
    job_id: str,
    service: DriftMonitorServiceDep,
) -> MessageResponse:
    """Cancel an active comparison job."""
    cancelled = await service.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Job not found or already completed")

    return MessageResponse(message="Job cancelled")


# Helper functions


def _monitor_to_dict(monitor) -> dict:
    """Convert monitor model to dictionary."""
    # Get source names from relationships if available
    baseline_source_name = None
    current_source_name = None
    if hasattr(monitor, "baseline_source") and monitor.baseline_source:
        baseline_source_name = monitor.baseline_source.name
    if hasattr(monitor, "current_source") and monitor.current_source:
        current_source_name = monitor.current_source.name

    return {
        "id": monitor.id,
        "name": monitor.name,
        "baseline_source_id": monitor.baseline_source_id,
        "current_source_id": monitor.current_source_id,
        "baseline_source_name": baseline_source_name,
        "current_source_name": current_source_name,
        "cron_expression": monitor.cron_expression,
        "method": monitor.method,
        "threshold": monitor.threshold,
        "columns": monitor.columns_json,
        "alert_on_drift": monitor.alert_on_drift,
        "alert_threshold_critical": monitor.alert_threshold_critical,
        "alert_threshold_high": monitor.alert_threshold_high,
        "notification_channel_ids": monitor.notification_channel_ids_json,
        "status": monitor.status,
        "last_run_at": monitor.last_run_at,
        "last_drift_detected": monitor.last_drift_detected,
        "total_runs": monitor.total_runs,
        "drift_detected_count": monitor.drift_detected_count,
        "consecutive_drift_count": monitor.consecutive_drift_count,
        "created_at": monitor.created_at,
        "updated_at": monitor.updated_at,
    }


def _alert_to_dict(alert) -> dict:
    """Convert alert model to dictionary."""
    return {
        "id": alert.id,
        "monitor_id": alert.monitor_id,
        "comparison_id": alert.run_id,  # Map run_id to comparison_id for frontend compatibility
        "severity": alert.severity,
        "drift_percentage": alert.drift_score,  # Map drift_score to drift_percentage
        "drifted_columns": alert.affected_columns or [],  # Map affected_columns to drifted_columns
        "message": alert.message,
        "status": alert.status,
        "acknowledged_at": alert.acknowledged_at,
        "acknowledged_by": alert.acknowledged_by,
        "resolved_at": alert.resolved_at,
        "notes": alert.notes,
        "created_at": alert.created_at,
        "updated_at": alert.updated_at,
    }
