"""Enterprise Sampling Schemas.

This module provides Pydantic models for truthound 1.2.10's enterprise-scale
sampling capabilities, supporting 100M+ row datasets with:
- Block Sampling
- Multi-Stage Sampling
- Column-Aware Sampling
- Progressive Sampling
- Probabilistic Data Structures (HyperLogLog, Count-Min Sketch, Bloom Filter)

Architecture follows the Strategy pattern for extensibility.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Enums
# ============================================================================


class ScaleCategory(str, Enum):
    """Dataset scale categories for automatic strategy selection."""

    SMALL = "small"  # < 1M rows - no sampling needed
    MEDIUM = "medium"  # 1M - 10M rows - column-aware sampling
    LARGE = "large"  # 10M - 100M rows - block sampling
    XLARGE = "xlarge"  # 100M - 1B rows - multi-stage sampling
    XXLARGE = "xxlarge"  # > 1B rows - sketches + multi-stage


class EnterpriseSamplingStrategy(str, Enum):
    """Enterprise-scale sampling strategies from truthound 1.2.10."""

    # Basic strategies (already supported)
    NONE = "none"
    RANDOM = "random"
    HEAD = "head"
    TAIL = "tail"
    STRATIFIED = "stratified"
    RESERVOIR = "reservoir"
    SYSTEMATIC = "systematic"
    ADAPTIVE = "adaptive"
    HASH = "hash"

    # Enterprise strategies (new in 1.2.10)
    BLOCK = "block"  # Block-based parallel sampling
    MULTI_STAGE = "multi_stage"  # Hierarchical multi-stage sampling
    COLUMN_AWARE = "column_aware"  # Type-weighted adaptive sampling
    PROGRESSIVE = "progressive"  # Convergence-based iterative sampling
    PARALLEL_BLOCK = "parallel_block"  # Multi-threaded block sampling


class SamplingQuality(str, Enum):
    """Sampling quality presets."""

    SKETCH = "sketch"  # Fast approximation, 10K samples
    QUICK = "quick"  # 90% confidence, 50K samples
    STANDARD = "standard"  # 95% confidence, 100K samples (default)
    HIGH = "high"  # 99% confidence, 500K samples
    EXACT = "exact"  # Full scan, 100% accuracy


class SketchType(str, Enum):
    """Probabilistic data structure types."""

    HYPERLOGLOG = "hyperloglog"  # Cardinality estimation
    COUNTMIN = "countmin"  # Frequency estimation
    BLOOM = "bloom"  # Membership testing


class SchedulingPolicy(str, Enum):
    """Parallel execution scheduling policies."""

    ROUND_ROBIN = "round_robin"
    WORK_STEALING = "work_stealing"
    ADAPTIVE = "adaptive"


# ============================================================================
# Configuration Models
# ============================================================================


class MemoryBudgetConfig(BaseModel):
    """Memory budget configuration for enterprise sampling."""

    model_config = ConfigDict(extra="forbid")

    max_memory_mb: int = Field(
        default=1024,
        ge=128,
        le=65536,
        description="Maximum memory in MB",
    )
    reserved_memory_mb: int = Field(
        default=256,
        ge=64,
        le=8192,
        description="Reserved memory for system operations",
    )
    gc_threshold_mb: int | None = Field(
        default=None,
        description="GC trigger threshold (default: 75% of max)",
    )
    backpressure_enabled: bool = Field(
        default=True,
        description="Enable memory backpressure",
    )


class ParallelSamplingConfig(BaseModel):
    """Parallel block sampling configuration."""

    model_config = ConfigDict(extra="forbid")

    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum parallel workers (0 = auto)",
    )
    enable_work_stealing: bool = Field(
        default=True,
        description="Enable work stealing for load balancing",
    )
    scheduling_policy: SchedulingPolicy = Field(
        default=SchedulingPolicy.ADAPTIVE,
        description="Task scheduling policy",
    )
    backpressure_threshold: float = Field(
        default=0.75,
        ge=0.5,
        le=0.95,
        description="Memory threshold for backpressure (0.0-1.0)",
    )
    chunk_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=3600.0,
        description="Timeout per block in seconds",
    )


class BlockSamplingConfig(BaseModel):
    """Block sampling specific configuration."""

    model_config = ConfigDict(extra="forbid")

    block_size: int = Field(
        default=0,
        ge=0,
        description="Rows per block (0 = auto-detect)",
    )
    sample_per_block: int | None = Field(
        default=None,
        description="Samples per block (None = proportional)",
    )
    parallel: ParallelSamplingConfig = Field(
        default_factory=ParallelSamplingConfig,
        description="Parallel processing configuration",
    )


class MultiStageSamplingConfig(BaseModel):
    """Multi-stage hierarchical sampling configuration."""

    model_config = ConfigDict(extra="forbid")

    num_stages: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Number of sampling stages",
    )
    stage_reduction_factor: float | None = Field(
        default=None,
        description="Reduction factor per stage (None = auto)",
    )
    early_stop_enabled: bool = Field(
        default=True,
        description="Enable early stopping on convergence",
    )


class ColumnAwareSamplingConfig(BaseModel):
    """Column-aware adaptive sampling configuration."""

    model_config = ConfigDict(extra="forbid")

    string_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Sample multiplier for string columns",
    )
    categorical_multiplier: float = Field(
        default=0.5,
        ge=0.1,
        le=2.0,
        description="Sample multiplier for categorical columns",
    )
    complex_multiplier: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Sample multiplier for complex types (List/Struct)",
    )
    numeric_multiplier: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Baseline multiplier for numeric columns",
    )


class ProgressiveSamplingConfig(BaseModel):
    """Progressive sampling with convergence detection."""

    model_config = ConfigDict(extra="forbid")

    convergence_threshold: float = Field(
        default=0.01,
        ge=0.001,
        le=0.1,
        description="Convergence threshold (stop when estimates stabilize)",
    )
    max_stages: int = Field(
        default=5,
        ge=2,
        le=10,
        description="Maximum number of progressive stages",
    )
    initial_sample_ratio: float = Field(
        default=0.01,
        ge=0.001,
        le=0.1,
        description="Initial sample ratio (0.01 = 1%)",
    )
    growth_factor: float = Field(
        default=2.0,
        ge=1.5,
        le=4.0,
        description="Sample size growth factor per stage",
    )


class SketchConfig(BaseModel):
    """Probabilistic data structure configuration."""

    model_config = ConfigDict(extra="forbid")

    sketch_type: SketchType = Field(
        default=SketchType.HYPERLOGLOG,
        description="Type of sketch to use",
    )

    # HyperLogLog parameters
    hll_precision: int = Field(
        default=14,
        ge=10,
        le=18,
        description="HyperLogLog precision (10-18, higher = more accurate)",
    )

    # Count-Min Sketch parameters
    cms_width: int = Field(
        default=2000,
        ge=100,
        le=100000,
        description="Count-Min Sketch width",
    )
    cms_depth: int = Field(
        default=5,
        ge=3,
        le=10,
        description="Count-Min Sketch depth",
    )
    cms_epsilon: float | None = Field(
        default=None,
        description="Error bound (alternative to width)",
    )
    cms_delta: float | None = Field(
        default=None,
        description="Confidence level (alternative to depth)",
    )

    # Bloom Filter parameters
    bloom_capacity: int = Field(
        default=10_000_000,
        ge=1000,
        description="Expected number of items",
    )
    bloom_error_rate: float = Field(
        default=0.01,
        ge=0.0001,
        le=0.1,
        description="Desired false positive rate",
    )


# ============================================================================
# Main Request/Response Models
# ============================================================================


class EnterpriseSamplingRequest(BaseModel):
    """Request model for enterprise-scale sampling operations."""

    model_config = ConfigDict(extra="forbid")

    # Basic parameters
    source_id: str = Field(..., description="Source ID to sample from")
    target_rows: int = Field(
        default=100_000,
        ge=1000,
        le=10_000_000,
        description="Target number of rows to sample",
    )
    quality: SamplingQuality = Field(
        default=SamplingQuality.STANDARD,
        description="Sampling quality preset",
    )

    # Strategy selection
    strategy: EnterpriseSamplingStrategy = Field(
        default=EnterpriseSamplingStrategy.ADAPTIVE,
        description="Sampling strategy (adaptive = auto-select)",
    )

    # Resource budgets
    memory_budget: MemoryBudgetConfig = Field(
        default_factory=MemoryBudgetConfig,
        description="Memory budget configuration",
    )
    time_budget_seconds: float = Field(
        default=0.0,
        ge=0.0,
        le=3600.0,
        description="Time budget in seconds (0 = unlimited)",
    )

    # Statistical parameters
    confidence_level: float = Field(
        default=0.95,
        ge=0.80,
        le=0.99,
        description="Statistical confidence level",
    )
    margin_of_error: float = Field(
        default=0.05,
        ge=0.01,
        le=0.10,
        description="Acceptable margin of error",
    )

    # Adaptive parameters
    min_sample_ratio: float = Field(
        default=0.001,
        ge=0.0001,
        le=0.1,
        description="Minimum sample ratio",
    )
    max_sample_ratio: float = Field(
        default=0.10,
        ge=0.01,
        le=1.0,
        description="Maximum sample ratio",
    )

    # Reproducibility
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )

    # Strategy-specific configurations
    block_config: BlockSamplingConfig | None = Field(
        default=None,
        description="Block sampling configuration",
    )
    multi_stage_config: MultiStageSamplingConfig | None = Field(
        default=None,
        description="Multi-stage sampling configuration",
    )
    column_aware_config: ColumnAwareSamplingConfig | None = Field(
        default=None,
        description="Column-aware sampling configuration",
    )
    progressive_config: ProgressiveSamplingConfig | None = Field(
        default=None,
        description="Progressive sampling configuration",
    )

    # Sketch parameters (for XXLARGE datasets)
    sketch_config: SketchConfig | None = Field(
        default=None,
        description="Probabilistic sketch configuration",
    )


class SamplingMetrics(BaseModel):
    """Metrics from sampling operation."""

    model_config = ConfigDict(extra="forbid")

    # Basic metrics
    original_rows: int = Field(..., description="Original row count")
    sampled_rows: int = Field(..., description="Sampled row count")
    sampling_ratio: float = Field(..., description="Actual sampling ratio")

    # Strategy info
    strategy_used: EnterpriseSamplingStrategy = Field(..., description="Strategy used")
    scale_category: ScaleCategory = Field(..., description="Dataset scale category")
    is_sampled: bool = Field(..., description="Whether sampling was performed")

    # Performance metrics
    sampling_time_ms: float = Field(..., description="Total sampling time in ms")
    throughput_rows_per_sec: float = Field(..., description="Processing throughput")
    speedup_factor: float = Field(
        default=1.0,
        description="Speedup compared to full scan",
    )

    # Resource usage
    peak_memory_mb: float = Field(default=0.0, description="Peak memory usage in MB")
    workers_used: int = Field(default=1, description="Number of workers used")
    worker_utilization: float = Field(
        default=0.0,
        description="Worker utilization (0.0-1.0)",
    )

    # Block metrics (for block-based strategies)
    blocks_processed: int | None = Field(
        default=None,
        description="Number of blocks processed",
    )
    time_per_block_ms: float | None = Field(
        default=None,
        description="Average time per block",
    )

    # Progressive metrics
    stages_completed: int | None = Field(
        default=None,
        description="Number of progressive stages",
    )
    converged_early: bool | None = Field(
        default=None,
        description="Whether converged before max stages",
    )

    # Backpressure metrics
    backpressure_events: int = Field(
        default=0,
        description="Number of backpressure events",
    )

    # Statistical info
    margin_of_error_actual: float | None = Field(
        default=None,
        description="Achieved margin of error",
    )
    confidence_achieved: float | None = Field(
        default=None,
        description="Achieved confidence level",
    )


class EnterpriseSamplingResponse(BaseModel):
    """Response model for enterprise sampling operations."""

    model_config = ConfigDict(extra="forbid")

    # Request info
    source_id: str = Field(..., description="Source ID")
    job_id: str = Field(..., description="Sampling job ID")

    # Status
    status: str = Field(..., description="Job status: pending, running, completed, failed")
    started_at: datetime = Field(..., description="Job start time")
    completed_at: datetime | None = Field(None, description="Job completion time")

    # Results
    metrics: SamplingMetrics | None = Field(
        None,
        description="Sampling metrics (available when completed)",
    )
    sampled_data_path: str | None = Field(
        None,
        description="Path to sampled data file",
    )

    # Error info
    error_message: str | None = Field(None, description="Error message if failed")


class SampleSizeEstimateRequest(BaseModel):
    """Request for sample size estimation."""

    model_config = ConfigDict(extra="forbid")

    population_size: int = Field(..., ge=1, description="Total population size")
    confidence_level: float = Field(
        default=0.95,
        ge=0.80,
        le=0.99,
        description="Desired confidence level",
    )
    margin_of_error: float = Field(
        default=0.05,
        ge=0.01,
        le=0.10,
        description="Desired margin of error",
    )
    quality: SamplingQuality = Field(
        default=SamplingQuality.STANDARD,
        description="Quality preset",
    )


class SampleSizeEstimateResponse(BaseModel):
    """Response with sample size recommendations."""

    model_config = ConfigDict(extra="forbid")

    population_size: int = Field(..., description="Input population size")
    scale_category: ScaleCategory = Field(..., description="Dataset scale category")

    # Recommended sizes
    recommended_size: int = Field(..., description="Recommended sample size")
    min_size: int = Field(..., description="Minimum acceptable sample size")
    max_size: int = Field(..., description="Maximum useful sample size")

    # Estimates
    estimated_time_seconds: float = Field(..., description="Estimated processing time")
    estimated_memory_mb: float = Field(..., description="Estimated memory usage")
    speedup_factor: float = Field(..., description="Expected speedup factor")

    # Strategy recommendation
    recommended_strategy: EnterpriseSamplingStrategy = Field(
        ...,
        description="Recommended sampling strategy",
    )
    strategy_rationale: str = Field(..., description="Why this strategy is recommended")


class SketchEstimateRequest(BaseModel):
    """Request for sketch-based estimation."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Source ID")
    columns: list[str] = Field(..., min_length=1, description="Columns to analyze")
    sketch_type: SketchType = Field(..., description="Sketch type")
    sketch_config: SketchConfig | None = Field(
        None,
        description="Sketch configuration",
    )


