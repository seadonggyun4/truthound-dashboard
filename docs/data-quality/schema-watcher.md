# Schema Watcher

The Schema Watcher module provides continuous schema monitoring with alerting capabilities, breaking change detection, rename detection using similarity algorithms, and comprehensive version management with diff and rollback capabilities.

## Overview

Schema evolution is an inevitable aspect of data system lifecycles. As business requirements change, database schemas must adapt through column additions, type modifications, constraint changes, and structural reorganizations. While schema evolution tracking provides point-in-time schema change analysis, Schema Watcher establishes persistent monitoring configurations that execute automatically, generate alerts when schema changes are detected, and provide analytical tools to understand and address schema modifications.

The Schema Watcher module integrates with truthound's Schema Evolution subsystem (`truthound.profiler.evolution`) to leverage enterprise-grade capabilities including:

- **SchemaEvolutionDetector**: Core change detection engine
- **SchemaHistory**: Version management with multiple strategies
- **SchemaWatcher**: Continuous monitoring orchestration
- **ColumnRenameDetector**: Similarity-based rename detection
- **BreakingChangeAlertManager**: Alert lifecycle management
- **ImpactAnalyzer**: Downstream impact assessment

## Theoretical Foundation

### Schema Version Management

Schema versioning follows established software engineering practices adapted for data governance. The module supports four distinct versioning strategies, each optimized for different organizational workflows.

#### Semantic Versioning

Semantic versioning (SemVer) applies the MAJOR.MINOR.PATCH convention to schema changes:

| Version Component | Trigger Condition | Example |
|-------------------|-------------------|---------|
| **MAJOR** | Breaking changes (column removal, type change) | 1.0.0 → 2.0.0 |
| **MINOR** | Non-breaking additions (new nullable column) | 1.0.0 → 1.1.0 |
| **PATCH** | Metadata changes (comments, constraints) | 1.0.0 → 1.0.1 |

This approach enables downstream consumers to assess compatibility risk through version number analysis alone.

#### Incremental Versioning

Incremental versioning maintains a simple monotonically increasing integer sequence (1, 2, 3, ...). This strategy is appropriate for systems where change magnitude is less relevant than temporal ordering.

#### Timestamp Versioning

Timestamp versioning uses ISO 8601 datetime strings as version identifiers (e.g., `2024-01-15T10:30:00Z`). This approach provides immediate temporal context and integrates naturally with time-series analysis.

#### Git-Integrated Versioning

Git versioning synchronizes schema versions with repository commit history, enabling correlation between schema changes and application code modifications. This strategy is particularly valuable in GitOps environments.

### Column Rename Detection

Column renaming presents a detection challenge: from a purely structural perspective, a rename appears as a column deletion followed by an addition. The Schema Watcher module employs similarity algorithms to identify probable renames by comparing the characteristics of removed and added columns.

#### Similarity Algorithms

| Algorithm | Methodology | Optimal Use Case |
|-----------|-------------|------------------|
| **Composite** | Weighted ensemble of multiple algorithms | General-purpose detection (recommended) |
| **Levenshtein** | Edit distance normalized by string length | Typo corrections, minor modifications |
| **Jaro-Winkler** | Character-level similarity with prefix bonus | Names sharing common prefixes |
| **N-gram** | Overlap coefficient of character n-grams | Partial name preservation |
| **Token** | Jaccard similarity of word-level tokens | Multi-word column names |

The composite algorithm applies a weighted combination of the above methods, providing robust detection across diverse naming conventions. The default similarity threshold of 0.8 balances precision (avoiding false positives) against recall (capturing true renames).

#### Similarity Score Interpretation

| Score Range | Interpretation | Recommended Action |
|-------------|----------------|-------------------|
| 0.95 - 1.00 | Near-certain rename | Automatic acceptance |
| 0.85 - 0.94 | Highly probable rename | Review recommended |
| 0.70 - 0.84 | Possible rename | Manual verification required |
| Below 0.70 | Unlikely rename | Treat as add/remove |

### Breaking Change Classification

Schema changes are classified by their impact on downstream consumers:

| Change Type | Breaking | Rationale |
|-------------|----------|-----------|
| **Column Added** | No | Existing queries remain valid |
| **Column Removed** | Yes | References become invalid |
| **Type Changed** | Yes | Type coercion may fail |
| **Nullable Changed** (to non-null) | Yes | Null values cause errors |
| **Nullable Changed** (to nullable) | No | Existing values remain valid |
| **Constraint Relaxed** | No | Existing data remains valid |
| **Constraint Tightened** | Yes | Existing data may violate constraint |
| **Column Renamed** | Conditional | Breaking if not handled |

