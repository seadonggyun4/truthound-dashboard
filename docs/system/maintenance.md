# Maintenance

The Maintenance module provides configuration and execution controls for system maintenance operations including data retention, database optimization, and cache management.

## Overview

Regular maintenance ensures optimal system performance and manages storage consumption. This module enables administrators to configure retention policies, execute cleanup operations, and monitor system health metrics.

## Maintenance Interface

### Maintenance Settings

The Maintenance page provides configuration through the MaintenanceSettings component.

## Retention Configuration

### Retention Policies

Configure how long different data types are retained:

| Setting | Description | Range |
|---------|-------------|-------|
| **Validation Retention** | Days to keep validation results | 1-365 days |
| **Profile Retention** | Profiles to keep per source | 1-100 count |
| **Notification Log Retention** | Days to keep notification logs | 1-365 days |

### Configuring Retention

1. Access Maintenance settings
2. Adjust retention values:
   - **Validation Results**: How many days of validation history to retain
   - **Profile History**: How many profile snapshots per source to keep
   - **Notification Logs**: How many days of notification history to retain
3. Save configuration

### Retention Recommendations

| Data Type | Recommended Retention | Rationale |
|-----------|----------------------|-----------|
| **Validation Results** | 30-90 days | Balance history with storage |
| **Profile History** | 10-30 profiles | Track recent trends |
| **Notification Logs** | 14-30 days | Audit trail requirements |

## Cleanup Operations

### Manual Cleanup

Execute cleanup operations on demand:

1. Click **Run Cleanup**
2. System identifies expired data
3. Review cleanup summary
4. Confirm execution
5. Expired data is removed

### Cleanup Scope

Cleanup operations process:

| Data Type | Cleanup Behavior |
|-----------|-----------------|
| **Validation Results** | Delete results older than retention period |
| **Profile History** | Keep most recent N profiles per source |
| **Notification Logs** | Delete logs older than retention period |
| **Expired Reports** | Delete reports past expiration |
| **Orphaned Data** | Remove data without parent references |

### Automatic Cleanup

Configure automatic cleanup:

| Setting | Description |
|---------|-------------|
| **Enable Auto Cleanup** | Toggle automatic execution |
| **Cleanup Schedule** | Cron expression for cleanup timing |
| **Cleanup Window** | Preferred execution time window |

## Database Optimization

### VACUUM Operation

SQLite VACUUM reclaims unused space and optimizes database:

1. Click **Run Vacuum**
2. System executes VACUUM operation
3. Database file is optimized
4. Review completion status

### VACUUM Behavior

| Aspect | Description |
|--------|-------------|
| **Space Recovery** | Reclaims deleted row space |
| **Defragmentation** | Reorganizes database structure |
| **Index Optimization** | Rebuilds indexes |
| **Exclusive Lock** | Requires exclusive database access |

### Automatic VACUUM

Configure VACUUM with cleanup:

| Setting | Description |
|---------|-------------|
| **Run VACUUM on Cleanup** | Execute VACUUM after cleanup |

### VACUUM Recommendations

| Frequency | Use Case |
|-----------|----------|
| **Weekly** | Active systems with frequent deletions |
| **Monthly** | Moderate activity systems |
| **On-Demand** | After large data removals |

## Cache Management

### Cache Statistics

View current cache state:

| Metric | Description |
|--------|-------------|
| **Cache Size** | Current memory consumption |
| **Hit Rate** | Percentage of cache hits |
| **Entry Count** | Number of cached items |
| **Oldest Entry** | Age of oldest cache entry |

### Clear Cache

Remove all cached data:

1. Click **Clear Cache**
2. All cached data is removed
3. Cache rebuilds on subsequent requests

### Cache Clearing Use Cases

| Scenario | Recommendation |
|----------|----------------|
| **Configuration Changes** | Clear after major config updates |
| **Data Corrections** | Clear after data fixes |
| **Memory Pressure** | Clear if memory consumption high |
| **Troubleshooting** | Clear when debugging issues |

