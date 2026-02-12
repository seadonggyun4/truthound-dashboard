# Schema Watcher

The Schema Watcher module implements continuous schema surveillance with integrated alerting capabilities, breaking change detection, rename detection through similarity algorithms, and comprehensive version management encompassing diff and rollback functionality.

## Overview

Schema evolution is recognized as an inevitable aspect of data system lifecycles. As business requirements undergo transformation, database schemas must be adapted through column additions, type modifications, constraint alterations, and structural reorganizations. Whereas schema evolution tracking provides point-in-time schema change analysis, the Schema Watcher establishes persistent monitoring configurations that are executed automatically, generates alerts upon detection of schema changes, and furnishes analytical tools for the comprehension and remediation of schema modifications.

The Schema Watcher module is integrated with truthound's Schema Evolution subsystem (`truthound.profiler.evolution`) to leverage enterprise-grade capabilities, including:

- **SchemaEvolutionDetector**: Core change detection engine
- **SchemaHistory**: Version management with multiple strategies
- **SchemaWatcher**: Continuous monitoring orchestration
- **ColumnRenameDetector**: Similarity-based rename detection
- **BreakingChangeAlertManager**: Alert lifecycle management
- **ImpactAnalyzer**: Downstream impact assessment

## Theoretical Foundation

### Schema Version Management

Schema versioning adheres to established software engineering practices that have been adapted for data governance contexts. The module supports four distinct versioning strategies, each of which has been optimized for different organizational workflows.

#### Semantic Versioning

Semantic versioning (SemVer) applies the MAJOR.MINOR.PATCH convention to schema changes:

| Version Component | Trigger Condition | Example |
|-------------------|-------------------|---------|
| **MAJOR** | Breaking changes (column removal, type change) | 1.0.0 → 2.0.0 |
| **MINOR** | Non-breaking additions (new nullable column) | 1.0.0 → 1.1.0 |
| **PATCH** | Metadata changes (comments, constraints) | 1.0.0 → 1.0.1 |

This approach enables downstream consumers to assess compatibility risk through version number analysis alone.

#### Incremental Versioning

Incremental versioning maintains a simple monotonically increasing integer sequence (1, 2, 3, ...). This strategy is deemed appropriate for systems in which change magnitude is considered less relevant than temporal ordering.

#### Timestamp Versioning

Timestamp versioning employs ISO 8601 datetime strings as version identifiers (e.g., `2024-01-15T10:30:00Z`). This approach provides immediate temporal context and is naturally integrated with time-series analysis methodologies.

#### Git-Integrated Versioning

Git versioning synchronizes schema versions with repository commit history, thereby enabling correlation between schema changes and application code modifications. This strategy is considered particularly valuable in GitOps environments.

### Column Rename Detection

Column renaming presents a significant detection challenge: from a purely structural perspective, a rename manifests as a column deletion followed by an addition. The Schema Watcher module employs similarity algorithms to identify probable renames by comparing the characteristics of removed and added columns.

#### Similarity Algorithms

| Algorithm | Methodology | Optimal Use Case |
|-----------|-------------|------------------|
| **Composite** | Weighted ensemble of multiple algorithms | General-purpose detection (recommended) |
| **Levenshtein** | Edit distance normalized by string length | Typo corrections, minor modifications |
| **Jaro-Winkler** | Character-level similarity with prefix bonus | Names sharing common prefixes |
| **N-gram** | Overlap coefficient of character n-grams | Partial name preservation |
| **Token** | Jaccard similarity of word-level tokens | Multi-word column names |

The composite algorithm applies a weighted combination of the above methods, thereby providing robust detection across diverse naming conventions. The default similarity threshold of 0.8 is established to balance precision (the avoidance of false positives) against recall (the capture of true renames).

#### Similarity Score Interpretation

| Score Range | Interpretation | Recommended Action |
|-------------|----------------|-------------------|
| 0.95 - 1.00 | Near-certain rename | Automatic acceptance |
| 0.85 - 0.94 | Highly probable rename | Review recommended |
| 0.70 - 0.84 | Possible rename | Manual verification required |
| Below 0.70 | Unlikely rename | Treat as add/remove |

### Breaking Change Classification

Schema changes are classified according to their impact on downstream consumers:

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

The ImpactAnalyzer component is employed to assess the scope of schema changes:

| Impact Scope | Definition | Example |
|--------------|------------|---------|
| **Local** | Affects only the immediate table | Adding an optional column |
| **Downstream** | Affects dependent tables and views | Removing a foreign key column |
| **System-wide** | Affects multiple subsystems | Changing a primary key type |

## Capability Summary

### Continuous Monitoring

- **Configurable Polling**: Intervals ranging from 10 seconds to 24 hours are supported
- **Automatic Scheduling**: Background execution is orchestrated via APScheduler
- **State Persistence**: Watcher state is preserved across service restarts
- **Error Resilience**: Automatic retry with exponential backoff is applied upon failure

### Version Management

- **Multi-Strategy Support**: Semantic, incremental, timestamp, and git versioning strategies are provided
- **Version History**: A complete audit trail of all schema states is maintained
- **Version Comparison**: Side-by-side diff between any two versions may be performed
- **Rollback Capability**: Restoration to previous schema versions is facilitated with migration hints

### Alert Management

- **Severity Classification**: Severity is automatically assigned based on change impact assessment
- **Lifecycle Workflow**: Alerts transition through Open, Acknowledged, and Resolved states
- **Notification Integration**: Webhook, email, and Slack notification channels are supported
- **Alert Suppression**: Non-actionable alerts may be dismissed

### Rename Detection

- **Multiple Algorithms**: Composite, Levenshtein, Jaro-Winkler, N-gram, and Token algorithms are available
- **Configurable Threshold**: The precision/recall trade-off may be adjusted
- **Candidate Ranking**: Multiple candidates are presented in descending confidence order

## Schema Watcher Lifecycle Management

### Statistics Dashboard

The monitoring interface presents aggregate statistics as follows:

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

The following procedure is to be followed for watcher creation:

1. The **Create Watcher** button is to be selected
2. The watcher parameters are to be configured:
   - **Name**: A descriptive identifier for the watcher
   - **Data Source**: The data source to be monitored for schema changes
   - **Poll Interval**: The frequency at which schema changes are to be checked
   - **Only Breaking Changes**: When enabled, alerts are generated exclusively for breaking schema changes
   - **Enable Rename Detection**: Enables column rename detection using similarity algorithms
   - **Similarity Algorithm**: The algorithm employed for rename detection (composite, levenshtein, jaro_winkler, ngram, token)
   - **Rename Similarity Threshold**: The threshold for rename detection (0.0-1.0)
   - **Version Strategy**: The strategy by which schema changes are versioned
   - **Notify on Change**: Determines whether notifications are dispatched upon change detection
   - **Track History**: Determines whether schema changes are recorded in history
3. The watcher configuration is to be saved

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
| **Check Now** | The watcher is executed immediately, independent of its schedule |
| **Pause** | Scheduled execution is suspended while the configuration is preserved |
| **Resume** | A paused watcher is reactivated |
| **Stop** | The watcher is permanently stopped |
| **Edit** | The watcher configuration is modified |
| **Delete** | The watcher and its associated history are removed |

### Watcher Status

| Status | Description |
|--------|-------------|
| **Active** | The watcher is running and checking for changes on schedule |
| **Paused** | The watcher is temporarily suspended |
| **Stopped** | The watcher has been permanently stopped |
| **Error** | The watcher has encountered errors (3+ consecutive failures) |

## Version Management

### Version History Tab

The Versions tab provides comprehensive schema version management capabilities:

#### Version List

Each version entry presents the following attributes:

| Attribute | Description |
|-----------|-------------|
| **Version** | Version identifier (format is determined by the selected strategy) |
| **Column Count** | Number of columns in this version |
| **Created At** | Timestamp indicating when the version was recorded |
| **Actions** | View details, compare, and rollback options |

#### Version Details

The version detail dialog presents the following information:

- **Complete Column List**: All columns with their associated types and constraints
- **Schema Hash**: A cryptographic hash for integrity verification
- **Column Snapshot**: Full metadata for each column
- **Compatibility Status**: An indication of whether changes are backward-compatible

### Version Comparison (Diff)

The diff functionality enables side-by-side comparison between any two schema versions:

#### Comparison View

| Section | Content |
|---------|---------|
| **From Version** | Base version selected for comparison |
| **To Version** | Target version selected for comparison |
| **Changes Summary** | Aggregated change statistics |
| **Change Details** | Individual change entries with associated severity |

#### Change Entry Format

Each change entry encompasses the following fields:

