"""Reporter adapters for external backends.

This module provides adapters that wrap external reporter implementations
(e.g., truthound reporters) to conform to our ReporterProtocol interface.

The adapter pattern enables:
1. Loose coupling with external dependencies
2. Easy testing with mock implementations
3. Graceful fallback when external libraries unavailable
4. Version compatibility across truthound updates

Example:
    from truthound_dashboard.core.reporters.adapters import (
        TruthoundReporterAdapter,
        create_truthound_reporter,
    )

    # Using the factory function
    reporter = create_truthound_reporter("json")
    output = await reporter.generate(data)

    # Using the adapter directly
    from truthound.reporters import get_reporter
    th_reporter = get_reporter("json")
    adapter = TruthoundReporterAdapter(th_reporter)
    output = await adapter.generate(data)
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any, Callable

from .interfaces import (
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReporterProtocol,
    ReportFormatType,
    ReportOutput,
    ReportThemeType,
    ValidationIssueData,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Thread pool for running sync truthound reporters
_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    """Get shared thread pool executor."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


def _shutdown_executor() -> None:
    """Shutdown the executor (for testing/cleanup)."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        _executor = None


class TruthoundReporterAdapter(BaseReporter[ReporterConfig]):
    """Adapter for truthound's reporter implementations.

    This adapter wraps truthound reporters to conform to our ReporterProtocol,
    enabling seamless integration with the dashboard's report generation system.

    The adapter handles:
    1. Data conversion from ReportData to truthound's expected format
    2. Config translation between our ReporterConfig and truthound's config
    3. Async execution of synchronous truthound reporters
    4. Format and content type mapping

    Example:
        from truthound.reporters import get_reporter

        # Wrap a truthound reporter
        th_reporter = get_reporter("json")
        adapter = TruthoundReporterAdapter(th_reporter)

        # Generate report using our interface
        output = await adapter.generate(report_data)
    """

    # Mapping from truthound format names to our ReportFormatType
    FORMAT_MAPPING: dict[str, ReportFormatType] = {
        "json": ReportFormatType.JSON,
        "html": ReportFormatType.HTML,
        "csv": ReportFormatType.CSV,
        "yaml": ReportFormatType.YAML,
        "ndjson": ReportFormatType.NDJSON,
        "console": ReportFormatType.CONSOLE,
    }

    # Content type mapping
    CONTENT_TYPE_MAPPING: dict[ReportFormatType, str] = {
        ReportFormatType.JSON: "application/json; charset=utf-8",
        ReportFormatType.HTML: "text/html; charset=utf-8",
        ReportFormatType.CSV: "text/csv; charset=utf-8",
        ReportFormatType.YAML: "application/x-yaml; charset=utf-8",
        ReportFormatType.NDJSON: "application/x-ndjson; charset=utf-8",
        ReportFormatType.CONSOLE: "text/plain; charset=utf-8",
    }

    # File extension mapping
    EXTENSION_MAPPING: dict[ReportFormatType, str] = {
        ReportFormatType.JSON: ".json",
        ReportFormatType.HTML: ".html",
        ReportFormatType.CSV: ".csv",
        ReportFormatType.YAML: ".yaml",
        ReportFormatType.NDJSON: ".ndjson",
        ReportFormatType.CONSOLE: ".txt",
    }

    def __init__(
        self,
        truthound_reporter: Any,
        format_override: ReportFormatType | None = None,
    ) -> None:
        """Initialize adapter.

        Args:
            truthound_reporter: A truthound reporter instance
                (e.g., JSONReporter, HTMLReporter from truthound.reporters).
            format_override: Override the detected format. Useful when
                the truthound reporter doesn't expose format information.
        """
        super().__init__()
        self._th_reporter = truthound_reporter
        self._format_override = format_override

        # Try to detect format from truthound reporter
        self._detected_format = self._detect_format()

    def _detect_format(self) -> ReportFormatType:
        """Detect the format from the truthound reporter."""
        if self._format_override:
            return self._format_override

        # Try getting format from truthound reporter
        if hasattr(self._th_reporter, "name"):
            name = self._th_reporter.name.lower()
            if name in self.FORMAT_MAPPING:
                return self.FORMAT_MAPPING[name]

        # Try from file_extension
        if hasattr(self._th_reporter, "file_extension"):
            ext = self._th_reporter.file_extension.lower()
            for fmt, mapped_ext in self.EXTENSION_MAPPING.items():
                if ext == mapped_ext or ext == mapped_ext[1:]:
                    return fmt

        # Default to JSON
        logger.warning(
            f"Could not detect format for {type(self._th_reporter).__name__}, "
            "defaulting to JSON"
        )
        return ReportFormatType.JSON

    @property
    def format(self) -> ReportFormatType:
        """Get the report format."""
        return self._detected_format

    @property
    def content_type(self) -> str:
        """Get the MIME content type."""
        # Try to get from truthound reporter first
        if hasattr(self._th_reporter, "content_type"):
            return self._th_reporter.content_type
        return self.CONTENT_TYPE_MAPPING.get(
            self._detected_format,
            "application/octet-stream",
        )

    @property
    def file_extension(self) -> str:
        """Get the file extension."""
        # Try to get from truthound reporter first
        if hasattr(self._th_reporter, "file_extension"):
            return self._th_reporter.file_extension
        return self.EXTENSION_MAPPING.get(self._detected_format, ".txt")

    async def _render_content(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> str | bytes:
        """Render content using the truthound reporter.

        This method converts our ReportData to the format expected by
        truthound reporters and executes the rendering in a thread pool.
        """
        # Convert ReportData to format expected by truthound
        th_input = self._convert_to_truthound_input(data, config)

        # Run truthound reporter in thread pool (it's synchronous)
        loop = asyncio.get_event_loop()
        executor = _get_executor()

        try:
            # Try the new truthound API first (render method)
            if hasattr(self._th_reporter, "render"):
                func = partial(self._th_reporter.render, th_input)
                result = await loop.run_in_executor(executor, func)
                return result

            # Fall back to __call__ method
            if callable(self._th_reporter):
                func = partial(self._th_reporter, th_input)
                result = await loop.run_in_executor(executor, func)
                return result

            raise ValueError(
                f"Truthound reporter {type(self._th_reporter).__name__} "
                "does not have a render() method or is not callable"
            )

        except Exception as e:
            logger.error(f"Error rendering with truthound reporter: {e}")
            # Return a fallback output
            return self._render_fallback(data, config, str(e))

    def _convert_to_truthound_input(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> Any:
        """Convert ReportData to truthound's expected input format.

        Truthound reporters expect a ValidationResult object from
        truthound.stores.results with these attributes:
        - run_id: str
        - run_time: datetime
        - data_asset: str
        - status: ResultStatus
        - results: list[ValidatorResult]
        - statistics: ResultStatistics
        - tags: dict

        Since we don't have direct access to these, we create a
        mock object that provides the same interface.
        """
        # If raw_data is available and is a truthound Report or ValidationResult, use it
        if data.raw_data is not None:
            # Check if it looks like a ValidationResult (preferred by reporters)
            if hasattr(data.raw_data, "results") and hasattr(data.raw_data, "run_id"):
                return data.raw_data
            # Check if it looks like a truthound Report (some reporters accept this)
            if hasattr(data.raw_data, "issues") and hasattr(data.raw_data, "has_issues"):
                return data.raw_data

        # Create a mock ValidationResult object that provides the truthound interface
        return _TruthoundValidationResultMock(data, config)

    def _render_fallback(
        self,
        data: ReportData,
        config: ReporterConfig,
        error: str,
    ) -> str:
        """Render a fallback output when truthound reporter fails."""
        if self._detected_format == ReportFormatType.JSON:
            import json

            return json.dumps(
                {
                    "error": error,
                    "fallback": True,
                    "data": data.to_dict(),
                },
                indent=2,
            )
        elif self._detected_format == ReportFormatType.HTML:
            return f"""
            <html>
            <head><title>Report Error</title></head>
            <body>
            <h1>Report Generation Error</h1>
            <p>Error: {error}</p>
            <h2>Validation ID: {data.validation_id}</h2>
            <h2>Issues: {data.summary.total_issues}</h2>
            </body>
            </html>
            """
        else:
            return f"Report generation error: {error}\nValidation ID: {data.validation_id}"


class _TruthoundReportMock:
    """Mock object that mimics truthound's Report interface.

    This allows us to use truthound reporters without having
    a real truthound Report object.
    """

    def __init__(self, data: ReportData, config: ReporterConfig) -> None:
        self._data = data
        self._config = config

        # Convert issues to mock ValidationIssue objects
        self._issues = [
            _MockValidationIssue(issue) for issue in data.issues
        ]

    @property
    def issues(self) -> list[_MockValidationIssue]:
        return self._issues

    @property
    def source(self) -> str:
        return self._data.source_name or self._data.source_id

    @property
    def row_count(self) -> int:
        return self._data.statistics.row_count or 0

    @property
    def column_count(self) -> int:
        return self._data.statistics.column_count or 0

    @property
    def has_issues(self) -> bool:
        return self._data.summary.total_issues > 0

    @property
    def has_critical(self) -> bool:
        return self._data.summary.has_critical

    @property
    def has_high(self) -> bool:
        return self._data.summary.has_high

    def to_json(self, indent: int | None = 2) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self._data.to_dict(), indent=indent)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self._data.to_dict()


class _MockValidationIssue:
    """Mock ValidationIssue for truthound reporters."""

    def __init__(self, issue: ValidationIssueData) -> None:
        self._issue = issue

    @property
    def column(self) -> str | None:
        return self._issue.column

    @property
    def issue_type(self) -> str:
        return self._issue.issue_type

    @property
    def severity(self) -> _MockSeverity:
        return _MockSeverity(self._issue.severity)

    @property
    def message(self) -> str:
        return self._issue.message

    @property
    def count(self) -> int:
        return self._issue.count

    @property
    def expected(self) -> Any:
        return self._issue.expected

    @property
    def actual(self) -> Any:
        return self._issue.actual

    @property
    def details(self) -> dict[str, Any] | None:
        return self._issue.details


class _MockSeverity:
    """Mock Severity enum for truthound reporters."""

    def __init__(self, value: str) -> None:
        self._value = value.lower()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class _TruthoundValidationResultMock:
    """Mock object that mimics truthound's ValidationResult interface.

    Truthound reporters expect ValidationResult which has:
    - run_id: str
    - run_time: datetime
    - data_asset: str
    - status: ResultStatus
    - results: list[ValidatorResult]
    - statistics: ResultStatistics
    - tags: dict
    - success: bool
    """

    def __init__(self, data: ReportData, config: ReporterConfig) -> None:
        from datetime import datetime as dt

        self._data = data
        self._config = config

        # Convert issues to mock ValidatorResult objects
        self._results = [
            _MockValidatorResult(issue) for issue in data.issues
        ]
        self._statistics = _MockResultStatistics(data)

    @property
    def run_id(self) -> str:
        return self._data.validation_id

    @property
    def run_time(self) -> Any:
        from datetime import datetime as dt

        if self._data.statistics.started_at:
            return self._data.statistics.started_at
        return dt.utcnow()

    @property
    def data_asset(self) -> str:
        return self._data.source_name or self._data.source_id

    @property
    def status(self) -> _MockResultStatus:
        return _MockResultStatus(self._data.summary.passed)

    @property
    def success(self) -> bool:
        """Whether the validation passed."""
        return self._data.summary.passed

    @property
    def results(self) -> list[_MockValidatorResult]:
        return self._results

    @property
    def statistics(self) -> _MockResultStatistics:
        return self._statistics

    @property
    def tags(self) -> dict[str, Any]:
        return self._data.metadata

    # Additional properties that truthound reporters might expect
    @property
    def suite_name(self) -> str:
        """Test suite name for JUnit-style reporters."""
        return self._config.title or "Truthound Validation"

    @property
    def source(self) -> str:
        """Alias for data_asset."""
        return self.data_asset

    @property
    def row_count(self) -> int:
        """Row count for Report-style access."""
        return self._data.statistics.row_count or 0

    @property
    def column_count(self) -> int:
        """Column count for Report-style access."""
        return self._data.statistics.column_count or 0

    @property
    def issues(self) -> list[_MockValidatorResult]:
        """Alias for results (Report-style access)."""
        return self._results

    @property
    def has_issues(self) -> bool:
        """Report-style check for issues."""
        return self._data.summary.total_issues > 0

    @property
    def has_critical(self) -> bool:
        """Report-style check for critical issues."""
        return self._data.summary.has_critical

    @property
    def has_high(self) -> bool:
        """Report-style check for high severity issues."""
        return self._data.summary.has_high

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "run_time": self.run_time.isoformat() if hasattr(self.run_time, 'isoformat') else str(self.run_time),
            "data_asset": self.data_asset,
            "status": self.status.value,
            "success": self.success,
            "results": [r.to_dict() for r in self.results],
            "statistics": self.statistics.to_dict(),
            "tags": self.tags,
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Convert to JSON string (Report-style)."""
        import json

        return json.dumps(self.to_dict(), indent=indent, default=str)


