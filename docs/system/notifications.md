# Notifications

The Notifications module provides enterprise-grade alert delivery capabilities built upon the truthound library's checkpoint notification infrastructure. This document presents the architectural foundations, channel implementations, and operational guidelines for configuring multi-channel notification delivery.

## 1. Introduction

### 1.1 Overview

The notification system serves as the communication layer between data quality events and operational teams. It transforms validation results, drift detections, and schema changes into actionable alerts delivered through preferred communication channels.

### 1.2 Architecture Foundation

The notification system is built on truthound's `checkpoint.actions` module, which provides battle-tested implementations for various notification channels:

```
┌─────────────────────────────────────────────────────────────────┐
│                    truthound-dashboard                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                NotificationDispatcher                   │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │             TruthoundNotificationAdapter          │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              truthound.checkpoint.actions               │    │
│  │  ┌────────┐ ┌────────┐ ┌─────┐ ┌───────┐ ┌────────┐   │    │
│  │  │ Slack  │ │ Email  │ │Teams│ │Discord│ │Telegram│   │    │
│  │  └────────┘ └────────┘ └─────┘ └───────┘ └────────┘   │    │
│  │  ┌──────────┐ ┌─────────┐ ┌────────┐ ┌────────┐       │    │
│  │  │PagerDuty │ │OpsGenie │ │Webhook │ │ GitHub │       │    │
│  │  └──────────┘ └─────────┘ └────────┘ └────────┘       │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Library-First** | All channel implementations delegate to truthound's checkpoint.actions |
| **Unified Interface** | Consistent API across all channel types |
| **Extensibility** | New channels can be added by wrapping truthound actions |
| **Reliability** | Built-in retry, logging, and error handling |

---

## 2. Notification Channels

### 2.1 Supported Channels

The dashboard supports nine notification channels, each backed by a corresponding truthound action class:

| Channel | truthound Action Class | Protocol | Primary Use Case |
|---------|------------------------|----------|------------------|
| **Slack** | `SlackNotification` | Incoming Webhook | Team collaboration |
| **Email** | `EmailNotification` | SMTP/SendGrid/SES | Formal notifications |
| **Microsoft Teams** | `TeamsNotification` | Adaptive Cards | Enterprise communication |
| **Discord** | `DiscordNotification` | Embed Webhook | Developer communities |
| **Telegram** | `TelegramNotification` | Bot API | Mobile-first teams |
| **PagerDuty** | `PagerDutyAction` | Events API v2 | On-call incident management |
| **OpsGenie** | `OpsGenieAction` | REST API | Alert orchestration |
| **Webhook** | `WebhookAction` | HTTP POST | Custom integrations |
| **GitHub** | `GitHubAction` | Issues API | Development workflow |

### 2.2 Channel Classification

Channels can be classified by their operational characteristics:

#### 2.2.1 By Delivery Semantics

| Category | Channels | Characteristics |
|----------|----------|-----------------|
| **Chat-based** | Slack, Teams, Discord, Telegram | Real-time, ephemeral, conversational |
| **Incident Management** | PagerDuty, OpsGenie | On-call rotation, escalation, acknowledgment |
| **Record-based** | Email, GitHub | Persistent, searchable, auditable |
| **Integration** | Webhook | Customizable, system-to-system |

#### 2.2.2 By Urgency Model

| Urgency Level | Recommended Channels | Rationale |
|---------------|----------------------|-----------|
| **Critical** | PagerDuty, OpsGenie, Slack (with mentions) | Immediate human attention required |
| **High** | Slack, Teams, Telegram | Team awareness needed |
| **Medium** | Email, GitHub | Documentation and tracking |
| **Low** | Webhook, Email digest | Background awareness |

---

## 3. Channel Configuration

### 3.1 Slack Channel

Slack integration uses the Incoming Webhook mechanism for message delivery.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Slack Incoming Webhook URL |
| `channel` | string | No | Channel override (#channel-name) |
| `username` | string | No | Bot display name (default: "Truthound Dashboard") |
| `icon_emoji` | string | No | Bot icon emoji (e.g., `:bar_chart:`) |
| `mention_on_failure` | array | No | User IDs to mention on failure events |

#### Message Format

Slack messages are delivered in Block Kit format providing rich, interactive content:

| Section | Content |
|---------|---------|
| **Header** | Status emoji with checkpoint name and result |
| **Context** | Data asset, run ID, timestamp |
| **Statistics** | Issue counts by severity, pass rate |
| **Details** | Issue summary (when enabled) |

#### Webhook URL Acquisition

1. Navigate to Slack workspace settings
2. Access **Apps** → **Incoming Webhooks**
3. Create new webhook for target channel
4. Copy the generated URL

### 3.2 Email Channel

Email notifications support three provider backends: SMTP, SendGrid, and AWS SES.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_address` | string | Yes | Sender email address |
| `to_addresses` | array | Yes | Recipient email addresses |
| `cc_addresses` | array | No | CC recipients |
| `smtp_host` | string | Conditional | SMTP server hostname (if provider=smtp) |
| `smtp_port` | integer | Conditional | SMTP server port (default: 587) |
| `smtp_user` | string | Conditional | SMTP authentication username |
| `smtp_password` | string | Conditional | SMTP authentication password |
| `use_tls` | boolean | No | Enable TLS encryption (default: true) |
| `use_ssl` | boolean | No | Enable SSL encryption (default: false) |
| `provider` | string | No | Provider: smtp, sendgrid, ses (default: smtp) |
| `api_key` | string | Conditional | API key for SendGrid/SES providers |

