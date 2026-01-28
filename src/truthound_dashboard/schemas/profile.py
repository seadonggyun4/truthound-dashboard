"""Profile-related Pydantic schemas.

This module defines schemas for data profiling API operations.

Note: truthound's th.profile() only supports (data, source) parameters.
Advanced options like sampling strategies, pattern detection configuration,
and correlation analysis are NOT supported by the underlying library.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import BaseSchema


# =============================================================================
# Profile Request Schema (Simplified)
# =============================================================================


class ProfileRequest(BaseSchema):
    """Request schema for basic data profiling.

    Note: truthound's th.profile() does not support advanced configuration.
    This schema exists for API compatibility but options are not used.
    For advanced profiling with configuration, use ProfileAdvancedRequest.
    """

    pass


class ProfileAdvancedRequest(BaseSchema):
    """Request schema for advanced data profiling with ProfilerConfig options.

    This schema maps to truthound's ProfilerConfig for fine-grained control
    over profiling behavior.
    """

    sample_size: int | None = Field(
        default=None,
        ge=100,
        description="Maximum rows to sample (None for all rows)",
    )
    random_seed: int = Field(
        default=42,
        ge=0,
        description="Random seed for reproducible sampling",
    )
    include_patterns: bool = Field(
        default=True,
        description="Enable pattern detection (email, phone, uuid, etc.)",
    )
    include_correlations: bool = Field(
        default=False,
        description="Calculate column correlations (can be slow for many columns)",
    )
    include_distributions: bool = Field(
        default=True,
        description="Include value distribution histograms",
    )
    top_n_values: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of top values to return per column",
    )
    pattern_sample_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Sample size for pattern detection",
    )
    correlation_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum correlation to report",
    )
    min_pattern_match_ratio: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Minimum match ratio to consider a pattern detected",
    )
    n_jobs: int = Field(
        default=1,
        ge=1,
        le=16,
        description="Number of parallel jobs for profiling",
    )


# =============================================================================
# Pattern Detection Results
# =============================================================================


class DetectedPattern(BaseSchema):
    """A detected data pattern in a column."""

    pattern_type: str = Field(
        ...,
        description="Type of pattern detected (email, phone, uuid, etc.)",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the pattern match (0-1).",
    )
    match_count: int = Field(
        ...,
        ge=0,
        description="Number of values matching this pattern.",
    )
    match_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of non-null values matching this pattern.",
    )
    sample_matches: list[str] | None = Field(
        default=None,
        description="Sample values matching this pattern (masked for sensitive data).",
    )


class HistogramBucket(BaseSchema):
    """A bucket in a value distribution histogram."""

    bucket: str = Field(..., description="Bucket label (range or category)")
    count: int = Field(..., ge=0, description="Count of values in this bucket")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total")


# =============================================================================
# Column Profile Schema
# =============================================================================


class ColumnProfile(BaseSchema):
    """Profile information for a single column.

    Includes basic statistics and distribution data.
    """

    # Basic identification
    name: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Physical data type (string, int64, float64, etc.)")

    # Inferred semantic type
    inferred_type: str | None = Field(
        default=None,
        description="Inferred semantic type based on pattern detection "
        "(email, phone, uuid, url, date, currency, etc.)",
    )

    # Completeness metrics
    null_pct: str = Field(default="0%", description="Percentage of null values")
    null_count: int | None = Field(default=None, description="Count of null values")

    # Uniqueness metrics
    unique_pct: str = Field(default="0%", description="Percentage of unique values")
    distinct_count: int | None = Field(
        default=None,
        description="Count of distinct values",
    )
    is_unique: bool | None = Field(
        default=None,
        description="Whether all non-null values are unique",
    )

    # Value range (for numeric/date columns)
    min: Any | None = Field(default=None, description="Minimum value")
    max: Any | None = Field(default=None, description="Maximum value")

    # Statistical measures (for numeric columns)
    mean: float | None = Field(default=None, description="Mean value (numeric columns)")
    std: float | None = Field(default=None, description="Standard deviation (numeric)")
    median: float | None = Field(default=None, description="Median value (numeric)")
    q1: float | None = Field(default=None, description="25th percentile (Q1)")
    q3: float | None = Field(default=None, description="75th percentile (Q3)")
    skewness: float | None = Field(default=None, description="Skewness of distribution")
    kurtosis: float | None = Field(default=None, description="Kurtosis of distribution")

    # String-specific metrics
    min_length: int | None = Field(default=None, description="Minimum string length")
    max_length: int | None = Field(default=None, description="Maximum string length")
    avg_length: float | None = Field(default=None, description="Average string length")

    # Pattern detection results
    patterns: list[DetectedPattern] | None = Field(
        default=None,
        description="Detected data patterns (email, phone, uuid, etc.)",
    )
    primary_pattern: str | None = Field(
        default=None,
        description="The most prevalent detected pattern type",
    )

    # Distribution data
    most_common: list[dict[str, Any]] | None = Field(
        default=None,
        description="Most common values with counts",
    )
    histogram: list[HistogramBucket] | None = Field(
        default=None,
        description="Value distribution histogram",
    )

    # Cardinality estimate for high-cardinality columns
    cardinality_estimate: int | None = Field(
        default=None,
        description="Estimated cardinality using HyperLogLog (for high-cardinality columns)",
    )


# =============================================================================
# Profile Response Schema
# =============================================================================


class ProfileResponse(BaseSchema):
    """Data profiling response with statistics."""

    source: str = Field(..., description="Source path/identifier")
    row_count: int = Field(..., ge=0, description="Total number of rows")
    column_count: int = Field(..., ge=0, description="Total number of columns")
    size_bytes: int = Field(..., ge=0, description="Data size in bytes")
    columns: list[ColumnProfile] = Field(
        default_factory=list,
        description="Profile for each column",
    )

    # Pattern detection summary
    detected_patterns_summary: dict[str, int] | None = Field(
        default=None,
        description="Summary of detected patterns across all columns {pattern_type: count}",
    )

    # Profiling metadata
    profiled_at: str | None = Field(
        default=None,
        description="ISO timestamp when profiling was performed",
    )
    profiling_duration_ms: int | None = Field(
        default=None,
        description="Time taken to profile in milliseconds",
    )

    # Computed properties
    @property
    def size_human(self) -> str:
        """Get human-readable size."""
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    @classmethod
    def _build_column_profile(cls, col: dict[str, Any] | Any) -> ColumnProfile:
        """Build a ColumnProfile from column data dict or ColumnProfileResult object.

        Args:
            col: Column data dictionary from adapter or database, or ColumnProfileResult object.

        Returns:
            ColumnProfile instance with all available fields.
        """
        # Helper function to get attribute from dict or object
        def get_val(key: str, default: Any = None) -> Any:
            if isinstance(col, dict):
                return col.get(key, default)
            return getattr(col, key, default)

        # Build patterns list if present
        patterns = None
        patterns_data = get_val("patterns") or get_val("detected_patterns")
        if patterns_data:
            patterns = [
                DetectedPattern(
                    pattern_type=p.get("pattern_type", p.get("type", p.get("pattern", "unknown")))
                    if isinstance(p, dict)
                    else getattr(p, "pattern_type", getattr(p, "pattern", "unknown")),
                    confidence=p.get("confidence", 0.0)
                    if isinstance(p, dict)
                    else getattr(p, "confidence", getattr(p, "match_ratio", 0.0)),
                    match_count=p.get("match_count", 0) if isinstance(p, dict) else getattr(p, "match_count", 0),
                    match_percentage=p.get("match_percentage", 0.0)
                    if isinstance(p, dict)
                    else getattr(p, "match_percentage", getattr(p, "match_ratio", 0.0) * 100),
                    sample_matches=p.get("sample_matches") if isinstance(p, dict) else getattr(p, "sample_matches", None),
                )
                for p in patterns_data
            ]

        # Build histogram if present
        histogram = None
        histogram_data = get_val("histogram")
        if histogram_data:
            histogram = [
                HistogramBucket(
                    bucket=h.get("bucket", "") if isinstance(h, dict) else getattr(h, "bucket", ""),
                    count=h.get("count", 0) if isinstance(h, dict) else getattr(h, "count", 0),
                    percentage=h.get("percentage", 0.0) if isinstance(h, dict) else getattr(h, "percentage", 0.0),
                )
                for h in histogram_data
            ]

        # Get dtype from dict or object (physical_type for ColumnProfileResult)
        dtype = get_val("dtype") or get_val("physical_type") or "unknown"

        # Get null_pct - format from ratio if needed
        null_pct = get_val("null_pct", "0%")
        if null_pct == "0%" and get_val("null_ratio") is not None:
            null_ratio = get_val("null_ratio", 0.0)
            null_pct = f"{null_ratio * 100:.1f}%"

        # Get unique_pct - format from ratio if needed
        unique_pct = get_val("unique_pct", "0%")
        if unique_pct == "0%" and get_val("unique_ratio") is not None:
            unique_ratio = get_val("unique_ratio", 0.0)
            unique_pct = f"{unique_ratio * 100:.1f}%"

        # Get distribution stats
        distribution = get_val("distribution")
        mean = get_val("mean")
        std = get_val("std")
        median = get_val("median")
        q1 = get_val("q1")
        q3 = get_val("q3")
        skewness = get_val("skewness")
        kurtosis = get_val("kurtosis")
        min_val = get_val("min")
        max_val = get_val("max")

        # Extract from distribution dict if present
        if distribution and isinstance(distribution, dict):
            mean = mean or distribution.get("mean")
            std = std or distribution.get("std")
            median = median or distribution.get("median")
            q1 = q1 or distribution.get("q1")
            q3 = q3 or distribution.get("q3")
            skewness = skewness or distribution.get("skewness")
            kurtosis = kurtosis or distribution.get("kurtosis")
            min_val = min_val or distribution.get("min")
            max_val = max_val or distribution.get("max")

        # Get most_common from top_values if needed
        most_common = get_val("most_common")
        if not most_common and get_val("top_values"):
            most_common = get_val("top_values")

        return ColumnProfile(
            name=get_val("name"),
            dtype=dtype,
            inferred_type=get_val("inferred_type"),
            null_pct=null_pct,
            null_count=get_val("null_count"),
            unique_pct=unique_pct,
            distinct_count=get_val("distinct_count"),
            is_unique=get_val("is_unique"),
            min=min_val,
            max=max_val,
            mean=mean,
            std=std,
            median=median,
            q1=q1,
            q3=q3,
            skewness=skewness,
            kurtosis=kurtosis,
            min_length=get_val("min_length"),
            max_length=get_val("max_length"),
            avg_length=get_val("avg_length"),
            patterns=patterns,
            primary_pattern=get_val("primary_pattern"),
            most_common=most_common,
            histogram=histogram,
            cardinality_estimate=get_val("cardinality_estimate"),
        )

    @classmethod
    def from_result(cls, result: Any) -> ProfileResponse:
        """Create response from adapter result or Profile model.

        Args:
            result: ProfileResult from adapter or Profile model.

        Returns:
            ProfileResponse instance.
        """
        # Handle Profile model (from database)
        if hasattr(result, "profile_json"):
            profile_json = result.profile_json
            source_name = profile_json.get("source", result.source_id)
            columns_data = profile_json.get("columns", [])
            columns = [cls._build_column_profile(col) for col in columns_data]

            return cls(
                source=source_name,
                row_count=result.row_count or 0,
                column_count=result.column_count or 0,
                size_bytes=result.size_bytes or 0,
                columns=columns,
                detected_patterns_summary=profile_json.get("detected_patterns_summary"),
                profiled_at=profile_json.get("profiled_at"),
                profiling_duration_ms=profile_json.get("profiling_duration_ms"),
            )

        # Handle ProfileResult (from adapter)
        columns = [cls._build_column_profile(col) for col in result.columns]

        return cls(
            source=result.source,
            row_count=result.row_count,
            column_count=result.column_count,
            size_bytes=result.size_bytes,
            columns=columns,
            detected_patterns_summary=getattr(result, "detected_patterns_summary", None),
            profiled_at=getattr(result, "profiled_at", None),
            profiling_duration_ms=getattr(result, "profiling_duration_ms", None),
        )