class _MockResultStatus:
    """Mock ResultStatus enum."""

    def __init__(self, passed: bool) -> None:
        self._passed = passed

    @property
    def value(self) -> str:
        return "SUCCESS" if self._passed else "FAILURE"

    def __str__(self) -> str:
        return self.value


class _MockResultStatistics:
    """Mock ResultStatistics object."""

    def __init__(self, data: ReportData) -> None:
        self._data = data

    @property
    def total_issues(self) -> int:
        return self._data.summary.total_issues

    @property
    def total_rows(self) -> int:
        return self._data.statistics.row_count or 0

    @property
    def total_columns(self) -> int:
        return self._data.statistics.column_count or 0

    @property
    def critical_count(self) -> int:
        return self._data.summary.critical_issues

    @property
    def high_count(self) -> int:
        return self._data.summary.high_issues

    @property
    def medium_count(self) -> int:
        return self._data.summary.medium_issues

    @property
    def low_count(self) -> int:
        return self._data.summary.low_issues

    @property
    def passed(self) -> bool:
        return self._data.summary.passed

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


class _MockValidatorResult:
    """Mock ValidatorResult object."""

    def __init__(self, issue: ValidationIssueData) -> None:
        self._issue = issue

    @property
    def validator_name(self) -> str:
        return self._issue.validator_name or self._issue.issue_type

    @property
    def column(self) -> str | None:
        return self._issue.column

    @property
    def issue_type(self) -> str:
        return self._issue.issue_type

    @property
    def severity(self) -> _MockSeverity:
        return _MockSeverity(self._issue.severity)

    @property
    def message(self) -> str:
        return self._issue.message

    @property
    def count(self) -> int:
        return self._issue.count

    @property
    def success(self) -> bool:
        return False  # All issues are failures

    @property
    def expected(self) -> Any:
        return self._issue.expected

    @property
    def actual(self) -> Any:
        return self._issue.actual

    @property
    def details(self) -> dict[str, Any]:
        return self._issue.details or {}

    @property
    def sample_values(self) -> list[Any]:
        return self._issue.sample_values or []

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


