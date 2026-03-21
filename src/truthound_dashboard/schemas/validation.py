"""Validation-related Pydantic schemas.

The dashboard keeps a small amount of derived summary data for UI cards, but
the primary response contract follows Truthound 3.0's ``ValidationRunResult``
shape: ``run_id``, ``run_time``, ``checks``, ``issues``,
``execution_issues``, ``row_count``, ``column_count``, and ``metadata``.
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

# Result format levels
ResultFormatLevel = Literal["boolean_only", "basic", "summary", "complete"]


# ---------------------------------------------------------------------------
# Structured validation detail
# ---------------------------------------------------------------------------

class ValidationDetailResult(BaseSchema):
    """Structured validation result detail.

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
# Exception information
# ---------------------------------------------------------------------------

class ExceptionInfoSchema(BaseSchema):
    """Individual validation exception info.

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
# Validation issues
# ---------------------------------------------------------------------------

class ValidationIssue(BaseSchema):
    """Single validation issue.

    Represents one issue found during validation, mapping to
    truthound's ValidationIssue dataclass.

    Truthound 3.0 still carries rich nested detail on each issue, including
    structured result data and optional exception context.
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

    validator_name: str | None = Field(
        default=None, description="Validator that generated this issue"
    )
    success: bool = Field(default=False, description="Whether this check passed")
    result: ValidationDetailResult | None = Field(
        default=None, description="Structured detail (BASIC+ result_format)"
    )

    exception_info: ExceptionInfoSchema | None = Field(
        default=None,
        description="Exception info if this issue was generated from a system error",
    )


