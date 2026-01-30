# Validations

The Validations module provides the central mechanism for executing data quality checks and inspecting their results. It encompasses the full lifecycle of a validation run—from configuration and execution through to result analysis, versioning, and historical trend monitoring.

## Overview

Data validation is the process of systematically verifying that a dataset conforms to a defined set of quality rules. Truthound Dashboard supports 289+ built-in validators spanning schema integrity, completeness, uniqueness, distribution, string patterns, datetime formats, aggregate statistics, cross-table relationships, geospatial coordinates, drift detection, anomaly detection, and privacy compliance.

The validation system is composed of three interrelated subsystems:

| Subsystem | Purpose | Page |
|-----------|---------|------|
| **Validation Execution** | Run validators against a data source and inspect results | Source Detail |
| **Validation History** | Track pass/fail trends over time with statistical analysis | History |
| **Version Management** | Create and compare snapshots of validation results | Version History |

## Validation Execution

### Running a Validation

Validation is initiated from the Source Detail page. The execution workflow proceeds as follows:

1. **Select Validators**: Use the Validator Selector to choose which validators to run
2. **Configure Parameters**: Adjust validator-specific parameters (thresholds, patterns, column selections)
3. **Execute**: Click "Configure & Run" to launch the validation
4. **Review Results**: Examine issues grouped by severity

### Validator Configuration

The Validator Selector provides a comprehensive interface for choosing and configuring validators:

| Feature | Description |
|---------|-------------|
| **Preset Templates** | Quick-start configurations: All Validators, Quick Check, Schema Only, Data Quality |
| **Category Filtering** | Filter by 14 categories (schema, completeness, uniqueness, distribution, etc.) |
| **Search** | Find validators by name, description, or tag |
| **Parameter Configuration** | Type-specific input forms (text, number, select, boolean, column list) |
| **Severity Override** | Override the default severity level for any validator |
| **Column Autocomplete** | Schema-aware column selection with autocomplete |

### Execution Parameters

The validation engine supports several execution-level parameters that control how validators are applied:

| Parameter | Description | Default |
|-----------|-------------|---------|
| **validators** | List of validators to execute | All enabled |
| **validator_config** | Per-validator parameter overrides | None |
| **min_severity** | Minimum severity threshold for reporting | low |
| **parallel** | Enable parallel execution across validators | false |
| **max_workers** | Number of parallel worker threads | CPU count |
| **pushdown** | Enable SQL query pushdown for database sources | false |
| **schema** | Schema file path or Schema object for constraint validation | Auto-detected |
| **auto_schema** | Automatically learn schema before validation | false |

### Validation Results

Upon completion, the validation result contains:

| Field | Description |
|-------|-------------|
| **passed** | Boolean indicating overall pass/fail status |
| **total_issues** | Total number of issues detected |
| **has_critical** | Whether any critical-severity issues were found |
| **has_high** | Whether any high-severity issues were found |
| **issues** | Detailed list of individual issues |
| **execution_time** | Duration of the validation run |
| **validators_run** | Number of validators that were executed |

### Issue Detail

Each detected issue includes the following attributes:

| Attribute | Description |
|-----------|-------------|
| **Column** | Name of the affected column (if applicable) |
| **Validator** | Name of the validator that detected the issue |
| **Severity** | critical, high, medium, or low |
| **Value** | The specific value or statistic that triggered the issue |
| **Description** | Human-readable explanation of the issue |
| **Row Count** | Number of rows affected (for row-level issues) |

### Severity Classification

Issues are classified into four severity levels:

| Severity | Description | Visual |
|----------|-------------|--------|
| **Critical** | Data is fundamentally corrupt or unusable | Red |
| **High** | Significant quality issues that require attention | Orange |
| **Medium** | Moderate issues that may affect downstream processes | Yellow |
| **Low** | Minor issues or informational observations | Blue |

## Validation History

The History page provides longitudinal analysis of validation results for a data source.

### Temporal Controls

| Control | Options | Purpose |
|---------|---------|---------|
| **Period Selector** | Last 7, 30, or 90 days | Define the time window for analysis |
| **Granularity Selector** | Hourly, daily, or weekly | Control the aggregation granularity of trend charts |

### Summary Statistics

Four summary cards display key metrics for the selected period:

| Metric | Description |
|--------|-------------|
| **Total Runs** | Number of validation executions in the period |
| **Success Rate** | Percentage of validations that passed |
| **Failure Rate** | Percentage of validations that failed |
| **Trend Direction** | Whether quality is improving (↑) or declining (↓) |

### Trend Visualization

The History page includes two chart types:

1. **Pass/Fail Rate Chart**: A line chart displaying the validation success and failure rates over time at the selected granularity
2. **Issue Frequency Chart**: A bar chart showing the frequency of different issue types, enabling identification of recurring quality problems

