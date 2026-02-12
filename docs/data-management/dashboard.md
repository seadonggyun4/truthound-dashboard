# Dashboard

The Dashboard module constitutes the primary entry point for Truthound Dashboard, providing a consolidated overview of data quality metrics and system status across all registered data sources.

## Overview

The Dashboard interface presents aggregated statistics and recent activity information, enabling practitioners to perform rapid assessment of the overall health of their data infrastructure without necessitating navigation to individual source detail pages.

## Interface Component Specifications

### Aggregate Statistical Indicators

The Dashboard presents four primary metric cards, each corresponding to a discrete system-level measurement:

| Metric | Description |
|--------|-------------|
| **Total Sources** | The aggregate count of registered data sources in the system |
| **Passed Validations** | Count of validation executions that completed without critical or high-severity issues |
| **Failed Validations** | Count of validation executions that identified critical or high-severity issues |
| **Pending Validations** | Count of sources awaiting their initial or scheduled validation execution |

Each statistical card is rendered with animated number transitions to provide visual feedback when metric values are refreshed.

### Recent Activity Panel

The Recent Activity Panel presents up to five of the most recently modified or validated data sources. Each source entry is composed of the following attributes:

- **Source Name**: The user-defined identifier assigned to the data source
- **Source Type**: The connection type classification (CSV, Parquet, PostgreSQL, MySQL, etc.)
- **Status Badge**: A visual indicator denoting the most recent validation result
  - Green: Validation passed
  - Red: Validation failed
  - Yellow: Validation completed with warnings
  - Gray: Pending validation
- **Last Validation Timestamp**: The date and time at which the most recent validation execution was recorded

### Navigation Elements

- **View All Sources**: A direct navigation link to the comprehensive Sources listing page
- **Source Cards**: Selection of any source card initiates navigation to the corresponding Source Detail page
- **Add First Source**: For newly provisioned installations with no configured sources, a call-to-action element is presented to guide practitioners to the source creation workflow

## Empty State Behavior

In the absence of configured data sources, the Dashboard renders an informational message accompanied by guidance for the addition of the initial data source. This state is characterized by the following elements:

- Descriptive text elucidating the initial setup process
- A prominently displayed button linking to the source creation dialog
- Visual iconography indicating the empty state condition

## Operational Workflow

1. **Initial Assessment**: Upon accessing the Dashboard, the aggregate statistical indicators should be reviewed to ascertain the current validation status across all registered sources
2. **Issue Identification**: Sources associated with failed validations are visually highlighted, thereby facilitating rapid identification of data quality concerns
3. **Detail Navigation**: Selection of any source card provides access to detailed validation results, schema information, and configuration options
4. **Trend Monitoring**: Regular Dashboard consultation affords longitudinal awareness of data quality trends across the organizational data infrastructure

## Enhanced Validation Result Presentation

With the Truthound core engine integration (PHASE 1–5), the Dashboard presents enriched validation diagnostics when individual source validation results are inspected:

### Structured Statistics Panel (PHASE 2)

When validation results include `statistics` (available through the `ReportStatistics` schema), the Dashboard renders an expanded analytical view comprising:

- **Success Rate**: Percentage of validators that completed without issues
- **Issues by Severity**: Distribution of detected issues across critical, high, medium, and low levels
- **Issues by Column**: Identification of the most problematic columns in the dataset
- **Issues by Validator**: Distribution of issues across validator types, enabling targeted remediation

### Execution Summary Panel (PHASE 4)

When the validation engine's DAG-based execution is active, an execution summary panel is displayed showing:

- **Executed/Skipped/Failed** counts with visual proportion indicators
- **Skip Reason Details**: For each skipped validator, the specific dependency failure that triggered the skip is disclosed

### Exception Summary Panel (PHASE 5)

When the fault-tolerant execution mode is enabled (`catch_exceptions=True`), an exception summary panel provides:

- **Total Exceptions**: Aggregate count of system-level errors encountered
- **Retry and Recovery Metrics**: Number of retried and successfully recovered validations
- **Failure Classification**: Distribution across transient, permanent, configuration, and data error categories

## Technical Implementation Details

Source information is retrieved by the Dashboard through the following API endpoint:

```
GET /api/v1/sources?limit=10
```

Source statistics are computed on the client side based on the validation status of returned sources. The interface is automatically refreshed upon navigation back from other pages.

Validation results are retrieved through:

```
GET /api/v1/validations/{id}
```

The response payload includes `statistics`, `validator_execution_summary`, and `exception_summary` fields when available, each rendered by dedicated React panel components (`StatisticsPanel`, `ExecutionSummaryPanel`, `ExceptionSummaryPanel`).
