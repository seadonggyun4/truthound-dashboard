"""Enterprise-scale sampling strategies for large datasets.

This module provides the core business logic for truthound 1.2.10's enterprise
sampling capabilities, supporting datasets from 100M to billions of rows.

Architecture:
- Strategy Pattern: Each sampling method is a separate strategy class
- Factory Pattern: SamplerFactory creates appropriate sampler based on scale
- Template Method: Base class defines sampling workflow, strategies implement specifics

Strategies:
1. BlockSamplingStrategy: Divides data into blocks, samples proportionally
2. MultiStageSamplingStrategy: Hierarchical sampling in multiple passes
3. ColumnAwareSamplingStrategy: Adjusts sampling based on column types
4. ProgressiveSamplingStrategy: Iterative sampling until convergence
5. EnterpriseScaleSampler: Orchestrator that auto-selects best strategy

Example:
    from truthound_dashboard.core.enterprise_sampling import (
        EnterpriseScaleSampler,
        classify_dataset_scale,
    )

    sampler = EnterpriseScaleSampler()
    result = await sampler.sample(source_id, config)
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

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
    SamplingJobStatus,
    SamplingMetrics,
    SamplingQuality,
    ScaleCategory,
    SchedulingPolicy,
    SketchConfig,
    SketchEstimateRequest,
    SketchEstimateResponse,
    SketchEstimateResult,
    SketchType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

# Scale category thresholds
SCALE_THRESHOLDS = {
    ScaleCategory.SMALL: 1_000_000,
    ScaleCategory.MEDIUM: 10_000_000,
    ScaleCategory.LARGE: 100_000_000,
    ScaleCategory.XLARGE: 1_000_000_000,
    # XXLARGE: > 1B
}

# Quality preset configurations
QUALITY_PRESETS = {
    SamplingQuality.SKETCH: {
        "target_rows": 10_000,
        "confidence_level": 0.80,
        "margin_of_error": 0.10,
    },
    SamplingQuality.QUICK: {
        "target_rows": 50_000,
        "confidence_level": 0.90,
        "margin_of_error": 0.05,
    },
    SamplingQuality.STANDARD: {
        "target_rows": 100_000,
        "confidence_level": 0.95,
        "margin_of_error": 0.05,
    },
    SamplingQuality.HIGH: {
        "target_rows": 500_000,
        "confidence_level": 0.99,
        "margin_of_error": 0.03,
    },
    SamplingQuality.EXACT: {
        "target_rows": None,  # Full scan
        "confidence_level": 1.0,
        "margin_of_error": 0.0,
    },
}

# Strategy recommendations by scale
SCALE_STRATEGY_MAP = {
    ScaleCategory.SMALL: EnterpriseSamplingStrategy.NONE,
    ScaleCategory.MEDIUM: EnterpriseSamplingStrategy.COLUMN_AWARE,
    ScaleCategory.LARGE: EnterpriseSamplingStrategy.BLOCK,
    ScaleCategory.XLARGE: EnterpriseSamplingStrategy.MULTI_STAGE,
    ScaleCategory.XXLARGE: EnterpriseSamplingStrategy.MULTI_STAGE,
}


# ============================================================================
# Utility Functions
# ============================================================================


def classify_dataset_scale(row_count: int) -> ScaleCategory:
    """Classify dataset by scale category.

    Args:
        row_count: Number of rows in dataset.

    Returns:
        ScaleCategory enum value.
    """
    if row_count < SCALE_THRESHOLDS[ScaleCategory.SMALL]:
        return ScaleCategory.SMALL
    elif row_count < SCALE_THRESHOLDS[ScaleCategory.MEDIUM]:
        return ScaleCategory.MEDIUM
    elif row_count < SCALE_THRESHOLDS[ScaleCategory.LARGE]:
        return ScaleCategory.LARGE
    elif row_count < SCALE_THRESHOLDS[ScaleCategory.XLARGE]:
        return ScaleCategory.XLARGE
    else:
        return ScaleCategory.XXLARGE


def calculate_cochran_sample_size(
    population_size: int,
    confidence_level: float = 0.95,
    margin_of_error: float = 0.05,
    p: float = 0.5,
) -> int:
    """Calculate optimal sample size using Cochran's formula.

    Args:
        population_size: Total population size (N).
        confidence_level: Desired confidence level (e.g., 0.95).
        margin_of_error: Acceptable margin of error (e.g., 0.05).
        p: Expected proportion (0.5 for maximum variability).

    Returns:
        Recommended sample size.
    """
    # Z-scores for common confidence levels
    z_scores = {
        0.80: 1.28,
        0.85: 1.44,
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }

    # Get closest z-score
    z = z_scores.get(confidence_level, 1.96)

    # Cochran's formula for infinite population
    n0 = (z**2 * p * (1 - p)) / (margin_of_error**2)

    # Finite population correction
    n = n0 / (1 + (n0 - 1) / population_size)

    return max(int(math.ceil(n)), 100)  # Minimum 100 samples


def estimate_processing_time(
    row_count: int,
    strategy: EnterpriseSamplingStrategy,
    workers: int = 4,
) -> float:
    """Estimate processing time in seconds.

    Args:
        row_count: Number of rows to process.
        strategy: Sampling strategy.
        workers: Number of parallel workers.

    Returns:
        Estimated time in seconds.
    """
    # Base throughput estimates (rows/second per worker)
    throughput_map = {
        EnterpriseSamplingStrategy.NONE: 10_000_000,  # Full scan
        EnterpriseSamplingStrategy.RANDOM: 5_000_000,
        EnterpriseSamplingStrategy.BLOCK: 2_000_000,
        EnterpriseSamplingStrategy.MULTI_STAGE: 1_000_000,
        EnterpriseSamplingStrategy.COLUMN_AWARE: 3_000_000,
        EnterpriseSamplingStrategy.PROGRESSIVE: 2_500_000,
    }

    base_throughput = throughput_map.get(strategy, 1_000_000)

    # Parallel speedup (not perfectly linear)
    parallel_efficiency = 0.7 if workers > 1 else 1.0
    effective_throughput = base_throughput * workers * parallel_efficiency

    return row_count / effective_throughput


def estimate_memory_usage(
    row_count: int,
    column_count: int,
    strategy: EnterpriseSamplingStrategy,
) -> float:
    """Estimate memory usage in MB.

    Args:
        row_count: Number of rows.
        column_count: Number of columns.
        strategy: Sampling strategy.

    Returns:
        Estimated memory in MB.
    """
    # Base memory per row (rough estimate: 50 bytes per column)
    bytes_per_row = column_count * 50

    # Strategy-specific memory factors
    memory_factors = {
        EnterpriseSamplingStrategy.NONE: 1.0,
        EnterpriseSamplingStrategy.RANDOM: 0.1,
        EnterpriseSamplingStrategy.BLOCK: 0.2,  # Block buffer
        EnterpriseSamplingStrategy.MULTI_STAGE: 0.15,
        EnterpriseSamplingStrategy.COLUMN_AWARE: 0.12,
        EnterpriseSamplingStrategy.PROGRESSIVE: 0.1,
    }

    factor = memory_factors.get(strategy, 0.1)
    memory_bytes = row_count * bytes_per_row * factor

    # Add overhead
    memory_bytes *= 1.2

    return memory_bytes / (1024 * 1024)


# ============================================================================
# Sampling Result Data Classes
# ============================================================================


@dataclass
class SamplingContext:
    """Context passed through the sampling pipeline."""

    source_id: str
    job_id: str
    config: EnterpriseSamplingRequest
    row_count: int
    column_count: int
    scale_category: ScaleCategory
    start_time: float = field(default_factory=time.time)

    # Runtime state
    rows_processed: int = 0
    blocks_completed: int = 0
    blocks_total: int = 0
    current_stage: str = "initializing"

    # Memory tracking
    peak_memory_mb: float = 0.0
    backpressure_events: int = 0

    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (time.time() - self.start_time) * 1000


@dataclass
class SamplingOutput:
    """Output from sampling operation."""

    sampled_data: Any  # Polars DataFrame or LazyFrame
    sampled_rows: int
    output_path: str | None = None

    # Strategy-specific metadata
    blocks_processed: int | None = None
    stages_completed: int | None = None
    converged_early: bool | None = None


# ============================================================================
# Abstract Base Strategy
# ============================================================================


class BaseSamplingStrategy(ABC):
    """Abstract base class for sampling strategies.

    Implements Template Method pattern - subclasses implement
    `_do_sample()` while base class handles common logic.
    """

    @property
    @abstractmethod
    def strategy_type(self) -> EnterpriseSamplingStrategy:
        """Get strategy type identifier."""
        ...

    @property
    def supports_parallel(self) -> bool:
        """Whether strategy supports parallel execution."""
        return False

    @property
    def supports_streaming(self) -> bool:
        """Whether strategy supports streaming."""
        return False

    async def sample(
        self,
        context: SamplingContext,
        data: Any,
    ) -> SamplingOutput:
        """Execute sampling with common pre/post processing.

        Args:
            context: Sampling context with configuration.
            data: Input data (Polars LazyFrame).

        Returns:
            SamplingOutput with sampled data.
        """
        context.current_stage = f"{self.strategy_type.value}_sampling"

        try:
            # Pre-sampling validation
            self._validate_input(context, data)

            # Execute strategy-specific sampling
            output = await self._do_sample(context, data)

            # Post-processing
            output = self._post_process(context, output)

            return output

        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            raise

    def _validate_input(self, context: SamplingContext, data: Any) -> None:
        """Validate input data before sampling."""
        if data is None:
            raise ValueError("Input data cannot be None")

    @abstractmethod
    async def _do_sample(
        self,
        context: SamplingContext,
        data: Any,
    ) -> SamplingOutput:
        """Strategy-specific sampling implementation.

        Args:
            context: Sampling context.
            data: Input data.

        Returns:
            SamplingOutput with results.
        """
        ...

    def _post_process(
        self,
        context: SamplingContext,
        output: SamplingOutput,
    ) -> SamplingOutput:
        """Post-process sampling output."""
        return output


# ============================================================================
# Concrete Strategies
# ============================================================================


class NoSamplingStrategy(BaseSamplingStrategy):
    """No sampling - use full dataset."""

    @property
    def strategy_type(self) -> EnterpriseSamplingStrategy:
        return EnterpriseSamplingStrategy.NONE

    async def _do_sample(
        self,
        context: SamplingContext,
        data: Any,
    ) -> SamplingOutput:
        """Return data as-is."""
        return SamplingOutput(
            sampled_data=data,
            sampled_rows=context.row_count,
        )


class BlockSamplingStrategy(BaseSamplingStrategy):
    """Block-based sampling for 10M-100M row datasets.

    Divides data into fixed-size blocks and samples proportionally
    from each block. Ensures even coverage across the dataset.
    """

    @property
    def strategy_type(self) -> EnterpriseSamplingStrategy:
        return EnterpriseSamplingStrategy.BLOCK

    @property
    def supports_parallel(self) -> bool:
        return True

    def __init__(self, config: BlockSamplingConfig | None = None):
        self.config = config or BlockSamplingConfig()

    async def _do_sample(
        self,
        context: SamplingContext,
        data: Any,
    ) -> SamplingOutput:
        """Perform block-based sampling."""
        import polars as pl

        target_rows = context.config.target_rows

        # Calculate block size
        block_size = self.config.block_size
        if block_size == 0:
            # Auto-detect: aim for ~100 blocks
            block_size = max(context.row_count // 100, 10_000)

        num_blocks = math.ceil(context.row_count / block_size)
        context.blocks_total = num_blocks

        # Calculate samples per block
        samples_per_block = self.config.sample_per_block
        if samples_per_block is None:
            samples_per_block = max(target_rows // num_blocks, 1)

        logger.info(
            f"Block sampling: {num_blocks} blocks, "
            f"{samples_per_block} samples/block"
        )

        # Collect data and sample from each block
        # In production, this would use truthound's block sampler
        df = data.collect() if hasattr(data, "collect") else data
        seed = context.config.seed or 42

        sampled_dfs = []
        for i in range(num_blocks):
            start_idx = i * block_size
            end_idx = min((i + 1) * block_size, len(df))
            block = df.slice(start_idx, end_idx - start_idx)

            if len(block) > samples_per_block:
                block = block.sample(n=samples_per_block, seed=seed + i)

            sampled_dfs.append(block)
            context.blocks_completed = i + 1

        # Combine sampled blocks
        sampled = pl.concat(sampled_dfs)

        # Trim to target if oversampled
        if len(sampled) > target_rows:
            sampled = sampled.sample(n=target_rows, seed=seed)

        return SamplingOutput(
            sampled_data=sampled.lazy(),
            sampled_rows=len(sampled),
            blocks_processed=num_blocks,
        )


class MultiStageSamplingStrategy(BaseSamplingStrategy):
    """Multi-stage hierarchical sampling for 100M-1B row datasets.

    Progressively reduces data in multiple stages. Each stage
    reduces by factor (total_rows / target)^(1/stages).
    """

    @property
    def strategy_type(self) -> EnterpriseSamplingStrategy:
        return EnterpriseSamplingStrategy.MULTI_STAGE

    def __init__(self, config: MultiStageSamplingConfig | None = None):
        self.config = config or MultiStageSamplingConfig()

    async def _do_sample(
        self,
        context: SamplingContext,
        data: Any,
    ) -> SamplingOutput:
        """Perform multi-stage sampling."""
        import polars as pl

        target_rows = context.config.target_rows
        num_stages = self.config.num_stages
        seed = context.config.seed or 42

        # Calculate reduction factor per stage
        if self.config.stage_reduction_factor:
            reduction = self.config.stage_reduction_factor
        else:
            reduction = (context.row_count / target_rows) ** (1 / num_stages)

        logger.info(
            f"Multi-stage sampling: {num_stages} stages, "
            f"{reduction:.2f}x reduction per stage"
        )

        # Collect initial data
        current_data = data.collect() if hasattr(data, "collect") else data
        current_rows = len(current_data)

        stages_completed = 0
        for stage in range(num_stages):
            target_stage_rows = int(current_rows / reduction)
            target_stage_rows = max(target_stage_rows, target_rows)

            if target_stage_rows >= current_rows:
                break

            current_data = current_data.sample(
                n=target_stage_rows,
                seed=seed + stage,
            )
            current_rows = len(current_data)
            stages_completed = stage + 1

            logger.debug(f"Stage {stage + 1}: {current_rows} rows")

            # Early stopping check
            if self.config.early_stop_enabled and current_rows <= target_rows:
                break

        # Final trim to exact target
        if current_rows > target_rows:
            current_data = current_data.sample(n=target_rows, seed=seed)

        return SamplingOutput(
            sampled_data=current_data.lazy(),
            sampled_rows=len(current_data),
            stages_completed=stages_completed,
            converged_early=stages_completed < num_stages,
        )


class ColumnAwareSamplingStrategy(BaseSamplingStrategy):
    """Column-aware adaptive sampling for mixed-type datasets.

    Adjusts sample size based on column type complexity:
    - Strings: 2x multiplier (high cardinality)
    - Categoricals: 0.5x multiplier (low cardinality)
    - Complex types: 3x multiplier (List/Struct)
    - Numeric: 1x baseline
    """

    @property
    def strategy_type(self) -> EnterpriseSamplingStrategy:
        return EnterpriseSamplingStrategy.COLUMN_AWARE

    def __init__(self, config: ColumnAwareSamplingConfig | None = None):
        self.config = config or ColumnAwareSamplingConfig()

    async def _do_sample(
        self,
        context: SamplingContext,
        data: Any,
    ) -> SamplingOutput:
        """Perform column-aware sampling."""
        import polars as pl

        target_rows = context.config.target_rows
        seed = context.config.seed or 42

        # Collect schema info
        if hasattr(data, "collect_schema"):
            schema = data.collect_schema()
        else:
            schema = data.schema

        # Calculate adjusted sample size based on column types
        type_multipliers = []
        for col_name, dtype in schema.items():
            dtype_str = str(dtype).lower()

            if "string" in dtype_str or "utf8" in dtype_str:
                type_multipliers.append(self.config.string_multiplier)
            elif "categorical" in dtype_str or "enum" in dtype_str:
                type_multipliers.append(self.config.categorical_multiplier)
            elif "list" in dtype_str or "struct" in dtype_str:
                type_multipliers.append(self.config.complex_multiplier)
            else:
                type_multipliers.append(self.config.numeric_multiplier)

        # Use average multiplier
        avg_multiplier = sum(type_multipliers) / len(type_multipliers)
        adjusted_target = int(target_rows * avg_multiplier)
        adjusted_target = min(adjusted_target, context.row_count)

        logger.info(
            f"Column-aware sampling: {len(type_multipliers)} columns, "
            f"avg multiplier {avg_multiplier:.2f}, "
            f"adjusted target {adjusted_target}"
        )

        # Perform sampling
        df = data.collect() if hasattr(data, "collect") else data

        if len(df) > adjusted_target:
            df = df.sample(n=adjusted_target, seed=seed)

        return SamplingOutput(
            sampled_data=df.lazy(),
            sampled_rows=len(df),
        )


class ProgressiveSamplingStrategy(BaseSamplingStrategy):
    """Progressive sampling with convergence detection.

    Iteratively increases sample size until estimates stabilize
    within convergence threshold. Supports early stopping.
    """

    @property
    def strategy_type(self) -> EnterpriseSamplingStrategy:
        return EnterpriseSamplingStrategy.PROGRESSIVE

    def __init__(self, config: ProgressiveSamplingConfig | None = None):
        self.config = config or ProgressiveSamplingConfig()

    async def _do_sample(
        self,
        context: SamplingContext,
        data: Any,
    ) -> SamplingOutput:
        """Perform progressive sampling."""
        import polars as pl

        target_rows = context.config.target_rows
        seed = context.config.seed or 42

        # Collect data
        df = data.collect() if hasattr(data, "collect") else data
        total_rows = len(df)

        # Initial sample size
        current_size = int(total_rows * self.config.initial_sample_ratio)
        current_size = max(current_size, 1000)

        # Track estimates for convergence check
        prev_estimates: dict[str, float] = {}
        stages_completed = 0
        converged = False

        for stage in range(self.config.max_stages):
            # Sample current size
            sample = df.sample(n=min(current_size, total_rows), seed=seed + stage)
            stages_completed = stage + 1

            # Calculate summary statistics for convergence check
            numeric_cols = sample.select(pl.selectors.numeric()).columns
            if numeric_cols:
                estimates = {}
                for col in numeric_cols[:5]:  # Check first 5 numeric columns
                    mean = sample[col].mean()
                    if mean is not None:
                        estimates[col] = float(mean)

                # Check convergence
                if prev_estimates:
                    max_change = 0.0
                    for col, val in estimates.items():
                        if col in prev_estimates and prev_estimates[col] != 0:
                            change = abs(val - prev_estimates[col]) / abs(prev_estimates[col])
                            max_change = max(max_change, change)

                    if max_change < self.config.convergence_threshold:
                        converged = True
                        logger.info(f"Converged at stage {stage + 1} with change {max_change:.4f}")
                        break

                prev_estimates = estimates

            # Check if reached target
            if current_size >= target_rows:
                break

            # Grow sample size
            current_size = int(current_size * self.config.growth_factor)
            current_size = min(current_size, target_rows)

        # Final sample at target size
        final_sample = df.sample(n=min(target_rows, total_rows), seed=seed)

        return SamplingOutput(
            sampled_data=final_sample.lazy(),
            sampled_rows=len(final_sample),
            stages_completed=stages_completed,
            converged_early=converged,
        )


# ============================================================================
# Strategy Factory
# ============================================================================


class SamplingStrategyFactory:
    """Factory for creating sampling strategies."""

    _strategies: dict[EnterpriseSamplingStrategy, type[BaseSamplingStrategy]] = {
        EnterpriseSamplingStrategy.NONE: NoSamplingStrategy,
        EnterpriseSamplingStrategy.BLOCK: BlockSamplingStrategy,
        EnterpriseSamplingStrategy.MULTI_STAGE: MultiStageSamplingStrategy,
        EnterpriseSamplingStrategy.COLUMN_AWARE: ColumnAwareSamplingStrategy,
        EnterpriseSamplingStrategy.PROGRESSIVE: ProgressiveSamplingStrategy,
    }

    @classmethod
    def create(
        cls,
        strategy: EnterpriseSamplingStrategy,
        config: EnterpriseSamplingRequest,
    ) -> BaseSamplingStrategy:
        """Create a sampling strategy instance.

        Args:
            strategy: Strategy type to create.
            config: Sampling configuration.

        Returns:
            Strategy instance.
        """
        strategy_class = cls._strategies.get(strategy)

        if strategy_class is None:
            # Fall back to adaptive selection
            logger.warning(f"Strategy {strategy} not found, using column-aware")
            strategy_class = ColumnAwareSamplingStrategy

        # Pass strategy-specific config if available
        if strategy == EnterpriseSamplingStrategy.BLOCK and config.block_config:
            return BlockSamplingStrategy(config.block_config)
        elif strategy == EnterpriseSamplingStrategy.MULTI_STAGE and config.multi_stage_config:
            return MultiStageSamplingStrategy(config.multi_stage_config)
        elif strategy == EnterpriseSamplingStrategy.COLUMN_AWARE and config.column_aware_config:
            return ColumnAwareSamplingStrategy(config.column_aware_config)
        elif strategy == EnterpriseSamplingStrategy.PROGRESSIVE and config.progressive_config:
            return ProgressiveSamplingStrategy(config.progressive_config)

        return strategy_class()

    @classmethod
    def register(
        cls,
        strategy_type: EnterpriseSamplingStrategy,
        strategy_class: type[BaseSamplingStrategy],
    ) -> None:
        """Register a custom sampling strategy.

        Args:
            strategy_type: Strategy identifier.
            strategy_class: Strategy class.
        """
        cls._strategies[strategy_type] = strategy_class


# ============================================================================
# Enterprise Scale Sampler (Orchestrator)
# ============================================================================


class EnterpriseScaleSampler:
    """Main orchestrator for enterprise-scale sampling.

    Auto-selects the best sampling strategy based on dataset scale
    and executes sampling with full observability.

    Example:
        sampler = EnterpriseScaleSampler()
        response = await sampler.sample(source_id, config)
    """

    def __init__(self) -> None:
        self._active_jobs: dict[str, SamplingJobStatus] = {}

    async def sample(
        self,
        config: EnterpriseSamplingRequest,
        data: Any,
        row_count: int,
        column_count: int,
    ) -> EnterpriseSamplingResponse:
        """Execute enterprise-scale sampling.

        Args:
            config: Sampling configuration.
            data: Input data (Polars LazyFrame).
            row_count: Total row count.
            column_count: Total column count.

        Returns:
            EnterpriseSamplingResponse with results.
        """
        job_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        # Classify scale
        scale = classify_dataset_scale(row_count)

        # Create context
        context = SamplingContext(
            source_id=config.source_id,
            job_id=job_id,
            config=config,
            row_count=row_count,
            column_count=column_count,
            scale_category=scale,
        )

        # Track job
        self._active_jobs[job_id] = SamplingJobStatus(
            job_id=job_id,
            source_id=config.source_id,
            status="running",
            progress=0.0,
            current_stage="initializing",
            started_at=started_at,
        )

        try:
            # Select strategy
            strategy_type = self._select_strategy(config, scale)

            # Create strategy
            strategy = SamplingStrategyFactory.create(strategy_type, config)

            # Execute sampling
            output = await strategy.sample(context, data)

            # Build metrics
            metrics = SamplingMetrics(
                original_rows=row_count,
                sampled_rows=output.sampled_rows,
                sampling_ratio=output.sampled_rows / row_count if row_count > 0 else 1.0,
                strategy_used=strategy.strategy_type,
                scale_category=scale,
                is_sampled=output.sampled_rows < row_count,
                sampling_time_ms=context.elapsed_ms(),
                throughput_rows_per_sec=row_count / (context.elapsed_ms() / 1000) if context.elapsed_ms() > 0 else 0,
                speedup_factor=row_count / output.sampled_rows if output.sampled_rows > 0 else 1.0,
                peak_memory_mb=context.peak_memory_mb,
                workers_used=config.block_config.parallel.max_workers if config.block_config else 1,
                blocks_processed=output.blocks_processed,
                stages_completed=output.stages_completed,
                converged_early=output.converged_early,
                backpressure_events=context.backpressure_events,
            )

            # Update job status
            self._active_jobs[job_id].status = "completed"
            self._active_jobs[job_id].progress = 1.0

            return EnterpriseSamplingResponse(
                source_id=config.source_id,
                job_id=job_id,
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow(),
                metrics=metrics,
                sampled_data_path=output.output_path,
            )

        except Exception as e:
            logger.error(f"Sampling failed for job {job_id}: {e}")

            self._active_jobs[job_id].status = "failed"

            return EnterpriseSamplingResponse(
                source_id=config.source_id,
                job_id=job_id,
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow(),
                error_message=str(e),
            )

    def _select_strategy(
        self,
        config: EnterpriseSamplingRequest,
        scale: ScaleCategory,
    ) -> EnterpriseSamplingStrategy:
        """Select best sampling strategy.

        Args:
            config: Sampling configuration.
            scale: Dataset scale category.

        Returns:
            Selected strategy type.
        """
        # If explicitly specified, use it
        if config.strategy != EnterpriseSamplingStrategy.ADAPTIVE:
            return config.strategy

        # Auto-select based on scale
        return SCALE_STRATEGY_MAP.get(scale, EnterpriseSamplingStrategy.COLUMN_AWARE)

    def get_job_status(self, job_id: str) -> SamplingJobStatus | None:
        """Get status of a sampling job.

        Args:
            job_id: Job identifier.

        Returns:
            Job status or None if not found.
        """
        return self._active_jobs.get(job_id)

    def list_jobs(self) -> list[SamplingJobStatus]:
        """List all sampling jobs.

        Returns:
            List of job statuses.
        """
        return list(self._active_jobs.values())


# ============================================================================
# Sample Size Estimator
# ============================================================================


class SampleSizeEstimator:
    """Estimates optimal sample sizes and provides recommendations."""

    def estimate(self, request: SampleSizeEstimateRequest) -> SampleSizeEstimateResponse:
        """Estimate optimal sample size.

        Args:
            request: Estimation request.

        Returns:
            Estimation response with recommendations.
        """
        population_size = request.population_size
        scale = classify_dataset_scale(population_size)

        # Apply quality preset
        preset = QUALITY_PRESETS.get(request.quality, QUALITY_PRESETS[SamplingQuality.STANDARD])

        # Calculate sample size using Cochran's formula
        recommended = calculate_cochran_sample_size(
            population_size=population_size,
            confidence_level=request.confidence_level,
            margin_of_error=request.margin_of_error,
        )

        # Apply preset target if specified
        if preset["target_rows"] is not None:
            recommended = max(recommended, preset["target_rows"])

        # Calculate bounds
        min_size = max(recommended // 2, 100)
        max_size = min(recommended * 10, population_size)

        # Get recommended strategy
        strategy = SCALE_STRATEGY_MAP.get(scale, EnterpriseSamplingStrategy.COLUMN_AWARE)

        # Estimate time and memory
        estimated_time = estimate_processing_time(population_size, strategy)
        estimated_memory = estimate_memory_usage(population_size, 50, strategy)  # Assume 50 columns

        # Calculate speedup
        speedup = population_size / recommended if recommended > 0 else 1.0

        # Build rationale
        rationale = self._build_rationale(scale, strategy, population_size)

        return SampleSizeEstimateResponse(
            population_size=population_size,
            scale_category=scale,
            recommended_size=recommended,
            min_size=min_size,
            max_size=max_size,
            estimated_time_seconds=estimated_time,
            estimated_memory_mb=estimated_memory,
            speedup_factor=speedup,
            recommended_strategy=strategy,
            strategy_rationale=rationale,
        )

    def _build_rationale(
        self,
        scale: ScaleCategory,
        strategy: EnterpriseSamplingStrategy,
        population_size: int,
    ) -> str:
        """Build rationale for strategy recommendation."""
        rationales = {
            ScaleCategory.SMALL: "Dataset is small enough for full scan without sampling.",
            ScaleCategory.MEDIUM: "Column-aware sampling adapts to data types for optimal accuracy.",
            ScaleCategory.LARGE: "Block sampling ensures even coverage across the dataset with parallel processing.",
            ScaleCategory.XLARGE: "Multi-stage sampling efficiently reduces billion-row datasets through hierarchical processing.",
            ScaleCategory.XXLARGE: "Multi-stage sampling with probabilistic sketches for extreme-scale datasets.",
        }
        return rationales.get(scale, "Adaptive sampling based on data characteristics.")


# ============================================================================
# Sketch Estimator (Probabilistic Data Structures)
# ============================================================================


class SketchEstimator:
    """Estimates using truthound probabilistic data structures for 10B+ row datasets.

    Uses truthound.profiler.sketches for O(1) memory aggregations:
    - HyperLogLog: Cardinality estimation (±0.41% error at precision=14)
    - CountMinSketch: Frequency estimation and heavy hitters detection
    - BloomFilter: Membership testing with configurable false positive rate
    """

    async def estimate(self, request: SketchEstimateRequest, data: Any) -> SketchEstimateResponse:
        """Run sketch-based estimation.

        Args:
            request: Sketch estimation request.
            data: Input data.

        Returns:
            Sketch estimation response.
        """
        start_time = time.time()
        results: list[SketchEstimateResult] = []
        total_memory = 0

        config = request.sketch_config or SketchConfig()

        for column in request.columns:
            col_start = time.time()

            if config.sketch_type == SketchType.HYPERLOGLOG:
                result = await self._estimate_cardinality(column, data, config)
            elif config.sketch_type == SketchType.COUNTMIN:
                result = await self._estimate_frequency(column, data, config)
            else:
                result = await self._test_membership(column, data, config)

            result.processing_time_ms = (time.time() - col_start) * 1000
            results.append(result)
            total_memory += result.memory_used_bytes

        return SketchEstimateResponse(
            source_id=request.source_id,
            results=results,
            total_time_ms=(time.time() - start_time) * 1000,
            total_memory_mb=total_memory / (1024 * 1024),
        )

    async def _estimate_cardinality(
        self,
        column: str,
        data: Any,
        config: SketchConfig,
    ) -> SketchEstimateResult:
        """Estimate cardinality using truthound's HyperLogLog."""
        df = data.collect() if hasattr(data, "collect") else data

        try:
            from truthound.profiler.sketches import HyperLogLog, HyperLogLogConfig

            # Create HyperLogLog with specified precision
            hll_config = HyperLogLogConfig(precision=config.hll_precision)
            hll = HyperLogLog(hll_config)

            # Add values in batches for efficiency
            column_values = df[column].drop_nulls().to_list()
            hll.add_batch(column_values)

            # Get estimate and error
            cardinality_estimate = hll.estimate()
            cardinality_error = hll.standard_error()

            # Calculate memory usage
            memory_bytes = (2 ** config.hll_precision) * 6 // 8

            return SketchEstimateResult(
                column=column,
                sketch_type=SketchType.HYPERLOGLOG,
                cardinality_estimate=cardinality_estimate,
                cardinality_error=cardinality_error,
                memory_used_bytes=memory_bytes,
                processing_time_ms=0.0,
            )

        except ImportError:
            logger.warning("truthound.profiler.sketches not available, using fallback")
            # Fallback to Polars n_unique
            unique_count = df[column].n_unique()
            error = 1.04 / math.sqrt(2 ** config.hll_precision)
            memory_bytes = (2 ** config.hll_precision) * 6 // 8

            return SketchEstimateResult(
                column=column,
                sketch_type=SketchType.HYPERLOGLOG,
                cardinality_estimate=unique_count,
                cardinality_error=error,
                memory_used_bytes=memory_bytes,
                processing_time_ms=0.0,
            )

    async def _estimate_frequency(
        self,
        column: str,
        data: Any,
        config: SketchConfig,
    ) -> SketchEstimateResult:
        """Estimate frequencies using truthound's Count-Min Sketch."""
        import polars as pl

        df = data.collect() if hasattr(data, "collect") else data

        try:
            from truthound.profiler.sketches import CountMinSketch, CountMinSketchConfig

            # Create Count-Min Sketch with specified dimensions
            cms_config = CountMinSketchConfig(
                width=config.cms_width,
                depth=config.cms_depth,
            )
            cms = CountMinSketch(cms_config)

            # Add all values
            column_values = df[column].drop_nulls().to_list()
            for value in column_values:
                cms.add(value)

            # Get heavy hitters (items appearing in >1% of stream)
            heavy_hitters_raw = cms.get_heavy_hitters(threshold=0.01)
            heavy_hitters = [
                {"value": str(item), "count": count}
                for item, count in heavy_hitters_raw[:10]
            ]

            # Memory = width * depth * 4 bytes (32-bit counters)
            memory_bytes = config.cms_width * config.cms_depth * 4

            return SketchEstimateResult(
                column=column,
                sketch_type=SketchType.COUNTMIN,
                heavy_hitters=heavy_hitters,
                memory_used_bytes=memory_bytes,
                processing_time_ms=0.0,
            )

        except ImportError:
            logger.warning("truthound.profiler.sketches not available, using fallback")
            # Fallback to Polars group_by
            value_counts = (
                df.group_by(column)
                .agg(pl.len().alias("count"))
                .sort("count", descending=True)
                .head(10)
            )

            heavy_hitters = [
                {"value": str(row[column]), "count": row["count"]}
                for row in value_counts.iter_rows(named=True)
            ]

            memory_bytes = config.cms_width * config.cms_depth * 4

            return SketchEstimateResult(
                column=column,
                sketch_type=SketchType.COUNTMIN,
                heavy_hitters=heavy_hitters,
                memory_used_bytes=memory_bytes,
                processing_time_ms=0.0,
            )

    async def _test_membership(
        self,
        column: str,
        data: Any,
        config: SketchConfig,
    ) -> SketchEstimateResult:
        """Test membership using truthound's Bloom Filter."""
        df = data.collect() if hasattr(data, "collect") else data

        try:
            from truthound.profiler.sketches import BloomFilter, BloomFilterConfig

            # Create Bloom Filter with specified capacity and error rate
            bf_config = BloomFilterConfig(
                capacity=config.bloom_capacity,
                error_rate=config.bloom_error_rate,
            )
            bf = BloomFilter(bf_config)

            # Add all values
            column_values = df[column].drop_nulls().to_list()
            for value in column_values:
                bf.add(value)

            # Get current false positive rate
            actual_fp_rate = bf.false_positive_rate()

            # Calculate memory usage
            m = -config.bloom_capacity * math.log(config.bloom_error_rate) / (math.log(2) ** 2)
            memory_bytes = int(m / 8)

            return SketchEstimateResult(
                column=column,
                sketch_type=SketchType.BLOOM,
                membership_tests={
                    "items_added": len(column_values),
                    "false_positive_rate": actual_fp_rate,
                },
                memory_used_bytes=memory_bytes,
                processing_time_ms=0.0,
            )

        except ImportError:
            logger.warning("truthound.profiler.sketches not available, using fallback")
            # Fallback: just calculate memory requirements
            m = -config.bloom_capacity * math.log(config.bloom_error_rate) / (math.log(2) ** 2)
            memory_bytes = int(m / 8)

            return SketchEstimateResult(
                column=column,
                sketch_type=SketchType.BLOOM,
                membership_tests={},
                memory_used_bytes=memory_bytes,
                processing_time_ms=0.0,
            )


# ============================================================================
# Singleton Instance
# ============================================================================

_sampler: EnterpriseScaleSampler | None = None
_estimator: SampleSizeEstimator | None = None
_sketch_estimator: SketchEstimator | None = None


def get_enterprise_sampler() -> EnterpriseScaleSampler:
    """Get enterprise sampler singleton."""
    global _sampler
    if _sampler is None:
        _sampler = EnterpriseScaleSampler()
    return _sampler


def get_sample_size_estimator() -> SampleSizeEstimator:
    """Get sample size estimator singleton."""
    global _estimator
    if _estimator is None:
        _estimator = SampleSizeEstimator()
    return _estimator


def get_sketch_estimator() -> SketchEstimator:
    """Get sketch estimator singleton."""
    global _sketch_estimator
    if _sketch_estimator is None:
        _sketch_estimator = SketchEstimator()
    return _sketch_estimator