## Configuration Reference

### Full Configuration Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | Boolean | true | Enable automatic maintenance |
| `validation_retention_days` | Integer | 30 | Validation result retention |
| `profile_keep_per_source` | Integer | 10 | Profiles per source |
| `notification_log_retention_days` | Integer | 14 | Notification log retention |
| `run_vacuum_on_cleanup` | Boolean | true | VACUUM during cleanup |
| `cleanup_schedule` | String | "0 3 * * *" | Cleanup cron expression |

### Configuration via API

Update configuration programmatically:

```json
{
  "enabled": true,
  "validation_retention_days": 30,
  "profile_keep_per_source": 10,
  "notification_log_retention_days": 14,
  "run_vacuum_on_cleanup": true
}
```

## Maintenance Status

### Status Monitoring

View current maintenance status:

| Metric | Description |
|--------|-------------|
| **Last Cleanup** | Timestamp of last cleanup execution |
| **Last Vacuum** | Timestamp of last VACUUM execution |
| **Next Scheduled** | Timestamp of next scheduled maintenance |
| **Database Size** | Current database file size |
| **Records Cleaned** | Count from last cleanup |

### Maintenance History

View historical maintenance operations:

| Column | Description |
|--------|-------------|
| **Timestamp** | When operation executed |
| **Operation** | Type of operation |
| **Duration** | Execution time |
| **Records Affected** | Data items processed |
| **Status** | Success or failure |

## Storage Management

### Monitoring Storage

Track storage consumption:

| Component | Location |
|-----------|----------|
| **Database** | `~/.truthound/dashboard.db` |
| **Logs** | `~/.truthound/logs/` |
| **Reports** | Stored in database |
| **Encryption Key** | `~/.truthound/.key` |

### Storage Optimization

| Practice | Recommendation |
|----------|----------------|
| **Regular Cleanup** | Execute cleanup weekly minimum |
| **Appropriate Retention** | Set retention matching requirements |
| **Report Management** | Delete unnecessary reports |
| **VACUUM Scheduling** | Schedule regular VACUUM operations |

## Best Practices

### Retention Policy Design

| Consideration | Recommendation |
|--------------|----------------|
| **Compliance** | Meet regulatory retention requirements |
| **Analysis** | Retain sufficient history for trends |
| **Storage** | Balance retention with storage capacity |
| **Performance** | Shorter retention improves query speed |

### Maintenance Scheduling

| Practice | Recommendation |
|----------|----------------|
| **Off-Peak** | Schedule during low-activity periods |
| **Consistency** | Use regular schedule |
| **Monitoring** | Verify maintenance completion |
| **Alerting** | Configure alerts for failures |

### Emergency Maintenance

| Situation | Action |
|-----------|--------|
| **High Storage** | Execute immediate cleanup |
| **Slow Performance** | Clear cache and run VACUUM |
| **Database Corruption** | Restore from backup |

## Troubleshooting

### Common Issues

| Issue | Resolution |
|-------|------------|
| **Cleanup Not Running** | Verify enabled and schedule |
| **High Storage After Cleanup** | Run VACUUM operation |
| **Slow Queries** | Clear cache, run VACUUM |
| **Missing Historical Data** | Check retention settings |

### Database Recovery

If database issues occur:

1. Stop the Truthound Dashboard
2. Backup current database file
3. Run SQLite integrity check
4. Restore from backup if necessary
5. Restart the dashboard

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/maintenance/config` | GET | Retrieve maintenance configuration |
| `/maintenance/config` | PUT | Update maintenance configuration |
| `/maintenance/status` | GET | Retrieve maintenance status |
| `/maintenance/cleanup` | POST | Execute manual cleanup |
| `/maintenance/vacuum` | POST | Execute manual VACUUM |
| `/maintenance/cache/clear` | POST | Clear system cache |
| `/maintenance/cache/statistics` | GET | Retrieve cache statistics |