#### Provider Selection

| Provider | Use Case | Requirements |
|----------|----------|--------------|
| **SMTP** | Self-hosted, corporate mail servers | SMTP credentials |
| **SendGrid** | Cloud-based, high volume | SendGrid API key |
| **AWS SES** | AWS infrastructure integration | AWS credentials (env/IAM) |

#### Message Format

Email notifications include HTML formatting with:
- Styled header with severity indicator
- Tabular issue summary
- Deep links to dashboard views

### 3.3 Microsoft Teams Channel

Teams integration uses Adaptive Cards for rich message formatting.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Teams Incoming Webhook URL |
| `channel` | string | No | Channel name for display purposes |
| `include_details` | boolean | No | Include detailed statistics (default: true) |

#### Webhook Configuration

1. Open Teams channel settings
2. Navigate to **Connectors**
3. Add **Incoming Webhook**
4. Configure name and icon
5. Copy generated URL

### 3.4 Discord Channel

Discord integration delivers embedded messages through webhooks.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Discord webhook URL |
| `username` | string | No | Bot display name (default: "Truthound Bot") |
| `avatar_url` | string | No | Bot avatar URL |
| `embed_color` | integer | No | Embed color as hex integer (auto-calculated based on severity) |
| `include_mentions` | array | No | Mentions to include (@here, role IDs) |

### 3.5 Telegram Channel

