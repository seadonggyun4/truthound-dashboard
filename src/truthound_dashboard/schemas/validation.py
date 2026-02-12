"""Validation-related Pydantic schemas.

This module defines schemas for validation API operations.
Supports truthound 1.3.0+ features including:
- PHASE 1: ResultFormat system (boolean_only/basic/summary/complete)
- PHASE 2: Structured validation results (ValidationDetail, ReportStatistics)
- PHASE 4: DAG execution info (ValidatorExecutionSummary)
- PHASE 5: Exception isolation & auto-retry (ExceptionInfo, ExceptionSummary)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field

from .base import BaseSchema, IDMixin, ListResponseWrapper
from .validators import ValidatorConfig

# Validation status types
ValidationStatus = Literal["pending", "running", "success", "failed", "error"]

# Issue severity types
IssueSeverity = Literal["critical", "high", "medium", "low"]

# Result format levels (PHASE 1)
ResultFormatLevel = Literal["boolean_only", "basic", "summary", "complete"]


# ---------------------------------------------------------------------------
# PHASE 2: Structured validation detail
# ---------------------------------------------------------------------------

class ValidationDetailResult(BaseSchema):
    """Structured validation result detail (PHASE 2).

    Maps to truthound's ValidationDetail dataclass.
    Fields are populated selectively based on the result_format level.
    """

    model_config = ConfigDict(extra="ignore")

    # Always populated
    element_count: int = Field(default=0, description="Total row count")
    missing_count: int = Field(default=0, description="Null row count")

    # BASIC+
    observed_value: Any | None = Field(default=None, description="Observed metric value")
    unexpected_count: int = Field(default=0, description="Failed row count")
    unexpected_percent: float = Field(default=0.0, description="Failure rate (total)")
    unexpected_percent_nonmissing: float = Field(
        default=0.0, description="Failure rate (excl. nulls)"
    )
    partial_unexpected_list: list[Any] | None = Field(
        default=None, description="Sample of failed values"
    )

    # SUMMARY+
    partial_unexpected_counts: list[dict[str, Any]] | None = Field(
        default=None, description="Failed value frequencies [{value, count}, ...]"
    )
    partial_unexpected_index_list: list[int] | None = Field(
        default=None, description="Sample of failed row indices"
    )

    # COMPLETE
    unexpected_list: list[Any] | None = Field(
        default=None, description="Full list of failed values"
    )
    unexpected_index_list: list[int] | None = Field(
        default=None, description="Full list of failed row indices"
    )
    unexpected_rows: list[dict[str, Any]] | None = Field(
        default=None, description="Failed rows as dicts (COMPLETE mode)"
    )
    debug_query: str | None = Field(
        default=None, description="Reproducible query for failed rows (COMPLETE mode)"
    )


# ---------------------------------------------------------------------------
# PHASE 5: Exception information
# ---------------------------------------------------------------------------

class ExceptionInfoSchema(BaseSchema):
    """Individual validation exception info (PHASE 5).

    Maps to truthound's ExceptionInfo dataclass.
    """

    model_config = ConfigDict(extra="ignore")

    exception_type: str | None = Field(default=None, description="Exception class name")
    exception_message: str | None = Field(default=None, description="Exception message")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    max_retries: int = Field(default=0, description="Maximum retries configured")
    is_retryable: bool = Field(default=False, description="Whether error is retryable")
    failure_category: str = Field(
        default="unknown",
        description="Failure classification: transient|permanent|configuration|data",
    )
    validator_name: str | None = Field(default=None)
    column: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Core: ValidationIssue (extended for PHASE 1-5)
# ---------------------------------------------------------------------------

class ValidationIssue(BaseSchema):
    """Single validation issue.

    Represents one issue found during validation, mapping to
    truthound's ValidationIssue dataclass.

    Extended in truthound 1.3.0+ with:
    - result: Structured detail (PHASE 2)
    - validator_name, success: Metadata (PHASE 2)
    - exception_info: Error context (PHASE 5)
    """

    model_config = ConfigDict(extra="ignore")

    column: str = Field(..., description="Column where issue was found")
    issue_type: str = Field(
        ..., description="Type of issue", examples=["null_values", "type_mismatch"]
    )
    count: int = Field(..., ge=0, description="Number of occurrences")
    severity: IssueSeverity = Field(..., description="Issue severity level")
    details: str | None = Field(default=None, description="Detailed description")
    expected: Any | None = Field(default=None, description="Expected value/type")
    actual: Any | None = Field(default=None, description="Actual value/type found")
    sample_values: list[Any] | None = Field(
        default=None,
        description="Sample problematic values",
    )

    # PHASE 2: Structured result & metadata
    validator_name: str | None = Field(
        default=None, description="Validator that generated this issue"
    )
    success: bool = Field(default=False, description="Whether this check passed")
    result: ValidationDetailResult | None = Field(
        default=None, description="Structured detail (BASIC+ result_format)"
    )

    # PHASE 5: Exception context
    exception_info: ExceptionInfoSchema | None = Field(
        default=None,
        description="Exception info if this issue was generated from a system error",
    )


class CustomValidatorConfig(BaseSchema):
    """Configuration for running a custom validator."""

    validator_id: str = Field(
        ..., description="ID of the custom validator to run"
    )
    column: str = Field(
        ..., description="Column to validate"
    )
    params: dict[str, Any] | None = Field(
        default=None, description="Parameter values for the validator"
    )


class ValidationRunRequest(BaseSchema):
    """Request to run validation on a source.

    This schema maps to truthound's th.check() parameters for maximum flexibility.
    All optional parameters default to None/False to use truthound's defaults.

    Supports three modes:
    1. Simple mode: Use `validators` list with validator names (backward compatible)
    2. Advanced mode: Use `validator_configs` for per-validator parameter configuration
    3. Custom validators: Use `custom_validators` to include user-defined validators
    """

    # Core validation options - Simple mode (backward compatible)
    validators: list[str] | None = Field(
        default=None,
        description="Specific validators to run by name. If None, all validators are used.",
        examples=[["Null", "Duplicate", "ColumnExists"]],
    )

    # Advanced mode - Per-validator configuration
    validator_configs: list[ValidatorConfig] | None = Field(
        default=None,
        description=(
            "Advanced: Configure individual validators with specific parameters. "
            "Takes precedence over 'validators' list if provided."
        ),
    )

    # Custom validators - User-defined validators
    custom_validators: list[CustomValidatorConfig] | None = Field(
        default=None,
        description=(
            "Custom validators to run alongside built-in validators. "
            "Each config specifies the validator_id, target column, and parameters."
        ),
    )

    schema_path: str | None = Field(
        default=None,
        description="Path to schema YAML file for schema validation",
    )
    auto_schema: bool = Field(
        default=False,
        description="Auto-learn and cache schema for validation",
    )

    # Severity filtering
    min_severity: Literal["low", "medium", "high", "critical"] | None = Field(
        default=None,
        description="Minimum severity level to report. Issues below this level are ignored.",
        examples=["medium"],
    )

    # Performance options
    parallel: bool = Field(
        default=False,
        description="If True, uses DAG-based parallel execution for validators.",
    )
    max_workers: int | None = Field(
        default=None,
        ge=1,
        le=32,
        description="Maximum number of worker threads for parallel execution. Only used when parallel=True.",
        examples=[4, 8],
    )
    pushdown: bool | None = Field(
        default=None,
        description="Enable query pushdown optimization for SQL data sources. None uses auto-detection.",
    )

    # PHASE 1: Result format control
    result_format: ResultFormatLevel | None = Field(
        default=None,
        description=(
            "Controls detail level of validation results. "
            "'boolean_only': pass/fail only. 'basic': + counts and samples. "
            "'summary': + value frequency counts (default). "
            "'complete': + full failure rows and debug queries."
        ),
        examples=["summary", "complete"],
    )
    include_unexpected_rows: bool = Field(
        default=False,
        description="Include failure row data in SUMMARY or higher results.",
    )
    max_unexpected_rows: int | None = Field(
        default=None,
        ge=1,
        le=10000,
        description="Maximum number of failure rows to return when include_unexpected_rows=True.",
    )

    # PHASE 5: Exception control
    catch_exceptions: bool = Field(
        default=True,
        description=(
            "If True (default), validator errors are caught and included in the report. "
            "If False (strict mode), the first validator error aborts the entire validation."
        ),
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description=(
            "Maximum retry attempts for transient errors (timeout, connection). "
            "Only applies when catch_exceptions=True."
        ),
    )


# ---------------------------------------------------------------------------
# PHASE 2: Report statistics
# ---------------------------------------------------------------------------

class ReportStatistics(BaseSchema):
    """Aggregated validation report statistics (PHASE 2).

    Maps to truthound's ReportStatistics dataclass.
    """

    model_config = ConfigDict(extra="ignore")

    total_validations: int = Field(default=0, description="Total validations performed")
    successful_validations: int = Field(default=0, description="Passed validations")
    unsuccessful_validations: int = Field(default=0, description="Failed validations")
    success_percent: float = Field(default=0.0, description="Success rate %")
    issues_by_severity: dict[str, int] = Field(default_factory=dict)
    issues_by_column: dict[str, int] = Field(default_factory=dict)
    issues_by_validator: dict[str, int] = Field(default_factory=dict)
    issues_by_type: dict[str, int] = Field(default_factory=dict)
    most_problematic_columns: list[list[Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# PHASE 4: Validator execution summary
# ---------------------------------------------------------------------------

class SkippedValidatorInfo(BaseSchema):
    """Info about a skipped validator (PHASE 4)."""

    validator_name: str = Field(..., description="Validator name")
    reason: str | None = Field(default=None, description="Skip reason")


class ValidatorExecutionSummary(BaseSchema):
    """Validator execution summary from DAG execution (PHASE 4)."""

    total_validators: int = Field(default=0, description="Total validators")
    executed: int = Field(default=0, description="Executed validators")
    skipped: int = Field(default=0, description="Skipped validators")
    failed: int = Field(default=0, description="Failed validators")
    skipped_details: list[SkippedValidatorInfo] | None = Field(
        default=None, description="Details of skipped validators"
    )


# ---------------------------------------------------------------------------
# PHASE 5: Exception summary
# ---------------------------------------------------------------------------

class ExceptionSummarySchema(BaseSchema):
    """Session-level exception summary (PHASE 5).

    Maps to truthound's ExceptionSummary dataclass.
    """

    model_config = ConfigDict(extra="ignore")

    total_exceptions: int = Field(default=0, description="Total exception count")
    total_retries: int = Field(default=0, description="Total retry attempts")
    exceptions_by_type: dict[str, int] = Field(default_factory=dict)
    exceptions_by_category: dict[str, int] = Field(default_factory=dict)
    exceptions_by_validator: dict[str, int] = Field(default_factory=dict)
    retryable_count: int = Field(default=0, description="Number of retryable errors")


# ---------------------------------------------------------------------------
# Core: Summary & Response
# ---------------------------------------------------------------------------

class ValidationSummary(BaseSchema):
    """Summary statistics for a validation run."""

    passed: bool | None = Field(default=None, description="Whether validation passed (null when status is error)")
    has_critical: bool = Field(default=False, description="Has critical issues")
    has_high: bool = Field(default=False, description="Has high severity issues")
    total_issues: int = Field(default=0, ge=0, description="Total issue count")
    critical_issues: int = Field(default=0, ge=0, description="Critical issue count")
    high_issues: int = Field(default=0, ge=0, description="High severity issue count")
    medium_issues: int = Field(
        default=0, ge=0, description="Medium severity issue count"
    )
    low_issues: int = Field(default=0, ge=0, description="Low severity issue count")


class ValidationResponse(IDMixin, ValidationSummary):
    """Full validation response with all details."""

    source_id: str = Field(..., description="Source that was validated")
    status: ValidationStatus = Field(..., description="Current validation status")

    # Data statistics
    row_count: int | None = Field(default=None, description="Number of rows validated")
    column_count: int | None = Field(default=None, description="Number of columns")

    # Issues list (full details)
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues",
    )

    # Error info (if status is 'error')
    error_message: str | None = Field(
        default=None,
        description="Error message if validation failed",
    )

    # Timing
    duration_ms: int | None = Field(
        default=None,
        ge=0,
        description="Validation duration in milliseconds",
    )
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(
        default=None, description="Completion timestamp"
    )
    created_at: datetime = Field(..., description="Record creation timestamp")

    # PHASE 1: Result format used
    result_format: str | None = Field(
        default=None, description="Result format level used for this validation"
    )

    # PHASE 2: Report statistics
    statistics: ReportStatistics | None = Field(
        default=None, description="Aggregated validation statistics"
    )

    # PHASE 4: Execution summary
    validator_execution_summary: ValidatorExecutionSummary | None = Field(
        default=None, description="Validator execution summary (parallel/DAG mode)"
    )

    # PHASE 5: Exception summary
    exception_summary: ExceptionSummarySchema | None = Field(
        default=None, description="Session-level exception summary"
    )

    @classmethod
    def from_model(cls, validation: Any) -> ValidationResponse:
        """Create response from model.

        Handles both legacy DB records (without PHASE 1-5 fields) and
        new records with full structured data.

        Args:
            validation: Validation model instance.

        Returns:
            ValidationResponse instance.
        """
        issues: list[ValidationIssue] = []
        result_json = validation.result_json or {}

        if "issues" in result_json:
            for issue_data in result_json["issues"]:
                try:
                    issues.append(ValidationIssue(**issue_data))
                except Exception:
                    # Fallback for legacy DB records missing new fields
                    issues.append(ValidationIssue(
                        column=issue_data.get("column", ""),
                        issue_type=issue_data.get("issue_type", "unknown"),
                        count=issue_data.get("count", 0),
                        severity=issue_data.get("severity", "medium"),
                        details=issue_data.get("details"),
                        expected=issue_data.get("expected"),
                        actual=issue_data.get("actual"),
                        sample_values=issue_data.get("sample_values"),
                    ))

        # PHASE 2: statistics
        statistics = None
        raw_stats = result_json.get("statistics")
        if raw_stats and isinstance(raw_stats, dict):
            try:
                statistics = ReportStatistics(**raw_stats)
            except Exception:
                pass

        # PHASE 4: execution summary
        exec_summary = None
        raw_exec = result_json.get("validator_execution_summary")
        if raw_exec and isinstance(raw_exec, dict):
            try:
                exec_summary = ValidatorExecutionSummary(**raw_exec)
            except Exception:
                pass

        # PHASE 5: exception summary
        exc_summary = None
        raw_exc = result_json.get("exception_summary")
        if raw_exc and isinstance(raw_exc, dict):
            try:
                exc_summary = ExceptionSummarySchema(**raw_exc)
            except Exception:
                pass

        return cls(
            id=validation.id,
            source_id=validation.source_id,
            status=validation.status,
            passed=None if validation.status == "error" else (validation.passed or False),
            has_critical=validation.has_critical or False,
            has_high=validation.has_high or False,
            total_issues=validation.total_issues or 0,
            critical_issues=validation.critical_issues or 0,
            high_issues=validation.high_issues or 0,
            medium_issues=validation.medium_issues or 0,
            low_issues=validation.low_issues or 0,
            row_count=validation.row_count,
            column_count=validation.column_count,
            issues=issues,
            error_message=validation.error_message,
            duration_ms=validation.duration_ms,
            started_at=validation.started_at,
            completed_at=validation.completed_at,
            created_at=validation.created_at,
            result_format=result_json.get("result_format"),
            statistics=statistics,
            validator_execution_summary=exec_summary,
            exception_summary=exc_summary,
        )


class ValidationListItem(IDMixin, ValidationSummary):
    """Validation list item (without full issues)."""

    source_id: str
    status: ValidationStatus
    row_count: int | None = None
    column_count: int | None = None
    duration_ms: int | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, validation: Any) -> ValidationListItem:
        """Create list item from model.

        Args:
            validation: Validation model instance.

        Returns:
            ValidationListItem instance.
        """
        return cls(
            id=validation.id,
            source_id=validation.source_id,
            status=validation.status,
            passed=None if validation.status == "error" else (validation.passed or False),
            has_critical=validation.has_critical or False,
            has_high=validation.has_high or False,
            total_issues=validation.total_issues or 0,
            critical_issues=validation.critical_issues or 0,
            high_issues=validation.high_issues or 0,
            medium_issues=validation.medium_issues or 0,
            low_issues=validation.low_issues or 0,
            row_count=validation.row_count,
            column_count=validation.column_count,
            duration_ms=validation.duration_ms,
            created_at=validation.created_at,
        )


class ValidationListResponse(ListResponseWrapper[ValidationListItem]):
    """Paginated validation list response."""

    pass
