"""Quality Reporter schemas for API request/response validation.

This module provides Pydantic schemas for the Quality Reporter feature,
enabling comprehensive quality assessment and reporting of validation rules.

Based on truthound's QualityReporter module:
- Quality scoring (F1, precision, recall, accuracy)
- Quality levels (excellent, good, acceptable, poor, unacceptable)
- Filtering and comparison capabilities
- Multiple report formats (console, json, html, markdown, junit)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, PaginatedResponse, TimestampMixin


# =============================================================================
# Enums
# =============================================================================


class QualityLevel(str, Enum):
    """Quality levels for rules based on F1 score."""

    EXCELLENT = "excellent"  # 0.9 - 1.0
    GOOD = "good"  # 0.7 - 0.9
    ACCEPTABLE = "acceptable"  # 0.5 - 0.7
    POOR = "poor"  # 0.3 - 0.5
    UNACCEPTABLE = "unacceptable"  # 0.0 - 0.3


class QualityReportFormat(str, Enum):
    """Available quality report formats."""

    CONSOLE = "console"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    JUNIT = "junit"


class QualityReportStatus(str, Enum):
    """Status of quality report generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportSortOrder(str, Enum):
    """Sort order for quality scores."""

    F1_DESC = "f1_desc"
    F1_ASC = "f1_asc"
    PRECISION_DESC = "precision_desc"
    PRECISION_ASC = "precision_asc"
    RECALL_DESC = "recall_desc"
    RECALL_ASC = "recall_asc"
    LEVEL_DESC = "level_desc"
    LEVEL_ASC = "level_asc"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"


class QualityDisplayMode(str, Enum):
    """Display mode for quality reports."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    COMPARISON = "comparison"
    TREND = "trend"


class ChartType(str, Enum):
    """Chart types for quality visualizations."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    RADAR = "radar"
    HEATMAP = "heatmap"
    SCATTER = "scatter"


# =============================================================================
# Confusion Matrix
# =============================================================================


class ConfusionMatrixSchema(BaseSchema):
    """Confusion matrix for rule evaluation."""

    true_positive: int = Field(default=0, ge=0, description="Correct violation detections")
    true_negative: int = Field(default=0, ge=0, description="Correct passes")
    false_positive: int = Field(default=0, ge=0, description="Incorrect violation detections (false alarms)")
    false_negative: int = Field(default=0, ge=0, description="Missed violations")

    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)."""
        total = self.true_positive + self.false_positive
        return self.true_positive / total if total > 0 else 0.0

    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN)."""
        total = self.true_positive + self.false_negative
        return self.true_positive / total if total > 0 else 0.0

    @property
    def f1_score(self) -> float:
        """F1 score: harmonic mean of precision and recall."""
        p, r = self.precision, self.recall
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        """Accuracy: (TP + TN) / Total."""
        total = (
            self.true_positive
            + self.true_negative
            + self.false_positive
            + self.false_negative
        )
        return (self.true_positive + self.true_negative) / total if total > 0 else 0.0


# =============================================================================
# Quality Metrics
# =============================================================================


class QualityMetricsSchema(BaseSchema):
    """Quality metrics for a validation rule."""

    f1_score: float = Field(..., ge=0.0, le=1.0, description="F1 score (0-1)")
    precision: float = Field(..., ge=0.0, le=1.0, description="Precision (0-1)")
    recall: float = Field(..., ge=0.0, le=1.0, description="Recall (0-1)")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Accuracy (0-1)")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    quality_level: QualityLevel = Field(..., description="Computed quality level")


class QualityThresholdsSchema(BaseSchema):
    """Configurable thresholds for quality levels."""

    excellent: float = Field(default=0.9, ge=0.0, le=1.0, description="Minimum for excellent")
    good: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum for good")
    acceptable: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum for acceptable")
    poor: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum for poor")


# =============================================================================
# Quality Score
# =============================================================================


class QualityScoreSchema(BaseSchema):
    """Quality score result for a single rule."""

    rule_name: str = Field(..., description="Name of the validation rule")
    rule_type: str | None = Field(default=None, description="Type of rule (pattern, range, etc.)")
    column: str | None = Field(default=None, description="Target column name")
    metrics: QualityMetricsSchema = Field(..., description="Quality metrics")
    confusion_matrix: ConfusionMatrixSchema | None = Field(default=None, description="Confusion matrix details")
    test_sample_size: int = Field(default=0, ge=0, description="Number of samples tested")
    evaluation_time_ms: float = Field(default=0.0, ge=0.0, description="Evaluation time in milliseconds")
    recommendation: str | None = Field(default=None, description="Recommendation message")
    should_use: bool = Field(default=True, description="Whether the rule should be used")
    issues: list[dict[str, Any]] = Field(default_factory=list, description="List of identified issues")


