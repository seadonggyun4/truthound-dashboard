/**
 * MSW handlers for Reports API
 */

import { http, HttpResponse } from "msw";

const API_BASE = "/api/v1/reports";

// Available report formats (6 formats including JUnit)
const REPORT_FORMATS = ["html", "csv", "json", "markdown", "pdf", "junit"];
const REPORT_THEMES = [
  "light",
  "dark",
  "professional",
  "minimal",
  "high_contrast",
];

// Sample HTML report content
const generateHtmlReport = (validationId: string): string => `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Validation Report</title>
    <style>
        body { font-family: -apple-system, system-ui, sans-serif; padding: 2rem; }
        .header { text-align: center; border-bottom: 2px solid #fd9e4b; }
        .card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; }
    </style>
</head>
<body>
    <header class="header">
        <h1>Validation Report</h1>
        <p>ID: ${validationId}</p>
    </header>
    <section class="card">
        <h2>Summary</h2>
        <p>Status: <strong>PASSED</strong></p>
        <p>Total Issues: 3</p>
    </section>
</body>
</html>
`;

// Sample CSV report content
const generateCsvReport = (): string => `# Validation Report
# Source,test_source
# Validation ID,mock-validation-id
# Generated At,${new Date().toISOString()}
# Status,PASSED

# Statistics
Metric,Value
Row Count,10000
Column Count,15
Total Issues,3
Critical Issues,0
High Issues,1
Medium Issues,2
Low Issues,0

# Issues
Column,Issue Type,Severity,Count,Details
email,null_values,medium,5,Missing email addresses
age,out_of_range,high,2,Values exceed maximum
status,invalid_category,medium,1,Unknown status value
`;

// Sample JSON report content
const generateJsonReport = (validationId: string) => ({
  metadata: {
    title: "Validation Report",
    generated_at: new Date().toISOString(),
    format: "json",
    theme: "professional",
  },
  validation: {
    id: validationId,
    source_id: "mock-source-id",
    source_name: "Test Data Source",
    status: "success",
    passed: true,
  },
  summary: {
    total_issues: 3,
    critical_issues: 0,
    high_issues: 1,
    medium_issues: 2,
    low_issues: 0,
    has_critical: false,
    has_high: true,
  },
  statistics: {
    row_count: 10000,
    column_count: 15,
    duration_ms: 1234,
    started_at: new Date(Date.now() - 5000).toISOString(),
    completed_at: new Date().toISOString(),
  },
  issues: [
    {
      column: "email",
      issue_type: "null_values",
      severity: "medium",
      count: 5,
      details: "Missing email addresses",
      sample_values: [null, null],
    },
    {
      column: "age",
      issue_type: "out_of_range",
      severity: "high",
      count: 2,
      details: "Values exceed maximum of 120",
      sample_values: [150, 999],
    },
    {
      column: "status",
      issue_type: "invalid_category",
      severity: "medium",
      count: 1,
      details: "Unknown status value",
      sample_values: ["unknown_status"],
    },
  ],
});

// Sample JUnit XML report content
const generateJunitReport = (validationId: string): string => `<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Truthound Validation" tests="4" failures="3" errors="0" time="1.234">
  <testsuite name="Validation: Test Data Source" tests="4" failures="3" errors="0" time="1.234" timestamp="${new Date().toISOString()}">
    <properties>
      <property name="source_id" value="mock-source-id"/>
      <property name="validation_id" value="${validationId}"/>
      <property name="row_count" value="10000"/>
      <property name="column_count" value="15"/>
      <property name="status" value="success"/>
      <property name="passed" value="true"/>
    </properties>
    <testcase name="Overall Validation" classname="truthound.test_source" time="1.234">
      <failure message="Validation failed with 3 issues" type="ValidationFailure">
        Validation Status: success
        Total Issues: 3
        Critical: 0
        High: 1
        Medium: 2
        Low: 0
      </failure>
    </testcase>
    <testcase name="Check: null_values" classname="truthound.validators.null_values" time="0">
      <failure message="1 issues found" type="ValidationFailure">
        Column: email, Count: 5
      </failure>
    </testcase>
    <testcase name="Check: out_of_range" classname="truthound.validators.out_of_range" time="0">
      <failure message="1 issues found" type="ValidationFailure">
        Column: age, Count: 2
      </failure>
    </testcase>
    <testcase name="Check: invalid_category" classname="truthound.validators.invalid_category" time="0">
      <failure message="1 issues found" type="ValidationFailure">
        Column: status, Count: 1
      </failure>
    </testcase>
    <system-out>
Truthound Validation Report
===========================
Source: Test Data Source
Validation ID: ${validationId}
Generated: ${new Date().toISOString()}
    </system-out>
  </testsuite>
</testsuites>`;