### Impact Analysis

The ImpactAnalyzer component assesses the scope of schema changes:

| Impact Scope | Definition | Example |
|--------------|------------|---------|
| **Local** | Affects only the immediate table | Adding an optional column |
| **Downstream** | Affects dependent tables and views | Removing a foreign key column |
| **System-wide** | Affects multiple subsystems | Changing a primary key type |

## Features

### Continuous Monitoring

- **Configurable Polling**: Intervals from 10 seconds to 24 hours
- **Automatic Scheduling**: Background execution via APScheduler
- **State Persistence**: Watcher state survives service restarts
- **Error Resilience**: Automatic retry with backoff on failures

### Version Management

- **Multi-Strategy Support**: Semantic, incremental, timestamp, and git versioning
- **Version History**: Complete audit trail of all schema states
- **Version Comparison**: Side-by-side diff between any two versions
- **Rollback Capability**: Restore previous schema versions with migration hints

### Alert Management

- **Severity Classification**: Automatic severity assignment based on change impact
- **Lifecycle Workflow**: Open → Acknowledged → Resolved states
- **Notification Integration**: Webhook, email, and Slack notifications
- **Alert Suppression**: Dismiss non-actionable alerts

### Rename Detection

- **Multiple Algorithms**: Composite, Levenshtein, Jaro-Winkler, N-gram, Token
- **Configurable Threshold**: Precision/recall trade-off adjustment
- **Candidate Ranking**: Multiple candidates presented in confidence order

## Schema Watcher Management

### Statistics Dashboard

The monitoring interface displays aggregate statistics:

| Metric | Description |
|--------|-------------|
| **Total Watchers** | Count of all configured schema watchers |
| **Active Watchers** | Count of watchers currently executing on schedule |
| **Paused Watchers** | Count of watchers temporarily suspended |
| **Error Watchers** | Count of watchers in error state |
| **Total Alerts** | Total schema change alerts |
| **Open Alerts** | Unresolved schema change alerts |
| **Acknowledged Alerts** | Alerts marked as seen |
| **Resolved Alerts** | Alerts that have been addressed |

### Creating a Schema Watcher

1. Click the **Create Watcher** button
2. Configure the watcher parameters:
   - **Name**: Descriptive identifier for the watcher
   - **Data Source**: The data source to monitor for schema changes
   - **Poll Interval**: How frequently to check for schema changes
   - **Only Breaking Changes**: Only create alerts for breaking schema changes
   - **Enable Rename Detection**: Detect column renames using similarity algorithms
   - **Similarity Algorithm**: Algorithm for rename detection (composite, levenshtein, jaro_winkler, ngram, token)
   - **Rename Similarity Threshold**: Threshold for rename detection (0.0-1.0)
   - **Version Strategy**: How to version schema changes
   - **Notify on Change**: Send notifications when changes are detected
   - **Track History**: Track schema changes in history
3. Save the watcher configuration

### Poll Interval Options

| Interval | Use Case |
|----------|----------|
| 10 seconds | High-frequency monitoring for critical schemas |
| 30 seconds | Near real-time monitoring |
| 1 minute | Standard monitoring |
| 5 minutes | Regular monitoring |
| 10 minutes | Moderate monitoring |
| 30 minutes | Low-frequency monitoring |
| 1 hour | Hourly checks |
| 6 hours | Periodic checks |
| 12 hours | Twice daily |
| 24 hours | Daily monitoring |

### Watcher Lifecycle Operations

| Action | Description |
|--------|-------------|
| **Check Now** | Execute the watcher immediately, independent of schedule |
| **Pause** | Suspend scheduled execution while preserving configuration |
| **Resume** | Reactivate a paused watcher |
| **Stop** | Permanently stop the watcher |
| **Edit** | Modify watcher configuration |
| **Delete** | Remove the watcher and its history |

### Watcher Status

| Status | Description |
|--------|-------------|
| **Active** | Watcher is running and checking for changes on schedule |
| **Paused** | Watcher is temporarily suspended |
| **Stopped** | Watcher is permanently stopped |
| **Error** | Watcher encountered errors (3+ consecutive failures) |

