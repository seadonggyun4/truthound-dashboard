"""Reporter interface definitions.

This module defines the abstract interfaces for the reporter system,
enabling loose coupling with truthound and other reporting backends.

The interface design follows these principles:
1. Protocol-based typing for flexible duck typing
2. Backend-agnostic data structures
3. Adapter pattern for external reporter integration
4. Factory pattern for reporter instantiation

Example:
    from truthound_dashboard.core.reporters.interfaces import (
        ReporterProtocol,
        ReporterConfig,
        ReportData,
    )

    class MyReporter:
        # Duck typing - no inheritance required
        def render(self, data: ReportData, config: ReporterConfig) -> str:
            ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

if TYPE_CHECKING:
    pass


class ReportFormatType(str, Enum):
    """Supported report output formats.

    This enum is backend-agnostic and maps to specific implementations.
    Includes both standard formats and CI-specific formats.
    """

    # Standard formats
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    YAML = "yaml"
    NDJSON = "ndjson"
    CONSOLE = "console"
    TABLE = "table"

    # CI platform formats (auto-detected or specific)
    CI = "ci"  # Auto-detect CI platform
    GITHUB = "github"  # GitHub Actions
    GITLAB = "gitlab"  # GitLab CI
    JENKINS = "jenkins"  # Jenkins
    AZURE = "azure"  # Azure DevOps
    CIRCLECI = "circleci"  # CircleCI
    BITBUCKET = "bitbucket"  # Bitbucket Pipelines
    TRAVIS = "travis"  # Travis CI
    TEAMCITY = "teamcity"  # TeamCity
    BUILDKITE = "buildkite"  # Buildkite
    DRONE = "drone"  # Drone CI

    @classmethod
    def from_string(cls, value: str) -> ReportFormatType:
        """Parse format from string (case-insensitive)."""
        value_lower = value.lower()
        for fmt in cls:
            if fmt.value == value_lower:
                return fmt
        raise ValueError(
            f"Unknown report format: {value}. "
            f"Supported formats: {[f.value for f in cls]}"
        )

    @classmethod
    def is_ci_format(cls, format: "ReportFormatType") -> bool:
        """Check if this is a CI-specific format."""
        return format in {
            cls.CI,
            cls.GITHUB,
            cls.GITLAB,
            cls.JENKINS,
            cls.AZURE,
            cls.CIRCLECI,
            cls.BITBUCKET,
            cls.TRAVIS,
            cls.TEAMCITY,
            cls.BUILDKITE,
            cls.DRONE,
        }


class ReportThemeType(str, Enum):
    """Report visual themes."""

    LIGHT = "light"
    DARK = "dark"
    PROFESSIONAL = "professional"
    MINIMAL = "minimal"
    HIGH_CONTRAST = "high_contrast"


@dataclass
class ReporterConfig:
    """Configuration for report generation.

    This is a backend-agnostic configuration that can be
    translated to specific backend configurations.

    Attributes:
        title: Report title.
        theme: Visual theme.
        locale: Language locale code (e.g., 'en', 'ko', 'ja').
        include_samples: Include sample values in output.
        include_statistics: Include statistics section.
        include_metadata: Include report metadata.
        max_sample_values: Maximum sample values to include.
        timestamp_format: Date/time format string.
        custom_options: Backend-specific options.
    """

    title: str = "Validation Report"
    theme: ReportThemeType = ReportThemeType.PROFESSIONAL
    locale: str = "en"
    include_samples: bool = True
    include_statistics: bool = True
    include_metadata: bool = True
    max_sample_values: int = 5
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    custom_options: dict[str, Any] = field(default_factory=dict)

    def with_option(self, key: str, value: Any) -> ReporterConfig:
        """Return a new config with an additional option."""
        new_options = {**self.custom_options, key: value}
        return ReporterConfig(
            title=self.title,
            theme=self.theme,
            locale=self.locale,
            include_samples=self.include_samples,
            include_statistics=self.include_statistics,
            include_metadata=self.include_metadata,
            max_sample_values=self.max_sample_values,
            timestamp_format=self.timestamp_format,
            custom_options=new_options,
        )


@dataclass
class ValidationIssueData:
    """Backend-agnostic validation issue representation.

    This data class standardizes issue data from various sources
    (truthound, custom validators, external systems).
    """

    column: str | None
    issue_type: str
    severity: str  # low, medium, high, critical
    message: str
    count: int = 1
    expected: Any = None
    actual: Any = None
    sample_values: list[Any] | None = None
    validator_name: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "column": self.column,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "count": self.count,
        }
        if self.expected is not None:
            result["expected"] = self.expected
        if self.actual is not None:
            result["actual"] = self.actual
        if self.sample_values:
            result["sample_values"] = self.sample_values
        if self.validator_name:
            result["validator_name"] = self.validator_name
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class ValidationSummary:
    """Summary statistics for validation results."""

    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    passed: bool = True

    @property
    def has_critical(self) -> bool:
        return self.critical_issues > 0

    @property
    def has_high(self) -> bool:
        return self.high_issues > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "high_issues": self.high_issues,
            "medium_issues": self.medium_issues,
            "low_issues": self.low_issues,
            "passed": self.passed,
            "has_critical": self.has_critical,
            "has_high": self.has_high,
        }


@dataclass
class DataStatistics:
    """Data statistics for reports."""

    row_count: int | None = None
    column_count: int | None = None
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class ReportData:
    """Backend-agnostic data container for report generation.

    This data class serves as the standardized input for all reporters,
    regardless of the original data source (truthound, database, etc.).

    Attributes:
        validation_id: Unique identifier for the validation run.
        source_id: Data source identifier.
        source_name: Human-readable source name.
        issues: List of validation issues.
        summary: Validation summary statistics.
        statistics: Data statistics.
        status: Validation status string.
        error_message: Error message if validation failed.
        metadata: Additional metadata.
        raw_data: Original raw data (for backends that need it).
    """

    validation_id: str
    source_id: str
    source_name: str | None = None
    issues: list[ValidationIssueData] = field(default_factory=list)
    summary: ValidationSummary = field(default_factory=ValidationSummary)
    statistics: DataStatistics = field(default_factory=DataStatistics)
    status: str = "completed"
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_data: Any = None  # Original truthound Report/ValidationResult if available

    @classmethod
    def from_validation_model(cls, validation: Any) -> ReportData:
        """Create ReportData from a Validation database model.

        Args:
            validation: Validation model from database.

        Returns:
            ReportData instance.
        """
        # Extract issues from result_json
        issues = []
        if validation.result_json and "issues" in validation.result_json:
            for issue_dict in validation.result_json["issues"]:
                issues.append(
                    ValidationIssueData(
                        column=issue_dict.get("column"),
                        issue_type=issue_dict.get("issue_type", "unknown"),
                        severity=issue_dict.get("severity", "medium"),
                        message=issue_dict.get("message", ""),
                        count=issue_dict.get("count", 1),
                        expected=issue_dict.get("expected"),
                        actual=issue_dict.get("actual"),
                        sample_values=issue_dict.get("sample_values"),
                        validator_name=issue_dict.get("validator_name"),
                        details=issue_dict.get("details"),
                    )
                )

        # Build summary
        summary = ValidationSummary(
            total_issues=validation.total_issues or 0,
            critical_issues=validation.critical_issues or 0,
            high_issues=validation.high_issues or 0,
            medium_issues=validation.medium_issues or 0,
            low_issues=validation.low_issues or 0,
            passed=validation.passed if validation.passed is not None else True,
        )

        # Build statistics
        statistics = DataStatistics(
            row_count=validation.row_count,
            column_count=validation.column_count,
            duration_ms=validation.duration_ms,
            started_at=validation.started_at,
            completed_at=validation.completed_at,
        )

        # Get source name
        source_name = None
        if hasattr(validation, "source") and validation.source:
            source_name = validation.source.name

        return cls(
            validation_id=str(validation.id),
            source_id=str(validation.source_id),
            source_name=source_name,
            issues=issues,
            summary=summary,
            statistics=statistics,
            status=validation.status or "completed",
            error_message=validation.error_message,
            metadata={
                "created_at": validation.created_at.isoformat()
                if validation.created_at
                else None,
            },
            raw_data=validation,
        )

    @classmethod
    def from_check_result(
        cls,
        check_result: Any,
        source_id: str | None = None,
    ) -> ReportData:
        """Create ReportData from a TruthoundAdapter CheckResult.

        This enables direct report generation from validation results
        without storing them in the database first.

        Args:
            check_result: CheckResult from TruthoundAdapter.
            source_id: Optional source identifier.

        Returns:
            ReportData instance.
        """
        # Convert issues
        issues = []
        for issue_dict in check_result.issues:
            issues.append(
                ValidationIssueData(
                    column=issue_dict.get("column"),
                    issue_type=issue_dict.get("issue_type", "unknown"),
                    severity=issue_dict.get("severity", "medium"),
                    message=issue_dict.get("message", ""),
                    count=issue_dict.get("count", 1),
                    expected=issue_dict.get("expected"),
                    actual=issue_dict.get("actual"),
                    sample_values=issue_dict.get("sample_values"),
                    validator_name=issue_dict.get("validator_name"),
                    details=issue_dict.get("details"),
                )
            )

        # Build summary
        summary = ValidationSummary(
            total_issues=check_result.total_issues,
            critical_issues=check_result.critical_issues,
            high_issues=check_result.high_issues,
            medium_issues=check_result.medium_issues,
            low_issues=check_result.low_issues,
            passed=check_result.passed,
        )

        # Build statistics
        run_time = check_result.run_time
        statistics = DataStatistics(
            row_count=check_result.row_count,
            column_count=check_result.column_count,
            started_at=run_time if run_time else None,
            completed_at=datetime.now(),
        )

        # Use run_id if available, otherwise generate one
        validation_id = check_result.run_id or f"check-{id(check_result)}"

        return cls(
            validation_id=validation_id,
            source_id=source_id or check_result.source,
            source_name=check_result.source,
            issues=issues,
            summary=summary,
            statistics=statistics,
            status="passed" if check_result.passed else "failed",
            raw_data=check_result._raw_result if hasattr(check_result, "_raw_result") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "validation_id": self.validation_id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": self.summary.to_dict(),
            "statistics": self.statistics.to_dict(),
            "status": self.status,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class ReportOutput:
    """Output from report generation.

    Attributes:
        content: Generated report content (string or bytes).
        content_type: MIME type of the content.
        filename: Suggested filename for download.
        format: Report format that was used.
        size_bytes: Size of content in bytes.
        generation_time_ms: Time taken to generate in milliseconds.
        metadata: Additional metadata about the report.
    """

    content: str | bytes
    content_type: str
    filename: str
    format: ReportFormatType
    size_bytes: int = 0
    generation_time_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate size if not set."""
        if self.size_bytes == 0:
            if isinstance(self.content, str):
                self.size_bytes = len(self.content.encode("utf-8"))
            else:
                self.size_bytes = len(self.content)


