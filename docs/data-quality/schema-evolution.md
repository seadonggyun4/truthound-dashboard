# Schema Evolution

The Schema Evolution module provides systematic tracking and analysis of structural changes in data sources over time. By maintaining a versioned history of schema states, it enables data engineers and quality analysts to identify breaking changes, assess migration impact, and ensure downstream system compatibility.

## Overview

Schema evolution refers to the natural process by which the structure of a dataset changes over time—columns are added, removed, renamed, or have their types altered. Without active monitoring, such changes can silently break data pipelines, invalidate validation rules, and introduce data quality regressions. The Schema Evolution module addresses this concern by capturing every schema modification, classifying its severity, and presenting the change history in an accessible timeline format.

## Core Concepts

### Schema Version

A schema version represents a snapshot of a data source's structure at a specific point in time. Each version is assigned a sequential version number and contains the complete column definitions, constraints, and metadata of the source at that moment.

| Attribute | Description |
|-----------|-------------|
| **Version Number** | Sequential identifier (e.g., v1, v2, v3) |
| **Timestamp** | Date and time the version was recorded |
| **Column Definitions** | Complete list of columns with types and constraints |
| **Change Summary** | Number of breaking, warning, and safe changes relative to the prior version |

### Change Types

The system detects and categorizes six types of structural changes:

| Change Type | Description | Typical Impact |
|-------------|-------------|----------------|
| **column_added** | A new column appears in the schema | Generally safe; downstream systems may ignore unknown columns |
| **column_removed** | An existing column is no longer present | Breaking; queries referencing this column will fail |
| **type_changed** | A column's data type has changed | Breaking or warning depending on type compatibility |
| **nullable_changed** | A column's nullable constraint has changed | Warning; may affect data integrity assumptions |
| **constraint_changed** | A column's constraint (unique, check, etc.) has changed | Warning; may affect validation rules |
| **column_renamed** | A column has been renamed (detected via heuristic matching) | Breaking; references to the old name will fail |

### Severity Classification

Each detected change is assigned a severity level that reflects its potential impact on downstream systems and data quality processes:

| Severity | Description | Visual Indicator |
|----------|-------------|------------------|
| **Breaking** | Change is likely to cause failures in dependent systems | Red badge |
| **Warning** | Change may affect behavior but is unlikely to cause immediate failure | Amber badge |
| **Safe** | Change is backward-compatible and low risk | Green badge |

The classification algorithm considers the change type, the direction of change (e.g., adding vs. removing a NOT NULL constraint), and compatibility between old and new data types.

## Schema Evolution Interface

### Source Selection

The page begins with a source selector that allows the user to choose which data source's schema history to examine. A period selector provides temporal filtering for the displayed changes.

### Summary Statistics

Four summary cards display aggregate metrics for the selected source:

| Card | Description |
|------|-------------|
| **Total Versions** | Number of recorded schema versions |
| **Breaking Changes** | Cumulative count of breaking changes across all versions |
| **Warnings** | Cumulative count of warning-level changes |
| **Safe Changes** | Cumulative count of backward-compatible changes |

### Version Timeline

Schema versions are displayed in reverse chronological order using an accordion interface. Each version entry includes:

1. **Version header**: Version number, timestamp, and a "latest" badge for the most recent version
2. **Change summary badges**: Counts of breaking, warning, and safe changes
3. **Change detail table**: Expanded view with per-column change information

The change detail table contains the following columns:

| Column | Description |
|--------|-------------|
| **Column Name** | Name of the affected column |
| **Change Type** | Category of change (added, removed, renamed, etc.) |
| **Old Value** | Previous state of the attribute |
| **New Value** | Current state of the attribute |
| **Severity** | Breaking, warning, or safe |
| **Reason** | Human-readable explanation of the change |

## Integration with Schema Watcher

Schema Evolution operates in conjunction with the [Schema Watcher](./schema-watcher.md) module. While Schema Evolution provides a historical view of changes that have already occurred, Schema Watcher performs continuous monitoring and issues real-time alerts when new changes are detected.

| Aspect | Schema Evolution | Schema Watcher |
|--------|------------------|----------------|
| **Purpose** | Historical analysis | Real-time monitoring |
| **Temporal Focus** | Past changes | Ongoing detection |
| **Output** | Version timeline | Alerts and notifications |
| **Use Case** | Impact assessment, auditing | Operational awareness, incident response |

## Use Cases

### Pipeline Impact Assessment

When a schema change is detected, engineers can review the version timeline to understand the full scope of the modification. The severity classification provides immediate guidance on whether the change requires pipeline updates.

1. Navigate to Schema Evolution and select the affected source
2. Identify the version where the change occurred
3. Review the change detail table for affected columns
4. Assess whether downstream queries, transformations, or validation rules reference the modified columns
5. Implement necessary adjustments before the change propagates

### Compliance Auditing

Organizations subject to data governance regulations can use the Schema Evolution timeline as an audit trail of structural changes. The versioned history provides evidence of:

- When changes occurred
- What specifically changed
- The severity classification of each change

### Regression Investigation

When data quality issues emerge, the Schema Evolution timeline can help determine whether a recent schema change is the root cause. By correlating the timing of quality regressions with schema version changes, analysts can quickly identify structural causes.

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| **Regular Review** | Periodically review schema evolution to catch unnoticed changes |
| **Pair with Schema Watcher** | Enable Schema Watcher for real-time alerting on new changes |
| **Document Breaking Changes** | Use the Business Glossary to document the rationale for breaking changes |
| **Validate After Changes** | Run validation immediately after detecting a schema change |
| **Track Rename Patterns** | Monitor column renames to update downstream references |

## API Reference

### Schema Evolution Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/schema-evolution` | GET | List schema changes with filtering |
| `/schema-evolution/sources/{id}` | GET | Get schema evolution for a specific source |
| `/schema-evolution/sources/{id}/versions` | GET | List all schema versions for a source |
| `/schema-evolution/sources/{id}/versions/{version}` | GET | Get details of a specific version |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_id` | string | Filter by data source |
| `period` | string | Time period (7d, 30d, 90d) |
| `severity` | string | Filter by severity (breaking, warning, safe) |
| `change_type` | string | Filter by change type |

## Glossary

| Term | Definition |
|------|------------|
| **Schema Version** | A point-in-time snapshot of a data source's structural definition |
| **Breaking Change** | A schema modification that is likely to cause failures in dependent systems |
| **Column Rename Detection** | Heuristic-based identification of columns that were renamed rather than added and removed |
| **Backward Compatibility** | The property of a schema change that allows existing consumers to continue operating without modification |