### Recent Validations Table

A paginated table lists individual validation runs with:

| Column | Description |
|--------|-------------|
| **Timestamp** | When the validation was executed |
| **Status** | Pass or fail |
| **Issue Count** | Number of issues detected |
| **Duration** | Execution time |
| **Validators** | Number of validators executed |

## Version Management

The Version History page enables creation and comparison of validation result snapshots.

### Version Creation

Validation results can be saved as versioned snapshots for future reference. This is initiated from the Validation Results page via the "Create Version" button. Each version captures:

| Attribute | Description |
|-----------|-------------|
| **Version Number** | Auto-incremented sequential identifier |
| **Timestamp** | Creation time of the snapshot |
| **Strategy** | Versioning strategy (incremental, semantic, timestamp, gitlike) |
| **Metadata** | Validation configuration and execution context |

### Versioning Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| **Incremental** | Simple sequential numbering | v1, v2, v3 |
| **Semantic** | Major.minor.patch version scheme | v1.0.0, v1.0.1, v1.1.0 |
| **Timestamp** | ISO 8601 timestamp-based identifiers | 2024-01-15T10:30:00 |
| **Git-like** | Short hash-based identifiers | a1b2c3d |

### Version Comparison

The comparison feature allows side-by-side analysis of two validation versions:

1. Select two versions from the timeline
2. The comparison view highlights differences in:
   - Overall pass/fail status
   - Issue counts by severity
   - Specific issues that appeared or disappeared
   - Changes in validation configuration

### Version Timeline

A visual timeline component displays all versions in chronological order, with version cards showing:

- Version number and strategy badge
- Creation timestamp
- Quick summary of the validation state

## Custom Validation Rules

The Rules page provides a YAML-based interface for defining custom validation rules.

### Rule Structure

Rules are defined in YAML format with two sections:

```yaml
columns:
  email:
    - not_null
    - unique
    - pattern: "^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
  age:
    - not_null
    - min: 0
    - max: 150

table:
  - row_count_min: 100
  - no_duplicate_rows
```

### Rule Management

| Operation | Description |
|-----------|-------------|
| **Create Rule** | Define a new rule with name, description, and YAML definition |
| **Edit Rule** | Modify an existing rule's definition |
| **Delete Rule** | Remove a rule from the source |
| **Activate Rule** | Set a rule as the active validation rule for the source |

## Integration Points

### Schedule Integration

Validation configurations can be attached to [Schedules](../system/schedules.md) for automated periodic execution. The schedule stores the complete validator configuration, ensuring consistent execution across runs.

### Notification Integration

Validation failures can trigger [Notifications](../system/notifications.md) through configured channels. Notification rules support filtering by severity, source, and validator type.

### Alert Integration

Validation results feed into the [Unified Alert](../system/alerts.md) system, where they can be correlated with drift, anomaly, and model monitoring alerts.

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| **Start with Quick Check** | Use the Quick Check preset for initial quality assessment |
| **Customize Gradually** | Progressively enable additional validators as you understand the data |
| **Set Appropriate Severity** | Override default severity levels to match business criticality |
| **Version Important Results** | Create version snapshots before and after major data changes |
| **Monitor Trends** | Use the History page to identify quality regression patterns |
| **Automate with Schedules** | Set up scheduled validations for production data sources |
| **Enable Parallel Execution** | Use parallel mode for large datasets with many validators |

## API Reference

### Validation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/validate` | POST | Run validation on a data source |
| `/validations` | GET | List validation results |
| `/validations/{id}` | GET | Get validation result details |
| `/validations/{id}/issues` | GET | Get issues for a validation |

### History Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/history/sources/{id}` | GET | Get validation history for a source |
| `/history/sources/{id}/trends` | GET | Get trend data for a source |

### Version Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/versioning/sources/{id}` | GET | List versions for a source |
| `/versioning/sources/{id}` | POST | Create a new version snapshot |
| `/versioning/sources/{id}/compare` | GET | Compare two versions |
| `/versioning/{version_id}` | GET | Get version details |

### Rules Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/rules` | GET | List rules for a source |
| `/sources/{id}/rules` | POST | Create a new rule |
| `/rules/{id}` | PUT | Update a rule |
| `/rules/{id}` | DELETE | Delete a rule |
| `/rules/{id}/activate` | POST | Set as active rule |

## Glossary

| Term | Definition |
|------|------------|
| **Validation Run** | A single execution of one or more validators against a data source |
| **Issue** | A specific quality problem detected by a validator |
| **Severity** | Classification of an issue's impact (critical, high, medium, low) |
| **Version Snapshot** | A preserved copy of validation results for future reference |
| **Pushdown** | Optimization that executes validation logic directly on the database server |
| **Validator Config** | Per-validator parameter overrides applied during execution |
