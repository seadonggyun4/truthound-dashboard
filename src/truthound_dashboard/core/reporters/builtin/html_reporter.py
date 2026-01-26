"""Built-in HTML reporter.

Generates HTML reports with embedded CSS without external dependencies.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

from ..interfaces import (
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReportFormatType,
    ReportThemeType,
)


class BuiltinHTMLReporter(BaseReporter[ReporterConfig]):
    """Built-in HTML report generator.

    Produces self-contained HTML reports with embedded CSS styling.
    Supports light, dark, and professional themes.
    """

    def __init__(self, locale: str = "en") -> None:
        """Initialize HTML reporter.

        Args:
            locale: Locale for i18n text.
        """
        super().__init__()
        self._locale = locale

    @property
    def format(self) -> ReportFormatType:
        return ReportFormatType.HTML

    @property
    def content_type(self) -> str:
        return "text/html; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".html"

    async def _render_content(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> str:
        """Render HTML report content."""
        theme_css = self._get_theme_css(config.theme)

        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"<title>{escape(config.title)}</title>",
            "<style>",
            self._get_base_css(),
            theme_css,
            "</style>",
            "</head>",
            "<body>",
            '<div class="container">',
        ]

        # Header
        html_parts.extend(self._render_header(data, config))

        # Summary
        html_parts.extend(self._render_summary(data))

        # Statistics
        if config.include_statistics:
            html_parts.extend(self._render_statistics(data))

        # Issues
        html_parts.extend(self._render_issues(data, config))

        # Footer
        html_parts.extend(self._render_footer())

        html_parts.extend([
            "</div>",
            "</body>",
            "</html>",
        ])

        return "\n".join(html_parts)

    def _get_base_css(self) -> str:
        """Get base CSS styles."""
        return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; line-height: 1.6; }
.container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
h1, h2, h3 { margin-bottom: 1rem; }
.header { margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid var(--border-color); }
.status-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 600; margin-left: 1rem; }
.status-passed { background: #dcfce7; color: #166534; }
.status-failed { background: #fee2e2; color: #991b1b; }
.card { background: var(--card-bg); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card-title { font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }
.stat-item { text-align: center; padding: 1rem; background: var(--stat-bg); border-radius: 6px; }
.stat-value { font-size: 2rem; font-weight: bold; color: var(--primary-color); }
.stat-label { font-size: 0.875rem; color: var(--muted-color); }
.issue-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.issue-table th, .issue-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border-color); }
.issue-table th { background: var(--header-bg); font-weight: 600; }
.severity-badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.severity-critical { background: #fecaca; color: #991b1b; }
.severity-high { background: #fed7aa; color: #9a3412; }
.severity-medium { background: #fef08a; color: #854d0e; }
.severity-low { background: #bfdbfe; color: #1e40af; }
.footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border-color); text-align: center; font-size: 0.875rem; color: var(--muted-color); }
code { background: var(--code-bg); padding: 0.125rem 0.375rem; border-radius: 4px; font-family: monospace; }
"""

    def _get_theme_css(self, theme: ReportThemeType) -> str:
        """Get theme-specific CSS variables."""
        if theme == ReportThemeType.DARK:
            return """
:root {
    --bg-color: #1a1a2e;
    --text-color: #e0e0e0;
    --card-bg: #16213e;
    --stat-bg: #0f3460;
    --header-bg: #1a1a2e;
    --border-color: #374151;
    --primary-color: #fd9e4b;
    --muted-color: #9ca3af;
    --code-bg: #374151;
}
body { background: var(--bg-color); color: var(--text-color); }
"""
        elif theme == ReportThemeType.HIGH_CONTRAST:
            return """
:root {
    --bg-color: #000000;
    --text-color: #ffffff;
    --card-bg: #1a1a1a;
    --stat-bg: #333333;
    --header-bg: #1a1a1a;
    --border-color: #ffffff;
    --primary-color: #ffff00;
    --muted-color: #cccccc;
    --code-bg: #333333;
}
body { background: var(--bg-color); color: var(--text-color); }
"""
        else:  # Light, Professional, Minimal
            return """
:root {
    --bg-color: #f8fafc;
    --text-color: #1e293b;
    --card-bg: #ffffff;
    --stat-bg: #f1f5f9;
    --header-bg: #f8fafc;
    --border-color: #e2e8f0;
    --primary-color: #fd9e4b;
    --muted-color: #64748b;
    --code-bg: #f1f5f9;
}
body { background: var(--bg-color); color: var(--text-color); }
"""

    def _render_header(self, data: ReportData, config: ReporterConfig) -> list[str]:
        """Render header section."""
        status_class = "status-passed" if data.summary.passed else "status-failed"
        status_text = "Passed" if data.summary.passed else "Failed"

        return [
            '<div class="header">',
            f'<h1>{escape(config.title)}<span class="status-badge {status_class}">{status_text}</span></h1>',
            f'<p>Source: <code>{escape(data.source_name or data.source_id)}</code></p>',
            '</div>',
        ]

    def _render_summary(self, data: ReportData) -> list[str]:
        """Render summary card."""
        summary = data.summary
        return [
            '<div class="card">',
            '<h2 class="card-title">Summary</h2>',
            '<div class="stats-grid">',
            f'<div class="stat-item"><div class="stat-value">{summary.total_issues}</div><div class="stat-label">Total Issues</div></div>',
            f'<div class="stat-item"><div class="stat-value" style="color:#dc2626">{summary.critical_issues}</div><div class="stat-label">Critical</div></div>',
            f'<div class="stat-item"><div class="stat-value" style="color:#ea580c">{summary.high_issues}</div><div class="stat-label">High</div></div>',
            f'<div class="stat-item"><div class="stat-value" style="color:#ca8a04">{summary.medium_issues}</div><div class="stat-label">Medium</div></div>',
            f'<div class="stat-item"><div class="stat-value" style="color:#2563eb">{summary.low_issues}</div><div class="stat-label">Low</div></div>',
            '</div>',
            '</div>',
        ]

    def _render_statistics(self, data: ReportData) -> list[str]:
        """Render statistics card."""
        stats = data.statistics
        parts = [
            '<div class="card">',
            '<h2 class="card-title">Statistics</h2>',
            '<div class="stats-grid">',
        ]

        if stats.row_count is not None:
            parts.append(f'<div class="stat-item"><div class="stat-value">{stats.row_count:,}</div><div class="stat-label">Rows</div></div>')
        if stats.column_count is not None:
            parts.append(f'<div class="stat-item"><div class="stat-value">{stats.column_count}</div><div class="stat-label">Columns</div></div>')
        if stats.duration_ms is not None:
            parts.append(f'<div class="stat-item"><div class="stat-value">{stats.duration_ms}</div><div class="stat-label">Duration (ms)</div></div>')

        parts.extend([
            '</div>',
            '</div>',
        ])
        return parts

    def _render_issues(self, data: ReportData, config: ReporterConfig) -> list[str]:
        """Render issues table."""
        parts = [
            '<div class="card">',
            '<h2 class="card-title">Issues</h2>',
        ]

        if not data.issues:
            parts.append('<p>No issues found!</p>')
        else:
            parts.append('<table class="issue-table">')
            parts.append('<thead><tr>')
            parts.append('<th>Severity</th><th>Column</th><th>Type</th><th>Message</th><th>Count</th>')
            if config.include_samples:
                parts.append('<th>Samples</th>')
            parts.append('</tr></thead>')
            parts.append('<tbody>')

            for issue in data.issues:
                severity_class = f"severity-{issue.severity.lower()}"
                parts.append('<tr>')
                parts.append(f'<td><span class="severity-badge {severity_class}">{escape(issue.severity.upper())}</span></td>')
                parts.append(f'<td><code>{escape(issue.column or "N/A")}</code></td>')
                parts.append(f'<td>{escape(issue.issue_type)}</td>')
                parts.append(f'<td>{escape(issue.message)}</td>')
                parts.append(f'<td>{issue.count}</td>')
                if config.include_samples:
                    samples = ""
                    if issue.sample_values:
                        samples = ", ".join(escape(str(v)) for v in issue.sample_values[:config.max_sample_values])
                    parts.append(f'<td><code>{samples}</code></td>')
                parts.append('</tr>')

            parts.append('</tbody></table>')

        parts.append('</div>')
        return parts

    def _render_footer(self) -> list[str]:
        """Render footer."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return [
            '<div class="footer">',
            f'<p>Generated at {timestamp}</p>',
            '<p>Powered by Truthound Dashboard</p>',
            '</div>',
        ]
