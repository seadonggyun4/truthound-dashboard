"""Protocol definitions for data quality operations.

This module defines the interfaces (protocols) that abstract away the
specific data quality library implementation (e.g., truthound).

Using protocols allows:
- Runtime duck typing (any object with matching methods works)
- Static type checking with mypy
- Easy mocking for tests
- Future backend swapping without code changes

Example:
    class MyCustomBackend(IDataQualityBackend):
        async def check(self, data, **kwargs) -> ICheckResult:
            # Custom implementation
            pass
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Any, Protocol, Union, runtime_checkable

# Type alias for data input - can be path string or DataSource object
DataInput = Union[str, Any]


# =============================================================================
# Data Source Capabilities
# =============================================================================


class DataSourceCapability(Enum):
    """Capabilities that a data source may support.

    This enum mirrors truthound's DataSourceCapability for loose coupling.
    Data sources declare their capabilities to enable optimizations.
    """
    LAZY_EVALUATION = auto()  # Supports lazy/deferred execution
    SQL_PUSHDOWN = auto()     # Can push operations to database
    SAMPLING = auto()         # Supports data sampling
    STREAMING = auto()        # Supports streaming processing
    SCHEMA_INFERENCE = auto() # Can infer schema automatically
    ROW_COUNT = auto()        # Can efficiently count rows
    CONNECTION_TEST = auto()  # Supports connection testing


# =============================================================================
# Data Source Configuration Protocol
# =============================================================================


@runtime_checkable
class IDataSourceConfig(Protocol):
    """Protocol for data source configuration objects.

    This abstracts away the specific configuration implementation
    to allow different backends to use their own config classes.
    """

    @property
    def name(self) -> str | None:
        """Get the source name."""
        ...

    @property
    def max_rows(self) -> int | None:
        """Get max rows limit."""
        ...

    @property
    def sample_size(self) -> int | None:
        """Get default sample size."""
        ...


# =============================================================================
# Data Source Protocol
# =============================================================================


@runtime_checkable
class IDataSource(Protocol):
    """Protocol for data source objects.

    Any object that provides access to tabular data should implement
    this interface. This abstracts away the specific DataSource
    implementation from truthound or other libraries.
    """

    @property
    def name(self) -> str:
        """Get the data source name."""
        ...

    @property
    def columns(self) -> list[str]:
        """Get list of column names."""
        ...

    @property
    def row_count(self) -> int | None:
        """Get row count if available."""
        ...

    @property
    def capabilities(self) -> set[DataSourceCapability]:
        """Get the capabilities of this data source.

        Returns:
            Set of capabilities this source supports.
        """
        ...

    def to_polars_lazyframe(self) -> Any:
        """Convert to Polars LazyFrame for processing.

        Returns:
            Polars LazyFrame representation of the data.
        """
        ...


# =============================================================================
# Validation Issue Protocol
# =============================================================================


@runtime_checkable
class IValidationIssue(Protocol):
    """Protocol for validation issue objects.

    Represents a single data quality issue found during validation.
    """

    @property
    def column(self) -> str:
        """Column name where issue was found."""
        ...

    @property
    def issue_type(self) -> str:
        """Type of issue (e.g., 'null_values', 'out_of_range')."""
        ...

    @property
    def count(self) -> int:
        """Number of rows affected."""
        ...

    @property
    def severity(self) -> Any:
        """Issue severity (may be enum or string)."""
        ...

    @property
    def details(self) -> str | None:
        """Human-readable description."""
        ...


# =============================================================================
# Result Protocols
# =============================================================================


@runtime_checkable
class ICheckResult(Protocol):
    """Protocol for validation check results.

    Contains the results of running data validation.
    """

    @property
    def issues(self) -> list[Any]:
        """List of validation issues found."""
        ...

    @property
    def passed(self) -> bool:
        """Whether validation passed (no issues)."""
        ...

    @property
    def has_critical(self) -> bool:
        """Whether critical issues were found."""
        ...

    @property
    def has_high(self) -> bool:
        """Whether high severity issues were found."""
        ...

    @property
    def row_count(self) -> int:
        """Number of rows validated."""
        ...

    @property
    def column_count(self) -> int:
        """Number of columns."""
        ...

    @property
    def source(self) -> str:
        """Data source name or path."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@runtime_checkable
