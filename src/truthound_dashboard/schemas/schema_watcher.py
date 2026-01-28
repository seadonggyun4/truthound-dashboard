"""Schema Watcher Pydantic schemas.

This module defines schemas for the SchemaWatcher functionality,
including continuous schema monitoring, alerts, and run history.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import BaseSchema, IDMixin, PaginatedResponse, TimestampMixin


# =============================================================================
# Enums
# =============================================================================


class SchemaWatcherStatus(str, Enum):
    """Status of a schema watcher."""

    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class SchemaWatcherAlertStatus(str, Enum):
    """Status of a schema watcher alert."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class SchemaWatcherAlertSeverity(str, Enum):
    """Severity of schema watcher alert."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VersionStrategy(str, Enum):
    """Schema version numbering strategy."""

    SEMANTIC = "semantic"
    INCREMENTAL = "incremental"
    TIMESTAMP = "timestamp"
    GIT = "git"


class ImpactScope(str, Enum):
    """Scope of schema change impact."""

    LOCAL = "local"
    DOWNSTREAM = "downstream"
    SYSTEM = "system"


# =============================================================================
# Schema Watcher Schemas
# =============================================================================


class SchemaWatcherBase(BaseSchema):
    """Base schema for schema watcher."""

    name: str = Field(..., min_length=1, max_length=255, description="Watcher name")
    source_id: str = Field(..., description="Source ID to watch")
    poll_interval_seconds: int = Field(
        default=60,
        ge=10,
        le=86400,
        description="Polling interval in seconds (10s - 24h)",
    )
    only_breaking: bool = Field(
        default=False,
        description="Only alert on breaking changes",
    )
    enable_rename_detection: bool = Field(
        default=True,
        description="Enable column rename detection",
    )
    rename_similarity_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Similarity threshold for rename detection (0.5-1.0)",
    )
    version_strategy: VersionStrategy = Field(
        default=VersionStrategy.SEMANTIC,
        description="Version numbering strategy",
    )
    notify_on_change: bool = Field(
        default=True,
        description="Send notifications when changes detected",
    )
    track_history: bool = Field(
        default=True,
        description="Track changes in schema history",
    )


class SchemaWatcherCreate(SchemaWatcherBase):
    """Schema for creating a new schema watcher."""

    config: dict[str, Any] | None = Field(
        default=None,
        description="Additional configuration",
    )


class SchemaWatcherUpdate(BaseSchema):
    """Schema for updating a schema watcher."""

    name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Watcher name"
    )
    poll_interval_seconds: int | None = Field(
        default=None,
        ge=10,
        le=86400,
        description="Polling interval in seconds",
    )
    only_breaking: bool | None = Field(
        default=None,
        description="Only alert on breaking changes",
    )
    enable_rename_detection: bool | None = Field(
        default=None,
        description="Enable column rename detection",
    )
    rename_similarity_threshold: float | None = Field(
        default=None,
        ge=0.5,
        le=1.0,
        description="Similarity threshold for rename detection",
    )
    version_strategy: VersionStrategy | None = Field(
        default=None,
        description="Version numbering strategy",
    )
    notify_on_change: bool | None = Field(
        default=None,
        description="Send notifications when changes detected",
    )
    track_history: bool | None = Field(
        default=None,
        description="Track changes in schema history",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="Additional configuration",
    )


class SchemaWatcherResponse(SchemaWatcherBase, IDMixin, TimestampMixin):
    """Schema watcher response."""

    status: SchemaWatcherStatus = Field(..., description="Current watcher status")
    last_check_at: datetime | None = Field(
        default=None, description="When last checked"
    )
    last_change_at: datetime | None = Field(
        default=None, description="When last change detected"
    )
    next_check_at: datetime | None = Field(
        default=None, description="When next check scheduled"
    )
    check_count: int = Field(default=0, description="Total checks performed")
    change_count: int = Field(default=0, description="Total changes detected")
    error_count: int = Field(default=0, description="Consecutive error count")
    last_error: str | None = Field(default=None, description="Last error message")
    config: dict[str, Any] | None = Field(
        default=None, description="Additional configuration"
    )

    # Computed properties serialized
    is_active: bool = Field(default=False, description="Whether watcher is active")
    is_healthy: bool = Field(default=True, description="Whether watcher is healthy")
    detection_rate: float = Field(default=0.0, description="Change detection rate")

    # Source info
    source_name: str | None = Field(default=None, description="Source name")


class SchemaWatcherSummary(BaseSchema):
    """Summary of a schema watcher for lists."""

    id: str = Field(..., description="Watcher ID")
    name: str = Field(..., description="Watcher name")
    source_id: str = Field(..., description="Source ID")
    source_name: str | None = Field(default=None, description="Source name")
    status: SchemaWatcherStatus = Field(..., description="Current status")
    poll_interval_seconds: int = Field(..., description="Polling interval")
    check_count: int = Field(default=0, description="Total checks")
    change_count: int = Field(default=0, description="Total changes")
    last_check_at: datetime | None = Field(default=None, description="Last check time")
    next_check_at: datetime | None = Field(default=None, description="Next check time")
    created_at: datetime = Field(..., description="Created at")


# =============================================================================
# Schema Watcher Alert Schemas
# =============================================================================


class SchemaWatcherAlertBase(BaseSchema):
    """Base schema for schema watcher alert."""

    title: str = Field(..., max_length=500, description="Alert title")
    severity: SchemaWatcherAlertSeverity = Field(
        default=SchemaWatcherAlertSeverity.MEDIUM,
        description="Alert severity",
    )


class SchemaWatcherAlertResponse(SchemaWatcherAlertBase, IDMixin, TimestampMixin):
    """Schema watcher alert response."""

    watcher_id: str = Field(..., description="Watcher ID")
    source_id: str = Field(..., description="Source ID")
    from_version_id: str | None = Field(default=None, description="Previous version ID")
    to_version_id: str = Field(..., description="New version ID")
    status: SchemaWatcherAlertStatus = Field(..., description="Alert status")
    total_changes: int = Field(default=0, description="Total changes")
    breaking_changes: int = Field(default=0, description="Breaking changes")
    changes_summary: dict[str, Any] | None = Field(
        default=None, description="Changes summary"
    )
    impact_scope: ImpactScope | None = Field(default=None, description="Impact scope")
    affected_consumers: list[str] | None = Field(
        default=None, description="Affected consumers"
    )
    recommendations: list[str] | None = Field(
        default=None, description="Recommendations"
    )

    # Acknowledgment
    acknowledged_at: datetime | None = Field(default=None, description="Acknowledged at")
    acknowledged_by: str | None = Field(default=None, description="Acknowledged by")

    # Resolution
    resolved_at: datetime | None = Field(default=None, description="Resolved at")
    resolved_by: str | None = Field(default=None, description="Resolved by")
    resolution_notes: str | None = Field(default=None, description="Resolution notes")

    # Computed
    is_open: bool = Field(default=True, description="Whether alert is open")
    has_breaking_changes: bool = Field(
        default=False, description="Has breaking changes"
    )
    time_to_acknowledge: float | None = Field(
        default=None, description="Time to acknowledge (seconds)"
    )
    time_to_resolve: float | None = Field(
        default=None, description="Time to resolve (seconds)"
    )

    # Related info
    source_name: str | None = Field(default=None, description="Source name")
    watcher_name: str | None = Field(default=None, description="Watcher name")


class SchemaWatcherAlertSummary(BaseSchema):
    """Summary of a schema watcher alert for lists."""

    id: str = Field(..., description="Alert ID")
    watcher_id: str = Field(..., description="Watcher ID")
    source_id: str = Field(..., description="Source ID")
    title: str = Field(..., description="Alert title")
    severity: SchemaWatcherAlertSeverity = Field(..., description="Severity")
    status: SchemaWatcherAlertStatus = Field(..., description="Status")
    total_changes: int = Field(default=0, description="Total changes")
    breaking_changes: int = Field(default=0, description="Breaking changes")
    created_at: datetime = Field(..., description="Created at")
    source_name: str | None = Field(default=None, description="Source name")


class SchemaWatcherAlertAcknowledge(BaseSchema):
    """Schema for acknowledging an alert."""

    acknowledged_by: str | None = Field(
        default=None, max_length=255, description="Who acknowledged"
    )


class SchemaWatcherAlertResolve(BaseSchema):
    """Schema for resolving an alert."""

    resolved_by: str | None = Field(
        default=None, max_length=255, description="Who resolved"
    )
    resolution_notes: str | None = Field(
        default=None, max_length=2000, description="Resolution notes"
    )


# =============================================================================
# Schema Watcher Run Schemas
# =============================================================================


class SchemaWatcherRunStatus(str, Enum):
    """Status of a schema watcher run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SchemaWatcherRunResponse(BaseSchema, IDMixin):
    """Schema watcher run response."""

    watcher_id: str = Field(..., description="Watcher ID")
    source_id: str = Field(..., description="Source ID")
    started_at: datetime = Field(..., description="Run start time")
    completed_at: datetime | None = Field(default=None, description="Run end time")
    status: SchemaWatcherRunStatus = Field(..., description="Run status")
    changes_detected: int = Field(default=0, description="Changes detected")
    breaking_detected: int = Field(default=0, description="Breaking changes detected")
    version_created_id: str | None = Field(
        default=None, description="Created version ID"
    )
    alert_created_id: str | None = Field(default=None, description="Created alert ID")
    duration_ms: float | None = Field(default=None, description="Duration in ms")
    error_message: str | None = Field(default=None, description="Error message")
    metadata: dict[str, Any] | None = Field(default=None, description="Run metadata")

    # Computed
    is_successful: bool = Field(default=False, description="Whether run succeeded")
    has_changes: bool = Field(default=False, description="Whether changes detected")

    # Related info
    source_name: str | None = Field(default=None, description="Source name")
    watcher_name: str | None = Field(default=None, description="Watcher name")


