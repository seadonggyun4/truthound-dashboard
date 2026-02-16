"""Async wrapper for truthound package.

This module provides an async interface to truthound functions,
enabling non-blocking validation operations in the FastAPI application.

The adapter uses ThreadPoolExecutor to run synchronous truthound
functions without blocking the async event loop.

Architecture:
    Dashboard Services
           ↓
    TruthoundAdapter (this module)
           ↓
    truthound library (external)

The adapter is designed for loose coupling with truthound:
- Protocol-based interfaces for type checking
- Graceful fallbacks when truthound versions differ
- All truthound interactions are isolated in this module

Features:
- Async wrappers for all truthound functions (check, learn, profile, compare, scan, mask)
- Support for both file paths and DataSource objects
- Automatic sampling for large datasets (100MB+ files)
- ValidationResult conversion for reporter integration
- Configurable sample size and sampling methods

Example:
    adapter = get_adapter()

    # With file path
    result = await adapter.check("/path/to/data.csv")

    # With DataSource
    from truthound_dashboard.core.datasource_factory import create_datasource
    source = create_datasource({"type": "postgresql", "table": "users", ...})
    result = await adapter.check(source)

    # With auto-sampling for large files
    result = await adapter.check_with_sampling("/path/to/large.csv")

    # Convert to ValidationResult for reporters
    validation_result = result.to_validation_result()
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, Union, runtime_checkable

import yaml

if TYPE_CHECKING:
    from truthound_dashboard.core.datasource_factory import SourceConfig

logger = logging.getLogger(__name__)

# Type alias for data input - can be path string or DataSource object
DataInput = Union[str, Any]


@runtime_checkable
class TruthoundResult(Protocol):
    """Protocol for truthound result objects."""

    @property
    def issues(self) -> list[Any]: ...


@dataclass
class CheckResult:
    """Validation check result.

    This class wraps truthound's Report/ValidationResult and provides
    a consistent interface for the dashboard regardless of truthound version.

    Attributes:
        passed: Whether validation passed (no issues).
        has_critical: Whether critical issues were found.
        has_high: Whether high severity issues were found.
        total_issues: Total number of issues.
        critical_issues: Number of critical issues.
        high_issues: Number of high severity issues.
        medium_issues: Number of medium severity issues.
        low_issues: Number of low severity issues.
        source: Data source path or name.
        row_count: Number of rows validated.
        column_count: Number of columns.
        issues: List of validation issues.
        run_id: Optional run identifier for tracking.
        run_time: Optional timestamp of the validation run.
        _raw_result: Internal reference to the original truthound result.
    """

    passed: bool
    has_critical: bool
    has_high: bool
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    source: str
    row_count: int
    column_count: int
    issues: list[dict[str, Any]]
    run_id: str | None = None
    run_time: Any = None
    _raw_result: Any = None

    # PHASE 1: result_format used
    result_format: str | None = None

    # PHASE 2: report statistics
    statistics: dict[str, Any] | None = None

    # PHASE 4: execution summary
    validator_execution_summary: dict[str, Any] | None = None

    # PHASE 5: exception summary
    exception_summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "passed": self.passed,
            "has_critical": self.has_critical,
            "has_high": self.has_high,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "high_issues": self.high_issues,
            "medium_issues": self.medium_issues,
            "low_issues": self.low_issues,
            "source": self.source,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "issues": self.issues,
        }
        if self.run_id:
            result["run_id"] = self.run_id
        if self.run_time:
            result["run_time"] = (
                self.run_time.isoformat()
                if hasattr(self.run_time, "isoformat")
                else str(self.run_time)
            )
        # PHASE 1
        if self.result_format:
            result["result_format"] = self.result_format
        # PHASE 2
        if self.statistics:
            result["statistics"] = self.statistics
        # PHASE 4
        if self.validator_execution_summary:
            result["validator_execution_summary"] = self.validator_execution_summary
        # PHASE 5
        if self.exception_summary:
            result["exception_summary"] = self.exception_summary
        return result

    def to_validation_result(self) -> Any:
        """Convert to truthound's ValidationResult format for reporters.

        This enables using truthound's reporters directly with this result.

        Returns:
            An object that implements the ValidationResult interface expected
            by truthound reporters, or the raw result if available.
        """
        # If we have the raw truthound result, prefer using it
        if self._raw_result is not None:
            # Check if it's already a ValidationResult
            if hasattr(self._raw_result, "results") and hasattr(
                self._raw_result, "run_id"
            ):
                return self._raw_result
            # It's a Report - try to convert
            return self._create_validation_result_mock()
        return self._create_validation_result_mock()

    def _create_validation_result_mock(self) -> "_ValidationResultMock":
        """Create a mock ValidationResult for reporter compatibility."""
        return _ValidationResultMock(self)


@dataclass
class LearnResult:
    """Schema learning result.

    Attributes:
        schema: Schema as dictionary.
        schema_yaml: Schema as YAML string.
        row_count: Number of rows analyzed.
        column_count: Number of columns.
        columns: List of column names.
    """

    schema: dict[str, Any]
    schema_yaml: str
    row_count: int | None
    column_count: int
    columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema": self.schema,
            "schema_yaml": self.schema_yaml,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": self.columns,
        }


@dataclass
class ColumnProfileResult:
    """Column-level profile result matching truthound's ColumnProfile structure.

    Attributes:
        name: Column name.
        physical_type: Polars data type (string).
        inferred_type: Inferred logical type (e.g., email, phone, integer).
        row_count: Number of rows.
        null_count: Number of null values.
        null_ratio: Ratio of null values (0.0-1.0).
        empty_string_count: Number of empty strings.
        distinct_count: Number of distinct values.
        unique_ratio: Ratio of unique values (0.0-1.0).
        is_unique: Whether all values are unique.
        is_constant: Whether all values are the same.
        distribution: Statistical distribution (for numeric columns).
        top_values: Most frequent values.
        bottom_values: Least frequent values.
        min_length: Minimum string length (for string columns).
        max_length: Maximum string length (for string columns).
        avg_length: Average string length (for string columns).
        detected_patterns: Detected patterns (for string columns).
        min_date: Minimum date (for datetime columns).
        max_date: Maximum date (for datetime columns).
        date_gaps: Number of date gaps (for datetime columns).
        suggested_validators: List of suggested validator names.
        profile_duration_ms: Time taken to profile this column.
    """

    name: str
    physical_type: str
    inferred_type: str = "unknown"
    row_count: int = 0
    null_count: int = 0
    null_ratio: float = 0.0
    empty_string_count: int = 0
    distinct_count: int = 0
    unique_ratio: float = 0.0
    is_unique: bool = False
    is_constant: bool = False
    distribution: dict[str, Any] | None = None
    top_values: list[dict[str, Any]] | None = None
    bottom_values: list[dict[str, Any]] | None = None
    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None
    detected_patterns: list[dict[str, Any]] | None = None
    min_date: str | None = None
    max_date: str | None = None
    date_gaps: int = 0
    suggested_validators: list[str] | None = None
    profile_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "physical_type": self.physical_type,
            "inferred_type": self.inferred_type,
            "row_count": self.row_count,
            "null_count": self.null_count,
            "null_ratio": self.null_ratio,
            "empty_string_count": self.empty_string_count,
            "distinct_count": self.distinct_count,
            "unique_ratio": self.unique_ratio,
            "is_unique": self.is_unique,
            "is_constant": self.is_constant,
            "profile_duration_ms": self.profile_duration_ms,
        }
        if self.distribution:
            result["distribution"] = self.distribution
        if self.top_values:
            result["top_values"] = self.top_values
        if self.bottom_values:
            result["bottom_values"] = self.bottom_values
        if self.min_length is not None:
            result["min_length"] = self.min_length
            result["max_length"] = self.max_length
            result["avg_length"] = self.avg_length
        if self.detected_patterns:
            result["detected_patterns"] = self.detected_patterns
        if self.min_date:
            result["min_date"] = self.min_date
            result["max_date"] = self.max_date
            result["date_gaps"] = self.date_gaps
        if self.suggested_validators:
            result["suggested_validators"] = self.suggested_validators
        return result


@dataclass
class ProfileResult:
    """Data profiling result matching truthound's TableProfile structure.

    Attributes:
        name: Table/source name.
        source: Data source path or name.
        row_count: Number of rows.
        column_count: Number of columns.
        estimated_memory_bytes: Estimated memory usage in bytes.
        columns: List of column profile results.
        duplicate_row_count: Number of duplicate rows.
        duplicate_row_ratio: Ratio of duplicate rows.
        correlations: Column correlation pairs with coefficients.
        profiled_at: Timestamp when profile was created.
        profile_duration_ms: Total profiling duration in milliseconds.
        size_bytes: Data size in bytes (backward compatibility).
    """

    name: str
    source: str
    row_count: int
    column_count: int
    estimated_memory_bytes: int
    columns: list[ColumnProfileResult]
    duplicate_row_count: int = 0
    duplicate_row_ratio: float = 0.0
    correlations: list[tuple[str, str, float]] | None = None
    profiled_at: str | None = None
    profile_duration_ms: float = 0.0
    size_bytes: int = 0  # Backward compatibility

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "source": self.source,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "estimated_memory_bytes": self.estimated_memory_bytes,
            "size_bytes": self.size_bytes or self.estimated_memory_bytes,
            "duplicate_row_count": self.duplicate_row_count,
            "duplicate_row_ratio": self.duplicate_row_ratio,
            "correlations": self.correlations,
            "profiled_at": self.profiled_at,
            "profile_duration_ms": self.profile_duration_ms,
            "columns": [col.to_dict() for col in self.columns],
        }

    def get_column(self, name: str) -> ColumnProfileResult | None:
        """Get column profile by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    @property
    def column_names(self) -> list[str]:
        """Get list of column names."""
        return [col.name for col in self.columns]


@dataclass
class GenerateSuiteResult:
    """Validation suite generation result.

    Result from generating validation rules based on profile data.

    Attributes:
        rules: List of generated validation rules.
        rule_count: Total number of rules generated.
        categories: Categories of rules generated.
        strictness: Strictness level used for generation.
        yaml_content: Generated rules as YAML string.
        json_content: Generated rules as JSON-serializable dict.
    """

    rules: list[dict[str, Any]]
    rule_count: int
    categories: list[str]
    strictness: str
    yaml_content: str
    json_content: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rules": self.rules,
            "rule_count": self.rule_count,
            "categories": self.categories,
            "strictness": self.strictness,
            "yaml_content": self.yaml_content,
            "json_content": self.json_content,
        }


@dataclass
class CompareResult:
    """Drift comparison result.

    Attributes:
        baseline_source: Baseline data source path or name.
        current_source: Current data source path or name.
        baseline_rows: Number of rows in baseline.
        current_rows: Number of rows in current.
        has_drift: Whether drift was detected.
        has_high_drift: Whether high-severity drift was detected.
        total_columns: Total columns compared.
        drifted_columns: List of column names with drift.
        columns: Per-column drift results.
    """

    baseline_source: str
    current_source: str
    baseline_rows: int
    current_rows: int
    has_drift: bool
    has_high_drift: bool
    total_columns: int
    drifted_columns: list[str]
    columns: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_source": self.baseline_source,
            "current_source": self.current_source,
            "baseline_rows": self.baseline_rows,
            "current_rows": self.current_rows,
            "has_drift": self.has_drift,
            "has_high_drift": self.has_high_drift,
            "total_columns": self.total_columns,
            "drifted_columns": self.drifted_columns,
            "columns": self.columns,
        }