def create_truthound_reporter(
    format_name: str,
    locale: str = "en",
    **config_options: Any,
) -> TruthoundReporterAdapter | None:
    """Factory function to create a truthound reporter adapter.

    This function attempts to import and instantiate a truthound reporter,
    returning None if truthound is not available.

    Args:
        format_name: Format name (e.g., 'json', 'html', 'markdown').
        locale: Locale for i18n (e.g., 'en', 'ko', 'ja').
        **config_options: Additional configuration passed to truthound reporter.

    Returns:
        TruthoundReporterAdapter or None if truthound unavailable.

    Example:
        reporter = create_truthound_reporter("json")
        if reporter:
            output = await reporter.generate(data)
    """
    try:
        from truthound.reporters import get_reporter

        # Get truthound reporter with locale support
        try:
            th_reporter = get_reporter(format_name, locale=locale, **config_options)
        except TypeError:
            # Fallback for reporters without locale support
            th_reporter = get_reporter(format_name, **config_options)

        return TruthoundReporterAdapter(th_reporter)

    except ImportError:
        logger.warning(
            f"truthound.reporters not available, cannot create {format_name} reporter"
        )
        return None
    except ValueError as e:
        logger.warning(f"Failed to create truthound reporter for {format_name}: {e}")
        return None


def is_truthound_available() -> bool:
    """Check if truthound reporters are available.

    Returns:
        True if truthound.reporters can be imported.
    """
    try:
        from truthound.reporters import get_reporter  # noqa: F401

        return True
    except ImportError:
        return False


