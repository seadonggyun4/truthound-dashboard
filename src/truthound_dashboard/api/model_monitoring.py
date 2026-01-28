"""API endpoints for ML Model Monitoring.

Provides REST API for:
- Model registration and management
- Prediction recording and metrics
- Alert rules and handlers
- Dashboard data

All data is persisted to the database.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.model_monitoring import ModelMonitoringService
from ..db import get_db_session
from ..schemas.base import MessageResponse
from ..schemas.model_monitoring import (
    AcknowledgeAlertRequest,
    AlertHandlerListResponse,
    AlertHandlerResponse,
    AlertInstance,
    AlertListResponse,
    AlertRuleListResponse,
    AlertRuleResponse,
    AlertSeverity,
    CreateAlertHandlerRequest,
    CreateAlertRuleRequest,
    MetricsResponse,
    MetricSummary,
    ModelDashboardData,
    ModelStatus,
    MonitoringOverview,
    RecordPredictionRequest,
    RecordPredictionResponse,
    RegisteredModelListResponse,
    RegisteredModelResponse,
    RegisterModelRequest,
    UpdateAlertHandlerRequest,
    UpdateAlertRuleRequest,
    UpdateModelRequest,
)

router = APIRouter(prefix="/model-monitoring", tags=["model-monitoring"])


def get_service(session: AsyncSession = Depends(get_db_session)) -> ModelMonitoringService:
    """Get model monitoring service instance."""
    return ModelMonitoringService(session)


# =============================================================================
# Model Registration Endpoints
# =============================================================================


@router.get("/models", response_model=RegisteredModelListResponse)
async def list_models(
    status: ModelStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
) -> RegisteredModelListResponse:
    """List all registered models."""
    status_filter = status.value if status else None
    models, total = await service.list_models(
        status=status_filter, offset=offset, limit=limit
    )

    items = [
        RegisteredModelResponse(
            id=m.id,
            name=m.name,
            version=m.version,
            description=m.description or "",
            status=ModelStatus(m.status),
            config=m.config,
            metadata=m.metadata_json or {},
            prediction_count=m.prediction_count,
            last_prediction_at=m.last_prediction_at,
            current_drift_score=m.current_drift_score,
            health_score=m.health_score,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in models
    ]

    return RegisteredModelListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/models", response_model=RegisteredModelResponse, status_code=201)
async def register_model(
    request: RegisterModelRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> RegisteredModelResponse:
    """Register a new model for monitoring."""
    model = await service.register_model(
        name=request.name,
        version=request.version,
        description=request.description,
        config=request.config.model_dump() if request.config else None,
        metadata=request.metadata,
    )

    return RegisteredModelResponse(
        id=model.id,
        name=model.name,
        version=model.version,
        description=model.description or "",
        status=ModelStatus(model.status),
        config=model.config,
        metadata=model.metadata_json or {},
        prediction_count=model.prediction_count,
        last_prediction_at=model.last_prediction_at,
        current_drift_score=model.current_drift_score,
        health_score=model.health_score,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.get("/models/{model_id}", response_model=RegisteredModelResponse)
async def get_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> RegisteredModelResponse:
    """Get a registered model by ID."""
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return RegisteredModelResponse(
        id=model.id,
        name=model.name,
        version=model.version,
        description=model.description or "",
        status=ModelStatus(model.status),
        config=model.config,
        metadata=model.metadata_json or {},
        prediction_count=model.prediction_count,
        last_prediction_at=model.last_prediction_at,
        current_drift_score=model.current_drift_score,
        health_score=model.health_score,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.put("/models/{model_id}", response_model=RegisteredModelResponse)
async def update_model(
    model_id: str,
    request: UpdateModelRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> RegisteredModelResponse:
    """Update a registered model."""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.version is not None:
        updates["version"] = request.version
    if request.description is not None:
        updates["description"] = request.description
    if request.status is not None:
        updates["status"] = request.status.value
    if request.config is not None:
        updates["config"] = request.config.model_dump()
    if request.metadata is not None:
        updates["metadata_json"] = request.metadata

    model = await service.update_model(model_id, **updates)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return RegisteredModelResponse(
        id=model.id,
        name=model.name,
        version=model.version,
        description=model.description or "",
        status=ModelStatus(model.status),
        config=model.config,
        metadata=model.metadata_json or {},
        prediction_count=model.prediction_count,
        last_prediction_at=model.last_prediction_at,
        current_drift_score=model.current_drift_score,
        health_score=model.health_score,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.delete("/models/{model_id}", response_model=MessageResponse)
async def delete_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> MessageResponse:
    """Delete a registered model."""
    deleted = await service.delete_model(model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")

    return MessageResponse(message="Model deleted")


@router.post("/models/{model_id}/pause", response_model=MessageResponse)
async def pause_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> MessageResponse:
    """Pause monitoring for a model."""
    model = await service.pause_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return MessageResponse(message="Model monitoring paused")


@router.post("/models/{model_id}/resume", response_model=MessageResponse)
async def resume_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> MessageResponse:
    """Resume monitoring for a model."""
    model = await service.resume_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return MessageResponse(message="Model monitoring resumed")


# =============================================================================
# Prediction Recording Endpoints
# =============================================================================


@router.post(
    "/models/{model_id}/predictions",
    response_model=RecordPredictionResponse,
    status_code=201,
)
async def record_prediction(
    model_id: str,
    request: RecordPredictionRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> RecordPredictionResponse:
    """Record a model prediction."""
    try:
        prediction = await service.record_prediction(
            model_id=model_id,
            features=request.features,
            prediction=request.prediction,
            actual=request.actual,
            latency_ms=request.latency_ms,
            metadata=request.metadata,
        )

        return RecordPredictionResponse(
            id=prediction.id,
            model_id=model_id,
            recorded_at=prediction.recorded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/models/{model_id}/metrics", response_model=MetricsResponse)
async def get_model_metrics(
    model_id: str,
    hours: int = Query(24, ge=1, le=168),
    service: ModelMonitoringService = Depends(get_service),
) -> MetricsResponse:
    """Get metrics for a model."""
    try:
        metrics_data = await service.get_model_metrics(model_id, hours)

        return MetricsResponse(
            model_id=metrics_data["model_id"],
            model_name=metrics_data["model_name"],
            time_range_hours=metrics_data["time_range_hours"],
            metrics=[MetricSummary(**m) for m in metrics_data["metrics"]],
            data_points=metrics_data["data_points"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Alert Rule Endpoints
# =============================================================================


@router.get("/rules", response_model=AlertRuleListResponse)
async def list_alert_rules(
    model_id: str | None = None,
    active_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
) -> AlertRuleListResponse:
    """List all alert rules."""
    rules = await service.get_alert_rules(model_id=model_id, active_only=active_only)

    # Apply pagination
    total = len(rules)
    paginated = list(rules)[offset : offset + limit]

    items = [
        AlertRuleResponse(
            id=r.id,
            name=r.name,
            model_id=r.model_id,
            rule_type=r.rule_type,
            severity=AlertSeverity(r.severity),
            config=r.config,
            is_active=r.is_active,
            last_triggered_at=r.last_triggered_at,
            trigger_count=r.trigger_count,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in paginated
    ]

    return AlertRuleListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(
    request: CreateAlertRuleRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> AlertRuleResponse:
    """Create a new alert rule."""
    try:
        rule = await service.create_alert_rule(
            model_id=request.model_id,
            name=request.name,
            rule_type=request.rule_type.value,
            config=request.config,
            severity=request.severity.value,
        )

        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            model_id=rule.model_id,
            rule_type=rule.rule_type,
            severity=AlertSeverity(rule.severity),
            config=rule.config,
            is_active=rule.is_active,
            last_triggered_at=rule.last_triggered_at,
            trigger_count=rule.trigger_count,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> AlertRuleResponse:
    """Get an alert rule by ID."""
    rules = await service.get_alert_rules()
    rule = next((r for r in rules if r.id == rule_id), None)

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return AlertRuleResponse(
        id=rule.id,
        name=rule.name,
        model_id=rule.model_id,
        rule_type=rule.rule_type,
        severity=AlertSeverity(rule.severity),
        config=rule.config,
        is_active=rule.is_active,
        last_triggered_at=rule.last_triggered_at,
        trigger_count=rule.trigger_count,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    request: UpdateAlertRuleRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> AlertRuleResponse:
    """Update an alert rule."""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.severity is not None:
        updates["severity"] = request.severity.value
    if request.config is not None:
        updates["config"] = request.config
    if request.is_active is not None:
        updates["is_active"] = request.is_active

    rule = await service.update_alert_rule(rule_id, **updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return AlertRuleResponse(
        id=rule.id,
        name=rule.name,
        model_id=rule.model_id,
        rule_type=rule.rule_type,
        severity=AlertSeverity(rule.severity),
        config=rule.config,
        is_active=rule.is_active,
        last_triggered_at=rule.last_triggered_at,
        trigger_count=rule.trigger_count,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.delete("/rules/{rule_id}", response_model=MessageResponse)
async def delete_alert_rule(
    rule_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> MessageResponse:
    """Delete an alert rule."""
    deleted = await service.delete_alert_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return MessageResponse(message="Alert rule deleted")


# =============================================================================
# Alert Handler Endpoints
# =============================================================================


@router.get("/handlers", response_model=AlertHandlerListResponse)
async def list_alert_handlers(
    active_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
) -> AlertHandlerListResponse:
    """List all alert handlers."""
    handlers = await service.get_alert_handlers(active_only=active_only)

    # Apply pagination
    total = len(handlers)
    paginated = list(handlers)[offset : offset + limit]

    items = [
        AlertHandlerResponse(
            id=h.id,
            name=h.name,
            handler_type=h.handler_type,
            config=h.config,
            is_active=h.is_active,
            last_sent_at=h.last_sent_at,
            send_count=h.send_count,
            failure_count=h.failure_count,
            created_at=h.created_at,
            updated_at=h.updated_at,
        )
        for h in paginated
    ]

    return AlertHandlerListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/handlers", response_model=AlertHandlerResponse, status_code=201)
async def create_alert_handler(
    request: CreateAlertHandlerRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> AlertHandlerResponse:
    """Create a new alert handler."""
    handler = await service.create_alert_handler(
        name=request.name,
        handler_type=request.handler_type.value,
        config=request.config,
    )

    return AlertHandlerResponse(
        id=handler.id,
        name=handler.name,
        handler_type=handler.handler_type,
        config=handler.config,
        is_active=handler.is_active,
        last_sent_at=handler.last_sent_at,
        send_count=handler.send_count,
        failure_count=handler.failure_count,
        created_at=handler.created_at,
        updated_at=handler.updated_at,
    )


@router.put("/handlers/{handler_id}", response_model=AlertHandlerResponse)
async def update_alert_handler(
    handler_id: str,
    request: UpdateAlertHandlerRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> AlertHandlerResponse:
    """Update an alert handler."""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.config is not None:
        updates["config"] = request.config
    if request.is_active is not None:
        updates["is_active"] = request.is_active

    handler = await service.update_alert_handler(handler_id, **updates)
    if not handler:
        raise HTTPException(status_code=404, detail="Alert handler not found")

    return AlertHandlerResponse(
        id=handler.id,
        name=handler.name,
        handler_type=handler.handler_type,
        config=handler.config,
        is_active=handler.is_active,
        last_sent_at=handler.last_sent_at,
        send_count=handler.send_count,
        failure_count=handler.failure_count,
        created_at=handler.created_at,
        updated_at=handler.updated_at,
    )


@router.delete("/handlers/{handler_id}", response_model=MessageResponse)
async def delete_alert_handler(
    handler_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> MessageResponse:
    """Delete an alert handler."""
    deleted = await service.delete_alert_handler(handler_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert handler not found")

    return MessageResponse(message="Alert handler deleted")


@router.post("/handlers/{handler_id}/test")
async def test_alert_handler(
    handler_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> dict:
    """Test an alert handler by sending a test notification.

    Validates the handler configuration and simulates sending a test notification.
    """
    try:
        result = await service.test_alert_handler(handler_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Alert Instance Endpoints
# =============================================================================


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    model_id: str | None = None,
    active_only: bool = False,
    severity: AlertSeverity | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
) -> AlertListResponse:
    """List alerts."""
    severity_filter = severity.value if severity else None
    alerts, total = await service.get_alerts(
        model_id=model_id,
        active_only=active_only,
        severity=severity_filter,
        offset=offset,
        limit=limit,
    )

    items = [
        AlertInstance(
            id=a.id,
            rule_id=a.rule_id,
            model_id=a.model_id,
            severity=AlertSeverity(a.severity),
            message=a.message,
            metric_value=a.metric_value,
            threshold_value=a.threshold_value,
            acknowledged=a.acknowledged,
            acknowledged_by=a.acknowledged_by,
            acknowledged_at=a.acknowledged_at,
            resolved=a.resolved,
            resolved_at=a.resolved_at,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in alerts
    ]

    return AlertListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertInstance)
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> AlertInstance:
    """Acknowledge an alert."""
    alert = await service.acknowledge_alert(alert_id, request.actor)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertInstance(
        id=alert.id,
        rule_id=alert.rule_id,
        model_id=alert.model_id,
        severity=AlertSeverity(alert.severity),
        message=alert.message,
        metric_value=alert.metric_value,
        threshold_value=alert.threshold_value,
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        resolved=alert.resolved,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.post("/alerts/{alert_id}/resolve", response_model=AlertInstance)
async def resolve_alert(
    alert_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> AlertInstance:
    """Resolve an alert."""
    alert = await service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertInstance(
        id=alert.id,
        rule_id=alert.rule_id,
        model_id=alert.model_id,
        severity=AlertSeverity(alert.severity),
        message=alert.message,
        metric_value=alert.metric_value,
        threshold_value=alert.threshold_value,
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        resolved=alert.resolved,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get("/overview", response_model=MonitoringOverview)
async def get_monitoring_overview(
    service: ModelMonitoringService = Depends(get_service),
) -> MonitoringOverview:
    """Get monitoring overview for dashboard."""
    overview = await service.get_monitoring_overview()

    return MonitoringOverview(
        total_models=overview["total_models"],
        active_models=overview["active_models"],
        degraded_models=overview["degraded_models"],
        total_predictions_24h=overview["total_predictions_24h"],
        active_alerts=overview["active_alerts"],
        models_with_drift=overview["models_with_drift"],
        avg_latency_ms=overview["avg_latency_ms"],
    )


@router.get("/models/{model_id}/dashboard", response_model=ModelDashboardData)
async def get_model_dashboard(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> ModelDashboardData:
    """Get dashboard data for a specific model."""
    try:
        dashboard = await service.get_model_dashboard(model_id)

        model_data = dashboard["model"]
        metrics_data = dashboard["metrics"]

        return ModelDashboardData(
            model=RegisteredModelResponse(
                id=model_data["id"],
                name=model_data["name"],
                version=model_data["version"],
                description=model_data["description"] or "",
                status=ModelStatus(model_data["status"]),
                config=model_data["config"],
                metadata=model_data["metadata"] or {},
                prediction_count=model_data["prediction_count"],
                last_prediction_at=model_data["last_prediction_at"],
                current_drift_score=model_data["current_drift_score"],
                health_score=model_data["health_score"],
                created_at=model_data["created_at"],
                updated_at=model_data["updated_at"],
            ),
            metrics=MetricsResponse(
                model_id=metrics_data["model_id"],
                model_name=metrics_data["model_name"],
                time_range_hours=metrics_data["time_range_hours"],
                metrics=[MetricSummary(**m) for m in metrics_data["metrics"]],
                data_points=metrics_data["data_points"],
            ),
            active_alerts=[
                AlertInstance(
                    id=a["id"],
                    rule_id=a["rule_id"],
                    model_id=a["model_id"],
                    severity=AlertSeverity(a["severity"]),
                    message=a["message"],
                    metric_value=a["metric_value"],
                    threshold_value=a["threshold_value"],
                    acknowledged=a["acknowledged"],
                    acknowledged_by=a["acknowledged_by"],
                    acknowledged_at=a["acknowledged_at"],
                    resolved=a["resolved"],
                    resolved_at=a["resolved_at"],
                    created_at=a["created_at"],
                    updated_at=a["updated_at"],
                )
                for a in dashboard["active_alerts"]
            ],
            recent_predictions=dashboard["recent_predictions"],
            health_status=dashboard["health_status"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/models/{model_id}/evaluate-rules")
async def evaluate_model_rules(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
) -> dict:
    """Evaluate all active rules for a model and create alerts if triggered."""
    alerts = await service.evaluate_rules(model_id)

    return {
        "model_id": model_id,
        "alerts_created": len(alerts),
        "alert_ids": [a.id for a in alerts],
    }


# =============================================================================
# Truthound Integration - Drift Detection
# =============================================================================


class DriftDetectionRequest(BaseModel):
    """Request for drift detection using truthound th.compare()."""

    reference_source_id: str = Field(..., description="Source ID for reference/baseline data")
    current_source_id: str = Field(..., description="Source ID for current data to compare")
    method: str = Field(
        default="auto",
        description="Drift detection method (auto, psi, ks, js, wasserstein, chi2, etc.)",
    )
    columns: list[str] | None = Field(
        default=None,
        description="Specific columns to check (default: all)",
    )


class DriftDetectionResponse(BaseModel):
    """Response from drift detection."""

    model_id: str
    method: str
    has_drift: bool
    overall_score: float
    drift_threshold: float
    drifted_columns: list[str]
    column_scores: dict[str, float]
    timestamp: str


@router.post(
    "/models/{model_id}/detect-drift",
    response_model=DriftDetectionResponse,
    summary="Detect drift for a model",
    description="""
    Compute drift score using truthound th.compare().

    Available methods:
    - auto: Auto-select best method based on column type
    - psi: Population Stability Index (<0.1 stable, 0.1-0.25 small drift, >0.25 significant)
    - ks: Kolmogorov-Smirnov test
    - js: Jensen-Shannon divergence
    - wasserstein: Earth Mover's Distance
    - chi2: Chi-squared (categorical)
    - kl: Kullback-Leibler divergence
    - cvm: Cramér-von Mises test
    - anderson: Anderson-Darling test
    - hellinger: Hellinger distance
    - bhattacharyya: Bhattacharyya distance
    - tv: Total Variation distance
    - energy: Energy distance
    - mmd: Maximum Mean Discrepancy
    """,
)
async def detect_model_drift(
    model_id: str,
    request: DriftDetectionRequest,
    service: ModelMonitoringService = Depends(get_service),
) -> DriftDetectionResponse:
    """Detect drift between reference and current data for a model."""
    from truthound_dashboard.core.services import SourceService
    from truthound_dashboard.db import get_async_session

    # Get source data
    async with get_async_session() as session:
        source_service = SourceService(session)

        reference_source = await source_service.get_source(request.reference_source_id)
        if reference_source is None:
            raise HTTPException(status_code=404, detail=f"Reference source '{request.reference_source_id}' not found")

        current_source = await source_service.get_source(request.current_source_id)
        if current_source is None:
            raise HTTPException(status_code=404, detail=f"Current source '{request.current_source_id}' not found")

    try:
        result = await service.compute_drift_score(
            model_id=model_id,
            reference_data=reference_source.connection_string,
            current_data=current_source.connection_string,
            method=request.method,
            columns=request.columns,
        )

        return DriftDetectionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drift detection failed: {str(e)}")


# =============================================================================
# Truthound Integration - Quality Metrics
# =============================================================================


class QualityMetricsResponse(BaseModel):
    """Response from quality metrics computation."""

    model_id: str
    enabled: bool
    has_data: bool = False
    model_type: str | None = None
    sample_count: int | None = None
    time_range_hours: int | None = None
    metrics: dict[str, float | None] | None = None
    message: str | None = None
    timestamp: str | None = None


@router.get(
    "/models/{model_id}/quality-metrics",
    response_model=QualityMetricsResponse,
    summary="Get quality metrics for a model",
    description="""
    Compute quality metrics from predictions with actual values.

    For classification models:
    - accuracy: Overall accuracy
    - precision: Precision (binary only)
    - recall: Recall (binary only)
    - f1_score: F1 score (binary only)

    For regression models:
    - mae: Mean Absolute Error
    - mse: Mean Squared Error
    - rmse: Root Mean Squared Error
    """,
)
async def get_model_quality_metrics(
    model_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    service: ModelMonitoringService = Depends(get_service),
) -> QualityMetricsResponse:
    """Get quality metrics for a model."""
    try:
        result = await service.compute_quality_metrics(model_id, hours=hours)
        return QualityMetricsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