@dataclass
class ScanResult:
    """PII scan result.

    Attributes:
        source: Data source path or name.
        row_count: Number of rows scanned.
        column_count: Number of columns.
        total_columns_scanned: Total columns that were scanned.
        columns_with_pii: Number of columns containing PII.
        total_findings: Total number of PII findings.
        has_violations: Whether any regulation violations were found.
        total_violations: Number of regulation violations.
        findings: List of PII finding dictionaries.
        violations: List of regulation violation dictionaries.
    """

    source: str
    row_count: int
    column_count: int
    total_columns_scanned: int
    columns_with_pii: int
    total_findings: int
    has_violations: bool
    total_violations: int
    findings: list[dict[str, Any]]
    violations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "total_columns_scanned": self.total_columns_scanned,
            "columns_with_pii": self.columns_with_pii,
            "total_findings": self.total_findings,
            "has_violations": self.has_violations,
            "total_violations": self.total_violations,
            "findings": self.findings,
            "violations": self.violations,
        }


@dataclass
class MaskResult:
    """Data masking result.

    Attributes:
        source: Original data source path or name.
        output_path: Path to the masked output file.
        row_count: Number of rows in the masked data.
        column_count: Number of columns in the masked data.
        columns_masked: List of columns that were masked.
        strategy: Masking strategy used (redact, hash, fake).
        original_columns: List of all column names.
    """

    source: str
    output_path: str
    row_count: int
    column_count: int
    columns_masked: list[str]
    strategy: str
    original_columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "output_path": self.output_path,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns_masked": self.columns_masked,
            "strategy": self.strategy,
            "original_columns": self.original_columns,
        }


def _get_source_name(data: DataInput) -> str:
    """Get source name from data input.

    Args:
        data: File path string or DataSource object.

    Returns:
        Source name string.
    """
    if isinstance(data, str):
        return data
    # DataSource objects have a name property
    return getattr(data, "name", str(type(data).__name__))


