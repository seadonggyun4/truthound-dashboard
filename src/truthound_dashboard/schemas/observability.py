"""Observability schemas for audit, metrics, and tracing.

This module defines schemas for observability API operations
using truthound's observability module.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseSchema, ListResponseWrapper


class AuditEventTypeEnum(str, Enum):
    """Audit event types from truthound."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    QUERY = "query"
    LIST = "list"
    COUNT = "count"
    INITIALIZE = "initialize"
    CLOSE = "close"
    FLUSH = "flush"
    BATCH_CREATE = "batch_create"
    BATCH_DELETE = "batch_delete"
    REPLICATE = "replicate"
    SYNC = "sync"
    MIGRATE = "migrate"
    ROLLBACK = "rollback"
    ACCESS_DENIED = "access_denied"
    ACCESS_GRANTED = "access_granted"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"


class AuditStatusEnum(str, Enum):
    """Audit status from truthound."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


class MetricTypeEnum(str, Enum):
    """Metric types from truthound."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class SpanKindEnum(str, Enum):
    """Span kinds from truthound."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatusEnum(str, Enum):
    """Span status from truthound."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


# =============================================================================
# Observability Configuration
# =============================================================================


class ObservabilityConfigRequest(BaseSchema):
    """Request to update observability configuration."""

    enable_audit: bool = Field(
        default=True,
        description="Enable audit logging",
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection",
    )
    enable_tracing: bool = Field(
        default=False,
        description="Enable distributed tracing",
    )
    audit_log_path: str | None = Field(
        default=None,
        description="Path for audit log files",
    )
    audit_rotate_daily: bool = Field(
        default=True,
        description="Rotate audit logs daily",
    )
    audit_max_events: int = Field(
        default=10000,
        ge=1000,
        le=1000000,
        description="Maximum events to keep in memory",
    )
    redact_fields: list[str] = Field(
        default_factory=lambda: ["password", "api_key", "token", "secret"],
        description="Fields to redact in audit logs",
    )
    metrics_prefix: str = Field(
        default="truthound_dashboard",
        max_length=50,
        description="Prefix for metric names",
    )
    tracing_service_name: str = Field(
        default="truthound-dashboard",
        max_length=100,
        description="Service name for tracing",
    )
    tracing_endpoint: str | None = Field(
        default=None,
        description="OpenTelemetry endpoint (e.g., http://localhost:4317)",
    )


class ObservabilityConfigResponse(ObservabilityConfigRequest):
    """Response with current observability configuration."""

    pass


# =============================================================================
# Audit Events
# =============================================================================


class AuditEventResponse(BaseSchema):
    """Audit event response."""

    event_id: str = Field(..., description="Unique event ID")
    event_type: AuditEventTypeEnum = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    status: AuditStatusEnum = Field(..., description="Event status")
    store_type: str = Field(..., description="Store backend type")
    store_id: str = Field(..., description="Store identifier")
    item_id: str | None = Field(default=None, description="Related item ID")
    user_id: str | None = Field(default=None, description="User who triggered event")
    session_id: str | None = Field(default=None, description="Session ID")
    duration_ms: float | None = Field(default=None, description="Operation duration")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )
    error_message: str | None = Field(default=None, description="Error message")
    ip_address: str | None = Field(default=None, description="Client IP address")
    user_agent: str | None = Field(default=None, description="Client user agent")


class AuditEventListResponse(ListResponseWrapper):
    """Response for audit event list."""

    items: list[AuditEventResponse]


class AuditQueryRequest(BaseSchema):
    """Request to query audit events."""

    event_type: AuditEventTypeEnum | None = Field(
        default=None, description="Filter by event type"
    )
    status: AuditStatusEnum | None = Field(
        default=None, description="Filter by status"
    )
    start_time: datetime | None = Field(
        default=None, description="Filter events after this time"
    )
    end_time: datetime | None = Field(
        default=None, description="Filter events before this time"
    )
    item_id: str | None = Field(
        default=None, description="Filter by item ID"
    )
    user_id: str | None = Field(
        default=None, description="Filter by user ID"
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum events to return"
    )
    offset: int = Field(
        default=0, ge=0, description="Offset for pagination"
    )


class AuditStatsResponse(BaseSchema):
    """Audit statistics response."""

    total_events: int = Field(default=0, ge=0, description="Total audit events")
    events_today: int = Field(default=0, ge=0, description="Events today")
    events_this_week: int = Field(default=0, ge=0, description="Events this week")
    by_event_type: dict[str, int] = Field(
        default_factory=dict, description="Events by type"
    )
    by_status: dict[str, int] = Field(
        default_factory=dict, description="Events by status"
    )
    error_rate: float = Field(
        default=0.0, ge=0, le=1, description="Error event rate"
    )
    avg_duration_ms: float | None = Field(
        default=None, description="Average operation duration"
    )


# =============================================================================
# Metrics
# =============================================================================


class MetricValue(BaseSchema):
    """A single metric value."""

    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    labels: dict[str, str] = Field(
        default_factory=dict, description="Metric labels"
    )
    timestamp: datetime | None = Field(
        default=None, description="Metric timestamp"
    )
    metric_type: MetricTypeEnum = Field(
        default=MetricTypeEnum.GAUGE, description="Metric type"
    )


class HistogramBucket(BaseSchema):
    """Histogram bucket."""

    le: float = Field(..., description="Less than or equal boundary")
    count: int = Field(..., ge=0, description="Count in bucket")


class HistogramValue(BaseSchema):
    """Histogram metric value."""

    name: str = Field(..., description="Metric name")
    count: int = Field(..., ge=0, description="Total count")
    sum: float = Field(..., description="Sum of values")
    buckets: list[HistogramBucket] = Field(
        default_factory=list, description="Histogram buckets"
    )
    labels: dict[str, str] = Field(
        default_factory=dict, description="Metric labels"
    )