class ILearnResult(Protocol):
    """Protocol for schema learning results."""

    @property
    def schema(self) -> dict[str, Any]:
        """Learned schema as dictionary."""
        ...

    @property
    def schema_yaml(self) -> str:
        """Schema as YAML string."""
        ...

    @property
    def row_count(self) -> int | None:
        """Number of rows analyzed."""
        ...

    @property
    def column_count(self) -> int:
        """Number of columns."""
        ...

    @property
    def columns(self) -> list[str]:
        """List of column names."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@runtime_checkable
class IColumnProfile(Protocol):
    """Protocol for column-level profiling results."""

    @property
    def name(self) -> str:
        """Column name."""
        ...

    @property
    def physical_type(self) -> str:
        """Physical data type."""
        ...

    @property
    def inferred_type(self) -> str:
        """Inferred logical type."""
        ...

    @property
    def null_count(self) -> int:
        """Number of null values."""
        ...

    @property
    def null_ratio(self) -> float:
        """Ratio of null values."""
        ...

    @property
    def distinct_count(self) -> int:
        """Number of distinct values."""
        ...

    @property
    def unique_ratio(self) -> float:
        """Ratio of unique values."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@runtime_checkable
class IProfileResult(Protocol):
    """Protocol for data profiling results."""

    @property
    def name(self) -> str:
        """Table/source name."""
        ...

    @property
    def source(self) -> str:
        """Data source path or name."""
        ...

    @property
    def row_count(self) -> int:
        """Number of rows."""
        ...

    @property
    def column_count(self) -> int:
        """Number of columns."""
        ...

    @property
    def estimated_memory_bytes(self) -> int:
        """Estimated memory usage."""
        ...

    @property
    def columns(self) -> list[Any]:
        """Column profile results."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@runtime_checkable
class ICompareResult(Protocol):
    """Protocol for drift comparison results."""

    @property
    def baseline_source(self) -> str:
        """Baseline data source."""
        ...

    @property
    def current_source(self) -> str:
        """Current data source."""
        ...

    @property
    def has_drift(self) -> bool:
        """Whether drift was detected."""
        ...

    @property
    def has_high_drift(self) -> bool:
        """Whether high-severity drift was detected."""
        ...

    @property
    def drifted_columns(self) -> list[str]:
        """Columns with detected drift."""
        ...

    @property
    def columns(self) -> list[dict[str, Any]]:
        """Per-column drift results."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@runtime_checkable
class IScanResult(Protocol):
    """Protocol for PII scan results."""

    @property
    def source(self) -> str:
        """Data source name or path."""
        ...

    @property
    def columns_with_pii(self) -> int:
        """Number of columns with PII."""
        ...

    @property
    def total_findings(self) -> int:
        """Total PII findings."""
        ...

    @property
    def has_violations(self) -> bool:
        """Whether regulation violations were found."""
        ...

    @property
    def findings(self) -> list[dict[str, Any]]:
        """PII findings."""
        ...

    @property
    def violations(self) -> list[dict[str, Any]]:
        """Regulation violations."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@runtime_checkable
class IMaskResult(Protocol):
    """Protocol for data masking results."""

    @property
    def source(self) -> str:
        """Original data source."""
        ...

    @property
    def output_path(self) -> str:
        """Path to masked output file."""
        ...

    @property
    def columns_masked(self) -> list[str]:
        """Columns that were masked."""
        ...

    @property
    def strategy(self) -> str:
        """Masking strategy used."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