class SchemaWatcherRunSummary(BaseSchema):
    """Summary of a schema watcher run for lists."""

    id: str = Field(..., description="Run ID")
    watcher_id: str = Field(..., description="Watcher ID")
    source_id: str = Field(..., description="Source ID")
    started_at: datetime = Field(..., description="Start time")
    status: SchemaWatcherRunStatus = Field(..., description="Status")
    changes_detected: int = Field(default=0, description="Changes detected")
    breaking_detected: int = Field(default=0, description="Breaking detected")
    duration_ms: float | None = Field(default=None, description="Duration")


# =============================================================================
# Statistics and Actions
# =============================================================================


class SchemaWatcherStatistics(BaseSchema):
    """Statistics for schema watchers."""

    total_watchers: int = Field(default=0, description="Total watchers")
    active_watchers: int = Field(default=0, description="Active watchers")
    paused_watchers: int = Field(default=0, description="Paused watchers")
    error_watchers: int = Field(default=0, description="Watchers with errors")

    total_alerts: int = Field(default=0, description="Total alerts")
    open_alerts: int = Field(default=0, description="Open alerts")
    acknowledged_alerts: int = Field(default=0, description="Acknowledged alerts")
    resolved_alerts: int = Field(default=0, description="Resolved alerts")

    total_runs: int = Field(default=0, description="Total runs")
    successful_runs: int = Field(default=0, description="Successful runs")
    failed_runs: int = Field(default=0, description="Failed runs")

    total_changes_detected: int = Field(default=0, description="Total changes detected")
    total_breaking_changes: int = Field(default=0, description="Total breaking changes")

    avg_detection_rate: float = Field(default=0.0, description="Average detection rate")
    avg_time_to_acknowledge: float | None = Field(
        default=None, description="Average time to acknowledge (seconds)"
    )
    avg_time_to_resolve: float | None = Field(
        default=None, description="Average time to resolve (seconds)"
    )