# Type variable for config
ConfigT = TypeVar("ConfigT", bound=ReporterConfig)


@runtime_checkable
class ReporterProtocol(Protocol):
    """Protocol for reporter implementations.

    This protocol enables duck typing for reporters from any source.
    Implementations don't need to inherit from any base class.

    Example:
        class MyReporter:
            @property
            def format(self) -> ReportFormatType:
                return ReportFormatType.HTML

            @property
            def content_type(self) -> str:
                return "text/html"

            @property
            def file_extension(self) -> str:
                return ".html"

            async def generate(
                self,
                data: ReportData,
                config: ReporterConfig | None = None,
            ) -> ReportOutput:
                ...
    """

    @property
    def format(self) -> ReportFormatType:
        """Get the report format this reporter produces."""
        ...

    @property
    def content_type(self) -> str:
        """Get the MIME content type for this format."""
        ...

    @property
    def file_extension(self) -> str:
        """Get the file extension for this format."""
        ...

    async def generate(
        self,
        data: ReportData,
        config: ReporterConfig | None = None,
    ) -> ReportOutput:
        """Generate a report.

        Args:
            data: Standardized report data.
            config: Optional configuration.

        Returns:
            ReportOutput with generated content.
        """
        ...


class BaseReporter(ABC, Generic[ConfigT]):
    """Abstract base class for reporter implementations.

    This provides a common base for dashboard-specific reporters
    while maintaining compatibility with the ReporterProtocol.

    Subclasses should implement:
    - format (property)
    - content_type (property)
    - file_extension (property)
    - _render_content (method)

    Example:
        class MyHTMLReporter(BaseReporter[ReporterConfig]):
            @property
            def format(self) -> ReportFormatType:
                return ReportFormatType.HTML

            @property
            def content_type(self) -> str:
                return "text/html"

            @property
            def file_extension(self) -> str:
                return ".html"

            async def _render_content(
                self,
                data: ReportData,
                config: ConfigT,
            ) -> str:
                return f"<html>...</html>"
    """

    def __init__(self, default_config: ConfigT | None = None) -> None:
        """Initialize reporter.

        Args:
            default_config: Default configuration for this reporter.
        """
        self._default_config = default_config or self._create_default_config()

    @property
    @abstractmethod
    def format(self) -> ReportFormatType:
        """Get the report format this reporter produces."""
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Get the MIME content type for this format."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Get the file extension for this format."""
        ...

    def _create_default_config(self) -> ConfigT:
        """Create default configuration.

        Override in subclasses to provide format-specific defaults.
        """
        return ReporterConfig()  # type: ignore

    async def generate(
        self,
        data: ReportData,
        config: ReporterConfig | None = None,
    ) -> ReportOutput:
        """Generate a report.

        This is the main entry point (Template Method pattern).
        Subclasses implement _render_content() for format-specific logic.

        Args:
            data: Standardized report data.
            config: Optional configuration (uses default if not provided).

        Returns:
            ReportOutput with generated content.
        """
        import time

        start_time = time.time()

        # Merge with default config
        effective_config = config or self._default_config

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{timestamp}{self.file_extension}"

        # Render content
        content = await self._render_content(data, effective_config)

        generation_time_ms = int((time.time() - start_time) * 1000)

        return ReportOutput(
            content=content,
            content_type=self.content_type,
            filename=filename,
            format=self.format,
            generation_time_ms=generation_time_ms,
            metadata={
                "title": effective_config.title,
                "theme": effective_config.theme.value,
                "locale": effective_config.locale,
                "validation_id": data.validation_id,
                "source_id": data.source_id,
                "source_name": data.source_name,
            },
        )

    @abstractmethod
    async def _render_content(
        self,
        data: ReportData,
        config: ConfigT,
    ) -> str | bytes:
        """Render the report content.

        Subclasses implement this to produce format-specific output.

        Args:
            data: Report data.
            config: Reporter configuration.

        Returns:
            Rendered report content.
        """
        ...

    def _get_severity_color(self, severity: str, theme: ReportThemeType) -> str:
        """Get color for severity level based on theme.

        Args:
            severity: Severity level (critical, high, medium, low).
            theme: Current theme.

        Returns:
            CSS color value.
        """
        if theme == ReportThemeType.DARK:
            colors = {
                "critical": "#ef4444",
                "high": "#f97316",
                "medium": "#eab308",
                "low": "#3b82f6",
            }
        else:
            colors = {
                "critical": "#dc2626",
                "high": "#ea580c",
                "medium": "#ca8a04",
                "low": "#2563eb",
            }
        return colors.get(severity.lower(), "#6b7280")


@runtime_checkable
class ReporterAdapterProtocol(Protocol):
    """Protocol for reporter adapters.

    Adapters wrap external reporter implementations (e.g., truthound)
    and translate them to the ReporterProtocol interface.
    """

    def adapt(self, external_reporter: Any) -> ReporterProtocol:
        """Adapt an external reporter to the ReporterProtocol.

        Args:
            external_reporter: External reporter instance.

        Returns:
            Reporter that implements ReporterProtocol.
        """
        ...


@runtime_checkable
class ReporterFactoryProtocol(Protocol):
    """Protocol for reporter factories.

    Factories create reporter instances based on format and configuration.
    """

    def get_reporter(
        self,
        format: ReportFormatType | str,
        config: ReporterConfig | None = None,
    ) -> ReporterProtocol:
        """Get a reporter for the specified format.

        Args:
            format: Report format.
            config: Optional configuration.

        Returns:
            Reporter instance.
        """
        ...

    def get_available_formats(self) -> list[str]:
        """Get list of available format names."""
        ...

    def is_format_available(self, format: ReportFormatType | str) -> bool:
        """Check if a format is available."""
        ...
