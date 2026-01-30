# Advanced Notifications

The Advanced Notifications module provides sophisticated notification orchestration features including content-based routing, deduplication, rate limiting, and multi-level escalation policies. This document presents the theoretical foundations, algorithmic approaches, and practical implementation guidelines for enterprise-scale notification management.

## 1. Introduction

### 1.1 Problem Statement

Modern data quality monitoring systems generate substantial volumes of alerts. Without proper orchestration, organizations face several challenges:

| Challenge | Impact |
|-----------|--------|
| **Alert Fatigue** | Operators become desensitized to frequent notifications |
| **Duplicate Notifications** | Same issue triggers multiple redundant alerts |
| **Notification Storms** | Cascading failures overwhelm communication channels |
| **Delayed Escalation** | Critical issues not escalated to appropriate personnel |

### 1.2 Solution Architecture

The Advanced Notifications module addresses these challenges through four complementary subsystems, each backed by the truthound library's checkpoint modules:

| Component | Truthound Module | Purpose |
|-----------|------------------|---------|
| **Routing** | `truthound.checkpoint.routing` | Content-based notification distribution |
| **Deduplication** | `truthound.checkpoint.deduplication` | Duplicate suppression via fingerprinting |
| **Throttling** | `truthound.checkpoint.throttling` | Rate limiting via token bucket algorithms |
| **Escalation** | `truthound.checkpoint.escalation` | Progressive notification with state machine |