class SchemaWatcherStatusAction(BaseSchema):
    """Schema for status change action."""

    status: SchemaWatcherStatus = Field(..., description="New status")


class SchemaWatcherCheckNowResponse(BaseSchema):
    """Response for check now action."""

    watcher_id: str = Field(..., description="Watcher ID")
    run_id: str = Field(..., description="Run ID")
    status: SchemaWatcherRunStatus = Field(..., description="Run status")
    changes_detected: int = Field(default=0, description="Changes detected")
    breaking_detected: int = Field(default=0, description="Breaking changes")
    alert_created_id: str | None = Field(default=None, description="Alert ID if created")
    version_created_id: str | None = Field(
        default=None, description="Version ID if created"
    )
    duration_ms: float | None = Field(default=None, description="Duration")
    message: str = Field(..., description="Result message")


# =============================================================================
# List Responses (using PaginatedResponse)
# =============================================================================

SchemaWatcherListResponse = PaginatedResponse[SchemaWatcherSummary]
SchemaWatcherAlertListResponse = PaginatedResponse[SchemaWatcherAlertSummary]
SchemaWatcherRunListResponse = PaginatedResponse[SchemaWatcherRunSummary]


# =============================================================================
# Schema Change Detection (truthound.profiler.evolution types)
# =============================================================================


