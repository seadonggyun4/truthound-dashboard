# Reports

The Reports module provides multi-format report generation capabilities, enabling users to create, manage, and distribute data quality documentation in various formats.

## Overview

Reports consolidate validation results, data quality metrics, and analysis findings into distributable documents. The module supports multiple output formats to accommodate diverse organizational requirements and stakeholder preferences.

## Reports Interface

### Statistics Dashboard

The interface displays report generation metrics:

| Metric | Description |
|--------|-------------|
| **Total Reports** | Count of all generated reports |
| **Total Size** | Aggregate storage consumed by reports |
| **Downloads** | Total report download count |
| **Avg Generation Time** | Mean time to generate reports |
| **Expired Count** | Reports past retention period |
| **Reporters Used** | Count of unique report formats generated |

## Report Listing

### Report Grid

The main Reports page displays generated reports:

| Column | Description |
|--------|-------------|
| **Name** | Report identifier |
| **Format** | Output format type |
| **Status** | Generation status |
| **Size** | File size |
| **Created** | Generation timestamp |
| **Expires** | Expiration date |
| **Actions** | Download, preview, delete |

### Status Indicators

| Status | Color | Description |
|--------|-------|-------------|
| **Completed** | Green | Report generated successfully |
| **Pending** | Yellow | Report generation queued |
| **Generating** | Blue | Report currently being generated |
| **Failed** | Red | Report generation failed |
| **Expired** | Gray | Report past retention period |

## Filtering and Search

### Search

Free-text search across report names.

### Format Filter

Filter reports by output format:

| Format | Description |
|--------|-------------|
| **HTML** | Interactive web-based reports |
| **CSV** | Comma-separated values |
| **JSON** | JavaScript Object Notation |
| **Markdown** | Markdown formatted text |
| **JUnit** | CI/CD integration XML format |

### Status Filter

Filter reports by generation status:

- Pending
- Generating
- Completed
- Failed
- Expired

### Include Expired Toggle

Toggle to show or hide expired reports in the listing.

## Report Formats

### HTML Reports

Interactive web-based reports:

| Characteristic | Description |
|---------------|-------------|
| **Interactivity** | Expandable sections, sorting, filtering |
| **Visualization** | Embedded charts and graphs |
| **Navigation** | Table of contents, anchor links |
| **Styling** | Professional formatting |

### CSV Reports

Comma-separated values:

| Characteristic | Description |
|---------------|-------------|
| **Simplicity** | Plain text format |
| **Compatibility** | Import into spreadsheets |
| **Processing** | Easy to parse programmatically |
| **Size** | Compact file size |

### JSON Reports

JavaScript Object Notation:

| Characteristic | Description |
|---------------|-------------|
| **Structured** | Hierarchical data representation |
| **API-Friendly** | Easy integration with systems |
| **Complete** | Full data preservation |
| **Machine-Readable** | Programmatic processing |

### Markdown Reports

Markdown formatted text:

| Characteristic | Description |
|---------------|-------------|
| **Readable** | Human-readable plain text |
| **Version Control** | Git-friendly format |
| **Convertible** | Easy conversion to other formats |
| **Documentation** | Suitable for documentation systems |

### JUnit Reports

CI/CD integration format:

| Characteristic | Description |
|---------------|-------------|
| **CI/CD Ready** | Native Jenkins, GitLab CI support |
| **Test Framework** | Standard test result format |
| **Automation** | Integrate with build pipelines |
| **Structured** | XML-based test suite output |

## Report Actions

### Download

Download a generated report:

1. Locate the report in the listing
2. Click **Download**
3. Browser downloads the report file
4. Open with appropriate application

### Preview

Preview compatible reports in the browser:

1. Locate the report (HTML or JSON format)
2. Click **Preview**
3. Report displays in a modal dialog
4. Review content without downloading

Note: Preview is available for HTML and JSON formats only.

### Delete

Remove a report:

1. Locate the report in the listing
2. Click **Delete**
3. Confirm deletion
4. Report file is permanently removed

