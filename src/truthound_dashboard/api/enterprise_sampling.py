"""Enterprise Sampling API endpoints.

This module provides REST API endpoints for truthound 1.2.10's enterprise-scale
sampling capabilities.

Endpoints:
- POST /api/v1/sampling/enterprise: Run enterprise sampling
- POST /api/v1/sampling/estimate-size: Estimate optimal sample size
- POST /api/v1/sampling/sketch: Run sketch-based estimation
- GET /api/v1/sampling/jobs: List sampling jobs
- GET /api/v1/sampling/jobs/{job_id}: Get job status
- POST /api/v1/sampling/jobs/{job_id}/cancel: Cancel job
- GET /api/v1/sampling/strategies: List available strategies
- GET /api/v1/sampling/quality-presets: List quality presets
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.api.deps import get_session
from truthound_dashboard.core.enterprise_sampling import (
    QUALITY_PRESETS,
    SCALE_STRATEGY_MAP,
    classify_dataset_scale,
    get_enterprise_sampler,
    get_sample_size_estimator,
    get_sketch_estimator,
)
from sqlalchemy import select
from truthound_dashboard.db import Source
from truthound_dashboard.schemas.enterprise_sampling import (
    BlockSamplingConfig,
    ColumnAwareSamplingConfig,
    EnterpriseSamplingRequest,
    EnterpriseSamplingResponse,
    EnterpriseSamplingStrategy,
    MemoryBudgetConfig,
    MultiStageSamplingConfig,
    ParallelSamplingConfig,
    ProgressiveSamplingConfig,
    SampleSizeEstimateRequest,
    SampleSizeEstimateResponse,
    SamplingJobListResponse,
    SamplingJobStatus,
    SamplingQuality,
    ScaleCategory,
    SchedulingPolicy,
    SketchConfig,
    SketchEstimateRequest,
    SketchEstimateResponse,
    SketchType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sampling", tags=["Enterprise Sampling"])


# ============================================================================
# Response Models for API Documentation
# ============================================================================


class StrategyInfo:
    """Strategy information for documentation."""

    def __init__(
        self,
        name: str,
        value: str,
        description: str,
        best_for: str,
        supports_parallel: bool = False,
        supports_streaming: bool = False,
    ):
        self.name = name
        self.value = value
        self.description = description
        self.best_for = best_for
        self.supports_parallel = supports_parallel
        self.supports_streaming = supports_streaming


STRATEGY_DOCS = {
    EnterpriseSamplingStrategy.NONE: StrategyInfo(
        name="No Sampling",
        value="none",
        description="Use full dataset without sampling",
        best_for="Datasets < 1M rows",
    ),
    EnterpriseSamplingStrategy.RANDOM: StrategyInfo(
        name="Random Sampling",
        value="random",
        description="Simple random sampling without replacement",
        best_for="General purpose, uniform distributions",
    ),
    EnterpriseSamplingStrategy.BLOCK: StrategyInfo(
        name="Block Sampling",
        value="block",
        description="Divides data into blocks and samples proportionally from each",
        best_for="10M-100M rows, when coverage across data is important",
        supports_parallel=True,
    ),
    EnterpriseSamplingStrategy.MULTI_STAGE: StrategyInfo(
        name="Multi-Stage Sampling",
        value="multi_stage",
        description="Hierarchical sampling in multiple progressive passes",
        best_for="100M-1B rows, when quick estimates are acceptable",
    ),
    EnterpriseSamplingStrategy.COLUMN_AWARE: StrategyInfo(
        name="Column-Aware Sampling",
        value="column_aware",
        description="Adjusts sample size based on column type complexity",
        best_for="Datasets with mixed column types",
    ),
    EnterpriseSamplingStrategy.PROGRESSIVE: StrategyInfo(
        name="Progressive Sampling",
        value="progressive",
        description="Iteratively increases sample size until convergence",
        best_for="Exploratory analysis, early stopping when possible",
    ),
    EnterpriseSamplingStrategy.ADAPTIVE: StrategyInfo(
        name="Adaptive (Auto-Select)",
        value="adaptive",
        description="Automatically selects best strategy based on data characteristics",
        best_for="When unsure which strategy to use",
    ),
}


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/enterprise",
    response_model=EnterpriseSamplingResponse,
    summary="Run enterprise-scale sampling",
    description="""
    Execute enterprise-scale sampling on a data source.

    Supports datasets from 100M to billions of rows with:
    - Block sampling for parallel processing
    - Multi-stage hierarchical sampling
    - Column-aware adaptive sampling
    - Progressive sampling with convergence detection

    The response includes detailed metrics about the sampling operation.
    """,
)
async def run_enterprise_sampling(
    request: EnterpriseSamplingRequest,
    db: AsyncSession = Depends(get_session),
) -> EnterpriseSamplingResponse:
    """Run enterprise-scale sampling on a data source."""
    # Get source
    result = await db.execute(select(Source).where(Source.id == request.source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {request.source_id}",
        )

    try:
        import polars as pl

        # Load data
        data_path = source.path
        if data_path.endswith(".csv"):
            lf = pl.scan_csv(data_path)
        elif data_path.endswith(".parquet"):
            lf = pl.scan_parquet(data_path)
        elif data_path.endswith(".json"):
            lf = pl.read_json(data_path).lazy()
        elif data_path.endswith(".jsonl") or data_path.endswith(".ndjson"):
            lf = pl.read_ndjson(data_path).lazy()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {data_path}",
            )

        # Get row count (may require a collect for some formats)
        schema = lf.collect_schema()
        column_count = len(schema)

        # Estimate row count
        try:
            row_count = lf.select(pl.len()).collect().item()
        except Exception:
            # Fall back to collecting and counting
            row_count = len(lf.collect())

        # Run sampling
        sampler = get_enterprise_sampler()
        response = await sampler.sample(
            config=request,
            data=lf,
            row_count=row_count,
            column_count=column_count,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enterprise sampling failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sampling failed: {str(e)}",
        )


@router.post(
    "/estimate-size",
    response_model=SampleSizeEstimateResponse,
    summary="Estimate optimal sample size",
    description="""
    Calculate the optimal sample size for a given population using Cochran's formula.

    Returns:
    - Recommended sample size with statistical confidence
    - Minimum and maximum useful sample sizes
    - Estimated processing time and memory usage
    - Recommended sampling strategy with rationale
    """,
)
async def estimate_sample_size(
    request: SampleSizeEstimateRequest,
) -> SampleSizeEstimateResponse:
    """Estimate optimal sample size for statistical confidence."""
    estimator = get_sample_size_estimator()
    return estimator.estimate(request)


@router.post(
    "/sketch",
    response_model=SketchEstimateResponse,
    summary="Run sketch-based estimation",
    description="""
    Use probabilistic data structures for O(1) memory aggregations on massive datasets.

    Supported sketch types:
    - **HyperLogLog**: Cardinality estimation (distinct count)
    - **Count-Min Sketch**: Frequency estimation (heavy hitters)
    - **Bloom Filter**: Membership testing

    Ideal for datasets exceeding 10B rows where exact computation is impractical.
    """,
)
async def run_sketch_estimation(
    request: SketchEstimateRequest,
    db: AsyncSession = Depends(get_session),
) -> SketchEstimateResponse:
    """Run sketch-based estimation using probabilistic data structures."""
    # Get source
    result = await db.execute(select(Source).where(Source.id == request.source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {request.source_id}",
        )

    try:
        import polars as pl

        # Load data
        data_path = source.path
        if data_path.endswith(".csv"):
            lf = pl.scan_csv(data_path)
        elif data_path.endswith(".parquet"):
            lf = pl.scan_parquet(data_path)
        else:
            lf = pl.read_csv(data_path).lazy()

        # Validate columns exist
        schema = lf.collect_schema()
        for col in request.columns:
            if col not in schema:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Column not found: {col}",
                )

        # Run sketch estimation
        estimator = get_sketch_estimator()
        response = await estimator.estimate(request, lf)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sketch estimation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sketch estimation failed: {str(e)}",
        )


@router.get(
    "/jobs",
    response_model=SamplingJobListResponse,
    summary="List sampling jobs",
    description="List all active and recent sampling jobs.",
)
async def list_sampling_jobs(
    status_filter: str | None = Query(
        None,
        description="Filter by status: pending, running, completed, failed",
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum jobs to return"),
) -> SamplingJobListResponse:
    """List all sampling jobs."""
    sampler = get_enterprise_sampler()
    all_jobs = sampler.list_jobs()

    # Filter by status if specified
    if status_filter:
        all_jobs = [j for j in all_jobs if j.status == status_filter]

    # Apply limit
    jobs = all_jobs[:limit]

    return SamplingJobListResponse(
        jobs=jobs,
        total=len(all_jobs),
        active_count=sum(1 for j in all_jobs if j.status in ("pending", "running")),
    )


@router.get(
    "/jobs/{job_id}",
    response_model=SamplingJobStatus,
    summary="Get job status",
    description="Get the status of a specific sampling job.",
)
async def get_job_status(job_id: str) -> SamplingJobStatus:
    """Get status of a specific sampling job."""
    sampler = get_enterprise_sampler()
    job = sampler.get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    return job


@router.post(
    "/jobs/{job_id}/cancel",
    summary="Cancel sampling job",
    description="Cancel an active sampling job.",
)
async def cancel_sampling_job(job_id: str) -> dict[str, Any]:
    """Cancel an active sampling job."""
    sampler = get_enterprise_sampler()
    job = sampler.get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    if job.status not in ("pending", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job cannot be cancelled: status is {job.status}",
        )

    # In production, this would actually cancel the job
    # For now, just mark it as cancelled
    job.status = "cancelled"

    return {"job_id": job_id, "status": "cancelled", "message": "Job cancellation requested"}


@router.get(
    "/strategies",
    summary="List available strategies",
    description="List all available enterprise sampling strategies with descriptions.",
)
async def list_strategies() -> list[dict[str, Any]]:
    """List available sampling strategies."""
    strategies = []

    for strategy_type, info in STRATEGY_DOCS.items():
        strategies.append({
            "name": info.name,
            "value": info.value,
            "description": info.description,
            "best_for": info.best_for,
            "supports_parallel": info.supports_parallel,
            "supports_streaming": info.supports_streaming,
        })

    return strategies


@router.get(
    "/quality-presets",
    summary="List quality presets",
    description="List available sampling quality presets with their configurations.",
)
async def list_quality_presets() -> list[dict[str, Any]]:
    """List available quality presets."""
    presets = []

    preset_descriptions = {
        SamplingQuality.SKETCH: "Fast approximation using probabilistic structures",
        SamplingQuality.QUICK: "Quick estimates with 90% confidence",
        SamplingQuality.STANDARD: "Balanced sampling with 95% confidence (recommended)",
        SamplingQuality.HIGH: "High accuracy with 99% confidence",
        SamplingQuality.EXACT: "Full scan without sampling",
    }

    for quality, config in QUALITY_PRESETS.items():
        presets.append({
            "name": quality.value,
            "description": preset_descriptions.get(quality, ""),
            "target_rows": config["target_rows"],
            "confidence_level": config["confidence_level"],
            "margin_of_error": config["margin_of_error"],
        })

    return presets


@router.get(
    "/scale-categories",
    summary="List scale categories",
    description="List dataset scale categories with recommended strategies.",
)
async def list_scale_categories() -> list[dict[str, Any]]:
    """List scale categories with recommended strategies."""
    categories = [
        {
            "name": ScaleCategory.SMALL.value,
            "row_count_range": "< 1M",
            "recommended_strategy": SCALE_STRATEGY_MAP[ScaleCategory.SMALL].value,
            "description": "Small datasets that don't require sampling",
        },
        {
            "name": ScaleCategory.MEDIUM.value,
            "row_count_range": "1M - 10M",
            "recommended_strategy": SCALE_STRATEGY_MAP[ScaleCategory.MEDIUM].value,
            "description": "Medium datasets suitable for column-aware sampling",
        },
        {
            "name": ScaleCategory.LARGE.value,
            "row_count_range": "10M - 100M",
            "recommended_strategy": SCALE_STRATEGY_MAP[ScaleCategory.LARGE].value,
            "description": "Large datasets requiring block-based parallel sampling",
        },
        {
            "name": ScaleCategory.XLARGE.value,
            "row_count_range": "100M - 1B",
            "recommended_strategy": SCALE_STRATEGY_MAP[ScaleCategory.XLARGE].value,
            "description": "Extra-large datasets requiring multi-stage sampling",
        },
        {
            "name": ScaleCategory.XXLARGE.value,
            "row_count_range": "> 1B",
            "recommended_strategy": SCALE_STRATEGY_MAP[ScaleCategory.XXLARGE].value,
            "description": "Massive datasets requiring sketches and multi-stage sampling",
        },
    ]

    return categories


@router.post(
    "/classify-scale",
    summary="Classify dataset scale",
    description="Classify a dataset by row count into a scale category.",
)
async def classify_scale(row_count: int = Query(..., ge=0)) -> dict[str, Any]:
    """Classify dataset scale by row count."""
    scale = classify_dataset_scale(row_count)
    strategy = SCALE_STRATEGY_MAP.get(scale, EnterpriseSamplingStrategy.COLUMN_AWARE)

    return {
        "row_count": row_count,
        "scale_category": scale.value,
        "recommended_strategy": strategy.value,
    }