def get_truthound_formats() -> list[str]:
    """Get list of available truthound report formats.

    Returns:
        List of format names available in truthound, or empty list if
        truthound is not available.
    """
    try:
        from truthound.reporters.factory import list_available_formats

        return list_available_formats()
    except ImportError:
        return []


def create_ci_reporter(
    platform: str | None = None,
    **config_options: Any,
) -> TruthoundReporterAdapter | None:
    """Create a CI platform reporter adapter.

    This function creates a reporter for CI/CD platforms. If no platform
    is specified, it attempts to auto-detect the current CI environment.

    Supported platforms:
    - github: GitHub Actions (::error::, ::warning::, step summary)
    - gitlab: GitLab CI (section markers, ANSI colors)
    - jenkins: Jenkins (JUnit XML compatible)
    - azure: Azure DevOps (##vso commands)
    - circleci: CircleCI
    - bitbucket: Bitbucket Pipelines
    - travis: Travis CI
    - teamcity: TeamCity (service messages)
    - buildkite: Buildkite (annotations)
    - drone: Drone CI

    Args:
        platform: CI platform name, or None for auto-detection.
        **config_options: Additional configuration passed to truthound reporter.

    Returns:
        TruthoundReporterAdapter for the CI platform, or None if unavailable.

    Example:
        # Auto-detect CI platform
        reporter = create_ci_reporter()

        # Specific platform
        reporter = create_ci_reporter("github")
    """
    try:
        # Try to auto-detect if no platform specified
        if platform is None:
            from truthound.checkpoint.ci import detect_ci_platform

            detected = detect_ci_platform()
            if detected:
                platform = detected.value.lower()
            else:
                logger.debug("No CI platform detected")
                return None
        else:
            platform = platform.lower()

        # Try new CI reporters API
        try:
            from truthound.reporters.ci import get_ci_reporter

            ci_reporter = get_ci_reporter(platform, **config_options)
            return TruthoundReporterAdapter(
                ci_reporter,
                format_override=_get_ci_format_type(platform),
            )
        except (ImportError, AttributeError):
            pass

        # Fallback: Try the generic CI reporter factory
        try:
            from truthound.reporters import get_reporter

            ci_reporter = get_reporter(platform, **config_options)
            return TruthoundReporterAdapter(
                ci_reporter,
                format_override=_get_ci_format_type(platform),
            )
        except ValueError:
            logger.warning(f"CI reporter for {platform} not available")
            return None

    except ImportError:
        logger.warning("truthound CI reporters not available")
        return None


