"""Reporter interfaces for validation result reporting.

Reporters generate formatted reports from validation results.
They support multiple output formats (HTML, CSV, JSON)
and can be customized for different use cases.

This module defines abstract interfaces for reporters that are loosely
coupled from truthound's reporters module.

Reporter features:
- Multiple output formats
- Template-based customization
- Localization support
- Custom reporter plugins
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    from truthound_dashboard.core.interfaces.checkpoint import CheckpointResult


class ReportFormat(str, Enum):
    """Supported report formats."""

    HTML = "html"
    CSV = "csv"
    JSON = "json"
    SLACK = "slack"  # Slack-formatted blocks
    TEXT = "text"


@dataclass
class ReporterConfig:
    """Configuration for report generation.

    Attributes:
        format: Output format.
        template: Template name or path.
        locale: Locale for localization.
        title: Report title.
        description: Report description.
        include_summary: Include summary section.
        include_issues: Include issues detail.
        include_statistics: Include statistics.
        include_charts: Include visualizations.
        max_issues: Maximum issues to include.
        output_path: Path for file output.
        metadata: Additional metadata.
    """

    format: ReportFormat = ReportFormat.HTML
    template: str | None = None
    locale: str = "en"
    title: str = "Validation Report"
    description: str = ""
    include_summary: bool = True
    include_issues: bool = True
    include_statistics: bool = True
    include_charts: bool = True
    max_issues: int = 1000
    output_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "format": self.format.value,
            "template": self.template,
            "locale": self.locale,
            "title": self.title,
            "description": self.description,
            "include_summary": self.include_summary,
            "include_issues": self.include_issues,
            "include_statistics": self.include_statistics,
            "include_charts": self.include_charts,
            "max_issues": self.max_issues,
            "output_path": self.output_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReporterConfig":
        """Create from dictionary."""
        format_str = data.get("format", "html")
        if isinstance(format_str, str):
            format_enum = ReportFormat(format_str)
        else:
            format_enum = format_str

        return cls(
            format=format_enum,
            template=data.get("template"),
            locale=data.get("locale", "en"),
            title=data.get("title", "Validation Report"),
            description=data.get("description", ""),
            include_summary=data.get("include_summary", True),
            include_issues=data.get("include_issues", True),
            include_statistics=data.get("include_statistics", True),
            include_charts=data.get("include_charts", True),
            max_issues=data.get("max_issues", 1000),
            output_path=data.get("output_path"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ReportData:
    """Data container for report generation.

    This is the standardized input for reporters, decoupled from
    any specific validation result format.

    Attributes:
        run_id: Validation run identifier.
        checkpoint_name: Checkpoint name.
        source_name: Data source name.
        status: Validation status.
        generated_at: Report generation time.
        validation_started_at: When validation started.
        validation_completed_at: When validation completed.
        duration_ms: Validation duration.
        row_count: Number of rows validated.
        column_count: Number of columns.
        issue_count: Total issues found.
        critical_count: Critical issues.
        high_count: High severity issues.
        medium_count: Medium severity issues.
        low_count: Low severity issues.
        issues: List of issue dictionaries.
        summary: Summary statistics.
        metadata: Additional metadata.
    """

    run_id: str
    checkpoint_name: str
    source_name: str
    status: str
    generated_at: datetime = field(default_factory=datetime.now)
    validation_started_at: datetime | None = None
    validation_completed_at: datetime | None = None
    duration_ms: float = 0.0
    row_count: int = 0
    column_count: int = 0
    issue_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    issues: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "checkpoint_name": self.checkpoint_name,
            "source_name": self.source_name,
            "status": self.status,
            "generated_at": self.generated_at.isoformat(),
            "validation_started_at": (
                self.validation_started_at.isoformat()
                if self.validation_started_at else None
            ),
            "validation_completed_at": (
                self.validation_completed_at.isoformat()
                if self.validation_completed_at else None
            ),
            "duration_ms": self.duration_ms,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "issue_count": self.issue_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "issues": self.issues,
            "summary": self.summary,
            "metadata": self.metadata,
        }

    @classmethod
    def from_checkpoint_result(
        cls,
        result: "CheckpointResult",
    ) -> "ReportData":
        """Create from a checkpoint result.

        Args:
            result: Checkpoint result.

        Returns:
            ReportData instance.
        """
        # Build summary
        summary = {
            "total_issues": result.issue_count,
            "by_severity": {
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
            },
            "pass_rate": (
                1 - (result.issue_count / result.row_count)
                if result.row_count > 0 else 1.0
            ),
        }

        return cls(
            run_id=result.run_id,
            checkpoint_name=result.checkpoint_name,
            source_name=result.source_name,
            status=result.status.value,
            validation_started_at=result.started_at,
            validation_completed_at=result.completed_at,
            duration_ms=result.duration_ms,
            row_count=result.row_count,
            column_count=result.column_count,
            issue_count=result.issue_count,
            critical_count=result.critical_count,
            high_count=result.high_count,
            medium_count=result.medium_count,
            low_count=result.low_count,
            issues=result.issues,
            summary=summary,
            metadata=result.metadata,
        )


@dataclass
class ReportOutput:
    """Output from report generation.

    Attributes:
        format: Output format.
        content: Report content (string for text formats, bytes for binary).
        file_path: Path to output file (if saved).
        mime_type: MIME type of the output.
        size_bytes: Size in bytes.
        generated_at: When report was generated.
        metadata: Additional output metadata.
    """

    format: ReportFormat
    content: str | bytes
    file_path: str | None = None
    mime_type: str = "text/html"
    size_bytes: int = 0
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate size if not set."""
        if self.size_bytes == 0:
            if isinstance(self.content, bytes):
                self.size_bytes = len(self.content)
            else:
                self.size_bytes = len(self.content.encode("utf-8"))

    def save(self, path: str | Path) -> str:
        """Save report content to file.

        Args:
            path: Output path.

        Returns:
            Absolute path to saved file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(self.content, bytes):
            path.write_bytes(self.content)
        else:
            path.write_text(self.content, encoding="utf-8")

        self.file_path = str(path.absolute())
        return self.file_path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (without content)."""
        return {
            "format": self.format.value,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }


