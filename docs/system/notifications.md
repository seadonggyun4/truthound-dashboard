# Notifications

The Notifications module provides multi-channel alert delivery capabilities, enabling users to configure notification channels, define routing rules, and monitor delivery status.

## Overview

The notification system delivers alerts through multiple communication channels including Slack, email, webhooks, and various incident management platforms. Configurable rules determine which events trigger notifications and to which channels they are routed.

## Notifications Interface

### Statistics Dashboard

The interface displays notification delivery metrics:

| Metric | Description |
|--------|-------------|
| **24h Total** | Notifications sent in last 24 hours |
| **Success Rate** | Percentage of successful deliveries |
| **Sent** | Successfully delivered notifications |
| **Failed** | Failed delivery attempts |

## Channels Tab

### Channel Management

The Channels tab manages notification delivery endpoints:

| Column | Description |
|--------|-------------|
| **Name** | Channel identifier |
| **Type** | Channel type (Slack, Email, etc.) |
| **Status** | Active or inactive |
| **Last Used** | Most recent notification delivery |
| **Actions** | Test, edit, delete options |

### Supported Channel Types

| Type | Description | Required Configuration |
|------|-------------|----------------------|
| **Slack** | Slack workspace integration | Webhook URL |
| **Email** | Email notifications | SMTP settings, recipients |
| **Webhook** | Generic HTTP webhook | URL, method, headers |
| **Discord** | Discord server integration | Webhook URL |
| **Telegram** | Telegram bot notifications | Bot token, chat ID |
| **PagerDuty** | PagerDuty incident creation | Integration key |
| **OpsGenie** | OpsGenie alert creation | API key |
| **Teams** | Microsoft Teams integration | Webhook URL |
| **GitHub** | GitHub Issues/Discussions | Token, repository |

### Creating a Channel

1. Click **Add Channel**
2. Select channel type
3. Configure type-specific settings
4. Save the channel

#### Slack Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **Webhook URL** | Slack incoming webhook URL |
| **Channel** | Target channel (optional override) |
| **Username** | Bot display name (optional) |
| **Icon** | Bot icon URL or emoji (optional) |

#### Email Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **SMTP Host** | Mail server hostname |
| **SMTP Port** | Mail server port |
| **Username** | SMTP authentication username |
| **Password** | SMTP authentication password |
| **From Address** | Sender email address |
| **Recipients** | Comma-separated recipient addresses |
| **Use TLS** | Enable TLS encryption |

#### Webhook Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **URL** | Webhook endpoint URL |
| **Method** | HTTP method (POST, PUT) |
| **Headers** | Custom HTTP headers (JSON) |
| **Authentication** | Auth type and credentials |

#### Discord Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **Webhook URL** | Discord webhook URL |
| **Username** | Bot display name (optional) |
| **Avatar URL** | Bot avatar (optional) |

#### Telegram Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **Bot Token** | Telegram bot API token |
| **Chat ID** | Target chat/group/channel ID |

#### PagerDuty Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **Integration Key** | PagerDuty integration key |
| **Severity Mapping** | Map alert severity to PD severity |

#### OpsGenie Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **API Key** | OpsGenie API key |
| **Tags** | Default tags for alerts |
| **Priority Mapping** | Map alert severity to priority |

#### Microsoft Teams Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **Webhook URL** | Teams incoming webhook URL |

#### GitHub Configuration

| Field | Description |
|-------|-------------|
| **Name** | Channel identifier |
| **Token** | GitHub personal access token |
| **Repository** | Target repository (owner/repo) |
| **Create Issues** | Create issues for alerts |
| **Labels** | Default issue labels |

### Testing a Channel

1. Click **Test** on the channel
2. System sends a test notification
3. Review success or failure result
4. Troubleshoot configuration if failed

### Channel Status

| Status | Description |
|--------|-------------|
| **Active** | Channel receiving notifications |
| **Inactive** | Channel disabled, not receiving |

Toggle channel status to enable or disable without deleting configuration.

## Rules Tab

### Rule Management

Rules determine when notifications are sent:

| Column | Description |
|--------|-------------|
| **Name** | Rule identifier |
| **Trigger** | Event that activates the rule |
| **Channels** | Destination channels |
| **Status** | Enabled or disabled |
| **Actions** | Edit, delete options |

