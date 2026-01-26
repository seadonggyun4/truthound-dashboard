# Dashboard

The Dashboard serves as the primary entry point for Truthound Dashboard, providing a consolidated overview of data quality metrics and system status across all registered data sources.

## Overview

The Dashboard interface presents aggregated statistics and recent activity information, enabling users to rapidly assess the overall health of their data infrastructure without navigating to individual source detail pages.

## Interface Components

### Statistical Summary Cards

The Dashboard displays four primary metric cards:

| Metric | Description |
|--------|-------------|
| **Total Sources** | The aggregate count of registered data sources in the system |
| **Passed Validations** | Count of validation executions that completed without critical or high-severity issues |
| **Failed Validations** | Count of validation executions that identified critical or high-severity issues |
| **Pending Validations** | Count of sources awaiting their initial or scheduled validation execution |

Each statistical card employs animated number transitions to provide visual feedback when metrics are updated.

### Recent Sources Panel

The Recent Sources panel displays up to five most recently modified or validated data sources. Each source entry includes:

- **Source Name**: The user-defined identifier for the data source
- **Source Type**: The connection type (CSV, Parquet, PostgreSQL, MySQL, etc.)
- **Status Badge**: Visual indicator of the most recent validation result
  - Green: Validation passed
  - Red: Validation failed
  - Yellow: Validation completed with warnings
  - Gray: Pending validation
- **Last Validation Timestamp**: The date and time of the most recent validation execution

### Navigation Elements

- **View All Sources**: Direct navigation link to the complete Sources listing page
- **Source Cards**: Clicking any source card navigates to the corresponding Source Detail page
- **Add First Source**: For new installations with no configured sources, a call-to-action button guides users to the source creation workflow

## Empty State Behavior

When no data sources have been configured, the Dashboard displays an informational message with guidance for adding the first data source. This state includes:

- Descriptive text explaining the initial setup process
- A prominent button linking to the source creation dialog
- Visual iconography indicating the empty state condition

## Usage Workflow

1. **Initial Assessment**: Upon accessing the Dashboard, review the statistical summary cards to understand the current validation status across all sources
2. **Identify Issues**: Sources with failed validations are highlighted, enabling rapid identification of data quality concerns
3. **Navigate to Details**: Click on any source card to access detailed validation results, schema information, and configuration options
4. **Monitor Trends**: Regular Dashboard visits provide longitudinal awareness of data quality trends across the organization

## Technical Implementation

The Dashboard retrieves source information through the following API endpoint:

```
GET /api/v1/sources?limit=10
```

Source statistics are computed client-side based on the validation status of returned sources. The interface updates automatically when navigating back from other pages.
