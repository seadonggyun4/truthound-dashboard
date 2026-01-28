"""Drift detection schemas.

Schemas for drift comparison request/response.

Drift Methods (14 supported by th.compare() in truthound v1.2.9+):

General purpose (any column type):
- auto: Smart selection (numeric → PSI, categorical → chi2) [RECOMMENDED]
- js: Jensen-Shannon divergence (symmetric, bounded 0-1)
- hellinger: Hellinger distance (bounded metric, 0-1)
- bhattacharyya: Bhattacharyya distance (classification error bounds)
- tv: Total Variation distance (max probability difference)

Numeric columns only:
- ks: Kolmogorov-Smirnov test
- psi: Population Stability Index (industry standard)
- kl: Kullback-Leibler divergence (asymmetric)
- wasserstein: Wasserstein/Earth Mover's Distance
- cvm: Cramér-von Mises test (tail sensitive)
- anderson: Anderson-Darling test (most tail sensitive)
- energy: Energy distance (location/scale sensitive)
- mmd: Maximum Mean Discrepancy (kernel-based, high-dimensional)

Categorical columns:
- chi2: Chi-Square test
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from .base import IDMixin, TimestampMixin


class DriftMethod(str, Enum):
    """Drift detection methods supported by truthound v1.2.9+.

    All 14 methods are fully supported by th.compare():

    General purpose (any column type):
    - auto: Smart selection based on data type (numeric → PSI, categorical → chi2)
    - js: Jensen-Shannon divergence - symmetric, bounded (0-1)
    - hellinger: Hellinger distance - bounded metric (0-1), triangle inequality
    - bhattacharyya: Bhattacharyya distance - classification error bounds
    - tv: Total Variation distance - max probability difference

    Numeric columns only:
    - ks: Kolmogorov-Smirnov test - detects any distribution shape difference
    - psi: Population Stability Index - industry standard for model monitoring
    - kl: Kullback-Leibler divergence - measures information loss (asymmetric)
    - wasserstein: Earth Mover's Distance - intuitive physical interpretation
    - cvm: Cramér-von Mises - more sensitive to tails than KS
    - anderson: Anderson-Darling - most sensitive to tail differences
    - energy: Energy distance - location/scale sensitive
    - mmd: Maximum Mean Discrepancy - kernel-based, high-dimensional

    Categorical columns:
    - chi2: Chi-Square test - best for categorical data
    """

    AUTO = "auto"
    KS = "ks"
    PSI = "psi"
    CHI2 = "chi2"
    JS = "js"
    KL = "kl"
    WASSERSTEIN = "wasserstein"
    CVM = "cvm"
    ANDERSON = "anderson"
    # New in v1.2.9
    HELLINGER = "hellinger"
    BHATTACHARYYA = "bhattacharyya"
    TV = "tv"
    ENERGY = "energy"
    MMD = "mmd"


# Default thresholds for each detection method
DEFAULT_THRESHOLDS: dict[DriftMethod, float] = {
    DriftMethod.AUTO: 0.05,
    DriftMethod.KS: 0.05,
    DriftMethod.PSI: 0.1,
    DriftMethod.CHI2: 0.05,
    DriftMethod.JS: 0.1,
    DriftMethod.KL: 0.1,
    DriftMethod.WASSERSTEIN: 0.1,  # Scale-dependent, adjust based on data
    DriftMethod.CVM: 0.05,
    DriftMethod.ANDERSON: 0.05,
    # New in v1.2.9
    DriftMethod.HELLINGER: 0.1,
    DriftMethod.BHATTACHARYYA: 0.1,
    DriftMethod.TV: 0.1,
    DriftMethod.ENERGY: 0.1,
    DriftMethod.MMD: 0.1,
}


def get_default_threshold(method: DriftMethod | str) -> float:
    """Get default threshold for a drift detection method.

    Args:
        method: Drift detection method

    Returns:
        Default threshold value for the method
    """
    if isinstance(method, str):
        try:
            method = DriftMethod(method)
        except ValueError:
            return 0.05  # Fallback default
    return DEFAULT_THRESHOLDS.get(method, 0.05)


# Type alias for method values (for Literal type hints)
DriftMethodLiteral = Literal[
    "auto", "ks", "psi", "chi2", "js", "kl", "wasserstein", "cvm", "anderson",
    "hellinger", "bhattacharyya", "tv", "energy", "mmd"
]


class DriftCompareRequest(BaseModel):
    """Request body for drift comparison."""

    baseline_source_id: str = Field(..., description="Baseline source ID")
    current_source_id: str = Field(..., description="Current source ID to compare")
    columns: list[str] | None = Field(
        None, description="Columns to compare (None = all)"
    )
    method: DriftMethodLiteral = Field(
        "auto",
        description=(
            "Drift detection method (14 available): "
            "auto (smart selection), ks, psi, chi2, js, kl, wasserstein, cvm, anderson, "
            "hellinger, bhattacharyya, tv, energy, mmd"
        ),
    )
    threshold: float | None = Field(
        None,
        ge=0,
        le=1,
        description="Custom threshold (default varies by method: KS/chi2/cvm/anderson=0.05, PSI/JS/KL/wasserstein=0.1)",
    )
    sample_size: int | None = Field(
        None, ge=100, description="Sample size for large datasets"
    )


class ColumnDriftResult(BaseModel):
    """Drift result for a single column."""

    column: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Data type")
    drifted: bool = Field(..., description="Whether drift was detected")
    level: str = Field(..., description="Drift level (high, medium, low, none)")
    method: str = Field(..., description="Detection method used")
    statistic: float | None = Field(None, description="Test statistic value")
    p_value: float | None = Field(None, description="P-value")
    baseline_stats: dict[str, Any] = Field(
        default_factory=dict, description="Baseline statistics"
    )
    current_stats: dict[str, Any] = Field(
        default_factory=dict, description="Current statistics"
    )


class DriftResult(BaseModel):
    """Full drift comparison result."""

    baseline_source: str = Field(..., description="Baseline source path")
    current_source: str = Field(..., description="Current source path")
    baseline_rows: int = Field(..., description="Number of baseline rows")
    current_rows: int = Field(..., description="Number of current rows")
    has_drift: bool = Field(..., description="Whether any drift was detected")
    has_high_drift: bool = Field(
        ..., description="Whether high-severity drift was detected"
    )
    total_columns: int = Field(..., description="Total columns compared")
    drifted_columns: list[str] = Field(
        default_factory=list, description="Columns with drift"
    )
    columns: list[ColumnDriftResult] = Field(
        default_factory=list, description="Per-column results"
    )


class DriftSourceSummary(BaseModel):
    """Summary of a source in drift comparison."""

    id: str = Field(..., description="Source ID")
    name: str = Field(..., description="Source name")


class DriftComparisonResponse(BaseModel, IDMixin, TimestampMixin):
    """Response for drift comparison."""

    baseline_source_id: str = Field(..., description="Baseline source ID")
    current_source_id: str = Field(..., description="Current source ID")
    has_drift: bool = Field(..., description="Whether drift was detected")
    has_high_drift: bool = Field(
        ..., description="Whether high-severity drift was detected"
    )
    total_columns: int | None = Field(None, description="Total columns compared")
    drifted_columns: int | None = Field(
        None, description="Number of columns with drift"
    )
    drift_percentage: float = Field(0, description="Percentage of columns with drift")
    result: DriftResult | None = Field(None, description="Full drift result")
    config: dict[str, Any] | None = Field(None, description="Comparison configuration")

    # Optional source details
    baseline: DriftSourceSummary | None = Field(
        None, description="Baseline source info"
    )
    current: DriftSourceSummary | None = Field(None, description="Current source info")


class DriftComparisonListItem(BaseModel, IDMixin, TimestampMixin):
    """List item for drift comparisons."""

    baseline_source_id: str
    current_source_id: str
    has_drift: bool
    has_high_drift: bool
    total_columns: int | None = None
    drifted_columns: int | None = None
    drift_percentage: float = 0


class DriftComparisonListResponse(BaseModel):
    """Paginated list response for drift comparisons."""

    data: list[DriftComparisonListItem] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 100