### Creating a Rule

1. Click **Add Rule**
2. Configure rule properties:
   - **Name**: Rule identifier
   - **Trigger Condition**: Event type
   - **Channels**: Target channels
   - **Filters**: Additional conditions
3. Save the rule

### Trigger Conditions

| Trigger | Description |
|---------|-------------|
| **validation_failed** | Validation found issues |
| **critical_issues** | Critical severity issues detected |
| **high_issues** | High severity issues detected |
| **schedule_failed** | Scheduled validation error |
| **drift_detected** | Drift monitoring alert |
| **schema_changed** | Source schema modification |

### Rule Filters

Optional filters to narrow rule scope:

| Filter | Description |
|--------|-------------|
| **Source** | Specific data source |
| **Severity** | Minimum severity level |
| **Validator** | Specific validator type |

### Rule Configuration Example

**Rule: Critical Validation Failures**
- **Trigger**: validation_failed
- **Filter**: severity = critical
- **Channels**: Slack-Urgent, PagerDuty

## Logs Tab

### Notification Logs

View notification delivery history:

| Column | Description |
|--------|-------------|
| **Timestamp** | When notification was sent |
| **Channel** | Destination channel |
| **Rule** | Triggering rule |
| **Status** | Delivery status |
| **Message** | Notification content preview |

### Log Status

| Status | Color | Description |
|--------|-------|-------------|
| **Sent** | Green | Successfully delivered |
| **Failed** | Red | Delivery failed |
| **Pending** | Yellow | Awaiting delivery |

### Log Filtering

Filter logs by delivery status:

1. Click the **Status** filter
2. Select status to filter
3. View matching log entries

### Failed Notification Investigation

For failed notifications:

1. Locate the failed entry in logs
2. Review error message
3. Check channel configuration
4. Test channel connectivity
5. Retry or fix configuration

## Notification Content

### Message Format

Notifications include:

| Section | Content |
|---------|---------|
| **Title** | Alert summary |
| **Severity** | Issue severity level |
| **Source** | Affected data source |
| **Details** | Issue description |
| **Timestamp** | When issue was detected |
| **Link** | URL to view full details |

### Channel-Specific Formatting

| Channel | Format |
|---------|--------|
| **Slack** | Rich formatting with blocks |
| **Email** | HTML with styling |
| **Webhook** | JSON payload |
| **Discord** | Embed with fields |
| **Telegram** | Markdown formatting |
| **PagerDuty** | Incident payload |
| **OpsGenie** | Alert payload |
| **Teams** | Adaptive card |
| **GitHub** | Issue/comment body |

## Best Practices

### Channel Configuration

| Practice | Recommendation |
|----------|----------------|
| **Test First** | Always test channels after creation |
| **Descriptive Names** | Use clear, descriptive channel names |
| **Backup Channels** | Configure redundant delivery paths |
| **Credential Security** | Use secure credential storage |

### Rule Design

| Practice | Recommendation |
|----------|----------------|
| **Specificity** | Create specific rules over broad ones |
| **Severity Mapping** | Match rule urgency to channel urgency |
| **Avoid Duplication** | Don't send same alert to multiple similar channels |
| **Regular Review** | Periodically review and clean up rules |

### Alert Fatigue Prevention

| Practice | Recommendation |
|----------|----------------|
| **Threshold Tuning** | Adjust thresholds to reduce noise |
| **Consolidation** | Group related alerts |
| **Prioritization** | Reserve urgent channels for critical alerts |
| **Working Hours** | Consider time-based routing |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/channels` | GET | List notification channels |
| `/notifications/channels` | POST | Create a notification channel |
| `/notifications/channels/{id}` | PUT | Update a channel |
| `/notifications/channels/{id}` | DELETE | Delete a channel |
| `/notifications/channels/{id}/test` | POST | Test a channel |
| `/notifications/rules` | GET | List notification rules |
| `/notifications/rules` | POST | Create a notification rule |
| `/notifications/rules/{id}` | PUT | Update a rule |
| `/notifications/rules/{id}` | DELETE | Delete a rule |
| `/notifications/logs` | GET | List notification logs |
| `/notifications/stats` | GET | Retrieve notification statistics |
