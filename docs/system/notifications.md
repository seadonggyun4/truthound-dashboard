# Multi-Channel Notification Framework

The Notifications module provides enterprise-grade alert delivery capabilities built upon the truthound library's checkpoint notification infrastructure. This document presents the architectural foundations, channel implementations, and operational guidelines for configuring multi-channel notification delivery.

## 1. Introduction and Theoretical Foundations

### 1.1 System Overview

The notification system serves as the communication abstraction layer mediating between data quality events and operational teams. It is responsible for transforming validation results, drift detections, and schema changes into actionable alerts that are delivered through designated communication channels.

### 1.2 Architectural Foundation

The notification system is constructed upon truthound's `checkpoint.actions` module, which provides rigorously validated implementations for a variety of notification channels:

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

### 1.3 Governing Design Principles

| Principle | Description |
|-----------|-------------|
| **Library-First** | All channel implementations delegate to truthound's checkpoint.actions |
| **Unified Interface** | Consistent API across all channel types |
| **Extensibility** | New channels can be added by wrapping truthound actions |
| **Reliability** | Built-in retry, logging, and error handling |

---

## 2. Notification Channel Taxonomy

### 2.1 Supported Channels

The dashboard supports nine notification channels, each of which is underpinned by a corresponding truthound action class:

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

### 2.2 Channel Classification Schema

Channels may be classified according to their operational characteristics, as described in the following subsections.

#### 2.2.1 Classification by Delivery Semantics

| Category | Channels | Characteristics |
|----------|----------|-----------------|
| **Chat-based** | Slack, Teams, Discord, Telegram | Real-time, ephemeral, conversational |
| **Incident Management** | PagerDuty, OpsGenie | On-call rotation, escalation, acknowledgment |
| **Record-based** | Email, GitHub | Persistent, searchable, auditable |
| **Integration** | Webhook | Customizable, system-to-system |

#### 2.2.2 Classification by Urgency Model

| Urgency Level | Recommended Channels | Rationale |
|---------------|----------------------|-----------|
| **Critical** | PagerDuty, OpsGenie, Slack (with mentions) | Immediate human attention required |
| **High** | Slack, Teams, Telegram | Team awareness needed |
| **Medium** | Email, GitHub | Documentation and tracking |
| **Low** | Webhook, Email digest | Background awareness |

---

## 3. Channel Configuration Specifications

### 3.1 Slack Channel Configuration

