# Schedules

The Schedules module enables automated execution of data validation tasks through flexible scheduling mechanisms, supporting cron expressions, interval-based timing, data change triggers, and composite scheduling strategies.

## Overview

Scheduled validation automates the data quality monitoring process, ensuring consistent and timely verification of data sources without manual intervention. The module supports multiple trigger types to accommodate diverse operational requirements.

## Schedules Interface

### Schedule Listing

The main Schedules page displays all configured schedules:

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

## Creating a Schedule

### Schedule Creation Dialog

The creation dialog presents a multi-tab interface:

#### Basic Tab

Configure fundamental schedule properties:

| Field | Description |
|-------|-------------|
| **Name** (required) | Descriptive identifier for the schedule |
| **Source** (required) | Data source to validate |
| **Description** | Optional documentation |
| **Enabled** | Toggle schedule activation |

#### Preset Schedules

Quick configuration options:

| Preset | Cron Expression | Description |
|--------|-----------------|-------------|
| **Hourly** | `0 * * * *` | Every hour at minute 0 |
| **Every 6 Hours** | `0 */6 * * *` | Every 6 hours |
| **Daily** | `0 9 * * *` | Daily at 9:00 AM |
| **Weekly** | `0 9 * * 1` | Every Monday at 9:00 AM |
| **Monthly** | `0 9 1 * *` | First of month at 9:00 AM |

#### Trigger Tab

Configure the execution trigger mechanism:

##### Cron Trigger

Standard cron-based scheduling:

| Component | Values | Description |
|-----------|--------|-------------|
| **Minute** | 0-59 | Minute of the hour |
| **Hour** | 0-23 | Hour of the day |
| **Day of Month** | 1-31 | Day of the month |
| **Month** | 1-12 | Month of the year |
| **Day of Week** | 0-6 | Day of the week (0 = Sunday) |

**Cron Expression Examples:**

| Expression | Meaning |
|------------|---------|
| `0 9 * * *` | Every day at 9:00 AM |
| `0 */6 * * *` | Every 6 hours |
| `30 2 * * 1-5` | Weekdays at 2:30 AM |
| `0 0 1,15 * *` | 1st and 15th of each month |
| `*/15 * * * *` | Every 15 minutes |

##### Interval Trigger

Fixed interval between executions:

| Parameter | Description |
|-----------|-------------|
| **Interval** | Time between executions |
| **Unit** | Minutes, hours, or days |
| **Start Time** | Initial execution time |

##### Data Change Trigger

Execute when source data changes:

| Parameter | Description |
|-----------|-------------|
| **Detection Method** | How changes are detected |
| **Debounce** | Minimum time between executions |
| **Columns** | Specific columns to monitor (optional) |

##### Composite Trigger

Combine multiple trigger conditions:

| Operator | Description |
|----------|-------------|
| **AND** | All conditions must be met |
| **OR** | Any condition triggers execution |

##### Event Trigger

Execute in response to system events:

| Event Type | Description |
|------------|-------------|
| **Source Updated** | When source configuration changes |
| **Schema Changed** | When source schema is modified |
| **Validation Failed** | When another validation fails |
| **Custom Event** | User-defined event types |

##### Manual Trigger

Schedule exists but only executes on demand:

- No automatic execution
- Use "Run Now" to execute manually
- Useful for on-demand validation templates

#### Validators Tab

Configure which validators execute:

1. View available validators (150+ options)
2. Select validators to include
3. Configure validator-specific parameters
4. Set severity overrides if needed

##### Validator Configuration

For each selected validator:

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

## Schedule Management

### Run Now

Execute a schedule immediately:

1. Click **Run Now** on the schedule
2. Validation executes with configured settings
3. Results appear in validation history
4. Next scheduled run remains unchanged

### Pause

Temporarily suspend schedule execution:

1. Click **Pause** on the schedule
2. Schedule status changes to "Paused"
3. No automatic executions occur
4. Use **Resume** to reactivate

### Resume

Reactivate a paused schedule:

1. Click **Resume** on the paused schedule
2. Schedule status changes to "Active"
3. Next execution calculated from current time
4. Automatic executions continue

### Edit

Modify schedule configuration:

1. Click **Edit** on the schedule
2. Update configuration in the dialog
3. Save changes
4. Updated schedule takes effect immediately

### Delete

Remove a schedule:

1. Click **Delete** on the schedule
2. Confirm deletion
3. Schedule and configuration are removed
4. Historical execution records are preserved

## Schedule Notifications

### Configuring Notifications

Enable notifications for schedule events:

1. In the schedule configuration, enable notifications
2. Configure notification triggers:
   - On validation failure
   - On validation success
   - On schedule error
3. Select notification channels

### Notification Events

| Event | Description |
|-------|-------------|
| **Validation Failed** | Scheduled validation found issues |
| **Validation Passed** | Scheduled validation succeeded |
| **Schedule Error** | Schedule execution encountered error |
| **Timeout** | Validation exceeded time limit |

## Schedule Execution History

### Viewing History

Access execution history for a schedule:

1. Click on the schedule name
2. View historical executions:
   - Execution timestamp
   - Duration
   - Status (success/failure)
   - Issues found
   - Link to results

### Execution Details

| Attribute | Description |
|-----------|-------------|
| **Timestamp** | When execution started |
| **Duration** | Total execution time |
| **Status** | Success, failure, or error |
| **Validators Run** | Count of validators executed |
| **Issues Found** | Count of issues identified |
| **Triggered By** | Automatic or manual |

## Best Practices

### Schedule Design

| Consideration | Recommendation |
|--------------|----------------|
| **Frequency** | Balance thoroughness with resource usage |
| **Timing** | Schedule during low-activity periods |
| **Dependencies** | Consider upstream data refresh schedules |
| **Overlap** | Avoid concurrent schedules on same source |

### Validator Selection

| Scenario | Recommended Validators |
|----------|----------------------|
| **Frequent (Hourly)** | Quick check validators |
| **Daily** | Standard quality validators |
| **Weekly** | Comprehensive validation suite |
| **On-Demand** | Full validator set |

### Error Handling

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
