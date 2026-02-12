# Automated Validation Scheduling

The Schedules module facilitates the automated execution of data validation tasks through configurable scheduling mechanisms. Support is provided for cron expressions, interval-based timing, data change triggers, and composite scheduling strategies.

## Conceptual Overview

Scheduled validation serves to automate the data quality monitoring process, thereby ensuring consistent and timely verification of data sources in the absence of manual intervention. Multiple trigger types are supported to accommodate the heterogeneous operational requirements commonly encountered in production environments.

## Schedules Interface

### Schedule Enumeration

The primary Schedules interface presents a tabular listing of all configured schedules:

| Column | Description |
|--------|-------------|
| **Name** | Schedule identifier |
| **Source** | Target data source |
| **Trigger Type** | Scheduling mechanism |
| **Status** | Active, paused, or error |
| **Last Run** | Most recent execution timestamp |
| **Next Run** | Upcoming scheduled execution |
| **Actions** | Available operations |

### Status Indicators

| Status | Color | Description |
|--------|-------|-------------|
| **Active** | Green | Schedule executing as configured |
| **Paused** | Yellow | Schedule temporarily suspended |
| **Error** | Red | Schedule encountered execution errors |

## Schedule Registration

### Schedule Registration Dialog

The registration dialog is organized as a multi-tab interface to facilitate structured configuration.

#### Basic Tab

Fundamental schedule properties are configured within this tab:

| Field | Description |
|-------|-------------|
| **Name** (required) | Descriptive identifier for the schedule |
| **Source** (required) | Data source to validate |
| **Description** | Optional documentation |
| **Enabled** | Toggle schedule activation |

#### Preset Schedules

A set of predefined scheduling configurations is provided for expedient setup:

| Preset | Cron Expression | Description |
|--------|-----------------|-------------|
| **Hourly** | `0 * * * *` | Every hour at minute 0 |
| **Every 6 Hours** | `0 */6 * * *` | Every 6 hours |
| **Daily** | `0 9 * * *` | Daily at 9:00 AM |
| **Weekly** | `0 9 * * 1` | Every Monday at 9:00 AM |
| **Monthly** | `0 9 1 * *` | First of month at 9:00 AM |

#### Advanced Trigger Activation

The Trigger tab is rendered accessible only when the **Use advanced trigger options** toggle has been enabled within the Basic tab. This architectural decision separates simple cron-based scheduling from advanced trigger configurations, thereby reducing interface complexity for standard use cases.

| Toggle State | Behavior |
|--------------|----------|
| **Disabled** (default) | Simple cron preset and expression input displayed directly in the Basic tab. The Trigger tab is disabled. |
| **Enabled** | Cron input is replaced with a guidance message directing the user to the Trigger tab, which becomes active. |

When advanced triggers are enabled, a compatible cron expression is automatically derived for backend scheduling. The conversion rules are specified as follows:

| Trigger Type | Derived Cron Expression | Example |
|--------------|------------------------|---------|
| **Interval** (hours only) | `0 */{hours} * * *` | 2h → `0 */2 * * *` |
| **Interval** (minutes only) | `*/{minutes} * * * *` | 30m → `*/30 * * * *` |
| **Interval** (hours + minutes) | `{minutes} */{hours} * * *` | 2h15m → `15 */2 * * *` |
| **Daily** | `{minute} {hour} * * *` | 09:30 → `30 9 * * *` |
| **Other types** | Fallback `0 * * * *` | — |

#### Trigger Tab

The execution trigger mechanism is configured within this tab.

##### Cron Trigger

Standard cron-based scheduling is supported:

| Component | Values | Description |
|-----------|--------|-------------|
| **Minute** | 0-59 | Minute of the hour |
| **Hour** | 0-23 | Hour of the day |
| **Day of Month** | 1-31 | Day of the month |
| **Month** | 1-12 | Month of the year |
| **Day of Week** | 0-6 | Day of the week (0 = Sunday) |

**Illustrative Cron Expressions:**

| Expression | Meaning |
|------------|---------|
| `0 9 * * *` | Every day at 9:00 AM |
| `0 */6 * * *` | Every 6 hours |
| `30 2 * * 1-5` | Weekdays at 2:30 AM |
| `0 0 1,15 * *` | 1st and 15th of each month |
| `*/15 * * * *` | Every 15 minutes |

##### Interval Trigger