Slack integration employs the Incoming Webhook mechanism for message delivery.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Slack Incoming Webhook URL |
| `channel` | string | No | Channel override (#channel-name) |
| `username` | string | No | Bot display name (default: "Truthound Dashboard") |
| `icon_emoji` | string | No | Bot icon emoji (e.g., `:bar_chart:`) |
| `mention_on_failure` | array | No | User IDs to mention on failure events |

#### Message Format Specification

Slack messages are delivered in Block Kit format, thereby providing rich, interactive content:

| Section | Content |
|---------|---------|
| **Header** | Status emoji with checkpoint name and result |
| **Context** | Data asset, run ID, timestamp |
| **Statistics** | Issue counts by severity, pass rate |
| **Details** | Issue summary (when enabled) |

#### Webhook URL Acquisition Procedure

1. Navigate to Slack workspace settings
2. Access **Apps** → **Incoming Webhooks**
3. Create new webhook for target channel
4. Copy the generated URL

### 3.2 Email Channel Configuration

Email notifications are supported through three provider backends: SMTP, SendGrid, and AWS SES.

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

#### Provider Selection Criteria

| Provider | Use Case | Requirements |
|----------|----------|--------------|
| **SMTP** | Self-hosted, corporate mail servers | SMTP credentials |
| **SendGrid** | Cloud-based, high volume | SendGrid API key |
| **AWS SES** | AWS infrastructure integration | AWS credentials (env/IAM) |

#### Message Format Specification

Email notifications are rendered with HTML formatting that includes:
- A styled header incorporating a severity indicator
- A tabular issue summary
- Deep links to corresponding dashboard views

### 3.3 Microsoft Teams Channel Configuration

Teams integration utilizes Adaptive Cards for rich message formatting.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Teams Incoming Webhook URL |
| `channel` | string | No | Channel name for display purposes |
| `include_details` | boolean | No | Include detailed statistics (default: true) |

#### Webhook Configuration Procedure

1. Open Teams channel settings
2. Navigate to **Connectors**
3. Add **Incoming Webhook**
4. Configure name and icon
5. Copy generated URL

### 3.4 Discord Channel Configuration

Discord integration facilitates the delivery of embedded messages through webhooks.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Discord webhook URL |
| `username` | string | No | Bot display name (default: "Truthound Bot") |
| `avatar_url` | string | No | Bot avatar URL |
| `embed_color` | integer | No | Embed color as hex integer (auto-calculated based on severity) |
| `include_mentions` | array | No | Mentions to include (@here, role IDs) |

### 3.5 Telegram Channel Configuration

Telegram notifications are dispatched via the Bot API.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bot_token` | string | Yes | Telegram Bot API token |
| `chat_id` | string | Yes | Target chat/group/channel ID |
| `parse_mode` | string | No | Parse mode: Markdown or HTML (default: Markdown) |
| `disable_notification` | boolean | No | Send silently (default: false) |

#### Bot Provisioning Procedure

1. Contact @BotFather on Telegram
2. Create new bot with `/newbot`
3. Copy the API token
4. Add bot to target chat/channel
5. Obtain chat ID via bot API

### 3.6 PagerDuty Channel Configuration

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

#### Severity Mapping Correspondence

| Dashboard Severity | PagerDuty Severity | Behavior |
|-------------------|-------------------|----------|
| Critical | critical | Immediate page |
| High | error | High-urgency notification |
| Medium | warning | Low-urgency notification |
| Low | info | Informational |

### 3.7 OpsGenie Channel Configuration

OpsGenie integration is responsible for the creation and management of alerts through the REST API.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | OpsGenie API key |
| `region` | string | No | API region: us or eu (default: us) |
| `priority` | string | No | Alert priority: P1-P5 (default: P3) |
| `auto_priority` | boolean | No | Automatic priority mapping (default: true) |
| `tags` | array | No | Alert tags |
| `auto_close_on_success` | boolean | No | Auto-close on validation success (default: true) |

#### Automated Priority Mapping

When `auto_priority` is enabled, the following correspondence is applied:

| Validation Result | OpsGenie Priority |
|-------------------|-------------------|
| Critical issues | P1 |
| High issues | P2 |
| Medium issues | P3 |
| Low issues | P4 |
| Info only | P5 |

### 3.8 Webhook Channel Configuration

The generic webhook integration facilitates custom system-to-system communication.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Webhook endpoint URL |
| `method` | string | No | HTTP method: GET, POST, PUT, PATCH (default: POST) |
| `headers` | object | No | Custom HTTP headers |
| `timeout` | integer | No | Request timeout in seconds (default: 30) |
| `include_result` | boolean | No | Include full checkpoint result (default: true) |

#### Payload Format Specification

Webhook payloads conform to a standardized JSON structure:

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

### 3.9 GitHub Channel Configuration

GitHub integration is employed to create issues or check runs in response to data quality events.

#### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | GitHub personal access token |
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `labels` | array | No | Default issue labels (default: ["data-quality"]) |
| `assignees` | array | No | Issue assignees |
| `create_check_run` | boolean | No | Create check run instead of issue (default: false) |

#### Required Token Permission Scopes

The following token scopes are required:
- `repo` - Full repository access
- `issues:write` - Issue creation (if utilizing issues)
- `checks:write` - Check run creation (if utilizing check runs)

---

## 4. Notification Rule Configuration

### 4.1 Rule Fundamentals

Notification rules define the conditions under which notifications are dispatched and the channels to which they are directed.

#### Rule Component Definitions

| Component | Description |
|-----------|-------------|
| **Name** | Human-readable rule identifier |
| **Condition** | Event type that triggers the rule |
| **Channels** | Target notification channels |
| **Source Filter** | Optional restriction to specific data sources |
| **Status** | Active or inactive |

### 4.2 Trigger Condition Definitions

The available trigger conditions are aligned with dashboard event types:

| Condition | Event Type | Description |
|-----------|------------|-------------|
| `validation_failed` | `ValidationFailedEvent` | Validation detected any issues |
| `critical_issues` | `ValidationFailedEvent` | Critical severity issues found |
| `high_issues` | `ValidationFailedEvent` | High or critical severity issues found |
| `schedule_failed` | `ScheduleFailedEvent` | Scheduled validation error |
| `drift_detected` | `DriftDetectedEvent` | Drift monitoring alert |
| `schema_changed` | `SchemaChangedEvent` | Source schema modification |
| `breaking_schema_change` | `SchemaChangedEvent` | Breaking schema changes detected |

### 4.3 Rule Evaluation Process

Rules are evaluated against incoming events according to the following decision process:

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

### 4.4 Rule Design Principles

| Guideline | Rationale |
|-----------|-----------|
| **One purpose per rule** | Simplifies maintenance and troubleshooting |
| **Use descriptive names** | Enables quick identification (e.g., "Critical Production Failures to PagerDuty") |
| **Match urgency to channel** | Critical → PagerDuty, Low → Email |
| **Avoid channel duplication** | Don't send same alert to multiple similar channels |

---

## 5. Notification Log Architecture

### 5.1 Log Entry Structure

Each notification delivery attempt results in the creation of a log entry with the following schema:

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

### 5.2 Delivery Status Definitions

| Status | Description | Action |
|--------|-------------|--------|
| **sent** | Successfully delivered | None required |
| **failed** | Delivery failed | Review error, fix configuration |
| **pending** | Awaiting delivery | Check channel availability |

### 5.3 Delivery Statistics and Metrics

The statistics dashboard provides the following delivery metrics:

| Metric | Calculation | Target |
|--------|-------------|--------|
| **Total (24h)** | Count of all notifications | Varies by volume |
| **Success Rate** | sent / total × 100 | > 95% |
| **Sent** | Count of successful deliveries | - |
| **Failed** | Count of failed deliveries | < 5% of total |

---

## 6. Integration with the Advanced Notification Subsystem

The foundational notification system is designed to integrate seamlessly with the Advanced Notifications module (see [Advanced Notifications](./notifications-advanced.md)):

### 6.1 Processing Pipeline Integration

When Advanced Notifications are enabled, the following processing pipeline is invoked:

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

When Advanced Notifications are disabled or have not been configured, the following fallback pipeline is employed:

```
Event → Dispatcher (use_truthound=False)
    │
    ├─► Legacy rule matching
    │
    └─► Direct channel delivery
```

---

## 7. Recommended Operational Practices

### 7.1 Channel Verification Protocol

Prior to relying upon notification channels in production environments, the following verification procedure should be observed:

1. **Create channel** with complete configuration
2. **Send test notification** via "Test" button
3. **Verify delivery** in target system
4. **Review formatting** for readability
5. **Activate channel** only after successful test

### 7.2 Credential Management Practices

| Practice | Recommendation |
|----------|----------------|
| **Environment variables** | Store sensitive values in environment |
| **Secret rotation** | Rotate API keys and tokens periodically |
| **Minimal permissions** | Request only required scopes |
| **Audit access** | Review who has access to credentials |

### 7.3 Alert Fatigue Mitigation Strategies

| Strategy | Implementation |
|----------|----------------|
| **Severity alignment** | Match alert urgency to channel urgency |
| **Deduplication** | Enable Advanced Notifications deduplication |
| **Throttling** | Configure rate limits per channel |
| **Rule specificity** | Narrow rules to relevant conditions |
| **Regular review** | Audit and cleanup unused rules monthly |

### 7.4 Diagnostic Procedures for Failed Notifications

| Symptom | Possible Cause | Resolution |
|---------|----------------|------------|
| All notifications fail | Invalid credentials | Verify API keys/tokens |
| Intermittent failures | Rate limiting | Check provider rate limits |
| Delayed delivery | Network issues | Verify connectivity |
| Missing content | Formatting error | Review message template |
| Wrong channel | Misconfigured rule | Verify rule channel mappings |

---

## 8. Application Programming Interface Reference

### 8.1 Channels API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/channels` | GET | List notification channels |
| `/notifications/channels` | POST | Create notification channel |
| `/notifications/channels/types` | GET | Get available channel types with schemas |
| `/notifications/channels/{id}` | GET | Get channel details |
| `/notifications/channels/{id}` | PUT | Update channel configuration |
| `/notifications/channels/{id}` | DELETE | Delete channel |
| `/notifications/channels/{id}/test` | POST | Send test notification |

### 8.2 Rules API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/rules` | GET | List notification rules |
| `/notifications/rules` | POST | Create notification rule |
| `/notifications/rules/conditions` | GET | Get valid rule conditions |
| `/notifications/rules/{id}` | GET | Get rule details |
| `/notifications/rules/{id}` | PUT | Update rule |
| `/notifications/rules/{id}` | DELETE | Delete rule |

### 8.3 Logs API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/logs` | GET | List notification logs |
| `/notifications/logs/{id}` | GET | Get log details |
| `/notifications/logs/stats` | GET | Get delivery statistics |

---

## 9. References and Further Reading

1. truthound Documentation - Checkpoint Actions. https://truthound.readthedocs.io/checkpoint/actions/
2. Slack API - Incoming Webhooks. https://api.slack.com/messaging/webhooks
3. PagerDuty Developer Documentation - Events API v2. https://developer.pagerduty.com/docs/events-api-v2/
4. OpsGenie API Documentation. https://docs.opsgenie.com/docs/api-overview
5. Microsoft Teams - Connectors Documentation. https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/