## Version Management

### Version History Tab

The Versions tab provides comprehensive schema version management:

#### Version List

Each version entry displays:

| Attribute | Description |
|-----------|-------------|
| **Version** | Version identifier (format depends on strategy) |
| **Column Count** | Number of columns in this version |
| **Created At** | Timestamp when version was recorded |
| **Actions** | View details, compare, rollback options |

#### Version Details

The version detail dialog shows:

- **Complete Column List**: All columns with types and constraints
- **Schema Hash**: Cryptographic hash for integrity verification
- **Column Snapshot**: Full metadata for each column
- **Compatibility Status**: Whether changes are backward-compatible

### Version Comparison (Diff)

The diff functionality enables side-by-side comparison between any two schema versions:

#### Comparison View

| Section | Content |
|---------|---------|
| **From Version** | Base version for comparison |
| **To Version** | Target version for comparison |
| **Changes Summary** | Aggregated change statistics |
| **Change Details** | Individual change entries with severity |

#### Change Entry Format

Each change entry includes:

- **Change Type**: Added, removed, modified, renamed
- **Column Name**: Affected column identifier
- **Old Value**: Previous state (if applicable)
- **New Value**: Current state (if applicable)
- **Severity**: Info, warning, or critical
- **Compatibility**: Whether change is backward-compatible

### Schema Rollback

The rollback functionality enables reversion to a previous schema version:

#### Rollback Process

1. Select target version from version history
2. Review migration hints (automatically generated)
3. Confirm rollback operation
4. System generates and applies migration

#### Migration Hints

The rollback system generates migration hints to guide the transition:

| Change Type | Migration Hint |
|-------------|----------------|
| **Column Restore** | `ALTER TABLE ADD COLUMN ... DEFAULT ...` |
| **Type Revert** | `ALTER TABLE ALTER COLUMN ... TYPE ...` |
| **Constraint Restore** | `ALTER TABLE ADD CONSTRAINT ...` |
| **Data Migration** | Required data transformation steps |

#### Rollback Confirmation

The confirmation dialog displays:

- Target version details
- Impact assessment
- Required migration steps
- Potential data loss warnings

## Alerts Tab

### Alert Listing

The Alerts tab displays all schema change alerts with filtering capabilities:

#### Filter Options

- **Status**: Open, Acknowledged, Resolved, Suppressed
- **Severity**: Critical, High, Medium, Low, Info
- **Source**: Filter by data source
- **Watcher**: Filter by watcher

#### Alert Information

| Attribute | Description |
|-----------|-------------|
| **Title** | Summary of the schema change |
| **Severity** | Alert severity level based on breaking changes |
| **Status** | Current alert status |
| **Total Changes** | Number of schema changes detected |
| **Breaking Changes** | Number of breaking changes detected |
| **Created At** | Timestamp when alert was generated |

### Alert Severity

| Severity | Criteria |
|----------|----------|
| **Critical** | 3+ breaking changes detected |
| **High** | 1-2 breaking changes detected |
| **Medium** | 5+ non-breaking changes |
| **Low** | Less than 5 non-breaking changes |
| **Info** | Informational schema update |

### Alert Actions

| Action | Description |
|--------|-------------|
| **Acknowledge** | Mark alert as seen and under investigation |
| **Resolve** | Mark alert as addressed and closed |
| **Suppress** | Dismiss alert as non-actionable |
| **View Details** | See full alert details including changes |

### Alert Details

The alert detail view provides:

- **Changes Summary**: List of all detected changes
- **Impact Scope**: Local, Downstream, or System-wide impact
- **Affected Consumers**: List of downstream systems affected
- **Recommendations**: Suggested actions to address the changes
- **Timeline**: When the alert was acknowledged and resolved
- **Resolution Notes**: Notes about how the alert was resolved

## Run History Tab

### Run Listing

The Run History tab shows all schema check executions:

| Attribute | Description |
|-----------|-------------|
| **Watcher** | The watcher that executed the check |
| **Status** | Pending, Running, Completed, or Failed |
| **Changes Detected** | Number of schema changes found |
| **Breaking Detected** | Number of breaking changes found |
| **Duration** | How long the check took (ms) |
| **Started At** | When the check started |

### Run Status

| Status | Description |
|--------|-------------|
| **Pending** | Run is queued for execution |
| **Running** | Run is currently executing |
| **Completed** | Run finished successfully |
| **Failed** | Run encountered an error |