# =============================================================================
# Quality Statistics
# =============================================================================


class QualityStatisticsSchema(BaseSchema):
    """Aggregate statistics for quality scores."""

    total_count: int = Field(default=0, ge=0, description="Total number of rules")
    excellent_count: int = Field(default=0, ge=0, description="Count of excellent rules")
    good_count: int = Field(default=0, ge=0, description="Count of good rules")
    acceptable_count: int = Field(default=0, ge=0, description="Count of acceptable rules")
    poor_count: int = Field(default=0, ge=0, description="Count of poor rules")
    unacceptable_count: int = Field(default=0, ge=0, description="Count of unacceptable rules")
    should_use_count: int = Field(default=0, ge=0, description="Count of recommended rules")
    avg_f1: float = Field(default=0.0, ge=0.0, le=1.0, description="Average F1 score")
    min_f1: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum F1 score")
    max_f1: float = Field(default=0.0, ge=0.0, le=1.0, description="Maximum F1 score")
    avg_precision: float = Field(default=0.0, ge=0.0, le=1.0, description="Average precision")
    avg_recall: float = Field(default=0.0, ge=0.0, le=1.0, description="Average recall")
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Average confidence")


class QualityLevelDistribution(BaseSchema):
    """Distribution of quality levels."""

    level: QualityLevel = Field(..., description="Quality level")
    count: int = Field(..., ge=0, description="Number of rules at this level")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total")


# =============================================================================
# Request Schemas
# =============================================================================


class QualityScoreRequest(BaseSchema):
    """Request to score validation rules."""

    source_id: str | None = Field(default=None, description="Source ID to score rules for")
    validation_id: str | None = Field(default=None, description="Validation ID to score")
    rule_names: list[str] | None = Field(default=None, description="Specific rules to score (optional)")
    sample_size: int = Field(default=10000, ge=100, le=1000000, description="Sample size for scoring")
    thresholds: QualityThresholdsSchema | None = Field(default=None, description="Custom quality thresholds")


class QualityFilterRequest(BaseSchema):
    """Request to filter quality scores."""

    min_level: QualityLevel | None = Field(default=None, description="Minimum quality level")
    max_level: QualityLevel | None = Field(default=None, description="Maximum quality level")
    min_f1: float | None = Field(default=None, ge=0.0, le=1.0, description="Minimum F1 score")
    max_f1: float | None = Field(default=None, ge=0.0, le=1.0, description="Maximum F1 score")
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Minimum confidence")
    should_use_only: bool = Field(default=False, description="Only include recommended rules")
    include_columns: list[str] | None = Field(default=None, description="Filter by specific columns")
    exclude_columns: list[str] | None = Field(default=None, description="Exclude specific columns")
    rule_types: list[str] | None = Field(default=None, description="Filter by rule types")


class QualityReportConfigSchema(BaseSchema):
    """Configuration for quality report generation."""

    title: str | None = Field(default=None, description="Report title")
    description: str | None = Field(default=None, description="Report description")

    # Content settings
    include_metrics: bool = Field(default=True, description="Include detailed metrics")
    include_confusion_matrix: bool = Field(default=False, description="Include confusion matrices")
    include_recommendations: bool = Field(default=True, description="Include recommendations")
    include_statistics: bool = Field(default=True, description="Include aggregate statistics")
    include_summary: bool = Field(default=True, description="Include summary section")
    include_charts: bool = Field(default=True, description="Include visual charts (HTML only)")

    # Formatting
    metric_precision: int = Field(default=2, ge=0, le=6, description="Decimal places for metrics")
    percentage_format: bool = Field(default=True, description="Display as percentages")

    # Display
    sort_order: ReportSortOrder = Field(
        default=ReportSortOrder.F1_DESC, description="Sort order for scores"
    )
    max_scores: int | None = Field(default=None, ge=1, description="Maximum scores to include")

    # HTML-specific
    theme: Literal["light", "dark", "professional"] = Field(
        default="professional", description="Theme for HTML reports"
    )


class QualityReportGenerateRequest(BaseSchema):
    """Request to generate a quality report."""

    source_id: str | None = Field(default=None, description="Source ID for the report")
    validation_id: str | None = Field(default=None, description="Validation ID for the report")
    format: QualityReportFormat = Field(
        default=QualityReportFormat.HTML, description="Report format"
    )
    config: QualityReportConfigSchema | None = Field(default=None, description="Report configuration")
    filter: QualityFilterRequest | None = Field(default=None, description="Score filter")
    score_rules: bool = Field(
        default=True, description="Score rules before generating report"
    )
    sample_size: int = Field(default=10000, ge=100, le=1000000, description="Sample size for scoring")


