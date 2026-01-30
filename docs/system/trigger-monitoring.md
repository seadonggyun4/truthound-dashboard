# Trigger Monitoring

The Trigger Monitoring module provides real-time visibility into the execution state of all configured triggers within the scheduling system. It enables operators to observe trigger health, track cooldown states, inspect execution history, and manage webhook endpoints for external system integration.

## Overview

Truthound Dashboard's scheduling system supports six distinct trigger types that determine when and how validations are executed. While the [Schedules](./schedules.md) module is concerned with creating and configuring triggers, the Trigger Monitoring module focuses on their operational state—whether they are firing correctly, in cooldown, failing, or awaiting external input.

This separation of concerns follows the principle that configuration and monitoring are distinct operational activities, each requiring a purpose-built interface.

## Trigger Types

The scheduling system supports the following trigger types, each with distinct monitoring characteristics:

| Trigger Type | Description | Monitoring Focus |
|--------------|-------------|------------------|
| **Cron** | Time-based scheduling using cron expressions | Next fire time, execution history |
| **Interval** | Fixed-interval repetition (e.g., every 6 hours) | Last run, interval countdown |
| **Data Change** | Fires when source data profile changes beyond threshold | Change detection status, profile comparison |
| **Composite** | Combines multiple sub-triggers with AND/OR logic | Sub-trigger states, composite evaluation |
| **Webhook** | Fires when an external system sends an HTTP request | Endpoint URL, recent invocations |
| **Event** | Fires in response to internal system events | Event queue, matching rules |
| **Manual** | Triggered only through explicit API/UI action | Last manual execution |

### Visual Identification

Each trigger type is assigned a distinct color for quick visual identification in the monitoring interface:

| Type | Color | Badge |
|------|-------|-------|
| Cron | Blue | `cron` |
| Interval | Green | `interval` |
| Data Change | Amber | `data_change` |
| Composite | Purple | `composite` |
| Webhook | Pink | `webhook` |
| Event | Cyan | `event` |
| Manual | Gray | `manual` |

## Trigger Monitoring Interface

### Summary Statistics

Four aggregated metrics provide an at-a-glance view of trigger system health:

| Card | Description |
|------|-------------|
| **Total Triggers** | Number of configured triggers across all types |
| **Active Triggers** | Number of triggers currently enabled and operational |
| **Failed Triggers** | Number of triggers whose last execution resulted in failure |
| **In Cooldown** | Number of triggers currently in cooldown period |

### Trigger Status Table

The primary monitoring view is a detailed table displaying the operational state of each trigger:

| Column | Description |
|--------|-------------|
| **Name** | Trigger identifier |
| **Type** | Trigger type with color-coded badge |
| **Source** | Associated data source |
| **Last Evaluation** | Timestamp of the most recent trigger evaluation |
| **Cooldown Remaining** | Time remaining in cooldown period (e.g., "5m 30s") |
| **Last Status** | Result of the most recent execution (success/failed) |
| **Next Check** | Scheduled time for the next trigger evaluation |

### Status Indicators

| Icon | Status | Description |
|------|--------|-------------|
| ✅ CheckCircle | Success | Last execution completed successfully |
| ⚠️ AlertCircle | Failed | Last execution encountered an error |
| ⏳ Clock | Cooldown | Trigger is in cooldown period and will not fire |
| ⏸ Pause | Disabled | Trigger is configured but not active |

## Cooldown Mechanism

The cooldown system prevents triggers from firing too frequently, which could overwhelm downstream systems or generate excessive notifications.

### How Cooldown Works

1. A trigger fires and begins execution
2. Upon completion (success or failure), the cooldown timer starts
3. During the cooldown period, the trigger will not fire even if conditions are met
4. The monitoring interface displays the remaining cooldown time in real-time
5. Once the cooldown expires, the trigger resumes normal evaluation

### Cooldown Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| **cooldown_seconds** | Duration of the cooldown period in seconds | 300 (5 minutes) |
| **cooldown_on_failure** | Whether to apply cooldown after failed executions | true |
| **max_cooldown** | Maximum cooldown duration (for exponential backoff) | 3600 (1 hour) |

## Data Change Triggers

Data change triggers represent a specialized trigger type that monitors data profiles for significant changes. The monitoring interface provides additional detail for these triggers:

### Change Detection Process

1. The trigger generates a current data profile at each evaluation interval
2. The current profile is compared against the baseline profile
3. If any monitored metric exceeds the configured threshold, the trigger fires
4. The baseline is updated after each successful validation

### Monitored Metrics