- **Change Type**: Added, removed, modified, or renamed
- **Column Name**: The affected column identifier
- **Old Value**: The previous state (if applicable)
- **New Value**: The current state (if applicable)
- **Severity**: Info, warning, or critical
- **Compatibility**: An indication of whether the change is backward-compatible

### Schema Rollback

The rollback functionality enables reversion to a previously recorded schema version:

#### Rollback Process

1. The target version is selected from the version history
2. Migration hints (which are automatically generated) are reviewed
3. The rollback operation is confirmed
4. The system generates and applies the requisite migration

#### Migration Hints

The rollback system generates migration hints to guide the transition process:

| Change Type | Migration Hint |
|-------------|----------------|
| **Column Restore** | `ALTER TABLE ADD COLUMN ... DEFAULT ...` |
| **Type Revert** | `ALTER TABLE ALTER COLUMN ... TYPE ...` |
| **Constraint Restore** | `ALTER TABLE ADD CONSTRAINT ...` |
| **Data Migration** | Required data transformation steps |

#### Rollback Confirmation

The confirmation dialog presents the following information:

- Target version details
- Impact assessment
- Required migration steps
- Potential data loss warnings

## Alerts Tab

### Alert Listing

The Alerts tab presents all schema change alerts with filtering capabilities:

#### Filter Options

- **Status**: Open, Acknowledged, Resolved, Suppressed
- **Severity**: Critical, High, Medium, Low, Info
- **Source**: Filter by data source
- **Watcher**: Filter by watcher

#### Alert Information

| Attribute | Description |
|-----------|-------------|
| **Title** | A summary of the schema change |
| **Severity** | The alert severity level, determined by breaking change assessment |
| **Status** | The current alert status |
| **Total Changes** | The number of schema changes detected |
| **Breaking Changes** | The number of breaking changes detected |
| **Created At** | The timestamp indicating when the alert was generated |

### Alert Severity

| Severity | Criteria |
|----------|----------|
| **Critical** | 3+ breaking changes have been detected |
| **High** | 1-2 breaking changes have been detected |
| **Medium** | 5+ non-breaking changes have been detected |
| **Low** | Fewer than 5 non-breaking changes have been detected |
| **Info** | Informational schema update |

### Alert Actions

| Action | Description |
|--------|-------------|
| **Acknowledge** | The alert is marked as seen and under investigation |
| **Resolve** | The alert is marked as addressed and closed |
| **Suppress** | The alert is dismissed as non-actionable |
| **View Details** | Full alert details, including changes, are displayed |

### Alert Details

The alert detail view provides the following information:

- **Changes Summary**: A listing of all detected changes
- **Impact Scope**: Local, Downstream, or System-wide impact classification
- **Affected Consumers**: A listing of downstream systems that are affected
- **Recommendations**: Suggested actions to address the identified changes
- **Timeline**: Timestamps indicating when the alert was acknowledged and resolved
- **Resolution Notes**: Documentation of how the alert was resolved

## Run History Tab

### Run Listing

The Run History tab presents all schema check executions:

| Attribute | Description |
|-----------|-------------|
| **Watcher** | The watcher that executed the check |
| **Status** | Pending, Running, Completed, or Failed |
| **Changes Detected** | The number of schema changes identified |
| **Breaking Detected** | The number of breaking changes identified |
| **Duration** | The elapsed time for the check (ms) |
| **Started At** | The timestamp indicating when the check commenced |

### Run Status

| Status | Description |
|--------|-------------|
| **Pending** | The run is queued for execution |
| **Running** | The run is currently being executed |
| **Completed** | The run has finished successfully |
| **Failed** | The run encountered an error |

## Change Types

The Schema Watcher is designed to detect the following change types:

| Change Type | Breaking | Description |
|-------------|----------|-------------|
| **Column Added** | No | A new column has been added to the schema |
| **Column Removed** | Yes | An existing column has been removed |
| **Type Changed** | Yes | A column data type has been changed |
| **Nullable Changed** | Depends | A nullable constraint has been changed |
| **Constraint Changed** | Depends | A column constraint has been modified |
| **Column Renamed** | Yes* | A column has been renamed (detected via similarity) |

*It should be noted that rename detection can reduce breaking change impact if the rename is properly handled.

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

The Schema Watcher is integrated with the validation scheduler to facilitate automatic background execution:

- **Check Interval**: The scheduler examines due watchers at an interval of every 10 seconds
- **Due Watchers**: Watchers whose `next_check_at` timestamp has elapsed are identified
- **Automatic Execution**: Due watchers are processed automatically without manual intervention
- **State Updates**: Watcher state is updated subsequent to each check