@runtime_checkable
class ReporterProtocol(Protocol):
    """Protocol for reporter implementations.

    Reporters generate formatted reports from validation data.

    Example:
        class HTMLReporter:
            def generate(self, data: ReportData, config: ReporterConfig) -> ReportOutput:
                html = render_template(data, config)
                return ReportOutput(format=ReportFormat.HTML, content=html)
    """

    @property
    def name(self) -> str:
        """Get reporter name."""
        ...

    @property
    def supported_formats(self) -> list[ReportFormat]:
        """Get supported output formats."""
        ...

    def generate(
        self,
        data: ReportData,
        config: ReporterConfig | None = None,
    ) -> ReportOutput:
        """Generate a report synchronously.

        Args:
            data: Report data.
            config: Report configuration.

        Returns:
            Report output.
        """
        ...


@runtime_checkable
class AsyncReporterProtocol(Protocol):
    """Protocol for async reporter implementations."""

    @property
    def name(self) -> str:
        """Get reporter name."""
        ...

    @property
    def supported_formats(self) -> list[ReportFormat]:
        """Get supported output formats."""
        ...

    async def generate_async(
        self,
        data: ReportData,
        config: ReporterConfig | None = None,
    ) -> ReportOutput:
        """Generate a report asynchronously.

        Args:
            data: Report data.
            config: Report configuration.

        Returns:
            Report output.
        """
        ...