A fixed interval between successive executions may be specified:

| Parameter | Description |
|-----------|-------------|
| **Interval** | Time between executions |
| **Unit** | Minutes, hours, or days |
| **Start Time** | Initial execution time |

##### Data Change Trigger

Execution is initiated upon detection of modifications to the source data:

| Parameter | Description |
|-----------|-------------|
| **Detection Method** | How changes are detected |
| **Debounce** | Minimum time between executions |
| **Columns** | Specific columns to monitor (optional) |

##### Composite Trigger

Multiple trigger conditions may be combined using logical operators:

| Operator | Description |
|----------|-------------|
| **AND** | All conditions must be met |
| **OR** | Any condition triggers execution |

##### Event Trigger

Execution is initiated in response to designated system events:

| Event Type | Description |
|------------|-------------|
| **Source Updated** | When source configuration changes |
| **Schema Changed** | When source schema is modified |
| **Validation Failed** | When another validation fails |
| **Custom Event** | User-defined event types |

##### Manual Trigger

A schedule may be configured to execute exclusively on demand:

- No automatic execution is performed
- The "Run Now" action is employed to initiate manual execution
- This configuration is intended for on-demand validation templates

#### Validators Tab

The selection and configuration of validators for scheduled execution is performed within this tab:

1. Available validators are enumerated (150+ options)
2. Validators to be included are selected
3. Validator-specific parameters are configured
4. Severity overrides are applied as appropriate

##### Validator Configuration

The following settings are available for each selected validator:

| Setting | Description |
|---------|-------------|
| **Enabled** | Include in scheduled execution |
| **Parameters** | Validator-specific settings |
| **Severity Override** | Override default severity |
| **Columns** | Target columns (where applicable) |

##### Preset Templates

| Template | Description |
|----------|-------------|
| **All Validators** | Execute all applicable validators |
| **Quick Check** | Essential validators only |
| **Schema Only** | Schema validation validators |
| **Data Quality** | Comprehensive quality validators |

## Schedule Lifecycle Management

### Immediate Execution

A schedule may be executed immediately, irrespective of its configured timing:

1. Click **Run Now** on the schedule
2. Validation executes with configured settings
3. Results appear in validation history
4. Next scheduled run remains unchanged

Upon completion, the system provides differentiated visual feedback:

| Validation Result | Notification Style | Description |
|-------------------|--------------------|-------------|
| **Passed** | Default (neutral) | All validators passed without issues |
| **Failed** | Destructive (red) | One or more validators reported issues |

This distinction ensures that operators are able to immediately identify whether manual intervention is required following an ad-hoc execution.

### Suspension

Schedule execution may be temporarily suspended:

1. Click **Pause** on the schedule
2. Schedule status changes to "Paused"
3. No automatic executions occur
4. Use **Resume** to reactivate

### Resumption

A previously suspended schedule may be reactivated:

1. Click **Resume** on the paused schedule
2. Schedule status changes to "Active"
3. Next execution calculated from current time
4. Automatic executions continue

### Modification

Schedule configuration may be modified at any time:

1. Click **Edit** on the schedule
2. Update configuration in the dialog
3. Save changes
4. Updated schedule takes effect immediately

### Removal

A schedule may be permanently removed from the system:

1. Click **Delete** on the schedule
2. Confirm deletion
3. Schedule and configuration are removed
4. Historical execution records are preserved

## Notification Configuration

### Establishing Notification Policies

Notifications may be enabled for schedule-related events through the following procedure:

1. Within the schedule configuration, notification delivery is enabled
2. Notification triggers are configured:
   - On validation failure
   - On validation success
   - On schedule error
3. Appropriate notification channels are selected

### Notification Event Taxonomy

| Event | Description |
|-------|-------------|
| **Validation Failed** | Scheduled validation found issues |
| **Validation Passed** | Scheduled validation succeeded |
| **Schedule Error** | Schedule execution encountered error |
| **Timeout** | Validation exceeded time limit |

## Execution History and Audit Trail

### Accessing Execution Records

The execution history for a given schedule is accessed as follows:

1. Click on the schedule name
2. Historical executions are presented, including:
   - Execution timestamp
   - Duration
   - Status (success/failure)
   - Issues found
   - Link to results

### Execution Record Attributes