### Scheduler Status

The current scheduler status may be obtained as follows:

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

## Recommended Operational Practices

### Monitoring Strategy

1. **Critical Schemas**: It is recommended that short poll intervals (10-60 seconds) be employed for schemas that affect production systems
2. **Development Schemas**: Longer intervals (1-6 hours) are considered appropriate for non-critical schemas
3. **Breaking Changes Only**: Enabling `only_breaking` is advised for high-volume schemas to reduce alert noise

### Rename Detection

1. **Algorithm Selection**:
   - The **composite** algorithm (default) is recommended for general-purpose detection
   - The **levenshtein** algorithm is suited for typo-like changes
   - The **jaro_winkler** algorithm is optimal for prefix-preserving renames
   - The **ngram** algorithm is appropriate for partial name preservation
   - The **token** algorithm is designed for multi-word column names

2. **Threshold Tuning**: The `rename_similarity_threshold` should be configured based on prevailing naming conventions
   - 0.9+ for strict matching requirements
   - 0.7-0.8 for moderate matching requirements
   - Values below 0.7 may produce false positives and are generally discouraged

3. **Review of Detected Renames**: It is strongly recommended that all detected renames be verified before they are accepted as correct

### Version Management

1. **Strategy Selection**:
   - The **semantic** strategy is recommended for production systems requiring compatibility assessment
   - The **incremental** strategy is appropriate for simple sequential tracking
   - The **timestamp** strategy is suited for time-series analysis
   - The **git** strategy is recommended for GitOps environments

2. **Regular Diff Review**: Periodic comparison of versions is advised to identify and understand evolution patterns

3. **Rollback Testing**: It is recommended that rollback procedures be tested in non-production environments prior to their use in production

### Alert Management

1. **Prompt Acknowledgment**: Alerts should be acknowledged in a timely manner to indicate that they are under investigation
2. **Resolution Notes**: Detailed notes should be appended when resolving alerts to document the actions taken
3. **Noise Suppression**: The suppress functionality should be utilized for known acceptable changes

### Integration with CI/CD Pipelines

1. **Pre-deployment Checks**: Execution of `check_now` prior to deployments is recommended
2. **Post-deployment Monitoring**: Short polling intervals should be employed immediately following schema changes
3. **Rollback Triggers**: Notifications should be configured to trigger rollback procedures upon detection of breaking changes

## Diagnostic and Troubleshooting Procedures

### Watcher in Error State

If a watcher enters an error state (3+ consecutive failures), the following diagnostic procedure should be followed:

1. The `last_error` field should be examined for the error message
2. The data source connection should be verified to be operational
3. Schema accessibility should be confirmed
4. The watcher may be resumed after the underlying issue has been resolved

### Missing Change Detection

If expected changes are not being detected, the following investigative steps are recommended:

1. It should be verified that the poll interval is appropriate for the expected change frequency
2. The watcher status should be confirmed as active
3. The source should be verified to contain the expected schema
4. The `enable_rename_detection` setting should be reviewed
5. The similarity algorithm and threshold settings should be examined

### False Positive Renames

If incorrect renames are being detected, the following corrective measures are recommended:

1. The `rename_similarity_threshold` value should be increased
2. A more specific algorithm (e.g., levenshtein for typographical corrections) should be considered
3. The prevailing column naming conventions should be reviewed

### High Alert Volume

If an excessive number of alerts is being generated, the following mitigation strategies should be applied:

1. The `only_breaking` option should be enabled to filter non-breaking changes
2. The poll interval should be increased
3. The suppress functionality should be utilized for known acceptable changes

### Version Rollback Failures

If rollback operations fail, the following diagnostic steps should be undertaken:

1. The migration hints should be reviewed for completeness and accuracy
2. Data dependencies that may prevent rollback should be identified
3. The `dry_run: true` option should be employed to preview changes prior to execution
4. It should be verified that the database user possesses sufficient permissions

## References

- truthound Schema Evolution Module: `truthound.profiler.evolution`
- Levenshtein Distance: Levenshtein, V.I. (1966). "Binary codes capable of correcting deletions, insertions, and reversals"
- Jaro-Winkler Similarity: Winkler, W.E. (1990). "String Comparator Metrics and Enhanced Decision Rules in the Fellegi-Sunter Model of Record Linkage"
- Semantic Versioning: https://semver.org/
