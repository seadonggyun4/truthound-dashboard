"""Quality Reporter API endpoints.

This module provides REST API endpoints for quality assessment and reporting
of validation rules, integrating with truthound's QualityReporter module.

Endpoints:
- GET /quality/formats - Get available report formats and options
- POST /quality/sources/{source_id}/score - Score validation rules
- POST /quality/sources/{source_id}/report - Generate quality report
- GET /quality/sources/{source_id}/report/download - Download report
- GET /quality/sources/{source_id}/summary - Get quality summary
- POST /quality/filter - Filter quality scores
- POST /quality/compare - Compare quality scores
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response

from truthound_dashboard.core.quality_reporter import (
    QualityFilter,
    QualityReportConfig,
    QualityReportFormat,
    QualityReportStatus,
    QualityReporterService,
    QualityThresholds,
)
from truthound_dashboard.schemas.quality_reporter import (
    QualityCompareRequest,
    QualityCompareResponse,
    QualityFilterRequest,
    QualityFormatsResponse,
    QualityLevel,
    QualityLevelDistribution,
    QualityMetricsSchema,
    QualityReportConfigSchema,
    QualityReportFormat as QualityReportFormatSchema,
    QualityReportGenerateRequest,
    QualityReportResponse,
    QualityReportStatus as QualityReportStatusSchema,
    QualityScoreRequest,
    QualityScoreResponse,
    QualityScoreSchema,
    QualityStatisticsSchema,
    QualitySummaryResponse,
    QualityThresholdsSchema,
)

from .deps import SessionDep

router = APIRouter(prefix="/quality")


# =============================================================================
# Dependency
# =============================================================================


async def get_quality_reporter_service(session: SessionDep) -> QualityReporterService:
    """Get quality reporter service dependency."""
    return QualityReporterService(session)


QualityReporterServiceDep = Annotated[
    QualityReporterService,
    __import__("fastapi").Depends(get_quality_reporter_service)
]


# =============================================================================
# Helper Functions
# =============================================================================


def _convert_score_to_response(score: dict[str, Any]) -> QualityScoreSchema:
    """Convert internal score to response schema."""
    metrics = score.get("metrics", {})
    return QualityScoreSchema(
        rule_name=score["rule_name"],
        rule_type=score.get("rule_type"),
        column=score.get("column"),
        metrics=QualityMetricsSchema(
            f1_score=metrics.get("f1_score", 0.0),
            precision=metrics.get("precision", 0.0),
            recall=metrics.get("recall", 0.0),
            accuracy=metrics.get("accuracy", 0.0),
            confidence=metrics.get("confidence", 0.0),
            quality_level=QualityLevel(metrics.get("quality_level", "unacceptable")),
        ),
        confusion_matrix=score.get("confusion_matrix"),
        test_sample_size=score.get("test_sample_size", 0),
        evaluation_time_ms=score.get("evaluation_time_ms", 0.0),
        recommendation=score.get("recommendation"),
        should_use=score.get("should_use", True),
        issues=score.get("issues", []),
    )


def _convert_statistics_to_response(
    stats: dict[str, Any] | None,
) -> QualityStatisticsSchema | None:
    """Convert internal statistics to response schema."""
    if not stats:
        return None
    return QualityStatisticsSchema(
        total_count=stats.get("total_count", 0),
        excellent_count=stats.get("excellent_count", 0),
        good_count=stats.get("good_count", 0),
        acceptable_count=stats.get("acceptable_count", 0),
        poor_count=stats.get("poor_count", 0),
        unacceptable_count=stats.get("unacceptable_count", 0),
        should_use_count=stats.get("should_use_count", 0),
        avg_f1=stats.get("avg_f1", 0.0),
        min_f1=stats.get("min_f1", 0.0),
        max_f1=stats.get("max_f1", 0.0),
        avg_precision=stats.get("avg_precision", 0.0),
        avg_recall=stats.get("avg_recall", 0.0),
        avg_confidence=stats.get("avg_confidence", 0.0),
    )


def _convert_distribution_to_response(
    dist: list[dict[str, Any]] | None,
) -> list[QualityLevelDistribution] | None:
    """Convert internal distribution to response schema."""
    if not dist:
        return None
    return [
        QualityLevelDistribution(
            level=QualityLevel(d["level"]),
            count=d["count"],
            percentage=d["percentage"],
        )
        for d in dist
    ]


def _request_to_filter(request: QualityFilterRequest) -> QualityFilter:
    """Convert request schema to internal filter."""
    from truthound_dashboard.core.quality_reporter import (
        QualityLevel as InternalLevel,
    )

    min_level = None
    max_level = None
    if request.min_level:
        min_level = InternalLevel(request.min_level.value)
    if request.max_level:
        max_level = InternalLevel(request.max_level.value)

    return QualityFilter(
        min_level=min_level,
        max_level=max_level,
        min_f1=request.min_f1,
        max_f1=request.max_f1,
        min_confidence=request.min_confidence,
        should_use_only=request.should_use_only,
        include_columns=request.include_columns,
        exclude_columns=request.exclude_columns,
        rule_types=request.rule_types,
    )


def _request_to_config(request: QualityReportConfigSchema | None) -> QualityReportConfig:
    """Convert request schema to internal config."""
    if not request:
        return QualityReportConfig()

    return QualityReportConfig(
        title=request.title,
        description=request.description,
        include_metrics=request.include_metrics,
        include_confusion_matrix=request.include_confusion_matrix,
        include_recommendations=request.include_recommendations,
        include_statistics=request.include_statistics,
        include_summary=request.include_summary,
        include_charts=request.include_charts,
        metric_precision=request.metric_precision,
        percentage_format=request.percentage_format,
        sort_order=request.sort_order.value if request.sort_order else "f1_desc",
        max_scores=request.max_scores,
        theme=request.theme,
    )


def _request_to_thresholds(
    request: QualityThresholdsSchema | None,
) -> QualityThresholds:
    """Convert request schema to internal thresholds."""
    if not request:
        return QualityThresholds()

    return QualityThresholds(
        excellent=request.excellent,
        good=request.good,
        acceptable=request.acceptable,
        poor=request.poor,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/formats",
    response_model=QualityFormatsResponse,
    summary="Get available quality report formats",
    description="List all available report formats, sort orders, themes, and options",
)
async def get_formats(
    service: QualityReporterServiceDep,
) -> QualityFormatsResponse:
    """Get available quality report formats and options.

    Returns:
        Available formats, sort orders, themes, and default quality thresholds.
    """
    data = service.get_available_formats()
    return QualityFormatsResponse(
        formats=data["formats"],
        sort_orders=data["sort_orders"],
        themes=data["themes"],
        default_thresholds=QualityThresholdsSchema(**data["default_thresholds"]),
    )


@router.post(
    "/sources/{source_id}/score",
    response_model=QualityScoreResponse,
    summary="Score validation rules for a source",
    description="Evaluate quality of validation rules using F1 score, precision, recall, and accuracy",
)
async def score_source(
    service: QualityReporterServiceDep,
    source_id: Annotated[str, Path(description="Source ID to score")],
    request: QualityScoreRequest | None = None,
) -> QualityScoreResponse:
    """Score validation rules for a source.

    This endpoint evaluates the quality of validation rules by:
    - Computing F1 score, precision, recall, and accuracy
    - Assigning quality levels (excellent, good, acceptable, poor, unacceptable)
    - Generating recommendations for rule usage

    Args:
        service: Quality reporter service.
        source_id: Source ID to score.
        request: Optional scoring configuration.

    Returns:
        Quality score result with metrics and statistics.
    """
    request = request or QualityScoreRequest()
    thresholds = _request_to_thresholds(request.thresholds)

    result = await service.score_source(
        source_id,
        validation_id=request.validation_id,
        rule_names=request.rule_names,
        sample_size=request.sample_size,
        thresholds=thresholds,
    )

    # Convert internal result to response
    scores = [_convert_score_to_response(s.to_dict()) for s in result.scores]
    statistics = _convert_statistics_to_response(
        result.statistics.to_dict() if result.statistics else None
    )
    distribution = _convert_distribution_to_response(
        [d.to_dict() for d in result.level_distribution] if result.level_distribution else None
    )

    return QualityScoreResponse(
        id=result.id,
        source_id=result.source_id,
        source_name=result.source_name,
        validation_id=result.validation_id,
        status=QualityReportStatusSchema(result.status.value),
        scores=scores,
        statistics=statistics,
        level_distribution=distribution,
        sample_size=result.sample_size,
        evaluation_time_ms=result.evaluation_time_ms,
        error_message=result.error_message,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.post(
    "/sources/{source_id}/report",
    response_model=QualityReportResponse,
    summary="Generate quality report",
    description="Generate a comprehensive quality report in various formats (HTML, JSON, Markdown, etc.)",
)
async def generate_report(
    service: QualityReporterServiceDep,
    source_id: Annotated[str, Path(description="Source ID for the report")],
    request: QualityReportGenerateRequest | None = None,
) -> QualityReportResponse:
    """Generate a quality report for a source.

    Generates a comprehensive quality report that includes:
    - Quality scores for all validation rules
    - Aggregate statistics and level distribution
    - Visual charts (HTML format)
    - Recommendations

    Args:
        service: Quality reporter service.
        source_id: Source ID for the report.
        request: Report generation configuration.

    Returns:
        Generated report metadata.
    """
    request = request or QualityReportGenerateRequest()

    # Convert format enum
    from truthound_dashboard.core.quality_reporter import (
        QualityReportFormat as InternalFormat,
    )

    format_value = request.format.value if request.format else "html"
    internal_format = InternalFormat(format_value)

    # Convert config and filter
    config = _request_to_config(request.config)
    filter_config = _request_to_filter(request.filter) if request.filter else None

    result = await service.generate_report(
        source_id=source_id,
        validation_id=request.validation_id,
        format=internal_format,
        config=config,
        filter_config=filter_config,
        score_rules=request.score_rules,
        sample_size=request.sample_size,
    )

    statistics = _convert_statistics_to_response(
        result.statistics.to_dict() if result.statistics else None
    )

    return QualityReportResponse(
        id=result.id,
        source_id=result.source_id,
        source_name=result.source_name,
        validation_id=result.validation_id,
        format=QualityReportFormatSchema(result.format.value),
        status=QualityReportStatusSchema(result.status.value),
        filename=result.filename,
        file_path=result.file_path,
        file_size_bytes=result.file_size_bytes,
        content_type=result.content_type,
        generation_time_ms=result.generation_time_ms,
        scores_count=result.scores_count,
        statistics=statistics,
        error_message=result.error_message,
        download_count=result.download_count,
        expires_at=result.expires_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get(
    "/sources/{source_id}/report/download",
    summary="Download quality report",
    description="Download the generated quality report content",
)
async def download_report(
    service: QualityReporterServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    format: Annotated[
        QualityReportFormatSchema,
        Query(description="Report format"),
    ] = QualityReportFormatSchema.HTML,
    title: Annotated[str | None, Query(description="Report title")] = None,
    include_charts: Annotated[
        bool, Query(description="Include charts (HTML only)")
    ] = True,
    theme: Annotated[
        str, Query(description="Report theme")
    ] = "professional",
    max_scores: Annotated[
        int | None, Query(description="Maximum scores to include", ge=1)
    ] = None,
) -> Response:
    """Download quality report as file.

    Args:
        service: Quality reporter service.
        source_id: Source ID.
        format: Report format.
        title: Optional report title.
        include_charts: Include charts in HTML reports.
        theme: Report theme.
        max_scores: Maximum scores to include.

    Returns:
        Report file content.
    """
    from truthound_dashboard.core.quality_reporter import (
        QualityReportFormat as InternalFormat,
    )

    config = QualityReportConfig(
        title=title,
        include_charts=include_charts,
        theme=theme,
        max_scores=max_scores,
    )

    internal_format = InternalFormat(format.value)
    result = await service.generate_report(
        source_id=source_id,
        format=internal_format,
        config=config,
    )

    if result.status != QualityReportStatus.COMPLETED or not result.content:
        raise HTTPException(
            status_code=500,
            detail=result.error_message or "Failed to generate report",
        )

    # Determine media type
    media_types = {
        QualityReportFormatSchema.CONSOLE: "text/plain",
        QualityReportFormatSchema.JSON: "application/json",
        QualityReportFormatSchema.HTML: "text/html",
        QualityReportFormatSchema.MARKDOWN: "text/markdown",
        QualityReportFormatSchema.JUNIT: "application/xml",
    }
    media_type = media_types.get(format, "text/plain")

    return Response(
        content=result.content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )


@router.get(
    "/sources/{source_id}/report/preview",
    summary="Preview quality report",
    description="Preview the quality report content inline",
)
async def preview_report(
    service: QualityReporterServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    format: Annotated[
        QualityReportFormatSchema,
        Query(description="Report format"),
    ] = QualityReportFormatSchema.HTML,
    theme: Annotated[str, Query(description="Report theme")] = "professional",
    max_scores: Annotated[
        int | None, Query(description="Maximum scores", ge=1)
    ] = 20,
) -> Response:
    """Preview quality report inline.

    Args:
        service: Quality reporter service.
        source_id: Source ID.
        format: Report format.
        theme: Report theme.
        max_scores: Maximum scores to include.

    Returns:
        Report content for inline display.
    """
    from truthound_dashboard.core.quality_reporter import (
        QualityReportFormat as InternalFormat,
    )

    config = QualityReportConfig(
        theme=theme,
        max_scores=max_scores,
        include_charts=True,
    )

    internal_format = InternalFormat(format.value)
    result = await service.generate_report(
        source_id=source_id,
        format=internal_format,
        config=config,
    )

    if result.status != QualityReportStatus.COMPLETED or not result.content:
        raise HTTPException(
            status_code=500,
            detail=result.error_message or "Failed to generate report",
        )

    media_types = {
        QualityReportFormatSchema.CONSOLE: "text/plain",
        QualityReportFormatSchema.JSON: "application/json",
        QualityReportFormatSchema.HTML: "text/html",
        QualityReportFormatSchema.MARKDOWN: "text/markdown",
        QualityReportFormatSchema.JUNIT: "application/xml",
    }
    media_type = media_types.get(format, "text/plain")

    return Response(content=result.content, media_type=media_type)


@router.get(
    "/sources/{source_id}/summary",
    response_model=QualitySummaryResponse,
    summary="Get quality summary",
    description="Get a summary of quality scores for a source",
)
async def get_summary(
    service: QualityReporterServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    validation_id: Annotated[
        str | None, Query(description="Validation ID")
    ] = None,
    sample_size: Annotated[
        int, Query(description="Sample size", ge=100, le=1000000)
    ] = 10000,
) -> QualitySummaryResponse:
    """Get quality summary for a source.

    Returns aggregate statistics including:
    - Total rules scored
    - Quality level distribution
    - Recommendations summary
    - Metric averages (F1, precision, recall, confidence)

    Args:
        service: Quality reporter service.
        source_id: Source ID.
        validation_id: Optional validation ID.
        sample_size: Sample size for scoring.

    Returns:
        Quality summary.
    """
    summary = await service.get_summary(
        source_id,
        validation_id=validation_id,
        sample_size=sample_size,
    )

    if "error" in summary:
        raise HTTPException(status_code=500, detail=summary["error"])

    statistics = _convert_statistics_to_response(summary["statistics"])
    if not statistics:
        statistics = QualityStatisticsSchema()

    distribution = [
        QualityLevelDistribution(
            level=QualityLevel(d["level"]),
            count=d["count"],
            percentage=d["percentage"],
        )
        for d in summary.get("level_distribution", [])
    ]

    return QualitySummaryResponse(
        total_rules=summary["total_rules"],
        statistics=statistics,
        level_distribution=distribution,
        recommendations=summary["recommendations"],
        metric_averages=summary["metric_averages"],
    )


@router.post(
    "/compare",
    response_model=QualityCompareResponse,
    summary="Compare quality scores",
    description="Compare and rank quality scores across sources",
)
async def compare_scores(
    service: QualityReporterServiceDep,
    request: QualityCompareRequest,
) -> QualityCompareResponse:
    """Compare quality scores across sources.

    Compares and ranks quality scores by specified metrics.
    Can optionally group results by column, level, or rule type.

    Args:
        service: Quality reporter service.
        request: Comparison configuration.

    Returns:
        Comparison result with ranked scores.
    """
    # Get scores from sources
    all_scores = []

    if request.source_ids:
        for source_id in request.source_ids:
            result = await service.score_source(source_id)
            if result.status == QualityReportStatus.COMPLETED:
                all_scores.extend(result.scores)

    if not all_scores:
        raise HTTPException(
            status_code=400,
            detail="No scores available for comparison",
        )

    # Compare scores
    comparison = await service.compare_scores(
        all_scores,
        sort_by=request.sort_by,
        descending=request.descending,
        group_by=request.group_by,
        max_results=request.max_results,
    )

    # Convert to response
    scores = [
        _convert_score_to_response(s) for s in comparison.get("scores", [])
    ]

    best_rule = None
    if comparison.get("best_rule"):
        best_rule = _convert_score_to_response(comparison["best_rule"])

    worst_rule = None
    if comparison.get("worst_rule"):
        worst_rule = _convert_score_to_response(comparison["worst_rule"])

    statistics = _convert_statistics_to_response(comparison.get("statistics"))

    # Convert groups
    groups = None
    if comparison.get("groups"):
        groups = {
            key: [_convert_score_to_response(s) for s in group_scores]
            for key, group_scores in comparison["groups"].items()
        }

    return QualityCompareResponse(
        scores=scores,
        ranked_by=comparison["ranked_by"],
        best_rule=best_rule,
        worst_rule=worst_rule,
        groups=groups,
        statistics=statistics,
    )


@router.post(
    "/filter",
    response_model=list[QualityScoreSchema],
    summary="Filter quality scores",
    description="Filter quality scores by various criteria",
)
async def filter_scores(
    service: QualityReporterServiceDep,
    source_id: Annotated[str, Query(description="Source ID to filter scores from")],
    request: QualityFilterRequest,
) -> list[QualityScoreSchema]:
    """Filter quality scores by criteria.

    Available filters:
    - Quality level (min/max)
    - F1 score range
    - Confidence threshold
    - Specific columns
    - Rule types
    - Should-use recommendation

    Args:
        service: Quality reporter service.
        source_id: Source ID to get scores from.
        request: Filter configuration.

    Returns:
        Filtered quality scores.
    """
    # Get scores first
    result = await service.score_source(source_id)

    if result.status != QualityReportStatus.COMPLETED:
        raise HTTPException(
            status_code=500,
            detail=result.error_message or "Failed to score source",
        )

    # Apply filter
    filter_config = _request_to_filter(request)
    filtered = await service.filter_scores(result.scores, filter_config)

    return [_convert_score_to_response(s.to_dict()) for s in filtered]