### Cleanup Expired

Remove all expired reports:

1. Click **Cleanup Expired**
2. System identifies expired reports
3. Confirm bulk deletion
4. All expired reports are removed

## Report Generation

### Generating Reports

Reports are typically generated through other modules:

| Source | Trigger |
|--------|---------|
| **Validation Results** | Generate report from validation |
| **Drift Comparison** | Generate comparison report |
| **Anomaly Detection** | Generate anomaly report |
| **Scheduled Jobs** | Automatic report generation |

### Report Configuration

When generating reports:

| Setting | Description |
|---------|-------------|
| **Format** | Output format selection |
| **Name** | Report identifier |
| **Include Sections** | Content sections to include |
| **Retention** | How long to keep the report |

## Report Content

### Standard Report Sections

| Section | Content |
|---------|---------|
| **Summary** | Executive overview |
| **Details** | Detailed findings |
| **Issues** | List of identified issues |
| **Statistics** | Quantitative metrics |
| **Recommendations** | Suggested actions |
| **Appendix** | Supporting data |

### Validation Report Content

| Section | Content |
|---------|---------|
| **Overview** | Source info, validation date, status |
| **Results Summary** | Pass/fail counts, severity breakdown |
| **Issue Details** | Per-issue information |
| **Column Statistics** | Per-column validation results |
| **Trend Data** | Historical comparison |

### Drift Report Content

| Section | Content |
|---------|---------|
| **Configuration** | Comparison parameters |
| **Summary** | Overall drift assessment |
| **Column Analysis** | Per-column drift metrics |
| **Visualizations** | Distribution comparisons |
| **Recommendations** | Suggested actions |

## Report Retention

### Retention Policies

Reports are subject to retention policies:

| Policy Type | Description |
|-------------|-------------|
| **Default** | System-wide default retention |
| **Custom** | Per-report retention setting |
| **Permanent** | No automatic expiration |

### Expiration Behavior

When a report expires:

1. Report marked as expired
2. Hidden from default listing
3. Available via "Include Expired" toggle
4. Eligible for cleanup operations

### Managing Retention

Configure retention in Maintenance settings:

- Set default retention period
- Enable automatic cleanup
- Configure cleanup frequency

## Integration with Other Modules

### Validation Integration

Generate reports from validation results:

- Single validation report
- Historical trend report
- Comparison report

### Drift Monitoring Integration

Generate drift analysis reports:

- Comparison report
- Trend analysis report
- Root cause report

### Notification Integration

Automate report distribution:

- Email reports on completion
- Notify stakeholders of new reports
- Schedule regular report generation

## Best Practices

### Format Selection

| Audience | Recommended Format |
|----------|-------------------|
| **Executives** | HTML |
| **Data Engineers** | JSON, CSV |
| **Documentation** | Markdown |
| **Business Analysts** | CSV, HTML |
| **CI/CD Pipelines** | JUnit |
| **Automated Systems** | JSON |

### Report Naming

| Practice | Recommendation |
|----------|----------------|
| **Descriptive** | Include source, date, type |
| **Consistent** | Follow naming convention |
| **Searchable** | Include relevant keywords |

### Retention Management

| Practice | Recommendation |
|----------|----------------|
| **Regular Cleanup** | Schedule periodic cleanup |
| **Archive Important** | Export critical reports externally |
| **Storage Monitoring** | Monitor report storage usage |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reports/history` | GET | List reports with filters |
| `/reports/history` | POST | Generate a new report |
| `/reports/history/statistics` | GET | Retrieve report statistics |
| `/reports/history/{id}` | GET | Retrieve report details |
| `/reports/history/{id}` | PATCH | Update report metadata |
| `/reports/history/{id}/download` | GET | Download report file |
| `/reports/history/{id}/generate` | POST | Re-generate a report |
| `/reports/history/{id}` | DELETE | Delete a report |
| `/reports/history/cleanup` | DELETE | Delete expired reports |