class QualityCompareRequest(BaseSchema):
    """Request to compare quality scores."""

    score_ids: list[str] | None = Field(default=None, description="Score IDs to compare")
    source_ids: list[str] | None = Field(default=None, description="Source IDs to compare")
    sort_by: Literal["f1_score", "precision", "recall", "confidence"] = Field(
        default="f1_score", description="Metric to sort by"
    )
    descending: bool = Field(default=True, description="Sort in descending order")
    group_by: Literal["column", "level", "rule_type"] | None = Field(
        default=None, description="Group results by"
    )
    max_results: int = Field(default=50, ge=1, le=500, description="Maximum results")


# =============================================================================
# Response Schemas
# =============================================================================


class QualityScoreResponse(BaseSchema, IDMixin, TimestampMixin):
    """Response for a quality score."""

    source_id: str = Field(..., description="Source ID")
    source_name: str | None = Field(default=None, description="Source name")
    validation_id: str | None = Field(default=None, description="Associated validation ID")
    status: QualityReportStatus = Field(..., description="Score status")
    scores: list[QualityScoreSchema] = Field(default_factory=list, description="Individual rule scores")
    statistics: QualityStatisticsSchema | None = Field(default=None, description="Aggregate statistics")
    level_distribution: list[QualityLevelDistribution] | None = Field(
        default=None, description="Quality level distribution"
    )
    sample_size: int = Field(default=0, ge=0, description="Sample size used")
    evaluation_time_ms: float = Field(default=0.0, ge=0.0, description="Total evaluation time")
    error_message: str | None = Field(default=None, description="Error message if failed")


class QualityReportResponse(BaseSchema, IDMixin, TimestampMixin):
    """Response for a generated quality report."""

    source_id: str | None = Field(default=None, description="Source ID")
    source_name: str | None = Field(default=None, description="Source name")
    validation_id: str | None = Field(default=None, description="Validation ID")
    format: QualityReportFormat = Field(..., description="Report format")
    status: QualityReportStatus = Field(..., description="Report status")
    filename: str | None = Field(default=None, description="Generated filename")
    file_path: str | None = Field(default=None, description="File path")
    file_size_bytes: int | None = Field(default=None, ge=0, description="File size in bytes")
    content_type: str | None = Field(default=None, description="Content type")
    generation_time_ms: float | None = Field(default=None, ge=0.0, description="Generation time")
    scores_count: int = Field(default=0, ge=0, description="Number of scores in report")
    statistics: QualityStatisticsSchema | None = Field(default=None, description="Report statistics")
    error_message: str | None = Field(default=None, description="Error message if failed")
    download_count: int = Field(default=0, ge=0, description="Number of downloads")
    expires_at: datetime | None = Field(default=None, description="Expiration timestamp")


class QualityCompareResponse(BaseSchema):
    """Response for quality comparison."""

    scores: list[QualityScoreSchema] = Field(..., description="Compared scores")
    ranked_by: str = Field(..., description="Metric used for ranking")
    best_rule: QualityScoreSchema | None = Field(default=None, description="Best performing rule")
    worst_rule: QualityScoreSchema | None = Field(default=None, description="Worst performing rule")
    groups: dict[str, list[QualityScoreSchema]] | None = Field(
        default=None, description="Grouped scores"
    )
    statistics: QualityStatisticsSchema | None = Field(default=None, description="Comparison statistics")


class QualitySummaryResponse(BaseSchema):
    """Summary response for quality scores."""

    total_rules: int = Field(..., ge=0, description="Total rules scored")
    statistics: QualityStatisticsSchema = Field(..., description="Quality statistics")
    level_distribution: list[QualityLevelDistribution] = Field(
        ..., description="Level distribution"
    )
    recommendations: dict[str, int] = Field(
        ..., description="Recommendation counts (should_use, should_not_use)"
    )
    metric_averages: dict[str, dict[str, float]] = Field(
        ..., description="Metric averages (avg, min, max)"
    )


# =============================================================================
# List Response Types
# =============================================================================


class QualityScoreListResponse(PaginatedResponse[QualityScoreResponse]):
    """Paginated list of quality scores."""

    pass


class QualityReportListResponse(PaginatedResponse[QualityReportResponse]):
    """Paginated list of quality reports."""

    pass


# =============================================================================
# Available Formats Response
# =============================================================================


class QualityFormatsResponse(BaseSchema):
    """Available quality report formats and options."""

    formats: list[str] = Field(..., description="Available report formats")
    sort_orders: list[str] = Field(..., description="Available sort orders")
    themes: list[str] = Field(..., description="Available themes")
    default_thresholds: QualityThresholdsSchema = Field(
        ..., description="Default quality thresholds"
    )