class SchemaChangeType(str, Enum):
    """Type of schema change."""

    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_RENAMED = "column_renamed"
    TYPE_CHANGED = "type_changed"
    NULLABLE_CHANGED = "nullable_changed"
    CONSTRAINT_CHANGED = "constraint_changed"


class SchemaChangeSeverity(str, Enum):
    """Severity of a schema change."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CompatibilityLevel(str, Enum):
    """Schema compatibility level."""

    COMPATIBLE = "compatible"
    MINOR = "minor"
    BREAKING = "breaking"


class RenameConfidence(str, Enum):
    """Confidence level for rename detection."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SimilarityAlgorithm(str, Enum):
    """Similarity algorithm for rename detection."""

    COMPOSITE = "composite"
    LEVENSHTEIN = "levenshtein"
    JARO_WINKLER = "jaro_winkler"
    NGRAM = "ngram"
    TOKEN = "token"


class SchemaChangeDetail(BaseSchema):
    """Detail of a single schema change."""

    change_type: SchemaChangeType = Field(..., description="Type of change")
    column_name: str = Field(..., description="Affected column name")
    old_value: Any = Field(default=None, description="Previous value")
    new_value: Any = Field(default=None, description="New value")
    severity: SchemaChangeSeverity = Field(..., description="Change severity")
    breaking: bool = Field(default=False, description="Is breaking change")
    description: str = Field(default="", description="Change description")
    migration_hint: str | None = Field(
        default=None, description="Migration suggestion"
    )


class RenameDetectionDetail(BaseSchema):
    """Detail of a detected column rename."""

    old_name: str = Field(..., description="Original column name")
    new_name: str = Field(..., description="New column name")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    confidence: RenameConfidence = Field(..., description="Detection confidence")
    reasons: list[str] = Field(default_factory=list, description="Detection reasons")


class RenameDetectionRequest(BaseSchema):
    """Request for rename detection."""

    added_columns: dict[str, str] = Field(
        ..., description="Added columns {name: type}"
    )
    removed_columns: dict[str, str] = Field(
        ..., description="Removed columns {name: type}"
    )
    similarity_threshold: float = Field(
        default=0.8, ge=0.5, le=1.0, description="Similarity threshold"
    )
    require_type_match: bool = Field(
        default=True, description="Require matching types"
    )
    allow_compatible_types: bool = Field(
        default=True, description="Allow compatible type changes"
    )
    algorithm: SimilarityAlgorithm = Field(
        default=SimilarityAlgorithm.COMPOSITE, description="Similarity algorithm"
    )


class RenameDetectionResponse(BaseSchema):
    """Response from rename detection."""

    confirmed_renames: list[RenameDetectionDetail] = Field(
        default_factory=list, description="Confirmed renames"
    )
    possible_renames: list[RenameDetectionDetail] = Field(
        default_factory=list, description="Possible renames"
    )
    unmatched_added: list[str] = Field(
        default_factory=list, description="Unmatched added columns"
    )
    unmatched_removed: list[str] = Field(
        default_factory=list, description="Unmatched removed columns"
    )


class SchemaDetectionRequest(BaseSchema):
    """Request for schema change detection."""

    current_schema: dict[str, Any] = Field(
        ..., description="Current schema {column: type}"
    )
    baseline_schema: dict[str, Any] = Field(
        ..., description="Baseline schema {column: type}"
    )
    detect_renames: bool = Field(
        default=True, description="Enable rename detection"
    )
    rename_similarity_threshold: float = Field(
        default=0.8, ge=0.5, le=1.0, description="Rename threshold"
    )


class SchemaDetectionResponse(BaseSchema):
    """Response from schema change detection."""

    total_changes: int = Field(..., description="Total changes detected")
    breaking_changes: int = Field(..., description="Breaking changes count")
    compatibility_level: CompatibilityLevel = Field(
        ..., description="Compatibility assessment"
    )
    changes: list[SchemaChangeDetail] = Field(
        default_factory=list, description="List of changes"
    )


# =============================================================================
# Schema Version History (truthound.profiler.evolution.SchemaHistory)
# =============================================================================


class SchemaVersionCreate(BaseSchema):
    """Request to create a schema version."""

    schema: dict[str, Any] = Field(..., description="Schema dictionary")
    version: str | None = Field(
        default=None, description="Explicit version (auto-generated if not provided)"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata"
    )


