"""HTML report generator.

Generates professional HTML reports with responsive design,
theme support, and interactive features.
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata, ReportTheme

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class HTMLReporter(Reporter):
    """HTML report generator with theme support.

    Produces standalone HTML documents with embedded CSS.
    Supports multiple themes and responsive design.
    """

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.HTML

    @property
    def content_type(self) -> str:
        return "text/html; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".html"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render HTML report content."""
        issues = self._extract_issues(validation)
        theme = metadata.theme

        # Build HTML sections
        css = self._generate_css(theme)
        header = self._render_header(validation, metadata)
        summary = self._render_summary(validation, theme)
        statistics = (
            self._render_statistics(validation, theme) if include_statistics else ""
        )
        issues_section = self._render_issues(issues, theme, include_samples)
        footer = self._render_footer(metadata)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(metadata.title)}</title>
    <style>
{css}
    </style>
</head>
<body class="theme-{theme.value}">
    <div class="container">
        {header}
        {summary}
        {statistics}
        {issues_section}
        {footer}
    </div>
</body>
</html>"""

    def _generate_css(self, theme: ReportTheme) -> str:
        """Generate CSS based on theme."""
        # Base colors for themes
        theme_colors = {
            ReportTheme.LIGHT: {
                "bg": "#ffffff",
                "text": "#1f2937",
                "text-muted": "#6b7280",
                "border": "#e5e7eb",
                "card-bg": "#f9fafb",
                "primary": "#fd9e4b",
                "success": "#10b981",
                "danger": "#ef4444",
            },
            ReportTheme.DARK: {
                "bg": "#1f2937",
                "text": "#f9fafb",
                "text-muted": "#9ca3af",
                "border": "#374151",
                "card-bg": "#111827",
                "primary": "#fd9e4b",
                "success": "#34d399",
                "danger": "#f87171",
            },
            ReportTheme.PROFESSIONAL: {
                "bg": "#f8fafc",
                "text": "#0f172a",
                "text-muted": "#64748b",
                "border": "#cbd5e1",
                "card-bg": "#ffffff",
                "primary": "#fd9e4b",
                "success": "#059669",
                "danger": "#dc2626",
            },
            ReportTheme.MINIMAL: {
                "bg": "#ffffff",
                "text": "#000000",
                "text-muted": "#666666",
                "border": "#e0e0e0",
                "card-bg": "#fafafa",
                "primary": "#fd9e4b",
                "success": "#22c55e",
                "danger": "#ef4444",
            },
            ReportTheme.HIGH_CONTRAST: {
                "bg": "#000000",
                "text": "#ffffff",
                "text-muted": "#e0e0e0",
                "border": "#ffffff",
                "card-bg": "#1a1a1a",
                "primary": "#ffb347",
                "success": "#00ff00",
                "danger": "#ff0000",
            },
        }

        c = theme_colors.get(theme, theme_colors[ReportTheme.PROFESSIONAL])

        return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                         'Helvetica Neue', Arial, sans-serif;
            background-color: {c['bg']};
            color: {c['text']};
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid {c['primary']};
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: {c['primary']};
        }}

        .header .subtitle {{
            color: {c['text-muted']};
            font-size: 0.95rem;
        }}

        .card {{
            background: {c['card-bg']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid {c['border']};
        }}

        .status-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 1.1rem;
        }}

        .status-passed {{
            background: {c['success']}20;
            color: {c['success']};
        }}

        .status-failed {{
            background: {c['danger']}20;
            color: {c['danger']};
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}

        .summary-item {{
            text-align: center;
            padding: 1rem;
            background: {c['bg']};
            border-radius: 8px;
            border: 1px solid {c['border']};
        }}

        .summary-item .value {{
            font-size: 2rem;
            font-weight: 700;
            display: block;
        }}

        .summary-item .label {{
            color: {c['text-muted']};
            font-size: 0.875rem;
        }}

        .severity-critical {{ color: #dc2626; }}
        .severity-high {{ color: #ea580c; }}
        .severity-medium {{ color: #ca8a04; }}
        .severity-low {{ color: #2563eb; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}

        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid {c['border']};
        }}

        th {{
            background: {c['bg']};
            font-weight: 600;
            color: {c['text-muted']};
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        tr:hover {{
            background: {c['card-bg']};
        }}

        .severity-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-critical {{
            background: #dc262620;
            color: #dc2626;
        }}

        .badge-high {{
            background: #ea580c20;
            color: #ea580c;
        }}

        .badge-medium {{
            background: #ca8a0420;
            color: #ca8a04;
        }}

        .badge-low {{
            background: #2563eb20;
            color: #2563eb;
        }}

        .samples {{
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: {c['bg']};
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.875rem;
            color: {c['text-muted']};
        }}

        .footer {{
            text-align: center;
            padding-top: 1.5rem;
            margin-top: 2rem;
            border-top: 1px solid {c['border']};
            color: {c['text-muted']};
            font-size: 0.875rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }}

        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid {c['border']};
        }}

        .stat-row:last-child {{
            border-bottom: none;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}

            .summary-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            table {{
                display: block;
                overflow-x: auto;
            }}
        }}

        @media print {{
            body {{
                padding: 0;
            }}

            .card {{
                break-inside: avoid;
            }}
        }}
        """

    def _render_header(self, validation: Validation, metadata: ReportMetadata) -> str:
        """Render report header."""
        source_name = escape(metadata.source_name or validation.source_id)
        generated = metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""
        <header class="header">
            <h1>{escape(metadata.title)}</h1>
            <p class="subtitle">
                Source: <strong>{source_name}</strong> |
                Generated: {generated}
            </p>
        </header>
        """

    def _render_summary(self, validation: Validation, theme: ReportTheme) -> str:
        """Render validation summary card."""
        passed = validation.passed
        status_class = "status-passed" if passed else "status-failed"
        status_text = self._get_status_indicator(passed)

        return f"""
        <section class="card">
            <h2 class="card-title">Validation Summary</h2>
            <div style="text-align: center; margin-bottom: 1rem;">
                <span class="status-badge {status_class}">{status_text}</span>
            </div>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="value">{validation.total_issues or 0}</span>
                    <span class="label">Total Issues</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-critical">{validation.critical_issues or 0}</span>
                    <span class="label">Critical</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-high">{validation.high_issues or 0}</span>
                    <span class="label">High</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-medium">{validation.medium_issues or 0}</span>
                    <span class="label">Medium</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-low">{validation.low_issues or 0}</span>
                    <span class="label">Low</span>
                </div>
            </div>
        </section>
        """

    def _render_statistics(self, validation: Validation, theme: ReportTheme) -> str:
        """Render data statistics card."""
        duration = validation.duration_ms
        duration_str = f"{duration / 1000:.2f}s" if duration else "N/A"

        started = (
            validation.started_at.strftime("%Y-%m-%d %H:%M:%S")
            if validation.started_at
            else "N/A"
        )
        completed = (
            validation.completed_at.strftime("%Y-%m-%d %H:%M:%S")
            if validation.completed_at
            else "N/A"
        )

        return f"""
        <section class="card">
            <h2 class="card-title">Data Statistics</h2>
            <div class="stats-grid">
                <div class="stat-row">
                    <span>Row Count</span>
                    <strong>{validation.row_count or 'N/A':,}</strong>
                </div>
                <div class="stat-row">
                    <span>Column Count</span>
                    <strong>{validation.column_count or 'N/A'}</strong>
                </div>
                <div class="stat-row">
                    <span>Duration</span>
                    <strong>{duration_str}</strong>
                </div>
                <div class="stat-row">
                    <span>Status</span>
                    <strong>{escape(validation.status)}</strong>
                </div>
                <div class="stat-row">
                    <span>Started At</span>
                    <strong>{started}</strong>
                </div>
                <div class="stat-row">
                    <span>Completed At</span>
                    <strong>{completed}</strong>
                </div>
            </div>
        </section>
        """

    def _render_issues(
        self,
        issues: list[dict[str, Any]],
        theme: ReportTheme,
        include_samples: bool,
    ) -> str:
        """Render issues table."""
        if not issues:
            return """
            <section class="card">
                <h2 class="card-title">Issues</h2>
                <p style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    No issues found. All validations passed.
                </p>
            </section>
            """

        rows = []
        for issue in issues:
            severity = issue.get("severity", "medium").lower()
            badge_class = f"badge-{severity}"

            samples_html = ""
            if include_samples and issue.get("sample_values"):
                samples = [str(v)[:50] for v in issue["sample_values"][:5]]
                samples_html = f'<div class="samples">{escape(", ".join(samples))}</div>'

            rows.append(f"""
                <tr>
                    <td>{escape(issue.get('column', 'N/A'))}</td>
                    <td>{escape(issue.get('issue_type', 'Unknown'))}</td>
                    <td><span class="severity-badge {badge_class}">{severity}</span></td>
                    <td>{issue.get('count', 0):,}</td>
                    <td>
                        {escape(issue.get('details', '') or '')}
                        {samples_html}
                    </td>
                </tr>
            """)

        return f"""
        <section class="card">
            <h2 class="card-title">Issues ({len(issues)})</h2>
            <table>
                <thead>
                    <tr>
                        <th>Column</th>
                        <th>Issue Type</th>
                        <th>Severity</th>
                        <th>Count</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </section>
        """

    def _render_footer(self, metadata: ReportMetadata) -> str:
        """Render report footer."""
        return f"""
        <footer class="footer">
            <p>Generated by Truthound Dashboard</p>
            <p>Validation ID: {escape(metadata.validation_id or 'N/A')}</p>
        </footer>
        """
