"""Compatibility bridge between old and new reporter APIs.

This module provides backward compatibility with the existing reporter
system while enabling gradual migration to the new interface-based
architecture.

The bridge handles:
1. Converting old Validation models to new ReportData format
2. Adapting new reporters to work with old generate_report calls
3. Providing legacy generate_report function that uses new infrastructure

Example:
    # Old style (still works)
    from truthound_dashboard.core.reporters import generate_report
    report = await generate_report(validation, format="html")

    # New style (recommended)
    from truthound_dashboard.core.reporters.factory import (
        generate_report_from_validation
    )
    output = await generate_report_from_validation(validation, format="html")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .interfaces import (
    ReportData,
    ReporterConfig,
    ReportFormatType,
    ReportOutput,
    ReportThemeType,
)

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation

logger = logging.getLogger(__name__)


class LegacyReportResult:
    """Wrapper that mimics the old ReportResult interface.

    This allows new reporters to be used with code that expects
    the old ReportResult format.
    """

    def __init__(self, output: ReportOutput, config: ReporterConfig) -> None:
        """Initialize from new ReportOutput.

        Args:
            output: New-style report output.
            config: Reporter configuration used.
        """
        self._output = output
        self._config = config

    @property
    def content(self) -> str | bytes:
        return self._output.content

    @property
    def content_type(self) -> str:
        return self._output.content_type

    @property
    def filename(self) -> str:
        return self._output.filename

    @property
    def size_bytes(self) -> int:
        return self._output.size_bytes

    @property
    def generation_time_ms(self) -> int:
        return self._output.generation_time_ms

    @property
    def metadata(self) -> "LegacyReportMetadata":
        return LegacyReportMetadata(self._output, self._config)


class LegacyReportMetadata:
    """Wrapper that mimics the old ReportMetadata interface."""

    def __init__(self, output: ReportOutput, config: ReporterConfig) -> None:
        self._output = output
        self._config = config

    @property
    def title(self) -> str:
        return self._config.title

    @property
    def generated_at(self) -> Any:
        from datetime import datetime

        return datetime.utcnow()

    @property
    def source_name(self) -> str | None:
        return self._output.metadata.get("source_name")

    @property
    def source_id(self) -> str | None:
        return self._output.metadata.get("source_id")

    @property
    def validation_id(self) -> str | None:
        return self._output.metadata.get("validation_id")

    @property
    def theme(self) -> Any:
        """Return a theme object with .value property."""
        from .base import ReportTheme

        theme_str = self._config.theme.value
        return ReportTheme(theme_str)

    @property
    def format(self) -> Any:
        """Return a format object with .value property."""
        from .base import ReportFormat

        format_str = self._output.format.value
        return ReportFormat(format_str)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "source_name": self.source_name,
            "source_id": self.source_id,
            "validation_id": self.validation_id,
            "theme": self._config.theme.value,
            "format": self._output.format.value,
        }


def convert_validation_to_report_data(validation: "Validation") -> ReportData:
    """Convert a Validation model to ReportData.

    This function bridges the old Validation model with the new
    backend-agnostic ReportData format.

    Args:
        validation: Validation model from database.

    Returns:
        ReportData instance.
    """
    return ReportData.from_validation_model(validation)


def convert_theme(theme: str | Any) -> ReportThemeType:
    """Convert theme string or old ReportTheme to new ReportThemeType.

    Args:
        theme: Theme as string or ReportTheme enum.

    Returns:
        ReportThemeType enum.
    """
    if isinstance(theme, ReportThemeType):
        return theme
    if hasattr(theme, "value"):
        theme = theme.value
    return ReportThemeType(theme)


def convert_format(format: str | Any) -> ReportFormatType:
    """Convert format string or old ReportFormat to new ReportFormatType.

    Args:
        format: Format as string or ReportFormat enum.

    Returns:
        ReportFormatType enum.
    """
    if isinstance(format, ReportFormatType):
        return format
    if hasattr(format, "value"):
        format = format.value
    return ReportFormatType.from_string(format)


async def legacy_generate_report(
    validation: "Validation",
    *,
    format: str = "html",
    theme: str = "professional",
    locale: str = "en",
    title: str | None = None,
    include_samples: bool = True,
    include_statistics: bool = True,
    custom_metadata: dict[str, Any] | None = None,
) -> LegacyReportResult:
    """Generate a report using the new infrastructure but returning old format.

    This function provides backward compatibility with existing code
    that uses the old generate_report signature.

    Args:
        validation: Validation model from database.
        format: Report format (html, json, csv, etc.).
        theme: Visual theme.
        locale: Language locale.
        title: Custom title.
        include_samples: Include sample values.
        include_statistics: Include statistics section.
        custom_metadata: Additional metadata.

    Returns:
        LegacyReportResult that mimics the old ReportResult.
    """
    from .factory import generate_report_from_validation

    # Build config
    config = ReporterConfig(
        title=title or f"Validation Report - {validation.source_id}",
        theme=convert_theme(theme),
        locale=locale,
        include_samples=include_samples,
        include_statistics=include_statistics,
        custom_options=custom_metadata or {},
    )

    # Convert format
    format_type = convert_format(format)

    # Generate using new infrastructure
    output = await generate_report_from_validation(
        validation,
        format=format_type,
        config=config,
        locale=locale,
    )

    return LegacyReportResult(output, config)


# Backward compatibility aliases
async def generate_report_compat(
    validation: "Validation",
    *,
    format: str = "html",
    theme: str = "professional",
    locale: str = "en",
    title: str | None = None,
    include_samples: bool = True,
    include_statistics: bool = True,
    custom_metadata: dict[str, Any] | None = None,
) -> LegacyReportResult:
    """Alias for legacy_generate_report for explicit compatibility usage."""
    return await legacy_generate_report(
        validation,
        format=format,
        theme=theme,
        locale=locale,
        title=title,
        include_samples=include_samples,
        include_statistics=include_statistics,
        custom_metadata=custom_metadata,
    )
