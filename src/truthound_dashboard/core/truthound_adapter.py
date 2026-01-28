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
        columns: list[str] | None = None,
        min_severity: str | None = None,
        strict: bool = False,
        parallel: bool = False,
        max_workers: int | None = None,
        pushdown: bool | None = None,
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
            columns: Columns to validate. If None, validates all columns.
            min_severity: Minimum severity to report ("low", "medium", "high", "critical").
            strict: If True, raises exception on validation failures.
            parallel: If True, uses DAG-based parallel execution.
            max_workers: Max threads for parallel execution.
            pushdown: Enable query pushdown for SQL sources. None uses auto-detection.

        Returns:
            CheckResult with validation results.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
            ValidationError: If strict=True and validation fails.
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
        if columns is not None:
            kwargs["columns"] = columns
        if min_severity is not None:
            kwargs["min_severity"] = min_severity
        if strict:
            kwargs["strict"] = strict
        if max_workers is not None:
            kwargs["max_workers"] = max_workers
        if pushdown is not None:
            kwargs["pushdown"] = pushdown

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
    ) -> LearnResult:
        """Learn schema from data asynchronously.

        Uses truthound's th.learn() to analyze data and generate schema.

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

        Returns:
            LearnResult with schema information.
        """
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

    async def scan(
        self,
        data: DataInput,
        *,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
        min_confidence: float = 0.8,
    ) -> ScanResult:
        """Run PII scan on data asynchronously.

        Uses truthound's th.scan() to detect personally identifiable information
        and check compliance with privacy regulations.

        Args:
            data: Data source - can be:
                - File path string (CSV, Parquet, etc.)
                - DataSource object
            columns: Optional list of columns to scan. If None, scans all columns.
            regulations: Optional list of regulations to check compliance.
                Supported: "gdpr", "ccpa", "lgpd"
            min_confidence: Minimum confidence threshold for PII detection (0.0-1.0).
                Default is 0.8.

        Returns:
            ScanResult with PII findings and regulation violations.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
        """
        import truthound as th

        # Note: truthound's th.scan() does not support min_confidence, columns,
        # or regulations parameters. We filter results after scanning.
        # See: .truthound_docs/python-api/core-functions.md

        func = partial(th.scan, data)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_scan_result(
            result,
            min_confidence=min_confidence,
            columns=columns,
            regulations=regulations,
        )

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

        return await self.learn(
            source,
            infer_constraints=infer_constraints,
            categorical_threshold=categorical_threshold,
            sample_size=sample_size,
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

        The truthound Report contains:
        - issues: list[ValidationIssue]
        - source: str
        - row_count: int
        - column_count: int
        - has_issues: bool
        - has_critical: bool
        - has_high: bool

        Also handles truthound 2.x ValidationResult format with:
        - run_id: str
        - run_time: datetime
        - results: list[ValidatorResult]
        - statistics: ResultStatistics
        """
        from datetime import datetime

        issues = result.issues
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in issues:
            severity = issue.severity.value.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        converted_issues = [
            {
                "column": issue.column,
                "issue_type": issue.issue_type,
                "count": issue.count,
                "severity": issue.severity.value,
                "details": getattr(issue, "details", None),
                "expected": getattr(issue, "expected", None),
                "actual": getattr(issue, "actual", None),
                "validator_name": getattr(issue, "validator_name", issue.issue_type),
                "message": getattr(issue, "message", ""),
                "sample_values": getattr(issue, "sample_values", None),
            }
            for issue in issues
        ]

        # Extract run_id and run_time if available (truthound 2.x)
        run_id = getattr(result, "run_id", None)
        run_time = getattr(result, "run_time", None)
        if run_time is None:
            run_time = datetime.now()

        return CheckResult(
            passed=not result.has_issues,
            has_critical=result.has_critical,
            has_high=result.has_high,
            total_issues=len(issues),
            critical_issues=severity_counts["critical"],
            high_issues=severity_counts["high"],
            medium_issues=severity_counts["medium"],
            low_issues=severity_counts["low"],
            source=result.source,
            row_count=result.row_count,
            column_count=result.column_count,
            issues=converted_issues,
            run_id=run_id,
            run_time=run_time,
            _raw_result=result,  # Store raw result for reporter integration
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

    def _convert_scan_result(
        self,
        result: Any,
        *,
        min_confidence: float = 0.8,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
    ) -> ScanResult:
        """Convert truthound PIIReport to ScanResult with optional filtering.

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
            min_confidence: Filter findings by minimum confidence (0.0-1.0).
            columns: Filter findings to specific columns only.
            regulations: Filter findings by regulation types.

        Returns:
            ScanResult with filtered PII findings.
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

            # Apply min_confidence filter (confidence is 0-100 in findings)
            if confidence < min_confidence * 100:
                continue

            # Apply columns filter
            if columns and column not in columns:
                continue

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
            # Apply regulations filter
            if regulations and violation.regulation not in regulations:
                continue

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
