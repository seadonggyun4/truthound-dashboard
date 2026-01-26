"""Built-in CSV reporter.

Generates CSV reports for spreadsheet analysis without external dependencies.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from ..interfaces import (
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReportFormatType,
)


class BuiltinCSVReporter(BaseReporter[ReporterConfig]):
    """Built-in CSV report generator.

    Produces CSV reports suitable for spreadsheet analysis.
    Each row represents one validation issue.
    """

    def __init__(
        self,
        delimiter: str = ",",
        quotechar: str = '"',
        include_header: bool = True,
    ) -> None:
        """Initialize CSV reporter.

        Args:
            delimiter: Field delimiter character.
            quotechar: Quote character for strings.
            include_header: Whether to include header row.
        """
        super().__init__()
        self._delimiter = delimiter
        self._quotechar = quotechar
        self._include_header = include_header

    @property
    def format(self) -> ReportFormatType:
        return ReportFormatType.CSV

    @property
    def content_type(self) -> str:
        return "text/csv; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".csv"

    async def _render_content(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> str:
        """Render CSV report content."""
        output = io.StringIO()
        writer = csv.writer(
            output,
            delimiter=self._delimiter,
            quotechar=self._quotechar,
            quoting=csv.QUOTE_MINIMAL,
        )

        # Define columns
        columns = [
            "validation_id",
            "source_id",
            "column",
            "issue_type",
            "severity",
            "message",
            "count",
            "validator_name",
        ]

        if config.include_samples:
            columns.append("sample_values")

        # Write header
        if self._include_header:
            writer.writerow(columns)

        # Write issues
        for issue in data.issues:
            row = [
                data.validation_id,
                data.source_id,
                issue.column or "",
                issue.issue_type,
                issue.severity,
                issue.message,
                str(issue.count),
                issue.validator_name or "",
            ]

            if config.include_samples:
                samples = ""
                if issue.sample_values:
                    samples = "; ".join(str(v) for v in issue.sample_values[:config.max_sample_values])
                row.append(samples)

            writer.writerow(row)

        return output.getvalue()
