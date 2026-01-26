"""Built-in Markdown reporter.

Generates Markdown reports for documentation without external dependencies.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..interfaces import (
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReportFormatType,
    ReportThemeType,
)


class BuiltinMarkdownReporter(BaseReporter[ReporterConfig]):
    """Built-in Markdown report generator.

    Produces Markdown reports suitable for documentation and GitHub/GitLab.
    """

    # Status emojis
    STATUS_EMOJI = {
        True: "\u2705",  # ✅
        False: "\u274c",  # ❌
        None: "\u23f3",  # ⏳
    }

    # Severity emojis
    SEVERITY_EMOJI = {
        "critical": "\U0001f534",  # 🔴
        "high": "\U0001f7e0",  # 🟠
        "medium": "\U0001f7e1",  # 🟡
        "low": "\U0001f535",  # 🔵
    }

    def __init__(
        self,
        include_toc: bool = True,
        heading_level: int = 1,
        locale: str = "en",
    ) -> None:
        """Initialize Markdown reporter.

        Args:
            include_toc: Whether to include table of contents.
            heading_level: Starting heading level (1-6).
            locale: Locale for i18n text.
        """
        super().__init__()
        self._include_toc = include_toc
        self._heading_level = heading_level
        self._locale = locale

    @property
    def format(self) -> ReportFormatType:
        return ReportFormatType.MARKDOWN

    @property
    def content_type(self) -> str:
        return "text/markdown; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".md"

    def _h(self, level: int) -> str:
        """Get heading prefix for level."""
        return "#" * min(level + self._heading_level - 1, 6)

    async def _render_content(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> str:
        """Render Markdown report content."""
        lines: list[str] = []

        # Title
        status_emoji = self.STATUS_EMOJI.get(data.summary.passed, "\u2753")
        lines.append(f"{self._h(1)} {status_emoji} {config.title}")
        lines.append("")

        # Table of contents
        if self._include_toc:
            lines.extend(self._render_toc(data, config))

        # Summary section
        lines.extend(self._render_summary(data, config))

        # Statistics section
        if config.include_statistics:
            lines.extend(self._render_statistics(data))

        # Issues section
        lines.extend(self._render_issues(data, config))

        # Footer
        lines.extend(self._render_footer(config))

        return "\n".join(lines)

    def _render_toc(self, data: ReportData, config: ReporterConfig) -> list[str]:
        """Render table of contents."""
        lines = [
            f"{self._h(2)} Table of Contents",
            "",
            "- [Summary](#summary)",
        ]
        if config.include_statistics:
            lines.append("- [Statistics](#statistics)")
        lines.append("- [Issues](#issues)")
        lines.extend(["", "---", ""])
        return lines

    def _render_summary(self, data: ReportData, config: ReporterConfig) -> list[str]:
        """Render summary section."""
        summary = data.summary
        lines = [
            f"{self._h(2)} Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Status** | {self.STATUS_EMOJI.get(summary.passed)} {'Passed' if summary.passed else 'Failed'} |",
            f"| **Source** | `{data.source_name or data.source_id}` |",
            f"| **Total Issues** | {summary.total_issues} |",
        ]

        if summary.critical_issues > 0:
            lines.append(f"| **Critical** | {self.SEVERITY_EMOJI['critical']} {summary.critical_issues} |")
        if summary.high_issues > 0:
            lines.append(f"| **High** | {self.SEVERITY_EMOJI['high']} {summary.high_issues} |")
        if summary.medium_issues > 0:
            lines.append(f"| **Medium** | {self.SEVERITY_EMOJI['medium']} {summary.medium_issues} |")
        if summary.low_issues > 0:
            lines.append(f"| **Low** | {self.SEVERITY_EMOJI['low']} {summary.low_issues} |")

        lines.extend(["", ""])
        return lines

    def _render_statistics(self, data: ReportData) -> list[str]:
        """Render statistics section."""
        stats = data.statistics
        lines = [
            f"{self._h(2)} Statistics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ]

        if stats.row_count is not None:
            lines.append(f"| Rows | {stats.row_count:,} |")
        if stats.column_count is not None:
            lines.append(f"| Columns | {stats.column_count} |")
        if stats.duration_ms is not None:
            lines.append(f"| Duration | {stats.duration_ms}ms |")
        if stats.started_at:
            lines.append(f"| Started | {stats.started_at.strftime('%Y-%m-%d %H:%M:%S')} |")
        if stats.completed_at:
            lines.append(f"| Completed | {stats.completed_at.strftime('%Y-%m-%d %H:%M:%S')} |")

        lines.extend(["", ""])
        return lines

    def _render_issues(self, data: ReportData, config: ReporterConfig) -> list[str]:
        """Render issues section."""
        lines = [
            f"{self._h(2)} Issues",
            "",
        ]

        if not data.issues:
            lines.extend([
                "> No issues found!",
                "",
            ])
            return lines

        # Group issues by severity
        by_severity: dict[str, list] = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }
        for issue in data.issues:
            severity = issue.severity.lower()
            if severity in by_severity:
                by_severity[severity].append(issue)

        # Render each severity group
        for severity in ["critical", "high", "medium", "low"]:
            issues = by_severity[severity]
            if not issues:
                continue

            emoji = self.SEVERITY_EMOJI.get(severity, "")
            lines.extend([
                f"{self._h(3)} {emoji} {severity.capitalize()} ({len(issues)})",
                "",
            ])

            for issue in issues:
                lines.append(f"- **{issue.column or 'N/A'}**: {issue.issue_type}")
                lines.append(f"  - {issue.message}")
                if issue.count > 1:
                    lines.append(f"  - Count: {issue.count}")
                if config.include_samples and issue.sample_values:
                    samples = ", ".join(f"`{v}`" for v in issue.sample_values[:config.max_sample_values])
                    lines.append(f"  - Samples: {samples}")
                lines.append("")

        return lines

    def _render_footer(self, config: ReporterConfig) -> list[str]:
        """Render footer section."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return [
            "---",
            "",
            f"*Generated at {timestamp}*",
            "",
        ]
