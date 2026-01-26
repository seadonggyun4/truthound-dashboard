"""Abstract base class for data quality backends.

This module defines the abstract base class that all data quality
backends must implement. It provides the contract for validation,
profiling, schema learning, and other data quality operations.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from truthound_dashboard.core.interfaces import DataInput

# Import result types from the main adapter (will be moved later)
from truthound_dashboard.core.truthound_adapter import (
    CheckResult,
    CompareResult,
    GenerateSuiteResult,
    LearnResult,
    MaskResult,
    ProfileResult,
    ScanResult,
)


class BaseDataQualityBackend(ABC):
    """Abstract base class for data quality backends.

    This class defines the interface that all data quality backends
    must implement. Concrete implementations (e.g., TruthoundBackend,
    MockBackend) inherit from this class.

    The backend is responsible for:
    - Running data validations (check)
    - Learning schemas from data (learn)
    - Profiling data (profile)
    - Detecting drift between datasets (compare)
    - Scanning for PII (scan)
    - Masking sensitive data (mask)
    - Generating validation suites (generate_suite)

    Example:
        class MyBackend(BaseDataQualityBackend):
            def is_available(self) -> bool:
                return True

            async def check(self, data, **kwargs) -> CheckResult:
                # Custom implementation
                pass
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize backend.

        Args:
            max_workers: Maximum worker threads for async operations.
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._max_workers = max_workers

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available.

        This method should verify that all required dependencies
        are installed and the backend can function.

        Returns:
            True if the backend is ready to use.
        """
        ...

    def get_version(self) -> str | None:
        """Get the backend library version.

        Returns:
            Version string or None if not available.
        """
        return None

    @abstractmethod
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
            CheckResult with validation results.
        """
        ...

    @abstractmethod
    async def learn(
        self,
        source: DataInput,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> LearnResult:
        """Learn schema from data.

        Args:
            source: File path or DataSource object.
            infer_constraints: Infer constraints from statistics.
            categorical_threshold: Max unique values for categorical.
            sample_size: Number of rows to sample.

        Returns:
            LearnResult with schema information.
        """
        ...

    @abstractmethod
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
        """Run data profiling.

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
        ...

    @abstractmethod
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
            CompareResult with drift results.
        """
        ...

    @abstractmethod
    async def scan(
        self,
        data: DataInput,
        *,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
        min_confidence: float = 0.8,
    ) -> ScanResult:
        """Scan for PII.

        Args:
            data: File path or DataSource object.
            columns: Columns to scan.
            regulations: Regulations to check.
            min_confidence: Minimum PII confidence.

        Returns:
            ScanResult with PII findings.
        """
        ...

    @abstractmethod
    async def mask(
        self,
        data: DataInput,
        output: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
    ) -> MaskResult:
        """Mask sensitive data.

        Args:
            data: File path or DataSource object.
            output: Output file path.
            columns: Columns to mask.
            strategy: Masking strategy.

        Returns:
            MaskResult with masking details.
        """
        ...

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

        Default implementation raises NotImplementedError.
        Override in backends that support suite generation.

        Args:
            profile: Profile result or dictionary.
            strictness: Rule strictness level.
            preset: Rule generation preset.
            include: Rule categories to include.
            exclude: Rule categories to exclude.
            output_format: Output format.

        Returns:
            GenerateSuiteResult with generated rules.

        Raises:
            NotImplementedError: If backend doesn't support this.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support generate_suite"
        )

    async def _run_in_executor(self, func, *args, **kwargs):
        """Run a synchronous function in the thread pool executor.

        Args:
            func: Function to run.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Function result.
        """
        loop = asyncio.get_event_loop()
        if kwargs:
            func = partial(func, *args, **kwargs)
            return await loop.run_in_executor(self._executor, func)
        return await loop.run_in_executor(self._executor, func, *args)

    def shutdown(self) -> None:
        """Shutdown the executor."""
        self._executor.shutdown(wait=False)