| Attribute | Description |
|-----------|-------------|
| **Timestamp** | When execution started |
| **Duration** | Total execution time |
| **Status** | Success, failure, or error |
| **Validators Run** | Count of validators executed |
| **Issues Found** | Count of issues identified |
| **Triggered By** | Automatic or manual |

## Truthound Core Library Integration

The Schedules module is built upon truthound's native trigger system, as provided by `truthound.checkpoint.triggers`:

### Core Trigger Type Specifications

| Trigger Type | Truthound Module | Description |
|--------------|------------------|-------------|
| Schedule | `truthound.checkpoint.triggers.ScheduleTrigger` | Time interval-based execution |
| Cron | `truthound.checkpoint.triggers.CronTrigger` | Cron expression scheduling |
| Event | `truthound.checkpoint.triggers.EventTrigger` | External event-driven execution |
| FileWatch | `truthound.checkpoint.triggers.FileWatchTrigger` | File system change detection |

### ScheduleTrigger

The `ScheduleTrigger` provides configurable interval-based scheduling:

| Parameter | Description | Default |
|-----------|-------------|---------|
| interval_seconds | Execution interval in seconds | 0 |
| interval_minutes | Execution interval in minutes | 0 |
| interval_hours | Execution interval in hours | 0 |
| start_time | First execution time | None (immediate) |
| end_time | Last execution time | None (unlimited) |
| run_on_weekdays | Days to run (0=Mon, 6=Sun) | None (all days) |
| timezone | Timezone for scheduling | None (system default) |

### CronTrigger

The `CronTrigger` supports standard cron expressions, with an optional seconds field:

| Format | Fields | Example |
|--------|--------|---------|
| 5-field | minute hour day month weekday | `0 9 * * *` |
| 6-field | second minute hour day month weekday | `30 0 9 * * *` |

### EventTrigger

The `EventTrigger` enables event-driven execution with support for filtering and batching:

| Parameter | Description | Default |
|-----------|-------------|---------|
| event_type | Event type filter | "" |
| event_filter | Filter conditions dictionary | {} |
| debounce_seconds | Minimum time between executions | 0 |
| batch_events | Enable event batching | false |
| batch_window_seconds | Batch collection window | 30 |

### FileWatchTrigger

The `FileWatchTrigger` provides file system change monitoring capabilities:

| Parameter | Description | Default |
|-----------|-------------|---------|
| paths | Directories to monitor | [] |
| patterns | File glob patterns | ["*"] |
| recursive | Include subdirectories | true |
| events | Event types (modified, created, deleted) | ["modified"] |
| ignore_patterns | Patterns to exclude | [] |
| hash_check | Content-based change detection | true |
| poll_interval_seconds | Polling frequency | 5 |

### Common Trigger Configuration Parameters

The following configuration options are applicable to all trigger types:

| Parameter | Description | Default |
|-----------|-------------|---------|
| enabled | Trigger activation state | true |
| max_runs | Maximum execution count (0=unlimited) | 0 |
| run_immediately | Execute on trigger start | false |
| catch_up | Execute missed runs | false |
| max_concurrent | Maximum parallel executions | 1 |

## Recommended Operational Practices

### Schedule Design Considerations

| Consideration | Recommendation |
|--------------|----------------|
| **Frequency** | Balance thoroughness with resource usage |
| **Timing** | Schedule during low-activity periods |
| **Dependencies** | Consider upstream data refresh schedules |
| **Overlap** | Avoid concurrent schedules on same source |

### Validator Selection Guidelines

| Scenario | Recommended Validators |
|----------|----------------------|
| **Frequent (Hourly)** | Quick check validators |
| **Daily** | Standard quality validators |
| **Weekly** | Comprehensive validation suite |
| **On-Demand** | Full validator set |

### Error Handling Strategies

| Situation | Recommended Action |
|-----------|-------------------|
| **Transient Failures** | Configure retry logic |
| **Persistent Failures** | Pause schedule, investigate |
| **Timeout** | Reduce validator scope or increase timeout |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/schedules` | GET | List all schedules |
| `/schedules` | POST | Create a new schedule |
| `/schedules/{id}` | GET | Retrieve schedule details |
| `/schedules/{id}` | PUT | Update schedule configuration |
| `/schedules/{id}` | DELETE | Delete a schedule |
| `/schedules/{id}/pause` | POST | Pause a schedule |
| `/schedules/{id}/resume` | POST | Resume a schedule |
| `/schedules/{id}/run` | POST | Execute schedule immediately |