class SketchEstimateResult(BaseModel):
    """Result from sketch-based estimation."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(..., description="Column name")
    sketch_type: SketchType = Field(..., description="Sketch type used")

    # HyperLogLog results
    cardinality_estimate: int | None = Field(
        None,
        description="Estimated distinct count",
    )
    cardinality_error: float | None = Field(
        None,
        description="Standard error of cardinality estimate",
    )

    # Count-Min Sketch results
    heavy_hitters: list[dict[str, Any]] | None = Field(
        None,
        description="Frequent items with estimated counts",
    )

    # Bloom Filter results
    membership_tests: dict[str, bool] | None = Field(
        None,
        description="Membership test results",
    )

    # Common metrics
    memory_used_bytes: int = Field(..., description="Memory used by sketch")
    processing_time_ms: float = Field(..., description="Processing time in ms")


class SketchEstimateResponse(BaseModel):
    """Response with sketch-based estimates."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Source ID")
    results: list[SketchEstimateResult] = Field(..., description="Results per column")
    total_time_ms: float = Field(..., description="Total processing time")
    total_memory_mb: float = Field(..., description="Total memory used")


# ============================================================================
# Job Management Models
# ============================================================================


class SamplingJobStatus(BaseModel):
    """Sampling job status for monitoring."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., description="Job ID")
    source_id: str = Field(..., description="Source ID")
    status: str = Field(..., description="Job status")
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress (0.0-1.0)",
    )
    current_stage: str | None = Field(None, description="Current processing stage")
    started_at: datetime = Field(..., description="Start time")
    estimated_completion: datetime | None = Field(
        None,
        description="Estimated completion time",
    )

    # Progress details
    rows_processed: int = Field(default=0, description="Rows processed so far")
    blocks_completed: int | None = Field(None, description="Blocks completed")
    blocks_total: int | None = Field(None, description="Total blocks")


class SamplingJobListResponse(BaseModel):
    """Response listing sampling jobs."""

    model_config = ConfigDict(extra="forbid")

    jobs: list[SamplingJobStatus] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total job count")
    active_count: int = Field(..., description="Active job count")
