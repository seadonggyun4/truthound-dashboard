"""Truthound result converters.

This module isolates all truthound-specific result object conversions.
It handles converting truthound's Report, Schema, TableProfile, etc.
into dashboard-standard result dataclasses.

By isolating conversions here, we can:
- Handle truthound API changes in one place
- Support multiple truthound versions
- Provide graceful fallbacks for missing attributes
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class TruthoundResultConverter:
    """Converter for truthound result objects.

    This class provides static methods to convert truthound-specific
    objects into dashboard result dataclasses.

    All conversions use defensive attribute access (getattr with defaults)
    to handle different truthound versions gracefully.
    """

    @staticmethod
    def convert_severity(severity: Any) -> str:
        """Safely convert severity enum or value to lowercase string.

        Args:
            severity: Severity value (enum with .value or string).

        Returns:
            Lowercase severity string.
        """
        if hasattr(severity, "value"):
            return str(severity.value).lower()
        return str(severity).lower()

    @staticmethod
    def convert_check_result(result: Any) -> dict[str, Any]:
        """Convert truthound Report to CheckResult dict.

        The truthound Report contains:
        - issues: list[ValidationIssue]
        - source: str
        - row_count: int
        - column_count: int
        - has_issues: bool
        - has_critical: bool
        - has_high: bool

        Args:
            result: Truthound Report object.

        Returns:
            Dictionary with CheckResult fields.
        """
        issues = getattr(result, "issues", [])
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        converted_issues = []
        for issue in issues:
            severity = TruthoundResultConverter.convert_severity(issue.severity)
            if severity in severity_counts:
                severity_counts[severity] += 1

            converted_issues.append({
                "column": getattr(issue, "column", ""),
                "issue_type": getattr(issue, "issue_type", "unknown"),
                "count": getattr(issue, "count", 0),
                "severity": severity,
                "details": getattr(issue, "details", None),
                "expected": getattr(issue, "expected", None),
                "actual": getattr(issue, "actual", None),
                "sample_values": getattr(issue, "sample_values", None),
            })

        return {
            "passed": not getattr(result, "has_issues", len(issues) > 0),
            "has_critical": getattr(result, "has_critical", severity_counts["critical"] > 0),
            "has_high": getattr(result, "has_high", severity_counts["high"] > 0),
            "total_issues": len(issues),
            "critical_issues": severity_counts["critical"],
            "high_issues": severity_counts["high"],
            "medium_issues": severity_counts["medium"],
            "low_issues": severity_counts["low"],
            "source": getattr(result, "source", ""),
            "row_count": getattr(result, "row_count", 0),
            "column_count": getattr(result, "column_count", 0),
            "issues": converted_issues,
        }

    @staticmethod
    def convert_learn_result(result: Any) -> dict[str, Any]:
        """Convert truthound Schema to LearnResult dict.

        The truthound Schema contains:
        - columns: dict[str, ColumnSchema]
        - row_count: int | None
        - version: str
        - to_dict(): Convert to dictionary

        Args:
            result: Truthound Schema object.

        Returns:
            Dictionary with LearnResult fields.
        """
        schema_dict = result.to_dict() if hasattr(result, "to_dict") else {}
        schema_yaml = yaml.dump(
            schema_dict,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        columns = getattr(result, "columns", {})
        column_list = list(columns.keys()) if isinstance(columns, dict) else []

        return {
            "schema": schema_dict,
            "schema_yaml": schema_yaml,
            "row_count": getattr(result, "row_count", None),
            "column_count": len(column_list),
            "columns": column_list,
        }

    @staticmethod
    def convert_profile_result(result: Any) -> dict[str, Any]:
        """Convert truthound TableProfile or ProfileReport to ProfileResult dict.

        Supports both new TableProfile and legacy ProfileReport formats.

        Args:
            result: Truthound profile result object.

        Returns:
            Dictionary with ProfileResult fields.
        """
        # Check if this is the new TableProfile or legacy ProfileReport
        if hasattr(result, "estimated_memory_bytes"):
            return TruthoundResultConverter._convert_table_profile(result)
        else:
            return TruthoundResultConverter._convert_legacy_profile(result)

    @staticmethod
    def _convert_table_profile(result: Any) -> dict[str, Any]:
        """Convert new truthound TableProfile to ProfileResult dict."""
        columns = []
        for col in getattr(result, "columns", []):
            col_data = TruthoundResultConverter._convert_column_profile(col)
            columns.append(col_data)

        # Convert correlations
        correlations = None
        raw_correlations = getattr(result, "correlations", None)
        if raw_correlations:
            correlations = [(c[0], c[1], c[2]) for c in raw_correlations]

        # Get profiled_at as ISO string
        profiled_at = None
        raw_profiled_at = getattr(result, "profiled_at", None)
        if raw_profiled_at:
            profiled_at = (
                raw_profiled_at.isoformat()
                if isinstance(raw_profiled_at, datetime)
                else str(raw_profiled_at)
            )

        estimated_memory = getattr(result, "estimated_memory_bytes", 0)

        return {
            "name": getattr(result, "name", ""),
            "source": getattr(result, "source", ""),
            "row_count": getattr(result, "row_count", 0),
            "column_count": getattr(result, "column_count", 0),
            "estimated_memory_bytes": estimated_memory,
            "columns": columns,
            "duplicate_row_count": getattr(result, "duplicate_row_count", 0),
            "duplicate_row_ratio": getattr(result, "duplicate_row_ratio", 0.0),
            "correlations": correlations,
            "profiled_at": profiled_at,
            "profile_duration_ms": getattr(result, "profile_duration_ms", 0.0),
            "size_bytes": estimated_memory,
        }

    @staticmethod
    def _convert_column_profile(col: Any) -> dict[str, Any]:
        """Convert a single column profile."""
        # Extract distribution stats if present
        distribution = None
        raw_distribution = getattr(col, "distribution", None)
        if raw_distribution:
            distribution = {
                "mean": getattr(raw_distribution, "mean", None),
                "std": getattr(raw_distribution, "std", None),
                "min": getattr(raw_distribution, "min", None),
                "max": getattr(raw_distribution, "max", None),
                "median": getattr(raw_distribution, "median", None),
                "q1": getattr(raw_distribution, "q1", None),
                "q3": getattr(raw_distribution, "q3", None),
                "skewness": getattr(raw_distribution, "skewness", None),
                "kurtosis": getattr(raw_distribution, "kurtosis", None),
            }

        # Convert top_values
        top_values = None
        raw_top_values = getattr(col, "top_values", None)
        if raw_top_values:
            top_values = [
                {
                    "value": str(v.value) if getattr(v, "value", None) is not None else None,
                    "count": getattr(v, "count", 0),
                    "ratio": getattr(v, "ratio", 0.0),
                }
                for v in raw_top_values
            ]

        # Convert bottom_values
        bottom_values = None
        raw_bottom_values = getattr(col, "bottom_values", None)
        if raw_bottom_values:
            bottom_values = [
                {
                    "value": str(v.value) if getattr(v, "value", None) is not None else None,
                    "count": getattr(v, "count", 0),
                    "ratio": getattr(v, "ratio", 0.0),
                }
                for v in raw_bottom_values
            ]

        # Convert detected_patterns
        detected_patterns = None
        raw_patterns = getattr(col, "detected_patterns", None)
        if raw_patterns:
            detected_patterns = [
                {
                    "pattern": getattr(p, "pattern", None),
                    "regex": getattr(p, "regex", None),
                    "match_ratio": getattr(p, "match_ratio", 0.0),
                    "sample_matches": list(getattr(p, "sample_matches", [])),
                }
                for p in raw_patterns
            ]

        # Get inferred type value
        inferred_type = "unknown"
        raw_inferred_type = getattr(col, "inferred_type", None)
        if raw_inferred_type:
            inferred_type = (
                raw_inferred_type.value
                if hasattr(raw_inferred_type, "value")
                else str(raw_inferred_type)
            )

        # Convert datetime fields
        min_date = None
        max_date = None
        raw_min_date = getattr(col, "min_date", None)
        raw_max_date = getattr(col, "max_date", None)
        if raw_min_date:
            min_date = (
                raw_min_date.isoformat()
                if isinstance(raw_min_date, datetime)
                else str(raw_min_date)
            )
        if raw_max_date:
            max_date = (
                raw_max_date.isoformat()
                if isinstance(raw_max_date, datetime)
                else str(raw_max_date)
            )

        # Get suggested validators
        suggested_validators = None
        raw_validators = getattr(col, "suggested_validators", None)
        if raw_validators:
            suggested_validators = list(raw_validators)

        return {
            "name": getattr(col, "name", ""),
            "physical_type": getattr(col, "physical_type", "unknown"),
            "inferred_type": inferred_type,
            "row_count": getattr(col, "row_count", 0),
            "null_count": getattr(col, "null_count", 0),
            "null_ratio": getattr(col, "null_ratio", 0.0),
            "empty_string_count": getattr(col, "empty_string_count", 0),
            "distinct_count": getattr(col, "distinct_count", 0),
            "unique_ratio": getattr(col, "unique_ratio", 0.0),
            "is_unique": getattr(col, "is_unique", False),
            "is_constant": getattr(col, "is_constant", False),
            "distribution": distribution,
            "top_values": top_values,
            "bottom_values": bottom_values,
            "min_length": getattr(col, "min_length", None),
            "max_length": getattr(col, "max_length", None),
            "avg_length": getattr(col, "avg_length", None),
            "detected_patterns": detected_patterns,
            "min_date": min_date,
            "max_date": max_date,
            "date_gaps": getattr(col, "date_gaps", 0),
            "suggested_validators": suggested_validators,
            "profile_duration_ms": getattr(col, "profile_duration_ms", 0.0),
        }

    @staticmethod
    def _convert_legacy_profile(result: Any) -> dict[str, Any]:
        """Convert legacy truthound ProfileReport to ProfileResult dict."""
        row_count = getattr(result, "row_count", 0)
        columns = []

        for col in getattr(result, "columns", []):
            if isinstance(col, dict):
                col_data = TruthoundResultConverter._convert_legacy_column(col, row_count)
            else:
                col_data = TruthoundResultConverter._convert_column_profile(col)
            columns.append(col_data)

        size_bytes = getattr(result, "size_bytes", 0)

        return {
            "name": getattr(result, "source", ""),
            "source": getattr(result, "source", ""),
            "row_count": row_count,
            "column_count": getattr(result, "column_count", len(columns)),
            "estimated_memory_bytes": size_bytes,
            "columns": columns,
            "duplicate_row_count": 0,
            "duplicate_row_ratio": 0.0,
            "correlations": None,
            "profiled_at": None,
            "profile_duration_ms": 0.0,
            "size_bytes": size_bytes,
        }

    @staticmethod
    def _convert_legacy_column(col: dict, row_count: int) -> dict[str, Any]:
        """Convert legacy column dict to column profile dict."""
        # Parse null_pct and unique_pct
        null_ratio = 0.0
        unique_ratio = 0.0

        null_pct = col.get("null_pct")
        if isinstance(null_pct, str):
            null_ratio = float(null_pct.rstrip("%")) / 100.0
        elif isinstance(null_pct, (int, float)):
            null_ratio = float(null_pct)

        unique_pct = col.get("unique_pct")
        if isinstance(unique_pct, str):
            unique_ratio = float(unique_pct.rstrip("%")) / 100.0
        elif isinstance(unique_pct, (int, float)):
            unique_ratio = float(unique_pct)

        # Build distribution if numeric stats present
        distribution = None
        if col.get("min") is not None or col.get("mean") is not None:
            distribution = {
                "min": col.get("min"),
                "max": col.get("max"),
                "mean": col.get("mean"),
                "std": col.get("std"),
            }

        return {
            "name": col.get("name", ""),
            "physical_type": col.get("dtype", "unknown"),
            "inferred_type": col.get("dtype", "unknown"),
            "row_count": row_count,
            "null_count": 0,
            "null_ratio": null_ratio,
            "empty_string_count": 0,
            "distinct_count": 0,
            "unique_ratio": unique_ratio,
            "is_unique": False,
            "is_constant": False,
            "distribution": distribution,
            "top_values": None,
            "bottom_values": None,
            "min_length": None,
            "max_length": None,
            "avg_length": None,
            "detected_patterns": None,
            "min_date": None,
            "max_date": None,
            "date_gaps": 0,
            "suggested_validators": None,
            "profile_duration_ms": 0.0,
        }

    @staticmethod
    def convert_compare_result(result: Any) -> dict[str, Any]:
        """Convert truthound DriftReport to CompareResult dict.

        The truthound DriftReport contains:
        - baseline_source: str
        - current_source: str
        - baseline_rows: int
        - current_rows: int
        - columns: list[ColumnDrift]
        - has_drift: bool
        - has_high_drift: bool
        - get_drifted_columns(): list[str]

        Args:
            result: Truthound DriftReport object.

        Returns:
            Dictionary with CompareResult fields.
        """
        columns = []
        for col in getattr(result, "columns", []):
            col_result = getattr(col, "result", None)
            if col_result:
                level = getattr(col_result, "level", "none")
                level_str = (
                    level.value if hasattr(level, "value") else str(level)
                )
                columns.append({
                    "column": getattr(col, "column", ""),
                    "dtype": getattr(col, "dtype", "unknown"),
                    "drifted": getattr(col_result, "drifted", False),
                    "level": level_str,
                    "method": getattr(col_result, "method", "unknown"),
                    "statistic": getattr(col_result, "statistic", 0.0),
                    "p_value": getattr(col_result, "p_value", 1.0),
                    "baseline_stats": getattr(col, "baseline_stats", {}),
                    "current_stats": getattr(col, "current_stats", {}),
                })

        # Get drifted columns
        drifted_columns = []
        if hasattr(result, "get_drifted_columns"):
            drifted_columns = result.get_drifted_columns()
        else:
            drifted_columns = [c["column"] for c in columns if c.get("drifted")]

        return {
            "baseline_source": getattr(result, "baseline_source", ""),
            "current_source": getattr(result, "current_source", ""),
            "baseline_rows": getattr(result, "baseline_rows", 0),
            "current_rows": getattr(result, "current_rows", 0),
            "has_drift": getattr(result, "has_drift", False),
            "has_high_drift": getattr(result, "has_high_drift", False),
            "total_columns": len(columns),
            "drifted_columns": drifted_columns,
            "columns": columns,
        }

    @staticmethod
    def convert_scan_result(result: Any) -> dict[str, Any]:
        """Convert truthound PIIReport to ScanResult dict.

        Args:
            result: Truthound PIIReport object.

        Returns:
            Dictionary with ScanResult fields.
        """
        # Convert findings
        findings = []
        columns_with_pii = set()
        for finding in getattr(result, "findings", []):
            col = getattr(finding, "column", "")
            columns_with_pii.add(col)
            findings.append({
                "column": col,
                "pii_type": getattr(finding, "pii_type", "unknown"),
                "confidence": getattr(finding, "confidence", 0.0),
                "sample_count": getattr(finding, "sample_count", 0),
                "sample_values": getattr(finding, "sample_values", None),
            })

        # Convert violations
        violations = []
        for violation in getattr(result, "violations", []):
            violations.append({
                "regulation": getattr(violation, "regulation", "unknown"),
                "column": getattr(violation, "column", ""),
                "pii_type": getattr(violation, "pii_type", "unknown"),
                "message": getattr(violation, "message", ""),
                "severity": getattr(violation, "severity", "high"),
            })

        return {
            "source": getattr(result, "source", ""),
            "row_count": getattr(result, "row_count", 0),
            "column_count": getattr(result, "column_count", 0),
            "total_columns_scanned": getattr(result, "column_count", 0),
            "columns_with_pii": len(columns_with_pii),
            "total_findings": len(findings),
            "has_violations": getattr(result, "has_violations", len(violations) > 0),
            "total_violations": len(violations),
            "findings": findings,
            "violations": violations,
        }

    @staticmethod
    def convert_mask_result(
        source: Any,
        output: str,
        masked_df: Any,
        strategy: str,
        columns: list[str] | None,
    ) -> dict[str, Any]:
        """Convert truthound mask result to MaskResult dict.

        Args:
            source: Original data source.
            output: Output file path.
            masked_df: Polars DataFrame with masked data.
            strategy: Masking strategy used.
            columns: Columns that were masked.

        Returns:
            Dictionary with MaskResult fields.
        """
        # Get column information from the DataFrame
        all_columns = list(masked_df.columns) if hasattr(masked_df, "columns") else []
        row_count = len(masked_df) if hasattr(masked_df, "__len__") else 0

        # Get source name
        if isinstance(source, str):
            source_name = source
        else:
            source_name = getattr(source, "name", str(type(source).__name__))

        # Write the masked data to output file
        output_path = Path(output)
        suffix = output_path.suffix.lower()

        if hasattr(masked_df, "write_csv"):
            if suffix == ".csv":
                masked_df.write_csv(output)
            elif suffix == ".parquet" and hasattr(masked_df, "write_parquet"):
                masked_df.write_parquet(output)
            elif suffix == ".json" and hasattr(masked_df, "write_json"):
                masked_df.write_json(output)
            else:
                # Default to CSV
                masked_df.write_csv(output)

        return {
            "source": source_name,
            "output_path": str(output_path.absolute()),
            "row_count": row_count,
            "column_count": len(all_columns),
            "columns_masked": columns if columns else [],
            "strategy": strategy,
            "original_columns": all_columns,
        }

    @staticmethod
    def convert_suite_result(
        suite: Any,
        strictness: str,
        output_format: str = "yaml",
    ) -> dict[str, Any]:
        """Convert truthound ValidationSuite to GenerateSuiteResult dict.

        Args:
            suite: ValidationSuite from generate_suite().
            strictness: Strictness level used.
            output_format: Requested output format.

        Returns:
            Dictionary with GenerateSuiteResult fields.
        """
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

        return {
            "rules": rules,
            "rule_count": len(rules),
            "categories": sorted(categories),
            "strictness": strictness,
            "yaml_content": yaml_content,
            "json_content": json_content,
        }