| Metric | Description |
|--------|-------------|
| **Row Count Change** | Percentage change in total row count |
| **Null Rate Change** | Change in null percentage for monitored columns |
| **Schema Change** | Any structural modification detected |
| **Distribution Shift** | Statistical distribution change beyond threshold |

## Composite Triggers

Composite triggers combine multiple sub-triggers using boolean logic. The monitoring interface displays the evaluation state of each sub-trigger:

### Composite Logic

| Mode | Behavior |
|------|----------|
| **AND** | All sub-triggers must be in a "fired" state for the composite to fire |
| **OR** | Any sub-trigger in a "fired" state causes the composite to fire |

### Monitoring Composite Triggers

The monitoring interface displays:

- Overall composite trigger state (fired / not fired)
- Individual sub-trigger states with their last evaluation results
- Which sub-triggers contributed to the composite decision

## Webhook Triggers

Webhook triggers expose HTTP endpoints that external systems can invoke to trigger validation runs. The monitoring interface provides:

### Webhook Management

| Feature | Description |
|---------|-------------|
| **Endpoint URL** | The URL that external systems should call |
| **Copy Button** | One-click copy of the webhook URL to clipboard |
| **Recent Invocations** | History of incoming webhook requests |
| **Authentication** | Token-based authentication for webhook security |

### Webhook Endpoint Format

```
POST /api/v1/triggers/webhook/{trigger_id}
```

External systems (CI/CD pipelines, orchestrators, monitoring tools) send POST requests to this endpoint to initiate validation. The request can include optional payload data that is passed to the validation configuration.

### Integration Patterns

| Pattern | Description |
|---------|-------------|
| **CI/CD Pipeline** | Trigger validation after data deployment |
| **ETL Completion** | Validate data after ETL job completes |
| **Orchestrator** | Airflow, Dagster, or Prefect task completion triggers |
| **Monitoring Alert** | External monitoring system detects an anomaly and triggers validation |

## Execution History

The Trigger Monitoring module maintains a history of trigger executions for each trigger:

| Field | Description |
|-------|-------------|
| **Timestamp** | When the execution occurred |
| **Trigger Type** | Type of trigger that fired |
| **Result** | Success or failure |
| **Duration** | Execution duration |
| **Details** | Additional context (error message for failures) |

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| **Monitor Failed Triggers** | Investigate any trigger with a failed status promptly |
| **Set Appropriate Cooldowns** | Balance responsiveness with system load |
| **Use Composite Triggers** | Combine conditions to reduce false positive trigger firings |
| **Secure Webhooks** | Always use authentication tokens for webhook endpoints |
| **Review Execution History** | Periodically audit trigger execution patterns for anomalies |
| **Refresh Regularly** | Use the refresh button to get the latest trigger states |

## Troubleshooting

### Common Issues

| Issue | Possible Cause | Resolution |
|-------|---------------|------------|
| **Trigger Not Firing** | Cooldown active, trigger disabled, or conditions not met | Check cooldown status and trigger configuration |
| **Excessive Failures** | Data source unavailable or validation errors | Check source connectivity and validator configuration |
| **Webhook Not Responding** | Incorrect URL, authentication failure, or network issue | Verify URL, token, and network connectivity |
| **Composite Never Fires** | AND logic with sub-triggers that never align | Review sub-trigger timing and consider OR logic |
| **Long Cooldown** | Exponential backoff after repeated failures | Fix underlying failure and manually reset cooldown |

## API Reference

### Trigger Monitoring Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/triggers/monitoring` | GET | Get all trigger monitoring states |
| `/triggers/monitoring/{id}` | GET | Get monitoring state for a specific trigger |
| `/triggers/monitoring/stats` | GET | Get aggregate trigger statistics |
| `/triggers/webhook` | POST | External webhook trigger endpoint |
| `/triggers/{id}/reset-cooldown` | POST | Manually reset a trigger's cooldown |
| `/triggers/{id}/history` | GET | Get execution history for a trigger |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by trigger type |
| `status` | string | Filter by status (active, failed, cooldown, disabled) |
| `source_id` | string | Filter by associated source |
| `limit` | integer | Maximum results to return |

## Glossary

| Term | Definition |
|------|------------|
| **Trigger** | A condition or event that initiates a validation run |
| **Cooldown** | A time period during which a trigger will not fire, preventing excessive execution |
| **Composite Trigger** | A trigger that combines multiple sub-triggers using boolean logic |
| **Webhook** | An HTTP endpoint that allows external systems to initiate validation |
| **Evaluation** | The process of checking whether a trigger's conditions are met |
| **Sub-trigger** | An individual trigger that is part of a composite trigger |