class BaseReporter(ABC):
    """Abstract base class for reporters.

    Provides common functionality for all reporters.
    Subclasses must implement the _do_generate method.
    """

    def __init__(
        self,
        name: str | None = None,
        default_config: ReporterConfig | None = None,
    ) -> None:
        """Initialize reporter.

        Args:
            name: Reporter name.
            default_config: Default configuration.
        """
        self._name = name or self.__class__.__name__
        self._default_config = default_config or ReporterConfig()

    @property
    def name(self) -> str:
        """Get reporter name."""
        return self._name

    @property
    @abstractmethod
    def supported_formats(self) -> list[ReportFormat]:
        """Get supported output formats."""
        ...

    def generate(
        self,
        data: ReportData,
        config: ReporterConfig | None = None,
    ) -> ReportOutput:
        """Generate a report.

        Args:
            data: Report data.
            config: Report configuration.

        Returns:
            Report output.
        """
        config = config or self._default_config

        # Validate format
        if config.format not in self.supported_formats:
            raise ValueError(
                f"Format {config.format} not supported by {self.name}. "
                f"Supported: {[f.value for f in self.supported_formats]}"
            )

        output = self._do_generate(data, config)

        # Save to file if path specified
        if config.output_path:
            output.save(config.output_path)

        return output

    @abstractmethod
    def _do_generate(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> ReportOutput:
        """Perform the actual report generation.

        Subclasses must implement this method.

        Args:
            data: Report data.
            config: Report configuration.

        Returns:
            Report output.
        """
        ...


class AsyncBaseReporter(ABC):
    """Abstract base class for async reporters."""

    def __init__(
        self,
        name: str | None = None,
        default_config: ReporterConfig | None = None,
    ) -> None:
        """Initialize reporter."""
        self._name = name or self.__class__.__name__
        self._default_config = default_config or ReporterConfig()

    @property
    def name(self) -> str:
        """Get reporter name."""
        return self._name

    @property
    @abstractmethod
    def supported_formats(self) -> list[ReportFormat]:
        """Get supported output formats."""
        ...

    async def generate_async(
        self,
        data: ReportData,
        config: ReporterConfig | None = None,
    ) -> ReportOutput:
        """Generate a report asynchronously."""
        config = config or self._default_config

        if config.format not in self.supported_formats:
            raise ValueError(
                f"Format {config.format} not supported by {self.name}"
            )

        output = await self._do_generate_async(data, config)

        if config.output_path:
            output.save(config.output_path)

        return output

    @abstractmethod
    async def _do_generate_async(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> ReportOutput:
        """Perform the actual async report generation."""
        ...


# =============================================================================
# Reporter Registry
# =============================================================================


class ReporterRegistry:
    """Registry for reporter types.

    Manages reporter registration and access.

    Example:
        registry = ReporterRegistry()
        registry.register("html", HTMLReporter())
        registry.register("pdf", PDFReporter())

        reporter = registry.get("html")
        output = reporter.generate(data, config)
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._reporters: dict[str, BaseReporter | AsyncBaseReporter] = {}
        self._factories: dict[str, Callable[..., BaseReporter | AsyncBaseReporter]] = {}

    def register(
        self,
        name: str,
        reporter: BaseReporter | AsyncBaseReporter,
    ) -> None:
        """Register a reporter instance.

        Args:
            name: Reporter name.
            reporter: Reporter instance.
        """
        self._reporters[name] = reporter

    def register_factory(
        self,
        name: str,
        factory: Callable[..., BaseReporter | AsyncBaseReporter],
    ) -> None:
        """Register a reporter factory.

        Args:
            name: Reporter name.
            factory: Factory function.
        """
        self._factories[name] = factory

    def get(self, name: str) -> BaseReporter | AsyncBaseReporter | None:
        """Get a reporter by name.

        Args:
            name: Reporter name.

        Returns:
            Reporter or None if not found.
        """
        return self._reporters.get(name)

    def create(
        self,
        name: str,
        **kwargs: Any,
    ) -> BaseReporter | AsyncBaseReporter:
        """Create a reporter using a factory.

        Args:
            name: Reporter name.
            **kwargs: Factory arguments.

        Returns:
            Reporter instance.

        Raises:
            KeyError: If factory not found.
        """
        if name not in self._factories:
            raise KeyError(f"Reporter factory not found: {name}")
        return self._factories[name](**kwargs)

    def list_reporters(self) -> list[str]:
        """List all registered reporter names.

        Returns:
            List of reporter names.
        """
        return list(set(self._reporters.keys()) | set(self._factories.keys()))

    def has_reporter(self, name: str) -> bool:
        """Check if a reporter is registered.

        Args:
            name: Reporter name.

        Returns:
            True if reporter is registered.
        """
        return name in self._reporters or name in self._factories

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported formats for all reporters.

        Returns:
            Dictionary mapping reporter names to supported formats.
        """
        result = {}
        for name, reporter in self._reporters.items():
            result[name] = [f.value for f in reporter.supported_formats]
        return result


# Global reporter registry
_reporter_registry: ReporterRegistry | None = None


def get_reporter_registry() -> ReporterRegistry:
    """Get the global reporter registry.

    Returns:
        Global ReporterRegistry instance.
    """
    global _reporter_registry
    if _reporter_registry is None:
        _reporter_registry = ReporterRegistry()
    return _reporter_registry


def register_reporter(name: str) -> Callable[[type], type]:
    """Decorator to register a reporter class.

    Example:
        @register_reporter("my_custom")
        class MyCustomReporter(BaseReporter):
            ...
    """

    def decorator(cls: type) -> type:
        get_reporter_registry().register_factory(name, cls)
        return cls

    return decorator
