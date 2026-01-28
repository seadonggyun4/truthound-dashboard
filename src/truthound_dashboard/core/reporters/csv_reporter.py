"""CSV report generator.

Generates CSV reports suitable for data analysis and spreadsheet tools.
"""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class CSVReporter(Reporter):
    """CSV report generator.

    Produces CSV files with validation issues and statistics.
    Supports customizable delimiters and encoding.
    """

    def __init__(
        self,
        delimiter: str = ",",
        include_header: bool = True,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize CSV reporter.

        Args:
            delimiter: CSV delimiter character.
            include_header: Whether to include column headers.
            encoding: Output encoding.
        """
        self._delimiter = delimiter
        self._include_header = include_header
        self._encoding = encoding

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.CSV

    @property
    def content_type(self) -> str:
        return f"text/csv; charset={self._encoding}"

    @property
    def file_extension(self) -> str:
        return ".csv"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render CSV report content."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self._delimiter)

        # Write issues section (main data)
        issues = self._extract_issues(validation)

        # Define headers based on options
        headers = ["Column", "Issue Type", "Severity", "Count", "Details"]
        if include_samples:
            headers.append("Sample Values")

        if self._include_header:
            writer.writerow(headers)

        # Write issue rows
        for issue in issues:
            row = [
                issue.get("column", ""),
                issue.get("issue_type", ""),
                issue.get("severity", ""),
                issue.get("count", 0),
                issue.get("details", "") or "",
            ]
            if include_samples:
                samples = issue.get("sample_values") or []
                samples_str = "; ".join(str(v)[:50] for v in samples[:5])
                row.append(samples_str)

            writer.writerow(row)

        return output.getvalue()


class ExcelCSVReporter(CSVReporter):
    """CSV reporter optimized for Microsoft Excel.

    Uses UTF-8 BOM for proper encoding detection and semicolon delimiter
    for better compatibility with Excel's regional settings.
    """

    def __init__(self) -> None:
        """Initialize Excel-optimized CSV reporter."""
        super().__init__(delimiter=";", include_header=True, encoding="utf-8-sig")

    @property
    def file_extension(self) -> str:
        return ".csv"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render CSV with BOM for Excel."""
        content = await super()._render_content(
            validation, metadata, include_samples, include_statistics
        )
        # Add UTF-8 BOM for Excel
        return "\ufeff" + content