@runtime_checkable
class IGenerateSuiteResult(Protocol):
    """Protocol for validation suite generation results."""

    @property
    def rules(self) -> list[dict[str, Any]]:
        """Generated validation rules."""
        ...

    @property
    def rule_count(self) -> int:
        """Number of rules generated."""
        ...

    @property
    def yaml_content(self) -> str:
        """Rules as YAML string."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


# =============================================================================
# Main Backend Interface
# =============================================================================


@runtime_checkable
class IDataQualityBackend(Protocol):
    """Protocol for data quality backend implementations.

    This is the main interface that all data quality backends must implement.
    It provides methods for validation, profiling, schema learning, drift
    detection, PII scanning, and data masking.

    Example:
        class TruthoundBackend(IDataQualityBackend):
            async def check(self, data, **kwargs) -> ICheckResult:
                import truthound as th
                result = th.check(data, **kwargs)
                return convert_to_check_result(result)

        class MockBackend(IDataQualityBackend):
            async def check(self, data, **kwargs) -> ICheckResult:
                return MockCheckResult(passed=True, issues=[])
    """

    def is_available(self) -> bool:
        """Check if the backend is available (library installed).

        Returns:
            True if the backend library is installed and working.
        """
        ...

    async def check(
        self,
        data: DataInput,
        *,
        validators: list[str] | None = None,
        validator_config: dict[str, dict[str, Any]] | None = None,
        schema: str | None = None,
        auto_schema: bool = False,
        columns: list[str] | None = None,
        min_severity: str | None = None,
        strict: bool = False,
        parallel: bool = False,
        max_workers: int | None = None,
        pushdown: bool | None = None,
    ) -> ICheckResult:
        """Run data validation.

        Args:
            data: File path or DataSource object.
            validators: List of validator names to run.
            validator_config: Per-validator configuration.
            schema: Path to schema YAML file.
            auto_schema: Auto-learn schema for validation.
            columns: Columns to validate.
            min_severity: Minimum severity to report.
            strict: Raise exception on failures.
            parallel: Use parallel execution.
            max_workers: Max threads for parallel.
            pushdown: Enable query pushdown.

        Returns:
            Validation result implementing ICheckResult.
        """
        ...

    async def learn(
        self,
        source: DataInput,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> ILearnResult:
        """Learn schema from data.

        Args:
            source: File path or DataSource object.
            infer_constraints: Infer constraints from statistics.
            categorical_threshold: Max unique values for categorical.
            sample_size: Number of rows to sample.

        Returns:
            Schema result implementing ILearnResult.
        """
        ...

    async def profile(
        self,
        source: DataInput,
        *,
        sample_size: int | None = None,
        include_patterns: bool = True,
        include_correlations: bool = False,
        include_distributions: bool = True,
        top_n_values: int = 10,
    ) -> IProfileResult:
        """Run data profiling.

        Args:
            source: File path or DataSource object.
            sample_size: Max rows to sample.
            include_patterns: Enable pattern detection.
            include_correlations: Calculate correlations.
            include_distributions: Include distribution stats.
            top_n_values: Top/bottom values per column.

        Returns:
            Profile result implementing IProfileResult.
        """
        ...

    async def compare(
        self,
        baseline: DataInput,
        current: DataInput,
        *,
        columns: list[str] | None = None,
        method: str = "auto",
        threshold: float | None = None,
        correction: str | None = None,
        sample_size: int | None = None,
    ) -> ICompareResult:
        """Compare datasets for drift detection.

        Args:
            baseline: Reference data.
            current: Current data to compare.
            columns: Columns to compare.
            method: Detection method.
            threshold: Drift threshold.
            correction: Multiple testing correction.
            sample_size: Sample size for large datasets.

        Returns:
            Comparison result implementing ICompareResult.
        """
        ...

    async def scan(
        self,
        data: DataInput,
        *,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
        min_confidence: float = 0.8,
    ) -> IScanResult:
        """Scan for PII.

        Args:
            data: File path or DataSource object.
            columns: Columns to scan.
            regulations: Regulations to check.
            min_confidence: Minimum PII confidence.

        Returns:
            Scan result implementing IScanResult.
        """
        ...

    async def mask(
        self,
        data: DataInput,
        output: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
    ) -> IMaskResult:
        """Mask sensitive data.

        Args:
            data: File path or DataSource object.
            output: Output file path.
            columns: Columns to mask.
            strategy: Masking strategy.

        Returns:
            Mask result implementing IMaskResult.
        """
        ...

    async def generate_suite(
        self,
        profile: IProfileResult | dict[str, Any],
        *,
        strictness: str = "medium",
        preset: str = "default",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> IGenerateSuiteResult:
        """Generate validation suite from profile.

        Args:
            profile: Profile result or dictionary.
            strictness: Rule strictness level.
            preset: Rule generation preset.
            include: Rule categories to include.
            exclude: Rule categories to exclude.

        Returns:
            Suite result implementing IGenerateSuiteResult.
        """
        ...