## Change Types

Schema Watcher detects the following change types:

| Change Type | Breaking | Description |
|-------------|----------|-------------|
| **Column Added** | No | New column added to schema |
| **Column Removed** | Yes | Existing column removed |
| **Type Changed** | Yes | Column data type changed |
| **Nullable Changed** | Depends | Nullable constraint changed |
| **Constraint Changed** | Depends | Column constraint modified |
| **Column Renamed** | Yes* | Column was renamed (detected via similarity) |

*Rename detection can reduce breaking change impact if properly handled.

## API Reference

### Watcher Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/schema-watchers` | List all watchers |
| `POST` | `/api/v1/schema-watchers` | Create a new watcher |
| `GET` | `/api/v1/schema-watchers/{id}` | Get watcher details |
| `PUT` | `/api/v1/schema-watchers/{id}` | Update watcher configuration |
| `DELETE` | `/api/v1/schema-watchers/{id}` | Delete a watcher |
| `POST` | `/api/v1/schema-watchers/{id}/status` | Change watcher status |
| `POST` | `/api/v1/schema-watchers/{id}/check` | Execute check immediately |
| `GET` | `/api/v1/schema-watchers/statistics` | Get aggregate statistics |
| `GET` | `/api/v1/schema-watchers/scheduler/status` | Get scheduler status |

### Version Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/schema-watchers/{id}/versions` | List version history |
| `GET` | `/api/v1/schema-watchers/{id}/versions/{version}` | Get version details |
| `POST` | `/api/v1/schema-watchers/{id}/versions/diff` | Compare two versions |
| `POST` | `/api/v1/schema-watchers/{id}/versions/rollback` | Rollback to version |

### Alert Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/schema-watchers/alerts` | List all alerts |
| `GET` | `/api/v1/schema-watchers/alerts/{id}` | Get alert details |
| `POST` | `/api/v1/schema-watchers/alerts/{id}/acknowledge` | Acknowledge alert |
| `POST` | `/api/v1/schema-watchers/alerts/{id}/resolve` | Resolve alert |

### Run Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/schema-watchers/runs` | List all runs |
| `GET` | `/api/v1/schema-watchers/runs/{id}` | Get run details |

### Example: Create Watcher with Similarity Algorithm

```bash
curl -X POST http://localhost:8765/api/v1/schema-watchers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Users Schema",
    "source_id": "source-uuid",
    "poll_interval_seconds": 300,
    "only_breaking": false,
    "enable_rename_detection": true,
    "similarity_algorithm": "composite",
    "rename_similarity_threshold": 0.8,
    "version_strategy": "semantic",
    "notify_on_change": true,
    "track_history": true
  }'
```

### Example: Compare Schema Versions

```bash
curl -X POST http://localhost:8765/api/v1/schema-watchers/{watcher_id}/versions/diff \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0"
  }'
```

Response:
```json
{
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "changes": [
    {
      "change_type": "column_removed",
      "column_name": "legacy_field",
      "old_value": "VARCHAR(255)",
      "new_value": null,
      "severity": "critical",
      "is_compatible": false
    },
    {
      "change_type": "column_added",
      "column_name": "new_field",
      "old_value": null,
      "new_value": "INTEGER",
      "severity": "info",
      "is_compatible": true
    }
  ],
  "total_changes": 2,
  "breaking_changes": 1,
  "is_compatible": false
}
```

### Example: Rollback Schema Version

```bash
curl -X POST http://localhost:8765/api/v1/schema-watchers/{watcher_id}/versions/rollback \
  -H "Content-Type: application/json" \
  -d '{
    "target_version": "1.0.0",
    "dry_run": true
  }'
```

Response:
```json
{
  "success": true,
  "target_version": "1.0.0",
  "current_version": "2.0.0",
  "migration_hints": [
    "ALTER TABLE users ADD COLUMN legacy_field VARCHAR(255)",
    "ALTER TABLE users DROP COLUMN new_field"
  ],
  "warnings": [
    "Data in 'new_field' will be lost"
  ],
  "dry_run": true
}
```

### Example: Check Now

```bash
curl -X POST http://localhost:8765/api/v1/schema-watchers/{watcher_id}/check
```

