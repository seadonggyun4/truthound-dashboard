"""Observability API endpoints.

This module provides endpoints for audit logging, metrics, and tracing
using truthound's observability module.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from truthound_dashboard.core.store_manager import get_store_manager
from truthound_dashboard.schemas.observability import (
    AuditEventListResponse,
    AuditEventResponse,
    AuditEventTypeEnum,
    AuditQueryRequest,
    AuditStatsResponse,
    AuditStatusEnum,
    MetricsResponse,
    MetricValue,
    ObservabilityConfigRequest,
    ObservabilityConfigResponse,
    ObservabilityStatsResponse,
    SpanListResponse,
    SpanResponse,
    StoreMetricsResponse,
    TracingStatsResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Store observability config
_observability_config = ObservabilityConfigRequest()


@router.get(
    "/config",
    response_model=ObservabilityConfigResponse,
    summary="Get observability config",
    description="Get current observability configuration",
)
async def get_observability_config() -> ObservabilityConfigResponse:
    """Get current observability configuration.

    Returns:
        Current observability configuration.
    """
    return ObservabilityConfigResponse(**_observability_config.model_dump())


@router.put(
    "/config",
    response_model=ObservabilityConfigResponse,
    summary="Update observability config",
    description="Update observability configuration",
)
async def update_observability_config(
    config: ObservabilityConfigRequest,
) -> ObservabilityConfigResponse:
    """Update observability configuration.

    Args:
        config: New observability configuration.

    Returns:
        Updated configuration.
    """
    global _observability_config
    _observability_config = config

    logger.info(
        f"Observability config updated: "
        f"audit={config.enable_audit}, "
        f"metrics={config.enable_metrics}, "
        f"tracing={config.enable_tracing}"
    )

    return ObservabilityConfigResponse(**config.model_dump())


@router.get(
    "/stats",
    response_model=ObservabilityStatsResponse,
    summary="Get observability stats",
    description="Get combined statistics from audit, metrics, and tracing",
)
async def get_observability_stats() -> ObservabilityStatsResponse:
    """Get combined observability statistics.

    Returns:
        Combined statistics from all observability pillars.
    """
    store_manager = get_store_manager()
    if not store_manager._initialized:
        store_manager.initialize()

    # Audit stats
    audit_stats = AuditStatsResponse(
        total_events=0,
        events_today=0,
        events_this_week=0,
        by_event_type={},
        by_status={},
        error_rate=0.0,
        avg_duration_ms=None,
    )

    try:
        events = store_manager.get_audit_events(limit=1000)
        if events:
            today = datetime.utcnow().date()
            week_ago = datetime.utcnow() - timedelta(days=7)

            events_today = sum(1 for e in events if e.timestamp.date() == today)
            events_week = sum(1 for e in events if e.timestamp >= week_ago)

            by_type: dict[str, int] = {}
            by_status: dict[str, int] = {}
            error_count = 0
            total_duration = 0.0
            duration_count = 0

            for e in events:
                by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
                by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
                if e.status.value in ("failure", "error"):
                    error_count += 1
                if e.duration_ms:
                    total_duration += e.duration_ms
                    duration_count += 1

            audit_stats = AuditStatsResponse(
                total_events=len(events),
                events_today=events_today,
                events_this_week=events_week,
                by_event_type=by_type,
                by_status=by_status,
                error_rate=error_count / len(events) if events else 0.0,
                avg_duration_ms=total_duration / duration_count if duration_count else None,
            )
    except Exception as e:
        logger.warning(f"Failed to get audit stats: {e}")

    # Store metrics
    store_metrics = StoreMetricsResponse(
        operations_total=0,
        operations_by_type={},
        bytes_read_total=0,
        bytes_written_total=0,
        active_connections=0,
        cache_hits=0,
        cache_misses=0,
        cache_hit_rate=0.0,
        errors_total=0,
        errors_by_type={},
        avg_operation_duration_ms=None,
    )

    try:
        metrics = store_manager.get_store_metrics()
        if metrics:
            store_metrics = StoreMetricsResponse(**metrics)
    except Exception as e:
        logger.warning(f"Failed to get store metrics: {e}")

    # Tracing stats (if enabled)
    tracing_stats = None
    if _observability_config.enable_tracing:
        tracing_stats = TracingStatsResponse(
            enabled=True,
            total_traces=0,
            total_spans=0,
            avg_trace_duration_ms=None,
            traces_today=0,
            error_rate=0.0,
            by_service={},
        )

    return ObservabilityStatsResponse(
        audit=audit_stats,
        store_metrics=store_metrics,
        tracing=tracing_stats,
        last_updated=datetime.utcnow(),
    )


# =============================================================================
# Audit Endpoints
# =============================================================================


@router.get(
    "/audit/events",
    response_model=AuditEventListResponse,
    summary="List audit events",
    description="Query audit events with filters",
)
async def list_audit_events(
    event_type: AuditEventTypeEnum | None = Query(None, description="Filter by event type"),
    status: AuditStatusEnum | None = Query(None, description="Filter by status"),
    start_time: datetime | None = Query(None, description="Filter after this time"),
    end_time: datetime | None = Query(None, description="Filter before this time"),
    item_id: str | None = Query(None, description="Filter by item ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum events"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> AuditEventListResponse:
    """List audit events with optional filters.

    Args:
        event_type: Filter by event type.
        status: Filter by status.
        start_time: Filter events after this time.
        end_time: Filter events before this time.
        item_id: Filter by item ID.
        limit: Maximum events to return.
        offset: Offset for pagination.

    Returns:
        List of audit events.
    """
    store_manager = get_store_manager()
    if not store_manager._initialized:
        store_manager.initialize()

    try:
        # Convert enum to truthound enum if provided
        th_event_type = None
        if event_type:
            from truthound.stores.observability.audit import AuditEventType
            th_event_type = AuditEventType(event_type.value)

        events = store_manager.get_audit_events(
            event_type=th_event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit + offset,  # Get extra for offset
        )

        # Apply offset and additional filters
        filtered_events = []
        for e in events[offset:]:
            if item_id and e.item_id != item_id:
                continue
            if status and e.status.value != status.value:
                continue

            filtered_events.append(
                AuditEventResponse(
                    event_id=e.event_id,
                    event_type=AuditEventTypeEnum(e.event_type.value),
                    timestamp=e.timestamp,
                    status=AuditStatusEnum(e.status.value),
                    store_type=e.store_type,
                    store_id=e.store_id,
                    item_id=e.item_id,
                    user_id=e.user_id,
                    session_id=e.session_id,
                    duration_ms=e.duration_ms,
                    metadata=e.metadata,
                    error_message=e.error_message,
                    ip_address=e.ip_address,
                    user_agent=e.user_agent,
                )
            )

            if len(filtered_events) >= limit:
                break

        return AuditEventListResponse(
            items=filtered_events,
            total=len(events),
            page=offset // limit + 1 if limit else 1,
            page_size=limit,
        )

    except Exception as e:
        logger.error(f"Failed to list audit events: {e}")
        return AuditEventListResponse(
            items=[],
            total=0,
            page=1,
            page_size=limit,
        )


@router.get(
    "/audit/stats",
    response_model=AuditStatsResponse,
    summary="Get audit stats",
    description="Get audit event statistics",
)
async def get_audit_stats() -> AuditStatsResponse:
    """Get audit event statistics.

    Returns:
        Audit statistics.
    """
    store_manager = get_store_manager()
    if not store_manager._initialized:
        store_manager.initialize()

    try:
        events = store_manager.get_audit_events(limit=10000)

        if not events:
            return AuditStatsResponse(
                total_events=0,
                events_today=0,
                events_this_week=0,
                by_event_type={},
                by_status={},
                error_rate=0.0,
                avg_duration_ms=None,
            )

        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)

        events_today = sum(1 for e in events if e.timestamp.date() == today)
        events_week = sum(1 for e in events if e.timestamp >= week_ago)

        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        error_count = 0
        total_duration = 0.0
        duration_count = 0

        for e in events:
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
            if e.status.value in ("failure", "error"):
                error_count += 1
            if e.duration_ms:
                total_duration += e.duration_ms
                duration_count += 1

        return AuditStatsResponse(
            total_events=len(events),
            events_today=events_today,
            events_this_week=events_week,
            by_event_type=by_type,
            by_status=by_status,
            error_rate=error_count / len(events) if events else 0.0,
            avg_duration_ms=total_duration / duration_count if duration_count else None,
        )

    except Exception as e:
        logger.error(f"Failed to get audit stats: {e}")
        return AuditStatsResponse(
            total_events=0,
            events_today=0,
            events_this_week=0,
            by_event_type={},
            by_status={},
            error_rate=0.0,
            avg_duration_ms=None,
        )


# =============================================================================
# Metrics Endpoints
# =============================================================================


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Get all metrics",
    description="Get all current metrics",
)
async def get_metrics() -> MetricsResponse:
    """Get all current metrics.

    Returns:
        All metrics organized by type.
    """
    store_manager = get_store_manager()
    if not store_manager._initialized:
        store_manager.initialize()

    try:
        raw_metrics = store_manager.get_store_metrics()

        # Convert to structured response
        counters = []
        gauges = []

        if raw_metrics:
            # Operations are counters
            if "operations_total" in raw_metrics:
                counters.append(MetricValue(
                    name="store_operations_total",
                    value=float(raw_metrics["operations_total"]),
                    labels={"store": "dashboard"},
                ))

            if "bytes_read_total" in raw_metrics:
                counters.append(MetricValue(
                    name="store_bytes_read_total",
                    value=float(raw_metrics["bytes_read_total"]),
                    labels={"store": "dashboard"},
                ))

            if "bytes_written_total" in raw_metrics:
                counters.append(MetricValue(
                    name="store_bytes_written_total",
                    value=float(raw_metrics["bytes_written_total"]),
                    labels={"store": "dashboard"},
                ))

            if "cache_hits" in raw_metrics:
                counters.append(MetricValue(
                    name="store_cache_hits_total",
                    value=float(raw_metrics["cache_hits"]),
                    labels={"store": "dashboard"},
                ))

            if "cache_misses" in raw_metrics:
                counters.append(MetricValue(
                    name="store_cache_misses_total",
                    value=float(raw_metrics["cache_misses"]),
                    labels={"store": "dashboard"},
                ))

            if "errors_total" in raw_metrics:
                counters.append(MetricValue(
                    name="store_errors_total",
                    value=float(raw_metrics["errors_total"]),
                    labels={"store": "dashboard"},
                ))

            # Active connections is a gauge
            if "active_connections" in raw_metrics:
                gauges.append(MetricValue(
                    name="store_connections_active",
                    value=float(raw_metrics["active_connections"]),
                    labels={"store": "dashboard"},
                ))

            # Cache hit rate is a gauge
            if "cache_hit_rate" in raw_metrics:
                gauges.append(MetricValue(
                    name="store_cache_hit_rate",
                    value=float(raw_metrics["cache_hit_rate"]),
                    labels={"store": "dashboard"},
                ))

        return MetricsResponse(
            counters=counters,
            gauges=gauges,
            histograms=[],
            summaries=[],
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return MetricsResponse(
            counters=[],
            gauges=[],
            histograms=[],
            summaries=[],
            timestamp=datetime.utcnow(),
        )


@router.get(
    "/metrics/store",
    response_model=StoreMetricsResponse,
    summary="Get store metrics",
    description="Get store-specific metrics",
)
async def get_store_metrics() -> StoreMetricsResponse:
    """Get store-specific metrics.

    Returns:
        Store metrics.
    """
    store_manager = get_store_manager()
    if not store_manager._initialized:
        store_manager.initialize()

    try:
        metrics = store_manager.get_store_metrics()

        if not metrics:
            return StoreMetricsResponse()

        return StoreMetricsResponse(
            operations_total=metrics.get("operations_total", 0),
            operations_by_type=metrics.get("operations_by_type", {}),
            bytes_read_total=metrics.get("bytes_read_total", 0),
            bytes_written_total=metrics.get("bytes_written_total", 0),
            active_connections=metrics.get("active_connections", 0),
            cache_hits=metrics.get("cache_hits", 0),
            cache_misses=metrics.get("cache_misses", 0),
            cache_hit_rate=metrics.get("cache_hit_rate", 0.0),
            errors_total=metrics.get("errors_total", 0),
            errors_by_type=metrics.get("errors_by_type", {}),
            avg_operation_duration_ms=metrics.get("avg_operation_duration_ms"),
        )

    except Exception as e:
        logger.error(f"Failed to get store metrics: {e}")
        return StoreMetricsResponse()


# =============================================================================
# Tracing Endpoints
# =============================================================================


@router.get(
    "/tracing/stats",
    response_model=TracingStatsResponse,
    summary="Get tracing stats",
    description="Get distributed tracing statistics",
)
async def get_tracing_stats() -> TracingStatsResponse:
    """Get distributed tracing statistics.

    Returns:
        Tracing statistics.
    """
    if not _observability_config.enable_tracing:
        return TracingStatsResponse(
            enabled=False,
            total_traces=0,
            total_spans=0,
            avg_trace_duration_ms=None,
            traces_today=0,
            error_rate=0.0,
            by_service={},
        )

    # In a full implementation, this would query the tracing backend
    return TracingStatsResponse(
        enabled=True,
        total_traces=0,
        total_spans=0,
        avg_trace_duration_ms=None,
        traces_today=0,
        error_rate=0.0,
        by_service={},
    )


@router.get(
    "/tracing/spans",
    response_model=SpanListResponse,
    summary="List spans",
    description="List recent spans (requires tracing to be enabled)",
)
async def list_spans(
    limit: int = Query(100, ge=1, le=1000, description="Maximum spans"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> SpanListResponse:
    """List recent spans.

    Args:
        limit: Maximum spans to return.
        offset: Offset for pagination.

    Returns:
        List of spans.
    """
    if not _observability_config.enable_tracing:
        return SpanListResponse(
            items=[],
            total=0,
            page=1,
            page_size=limit,
        )

    # In a full implementation, this would query the tracing backend
    return SpanListResponse(
        items=[],
        total=0,
        page=offset // limit + 1 if limit else 1,
        page_size=limit,
    )