class TruthoundAdapter:
    """Async wrapper for truthound functions.

    This adapter provides an async interface to truthound operations,
    running them in a thread pool to avoid blocking the event loop.

    The adapter supports both file paths and DataSource objects for
    validation, profiling, and other operations.

    Attributes:
        max_workers: Maximum number of worker threads.
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize adapter.

        Args:
            max_workers: Maximum worker threads for concurrent operations.
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._max_workers = max_workers

    async def check(
        self,
        data: DataInput,
        *,
        validators: list[str] | None = None,
        validator_config: dict[str, dict[str, Any]] | None = None,
        schema: str | None = None,
        auto_schema: bool = False,
        min_severity: str | None = None,
        parallel: bool = False,
        max_workers: int | None = None,
        pushdown: bool | None = None,
        # PHASE 1: result format control
        result_format: str | None = None,
        include_unexpected_rows: bool = False,
        max_unexpected_rows: int | None = None,
        # PHASE 5: exception control
        catch_exceptions: bool = True,
        max_retries: int = 3,
    ) -> CheckResult:
        """Run data validation asynchronously.

        This method wraps truthound's th.check() with full parameter support.
        All parameters map directly to th.check() for maximum flexibility.

        Args:
            data: Data source - can be:
                - File path string (CSV, Parquet, JSON, etc.)
                - DataSource object (SQL, Cloud DW, etc.)
            validators: Optional list of validator names to run.
            validator_config: Optional dict of per-validator configuration.
                Format: {"ValidatorName": {"param1": value1, "param2": value2}}
                Example: {"Null": {"columns": ("a", "b"), "mostly": 0.95}}
                Note: In truthound 2.x, columns should be tuples, not lists.
            schema: Optional path to schema YAML file.
            auto_schema: If True, auto-learns schema for validation.
            min_severity: Minimum severity to report ("low", "medium", "high", "critical").
            parallel: If True, uses DAG-based parallel execution.
            max_workers: Max threads for parallel execution.
            pushdown: Enable query pushdown for SQL sources. None uses auto-detection.
            result_format: Result detail level (boolean_only/basic/summary/complete).
            include_unexpected_rows: Include failure rows in SUMMARY+ results.
            max_unexpected_rows: Max failure rows to return.
            catch_exceptions: If True, catch validator errors gracefully.
            max_retries: Max retry attempts for transient errors.

        Returns:
            CheckResult with validation results.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
        """
        import truthound as th

        # Build kwargs dynamically to avoid passing None for optional params
        # Use 'source' parameter for DataSource objects (truthound 2.x API)
        if isinstance(data, str):
            kwargs: dict[str, Any] = {"data": data}
        else:
            kwargs = {"source": data}

        kwargs.update(
            {
                "validators": validators,
                "schema": schema,
                "auto_schema": auto_schema,
                "parallel": parallel,
            }
        )

        # Add per-validator configuration if provided (truthound 2.x uses validator_config)
        if validator_config:
            kwargs["validator_config"] = validator_config

        # Only add optional params if explicitly set
        if min_severity is not None:
            kwargs["min_severity"] = min_severity
        if max_workers is not None:
            kwargs["max_workers"] = max_workers
        if pushdown is not None:
            kwargs["pushdown"] = pushdown

        # PHASE 1: result_format
        if result_format is not None:
            if include_unexpected_rows or max_unexpected_rows is not None:
                try:
                    from truthound.types import ResultFormat, ResultFormatConfig
                    rf_config = ResultFormatConfig(
                        format=ResultFormat(result_format),
                        include_unexpected_rows=include_unexpected_rows,
                        max_unexpected_rows=max_unexpected_rows or 1000,
                    )
                    kwargs["result_format"] = rf_config
                except ImportError:
                    kwargs["result_format"] = result_format
            else:
                kwargs["result_format"] = result_format

        # PHASE 5: exception control
        if not catch_exceptions:
            kwargs["catch_exceptions"] = False
        if max_retries != 3:
            kwargs["max_retries"] = max_retries

        func = partial(th.check, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_check_result(result)

    async def learn(
        self,
        source: DataInput,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> LearnResult:
        """Learn schema from data asynchronously.

        Uses truthound's th.learn() to analyze data and generate schema.
        If sample_size is provided, delegates to learn_with_sampling() which
        handles dashboard-level sampling before calling th.learn().

        Note: th.learn() only supports (data, infer_constraints, categorical_threshold).
        sample_size is handled at dashboard level, not passed to truthound.

        Args:
            source: Data source - can be:
                - File path string
                - DataSource object
            infer_constraints: If True, infers constraints (min/max, allowed values)
                from data statistics.
            categorical_threshold: Maximum unique values for categorical detection.
                Columns with unique values <= threshold are treated as categorical
                and will have allowed_values inferred. If None, uses truthound
                default (20).
            sample_size: Sample size for large datasets. Handled at dashboard level
                by pre-sampling data before passing to th.learn().

        Returns:
            LearnResult with schema information.
        """
        if sample_size is not None:
            return await self.learn_with_sampling(
                source,
                infer_constraints=infer_constraints,
                categorical_threshold=categorical_threshold,
                sample_size=sample_size,
            )

        import truthound as th

        # Build kwargs dynamically to let truthound use its defaults when not specified
        kwargs: dict[str, Any] = {"infer_constraints": infer_constraints}

        if categorical_threshold is not None:
            kwargs["categorical_threshold"] = categorical_threshold

        func = partial(th.learn, source, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_learn_result(result)

    async def profile(
        self,
        source: DataInput,
    ) -> ProfileResult:
        """Run data profiling asynchronously.

        Note: truthound's th.profile() only accepts (data, source) parameters.
        Advanced configuration options are NOT supported by the underlying library.

        Args:
            source: Data source - can be:
                - File path string
                - DataSource object

        Returns:
            ProfileResult with profiling information.
        """
        import truthound as th

        func = partial(th.profile, source)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)
        return self._convert_profile_result(result)

    async def profile_advanced(
        self,
        source: DataInput,
        *,
        config: dict[str, Any] | None = None,
    ) -> ProfileResult:
        """Run advanced data profiling with full ProfilerConfig support.

        This method provides direct access to all ProfilerConfig options
        through a configuration dictionary.

        Note: DataProfiler.profile() only accepts LazyFrame, so file paths
        are converted to LazyFrame first. For simple profiling without
        advanced config, use profile() method instead.

        Args:
            source: Data source - file path string or DataSource object.
            config: ProfilerConfig options as dictionary. Supported keys:
                - sample_size: int | None (max rows to sample)
                - random_seed: int (default 42)
                - include_patterns: bool (default True)
                - include_correlations: bool (default False)
                - include_distributions: bool (default True)
                - top_n_values: int (default 10)
                - pattern_sample_size: int (default 1000)
                - correlation_threshold: float (default 0.7)
                - min_pattern_match_ratio: float (default 0.8)
                - n_jobs: int (default 1)

        Returns:
            ProfileResult with comprehensive profiling information.

        Raises:
            ImportError: If truthound.profiler module is not available.
        """
        import polars as pl

        from truthound.profiler import DataProfiler, ProfilerConfig

        config = config or {}

        profiler_config = ProfilerConfig(
            sample_size=config.get("sample_size"),
            random_seed=config.get("random_seed", 42),
            include_patterns=config.get("include_patterns", True),
            include_correlations=config.get("include_correlations", False),
            include_distributions=config.get("include_distributions", True),
            top_n_values=config.get("top_n_values", 10),
            pattern_sample_size=config.get("pattern_sample_size", 1000),
            correlation_threshold=config.get("correlation_threshold", 0.7),
            min_pattern_match_ratio=config.get("min_pattern_match_ratio", 0.8),
            n_jobs=config.get("n_jobs", 1),
        )

        profiler = DataProfiler(config=profiler_config)

        # DataProfiler.profile() only accepts LazyFrame
        # Convert file path to LazyFrame
        if isinstance(source, str):
            # Determine file format and create LazyFrame
            source_lower = source.lower()
            if source_lower.endswith(".csv"):
                lf = pl.scan_csv(source)
            elif source_lower.endswith(".parquet"):
                lf = pl.scan_parquet(source)
            elif source_lower.endswith((".json", ".ndjson", ".jsonl")):
                lf = pl.scan_ndjson(source)
            else:
                # Fallback to th.profile() for unsupported formats
                import truthound as th

                func = partial(th.profile, source)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self._executor, func)
                return self._convert_profile_result(result)

            func = partial(profiler.profile, lf, name=source, source=source)
        elif hasattr(source, "lazy"):
            # DataFrame with .lazy() method
            func = partial(profiler.profile, source.lazy())
        elif hasattr(source, "collect"):
            # Already a LazyFrame
            func = partial(profiler.profile, source)
        else:
            # Fallback to th.profile() for other types
            import truthound as th

            func = partial(th.profile, source)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, func)
            return self._convert_profile_result(result)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)
        return self._convert_profile_result(result)

    async def generate_suite(
        self,
        profile: ProfileResult | dict[str, Any],
        *,
        strictness: str = "medium",
        preset: str = "default",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        output_format: str = "yaml",
    ) -> GenerateSuiteResult:
        """Generate validation suite from profile.

        Uses truthound's generate_suite() to automatically create validation
        rules based on profiled data characteristics.

        Args:
            profile: Profile result from profile() or profile_advanced(),
                or a dictionary representation of a profile.
            strictness: Strictness level for rule generation:
                - "loose": Permissive thresholds, fewer rules
                - "medium": Balanced defaults (default)
                - "strict": Tight thresholds, comprehensive rules
            preset: Configuration preset for rule generation:
                - "default": General purpose
                - "strict": Production data
                - "loose": Development/testing
                - "minimal": Essential rules only
                - "comprehensive": All available rules
                - "ci_cd": Optimized for CI/CD pipelines
                - "schema_only": Structure validation only
                - "format_only": Format/pattern rules only
            include: List of rule categories to include (None = all).
                Categories: schema, stats, pattern, completeness, uniqueness, distribution
            exclude: List of rule categories to exclude.
            output_format: Output format ("yaml", "json", "python").

        Returns:
            GenerateSuiteResult with generated rules.

        Raises:
            ImportError: If truthound.profiler module is not available.
        """
        from truthound.profiler import generate_suite
        from truthound.profiler.generators import Strictness

        # Convert strictness string to enum
        strictness_map = {
            "loose": Strictness.LOOSE,
            "medium": Strictness.MEDIUM,
            "strict": Strictness.STRICT,
        }
        strictness_enum = strictness_map.get(strictness.lower(), Strictness.MEDIUM)

        # Convert ProfileResult to dict if needed
        if isinstance(profile, ProfileResult):
            profile_data = profile.to_dict()
        else:
            profile_data = profile

        # Build kwargs
        kwargs: dict[str, Any] = {
            "strictness": strictness_enum,
            "preset": preset,
        }
        if include:
            kwargs["include"] = include
        if exclude:
            kwargs["exclude"] = exclude

        # Generate suite in thread pool
        def _generate():
            return generate_suite(profile_data, **kwargs)

        loop = asyncio.get_event_loop()
        suite = await loop.run_in_executor(self._executor, _generate)

        return self._convert_suite_result(suite, strictness, output_format)

    async def generate_suite_from_source(
        self,
        source: DataInput,
        *,
        strictness: str = "medium",
        preset: str = "default",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        sample_size: int | None = None,
        include_patterns: bool = True,
    ) -> GenerateSuiteResult:
        """Profile a source and generate validation suite in one step.

        Convenience method that combines profile() and generate_suite().

        Args:
            source: Data source - file path string or DataSource object.
            strictness: Strictness level ("loose", "medium", "strict").
            preset: Rule generation preset.
            include: Rule categories to include.
            exclude: Rule categories to exclude.
            sample_size: Number of rows to sample for profiling.
            include_patterns: Enable pattern detection during profiling.

        Returns:
            GenerateSuiteResult with generated rules.
        """
        # Profile the source first
        profile = await self.profile(
            source,
            sample_size=sample_size,
            include_patterns=include_patterns,
        )

        # Generate suite from profile
        return await self.generate_suite(
            profile,
            strictness=strictness,
            preset=preset,
            include=include,
            exclude=exclude,
        )

    def _convert_suite_result(
        self,
        suite: Any,
        strictness: str,
        output_format: str,
    ) -> GenerateSuiteResult:
        """Convert truthound ValidationSuite to GenerateSuiteResult.

        Args:
            suite: ValidationSuite from generate_suite().
            strictness: Strictness level used.
            output_format: Requested output format.

        Returns:
            GenerateSuiteResult.
        """
        # Extract rules from suite
        rules = []
        categories = set()

        if hasattr(suite, "rules"):
            for rule in suite.rules:
                rule_dict = {
                    "name": getattr(rule, "name", ""),
                    "validator": getattr(rule, "validator", ""),
                    "column": getattr(rule, "column", None),
                    "params": getattr(rule, "params", {}),
                    "severity": getattr(rule, "severity", "medium"),
                    "category": getattr(rule, "category", "unknown"),
                }
                rules.append(rule_dict)
                if rule_dict["category"]:
                    categories.add(rule_dict["category"])

        # Generate YAML content
        yaml_content = ""
        if hasattr(suite, "to_yaml"):
            yaml_content = suite.to_yaml()
        else:
            yaml_content = yaml.dump(
                {"rules": rules},
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        # Generate JSON content
        json_content = {"rules": rules}
        if hasattr(suite, "to_dict"):
            json_content = suite.to_dict()

        return GenerateSuiteResult(
            rules=rules,
            rule_count=len(rules),
            categories=sorted(categories),
            strictness=strictness,
            yaml_content=yaml_content,
            json_content=json_content,
        )

    async def scan(self, data: DataInput) -> ScanResult:
        """Run PII scan on data asynchronously.

        Uses truthound's th.scan() to detect personally identifiable information.

        Note: truthound's th.scan() does not support any configuration parameters.
        The scan runs on all columns with default settings.

        Args:
            data: Data source - can be:
                - File path string (CSV, Parquet, etc.)
                - DataSource object

        Returns:
            ScanResult with PII findings.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
        """
        import truthound as th

        func = partial(th.scan, data)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_scan_result(result)

    async def compare(
        self,
        baseline: DataInput,
        current: DataInput,
        *,
        columns: list[str] | None = None,
        method: str = "auto",
        threshold: float | None = None,
        sample_size: int | None = None,
    ) -> CompareResult:
        """Compare two datasets for drift detection.

        Args:
            baseline: Reference data - can be path string or DataSource.
            current: Current data to compare - can be path string or DataSource.
            columns: Optional list of columns to compare. If None, all common columns.
            method: Detection method. Supported methods:
                - "auto": Smart selection (numeric → PSI, categorical → chi2)
                - "ks": Kolmogorov-Smirnov test (continuous distributions)
                - "psi": Population Stability Index (industry standard)
                - "chi2": Chi-Square test (categorical data)
                - "js": Jensen-Shannon divergence (symmetric, bounded)
                - "kl": Kullback-Leibler divergence (information loss)
                - "wasserstein": Earth Mover's Distance (distribution transport)
                - "cvm": Cramér-von Mises (sensitive to tails)
                - "anderson": Anderson-Darling (tail-weighted)
            threshold: Optional custom threshold for drift detection.
                Defaults vary by method: KS/chi2/cvm/anderson=0.05, PSI/JS/KL/wasserstein=0.1
            sample_size: Optional sample size for large datasets.

        Returns:
            CompareResult with drift detection results.
        """
        import truthound as th

        kwargs: dict[str, Any] = {
            "columns": columns,
            "method": method,
        }

        if threshold is not None:
            kwargs["threshold"] = threshold
        if sample_size is not None:
            kwargs["sample_size"] = sample_size

        func = partial(th.compare, baseline, current, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_compare_result(result)

    async def mask(
        self,
        data: DataInput,
        output: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
    ) -> MaskResult:
        """Mask sensitive data in a file asynchronously.

        Uses truthound's th.mask() to mask PII and sensitive data with
        three strategies: redact, hash, and fake.

        Args:
            data: Data source - can be:
                - File path string (CSV, Parquet, etc.)
                - DataSource object
            output: Output file path for the masked data.
            columns: Optional list of columns to mask. If None, auto-detects PII.
            strategy: Masking strategy:
                - "redact": Replace values with asterisks (default)
                - "hash": Replace values with SHA256 hash
                - "fake": Replace values with realistic fake data

        Returns:
            MaskResult with masking operation details.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
            ValueError: If invalid strategy is provided.
        """
        import truthound as th

        # Validate strategy
        if strategy not in ("redact", "hash", "fake"):
            raise ValueError(
                f"Invalid strategy: {strategy}. Use 'redact', 'hash', or 'fake'."
            )

        # Build kwargs dynamically
        kwargs: dict[str, Any] = {
            "strategy": strategy,
        }

        if columns is not None:
            kwargs["columns"] = columns

        func = partial(th.mask, data, **kwargs)

        loop = asyncio.get_event_loop()
        masked_df = await loop.run_in_executor(self._executor, func)

        return self._convert_mask_result(data, output, masked_df, strategy, columns)

    async def check_with_sampling(
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
        sample_size: int | None = None,
        sampling_method: str | None = None,
    ) -> CheckResult:
        """Run data validation with automatic sampling for large datasets.

        This method automatically samples large files (>100MB by default)
        before running validation, which significantly improves performance
        while maintaining validation accuracy for most use cases.

        Note: Sampling is only applied to file-based sources. DataSource
        objects handle their own data fetching and should use query-level
        sampling if needed.

        Args:
            data: Data source - can be file path or DataSource.
            validators: Optional list of validator names to run.
            validator_config: Optional dict of per-validator configuration.
            schema: Optional path to schema YAML file.
            auto_schema: If True, auto-learns schema for validation.
            columns: Columns to validate. If None, validates all columns.
            min_severity: Minimum severity to report.
            strict: If True, raises exception on validation failures.
            parallel: If True, uses parallel execution.
            max_workers: Max threads for parallel execution.
            pushdown: Enable query pushdown for SQL sources.
            sample_size: Number of rows to sample. Uses config default if not specified.
            sampling_method: Sampling method ("random", "head", "stratified").

        Returns:
            CheckResult with validation results.

        Note:
            The result.row_count reflects the sampled row count when sampling
            was performed. Check the sampling metadata for original row count.
        """
        # Only apply sampling to file paths
        if isinstance(data, str):
            from truthound_dashboard.core.sampling import SamplingMethod, get_sampler

            sampler = get_sampler()

            # Check if sampling is needed and perform if so
            path = Path(data)
            if path.exists() and sampler.needs_sampling(path):
                # Determine sampling method
                method = None
                if sampling_method:
                    try:
                        method = SamplingMethod(sampling_method)
                    except ValueError:
                        logger.warning(f"Unknown sampling method: {sampling_method}")

                # Perform sampling
                sample_result = await sampler.auto_sample(
                    path,
                    n=sample_size,
                    method=method,
                )

                if sample_result.was_sampled:
                    logger.info(
                        f"Sampled {sample_result.sampled_rows} rows from "
                        f"{sample_result.original_rows} ({sample_result.size_reduction_pct:.1f}% reduction)"
                    )
                    data = sample_result.sampled_path

        # Run validation on (possibly sampled) data
        return await self.check(
            data,
            validators=validators,
            validator_config=validator_config,
            schema=schema,
            auto_schema=auto_schema,
            columns=columns,
            min_severity=min_severity,
            strict=strict,
            parallel=parallel,
            max_workers=max_workers,
            pushdown=pushdown,
        )

    async def learn_with_sampling(
        self,
        source: DataInput,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> LearnResult:
        """Learn schema from data with automatic sampling for large datasets.

        This method first applies dashboard-level sampling for very large files,
        then passes the sample_size to th.learn() if specified.

        Note: Sampling is only applied to file-based sources.

        Args:
            source: Data source - can be file path or DataSource.
            infer_constraints: If True, infer constraints from statistics.
            categorical_threshold: Maximum unique values for categorical detection.
            sample_size: Number of rows to sample. Used both for dashboard sampling
                and passed to th.learn() for internal sampling.

        Returns:
            LearnResult with schema information.
        """
        # Only apply sampling to file paths
        if isinstance(source, str):
            from truthound_dashboard.core.sampling import get_sampler

            sampler = get_sampler()

            path = Path(source)
            if path.exists() and sampler.needs_sampling(path):
                sample_result = await sampler.auto_sample(path, n=sample_size)
                if sample_result.was_sampled:
                    logger.info(
                        f"Sampled {sample_result.sampled_rows} rows for schema learning"
                    )
                    source = sample_result.sampled_path

        # sample_size already handled by dashboard-level sampling above,
        # do NOT pass it to self.learn() — th.learn() doesn't support it
        return await self.learn(
            source,
            infer_constraints=infer_constraints,
            categorical_threshold=categorical_threshold,
        )

    async def profile_with_sampling(
        self,
        source: DataInput,
        *,
        sample_size: int | None = None,
        include_patterns: bool = True,
        include_correlations: bool = False,
    ) -> ProfileResult:
        """Run data profiling with automatic sampling for large datasets.

        Note: Sampling is only applied to file-based sources.

        Args:
            source: Data source - can be file path or DataSource.
            sample_size: Number of rows to sample. Uses config default if not specified.
            include_patterns: Enable pattern detection. Default True.
            include_correlations: Calculate correlations. Default False.

        Returns:
            ProfileResult with profiling information.
        """
        # Only apply sampling to file paths
        if isinstance(source, str):
            from truthound_dashboard.core.sampling import get_sampler

            sampler = get_sampler()

            path = Path(source)
            if path.exists() and sampler.needs_sampling(path):
                sample_result = await sampler.auto_sample(path, n=sample_size)
                if sample_result.was_sampled:
                    logger.info(
                        f"Sampled {sample_result.sampled_rows} rows for profiling"
                    )
                    source = sample_result.sampled_path

        return await self.profile(
            source,
            sample_size=sample_size,
            include_patterns=include_patterns,
            include_correlations=include_correlations,
        )

    async def check_from_config(
        self,
        source_config: "SourceConfig | dict[str, Any]",
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
    ) -> CheckResult:
        """Run validation using source configuration.

        This convenience method creates a DataSource from config
        and runs validation.

        Args:
            source_config: Source configuration (SourceConfig or dict).
            validators: Optional list of validator names to run.
            validator_config: Optional dict of per-validator configuration.
            schema: Optional path to schema YAML file.
            auto_schema: If True, auto-learns schema for validation.
            columns: Columns to validate.
            min_severity: Minimum severity to report.
            strict: If True, raises exception on validation failures.
            parallel: If True, uses parallel execution.
            max_workers: Max threads for parallel execution.
            pushdown: Enable query pushdown for SQL sources.

        Returns:
            CheckResult with validation results.
        """
        from truthound_dashboard.core.datasource_factory import (
            SourceConfig,
            SourceType,
            create_datasource,
        )

        if isinstance(source_config, dict):
            config = SourceConfig.from_dict(source_config)
        else:
            config = source_config

        # For file sources, use path directly
        if SourceType.is_file_type(config.source_type) and config.path:
            data: DataInput = config.path
        else:
            data = create_datasource(config)

        return await self.check(
            data,
            validators=validators,
            validator_config=validator_config,
            schema=schema,
            auto_schema=auto_schema,
            columns=columns,
            min_severity=min_severity,
            strict=strict,
            parallel=parallel,
            max_workers=max_workers,
            pushdown=pushdown,
        )

    def _convert_check_result(self, result: Any) -> CheckResult:
        """Convert truthound Report to CheckResult.

        Supports truthound 1.3.0+ with PHASE 1-5 features.
        Uses TruthoundResultConverter for the heavy lifting, then
        constructs CheckResult with structured data.
        """
        from datetime import datetime
        from .converters.truthound import TruthoundResultConverter

        # Use the centralized converter for full PHASE 1-5 extraction
        converted = TruthoundResultConverter.convert_check_result(result)

        # Extract run_id and run_time if available (truthound 2.x)
        run_id = getattr(result, "run_id", None)
        run_time = getattr(result, "run_time", None)
        if run_time is None:
            run_time = datetime.now()

        return CheckResult(
            passed=converted["passed"],
            has_critical=converted["has_critical"],
            has_high=converted["has_high"],
            total_issues=converted["total_issues"],
            critical_issues=converted["critical_issues"],
            high_issues=converted["high_issues"],
            medium_issues=converted["medium_issues"],
            low_issues=converted["low_issues"],
            source=converted["source"],
            row_count=converted["row_count"],
            column_count=converted["column_count"],
            issues=converted["issues"],
            run_id=run_id,
            run_time=run_time,
            _raw_result=result,
            # PHASE 1
            result_format=converted.get("result_format"),
            # PHASE 2
            statistics=converted.get("statistics"),
            # PHASE 5
            exception_summary=converted.get("exception_summary"),
        )

    def _convert_learn_result(self, result: Any) -> LearnResult:
        """Convert truthound Schema to LearnResult.

        The truthound Schema contains:
        - columns: dict[str, ColumnSchema]
        - row_count: int | None
        - version: str
        - to_dict(): Convert to dictionary
        """
        schema_dict = result.to_dict()
        schema_yaml = yaml.dump(
            schema_dict,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        return LearnResult(
            schema=schema_dict,
            schema_yaml=schema_yaml,
            row_count=result.row_count,
            column_count=len(result.columns),
            columns=list(result.columns.keys()),
        )

    def _convert_profile_result(self, result: Any) -> ProfileResult:
        """Convert truthound TableProfile/ProfileReport to ProfileResult.

        The truthound TableProfile (new API) contains:
        - name: str
        - row_count: int
        - column_count: int
        - estimated_memory_bytes: int
        - columns: tuple[ColumnProfile, ...]
        - duplicate_row_count: int
        - duplicate_row_ratio: float
        - correlations: tuple[tuple[str, str, float], ...]
        - source: str
        - profiled_at: datetime
        - profile_duration_ms: float

        Each ColumnProfile contains:
        - name: str
        - physical_type: str
        - inferred_type: DataType enum
        - row_count, null_count, null_ratio, empty_string_count
        - distinct_count, unique_ratio, is_unique, is_constant
        - distribution: DistributionStats | None
        - top_values, bottom_values: tuple[ValueFrequency, ...]
        - min_length, max_length, avg_length (string columns)
        - detected_patterns: tuple[PatternMatch, ...]
        - min_date, max_date, date_gaps (datetime columns)
        - suggested_validators: tuple[str, ...]
        - profile_duration_ms: float

        Also supports legacy ProfileReport format for backward compatibility.
        """
        # Check if this is the new TableProfile or legacy ProfileReport
        if hasattr(result, "estimated_memory_bytes"):
            # New TableProfile format
            return self._convert_table_profile(result)
        else:
            # Legacy ProfileReport format - convert to new structure
            return self._convert_legacy_profile(result)

    def _convert_table_profile(self, result: Any) -> ProfileResult:
        """Convert new truthound TableProfile to ProfileResult."""
        from datetime import datetime

        columns = []
        for col in result.columns:
            # Extract distribution stats if present
            distribution = None
            if col.distribution:
                distribution = {
                    "mean": getattr(col.distribution, "mean", None),
                    "std": getattr(col.distribution, "std", None),
                    "min": getattr(col.distribution, "min", None),
                    "max": getattr(col.distribution, "max", None),
                    "median": getattr(col.distribution, "median", None),
                    "q1": getattr(col.distribution, "q1", None),
                    "q3": getattr(col.distribution, "q3", None),
                    "skewness": getattr(col.distribution, "skewness", None),
                    "kurtosis": getattr(col.distribution, "kurtosis", None),
                }

            # Convert top_values
            top_values = None
            if col.top_values:
                top_values = [
                    {
                        "value": str(v.value) if v.value is not None else None,
                        "count": v.count,
                        "ratio": v.ratio,
                    }
                    for v in col.top_values
                ]

            # Convert bottom_values
            bottom_values = None
            if col.bottom_values:
                bottom_values = [
                    {
                        "value": str(v.value) if v.value is not None else None,
                        "count": v.count,
                        "ratio": v.ratio,
                    }
                    for v in col.bottom_values
                ]

            # Convert detected_patterns
            detected_patterns = None
            if col.detected_patterns:
                detected_patterns = [
                    {
                        "pattern": getattr(p, "pattern", None),
                        "regex": getattr(p, "regex", None),
                        "match_ratio": getattr(p, "match_ratio", 0.0),
                        "sample_matches": list(getattr(p, "sample_matches", [])),
                    }
                    for p in col.detected_patterns
                ]

            # Get inferred type value
            inferred_type = "unknown"
            if hasattr(col, "inferred_type"):
                inferred_type = (
                    col.inferred_type.value
                    if hasattr(col.inferred_type, "value")
                    else str(col.inferred_type)
                )

            # Convert datetime fields to ISO strings
            min_date = None
            max_date = None
            if col.min_date:
                min_date = (
                    col.min_date.isoformat()
                    if isinstance(col.min_date, datetime)
                    else str(col.min_date)
                )
            if col.max_date:
                max_date = (
                    col.max_date.isoformat()
                    if isinstance(col.max_date, datetime)
                    else str(col.max_date)
                )

            col_result = ColumnProfileResult(
                name=col.name,
                physical_type=col.physical_type,
                inferred_type=inferred_type,
                row_count=col.row_count,
                null_count=col.null_count,
                null_ratio=col.null_ratio,
                empty_string_count=col.empty_string_count,
                distinct_count=col.distinct_count,
                unique_ratio=col.unique_ratio,
                is_unique=col.is_unique,
                is_constant=col.is_constant,
                distribution=distribution,
                top_values=top_values,
                bottom_values=bottom_values,
                min_length=col.min_length,
                max_length=col.max_length,
                avg_length=col.avg_length,
                detected_patterns=detected_patterns,
                min_date=min_date,
                max_date=max_date,
                date_gaps=col.date_gaps,
                suggested_validators=list(col.suggested_validators)
                if col.suggested_validators
                else None,
                profile_duration_ms=col.profile_duration_ms,
            )
            columns.append(col_result)

        # Convert correlations
        correlations = None
        if result.correlations:
            correlations = [
                (c[0], c[1], c[2]) for c in result.correlations
            ]

        # Get profiled_at as ISO string
        profiled_at = None
        if hasattr(result, "profiled_at") and result.profiled_at:
            profiled_at = (
                result.profiled_at.isoformat()
                if isinstance(result.profiled_at, datetime)
                else str(result.profiled_at)
            )

        return ProfileResult(
            name=getattr(result, "name", ""),
            source=getattr(result, "source", ""),
            row_count=result.row_count,
            column_count=result.column_count,
            estimated_memory_bytes=result.estimated_memory_bytes,
            columns=columns,
            duplicate_row_count=result.duplicate_row_count,
            duplicate_row_ratio=result.duplicate_row_ratio,
            correlations=correlations,
            profiled_at=profiled_at,
            profile_duration_ms=getattr(result, "profile_duration_ms", 0.0),
            size_bytes=result.estimated_memory_bytes,
        )

    def _convert_legacy_profile(self, result: Any) -> ProfileResult:
        """Convert legacy truthound ProfileReport to ProfileResult.

        Legacy ProfileReport contains:
        - source: str
        - row_count: int
        - column_count: int
        - size_bytes: int
        - columns: list[dict] with name, dtype, null_pct, unique_pct, min, max, mean, std
        """
        columns = []
        for col in result.columns:
            # Parse null_pct and unique_pct
            null_ratio = 0.0
            unique_ratio = 0.0
            if isinstance(col.get("null_pct"), str):
                null_ratio = float(col["null_pct"].rstrip("%")) / 100.0
            elif isinstance(col.get("null_pct"), (int, float)):
                null_ratio = float(col["null_pct"])
            if isinstance(col.get("unique_pct"), str):
                unique_ratio = float(col["unique_pct"].rstrip("%")) / 100.0
            elif isinstance(col.get("unique_pct"), (int, float)):
                unique_ratio = float(col["unique_pct"])

            # Build distribution if numeric stats present
            distribution = None
            if col.get("min") is not None or col.get("mean") is not None:
                distribution = {
                    "min": col.get("min"),
                    "max": col.get("max"),
                    "mean": col.get("mean"),
                    "std": col.get("std"),
                }

            col_result = ColumnProfileResult(
                name=col["name"],
                physical_type=col.get("dtype", "unknown"),
                inferred_type=col.get("dtype", "unknown"),
                row_count=result.row_count,
                null_ratio=null_ratio,
                unique_ratio=unique_ratio,
                distribution=distribution,
            )
            columns.append(col_result)

        return ProfileResult(
            name=getattr(result, "source", ""),
            source=result.source,
            row_count=result.row_count,
            column_count=result.column_count,
            estimated_memory_bytes=getattr(result, "size_bytes", 0),
            columns=columns,
            size_bytes=getattr(result, "size_bytes", 0),
        )

    def _convert_scan_result(self, result: Any) -> ScanResult:
        """Convert truthound PIIReport to ScanResult.

        The truthound PIIReport contains:
        - source: str
        - row_count: int
        - column_count: int
        - findings: list[PIIFinding]
        - has_violations: bool
        - violations: list[RegulationViolation]

        Each PIIFinding has:
        - column: str
        - pii_type: str
        - confidence: float (0-100)
        - sample_count: int
        - sample_values: list[str] (optional)

        Each RegulationViolation has:
        - regulation: str
        - column: str
        - pii_type: str
        - message: str
        - severity: str (optional)

        Args:
            result: truthound PIIReport object.

        Returns:
            ScanResult with PII findings.
        """
        # Convert findings to dictionaries
        findings = []
        columns_with_pii = set()
        for finding in result.findings:
            # Handle both dict and object-style findings
            if isinstance(finding, dict):
                confidence = finding.get("confidence", 0)
                column = finding.get("column", "")
                pii_type = finding.get("pii_type", "unknown")
                sample_count = finding.get("count", finding.get("sample_count", 0))
                sample_values = finding.get("sample_values")
            else:
                confidence = getattr(finding, "confidence", 0)
                column = getattr(finding, "column", "")
                pii_type = getattr(finding, "pii_type", "unknown")
                sample_count = getattr(finding, "sample_count", getattr(finding, "count", 0))
                sample_values = getattr(finding, "sample_values", None)

            columns_with_pii.add(column)
            # Normalize confidence to 0-1 range if it's in 0-100 range
            normalized_confidence = confidence / 100.0 if confidence > 1 else confidence
            findings.append(
                {
                    "column": column,
                    "pii_type": pii_type,
                    "confidence": normalized_confidence,
                    "sample_count": sample_count,
                    "sample_values": sample_values,
                }
            )

        # Convert violations to dictionaries
        violations = []
        for violation in getattr(result, "violations", []):
            violations.append(
                {
                    "regulation": violation.regulation,
                    "column": violation.column,
                    "pii_type": getattr(violation, "pii_type", "unknown"),
                    "message": violation.message,
                    "severity": getattr(violation, "severity", "high"),
                }
            )

        # Get column_count with fallback (not present in some truthound versions)
        column_count = getattr(result, "column_count", len(columns_with_pii) if columns_with_pii else 0)

        return ScanResult(
            source=result.source,
            row_count=result.row_count,
            column_count=column_count,
            total_columns_scanned=column_count,
            columns_with_pii=len(columns_with_pii),
            total_findings=len(findings),
            has_violations=getattr(result, "has_violations", len(violations) > 0),
            total_violations=len(violations),
            findings=findings,
            violations=violations,
        )

    def _convert_compare_result(self, result: Any) -> CompareResult:
        """Convert truthound DriftReport to CompareResult.

        The truthound DriftReport contains:
        - baseline_source: str
        - current_source: str
        - baseline_rows: int
        - current_rows: int
        - columns: list[ColumnDrift]
        - has_drift: bool
        - has_high_drift: bool
        - get_drifted_columns(): list[str]

        Each ColumnDrift has:
        - column: str
        - dtype: str
        - result: DriftResult (drifted, level, method, statistic, p_value)
        - baseline_stats: dict
        - current_stats: dict
        """
        columns = [
            {
                "column": col.column,
                "dtype": col.dtype,
                "drifted": col.result.drifted,
                "level": (
                    col.result.level.value
                    if hasattr(col.result.level, "value")
                    else str(col.result.level)
                ),
                "method": col.result.method,
                "statistic": col.result.statistic,
                "p_value": col.result.p_value,
                "baseline_stats": col.baseline_stats,
                "current_stats": col.current_stats,
            }
            for col in result.columns
        ]

        return CompareResult(
            baseline_source=result.baseline_source,
            current_source=result.current_source,
            baseline_rows=result.baseline_rows,
            current_rows=result.current_rows,
            has_drift=result.has_drift,
            has_high_drift=result.has_high_drift,
            total_columns=len(result.columns),
            drifted_columns=result.get_drifted_columns(),
            columns=columns,
        )

    def _convert_mask_result(
        self,
        source: DataInput,
        output: str,
        masked_df: Any,
        strategy: str,
        columns: list[str] | None,
    ) -> MaskResult:
        """Convert truthound mask result to MaskResult.

        Args:
            source: Original data source (path or DataSource).
            output: Output file path.
            masked_df: Polars DataFrame with masked data.
            strategy: Masking strategy used.
            columns: Columns that were requested to be masked.

        Returns:
            MaskResult with masking details.
        """
        # Get column information from the DataFrame
        all_columns = list(masked_df.columns)
        row_count = len(masked_df)

        # Determine which columns were actually masked
        # If columns was None, truthound auto-detected PII columns
        columns_masked = columns if columns else []

        # Write the masked data to output file
        output_path = Path(output)
        suffix = output_path.suffix.lower()

        if suffix == ".csv":
            masked_df.write_csv(output)
        elif suffix == ".parquet":
            masked_df.write_parquet(output)
        elif suffix == ".json":
            masked_df.write_json(output)
        else:
            # Default to CSV
            masked_df.write_csv(output)

        return MaskResult(
            source=_get_source_name(source),
            output_path=str(output_path.absolute()),
            row_count=row_count,
            column_count=len(all_columns),
            columns_masked=columns_masked,
            strategy=strategy,
            original_columns=all_columns,
        )

    def shutdown(self) -> None:
        """Shutdown the executor."""
        self._executor.shutdown(wait=False)


# =============================================================================
# ValidationResult Mock for Reporter Integration
# =============================================================================


class _ValidationResultMock:
    """Mock object that mimics truthound's ValidationResult interface.

    This enables using truthound reporters with CheckResult objects from
    this adapter, maintaining loose coupling with the truthound library.

    The mock provides compatibility with truthound reporters that expect:
    - ValidationResult from truthound.stores.results (new API)
    - Report from truthound.report (legacy API)
    """

    def __init__(self, check_result: CheckResult) -> None:
        from datetime import datetime

        self._result = check_result
        self._results = [
            _ValidatorResultMock(issue) for issue in check_result.issues
        ]
        self._statistics = _ResultStatisticsMock(check_result)
        self._run_time = check_result.run_time or datetime.now()

    # === ValidationResult interface (new API) ===

    @property
    def run_id(self) -> str:
        return self._result.run_id or f"run-{id(self._result)}"

    @property
    def run_time(self) -> Any:
        return self._run_time

    @property
    def data_asset(self) -> str:
        return self._result.source

    @property
    def status(self) -> "_ResultStatusMock":
        return _ResultStatusMock(self._result.passed)

    @property
    def success(self) -> bool:
        return self._result.passed

    @property
    def results(self) -> list["_ValidatorResultMock"]:
        return self._results

    @property
    def statistics(self) -> "_ResultStatisticsMock":
        return self._statistics

    @property
    def tags(self) -> dict[str, Any]:
        return {}

    # === Report interface (legacy API) ===

    @property
    def source(self) -> str:
        return self._result.source

    @property
    def row_count(self) -> int:
        return self._result.row_count

    @property
    def column_count(self) -> int:
        return self._result.column_count

    @property
    def issues(self) -> list["_ValidatorResultMock"]:
        return self._results

    @property
    def has_issues(self) -> bool:
        return self._result.total_issues > 0

    @property
    def has_critical(self) -> bool:
        return self._result.has_critical

    @property
    def has_high(self) -> bool:
        return self._result.has_high

    @property
    def suite_name(self) -> str:
        return "Truthound Validation"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_time": (
                self._run_time.isoformat()
                if hasattr(self._run_time, "isoformat")
                else str(self._run_time)
            ),
            "data_asset": self.data_asset,
            "status": self.status.value,
            "success": self.success,
            "results": [r.to_dict() for r in self.results],
            "statistics": self._statistics.to_dict(),
        }

    def to_json(self, indent: int | None = 2) -> str:
        import json

        return json.dumps(self.to_dict(), indent=indent, default=str)


class _ResultStatusMock:
    """Mock ResultStatus enum for reporter compatibility."""

    def __init__(self, passed: bool) -> None:
        self._passed = passed

    @property
    def value(self) -> str:
        return "SUCCESS" if self._passed else "FAILURE"

    def __str__(self) -> str:
        return self.value


class _ResultStatisticsMock:
    """Mock ResultStatistics for reporter compatibility."""

    def __init__(self, check_result: CheckResult) -> None:
        self._result = check_result

    @property
    def total_issues(self) -> int:
        return self._result.total_issues

    @property
    def total_rows(self) -> int:
        return self._result.row_count

    @property
    def total_columns(self) -> int:
        return self._result.column_count

    @property
    def critical_count(self) -> int:
        return self._result.critical_issues

    @property
    def high_count(self) -> int:
        return self._result.high_issues

    @property
    def medium_count(self) -> int:
        return self._result.medium_issues

    @property
    def low_count(self) -> int:
        return self._result.low_issues

    @property
    def passed(self) -> bool:
        return self._result.passed

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_issues": self.total_issues,
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "passed": self.passed,
        }


class _ValidatorResultMock:
    """Mock ValidatorResult for reporter compatibility."""

    def __init__(self, issue: dict[str, Any]) -> None:
        self._issue = issue

    @property
    def validator_name(self) -> str:
        return self._issue.get("validator_name") or self._issue.get("issue_type", "")

    @property
    def column(self) -> str | None:
        return self._issue.get("column")

    @property
    def issue_type(self) -> str:
        return self._issue.get("issue_type", "")

    @property
    def severity(self) -> "_SeverityMock":
        return _SeverityMock(self._issue.get("severity", "medium"))

    @property
    def message(self) -> str:
        return self._issue.get("message", "")

    @property
    def count(self) -> int:
        return self._issue.get("count", 0)

    @property
    def success(self) -> bool:
        return False  # All issues are failures

    @property
    def expected(self) -> Any:
        return self._issue.get("expected")

    @property
    def actual(self) -> Any:
        return self._issue.get("actual")

    @property
    def details(self) -> dict[str, Any]:
        return self._issue.get("details") or {}

    @property
    def sample_values(self) -> list[Any]:
        return self._issue.get("sample_values") or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "column": self.column,
            "issue_type": self.issue_type,
            "severity": self.severity.value,
            "message": self.message,
            "count": self.count,
            "success": self.success,
            "expected": self.expected,
            "actual": self.actual,
            "details": self.details,
            "sample_values": self.sample_values,
        }


class _SeverityMock:
    """Mock Severity enum for reporter compatibility."""

    def __init__(self, value: str) -> None:
        self._value = value.lower() if isinstance(value, str) else str(value).lower()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


# =============================================================================
# Singleton Management
# =============================================================================


# Singleton instance
_adapter: TruthoundAdapter | None = None


def get_adapter() -> TruthoundAdapter:
    """Get singleton adapter instance.

    Returns:
        TruthoundAdapter singleton.
    """
    global _adapter
    if _adapter is None:
        from truthound_dashboard.config import get_settings

        settings = get_settings()
        _adapter = TruthoundAdapter(max_workers=settings.max_workers)
    return _adapter


def reset_adapter() -> None:
    """Reset adapter singleton (for testing)."""
    global _adapter
    if _adapter is not None:
        _adapter.shutdown()
        _adapter = None


# =============================================================================
# Schema Evolution API (truthound.profiler.evolution)
# =============================================================================


@dataclass
class SchemaChangeResult:
    """Schema change detection result.

    Represents a single detected change between schema versions.

    Attributes:
        change_type: Type of change (column_added, column_removed, type_changed, etc.)
        column_name: Name of the affected column.
        old_value: Previous value (type, nullable, etc.)
        new_value: New value.
        severity: Change severity (info, warning, critical).
        breaking: Whether this is a breaking change.
        description: Human-readable description.
        migration_hint: Suggestion for handling the change.
    """

    change_type: str
    column_name: str
    old_value: Any
    new_value: Any
    severity: str
    breaking: bool
    description: str
    migration_hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "column_name": self.column_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": self.severity,
            "breaking": self.breaking,
            "description": self.description,
            "migration_hint": self.migration_hint,
        }


@dataclass
class SchemaDetectionResult:
    """Schema evolution detection result.

    Result from comparing two schemas.

    Attributes:
        total_changes: Total number of changes detected.
        breaking_changes: Number of breaking changes.
        compatibility_level: Compatibility assessment (compatible, minor, breaking).
        changes: List of individual changes.
    """

    total_changes: int
    breaking_changes: int
    compatibility_level: str
    changes: list[SchemaChangeResult]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_changes": self.total_changes,
            "breaking_changes": self.breaking_changes,
            "compatibility_level": self.compatibility_level,
            "changes": [c.to_dict() for c in self.changes],
        }


@dataclass
class RenameDetectionResult:
    """Column rename detection result.

    Attributes:
        old_name: Original column name.
        new_name: New column name.
        similarity: Similarity score (0.0-1.0).
        confidence: Confidence level (high, medium, low).
        reasons: Reasons for the rename detection.
    """

    old_name: str
    new_name: str
    similarity: float
    confidence: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "similarity": self.similarity,
            "confidence": self.confidence,
            "reasons": self.reasons,
        }


@dataclass
class RenameDetectionSummary:
    """Summary of rename detection results.

    Attributes:
        confirmed_renames: High-confidence confirmed renames.
        possible_renames: Lower-confidence possible renames.
        unmatched_added: Columns added without rename match.
        unmatched_removed: Columns removed without rename match.
    """

    confirmed_renames: list[RenameDetectionResult]
    possible_renames: list[RenameDetectionResult]
    unmatched_added: list[str]
    unmatched_removed: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "confirmed_renames": [r.to_dict() for r in self.confirmed_renames],
            "possible_renames": [r.to_dict() for r in self.possible_renames],
            "unmatched_added": self.unmatched_added,
            "unmatched_removed": self.unmatched_removed,
        }


@dataclass
class SchemaVersionResult:
    """Schema version information.

    Attributes:
        id: Version identifier (hash or version string).
        version: Version string (e.g., "1.0.0", "20260129.143000").
        schema: Schema dictionary.
        metadata: Optional metadata.
        created_at: Creation timestamp.
        has_breaking_changes: Whether this version has breaking changes from parent.
        changes_from_parent: List of changes from parent version.
    """

    id: str
    version: str
    schema: dict[str, Any]
    metadata: dict[str, Any] | None
    created_at: str | None
    has_breaking_changes: bool = False
    changes_from_parent: list[SchemaChangeResult] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "schema": self.schema,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "has_breaking_changes": self.has_breaking_changes,
            "changes_from_parent": (
                [c.to_dict() for c in self.changes_from_parent]
                if self.changes_from_parent
                else None
            ),
        }


@dataclass
class SchemaDiffResult:
    """Schema diff between two versions.

    Attributes:
        from_version: Source version string.
        to_version: Target version string.
        changes: List of changes.
        text_diff: Human-readable text diff.
    """

    from_version: str
    to_version: str
    changes: list[SchemaChangeResult]
    text_diff: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "changes": [c.to_dict() for c in self.changes],
            "text_diff": self.text_diff,
        }


@dataclass
class SchemaWatcherEvent:
    """Schema watcher change event.

    Attributes:
        source: Source name that changed.
        has_breaking_changes: Whether breaking changes were detected.
        total_changes: Total number of changes.
        changes: List of changes.
        timestamp: Event timestamp.
    """

    source: str
    has_breaking_changes: bool
    total_changes: int
    changes: list[SchemaChangeResult]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "has_breaking_changes": self.has_breaking_changes,
            "total_changes": self.total_changes,
            "changes": [c.to_dict() for c in self.changes],
            "timestamp": self.timestamp,
        }


@dataclass
class BreakingChangeAlert:
    """Breaking change alert with impact analysis.

    Attributes:
        alert_id: Unique alert identifier.
        title: Alert title.
        source: Source name.
        changes: List of breaking changes.
        impact_scope: Impact scope (local, downstream, system).
        affected_consumers: List of affected consumers.
        data_risk_level: Risk level (1-5).
        recommendations: List of recommendations.
        status: Alert status (open, acknowledged, resolved).
        created_at: Creation timestamp.
        acknowledged_at: Acknowledgment timestamp.
        resolved_at: Resolution timestamp.
    """

    alert_id: str
    title: str
    source: str
    changes: list[SchemaChangeResult]
    impact_scope: str
    affected_consumers: list[str]
    data_risk_level: int
    recommendations: list[str]
    status: str
    created_at: str
    acknowledged_at: str | None = None
    resolved_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "source": self.source,
            "changes": [c.to_dict() for c in self.changes],
            "impact_scope": self.impact_scope,
            "affected_consumers": self.affected_consumers,
            "data_risk_level": self.data_risk_level,
            "recommendations": self.recommendations,
            "status": self.status,
            "created_at": self.created_at,
            "acknowledged_at": self.acknowledged_at,
            "resolved_at": self.resolved_at,
        }


class SchemaEvolutionAdapter:
    """Async wrapper for truthound schema evolution functions.

    This adapter provides an async interface to truthound's schema evolution
    module (truthound.profiler.evolution), including:
    - SchemaEvolutionDetector for change detection
    - SchemaHistory for version management
    - SchemaWatcher for continuous monitoring
    - ColumnRenameDetector for rename detection
    - BreakingChangeAlertManager for alert management
    - ImpactAnalyzer for impact analysis

    All operations run in a thread pool to avoid blocking the event loop.
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize adapter.

        Args:
            max_workers: Maximum worker threads for concurrent operations.
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._watchers: dict[str, Any] = {}  # watcher_id -> SchemaWatcher
        self._histories: dict[str, Any] = {}  # history_id -> SchemaHistory
        self._alert_manager: Any = None
        self._impact_analyzer: Any = None

    async def detect_changes(
        self,
        current_schema: dict[str, Any],
        baseline_schema: dict[str, Any],
        *,
        detect_renames: bool = True,
        rename_similarity_threshold: float = 0.8,
    ) -> SchemaDetectionResult:
        """Detect schema changes between two schemas.

        Uses truthound's SchemaEvolutionDetector for comprehensive change
        detection including column additions, removals, type changes, and renames.

        Args:
            current_schema: Current schema dictionary ({"column": "Type"}).
            baseline_schema: Baseline schema dictionary.
            detect_renames: Enable rename detection.
            rename_similarity_threshold: Threshold for considering a rename (0.0-1.0).

        Returns:
            SchemaDetectionResult with all detected changes.
        """
        from truthound.profiler.evolution import SchemaEvolutionDetector

        def _detect():
            detector = SchemaEvolutionDetector(
                detect_renames=detect_renames,
                rename_similarity_threshold=rename_similarity_threshold,
            )
            changes = detector.detect_changes(current_schema, baseline_schema)
            summary = detector.get_change_summary(changes)
            return changes, summary

        loop = asyncio.get_event_loop()
        changes, summary = await loop.run_in_executor(self._executor, _detect)

        return self._convert_detection_result(changes, summary)

    async def detect_renames(
        self,
        added_columns: dict[str, str],
        removed_columns: dict[str, str],
        *,
        similarity_threshold: float = 0.8,
        require_type_match: bool = True,
        allow_compatible_types: bool = True,
        algorithm: str = "composite",
    ) -> RenameDetectionSummary:
        """Detect column renames between added and removed columns.

        Uses truthound's ColumnRenameDetector with configurable similarity
        algorithms for accurate rename detection.

        Args:
            added_columns: Dict of added columns {"name": "Type"}.
            removed_columns: Dict of removed columns {"name": "Type"}.
            similarity_threshold: Threshold for considering a rename (0.0-1.0).
            require_type_match: Require matching types for rename.
            allow_compatible_types: Allow compatible type changes (e.g., Int32->Int64).
            algorithm: Similarity algorithm:
                - "composite": Weighted combination (default)
                - "levenshtein": Edit distance
                - "jaro_winkler": Short strings, prefixes
                - "ngram": Partial matches
                - "token": snake_case/camelCase names

        Returns:
            RenameDetectionSummary with confirmed and possible renames.
        """
        from truthound.profiler.evolution import ColumnRenameDetector

        def _detect():
            detector = ColumnRenameDetector(
                similarity_threshold=similarity_threshold,
                require_type_match=require_type_match,
                allow_compatible_types=allow_compatible_types,
            )
            return detector.detect(
                added_columns=added_columns,
                removed_columns=removed_columns,
            )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, _detect)

        return self._convert_rename_result(result)

    async def create_history(
        self,
        history_id: str,
        storage_path: str,
        *,
        version_strategy: str = "semantic",
        max_versions: int = 100,
        compress: bool = True,
    ) -> str:
        """Create a new schema history storage.

        Uses truthound's SchemaHistory for version management with support
        for semantic, incremental, timestamp, and git versioning strategies.

        Args:
            history_id: Unique identifier for this history instance.
            storage_path: Path for file-based storage.
            version_strategy: Version numbering strategy:
                - "semantic": 1.2.3 format, auto-bumps based on change type
                - "incremental": 1, 2, 3 simple numbers
                - "timestamp": 20260128.143052 time-based
                - "git": a1b2c3d4 git-like hashes
            max_versions: Maximum versions to keep.
            compress: Compress stored files.

        Returns:
            History ID for future operations.
        """
        from truthound.profiler.evolution import SchemaHistory

        def _create():
            return SchemaHistory.create(
                storage_type="file",
                path=storage_path,
                version_strategy=version_strategy,
                max_versions=max_versions,
                compress=compress,
            )

        loop = asyncio.get_event_loop()
        history = await loop.run_in_executor(self._executor, _create)

        self._histories[history_id] = history
        return history_id

    async def save_schema_version(
        self,
        history_id: str,
        schema: dict[str, Any],
        *,
        version: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SchemaVersionResult:
        """Save a schema version to history.

        Args:
            history_id: History instance ID.
            schema: Schema dictionary to save.
            version: Optional explicit version string.
            metadata: Optional metadata (author, message, etc.).

        Returns:
            SchemaVersionResult with version info.

        Raises:
            ValueError: If history_id not found.
        """
        if history_id not in self._histories:
            raise ValueError(f"History '{history_id}' not found")

        history = self._histories[history_id]

        def _save():
            kwargs: dict[str, Any] = {}
            if version:
                kwargs["version"] = version
            if metadata:
                kwargs["metadata"] = metadata
            return history.save(schema, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, _save)

        return self._convert_version_result(result)

    async def get_schema_version(
        self,
        history_id: str,
        version: str,
    ) -> SchemaVersionResult | None:
        """Get a specific schema version.

        Args:
            history_id: History instance ID.
            version: Version string or ID.

        Returns:
            SchemaVersionResult or None if not found.
        """
        if history_id not in self._histories:
            raise ValueError(f"History '{history_id}' not found")

        history = self._histories[history_id]

        def _get():
            try:
                return history.get_by_version(version)
            except Exception:
                return history.get(version)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, _get)

        if result is None:
            return None
        return self._convert_version_result(result)

    async def list_schema_versions(
        self,
        history_id: str,
        *,
        limit: int = 50,
        since: str | None = None,
    ) -> list[SchemaVersionResult]:
        """List schema versions in history.

        Args:
            history_id: History instance ID.
            limit: Maximum versions to return.
            since: Filter versions since this datetime (ISO format).

        Returns:
            List of SchemaVersionResult.
        """
        from datetime import datetime, timedelta

        if history_id not in self._histories:
            raise ValueError(f"History '{history_id}' not found")

        history = self._histories[history_id]

        def _list():
            kwargs: dict[str, Any] = {"limit": limit}
            if since:
                kwargs["since"] = datetime.fromisoformat(since)
            return history.list(**kwargs)

        loop = asyncio.get_event_loop()
        versions = await loop.run_in_executor(self._executor, _list)

        return [self._convert_version_result(v) for v in versions]

    async def get_latest_version(
        self,
        history_id: str,
    ) -> SchemaVersionResult | None:
        """Get the latest schema version.

        Args:
            history_id: History instance ID.

        Returns:
            Latest SchemaVersionResult or None.
        """
        if history_id not in self._histories:
            raise ValueError(f"History '{history_id}' not found")

        history = self._histories[history_id]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor, lambda: history.latest
        )

        if result is None:
            return None
        return self._convert_version_result(result)

    async def diff_versions(
        self,
        history_id: str,
        from_version: str,
        to_version: str | None = None,
    ) -> SchemaDiffResult:
        """Get diff between two schema versions.

        Args:
            history_id: History instance ID.
            from_version: Source version string.
            to_version: Target version string (None = latest).

        Returns:
            SchemaDiffResult with changes and text diff.
        """
        if history_id not in self._histories:
            raise ValueError(f"History '{history_id}' not found")

        history = self._histories[history_id]

        def _diff():
            if to_version:
                return history.diff(from_version, to_version)
            else:
                return history.diff(from_version)

        loop = asyncio.get_event_loop()
        diff = await loop.run_in_executor(self._executor, _diff)

        return self._convert_diff_result(diff, from_version, to_version or "latest")

    async def has_breaking_changes_since(
        self,
        history_id: str,
        version: str,
    ) -> bool:
        """Check if there are breaking changes since a version.

        Args:
            history_id: History instance ID.
            version: Version to check from.

        Returns:
            True if breaking changes exist.
        """
        if history_id not in self._histories:
            raise ValueError(f"History '{history_id}' not found")

        history = self._histories[history_id]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, lambda: history.has_breaking_changes_since(version)
        )

    async def rollback_version(
        self,
        history_id: str,
        to_version: str,
        *,
        reason: str | None = None,
    ) -> SchemaVersionResult:
        """Rollback to a previous version.

        Creates a new version that matches the specified version.

        Args:
            history_id: History instance ID.
            to_version: Version to rollback to.
            reason: Reason for rollback.

        Returns:
            New SchemaVersionResult after rollback.
        """
        if history_id not in self._histories:
            raise ValueError(f"History '{history_id}' not found")

        history = self._histories[history_id]

        def _rollback():
            kwargs: dict[str, Any] = {}
            if reason:
                kwargs["reason"] = reason
            return history.rollback(to_version, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, _rollback)

        return self._convert_version_result(result)

    async def create_watcher(
        self,
        watcher_id: str,
        sources: list[dict[str, Any]],
        *,
        poll_interval: int = 60,
        only_breaking: bool = False,
        enable_history: bool = True,
        history_path: str | None = None,
    ) -> str:
        """Create a new schema watcher.

        Uses truthound's SchemaWatcher for continuous monitoring with
        configurable sources, handlers, and polling.

        Args:
            watcher_id: Unique identifier for this watcher.
            sources: List of source configurations, each with:
                - type: "file", "dict", or "polars"
                - path: For file sources
                - schema: For dict sources
                - name: Source name
            poll_interval: Polling interval in seconds.
            only_breaking: Only alert on breaking changes.
            enable_history: Enable history tracking.
            history_path: Path for history storage.

        Returns:
            Watcher ID for future operations.
        """
        from truthound.profiler.evolution import (
            SchemaWatcher,
            FileSchemaSource,
            DictSchemaSource,
            LoggingEventHandler,
            HistoryEventHandler,
            SchemaHistory,
        )

        def _create():
            watcher = SchemaWatcher()

            # Add sources
            for src in sources:
                src_type = src.get("type", "file")
                if src_type == "file":
                    watcher.add_source(FileSchemaSource(src["path"]))
                elif src_type == "dict":
                    watcher.add_source(
                        DictSchemaSource(src["schema"], src.get("name", "dict"))
                    )

            # Add logging handler
            watcher.add_handler(LoggingEventHandler())

            # Add history handler if enabled
            if enable_history and history_path:
                history = SchemaHistory.create(
                    storage_type="file",
                    path=history_path,
                )
                watcher.add_handler(HistoryEventHandler(history))

            return watcher

        loop = asyncio.get_event_loop()
        watcher = await loop.run_in_executor(self._executor, _create)

        self._watchers[watcher_id] = {
            "watcher": watcher,
            "poll_interval": poll_interval,
            "only_breaking": only_breaking,
            "status": "created",
        }
        return watcher_id

    async def start_watcher(
        self,
        watcher_id: str,
        *,
        daemon: bool = True,
    ) -> None:
        """Start a schema watcher.

        Args:
            watcher_id: Watcher ID to start.
            daemon: Run as daemon thread.

        Raises:
            ValueError: If watcher_id not found.
        """
        if watcher_id not in self._watchers:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        watcher_data = self._watchers[watcher_id]
        watcher = watcher_data["watcher"]
        poll_interval = watcher_data["poll_interval"]

        def _start():
            watcher.start(poll_interval=poll_interval, daemon=daemon)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, _start)

        watcher_data["status"] = "running"

    async def stop_watcher(self, watcher_id: str) -> None:
        """Stop a schema watcher.

        Args:
            watcher_id: Watcher ID to stop.
        """
        if watcher_id not in self._watchers:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        watcher_data = self._watchers[watcher_id]
        watcher = watcher_data["watcher"]

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, watcher.stop)

        watcher_data["status"] = "stopped"

    async def pause_watcher(self, watcher_id: str) -> None:
        """Pause a schema watcher.

        Args:
            watcher_id: Watcher ID to pause.
        """
        if watcher_id not in self._watchers:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        watcher_data = self._watchers[watcher_id]
        watcher = watcher_data["watcher"]

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, watcher.pause)

        watcher_data["status"] = "paused"

    async def resume_watcher(self, watcher_id: str) -> None:
        """Resume a paused schema watcher.

        Args:
            watcher_id: Watcher ID to resume.
        """
        if watcher_id not in self._watchers:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        watcher_data = self._watchers[watcher_id]
        watcher = watcher_data["watcher"]

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, watcher.resume)

        watcher_data["status"] = "running"

    async def check_watcher_now(
        self,
        watcher_id: str,
    ) -> list[SchemaWatcherEvent]:
        """Execute immediate check for a watcher.

        Args:
            watcher_id: Watcher ID to check.

        Returns:
            List of SchemaWatcherEvent for any detected changes.
        """
        if watcher_id not in self._watchers:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        watcher_data = self._watchers[watcher_id]
        watcher = watcher_data["watcher"]

        loop = asyncio.get_event_loop()
        events = await loop.run_in_executor(self._executor, watcher.check_now)

        return [self._convert_watcher_event(e) for e in events]

    async def get_watcher_status(self, watcher_id: str) -> dict[str, Any]:
        """Get watcher status.

        Args:
            watcher_id: Watcher ID.

        Returns:
            Status dictionary with status, poll_interval, only_breaking.
        """
        if watcher_id not in self._watchers:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        watcher_data = self._watchers[watcher_id]
        return {
            "watcher_id": watcher_id,
            "status": watcher_data["status"],
            "poll_interval": watcher_data["poll_interval"],
            "only_breaking": watcher_data["only_breaking"],
        }

    async def delete_watcher(self, watcher_id: str) -> None:
        """Delete a watcher.

        Stops the watcher if running and removes it.

        Args:
            watcher_id: Watcher ID to delete.
        """
        if watcher_id not in self._watchers:
            raise ValueError(f"Watcher '{watcher_id}' not found")

        watcher_data = self._watchers[watcher_id]
        if watcher_data["status"] == "running":
            await self.stop_watcher(watcher_id)

        del self._watchers[watcher_id]

    async def setup_impact_analyzer(
        self,
        consumers: dict[str, list[str]] | None = None,
        queries: dict[str, list[str]] | None = None,
    ) -> None:
        """Setup impact analyzer with consumer mappings.

        Args:
            consumers: Dict of consumer name -> list of sources it depends on.
            queries: Dict of source name -> list of queries using it.
        """
        from truthound.profiler.evolution import ImpactAnalyzer

        def _setup():
            analyzer = ImpactAnalyzer()
            if consumers:
                for consumer, sources in consumers.items():
                    analyzer.register_consumer(consumer, sources)
            if queries:
                for source, query_list in queries.items():
                    for query in query_list:
                        analyzer.register_query(source, query)
            return analyzer

        loop = asyncio.get_event_loop()
        self._impact_analyzer = await loop.run_in_executor(self._executor, _setup)

    async def setup_alert_manager(
        self,
        alert_storage_path: str,
    ) -> None:
        """Setup breaking change alert manager.

        Args:
            alert_storage_path: Path for alert storage.
        """
        from truthound.profiler.evolution import BreakingChangeAlertManager

        def _setup():
            return BreakingChangeAlertManager(
                impact_analyzer=self._impact_analyzer,
                alert_storage_path=alert_storage_path,
            )

        loop = asyncio.get_event_loop()
        self._alert_manager = await loop.run_in_executor(self._executor, _setup)

    async def create_alert(
        self,
        changes: list[dict[str, Any]],
        source: str,
    ) -> BreakingChangeAlert:
        """Create a breaking change alert.

        Args:
            changes: List of change dictionaries from detect_changes.
            source: Source name.

        Returns:
            BreakingChangeAlert with impact analysis.

        Raises:
            ValueError: If alert manager not setup.
        """
        if self._alert_manager is None:
            raise ValueError("Alert manager not setup. Call setup_alert_manager first.")

        def _create():
            return self._alert_manager.create_alert(changes, source=source)

        loop = asyncio.get_event_loop()
        alert = await loop.run_in_executor(self._executor, _create)

        return self._convert_alert_result(alert)

    async def acknowledge_alert(self, alert_id: str) -> None:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge.
        """
        if self._alert_manager is None:
            raise ValueError("Alert manager not setup.")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor, lambda: self._alert_manager.acknowledge_alert(alert_id)
        )

    async def resolve_alert(self, alert_id: str) -> None:
        """Resolve an alert.

        Args:
            alert_id: Alert ID to resolve.
        """
        if self._alert_manager is None:
            raise ValueError("Alert manager not setup.")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor, lambda: self._alert_manager.resolve_alert(alert_id)
        )

    async def get_alert_history(
        self,
        *,
        status: str | None = None,
    ) -> list[BreakingChangeAlert]:
        """Get alert history.

        Args:
            status: Filter by status (open, acknowledged, resolved).

        Returns:
            List of BreakingChangeAlert.
        """
        if self._alert_manager is None:
            raise ValueError("Alert manager not setup.")

        def _get():
            kwargs: dict[str, Any] = {}
            if status:
                kwargs["status"] = status
            return self._alert_manager.get_alert_history(**kwargs)

        loop = asyncio.get_event_loop()
        alerts = await loop.run_in_executor(self._executor, _get)

        return [self._convert_alert_result(a) for a in alerts]

    async def get_alert_stats(self) -> dict[str, int]:
        """Get alert statistics.

        Returns:
            Dict with total, open, acknowledged, resolved counts.
        """
        if self._alert_manager is None:
            raise ValueError("Alert manager not setup.")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._alert_manager.get_stats
        )

    # =========================================================================
    # Result Conversion Methods
    # =========================================================================

    def _convert_detection_result(
        self,
        changes: list[Any],
        summary: Any,
    ) -> SchemaDetectionResult:
        """Convert truthound detection result."""
        converted_changes = []
        for c in changes:
            converted_changes.append(
                SchemaChangeResult(
                    change_type=c.change_type.value if hasattr(c.change_type, "value") else str(c.change_type),
                    column_name=getattr(c, "column", getattr(c, "column_name", "")),
                    old_value=getattr(c, "old_value", None),
                    new_value=getattr(c, "new_value", None),
                    severity=c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                    breaking=getattr(c, "breaking", False),
                    description=getattr(c, "description", ""),
                    migration_hint=getattr(c, "migration_hint", None),
                )
            )

        compatibility = "compatible"
        if hasattr(summary, "compatibility_level"):
            compatibility = (
                summary.compatibility_level.value
                if hasattr(summary.compatibility_level, "value")
                else str(summary.compatibility_level)
            )

        return SchemaDetectionResult(
            total_changes=getattr(summary, "total_changes", len(changes)),
            breaking_changes=getattr(summary, "breaking_changes", 0),
            compatibility_level=compatibility,
            changes=converted_changes,
        )

    def _convert_rename_result(self, result: Any) -> RenameDetectionSummary:
        """Convert truthound rename detection result."""
        confirmed = []
        for r in getattr(result, "confirmed_renames", []):
            confirmed.append(
                RenameDetectionResult(
                    old_name=r.old_name,
                    new_name=r.new_name,
                    similarity=r.similarity,
                    confidence=r.confidence.value if hasattr(r.confidence, "value") else str(r.confidence),
                    reasons=list(getattr(r, "reasons", [])),
                )
            )

        possible = []
        for r in getattr(result, "possible_renames", []):
            possible.append(
                RenameDetectionResult(
                    old_name=r.old_name,
                    new_name=r.new_name,
                    similarity=r.similarity,
                    confidence=r.confidence.value if hasattr(r.confidence, "value") else str(r.confidence),
                    reasons=list(getattr(r, "reasons", [])),
                )
            )

        return RenameDetectionSummary(
            confirmed_renames=confirmed,
            possible_renames=possible,
            unmatched_added=list(getattr(result, "unmatched_added", [])),
            unmatched_removed=list(getattr(result, "unmatched_removed", [])),
        )

    def _convert_version_result(self, result: Any) -> SchemaVersionResult:
        """Convert truthound version result."""
        from datetime import datetime

        created_at = None
        if hasattr(result, "created_at") and result.created_at:
            created_at = (
                result.created_at.isoformat()
                if isinstance(result.created_at, datetime)
                else str(result.created_at)
            )

        changes = None
        if hasattr(result, "changes_from_parent") and result.changes_from_parent:
            changes = [
                SchemaChangeResult(
                    change_type=c.change_type.value if hasattr(c.change_type, "value") else str(c.change_type),
                    column_name=getattr(c, "column", getattr(c, "column_name", "")),
                    old_value=getattr(c, "old_value", None),
                    new_value=getattr(c, "new_value", None),
                    severity=c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                    breaking=getattr(c, "breaking", False),
                    description=getattr(c, "description", ""),
                    migration_hint=getattr(c, "migration_hint", None),
                )
                for c in result.changes_from_parent
            ]

        # Get schema as dict
        schema = {}
        if hasattr(result, "schema"):
            schema = result.schema if isinstance(result.schema, dict) else {}
        elif hasattr(result, "to_dict"):
            schema = result.to_dict().get("schema", {})

        return SchemaVersionResult(
            id=getattr(result, "id", getattr(result, "version_id", "")),
            version=str(getattr(result, "version", "")),
            schema=schema,
            metadata=getattr(result, "metadata", None),
            created_at=created_at,
            has_breaking_changes=getattr(result, "has_breaking_changes", False),
            changes_from_parent=changes,
        )

    def _convert_diff_result(
        self,
        diff: Any,
        from_version: str,
        to_version: str,
    ) -> SchemaDiffResult:
        """Convert truthound diff result."""
        changes = []
        for c in getattr(diff, "changes", []):
            changes.append(
                SchemaChangeResult(
                    change_type=c.change_type.value if hasattr(c.change_type, "value") else str(c.change_type),
                    column_name=getattr(c, "column", getattr(c, "column_name", "")),
                    old_value=getattr(c, "old_value", None),
                    new_value=getattr(c, "new_value", None),
                    severity=c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                    breaking=getattr(c, "breaking", False),
                    description=getattr(c, "description", ""),
                    migration_hint=getattr(c, "migration_hint", None),
                )
            )

        text_diff = ""
        if hasattr(diff, "format_text"):
            text_diff = diff.format_text()

        return SchemaDiffResult(
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            text_diff=text_diff,
        )

    def _convert_watcher_event(self, event: Any) -> SchemaWatcherEvent:
        """Convert truthound watcher event."""
        from datetime import datetime

        changes = []
        for c in getattr(event, "changes", []):
            changes.append(
                SchemaChangeResult(
                    change_type=c.change_type.value if hasattr(c.change_type, "value") else str(c.change_type),
                    column_name=getattr(c, "column", getattr(c, "column_name", "")),
                    old_value=getattr(c, "old_value", None),
                    new_value=getattr(c, "new_value", None),
                    severity=c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                    breaking=getattr(c, "breaking", False),
                    description=getattr(c, "description", ""),
                    migration_hint=getattr(c, "migration_hint", None),
                )
            )

        timestamp = datetime.utcnow().isoformat()
        if hasattr(event, "timestamp"):
            timestamp = (
                event.timestamp.isoformat()
                if isinstance(event.timestamp, datetime)
                else str(event.timestamp)
            )

        return SchemaWatcherEvent(
            source=getattr(event, "source", ""),
            has_breaking_changes=event.has_breaking_changes() if callable(getattr(event, "has_breaking_changes", None)) else getattr(event, "has_breaking_changes", False),
            total_changes=len(changes),
            changes=changes,
            timestamp=timestamp,
        )

    def _convert_alert_result(self, alert: Any) -> BreakingChangeAlert:
        """Convert truthound alert result."""
        from datetime import datetime

        changes = []
        for c in getattr(alert, "changes", []):
            if isinstance(c, dict):
                changes.append(
                    SchemaChangeResult(
                        change_type=c.get("change_type", "unknown"),
                        column_name=c.get("column_name", c.get("column", "")),
                        old_value=c.get("old_value"),
                        new_value=c.get("new_value"),
                        severity=c.get("severity", "info"),
                        breaking=c.get("breaking", False),
                        description=c.get("description", ""),
                        migration_hint=c.get("migration_hint"),
                    )
                )
            else:
                changes.append(
                    SchemaChangeResult(
                        change_type=c.change_type.value if hasattr(c.change_type, "value") else str(c.change_type),
                        column_name=getattr(c, "column", getattr(c, "column_name", "")),
                        old_value=getattr(c, "old_value", None),
                        new_value=getattr(c, "new_value", None),
                        severity=c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                        breaking=getattr(c, "breaking", False),
                        description=getattr(c, "description", ""),
                        migration_hint=getattr(c, "migration_hint", None),
                    )
                )

        # Extract impact info
        impact = getattr(alert, "impact", None)
        impact_scope = "local"
        affected_consumers: list[str] = []
        data_risk_level = 1
        recommendations: list[str] = []

        if impact:
            impact_scope = impact.scope.value if hasattr(impact.scope, "value") else str(impact.scope)
            affected_consumers = list(getattr(impact, "affected_consumers", []))
            data_risk_level = getattr(impact, "data_risk_level", 1)
            recommendations = list(getattr(impact, "recommendations", []))

        # Extract timestamps
        def _format_dt(dt: Any) -> str | None:
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt.isoformat()
            return str(dt)

        return BreakingChangeAlert(
            alert_id=getattr(alert, "alert_id", ""),
            title=getattr(alert, "title", ""),
            source=getattr(alert, "source", ""),
            changes=changes,
            impact_scope=impact_scope,
            affected_consumers=affected_consumers,
            data_risk_level=data_risk_level,
            recommendations=recommendations,
            status=getattr(alert, "status", "open"),
            created_at=_format_dt(getattr(alert, "created_at", None)) or datetime.utcnow().isoformat(),
            acknowledged_at=_format_dt(getattr(alert, "acknowledged_at", None)),
            resolved_at=_format_dt(getattr(alert, "resolved_at", None)),
        )

    def shutdown(self) -> None:
        """Shutdown the executor and stop all watchers."""
        # Stop all watchers
        for watcher_id in list(self._watchers.keys()):
            watcher_data = self._watchers[watcher_id]
            if watcher_data["status"] == "running":
                watcher_data["watcher"].stop()

        self._watchers.clear()
        self._histories.clear()
        self._executor.shutdown(wait=False)


# Singleton instance for schema evolution
_schema_evolution_adapter: SchemaEvolutionAdapter | None = None


def get_schema_evolution_adapter() -> SchemaEvolutionAdapter:
    """Get singleton schema evolution adapter instance.

    Returns:
        SchemaEvolutionAdapter singleton.
    """
    global _schema_evolution_adapter
    if _schema_evolution_adapter is None:
        from truthound_dashboard.config import get_settings

        settings = get_settings()
        _schema_evolution_adapter = SchemaEvolutionAdapter(
            max_workers=settings.max_workers
        )
    return _schema_evolution_adapter


def reset_schema_evolution_adapter() -> None:
    """Reset schema evolution adapter singleton (for testing)."""
    global _schema_evolution_adapter
    if _schema_evolution_adapter is not None:
        _schema_evolution_adapter.shutdown()
        _schema_evolution_adapter = None