Response:
```json
{
  "watcher_id": "watcher-uuid",
  "run_id": "run-uuid",
  "status": "completed",
  "changes_detected": 3,
  "breaking_detected": 1,
  "alert_created_id": "alert-uuid",
  "version_created_id": "version-uuid",
  "duration_ms": 245.5,
  "message": "Detected 3 changes (1 breaking)"
}
```

## Scheduler Integration

Schema Watcher is integrated with the validation scheduler for automatic background execution:

- **Check Interval**: The scheduler checks for due watchers every 10 seconds
- **Due Watchers**: Watchers whose `next_check_at` timestamp has passed
- **Automatic Execution**: Due watchers are processed automatically
- **State Updates**: Watcher state is updated after each check

### Scheduler Status

Get the current scheduler status:

```bash
curl http://localhost:8765/api/v1/schema-watchers/scheduler/status
```

Response:
```json
{
  "enabled": true,
  "checker_running": false,
  "checker_interval_seconds": 10,
  "last_checker_run_at": "2024-01-15T10:30:00Z",
  "total_checks": 1250,
  "total_processed": 45
}
```

## Best Practices

### Monitoring Strategy

1. **Critical Schemas**: Use short poll intervals (10-60 seconds) for schemas that affect production systems
2. **Development Schemas**: Use longer intervals (1-6 hours) for non-critical schemas
3. **Breaking Changes Only**: Enable `only_breaking` for high-volume schemas to reduce alert noise

### Rename Detection

1. **Algorithm Selection**:
   - Use **composite** (default) for general-purpose detection
   - Use **levenshtein** for typo-like changes
   - Use **jaro_winkler** for prefix-preserving renames
   - Use **ngram** for partial name preservation
   - Use **token** for multi-word column names

2. **Threshold Tuning**: Set `rename_similarity_threshold` based on your naming conventions
   - 0.9+ for strict matching
   - 0.7-0.8 for moderate matching
   - Below 0.7 may produce false positives

3. **Review Renames**: Always verify detected renames before assuming they are correct

### Version Management

1. **Strategy Selection**:
   - Use **semantic** for production systems requiring compatibility assessment
   - Use **incremental** for simple sequential tracking
   - Use **timestamp** for time-series analysis
   - Use **git** for GitOps environments

2. **Regular Diff Review**: Periodically compare versions to understand evolution patterns

3. **Rollback Testing**: Test rollback procedures in non-production environments first

### Alert Management

1. **Acknowledge Promptly**: Acknowledge alerts to indicate they are being investigated
2. **Resolution Notes**: Add notes when resolving to document what was done
3. **Suppress Noise**: Use suppress for known acceptable changes

### Integration with CI/CD

1. **Pre-deployment Checks**: Run `check_now` before deployments
2. **Post-deployment Monitoring**: Use short intervals immediately after schema changes
3. **Rollback Triggers**: Set up notifications to trigger rollback procedures on breaking changes

## Troubleshooting

### Watcher in Error State

If a watcher enters error state (3+ consecutive failures):

1. Check the `last_error` field for the error message
2. Verify the data source connection is working
3. Check if the schema is accessible
4. Resume the watcher after fixing the issue

### Missing Change Detection

If expected changes are not detected:

1. Verify the poll interval is appropriate
2. Check if the watcher is active
3. Verify the source has the expected schema
4. Check the `enable_rename_detection` setting
5. Review the similarity algorithm and threshold settings

### False Positive Renames

If incorrect renames are detected:

1. Increase the `rename_similarity_threshold` value
2. Consider using a more specific algorithm (e.g., levenshtein for typos)
3. Review the column naming conventions

### High Alert Volume

If too many alerts are generated:

1. Enable `only_breaking` to filter non-breaking changes
2. Increase the poll interval
3. Consider using suppress for known acceptable changes

### Version Rollback Failures

If rollback operations fail:

1. Review the migration hints for completeness
2. Check for data dependencies that prevent rollback
3. Consider using `dry_run: true` to preview changes first
4. Verify database user has sufficient permissions

## References

- truthound Schema Evolution Module: `truthound.profiler.evolution`
- Levenshtein Distance: Levenshtein, V.I. (1966). "Binary codes capable of correcting deletions, insertions, and reversals"
- Jaro-Winkler Similarity: Winkler, W.E. (1990). "String Comparator Metrics and Enhanced Decision Rules in the Fellegi-Sunter Model of Record Linkage"
- Semantic Versioning: https://semver.org/