class SchemaVersionResponse(BaseSchema):
    """Schema version response."""

    id: str = Field(..., description="Version ID")
    version: str = Field(..., description="Version string")
    schema: dict[str, Any] = Field(..., description="Schema dictionary")
    metadata: dict[str, Any] | None = Field(default=None, description="Metadata")
    created_at: datetime | None = Field(default=None, description="Created timestamp")
    has_breaking_changes: bool = Field(
        default=False, description="Has breaking changes from parent"
    )
    changes_from_parent: list[SchemaChangeDetail] | None = Field(
        default=None, description="Changes from parent version"
    )


class SchemaVersionSummary(BaseSchema):
    """Schema version summary for lists."""

    id: str = Field(..., description="Version ID")
    version: str = Field(..., description="Version string")
    column_count: int = Field(default=0, description="Number of columns")
    created_at: datetime | None = Field(default=None, description="Created timestamp")
    has_breaking_changes: bool = Field(default=False, description="Has breaking changes")


class SchemaDiffRequest(BaseSchema):
    """Request for schema diff."""

    from_version: str = Field(..., description="Source version")
    to_version: str | None = Field(
        default=None, description="Target version (latest if not provided)"
    )


class SchemaDiffResponse(BaseSchema):
    """Schema diff response."""

    from_version: str = Field(..., description="Source version")
    to_version: str = Field(..., description="Target version")
    changes: list[SchemaChangeDetail] = Field(
        default_factory=list, description="Changes between versions"
    )
    text_diff: str = Field(default="", description="Human-readable diff")


class SchemaHistoryCreate(BaseSchema):
    """Request to create schema history storage."""

    storage_path: str = Field(..., description="Path for file storage")
    version_strategy: VersionStrategy = Field(
        default=VersionStrategy.SEMANTIC, description="Version numbering strategy"
    )
    max_versions: int = Field(
        default=100, ge=1, le=1000, description="Maximum versions to keep"
    )
    compress: bool = Field(default=True, description="Compress stored files")


class SchemaHistoryResponse(BaseSchema):
    """Schema history response."""

    history_id: str = Field(..., description="History instance ID")
    storage_path: str = Field(..., description="Storage path")
    version_strategy: VersionStrategy = Field(..., description="Version strategy")
    max_versions: int = Field(..., description="Maximum versions")
    version_count: int = Field(default=0, description="Current version count")
    latest_version: str | None = Field(default=None, description="Latest version")


class SchemaRollbackRequest(BaseSchema):
    """Request to rollback schema version."""

    to_version: str = Field(..., description="Version to rollback to")
    reason: str | None = Field(default=None, description="Reason for rollback")


# =============================================================================
# Impact Analysis (truthound.profiler.evolution.ImpactAnalyzer)
# =============================================================================


class ConsumerMapping(BaseSchema):
    """Consumer to sources mapping."""

    consumer: str = Field(..., description="Consumer name")
    sources: list[str] = Field(..., description="Sources the consumer depends on")


class QueryMapping(BaseSchema):
    """Source to queries mapping."""

    source: str = Field(..., description="Source name")
    queries: list[str] = Field(..., description="Queries using the source")


class ImpactAnalyzerSetup(BaseSchema):
    """Setup request for impact analyzer."""

    consumers: list[ConsumerMapping] | None = Field(
        default=None, description="Consumer mappings"
    )
    queries: list[QueryMapping] | None = Field(
        default=None, description="Query mappings"
    )


class ImpactAnalysisResponse(BaseSchema):
    """Impact analysis response."""

    impact_scope: ImpactScope = Field(..., description="Impact scope")
    affected_consumers: list[str] = Field(
        default_factory=list, description="Affected consumers"
    )
    affected_queries: list[str] = Field(
        default_factory=list, description="Affected queries"
    )
    data_risk_level: int = Field(
        default=1, ge=1, le=5, description="Risk level (1-5)"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations"
    )


# =============================================================================
# Scheduler Status
# =============================================================================


class SchemaWatcherSchedulerStatus(BaseSchema):
    """Status of the schema watcher scheduler."""

    is_running: bool = Field(..., description="Whether scheduler is running")
    active_watchers: int = Field(default=0, description="Active watchers")
    next_check_at: datetime | None = Field(
        default=None, description="Next scheduled check"
    )
    last_run_at: datetime | None = Field(default=None, description="Last scheduler run")
    pending_checks: int = Field(default=0, description="Pending checks")