// Sample Markdown report content
const generateMarkdownReport = (validationId: string): string => `# Validation Report

**Source:** Test Data Source
**Generated:** ${new Date().toISOString()}
**Validation ID:** \`${validationId}\`

![Status](https://img.shields.io/badge/Status-PASSED-success)

## Summary

| Metric | Count |
|--------|-------|
| Total Issues | 3 |
| Critical | 0 |
| High | 1 |
| Medium | 2 |
| Low | 0 |

## Statistics

| Metric | Value |
|--------|-------|
| Row Count | 10,000 |
| Column Count | 15 |
| Duration | 1.23s |
| Status | success |

## Issues (3)

| Column | Issue Type | Severity | Count | Details |
| --- | --- | --- | --- | --- |
| \`email\` | null_values | ![medium](https://img.shields.io/badge/medium-yellow) | 5 | Missing email addresses |
| \`age\` | out_of_range | ![high](https://img.shields.io/badge/high-orange) | 2 | Values exceed maximum |
| \`status\` | invalid_category | ![medium](https://img.shields.io/badge/medium-yellow) | 1 | Unknown status value |

---

*Generated by [Truthound Dashboard](https://github.com/truthound/truthound-dashboard)*
`;

export const reportHandlers = [
  // GET /reports/formats - List available formats
  http.get(`${API_BASE}/formats`, () => {
    return HttpResponse.json({
      formats: REPORT_FORMATS,
      themes: REPORT_THEMES,
    });
  }),

  // POST /reports/validations/:validationId/report - Generate report metadata
  http.post<{ validationId: string }>(
    `${API_BASE}/validations/:validationId/report`,
    async ({ params, request }) => {
      const body = (await request.json()) as {
        format?: string;
        theme?: string;
        title?: string;
      };
      const format = body.format || "html";
      const theme = body.theme || "professional";

      // Simulate generation time
      await new Promise((resolve) => setTimeout(resolve, 200));

      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const extension =
        format === "markdown" ? "md" : format === "json" ? "json" : format;

      return HttpResponse.json({
        filename: `validation_report_${timestamp}.${extension}`,
        content_type:
          format === "html"
            ? "text/html; charset=utf-8"
            : format === "csv"
              ? "text/csv; charset=utf-8"
              : format === "json"
                ? "application/json; charset=utf-8"
                : "text/markdown; charset=utf-8",
        size_bytes: 2048 + Math.floor(Math.random() * 1000),
        generation_time_ms: 150 + Math.floor(Math.random() * 100),
        metadata: {
          title: body.title || `Validation Report - ${params.validationId}`,
          generated_at: new Date().toISOString(),
          source_name: "Test Data Source",
          source_id: "mock-source-id",
          validation_id: params.validationId,
          theme: theme,
          format: format,
        },
      });
    }
  ),

  // GET /reports/validations/:validationId/download - Download report
  http.get<{ validationId: string }>(
    `${API_BASE}/validations/:validationId/download`,
    ({ params, request }) => {
      const url = new URL(request.url);
      const format = url.searchParams.get("format") || "html";

      let content: string;
      let contentType: string;

      switch (format) {
        case "csv":
          content = generateCsvReport();
          contentType = "text/csv; charset=utf-8";
          break;
        case "json":
          content = JSON.stringify(
            generateJsonReport(params.validationId),
            null,
            2
          );
          contentType = "application/json; charset=utf-8";
          break;
        case "markdown":
          content = generateMarkdownReport(params.validationId);
          contentType = "text/markdown; charset=utf-8";
          break;
        case "junit":
          content = generateJunitReport(params.validationId);
          contentType = "application/xml; charset=utf-8";
          break;
        default:
          content = generateHtmlReport(params.validationId);
          contentType = "text/html; charset=utf-8";
      }

      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const extension =
        format === "markdown" ? "md" : format === "json" ? "json" : format === "junit" ? "xml" : format;
      const filename = `validation_report_${timestamp}.${extension}`;

      return new HttpResponse(content, {
        status: 200,
        headers: {
          "Content-Type": contentType,
          "Content-Disposition": `attachment; filename="${filename}"`,
          "Content-Length": String(content.length),
        },
      });
    }
  ),

  // GET /reports/validations/:validationId/preview - Preview report
  http.get<{ validationId: string }>(
    `${API_BASE}/validations/:validationId/preview`,
    ({ params, request }) => {
      const url = new URL(request.url);
      const format = url.searchParams.get("format") || "html";

      let content: string;
      let contentType: string;

      switch (format) {
        case "csv":
          content = generateCsvReport();
          contentType = "text/csv; charset=utf-8";
          break;
        case "json":
          content = JSON.stringify(
            generateJsonReport(params.validationId),
            null,
            2
          );
          contentType = "application/json; charset=utf-8";
          break;
        case "markdown":
          content = generateMarkdownReport(params.validationId);
          contentType = "text/markdown; charset=utf-8";
          break;
        case "junit":
          content = generateJunitReport(params.validationId);
          contentType = "application/xml; charset=utf-8";
          break;
        default:
          content = generateHtmlReport(params.validationId);
          contentType = "text/html; charset=utf-8";
      }

      return new HttpResponse(content, {
        status: 200,
        headers: {
          "Content-Type": contentType,
        },
      });
    }
  ),
];
