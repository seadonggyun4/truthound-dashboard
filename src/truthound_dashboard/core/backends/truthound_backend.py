"""Truthound backend implementation.

This module provides the concrete implementation of the data quality
backend using the truthound library. All truthound imports are isolated
here with lazy loading for better independence.

Updated for truthound 2.x API:
- Uses truthound.datasources.get_datasource() for auto-detection
- Supports both old and new import paths for backward compatibility
- Uses DataSourceCapability for feature detection
"""

from __future__ import annotations

import logging
from functools import partial
from typing import Any

from truthound_dashboard.core.converters import TruthoundResultConverter
from truthound_dashboard.core.interfaces import DataInput, DataSourceCapability
from truthound_dashboard.core.truthound_adapter import (
    CheckResult,
    ColumnProfileResult,
    CompareResult,
    GenerateSuiteResult,
    LearnResult,
    MaskResult,
    ProfileResult,
    ScanResult,
)

from .base import BaseDataQualityBackend
from .errors import BackendOperationError, BackendUnavailableError

logger = logging.getLogger(__name__)


class TruthoundBackend(BaseDataQualityBackend):
    """Truthound-based data quality backend.

    This backend uses the truthound library for all data quality operations.
    Truthound imports are lazy-loaded to allow the dashboard to start
    even if truthound is not installed (for testing or limited functionality).

    Example:
        backend = TruthoundBackend()
        if backend.is_available():
            result = await backend.check("data.csv")
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize truthound backend.

        Args:
            max_workers: Maximum worker threads for async operations.
        """
        super().__init__(max_workers=max_workers)
        self._th = None  # Lazy-loaded truthound module
        self._converter = TruthoundResultConverter()

    def _get_truthound(self):
        """Get truthound module with lazy loading.

        Returns:
            Truthound module.

        Raises:
            BackendUnavailableError: If truthound is not installed.
        """
        if self._th is None:
            try:
                import truthound as th
                self._th = th
            except ImportError as e:
                raise BackendUnavailableError(
                    "truthound",
                    "Library not installed. Install with: pip install truthound"
                ) from e
        return self._th

    def is_available(self) -> bool:
        """Check if truthound is available.

        Returns:
            True if truthound is installed and importable.
        """
        try:
            import truthound
            return True
        except ImportError:
            return False

    def get_version(self) -> str | None:
        """Get truthound version.

        Returns:
            Truthound version string or None if not available.
        """
        try:
            import truthound
            return getattr(truthound, "__version__", None)
        except ImportError:
            return None

    def _resolve_data_input(self, data: DataInput) -> Any:
        """Resolve DataInput to a format truthound can process.

        Truthound 2.x accepts DataSource objects directly, so we try to
        pass them through. For backward compatibility, we also support
        extracting LazyFrames from DataSource objects.

        Args:
            data: File path string, DataSource object, or DataFrame.

        Returns:
            File path string, DataSource, or DataFrame that truthound can process.
        """
        if isinstance(data, str):
            return data

        # Check if it's a truthound DataSource (new API)
        # These should be passed directly to truthound functions
        if hasattr(data, "capabilities"):
            # It's likely a truthound 2.x DataSource
            return data

        # Check if it's a DataSource with to_polars_lazyframe method (legacy)
        if hasattr(data, "to_polars_lazyframe"):
            try:
                return data.to_polars_lazyframe()
            except Exception:
                # If extraction fails, try passing the object directly
                return data

        # If it's already a LazyFrame or DataFrame, return as-is
        return data

    def _get_source_capabilities(self, data: DataInput) -> set[str]:
        """Get capabilities from a data source if available.

        Args:
            data: DataInput object.

        Returns:
            Set of capability names, or empty set if not available.
        """
        if hasattr(data, "capabilities"):
            try:
                capabilities = data.capabilities
                return {c.name for c in capabilities}
            except Exception:
                pass
        return set()

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
        """Run data validation using truthound.

        Updated for truthound 2.x API:
        - Supports passing DataSource objects directly via 'source' parameter
        - Falls back to 'data' parameter for file paths and DataFrames

        Args:
            data: File path, DataSource object, or DataFrame.
            validators: List of validator names to run.
            validator_config: Per-validator configuration.
            schema: Path to schema YAML file.
            auto_schema: Auto-learn schema for validation.
            columns: Columns to validate.
            min_severity: Minimum severity to report.
            strict: Raise exception on failures.
            parallel: Use parallel execution.
            max_workers: Max threads for parallel.
            pushdown: Enable query pushdown. If None, auto-detect from source capabilities.

        Returns:
            CheckResult with validation results.
        """
        th = self._get_truthound()

        # Resolve DataSource
        resolved_data = self._resolve_data_input(data)

        # Build kwargs
        kwargs: dict[str, Any] = {}

        # Truthound 2.x prefers 'source' for DataSource objects
        # but also accepts 'data' for backward compatibility
        if hasattr(resolved_data, "capabilities"):
            # It's a truthound 2.x DataSource, use 'source' parameter
            kwargs["source"] = resolved_data

            # Auto-enable pushdown if source supports it and not explicitly set
            if pushdown is None:
                source_caps = self._get_source_capabilities(resolved_data)
                if "SQL_PUSHDOWN" in source_caps:
                    pushdown = True
        else:
            # File path or DataFrame, use 'data' parameter
            kwargs["data"] = resolved_data

        kwargs.update({
            "validators": validators,
            "schema": schema,
            "auto_schema": auto_schema,
            "parallel": parallel,
        })

        if validator_config:
            kwargs["validator_config"] = validator_config
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

        try:
            func = partial(th.check, **kwargs)
            result = await self._run_in_executor(func)
            return self._convert_check_result(result)
        except Exception as e:
            if "truthound" in str(type(e).__module__):
                raise BackendOperationError(
                    "truthound", "check", str(e), original_error=e
                ) from e
            raise

    async def learn(
        self,
        source: DataInput,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> LearnResult:
        """Learn schema from data using truthound.

        Args:
            source: File path or DataSource object.
            infer_constraints: Infer constraints from statistics.
            categorical_threshold: Max unique values for categorical.
            sample_size: Number of rows to sample.

        Returns:
            LearnResult with schema information.
        """
        th = self._get_truthound()

        # Resolve DataSource to LazyFrame if needed
        resolved_source = self._resolve_data_input(source)

        kwargs: dict[str, Any] = {"infer_constraints": infer_constraints}
        if categorical_threshold is not None:
            kwargs["categorical_threshold"] = categorical_threshold
        if sample_size is not None:
            kwargs["sample_size"] = sample_size

        try:
            func = partial(th.learn, resolved_source, **kwargs)
            result = await self._run_in_executor(func)
            return self._convert_learn_result(result)
        except Exception as e:
            if "truthound" in str(type(e).__module__):
                raise BackendOperationError(
                    "truthound", "learn", str(e), original_error=e
                ) from e
            raise

    async def profile(
        self,
        source: DataInput,
        *,
        sample_size: int | None = None,
        include_patterns: bool = True,
        include_correlations: bool = False,
        include_distributions: bool = True,
        top_n_values: int = 10,
        pattern_sample_size: int = 1000,
        correlation_threshold: float = 0.7,
        min_pattern_match_ratio: float = 0.8,
        n_jobs: int = 1,
    ) -> ProfileResult:
        """Run data profiling using truthound.

        Args:
            source: File path or DataSource object.
            sample_size: Max rows to sample.
            include_patterns: Enable pattern detection.
            include_correlations: Calculate correlations.
            include_distributions: Include distribution stats.
            top_n_values: Top/bottom values per column.
            pattern_sample_size: Sample size for pattern matching.
            correlation_threshold: Minimum correlation to report.
            min_pattern_match_ratio: Minimum pattern match ratio.
            n_jobs: Number of parallel jobs.

        Returns:
            ProfileResult with profiling information.
        """
        # Resolve DataSource to LazyFrame if needed
        resolved_source = self._resolve_data_input(source)

        # Use th.profile() API which handles file paths and DataFrames
        # Note: th.profile() doesn't support advanced ProfilerConfig options,
        # those are only available via DataProfiler with LazyFrame input.
        # See: .truthound_docs/python-api/core-functions.md
        th = self._get_truthound()

        func = partial(th.profile, resolved_source)
        result = await self._run_in_executor(func)
        return self._convert_profile_result(result)

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
    ) -> CompareResult:
        """Compare datasets for drift detection using truthound.

        Args:
            baseline: Reference data.
            current: Current data to compare.
            columns: Columns to compare.
            method: Detection method.
            threshold: Drift threshold.
            correction: Multiple testing correction.
            sample_size: Sample size for large datasets.

        Returns:
            CompareResult with drift results.
        """
        th = self._get_truthound()

        # Resolve DataSource inputs to LazyFrame if needed
        resolved_baseline = self._resolve_data_input(baseline)
        resolved_current = self._resolve_data_input(current)

        kwargs: dict[str, Any] = {
            "columns": columns,
            "method": method,
        }

        if threshold is not None:
            kwargs["threshold"] = threshold
        if correction is not None:
            kwargs["correction"] = correction
        if sample_size is not None:
            kwargs["sample_size"] = sample_size

        try:
            func = partial(th.compare, resolved_baseline, resolved_current, **kwargs)
            result = await self._run_in_executor(func)
            return self._convert_compare_result(result)
        except Exception as e:
            if "truthound" in str(type(e).__module__):
                raise BackendOperationError(
                    "truthound", "compare", str(e), original_error=e
                ) from e
            raise

    async def scan(
        self,
        data: DataInput,
        *,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
        min_confidence: float = 0.8,
    ) -> ScanResult:
        """Scan for PII using truthound.

        Args:
            data: File path or DataSource object.
            columns: Columns to scan.
            regulations: Regulations to check.
            min_confidence: Minimum PII confidence.

        Returns:
            ScanResult with PII findings.
        """
        th = self._get_truthound()

        # Resolve DataSource to LazyFrame if needed
        resolved_data = self._resolve_data_input(data)

        # Note: truthound's th.scan() does not support min_confidence, columns,
        # or regulations parameters. We filter results after scanning.
        # See: .truthound_docs/python-api/core-functions.md

        try:
            func = partial(th.scan, resolved_data)
            result = await self._run_in_executor(func)
            return self._convert_scan_result(
                result,
                min_confidence=min_confidence,
                columns=columns,
                regulations=regulations,
            )
        except Exception as e:
            if "truthound" in str(type(e).__module__):
                raise BackendOperationError(
                    "truthound", "scan", str(e), original_error=e
                ) from e
            raise

    async def mask(
        self,
        data: DataInput,
        output: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
    ) -> MaskResult:
        """Mask sensitive data using truthound.

        Args:
            data: File path or DataSource object.
            output: Output file path.
            columns: Columns to mask.
            strategy: Masking strategy.

        Returns:
            MaskResult with masking details.
        """
        th = self._get_truthound()

        # Resolve DataSource to LazyFrame if needed
        resolved_data = self._resolve_data_input(data)

        if strategy not in ("redact", "hash", "fake"):
            raise ValueError(
                f"Invalid strategy: {strategy}. Use 'redact', 'hash', or 'fake'."
            )

        kwargs: dict[str, Any] = {
            "strategy": strategy,
        }

        if columns is not None:
            kwargs["columns"] = columns

        try:
            func = partial(th.mask, resolved_data, **kwargs)
            masked_df = await self._run_in_executor(func)
            return self._convert_mask_result(data, output, masked_df, strategy, columns)
        except Exception as e:
            if "truthound" in str(type(e).__module__):
                raise BackendOperationError(
                    "truthound", "mask", str(e), original_error=e
                ) from e
            raise

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
        """Generate validation suite from profile using truthound.

        Args:
            profile: Profile result or dictionary.
            strictness: Rule strictness level.
            preset: Rule generation preset.
            include: Rule categories to include.
            exclude: Rule categories to exclude.
            output_format: Output format.

        Returns:
            GenerateSuiteResult with generated rules.
        """
        from truthound.profiler import generate_suite
        from truthound.profiler.generators import Strictness

        strictness_map = {
            "loose": Strictness.LOOSE,
            "medium": Strictness.MEDIUM,
            "strict": Strictness.STRICT,
        }
        strictness_enum = strictness_map.get(strictness.lower(), Strictness.MEDIUM)

        if isinstance(profile, ProfileResult):
            profile_data = profile.to_dict()
        else:
            profile_data = profile

        kwargs: dict[str, Any] = {
            "strictness": strictness_enum,
            "preset": preset,
        }
        if include:
            kwargs["include"] = include
        if exclude:
            kwargs["exclude"] = exclude

        def _generate():
            return generate_suite(profile_data, **kwargs)

        suite = await self._run_in_executor(_generate)
        return self._convert_suite_result(suite, strictness, output_format)

    # =========================================================================
    # Result Conversion Methods
    # =========================================================================

    def _convert_check_result(self, result: Any) -> CheckResult:
        """Convert truthound Report to CheckResult."""
        data = self._converter.convert_check_result(result)
        return CheckResult(
            passed=data["passed"],
            has_critical=data["has_critical"],
            has_high=data["has_high"],
            total_issues=data["total_issues"],
            critical_issues=data["critical_issues"],
            high_issues=data["high_issues"],
            medium_issues=data["medium_issues"],
            low_issues=data["low_issues"],
            source=data["source"],
            row_count=data["row_count"],
            column_count=data["column_count"],
            issues=data["issues"],
        )

    def _convert_learn_result(self, result: Any) -> LearnResult:
        """Convert truthound Schema to LearnResult."""
        data = self._converter.convert_learn_result(result)
        return LearnResult(
            schema=data["schema"],
            schema_yaml=data["schema_yaml"],
            row_count=data["row_count"],
            column_count=data["column_count"],
            columns=data["columns"],
        )

    def _convert_profile_result(self, result: Any) -> ProfileResult:
        """Convert truthound TableProfile to ProfileResult."""
        data = self._converter.convert_profile_result(result)

        columns = [
            ColumnProfileResult(
                name=col["name"],
                physical_type=col["physical_type"],
                inferred_type=col.get("inferred_type", "unknown"),
                row_count=col.get("row_count", 0),
                null_count=col.get("null_count", 0),
                null_ratio=col.get("null_ratio", 0.0),
                empty_string_count=col.get("empty_string_count", 0),
                distinct_count=col.get("distinct_count", 0),
                unique_ratio=col.get("unique_ratio", 0.0),
                is_unique=col.get("is_unique", False),
                is_constant=col.get("is_constant", False),
                distribution=col.get("distribution"),
                top_values=col.get("top_values"),
                bottom_values=col.get("bottom_values"),
                min_length=col.get("min_length"),
                max_length=col.get("max_length"),
                avg_length=col.get("avg_length"),
                detected_patterns=col.get("detected_patterns"),
                min_date=col.get("min_date"),
                max_date=col.get("max_date"),
                date_gaps=col.get("date_gaps", 0),
                suggested_validators=col.get("suggested_validators"),
                profile_duration_ms=col.get("profile_duration_ms", 0.0),
            )
            for col in data["columns"]
        ]

        return ProfileResult(
            name=data["name"],
            source=data["source"],
            row_count=data["row_count"],
            column_count=data["column_count"],
            estimated_memory_bytes=data["estimated_memory_bytes"],
            columns=columns,
            duplicate_row_count=data.get("duplicate_row_count", 0),
            duplicate_row_ratio=data.get("duplicate_row_ratio", 0.0),
            correlations=data.get("correlations"),
            profiled_at=data.get("profiled_at"),
            profile_duration_ms=data.get("profile_duration_ms", 0.0),
            size_bytes=data.get("size_bytes", 0),
        )

    def _convert_compare_result(self, result: Any) -> CompareResult:
        """Convert truthound DriftReport to CompareResult."""
        data = self._converter.convert_compare_result(result)
        return CompareResult(
            baseline_source=data["baseline_source"],
            current_source=data["current_source"],
            baseline_rows=data["baseline_rows"],
            current_rows=data["current_rows"],
            has_drift=data["has_drift"],
            has_high_drift=data["has_high_drift"],
            total_columns=data["total_columns"],
            drifted_columns=data["drifted_columns"],
            columns=data["columns"],
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

        Args:
            result: truthound PIIReport object.
            min_confidence: Filter findings by minimum confidence (0.0-1.0).
            columns: Filter findings to specific columns only.
            regulations: Filter findings by regulation types.

        Returns:
            ScanResult with filtered PII findings.
        """
        data = self._converter.convert_scan_result(result)

        # Filter findings based on parameters
        findings = data["findings"]
        if findings:
            # Filter by min_confidence (confidence is 0-100 in findings)
            findings = [
                f for f in findings
                if f.get("confidence", 100) >= min_confidence * 100
            ]

            # Filter by columns
            if columns:
                findings = [
                    f for f in findings
                    if f.get("column") in columns
                ]

            # Filter by regulations (if finding has regulation info)
            if regulations:
                findings = [
                    f for f in findings
                    if not f.get("regulation") or f.get("regulation") in regulations
                ]

        # Recalculate summary stats after filtering
        columns_with_pii = len({f.get("column") for f in findings if f.get("column")})

        return ScanResult(
            source=data["source"],
            row_count=data["row_count"],
            column_count=data["column_count"],
            total_columns_scanned=data["total_columns_scanned"],
            columns_with_pii=columns_with_pii,
            total_findings=len(findings),
            has_violations=data["has_violations"],
            total_violations=data["total_violations"],
            findings=findings,
            violations=data["violations"],
        )

    def _convert_mask_result(
        self,
        source: DataInput,
        output: str,
        masked_df: Any,
        strategy: str,
        columns: list[str] | None,
    ) -> MaskResult:
        """Convert truthound mask result to MaskResult."""
        data = self._converter.convert_mask_result(
            source, output, masked_df, strategy, columns
        )
        return MaskResult(
            source=data["source"],
            output_path=data["output_path"],
            row_count=data["row_count"],
            column_count=data["column_count"],
            columns_masked=data["columns_masked"],
            strategy=data["strategy"],
            original_columns=data["original_columns"],
        )

    def _convert_suite_result(
        self,
        suite: Any,
        strictness: str,
        output_format: str,
    ) -> GenerateSuiteResult:
        """Convert truthound ValidationSuite to GenerateSuiteResult."""
        data = self._converter.convert_suite_result(suite, strictness, output_format)
        return GenerateSuiteResult(
            rules=data["rules"],
            rule_count=data["rule_count"],
            categories=data["categories"],
            strictness=data["strictness"],
            yaml_content=data["yaml_content"],
            json_content=data["json_content"],
        )
