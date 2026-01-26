"""Built-in JUnit XML reporter.

Generates JUnit XML reports for CI/CD integration without external dependencies.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any
from xml.etree import ElementTree as ET

from ..interfaces import (
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReportFormatType,
)


class BuiltinJUnitReporter(BaseReporter[ReporterConfig]):
    """Built-in JUnit XML report generator.

    Produces JUnit XML reports compatible with CI/CD tools like:
    - Jenkins
    - GitHub Actions
    - GitLab CI
    - CircleCI
    - Azure DevOps

    Each validation issue is represented as a test case, allowing
    CI/CD systems to track and report validation results.
    """

    def __init__(
        self,
        suite_name: str = "Truthound Validation",
        include_properties: bool = True,
    ) -> None:
        """Initialize JUnit reporter.

        Args:
            suite_name: Name for the test suite.
            include_properties: Whether to include properties element.
        """
        super().__init__()
        self._suite_name = suite_name
        self._include_properties = include_properties

    @property
    def format(self) -> ReportFormatType:
        return ReportFormatType.JUNIT

    @property
    def content_type(self) -> str:
        return "application/xml; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".xml"

    async def _render_content(
        self,
        data: ReportData,
        config: ReporterConfig,
    ) -> str:
        """Render JUnit XML report content."""
        # Create root testsuites element
        testsuites = ET.Element("testsuites")

        # Create testsuite
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", self._suite_name)
        testsuite.set("tests", str(len(data.issues) + 1))  # +1 for summary test
        testsuite.set("errors", "0")
        testsuite.set("failures", str(data.summary.total_issues))
        testsuite.set("skipped", "0")
        testsuite.set("timestamp", datetime.utcnow().isoformat())

        if data.statistics.duration_ms:
            testsuite.set("time", str(data.statistics.duration_ms / 1000.0))

        # Add properties
        if self._include_properties:
            properties = ET.SubElement(testsuite, "properties")
            self._add_property(properties, "source_id", data.source_id)
            self._add_property(properties, "source_name", data.source_name or "")
            self._add_property(properties, "validation_id", data.validation_id)
            self._add_property(properties, "total_issues", str(data.summary.total_issues))
            self._add_property(properties, "critical_issues", str(data.summary.critical_issues))
            self._add_property(properties, "high_issues", str(data.summary.high_issues))
            self._add_property(properties, "medium_issues", str(data.summary.medium_issues))
            self._add_property(properties, "low_issues", str(data.summary.low_issues))

            if data.statistics.row_count is not None:
                self._add_property(properties, "row_count", str(data.statistics.row_count))
            if data.statistics.column_count is not None:
                self._add_property(properties, "column_count", str(data.statistics.column_count))

        # Add summary test case (pass/fail based on validation result)
        summary_test = ET.SubElement(testsuite, "testcase")
        summary_test.set("classname", f"validation.{data.source_id}")
        summary_test.set("name", "Validation Summary")
        summary_test.set("time", "0")

        if not data.summary.passed:
            failure = ET.SubElement(summary_test, "failure")
            failure.set("type", "ValidationFailed")
            failure.set("message", f"Found {data.summary.total_issues} validation issues")
            failure.text = self._format_summary_message(data)

        # Add test case for each issue
        for i, issue in enumerate(data.issues):
            self._add_issue_testcase(testsuite, data, issue, i)

        # Convert to string with proper XML declaration
        tree = ET.ElementTree(testsuites)
        xml_str = ET.tostring(testsuites, encoding="unicode")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def _add_property(
        self,
        properties: ET.Element,
        name: str,
        value: str,
    ) -> None:
        """Add a property element."""
        prop = ET.SubElement(properties, "property")
        prop.set("name", name)
        prop.set("value", value)

    def _add_issue_testcase(
        self,
        testsuite: ET.Element,
        data: ReportData,
        issue: Any,
        index: int,
    ) -> None:
        """Add a test case for a validation issue."""
        testcase = ET.SubElement(testsuite, "testcase")

        # Use column as classname, issue_type as test name
        classname = f"validation.{data.source_id}.{issue.column or 'table'}"
        testcase.set("classname", classname)
        testcase.set("name", f"{issue.issue_type} ({index + 1})")
        testcase.set("time", "0")

        # All issues are failures
        failure = ET.SubElement(testcase, "failure")
        failure.set("type", issue.issue_type)
        failure.set("message", issue.message)

        # Add details to failure text
        details_lines = [
            f"Column: {issue.column or 'N/A'}",
            f"Severity: {issue.severity}",
            f"Count: {issue.count}",
        ]

        if issue.expected is not None:
            details_lines.append(f"Expected: {issue.expected}")
        if issue.actual is not None:
            details_lines.append(f"Actual: {issue.actual}")
        if issue.sample_values:
            samples = ", ".join(str(v) for v in issue.sample_values[:5])
            details_lines.append(f"Samples: {samples}")

        failure.text = "\n".join(details_lines)

    def _format_summary_message(self, data: ReportData) -> str:
        """Format summary message for failure element."""
        lines = [
            f"Validation failed for source: {data.source_name or data.source_id}",
            "",
            f"Total Issues: {data.summary.total_issues}",
            f"- Critical: {data.summary.critical_issues}",
            f"- High: {data.summary.high_issues}",
            f"- Medium: {data.summary.medium_issues}",
            f"- Low: {data.summary.low_issues}",
        ]
        return "\n".join(lines)