class SummaryQuantile(BaseSchema):
    """Summary quantile."""

    quantile: float = Field(..., ge=0, le=1, description="Quantile (0-1)")
    value: float = Field(..., description="Value at quantile")


class SummaryValue(BaseSchema):
    """Summary metric value."""

    name: str = Field(..., description="Metric name")
    count: int = Field(..., ge=0, description="Total count")
    sum: float = Field(..., description="Sum of values")
    quantiles: list[SummaryQuantile] = Field(
        default_factory=list, description="Quantile values"
    )
    labels: dict[str, str] = Field(
        default_factory=dict, description="Metric labels"
    )


class MetricsResponse(BaseSchema):
    """Response with all metrics."""

    counters: list[MetricValue] = Field(
        default_factory=list, description="Counter metrics"
    )
    gauges: list[MetricValue] = Field(
        default_factory=list, description="Gauge metrics"
    )
    histograms: list[HistogramValue] = Field(
        default_factory=list, description="Histogram metrics"
    )
    summaries: list[SummaryValue] = Field(
        default_factory=list, description="Summary metrics"
    )
    timestamp: datetime = Field(..., description="Metrics snapshot timestamp")


class StoreMetricsResponse(BaseSchema):
    """Store-specific metrics response."""

    operations_total: int = Field(
        default=0, ge=0, description="Total operations"
    )
    operations_by_type: dict[str, int] = Field(
        default_factory=dict, description="Operations by type"
    )
    bytes_read_total: int = Field(
        default=0, ge=0, description="Total bytes read"
    )
    bytes_written_total: int = Field(
        default=0, ge=0, description="Total bytes written"
    )
    active_connections: int = Field(
        default=0, ge=0, description="Active connections"
    )
    cache_hits: int = Field(
        default=0, ge=0, description="Cache hits"
    )
    cache_misses: int = Field(
        default=0, ge=0, description="Cache misses"
    )
    cache_hit_rate: float = Field(
        default=0.0, ge=0, le=1, description="Cache hit rate"
    )
    errors_total: int = Field(
        default=0, ge=0, description="Total errors"
    )
    errors_by_type: dict[str, int] = Field(
        default_factory=dict, description="Errors by type"
    )
    avg_operation_duration_ms: float | None = Field(
        default=None, description="Average operation duration"
    )


# =============================================================================
# Tracing
# =============================================================================


class SpanContext(BaseSchema):
    """Span context for distributed tracing."""

    trace_id: str = Field(..., description="Trace ID")
    span_id: str = Field(..., description="Span ID")
    parent_span_id: str | None = Field(
        default=None, description="Parent span ID"
    )
    trace_flags: int = Field(default=0, description="Trace flags")
    trace_state: dict[str, str] = Field(
        default_factory=dict, description="Trace state"
    )


class SpanEvent(BaseSchema):
    """Event within a span."""

    name: str = Field(..., description="Event name")
    timestamp: datetime = Field(..., description="Event timestamp")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Event attributes"
    )


class SpanResponse(BaseSchema):
    """Span response for tracing."""

    name: str = Field(..., description="Span name")
    kind: SpanKindEnum = Field(..., description="Span kind")
    context: SpanContext = Field(..., description="Span context")
    start_time: datetime = Field(..., description="Span start time")
    end_time: datetime | None = Field(default=None, description="Span end time")
    duration_ms: float | None = Field(default=None, description="Duration in ms")
    status: SpanStatusEnum = Field(
        default=SpanStatusEnum.UNSET, description="Span status"
    )
    status_message: str | None = Field(
        default=None, description="Status message if error"
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Span attributes"
    )
    events: list[SpanEvent] = Field(
        default_factory=list, description="Span events"
    )


class SpanListResponse(ListResponseWrapper):
    """Response for span list."""

    items: list[SpanResponse]


class TraceResponse(BaseSchema):
    """Full trace with all spans."""

    trace_id: str = Field(..., description="Trace ID")
    spans: list[SpanResponse] = Field(
        default_factory=list, description="All spans in trace"
    )
    duration_ms: float | None = Field(
        default=None, description="Total trace duration"
    )
    service_count: int = Field(
        default=0, ge=0, description="Number of services involved"
    )
    error_count: int = Field(
        default=0, ge=0, description="Number of error spans"
    )


class TracingStatsResponse(BaseSchema):
    """Tracing statistics response."""

    enabled: bool = Field(..., description="Whether tracing is enabled")
    total_traces: int = Field(default=0, ge=0, description="Total traces")
    total_spans: int = Field(default=0, ge=0, description="Total spans")
    avg_trace_duration_ms: float | None = Field(
        default=None, description="Average trace duration"
    )
    traces_today: int = Field(default=0, ge=0, description="Traces today")
    error_rate: float = Field(
        default=0.0, ge=0, le=1, description="Error span rate"
    )
    by_service: dict[str, int] = Field(
        default_factory=dict, description="Spans by service"
    )


# =============================================================================
# Combined Statistics
# =============================================================================


class ObservabilityStatsResponse(BaseSchema):
    """Combined observability statistics."""

    audit: AuditStatsResponse = Field(
        default_factory=AuditStatsResponse,
        description="Audit statistics",
    )
    store_metrics: StoreMetricsResponse = Field(
        default_factory=StoreMetricsResponse,
        description="Store metrics",
    )
    tracing: TracingStatsResponse | None = Field(
        default=None,
        description="Tracing statistics (if enabled)",
    )
    last_updated: datetime = Field(..., description="Last update timestamp")