def _get_ci_format_type(platform: str) -> ReportFormatType:
    """Map CI platform name to ReportFormatType."""
    platform_lower = platform.lower()
    mapping = {
        "github": ReportFormatType.GITHUB,
        "gitlab": ReportFormatType.GITLAB,
        "jenkins": ReportFormatType.JENKINS,
        "azure": ReportFormatType.AZURE,
        "circleci": ReportFormatType.CIRCLECI,
        "bitbucket": ReportFormatType.BITBUCKET,
        "travis": ReportFormatType.TRAVIS,
        "teamcity": ReportFormatType.TEAMCITY,
        "buildkite": ReportFormatType.BUILDKITE,
        "drone": ReportFormatType.DRONE,
    }
    return mapping.get(platform_lower, ReportFormatType.CI)


def is_ci_environment() -> bool:
    """Check if running in a CI environment.

    Returns:
        True if a CI environment is detected.
    """
    try:
        from truthound.checkpoint.ci import is_ci_environment as _is_ci

        return _is_ci()
    except ImportError:
        # Fallback: check common CI environment variables
        import os

        ci_vars = [
            "CI",
            "GITHUB_ACTIONS",
            "GITLAB_CI",
            "JENKINS_URL",
            "CIRCLECI",
            "BITBUCKET_BUILD_NUMBER",
            "TRAVIS",
            "TEAMCITY_VERSION",
            "BUILDKITE",
            "DRONE",
            "TF_BUILD",  # Azure DevOps
            "CODEBUILD_BUILD_ID",  # AWS CodeBuild
        ]
        return any(os.environ.get(var) for var in ci_vars)


