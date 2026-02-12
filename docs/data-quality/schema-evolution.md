# Schema Evolution

The Schema Evolution module implements systematic tracking and classification of structural changes in data sources over time. Through the maintenance of a versioned history of schema states, it enables data engineers and quality analysts to identify breaking changes, assess migration impact, and ensure downstream system compatibility.

## Overview

Schema evolution is defined as the process by which the structure of a dataset undergoes modification over time—columns may be added, removed, renamed, or subjected to type alterations. In the absence of active monitoring, such changes can silently compromise data pipelines, invalidate validation rules, and introduce data quality regressions. The Schema Evolution module was designed to address this concern by capturing every schema modification, classifying its severity according to established criteria, and presenting the change history in an accessible timeline format.

## Foundational Concepts

### Schema Version

A schema version is defined as a point-in-time snapshot of a data source's structure. Each version is assigned a sequential version number and encapsulates the complete column definitions, constraints, and metadata of the source as they existed at the moment of capture.

| Attribute | Description |
|-----------|-------------|
| **Version Number** | Sequential identifier (e.g., v1, v2, v3) |
| **Timestamp** | Date and time the version was recorded |
| **Column Definitions** | Complete list of columns with types and constraints |
| **Change Summary** | Number of breaking, warning, and safe changes relative to the prior version |

### Change Types

Six categories of structural change are detected and classified by the system:

| Change Type | Description | Typical Impact |
|-------------|-------------|----------------|
| **column_added** | A new column appears in the schema | Generally safe; downstream systems may ignore unknown columns |
| **column_removed** | An existing column is no longer present | Breaking; queries referencing this column will fail |
| **type_changed** | A column's data type has changed | Breaking or warning depending on type compatibility |
| **nullable_changed** | A column's nullable constraint has changed | Warning; may affect data integrity assumptions |
| **constraint_changed** | A column's constraint (unique, check, etc.) has changed | Warning; may affect validation rules |
| **column_renamed** | A column has been renamed (detected via heuristic matching) | Breaking; references to the old name will fail |

### Severity Classification

Each detected change is assigned a severity level that is intended to reflect its potential impact on downstream systems and data quality processes:

| Severity | Description | Visual Indicator |
|----------|-------------|------------------|
| **Breaking** | Change is likely to cause failures in dependent systems | Red badge |
| **Warning** | Change may affect behavior but is unlikely to cause immediate failure | Amber badge |
| **Safe** | Change is backward-compatible and low risk | Green badge |

The classification algorithm takes into account the change type, the directionality of the change (e.g., the addition versus removal of a NOT NULL constraint), and the degree of compatibility between old and new data types.

## Schema Evolution Interface Specifications

### Source Selection

The interface is initiated with a source selector through which the user may designate the data source whose schema history is to be examined. A period selector is provided for temporal filtering of the displayed changes.

### Summary Statistics

Four summary cards are presented, displaying aggregate metrics for the selected source:

| Card | Description |
|------|-------------|
| **Total Versions** | Number of recorded schema versions |
| **Breaking Changes** | Cumulative count of breaking changes across all versions |
| **Warnings** | Cumulative count of warning-level changes |
| **Safe Changes** | Cumulative count of backward-compatible changes |

### Version Timeline

Schema versions are rendered in reverse chronological order through an accordion interface. Each version entry comprises the following elements:

1. **Version header**: Version number, timestamp, and a "latest" badge for the most recent version
2. **Change summary badges**: Counts of breaking, warning, and safe changes
3. **Change detail table**: Expanded view with per-column change information

The change detail table is structured with the following columns:

| Column | Description |
|--------|-------------|
| **Column Name** | Name of the affected column |
| **Change Type** | Category of change (added, removed, renamed, etc.) |
| **Old Value** | Previous state of the attribute |
| **New Value** | Current state of the attribute |
| **Severity** | Breaking, warning, or safe |
| **Reason** | Human-readable explanation of the change |

## Integration with Schema Watcher

The Schema Evolution module is designed to operate in conjunction with the [Schema Watcher](./schema-watcher.md) module. Whereas Schema Evolution provides a historical view of changes that have already been recorded, Schema Watcher is responsible for continuous monitoring and the issuance of real-time alerts when new changes are detected.

| Aspect | Schema Evolution | Schema Watcher |
|--------|------------------|----------------|
| **Purpose** | Historical analysis | Real-time monitoring |
| **Temporal Focus** | Past changes | Ongoing detection |
| **Output** | Version timeline | Alerts and notifications |
| **Use Case** | Impact assessment, auditing | Operational awareness, incident response |

## Analytical Application Scenarios

### Pipeline Impact Assessment

When a schema change is detected, the version timeline may be consulted to ascertain the full scope of the modification. The severity classification provides immediate guidance as to whether the change necessitates pipeline updates.

1. Navigate to Schema Evolution and select the affected source
2. Identify the version where the change occurred
3. Review the change detail table for affected columns
4. Assess whether downstream queries, transformations, or validation rules reference the modified columns
5. Implement necessary adjustments before the change propagates

### Compliance Auditing

Organizations subject to data governance regulations may employ the Schema Evolution timeline as a formal audit trail of structural changes. The versioned history constitutes evidence of:

- When changes occurred
- What specifically was modified
- The severity classification assigned to each change

### Regression Investigation

When data quality issues are observed, the Schema Evolution timeline may be consulted to determine whether a recent schema change constitutes the root cause. By correlating the temporal occurrence of quality regressions with schema version changes, analysts are able to identify structural causes with greater precision.

## Recommended Operational Practices

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