class ValidationCheck(BaseSchema):
    """Canonical Truthound 3.0 per-check result."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Check name")
    category: str = Field(default="general", description="Check category")
    success: bool = Field(default=True, description="Whether the check passed")
    issue_count: int = Field(default=0, ge=0, description="Number of issues raised by this check")
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="Issues associated with this check",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary Truthound check metadata",
    )


class ExecutionIssue(BaseSchema):
    """Canonical Truthound 3.0 execution issue."""

    model_config = ConfigDict(extra="ignore")

    check_name: str = Field(..., description="Name of the check that failed during execution")
    message: str = Field(..., description="Execution failure message")
    exception_type: str | None = Field(default=None, description="Exception type when available")
    failure_category: str | None = Field(default=None, description="Execution failure classification")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")


class ValidationRunRequest(BaseSchema):
    """Request to run validation on a source.

    This schema maps to truthound's th.check() parameters for maximum flexibility.
    All optional parameters default to None/False to use truthound's defaults.

    Supports two modes:
    1. Simple mode: Use `validators` list with validator names
    2. Advanced mode: Use `validator_configs` for per-validator parameter configuration
    """

    # Core validation options - Simple mode
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

    # Result format control
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

    # Exception handling control
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
# Derived report statistics
# ---------------------------------------------------------------------------

class ReportStatistics(BaseSchema):
    """Aggregated validation report statistics derived from Truthound runs."""

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
# Execution summary
# ---------------------------------------------------------------------------

class SkippedValidatorInfo(BaseSchema):
    """Info about a skipped validator."""

    validator_name: str = Field(..., description="Validator name")
    reason: str | None = Field(default=None, description="Skip reason")


class ValidatorExecutionSummary(BaseSchema):
    """Validator execution summary from canonical check results."""

    total_validators: int = Field(default=0, description="Total validators")
    executed: int = Field(default=0, description="Executed validators")
    skipped: int = Field(default=0, description="Skipped validators")
    failed: int = Field(default=0, description="Failed validators")
    skipped_details: list[SkippedValidatorInfo] | None = Field(
        default=None, description="Details of skipped validators"
    )


# ---------------------------------------------------------------------------
# Exception summary
# ---------------------------------------------------------------------------

class ExceptionSummarySchema(BaseSchema):
    """Session-level exception summary derived from execution issues."""

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
    run_id: str | None = Field(default=None, description="Truthound run identifier")
    run_time: datetime | None = Field(default=None, description="Truthound run timestamp")

    # Data statistics
    row_count: int | None = Field(default=None, description="Number of rows validated")
    column_count: int | None = Field(default=None, description="Number of columns")

    checks: list[ValidationCheck] = Field(
        default_factory=list,
        description="Canonical Truthound 3.0 per-check results",
    )

    # Issues list (full details)
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues",
    )
    execution_issues: list[ExecutionIssue] = Field(
        default_factory=list,
        description="Canonical Truthound 3.0 execution issues",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Canonical Truthound 3.0 run metadata",
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

    result_format: str | None = Field(
        default=None, description="Result format level used for this validation"
    )

    statistics: ReportStatistics | None = Field(
        default=None, description="Aggregated validation statistics"
    )

    validator_execution_summary: ValidatorExecutionSummary | None = Field(
        default=None, description="Validator execution summary (parallel/DAG mode)"
    )

    exception_summary: ExceptionSummarySchema | None = Field(
        default=None, description="Session-level exception summary"
    )

    @staticmethod
    def _build_statistics(
        issues: list[ValidationIssue],
        checks: list[ValidationCheck],
    ) -> ReportStatistics | None:
        """Derive summary statistics from canonical Truthound results."""
        if not issues and not checks:
            return None

        issues_by_severity: dict[str, int] = {}
        issues_by_column: dict[str, int] = {}
        issues_by_validator: dict[str, int] = {}
        issues_by_type: dict[str, int] = {}

        for issue in issues:
            validator = issue.validator_name or issue.issue_type or "unknown"
            issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1
            issues_by_column[issue.column] = issues_by_column.get(issue.column, 0) + 1
            issues_by_validator[validator] = issues_by_validator.get(validator, 0) + 1
            issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1

        most_problematic_columns = [
            [column, count]
            for column, count in sorted(
                issues_by_column.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        total_checks = len(checks)
        successful_checks = sum(1 for check in checks if check.success)

        return ReportStatistics(
            total_validations=total_checks,
            successful_validations=successful_checks,
            unsuccessful_validations=total_checks - successful_checks,
            success_percent=(successful_checks / total_checks * 100.0) if total_checks else 100.0,
            issues_by_severity=issues_by_severity,
            issues_by_column=issues_by_column,
            issues_by_validator=issues_by_validator,
            issues_by_type=issues_by_type,
            most_problematic_columns=most_problematic_columns,
        )

    @staticmethod
    def _build_execution_summary(
        checks: list[ValidationCheck],
        execution_issues: list[ExecutionIssue],
    ) -> ValidatorExecutionSummary | None:
        """Derive a lightweight execution summary from canonical checks."""
        if not checks:
            return None

        return ValidatorExecutionSummary(
            total_validators=len(checks),
            executed=len(checks),
            skipped=0,
            failed=len(execution_issues),
            skipped_details=[],
        )

    @staticmethod
    def _build_exception_summary(
        execution_issues: list[ExecutionIssue],
    ) -> ExceptionSummarySchema | None:
        """Derive exception summary from Truthound 3.0 execution issues."""
        if not execution_issues:
            return None

        exceptions_by_type: dict[str, int] = {}
        exceptions_by_category: dict[str, int] = {}
        exceptions_by_validator: dict[str, int] = {}
        total_retries = 0
        retryable_count = 0

        for issue in execution_issues:
            exception_type = issue.exception_type or "unknown"
            category = issue.failure_category or "unknown"
            exceptions_by_type[exception_type] = exceptions_by_type.get(exception_type, 0) + 1
            exceptions_by_category[category] = exceptions_by_category.get(category, 0) + 1
            exceptions_by_validator[issue.check_name] = (
                exceptions_by_validator.get(issue.check_name, 0) + 1
            )
            total_retries += issue.retry_count
            if issue.retry_count > 0:
                retryable_count += 1

        return ExceptionSummarySchema(
            total_exceptions=len(execution_issues),
            total_retries=total_retries,
            exceptions_by_type=exceptions_by_type,
            exceptions_by_category=exceptions_by_category,
            exceptions_by_validator=exceptions_by_validator,
            retryable_count=retryable_count,
        )

    @classmethod
    def from_model(cls, validation: Any) -> ValidationResponse:
        """Create response from a stored validation model."""
        issues: list[ValidationIssue] = []
        result_json = validation.result_json or {}
        checks: list[ValidationCheck] = []
        execution_issues: list[ExecutionIssue] = []
        metadata = result_json.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        if "issues" in result_json:
            for issue_data in result_json["issues"]:
                try:
                    issues.append(ValidationIssue(**issue_data))
                except Exception:
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

        for check_data in result_json.get("checks", []):
            try:
                checks.append(ValidationCheck(**check_data))
            except Exception:
                checks.append(ValidationCheck(
                    name=check_data.get("name", "unknown"),
                    category=check_data.get("category", "general"),
                    success=check_data.get("success", True),
                    issue_count=check_data.get("issue_count", 0),
                    issues=[],
                    metadata=check_data.get("metadata") or {},
                ))

        for execution_issue_data in result_json.get("execution_issues", []):
            try:
                execution_issues.append(ExecutionIssue(**execution_issue_data))
            except Exception:
                execution_issues.append(ExecutionIssue(
                    check_name=execution_issue_data.get("check_name", "unknown"),
                    message=execution_issue_data.get("message", ""),
                    exception_type=execution_issue_data.get("exception_type"),
                    failure_category=execution_issue_data.get("failure_category"),
                    retry_count=execution_issue_data.get("retry_count", 0),
                ))

        statistics = None
        raw_stats = result_json.get("statistics")
        if raw_stats and isinstance(raw_stats, dict):
            try:
                statistics = ReportStatistics(**raw_stats)
            except Exception:
                pass
        if statistics is None:
            statistics = cls._build_statistics(issues, checks)

        exec_summary = None
        raw_exec = result_json.get("validator_execution_summary")
        if raw_exec and isinstance(raw_exec, dict):
            try:
                exec_summary = ValidatorExecutionSummary(**raw_exec)
            except Exception:
                pass
        if exec_summary is None:
            exec_summary = cls._build_execution_summary(checks, execution_issues)

        exc_summary = None
        raw_exc = result_json.get("exception_summary")
        if raw_exc and isinstance(raw_exc, dict):
            try:
                exc_summary = ExceptionSummarySchema(**raw_exc)
            except Exception:
                pass
        if exc_summary is None:
            exc_summary = cls._build_exception_summary(execution_issues)

        run_time = None
        raw_run_time = result_json.get("run_time")
        if isinstance(raw_run_time, datetime):
            run_time = raw_run_time
        elif isinstance(raw_run_time, str):
            try:
                run_time = datetime.fromisoformat(raw_run_time)
            except ValueError:
                run_time = None

        return cls(
            id=validation.id,
            source_id=validation.source_id,
            status=validation.status,
            run_id=result_json.get("run_id"),
            run_time=run_time,
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
            checks=checks,
            issues=issues,
            execution_issues=execution_issues,
            metadata=metadata,
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