### 1.3 Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Notification Processing Pipeline                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐                                                   │
│  │    Event     │  ValidationFailedEvent, DriftDetectedEvent,       │
│  │   Trigger    │  ScheduleFailedEvent, SchemaChangedEvent          │
│  └──────┬───────┘                                                   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │           TruthoundNotificationAdapter                       │    │
│  │  ┌────────────┐  ┌─────────────┐  ┌────────────┐            │    │
│  │  │  Routing   │→ │Deduplication│→ │ Throttling │            │    │
│  │  │(ActionRouter│  │(Fingerprint)│  │(TokenBucket)│           │    │
│  │  └────────────┘  └─────────────┘  └────────────┘            │    │
│  └─────────────────────────┬───────────────────────────────────┘    │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Channel Delivery Layer                          │    │
│  │  ┌──────┐ ┌───────┐ ┌───────┐ ┌─────────┐ ┌────────┐       │    │
│  │  │Slack │ │ Email │ │ Teams │ │PagerDuty│ │Webhook │       │    │
│  │  └──────┘ └───────┘ └───────┘ └─────────┘ └────────┘       │    │
│  └─────────────────────────┬───────────────────────────────────┘    │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │         Escalation Engine (State Machine)                    │    │
│  │  PENDING → ACTIVE → ESCALATING → ACKNOWLEDGED → RESOLVED    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Routing Engine

### 2.1 Theoretical Foundation

Content-based routing (CBR) is a message distribution paradigm where routing decisions are made based on message content rather than predetermined destinations. The truthound routing engine implements a rule-based CBR system with the following characteristics:

- **Declarative Rules**: Rules are specified as predicates over event attributes
- **Priority-Ordered Evaluation**: Rules are evaluated in priority order
- **Composable Conditions**: Rules can be combined using logical operators

### 2.2 Rule Types

The truthound `ActionRouter` provides 11 built-in rule types and 3 combinators:

#### 2.2.1 Primitive Rules

| Rule Type | Parameters | Matching Logic |
|-----------|------------|----------------|
| `AlwaysRule` | None | Always matches (default route) |
| `NeverRule` | None | Never matches (disabled route) |
| `SeverityRule` | `min_severity`, `max_severity`, `min_count` | Matches issues by severity level |
| `IssueCountRule` | `min_issues`, `max_issues`, `count_type` | Matches by issue count threshold |
| `StatusRule` | `statuses`, `negate` | Matches by checkpoint status |
| `TagRule` | `tags`, `match_all`, `negate` | Matches by resource tags |
| `DataAssetRule` | `pattern`, `is_regex`, `case_sensitive` | Matches by data asset name pattern |
| `MetadataRule` | `key_path`, `expected_value`, `comparator` | Matches by metadata values |
| `TimeWindowRule` | `start_time`, `end_time`, `days_of_week`, `timezone` | Matches by time period |
| `PassRateRule` | `min_rate`, `max_rate` | Matches by validation pass rate |
| `ErrorRule` | `pattern`, `negate` | Matches by error message pattern |

#### 2.2.2 Combinators

| Combinator | Semantics | Example Use Case |
|------------|-----------|------------------|
| `AllOf` | Logical conjunction (AND) | Critical AND Production |
| `AnyOf` | Logical disjunction (OR) | Critical OR Error |
| `NotRule` | Logical negation (NOT) | NOT Development environment |

### 2.3 Routing Modes

The `ActionRouter` supports three evaluation modes:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `FIRST_MATCH` | Execute only the first matching route | Mutually exclusive channels |
| `ALL_MATCHES` | Execute all matching routes | Multi-channel broadcast |
| `PRIORITY_GROUP` | Execute all routes in the highest priority group | Tiered response |

### 2.4 Route Context

The `RouteContext` data class encapsulates all attributes available for rule evaluation:

```python
@dataclass(frozen=True)
class RouteContext:
    checkpoint_name: str      # Checkpoint identifier
    run_id: str               # Execution run identifier
    status: str               # Result status (success, failure, error)
    data_asset: str           # Data asset name
    run_time: datetime        # Execution timestamp
    total_issues: int         # Total issue count
    critical_issues: int      # Critical severity count
    high_issues: int          # High severity count
    medium_issues: int        # Medium severity count
    low_issues: int           # Low severity count
    info_issues: int          # Info severity count
    pass_rate: float          # Validation pass rate (0-100)
    tags: dict[str, str]      # Resource tags
    metadata: dict[str, Any]  # Additional metadata
    validation_duration_ms: float  # Execution duration
    error: str | None         # Error message if applicable
```

### 2.5 Implementation Guidelines

#### Creating Effective Routing Rules

1. **Specificity Principle**: More specific rules should have lower priority numbers
2. **Default Route**: Always configure a catch-all route with `AlwaysRule`
3. **Testing**: Validate rules using the `/notifications/routing/rules/test` endpoint

#### Example Configuration

```yaml
routes:
  - name: critical_production
    priority: 10
    rule:
      type: all_of
      rules:
        - type: severity
          min_severity: critical
        - type: tag
          tags: { env: production }
    actions:
      - pagerduty_channel_id
      - slack_critical_channel_id

  - name: high_severity_alerts
    priority: 50
    rule:
      type: severity
      min_severity: high
    actions:
      - slack_alerts_channel_id

  - name: default_route
    priority: 100
    rule:
      type: always
    actions:
      - email_team_channel_id
```

---

## 3. Deduplication Engine

### 3.1 Theoretical Foundation

Notification deduplication addresses the problem of redundant alert generation. The approach employs **fingerprint-based duplicate detection** within sliding time windows. This technique is analogous to content-addressable storage systems and bloom filter applications in distributed systems.

#### 3.1.1 Fingerprint Generation

A notification fingerprint is a unique identifier derived from notification attributes:

```
fingerprint = hash(checkpoint_name || action_type || severity || data_asset)
```

The fingerprint function must satisfy:
- **Determinism**: Same input produces same output
- **Collision Resistance**: Different notifications should produce different fingerprints
- **Efficiency**: O(1) computation time

### 3.2 Deduplication Policies

The truthound `NotificationDeduplicator` supports five policies with increasing specificity:

| Policy | Fingerprint Components | Use Case |
|--------|------------------------|----------|
| `NONE` | Disabled | No deduplication |
| `BASIC` | checkpoint_name + action_type | Suppress same alert to same channel |
| `SEVERITY` | BASIC + severity | Differentiate by severity level |
| `ISSUE_BASED` | SEVERITY + issue_types | Differentiate by issue categories |
| `STRICT` | Full notification hash | Maximum differentiation |

### 3.3 Window Strategies

Four time-based windowing strategies are available:

#### 3.3.1 Sliding Window Strategy

The sliding window maintains a fixed-duration window that "slides" with time:

```
Time: ─────────────────────────────────────────────►
      │◄──── Window (5 min) ────►│
      │                          │
      │  Notification A          │  Notification B (duplicate)
      │  t=0                     │  t=2 min → SUPPRESSED
      │                          │
```

**Characteristics**:
- Window starts from each notification
- Simple implementation
- Memory efficient

#### 3.3.2 Tumbling Window Strategy

Non-overlapping fixed buckets:

```
Time: ─────────────────────────────────────────────►
      │◄── Bucket 1 ──►│◄── Bucket 2 ──►│
      │   15 minutes    │   15 minutes    │
      │                 │                 │
      │  A (allowed)    │  A (allowed)    │
      │  A (suppressed) │                 │
```

**Characteristics**:
- Fixed bucket boundaries
- Predictable suppression behavior
- Potential edge effects at boundaries

#### 3.3.3 Session Window Strategy

Event-driven sessions with gap-based expiration:

```
Time: ─────────────────────────────────────────────►
      │◄─ Session 1 ─►│  gap  │◄─ Session 2 ─►│
      │               │ >10min │               │
      │ A B C         │        │ A             │
      │ (A,B,C dedup) │        │ (new session) │
```

**Characteristics**:
- Dynamic window based on activity
- Suitable for bursty notifications
- Higher memory usage

### 3.4 Implementation Guidelines

#### Configuring Deduplication

| Parameter | Recommended Value | Rationale |
|-----------|-------------------|-----------|
| Window Duration | 300 seconds (5 min) | Balances suppression vs. visibility |
| Policy | `SEVERITY` | Good balance of differentiation |
| Strategy | `sliding` | Simplest, most predictable behavior |

#### Monitoring Metrics

| Metric | Formula | Target Range |
|--------|---------|--------------|
| Suppression Ratio | suppressed / total_evaluated | 10-40% |
| Active Fingerprints | Count of active entries | < 1000 |

---

## 4. Throttling Engine

### 4.1 Theoretical Foundation

Rate limiting is a fundamental technique for protecting systems from overload. The truthound throttling engine implements the **Token Bucket Algorithm**, a well-established approach used in network traffic shaping and API rate limiting.

#### 4.1.1 Token Bucket Algorithm

The token bucket maintains a bucket with maximum capacity `B` tokens. Tokens are added at rate `r` tokens per second. Each notification consumes one token. If no tokens are available, the notification is throttled.

**Mathematical Model**:
```
tokens(t) = min(B, tokens(t-1) + r × Δt)
```

Where:
- `B` = burst capacity
- `r` = token replenishment rate
- `Δt` = time since last update

**Algorithm Behavior**:
```
Tokens: ████████████ (12 tokens, capacity)
        ─────────────────────────────────────►
        │ Request │ Request │ Request │ ...
        │ 12→11   │ 11→10   │ 10→9    │
        │         │         │ +0.5/sec │  (replenishment)
```

### 4.2 Throttler Types

The truthound library provides five throttler implementations:

| Throttler | Algorithm | Characteristics |
|-----------|-----------|-----------------|
| `TokenBucketThrottler` | Token Bucket | Allows burst, smooth rate limiting |
| `SlidingWindowThrottler` | Sliding Window | More accurate, no boundary effects |
| `FixedWindowThrottler` | Fixed Window | Simple, potential 2x burst at boundaries |
| `CompositeThrottler` | Multi-level | Combines multiple rate limits |
| `NoOpThrottler` | Pass-through | Testing/disable mode |

### 4.3 Rate Limit Scopes

Rate limits can be applied at different granularities:

| Scope | Bucket Key | Use Case |
|-------|------------|----------|
| `GLOBAL` | Single bucket | Total notification limit |
| `PER_ACTION` | action_type | Per-channel limits |
| `PER_CHECKPOINT` | checkpoint_name | Per-source limits |
| `PER_ACTION_CHECKPOINT` | action + checkpoint | Fine-grained control |
| `PER_SEVERITY` | severity | Severity-based limits |
| `PER_DATA_ASSET` | data_asset | Asset-specific limits |

### 4.4 Multi-Level Rate Limiting

The `CompositeThrottler` enables hierarchical rate limits:

```yaml
throttling:
  per_minute_limit: 10    # Short-term burst control
  per_hour_limit: 100     # Medium-term control
  per_day_limit: 500      # Long-term budget
  burst_multiplier: 1.5   # 50% burst allowance
```

**Evaluation Logic**:
```
Request arrives
  │
  ├─► Check per_minute limit
  │     │
  │     ├─► PASS → Check per_hour limit
  │     │           │
  │     │           ├─► PASS → Check per_day limit
  │     │           │           │
  │     │           │           ├─► PASS → ALLOWED
  │     │           │           └─► FAIL → THROTTLED
  │     │           └─► FAIL → THROTTLED
  │     └─► FAIL → THROTTLED
```

### 4.5 Implementation Guidelines

#### Recommended Configuration

| Channel Type | per_minute | per_hour | per_day | Rationale |
|--------------|------------|----------|---------|-----------|
| PagerDuty | 5 | 20 | 100 | On-call fatigue prevention |
| Slack | 20 | 200 | 1000 | Chat noise reduction |
| Email | 5 | 50 | 200 | Inbox management |

#### Priority Bypass

Critical notifications can bypass throttling:

```yaml
priority_bypass: true
priority_threshold: critical
```

When enabled, notifications with `severity=critical` bypass all rate limits.

---

## 5. Escalation Engine

### 5.1 Theoretical Foundation

Escalation management implements a **Finite State Machine (FSM)** for incident lifecycle tracking. This approach is derived from incident management frameworks such as ITIL and modern SRE practices.

#### 5.1.1 State Machine Definition

The escalation state machine is defined as:
```
FSM = (S, Σ, δ, s₀, F)

Where:
  S = {PENDING, ACTIVE, ESCALATING, ACKNOWLEDGED, RESOLVED, CANCELLED, TIMED_OUT, FAILED}
  Σ = {start, ack, resolve, cancel, timeout, escalate, error}
  s₀ = PENDING
  F = {RESOLVED, CANCELLED, TIMED_OUT, FAILED}
```

#### 5.1.2 State Transition Diagram

```
                    ┌─────────────────────────┐
                    │        PENDING          │
                    └────────────┬────────────┘
                                 │ start()
                                 ▼
        ┌───────────────────────────────────────────────┐
        │                    ACTIVE                     │
        └────┬─────────────┬────────────────┬───────────┘
             │             │                │
             │ ack()       │ timeout        │ escalate()
             ▼             ▼                ▼
    ┌────────────┐  ┌────────────┐  ┌────────────────┐
    │ACKNOWLEDGED│  │ TIMED_OUT  │  │   ESCALATING   │
    └──────┬─────┘  └────────────┘  └───────┬────────┘
           │                                │
           │ resolve()                      │ next_level
           ▼                                ▼
    ┌────────────┐                  ┌────────────────┐
    │  RESOLVED  │                  │     ACTIVE     │
    └────────────┘                  │ (next level)   │
                                    └────────────────┘

        cancel() from any state → CANCELLED
        error from any state → FAILED
```

### 5.2 Escalation Level Configuration

Each escalation level defines:

| Parameter | Type | Description |
|-----------|------|-------------|
| `level` | int | Level number (1 = first) |
| `delay_minutes` | int | Delay before escalating to next level |
| `targets` | list[EscalationTarget] | Notification recipients |
| `repeat_count` | int | Number of times to repeat at this level |
| `repeat_interval_minutes` | int | Interval between repeats |
| `require_ack` | bool | Whether acknowledgment is required |
| `auto_resolve_minutes` | int | Auto-resolve timeout (0 = disabled) |

### 5.3 Target Types

Escalation targets represent notification recipients:

| Target Type | Identifier Format | Description |
|-------------|-------------------|-------------|
| `user` | User ID | Individual user |
| `team` | Team ID | Team/group |
| `channel` | Channel ID | Slack channel, etc. |
| `schedule` | Schedule ID | On-call schedule |
| `webhook` | URL | Webhook endpoint |
| `email` | Email address | Direct email |
| `phone` | Phone number | SMS/voice call |

### 5.4 Trigger Conditions

Escalation can be triggered by various conditions:

| Trigger | Description |
|---------|-------------|
| `UNACKNOWLEDGED` | Alert not acknowledged within timeout |
| `UNRESOLVED` | Incident not resolved within timeout |
| `SEVERITY_UPGRADE` | Severity level increased |
| `REPEATED_FAILURE` | Same issue recurring |
| `THRESHOLD_BREACH` | Metric exceeded threshold |
| `MANUAL` | Manual trigger by operator |
| `SCHEDULED` | Time-based trigger |

### 5.5 Auto-Escalation by Event Severity

The `NotificationDispatcher` automatically triggers escalation for high-severity events:

| Event Type | Condition | Escalation Policy |
|------------|-----------|-------------------|
| `ValidationFailedEvent` | `has_critical=true` | `critical_alert` |
| `ValidationFailedEvent` | `has_high=true` | `high_alert` |
| `DriftDetectedEvent` | `has_high_drift=true` | `high_alert` |
| `ScheduleFailedEvent` | Always | `high_alert` |
| `SchemaChangedEvent` | `has_breaking_changes=true` | `high_alert` |

### 5.6 Implementation Guidelines

#### Designing Escalation Policies

| Principle | Recommendation |
|-----------|----------------|
| **Level Count** | 3-4 levels typically sufficient |
| **Timeout Progression** | Exponential backoff (5min → 15min → 30min) |
| **Final Level** | Must reach decision makers |
| **Acknowledgment** | Require ack at all levels |

#### Example Policy Configuration

```yaml
escalation_policies:
  - name: critical_production
    description: Critical production issue escalation
    levels:
      - level: 1
        delay_minutes: 0
        targets:
          - type: user
            identifier: team-lead
            name: Team Lead
          - type: channel
            identifier: "#alerts-critical"
            name: Critical Alerts
        repeat_count: 2
        repeat_interval_minutes: 5
        require_ack: true

      - level: 2
        delay_minutes: 15
        targets:
          - type: user
            identifier: engineering-manager
            name: Engineering Manager
          - type: schedule
            identifier: primary-oncall
            name: Primary On-call

      - level: 3
        delay_minutes: 30
        targets:
          - type: user
            identifier: director
            name: Director of Engineering
          - type: email
            identifier: leadership@company.com
            name: Leadership Team

    triggers:
      - unacknowledged
    severity_filter:
      - critical
      - high
    cooldown_minutes: 60
    max_escalations: 5
```

---

## 6. Notification Channels

### 6.1 Supported Channels

The dashboard integrates with truthound's notification actions:

| Channel | Truthound Action | Protocol |
|---------|------------------|----------|
| **Slack** | `SlackNotification` | Incoming Webhook |
| **Email** | `EmailNotification` | SMTP/SendGrid/SES |
| **Microsoft Teams** | `TeamsNotification` | Adaptive Cards |
| **Discord** | `DiscordNotification` | Embed Webhook |
| **Telegram** | `TelegramNotification` | Bot API |
| **PagerDuty** | `PagerDutyAction` | Events API v2 |
| **OpsGenie** | `OpsGenieAction` | REST API |
| **Webhook** | `WebhookAction` | HTTP POST |
| **GitHub** | `GitHubAction` | Issues API |

### 6.2 Channel Configuration

Each channel type has specific configuration requirements:

#### Slack Configuration

| Parameter | Required | Description |
|-----------|----------|-------------|
| `webhook_url` | Yes | Slack Incoming Webhook URL |
| `channel` | No | Channel override (#channel) |
| `username` | No | Bot display name |
| `icon_emoji` | No | Bot icon (:emoji:) |
| `mention_on_failure` | No | User IDs to mention |

#### Email Configuration

| Parameter | Required | Description |
|-----------|----------|-------------|
| `from_address` | Yes | Sender email address |
| `to_addresses` | Yes | Recipient email addresses |
| `smtp_host` | Conditional | SMTP server (if provider=smtp) |
| `provider` | No | smtp, sendgrid, or ses |
| `api_key` | Conditional | API key (if provider=sendgrid/ses) |

---

## 7. Statistics and Monitoring

### 7.1 Metric Categories

The Advanced Notifications system exposes two categories of metrics:

| Category | Source | Description |
|----------|--------|-------------|
| **Dashboard Stats** | SQLite Database | Configuration counts |
| **Runtime Stats** | Truthound Library | Processing metrics |

### 7.2 Key Performance Indicators

| KPI | Formula | Target | Action if Exceeded |
|-----|---------|--------|-------------------|
| Dedup Ratio | suppressed / evaluated | 10-40% | Review fingerprint strategy |
| Throttle Rate | throttled / checked | < 10% | Increase rate limits |
| Ack Rate | acknowledged / triggered | > 80% | Review escalation timeouts |
| MTTA | avg(ack_time - trigger_time) | < 15 min | Review escalation targets |
| MTTR | avg(resolve_time - trigger_time) | < 60 min | Review resolution process |

### 7.3 Statistics API

```
GET /notifications/advanced/stats
```

Response:
```json
{
  "routing": {
    "total_routes": 12,
    "mode": "all_matches"
  },
  "deduplication": {
    "total_evaluated": 1250,
    "suppressed": 340,
    "suppression_ratio": 0.272,
    "active_fingerprints": 45
  },
  "throttling": {
    "total_checked": 1250,
    "total_allowed": 1150,
    "total_throttled": 100,
    "throttle_rate": 0.08
  },
  "escalation": {
    "total_escalations": 23,
    "active_escalations": 2,
    "acknowledged_count": 18,
    "resolved_count": 15,
    "acknowledgment_rate": 0.78,
    "avg_time_to_acknowledge": 420
  }
}
```

---

## 8. Configuration Management

### 8.1 Export Configuration

Export all Advanced Notification configurations:

```
GET /notifications/config/export?include_routing_rules=true&include_deduplication=true&include_throttling=true&include_escalation=true
```

### 8.2 Import Configuration

Import configurations with conflict resolution:

```
POST /notifications/config/import
Content-Type: application/json

{
  "bundle": { ... },
  "conflict_resolution": "skip" | "overwrite" | "rename"
}
```

### 8.3 Configuration Bundle Schema

```json
{
  "version": "1.0",
  "exported_at": "2025-01-29T12:00:00Z",
  "routing_rules": [...],
  "deduplication_configs": [...],
  "throttling_configs": [...],
  "escalation_policies": [...]
}
```

---

## 9. Template Library

The Template Library provides a curated registry of pre-built notification configurations, enabling rapid deployment of proven orchestration patterns without manual parameter tuning.

### 9.1 Overview

Each template encapsulates a complete configuration for one of the four notification subsystems. Templates are categorized by their target subsystem and tagged with descriptive metadata to facilitate discovery.

| Attribute | Description |
|-----------|-------------|
| **Name** | Human-readable template identifier |
| **Category** | Target subsystem (routing, deduplication, throttling, escalation) |
| **Description** | Functional summary of the template's purpose |
| **Tags** | Searchable keywords for discovery |
| **Configuration** | Pre-defined parameter values for the target subsystem |

### 9.2 Available Template Categories

| Category | Purpose | Example Templates |
|----------|---------|-------------------|
| **Routing** | Content-based notification distribution rules | Severity-based routing, source-type routing |
| **Deduplication** | Duplicate suppression configurations | Aggressive dedup, conservative dedup |
| **Throttling** | Rate limiting presets | Burst-friendly throttle, strict rate limit |
| **Escalation** | Multi-level alert policies | On-call escalation, business-hours policy |

### 9.3 Template Selection Workflow

The Template Library implements an integrated workflow that bridges template selection with configuration editing:

1. **Browse and Search**: Open the Template Library panel to browse available templates. Use the search field or category tabs to locate a relevant template.
2. **Preview**: Review the template's description, tags, and configuration summary before selection.
3. **Apply**: Select a template to initiate the application process. The system performs the following actions automatically:
   - **Tab Navigation**: The active tab switches to the subsystem matching the template's category (e.g., selecting a throttling template activates the Throttling tab).
   - **Dialog Auto-Open**: The corresponding configuration dialog opens with the template's pre-filled values, allowing the user to review and adjust parameters before saving.
   - **Quick Templates Hidden**: When a template is applied from the Template Library, the in-dialog Quick Templates selector is hidden to avoid confusion between the externally applied template and the dialog's built-in presets.
4. **Save or Discard**: The user may modify the pre-filled values and save, or close the dialog to discard the template application.

### 9.4 Active Template Indicator

When a template is actively applied, the Template Library panel displays an indicator banner containing:

| Element | Description |
|---------|-------------|
| **Category Icon** | Visual icon corresponding to the template's subsystem |
| **Template Name** | Name of the currently applied template |
| **Category Badge** | Labeled badge showing the target subsystem |
| **Dismiss Button** | Allows the user to clear the active template selection |

This indicator persists within the current page session. Navigating away from the Advanced Notifications page clears the active template state, as templates serve as ephemeral configuration aids rather than persistent selections.

### 9.5 Relationship to Quick Templates

Each tab's configuration dialog also provides an independent Quick Templates selector for rapid in-context configuration. The Template Library and Quick Templates serve complementary roles:

| Feature | Template Library | Quick Templates |
|---------|-----------------|-----------------|
| **Scope** | Cross-subsystem, centralized | Per-subsystem, contextual |
| **Access** | From the page header | Within each configuration dialog |
| **Behavior** | Switches tab + opens dialog | Fills form within current dialog |
| **Visibility** | Always visible | Hidden when Template Library applies a template |

---

## 10. API Reference

### 10.1 Routing Rules API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/routing/rules` | GET | List routing rules |
| `/notifications/routing/rules` | POST | Create routing rule |
| `/notifications/routing/rules/{id}` | GET | Get routing rule |
| `/notifications/routing/rules/{id}` | PUT | Update routing rule |
| `/notifications/routing/rules/{id}` | DELETE | Delete routing rule |
| `/notifications/routing/rules/types` | GET | List available rule types |
| `/notifications/routing/rules/test` | POST | Test rule against context |

### 10.2 Deduplication API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/deduplication/configs` | GET | List configs |
| `/notifications/deduplication/configs` | POST | Create config |
| `/notifications/deduplication/configs/{id}` | GET | Get config |
| `/notifications/deduplication/configs/{id}` | PUT | Update config |
| `/notifications/deduplication/configs/{id}` | DELETE | Delete config |
| `/notifications/deduplication/stats` | GET | Get runtime stats |

### 10.3 Throttling API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/throttling/configs` | GET | List configs |
| `/notifications/throttling/configs` | POST | Create config |
| `/notifications/throttling/configs/{id}` | GET | Get config |
| `/notifications/throttling/configs/{id}` | PUT | Update config |
| `/notifications/throttling/configs/{id}` | DELETE | Delete config |
| `/notifications/throttling/stats` | GET | Get runtime stats |

### 10.4 Escalation API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/escalation/policies` | GET | List policies |
| `/notifications/escalation/policies` | POST | Create policy |
| `/notifications/escalation/policies/{id}` | GET | Get policy |
| `/notifications/escalation/policies/{id}` | PUT | Update policy |
| `/notifications/escalation/policies/{id}` | DELETE | Delete policy |
| `/notifications/escalation/incidents` | GET | List incidents |
| `/notifications/escalation/incidents/active` | GET | List active incidents |
| `/notifications/escalation/incidents/{id}` | GET | Get incident |
| `/notifications/escalation/incidents/{id}/acknowledge` | POST | Acknowledge incident |
| `/notifications/escalation/incidents/{id}/resolve` | POST | Resolve incident |
| `/notifications/escalation/stats` | GET | Get runtime stats |

---

## 11. Best Practices

### 11.1 Routing Best Practices

| Practice | Description |
|----------|-------------|
| Use specific rules first | Lower priority numbers for more specific conditions |
| Always have a default | Ensure all notifications have a destination |
| Test before deploying | Use the test endpoint to validate rules |
| Document routing logic | Maintain documentation for team reference |

### 11.2 Deduplication Best Practices

| Practice | Description |
|----------|-------------|
| Start with moderate windows | 5-minute default, adjust based on data |
| Monitor suppression ratio | 10-40% indicates healthy deduplication |
| Use SEVERITY policy | Good balance between dedup and visibility |
| Review active fingerprints | High counts may indicate memory pressure |

### 11.3 Throttling Best Practices

| Practice | Description |
|----------|-------------|
| Set conservative initial limits | Easier to relax than tighten |
| Configure per-channel limits | Different urgency levels need different limits |
| Enable priority bypass | Critical alerts should not be throttled |
| Monitor throttle rate | Above 10% may indicate configuration issues |

### 11.4 Escalation Best Practices

| Practice | Description |
|----------|-------------|
| Design for progressive urgency | Later levels should reach higher authority |
| Use reasonable timeouts | 5-15-30 minute progression works well |
| Require acknowledgment | Ensures humans are in the loop |
| Test escalation paths | Regular testing ensures functionality |
| Configure cooldowns | Prevent escalation storms |

---

## References

1. Beyer, B., et al. (2016). *Site Reliability Engineering*. O'Reilly Media.
2. Turner, J. (1986). New directions in communications (or which way to the information age?). *IEEE Communications Magazine*, 24(10), 8-15. [Token Bucket Algorithm]
3. ITIL Foundation (2019). *ITIL 4 Foundation*. Axelos.
4. truthound Documentation. https://truthound.readthedocs.io/