Telegram notifications are delivered via the Bot API.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bot_token` | string | Yes | Telegram Bot API token |
| `chat_id` | string | Yes | Target chat/group/channel ID |
| `parse_mode` | string | No | Parse mode: Markdown or HTML (default: Markdown) |
| `disable_notification` | boolean | No | Send silently (default: false) |

#### Bot Setup

1. Contact @BotFather on Telegram
2. Create new bot with `/newbot`
3. Copy the API token
4. Add bot to target chat/channel
5. Obtain chat ID via bot API

### 3.6 PagerDuty Channel

PagerDuty integration creates incidents through the Events API v2.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `routing_key` | string | Yes | PagerDuty Events API v2 routing key |
| `severity` | string | No | Default severity: critical, error, warning, info |
| `component` | string | No | Affected component name |
| `group` | string | No | Alert grouping key |
| `class_type` | string | No | Alert class/type classification |
| `custom_details` | object | No | Additional custom details |

#### Severity Mapping

| Dashboard Severity | PagerDuty Severity | Behavior |
|-------------------|-------------------|----------|
| Critical | critical | Immediate page |
| High | error | High-urgency notification |
| Medium | warning | Low-urgency notification |
| Low | info | Informational |

### 3.7 OpsGenie Channel

OpsGenie integration creates and manages alerts through the REST API.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | OpsGenie API key |
| `region` | string | No | API region: us or eu (default: us) |
| `priority` | string | No | Alert priority: P1-P5 (default: P3) |
| `auto_priority` | boolean | No | Automatic priority mapping (default: true) |
| `tags` | array | No | Alert tags |
| `auto_close_on_success` | boolean | No | Auto-close on validation success (default: true) |

#### Auto-Priority Mapping

When `auto_priority` is enabled:

| Validation Result | OpsGenie Priority |
|-------------------|-------------------|
| Critical issues | P1 |
| High issues | P2 |
| Medium issues | P3 |
| Low issues | P4 |
| Info only | P5 |

### 3.8 Webhook Channel

Generic webhook integration for custom system-to-system communication.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Webhook endpoint URL |
| `method` | string | No | HTTP method: GET, POST, PUT, PATCH (default: POST) |
| `headers` | object | No | Custom HTTP headers |
| `timeout` | integer | No | Request timeout in seconds (default: 30) |
| `include_result` | boolean | No | Include full checkpoint result (default: true) |

#### Payload Format

Webhook payloads follow a standardized JSON structure:

```json
{
  "checkpoint_name": "string",
  "run_id": "string",
  "status": "success | failure | error",
  "data_asset": "string",
  "statistics": {
    "total_issues": 0,
    "critical_issues": 0,
    "high_issues": 0,
    "medium_issues": 0,
    "low_issues": 0,
    "pass_rate": 100.0
  },
  "timestamp": "ISO8601 timestamp",
  "dashboard_url": "string"
}
```

### 3.9 GitHub Channel

GitHub integration creates issues or check runs for data quality events.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | GitHub personal access token |
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `labels` | array | No | Default issue labels (default: ["data-quality"]) |
| `assignees` | array | No | Issue assignees |
| `create_check_run` | boolean | No | Create check run instead of issue (default: false) |

#### Token Permissions

Required token scopes:
- `repo` - Full repository access
- `issues:write` - Issue creation (if using issues)
- `checks:write` - Check run creation (if using check runs)

---

## 4. Notification Rules

### 4.1 Rule Fundamentals

Notification rules define the conditions under which notifications are dispatched and to which channels.

#### Rule Components

| Component | Description |
|-----------|-------------|
| **Name** | Human-readable rule identifier |
| **Condition** | Event type that triggers the rule |
| **Channels** | Target notification channels |
| **Source Filter** | Optional restriction to specific data sources |
| **Status** | Active or inactive |

### 4.2 Trigger Conditions

Available trigger conditions align with dashboard event types:

| Condition | Event Type | Description |
|-----------|------------|-------------|
| `validation_failed` | `ValidationFailedEvent` | Validation detected any issues |
| `critical_issues` | `ValidationFailedEvent` | Critical severity issues found |
| `high_issues` | `ValidationFailedEvent` | High or critical severity issues found |
| `schedule_failed` | `ScheduleFailedEvent` | Scheduled validation error |
| `drift_detected` | `DriftDetectedEvent` | Drift monitoring alert |
| `schema_changed` | `SchemaChangedEvent` | Source schema modification |
| `breaking_schema_change` | `SchemaChangedEvent` | Breaking schema changes detected |

### 4.3 Rule Evaluation

Rules are evaluated against incoming events:

```
Event arrives
    │
    ├─► Match event type to conditions
    │     │
    │     ├─► Filter by source_ids (if specified)
    │     │     │
    │     │     ├─► Filter by condition-specific logic
    │     │     │     │
    │     │     │     ├─► MATCH: Dispatch to configured channels
    │     │     │     │
    │     │     │     └─► NO MATCH: Skip rule
    │     │     │
    │     │     └─► Source not in filter: Skip rule
    │     │
    │     └─► Condition not matched: Skip rule