def get_detected_ci_platform() -> str | None:
    """Detect the current CI platform.

    Returns:
        Platform name string or None if not in CI.
    """
    try:
        from truthound.checkpoint.ci import detect_ci_platform

        platform = detect_ci_platform()
        return platform.value.lower() if platform else None
    except ImportError:
        # Fallback detection
        import os

        if os.environ.get("GITHUB_ACTIONS"):
            return "github"
        if os.environ.get("GITLAB_CI"):
            return "gitlab"
        if os.environ.get("JENKINS_URL"):
            return "jenkins"
        if os.environ.get("TF_BUILD"):
            return "azure"
        if os.environ.get("CIRCLECI"):
            return "circleci"
        if os.environ.get("BITBUCKET_BUILD_NUMBER"):
            return "bitbucket"
        if os.environ.get("TRAVIS"):
            return "travis"
        if os.environ.get("TEAMCITY_VERSION"):
            return "teamcity"
        if os.environ.get("BUILDKITE"):
            return "buildkite"
        if os.environ.get("DRONE"):
            return "drone"
        return None


class ValidationModelAdapter:
    """Adapter for converting database Validation models to ReportData.

    This adapter handles the conversion from our SQLAlchemy Validation
    model to the backend-agnostic ReportData format.

    Example:
        validation = await service.get_validation(validation_id)
        data = ValidationModelAdapter.to_report_data(validation)
        output = await reporter.generate(data)
    """

    @staticmethod
    def to_report_data(validation: Any) -> ReportData:
        """Convert a Validation model to ReportData.

        Args:
            validation: Validation model from database.

        Returns:
            ReportData instance.
        """
        return ReportData.from_validation_model(validation)

    @staticmethod
    def to_truthound_result(validation: Any) -> Any:
        """Convert a Validation model to a truthound-compatible result.

        This is useful when you need to use truthound reporters directly
        without going through our adapter.

        Args:
            validation: Validation model from database.

        Returns:
            Object that mimics truthound's ValidationResult interface.
        """
        data = ReportData.from_validation_model(validation)
        return _TruthoundReportMock(data, ReporterConfig())
