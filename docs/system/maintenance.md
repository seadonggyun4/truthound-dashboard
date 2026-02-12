# Maintenance

The Maintenance module provides configuration and execution controls for system maintenance operations, encompassing data retention policy enforcement, database optimization, and cache management. These capabilities are considered essential for sustaining long-term system reliability and operational efficiency.

## Overview

The execution of regular maintenance procedures is fundamental to ensuring optimal system performance and effective management of storage resource consumption. This module enables system administrators to configure retention policies, execute cleanup operations, and monitor key system health metrics in a systematic manner.

## Maintenance Interface

### Maintenance Settings

The Maintenance page exposes configuration capabilities through the MaintenanceSettings component, which serves as the primary interface for administrative control of all maintenance-related parameters.

## Retention Configuration

### Retention Policies

The following table describes the configurable retention policies that govern the duration for which various data categories are preserved within the system:

| Setting | Description | Range |
|---------|-------------|-------|
| **Validation Retention** | Days to keep validation results | 1-365 days |
| **Profile Retention** | Profiles to keep per source | 1-100 count |
| **Notification Log Retention** | Days to keep notification logs | 1-365 days |

### Configuring Retention

The retention configuration procedure is carried out through the following steps:

1. Access Maintenance settings
2. Adjust retention values:
   - **Validation Results**: How many days of validation history to retain
   - **Profile History**: How many profile snapshots per source to keep
   - **Notification Logs**: How many days of notification history to retain
3. Save configuration

### Retention Recommendations

The following recommendations are provided to guide the establishment of appropriate retention periods based on common operational requirements:

| Data Type | Recommended Retention | Rationale |
|-----------|----------------------|-----------|
| **Validation Results** | 30-90 days | Balance history with storage |
| **Profile History** | 10-30 profiles | Track recent trends |
| **Notification Logs** | 14-30 days | Audit trail requirements |

## Cleanup Operation Procedures

### Manual Cleanup

Manual cleanup operations may be initiated on demand through the following procedure:

1. Click **Run Cleanup**
2. System identifies expired data
3. Review cleanup summary
4. Confirm execution
5. Expired data is removed

### Cleanup Scope

The scope of cleanup operations encompasses the following data categories and their corresponding behaviors:

| Data Type | Cleanup Behavior |
|-----------|-----------------|
| **Validation Results** | Delete results older than retention period |
| **Profile History** | Keep most recent N profiles per source |
| **Notification Logs** | Delete logs older than retention period |
| **Expired Reports** | Delete reports past expiration |
| **Orphaned Data** | Remove data without parent references |

### Automatic Cleanup

Automatic cleanup may be configured through the parameters described in the following table. It is recommended that automated scheduling be employed to ensure consistent enforcement of retention policies:

| Setting | Description |
|---------|-------------|
| **Enable Auto Cleanup** | Toggle automatic execution |
| **Cleanup Schedule** | Cron expression for cleanup timing |
| **Cleanup Window** | Preferred execution time window |

## Database Optimization Operations

### VACUUM Operation

The SQLite VACUUM operation is utilized to reclaim unused storage space and optimize the internal structure of the database. The procedure is executed as follows:

1. Click **Run Vacuum**
2. System executes VACUUM operation
3. Database file is optimized
4. Review completion status

### VACUUM Behavior

The operational characteristics of the VACUUM process are summarized in the following table:

| Aspect | Description |
|--------|-------------|
| **Space Recovery** | Reclaims deleted row space |
| **Defragmentation** | Reorganizes database structure |
| **Index Optimization** | Rebuilds indexes |
| **Exclusive Lock** | Requires exclusive database access |

### Automatic VACUUM

The VACUUM operation may be configured to execute in conjunction with cleanup operations:

| Setting | Description |
|---------|-------------|
| **Run VACUUM on Cleanup** | Execute VACUUM after cleanup |

### VACUUM Frequency Recommendations

The appropriate frequency of VACUUM execution is determined by the operational characteristics of the deployment environment, as outlined below:

| Frequency | Use Case |
|-----------|----------|
| **Weekly** | Active systems with frequent deletions |
| **Monthly** | Moderate activity systems |
| **On-Demand** | After large data removals |

## Cache Management and Statistics

### Cache Statistics

The current state of the system cache may be observed through the following metrics:

| Metric | Description |
|--------|-------------|
| **Cache Size** | Current memory consumption |
| **Hit Rate** | Percentage of cache hits |
| **Entry Count** | Number of cached items |
| **Oldest Entry** | Age of oldest cache entry |

### Clear Cache

All cached data may be purged from the system through the following procedure. It should be noted that subsequent requests will incur the overhead of cache reconstruction:

1. Click **Clear Cache**
2. All cached data is removed
3. Cache rebuilds on subsequent requests

### Cache Clearing Use Cases

The following scenarios represent conditions under which cache invalidation is considered appropriate:

| Scenario | Recommendation |
|----------|----------------|
| **Configuration Changes** | Clear after major config updates |
| **Data Corrections** | Clear after data fixes |
| **Memory Pressure** | Clear if memory consumption high |
| **Troubleshooting** | Clear when debugging issues |

## Configuration Reference

### Full Configuration Options

A comprehensive enumeration of all configurable maintenance parameters is provided in the following table:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | Boolean | true | Enable automatic maintenance |
| `validation_retention_days` | Integer | 30 | Validation result retention |
| `profile_keep_per_source` | Integer | 10 | Profiles per source |
| `notification_log_retention_days` | Integer | 14 | Notification log retention |
| `run_vacuum_on_cleanup` | Boolean | true | VACUUM during cleanup |
| `cleanup_schedule` | String | "0 3 * * *" | Cleanup cron expression |

### Configuration via API

Maintenance configuration may be updated programmatically through the API by submitting a JSON payload conforming to the following structure:

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

The current maintenance status of the system may be ascertained through the following observable metrics:

| Metric | Description |
|--------|-------------|
| **Last Cleanup** | Timestamp of last cleanup execution |
| **Last Vacuum** | Timestamp of last VACUUM execution |
| **Next Scheduled** | Timestamp of next scheduled maintenance |
| **Database Size** | Current database file size |
| **Records Cleaned** | Count from last cleanup |

### Maintenance History

A historical record of maintenance operations is maintained and may be reviewed through the following fields:

| Column | Description |
|--------|-------------|
| **Timestamp** | When operation executed |
| **Operation** | Type of operation |
| **Duration** | Execution time |
| **Records Affected** | Data items processed |
| **Status** | Success or failure |

## Storage Management

### Monitoring Storage

System storage consumption should be monitored across the following components and their respective locations:

| Component | Location |
|-----------|----------|
| **Database** | `~/.truthound/dashboard.db` |
| **Logs** | `~/.truthound/logs/` |
| **Reports** | Stored in database |
| **Encryption Key** | `~/.truthound/.key` |

### Storage Optimization

The following practices are recommended for the ongoing optimization of storage utilization:

| Practice | Recommendation |
|----------|----------------|
| **Regular Cleanup** | Execute cleanup weekly minimum |
| **Appropriate Retention** | Set retention matching requirements |
| **Report Management** | Delete unnecessary reports |
| **VACUUM Scheduling** | Schedule regular VACUUM operations |

## Recommended Operational Practices

### Retention Policy Design

The design of retention policies should be informed by the following considerations, which collectively ensure alignment between data governance requirements and system resource constraints:

| Consideration | Recommendation |
|--------------|----------------|
| **Compliance** | Meet regulatory retention requirements |
| **Analysis** | Retain sufficient history for trends |
| **Storage** | Balance retention with storage capacity |
| **Performance** | Shorter retention improves query speed |

### Maintenance Scheduling

The following scheduling practices are recommended to ensure that maintenance operations are conducted reliably and with minimal disruption to normal system operations:

| Practice | Recommendation |
|----------|----------------|
| **Off-Peak** | Schedule during low-activity periods |
| **Consistency** | Use regular schedule |
| **Monitoring** | Verify maintenance completion |
| **Alerting** | Configure alerts for failures |

### Emergency Maintenance

In the event that exceptional conditions arise, the following corrective actions should be undertaken in accordance with the nature of the observed anomaly:

| Situation | Action |
|-----------|--------|
| **High Storage** | Execute immediate cleanup |
| **Slow Performance** | Clear cache and run VACUUM |
| **Database Corruption** | Restore from backup |

## Diagnostic and Troubleshooting Procedures

### Common Issues

The following table enumerates frequently encountered issues and their corresponding resolutions. These diagnostic procedures should be consulted prior to escalation:

| Issue | Resolution |
|-------|------------|
| **Cleanup Not Running** | Verify enabled and schedule |
| **High Storage After Cleanup** | Run VACUUM operation |
| **Slow Queries** | Clear cache, run VACUUM |
| **Missing Historical Data** | Check retention settings |

### Database Recovery

In the event that database integrity issues are detected, the following recovery procedure should be executed in sequential order:

1. Stop the Truthound Dashboard
2. Backup current database file
3. Run SQLite integrity check
4. Restore from backup if necessary
5. Restart the dashboard

## API Reference

The following API endpoints are provided for programmatic interaction with the maintenance subsystem:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/maintenance/config` | GET | Retrieve maintenance configuration |
| `/maintenance/config` | PUT | Update maintenance configuration |
| `/maintenance/status` | GET | Retrieve maintenance status |
| `/maintenance/cleanup` | POST | Execute manual cleanup |
| `/maintenance/vacuum` | POST | Execute manual VACUUM |
| `/maintenance/cache/clear` | POST | Clear system cache |
| `/maintenance/cache/statistics` | GET | Retrieve cache statistics |