```

### 4.4 Rule Design Guidelines

| Guideline | Rationale |
|-----------|-----------|
| **One purpose per rule** | Simplifies maintenance and troubleshooting |
| **Use descriptive names** | Enables quick identification (e.g., "Critical Production Failures to PagerDuty") |
| **Match urgency to channel** | Critical → PagerDuty, Low → Email |
| **Avoid channel duplication** | Don't send same alert to multiple similar channels |

---

## 5. Notification Logs

### 5.1 Log Structure

Each notification delivery attempt creates a log entry:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique log identifier |
| `channel_id` | string | Target channel |
| `rule_id` | string | Triggering rule (optional) |
| `event_type` | string | Event type that triggered notification |
| `event_data` | object | Full event payload |
| `status` | string | Delivery status |
| `message` | string | Formatted notification content |
| `error_message` | string | Error details (if failed) |
| `created_at` | datetime | Log creation timestamp |
| `sent_at` | datetime | Successful delivery timestamp |

### 5.2 Delivery Status

| Status | Description | Action |
|--------|-------------|--------|
| **sent** | Successfully delivered | None required |
| **failed** | Delivery failed | Review error, fix configuration |
| **pending** | Awaiting delivery | Check channel availability |

### 5.3 Statistics

The statistics dashboard provides delivery metrics:

| Metric | Calculation | Target |
|--------|-------------|--------|
| **Total (24h)** | Count of all notifications | Varies by volume |
| **Success Rate** | sent / total × 100 | > 95% |
| **Sent** | Count of successful deliveries | - |
| **Failed** | Count of failed deliveries | < 5% of total |

---

## 6. Integration with Advanced Notifications

The basic notification system integrates seamlessly with the Advanced Notifications module (see [Advanced Notifications](./notifications-advanced.md)):

### 6.1 Processing Pipeline Integration

When Advanced Notifications are enabled:

```
Event → Dispatcher (use_truthound=True)
    │
    ├─► Routing: ActionRouter matches channels
    │
    ├─► Deduplication: Fingerprint-based suppression
    │
    ├─► Throttling: Rate limit enforcement
    │
    ├─► Channel Delivery: truthound actions
    │
    └─► Escalation: State machine for critical events
```

### 6.2 Fallback Behavior

When Advanced Notifications are disabled or not configured:

```
Event → Dispatcher (use_truthound=False)
    │
    ├─► Legacy rule matching
    │
    └─► Direct channel delivery
```

---

## 7. Operational Guidelines

### 7.1 Channel Testing

Before relying on notification channels in production:

1. **Create channel** with complete configuration
2. **Send test notification** via "Test" button
3. **Verify delivery** in target system
4. **Review formatting** for readability
5. **Activate channel** only after successful test

### 7.2 Credential Management

| Practice | Recommendation |
|----------|----------------|
| **Environment variables** | Store sensitive values in environment |
| **Secret rotation** | Rotate API keys and tokens periodically |
| **Minimal permissions** | Request only required scopes |
| **Audit access** | Review who has access to credentials |

### 7.3 Alert Fatigue Prevention

| Strategy | Implementation |
|----------|----------------|
| **Severity alignment** | Match alert urgency to channel urgency |
| **Deduplication** | Enable Advanced Notifications deduplication |
| **Throttling** | Configure rate limits per channel |
| **Rule specificity** | Narrow rules to relevant conditions |
| **Regular review** | Audit and cleanup unused rules monthly |

### 7.4 Troubleshooting Failed Notifications

| Symptom | Possible Cause | Resolution |
|---------|----------------|------------|
| All notifications fail | Invalid credentials | Verify API keys/tokens |
| Intermittent failures | Rate limiting | Check provider rate limits |
| Delayed delivery | Network issues | Verify connectivity |
| Missing content | Formatting error | Review message template |
| Wrong channel | Misconfigured rule | Verify rule channel mappings |

---

## 8. API Reference

### 8.1 Channels API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/channels` | GET | List notification channels |
| `/notifications/channels` | POST | Create notification channel |
| `/notifications/channels/types` | GET | Get available channel types with schemas |
| `/notifications/channels/{id}` | GET | Get channel details |
| `/notifications/channels/{id}` | PUT | Update channel configuration |
| `/notifications/channels/{id}` | DELETE | Delete channel |
| `/notifications/channels/{id}/test` | POST | Send test notification |

### 8.2 Rules API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/rules` | GET | List notification rules |
| `/notifications/rules` | POST | Create notification rule |
| `/notifications/rules/conditions` | GET | Get valid rule conditions |
| `/notifications/rules/{id}` | GET | Get rule details |
| `/notifications/rules/{id}` | PUT | Update rule |
| `/notifications/rules/{id}` | DELETE | Delete rule |

### 8.3 Logs API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/logs` | GET | List notification logs |
| `/notifications/logs/{id}` | GET | Get log details |
| `/notifications/logs/stats` | GET | Get delivery statistics |

---

## 9. References

1. truthound Documentation - Checkpoint Actions. https://truthound.readthedocs.io/checkpoint/actions/
2. Slack API - Incoming Webhooks. https://api.slack.com/messaging/webhooks
3. PagerDuty Developer Documentation - Events API v2. https://developer.pagerduty.com/docs/events-api-v2/
4. OpsGenie API Documentation. https://docs.opsgenie.com/docs/api-overview
5. Microsoft Teams - Connectors Documentation. https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/
