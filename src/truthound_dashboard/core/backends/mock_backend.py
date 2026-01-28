"""Mock backend implementation for testing.

This module provides a mock backend that can be used for:
- Unit testing without truthound dependency
- Development when truthound is not installed
- Fallback when truthound is unavailable

The mock backend returns sensible default results for all operations.
"""

from __future__ import annotations

from typing import Any

from truthound_dashboard.core.interfaces import DataInput
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


class MockBackend(BaseDataQualityBackend):
    """Mock data quality backend for testing.

    This backend provides predictable responses for all data quality
    operations without requiring truthound or any actual data processing.

    Use cases:
    - Unit testing services without truthound
    - Development environment setup
    - Fallback when truthound is unavailable

    Example:
        backend = MockBackend()
        result = await backend.check("data.csv")
        assert result.passed == True  # Mock always passes by default
    """

    def __init__(self, max_workers: int = 4, *, always_pass: bool = True) -> None:
        """Initialize mock backend.

        Args:
            max_workers: Maximum worker threads (ignored in mock).
            always_pass: If True, validation always passes.
        """
        super().__init__(max_workers=max_workers)
        self._always_pass = always_pass

    def is_available(self) -> bool:
        """Mock is always available.

        Returns:
            Always True.
        """
        return True

    def get_version(self) -> str | None:
        """Get mock version.

        Returns:
            Mock version string.
        """
        return "mock-1.0.0"

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
        """Mock validation check.

        Returns:
            CheckResult with mock data.
        """
        source_name = data if isinstance(data, str) else getattr(data, "name", "mock")

        if self._always_pass:
            return CheckResult(
                passed=True,
                has_critical=False,
                has_high=False,
                total_issues=0,
                critical_issues=0,
                high_issues=0,
                medium_issues=0,
                low_issues=0,
                source=source_name,
                row_count=1000,
                column_count=10,
                issues=[],
            )
        else:
            return CheckResult(
                passed=False,
                has_critical=False,
                has_high=True,
                total_issues=2,
                critical_issues=0,
                high_issues=1,
                medium_issues=1,
                low_issues=0,
                source=source_name,
                row_count=1000,
                column_count=10,
                issues=[
                    {
                        "column": "id",
                        "issue_type": "null_values",
                        "count": 10,
                        "severity": "high",
                        "details": "10 null values found",
                    },
                    {
                        "column": "email",
                        "issue_type": "invalid_format",
                        "count": 5,
                        "severity": "medium",
                        "details": "5 invalid email formats",
                    },
                ],
            )

    async def learn(
        self,
        source: DataInput,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> LearnResult:
        """Mock schema learning.

        Returns:
            LearnResult with mock schema.
        """
        mock_schema = {
            "version": "1.0",
            "row_count": 1000,
            "columns": {
                "id": {
                    "name": "id",
                    "dtype": "Int64",
                    "nullable": False,
                    "unique": True,
                },
                "name": {
                    "name": "name",
                    "dtype": "String",
                    "nullable": True,
                },
                "value": {
                    "name": "value",
                    "dtype": "Float64",
                    "nullable": True,
                    "min_value": 0.0,
                    "max_value": 100.0,
                },
            },
        }

        import yaml
        schema_yaml = yaml.dump(mock_schema, default_flow_style=False)

        return LearnResult(
            schema=mock_schema,
            schema_yaml=schema_yaml,
            row_count=1000,
            column_count=3,
            columns=["id", "name", "value"],
        )

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
        """Mock data profiling.

        Returns:
            ProfileResult with mock profile data.
        """
        source_name = source if isinstance(source, str) else getattr(source, "name", "mock")

        columns = [
            ColumnProfileResult(
                name="id",
                physical_type="Int64",
                inferred_type="integer",
                row_count=1000,
                null_count=0,
                null_ratio=0.0,
                distinct_count=1000,
                unique_ratio=1.0,
                is_unique=True,
                distribution={"min": 1, "max": 1000, "mean": 500.5},
            ),
            ColumnProfileResult(
                name="name",
                physical_type="String",
                inferred_type="string",
                row_count=1000,
                null_count=50,
                null_ratio=0.05,
                distinct_count=800,
                unique_ratio=0.8,
                min_length=1,
                max_length=100,
                avg_length=25.5,
            ),
            ColumnProfileResult(
                name="email",
                physical_type="String",
                inferred_type="email",
                row_count=1000,
                null_count=10,
                null_ratio=0.01,
                distinct_count=990,
                unique_ratio=0.99,
                detected_patterns=[
                    {
                        "pattern": "email",
                        "regex": r"^[\w.+-]+@[\w-]+\.[\w.-]+$",
                        "match_ratio": 0.99,
                    }
                ],
            ),
        ]

        return ProfileResult(
            name=source_name,
            source=source_name,
            row_count=1000,
            column_count=3,
            estimated_memory_bytes=100000,
            columns=columns,
            duplicate_row_count=0,
            duplicate_row_ratio=0.0,
            correlations=None,
            profiled_at="2024-01-01T00:00:00",
            profile_duration_ms=100.0,
            size_bytes=100000,
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
        """Mock drift comparison.

        Returns:
            CompareResult with mock drift data.
        """
        baseline_name = baseline if isinstance(baseline, str) else getattr(baseline, "name", "baseline")
        current_name = current if isinstance(current, str) else getattr(current, "name", "current")

        return CompareResult(
            baseline_source=baseline_name,
            current_source=current_name,
            baseline_rows=1000,
            current_rows=1100,
            has_drift=True,
            has_high_drift=False,
            total_columns=3,
            drifted_columns=["value"],
            columns=[
                {
                    "column": "id",
                    "dtype": "Int64",
                    "drifted": False,
                    "level": "none",
                    "method": "ks",
                    "statistic": 0.02,
                    "p_value": 0.85,
                },
                {
                    "column": "name",
                    "dtype": "String",
                    "drifted": False,
                    "level": "none",
                    "method": "chi2",
                    "statistic": 5.2,
                    "p_value": 0.15,
                },
                {
                    "column": "value",
                    "dtype": "Float64",
                    "drifted": True,
                    "level": "medium",
                    "method": "psi",
                    "statistic": 0.15,
                    "p_value": 0.03,
                },
            ],
        )

    async def scan(
        self,
        data: DataInput,
        *,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
        min_confidence: float = 0.8,
    ) -> ScanResult:
        """Mock PII scan.

        Returns:
            ScanResult with mock PII findings.
        """
        source_name = data if isinstance(data, str) else getattr(data, "name", "mock")

        return ScanResult(
            source=source_name,
            row_count=1000,
            column_count=5,
            total_columns_scanned=5,
            columns_with_pii=2,
            total_findings=2,
            has_violations=False,
            total_violations=0,
            findings=[
                {
                    "column": "email",
                    "pii_type": "email",
                    "confidence": 0.95,
                    "sample_count": 990,
                },
                {
                    "column": "phone",
                    "pii_type": "phone_number",
                    "confidence": 0.88,
                    "sample_count": 500,
                },
            ],
            violations=[],
        )

    async def mask(
        self,
        data: DataInput,
        output: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
    ) -> MaskResult:
        """Mock data masking.

        Returns:
            MaskResult with mock masking info.
        """
        source_name = data if isinstance(data, str) else getattr(data, "name", "mock")

        return MaskResult(
            source=source_name,
            output_path=output,
            row_count=1000,
            column_count=5,
            columns_masked=columns or ["email", "phone"],
            strategy=strategy,
            original_columns=["id", "name", "email", "phone", "value"],
        )

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
        """Mock suite generation.

        Returns:
            GenerateSuiteResult with mock rules.
        """
        rules = [
            {
                "name": "id_not_null",
                "validator": "NotNull",
                "column": "id",
                "params": {},
                "severity": "critical",
                "category": "completeness",
            },
            {
                "name": "id_unique",
                "validator": "Unique",
                "column": "id",
                "params": {},
                "severity": "critical",
                "category": "uniqueness",
            },
            {
                "name": "email_format",
                "validator": "Regex",
                "column": "email",
                "params": {"pattern": r"^[\w.+-]+@[\w-]+\.[\w.-]+$"},
                "severity": "medium",
                "category": "format",
            },
        ]

        yaml_content = "rules:\n"
        for rule in rules:
            yaml_content += f"  - name: {rule['name']}\n"
            yaml_content += f"    validator: {rule['validator']}\n"
            if rule.get("column"):
                yaml_content += f"    column: {rule['column']}\n"

        return GenerateSuiteResult(
            rules=rules,
            rule_count=len(rules),
            categories=["completeness", "uniqueness", "format"],
            strictness=strictness,
            yaml_content=yaml_content,
            json_content={"rules": rules},
        )
