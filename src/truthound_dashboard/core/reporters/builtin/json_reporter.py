"""Built-in JSON reporter.

Generates machine-readable JSON reports without external dependencies.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..interfaces import (
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReportFormatType,
)


class BuiltinJSONReporter(BaseReporter[ReporterConfig]):
    """Built-in JSON report generator.

    Produces structured JSON reports with complete validation data.
    This is a fallback when truthound's JSONReporter is not available.
    """

    def __init__(
        self,
        indent: int | None = 2,
        ensure_ascii: bool = False,
        locale: str = "en",
    ) -> None:
        """Initialize JSON reporter.

        Args:
            indent: Indentation for pretty printing. None for compact output.
            ensure_ascii: Whether to escape non-ASCII characters.
            locale: Locale (not used for JSON, but kept for interface consistency).
        """
        super().__init__()
        self._indent = indent
        self._ensure_ascii = ensure_ascii
        self._locale = locale

    @property
    def format(self) -> ReportFormatType:
        return ReportFormatType.JSON

    @property
    def content_type(self) -> str:
        return "application/json; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".json"

    async def _render_content(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> str:
        """Render JSON report content."""
        # Process issues
        issues = []
        for issue in data.issues:
            issue_dict = issue.to_dict()
            # Remove sample values if not requested
            if not config.include_samples:
                issue_dict.pop("sample_values", None)
            issues.append(issue_dict)

        report_data: dict[str, Any] = {
            "metadata": {
                "title": config.title,
                "generated_at": datetime.utcnow().isoformat(),
                "format": self.format.value,
                "theme": config.theme.value,
                "locale": config.locale,
            },
            "validation": {
                "id": data.validation_id,
                "source_id": data.source_id,
                "source_name": data.source_name,
                "status": data.status,
                "passed": data.summary.passed,
            },
            "summary": data.summary.to_dict(),
            "issues": issues,
        }

        # Add statistics if requested
        if config.include_statistics:
            report_data["statistics"] = data.statistics.to_dict()

        # Add error info if present
        if data.error_message:
            report_data["error"] = {
                "message": data.error_message,
            }

        # Add custom metadata
        if config.include_metadata and data.metadata:
            report_data["metadata"].update(data.metadata)

        return json.dumps(
            report_data,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii,
            default=self._json_serializer,
        )

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class CompactJSONReporter(BuiltinJSONReporter):
    """Compact JSON reporter without formatting."""

    def __init__(self, locale: str = "en") -> None:
        super().__init__(indent=None, ensure_ascii=False, locale=locale)
