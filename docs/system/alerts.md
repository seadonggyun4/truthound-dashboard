# Dashboard Alerts

The Dashboard Alerts module provides a centralized dashboard for managing alerts from all dashboard monitoring components, including validation failures, drift detection, anomaly detection, and model monitoring.

> **Note**: Dashboard Alerts is a dashboard-level aggregation system that collects alerts from various monitoring subsystems within the truthound-dashboard application. It is distinct from the truthound library's checkpoint alert system, which provides lower-level programmatic alerting capabilities.

## Overview

The alert system aggregates notifications from multiple sources into a single interface, enabling efficient triage, acknowledgment, and resolution workflows. This unified approach eliminates the need to monitor multiple alert sources independently.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dashboard Alerts System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Validation  │  │    Drift     │  │   Anomaly    │           │
│  │   Module     │  │   Module     │  │    Module    │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│         └────────────┬────┴─────────────────┘                    │
│                      ▼                                           │
│         ┌────────────────────────┐                               │
│         │   Alert Aggregator     │                               │
│         │   (Dashboard-level)    │                               │
│         └────────────┬───────────┘                               │
│                      │                                           │
│         ┌────────────▼───────────┐                               │
│         │   Dashboard Alerts     │                               │
│         │   UI & API             │                               │
│         └────────────────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Alerts Interface

### Summary Dashboard

The interface displays aggregate alert statistics:

| Metric | Description |
|--------|-------------|
| **Total Alerts** | Count of all alerts in the system |
| **Active Alerts** | Alerts in open or acknowledged status |
| **By Severity** | Breakdown by severity level |
| **By Source** | Breakdown by alert source |
| **By Status** | Breakdown by current status |
| **24h Trend** | Alert volume trend over 24 hours |
| **Top Sources** | Data sources with most alerts |

### Alert Listing

The main alert list displays all alerts with filtering capabilities:

| Column | Description |
|--------|-------------|
| **Alert ID** | Unique identifier |
| **Source Type** | Origin module (validation, drift, anomaly, model) |
| **Severity** | Critical, high, medium, low, info |
| **Status** | Open, acknowledged, resolved, ignored |
| **Message** | Alert description |
| **Created At** | Alert generation timestamp |
| **Actions** | Available operations |

## Alert Sources

### Source Types

| Source | Description |
|--------|-------------|
| **Validation** | Data quality validation failures |
| **Drift** | Distribution drift detection alerts |
| **Anomaly** | Anomaly detection alerts |
| **Model** | ML model performance alerts |

### Source Filter

Filter alerts by origin:

1. Click the **Source** filter dropdown
2. Select one or more sources
3. Alert list updates to show matching alerts

## Severity Levels

### Severity Classifications

| Severity | Color | Description |
|----------|-------|-------------|
| **Critical** | Red | Immediate action required |
| **High** | Orange | Urgent attention needed |
| **Medium** | Yellow | Should be addressed soon |
| **Low** | Blue | Minor issue for awareness |
| **Info** | Gray | Informational notification |

### Severity Filter

Filter alerts by severity:

1. Click the **Severity** filter dropdown
2. Select one or more severity levels
3. Alert list updates to show matching alerts

## Alert Status

### Status States

| Status | Description |
|--------|-------------|
| **Open** | Alert generated, not yet addressed |
| **Acknowledged** | Alert seen, investigation in progress |
| **Resolved** | Alert addressed and closed |
| **Ignored** | Alert dismissed as non-actionable |

### Status Filter

Filter alerts by status:

1. Click the **Status** filter dropdown
2. Select one or more statuses
3. Alert list updates to show matching alerts

## Alert Actions

### Individual Alert Actions

#### Acknowledge

Mark an alert as under investigation:

1. Click **Acknowledge** on the alert
2. Enter optional acknowledgment details:
   - **Actor Name**: Person acknowledging
   - **Message**: Investigation notes
3. Confirm acknowledgment
4. Alert status changes to "Acknowledged"

#### Resolve

Mark an alert as addressed:

1. Click **Resolve** on the alert
2. Enter resolution details:
   - **Actor Name**: Person resolving
   - **Resolution Notes**: How the issue was addressed
3. Confirm resolution
4. Alert status changes to "Resolved"

#### View Details

Access comprehensive alert information:

1. Click **View Details** on the alert
2. Review full alert data:
   - Complete alert message
   - Source information
   - Timestamps (created, acknowledged, resolved)
   - Actor information
   - Related data

### Bulk Actions

#### Bulk Acknowledge

Acknowledge multiple alerts simultaneously:

1. Select alerts using checkboxes
2. Click **Bulk Acknowledge**
3. Enter acknowledgment details
4. Confirm to acknowledge all selected alerts

#### Bulk Resolve

Resolve multiple alerts simultaneously:

1. Select alerts using checkboxes
2. Click **Bulk Resolve**
3. Enter resolution details
4. Confirm to resolve all selected alerts

## Alert Details Sheet

### Accessing Alert Details

Click **View Details** to open the alert details sheet:

| Section | Content |
|---------|---------|
| **Alert Information** | ID, source, severity, status |
| **Message** | Full alert description |
| **Timestamps** | Created, acknowledged, resolved times |
| **Actor Information** | Who acknowledged/resolved |
| **Source Details** | Data source, validation, or model information |
| **Related Data** | Context-specific information |

## Alert Correlations

### Viewing Correlations

The system identifies related alerts:

1. Click **View Correlations** on an alert
2. Review correlated alerts:
   - Same data source
   - Same time period
   - Related failure patterns
   - Cross-module correlations

### Correlation Analysis

| Correlation Type | Description |
|-----------------|-------------|
| **Temporal** | Alerts occurring near the same time |
| **Source-based** | Alerts from the same data source |
| **Causal** | Alerts that may share root cause |
| **Cross-module** | Drift correlating with anomalies |

## Cross-Alert System

### Overview

The Cross-Alert system provides persistent correlation between different alert types across the dashboard. This feature enables automatic detection of relationships between anomaly and drift alerts.

### Database-Backed Storage

All cross-alert configurations, correlations, and trigger events are stored in the database:

| Table | Description |
|-------|-------------|
| **CrossAlertConfig** | Global and source-specific configuration settings |
| **CrossAlertCorrelation** | Recorded correlation relationships between alerts |
| **CrossAlertTriggerEvent** | Auto-trigger event history and status |

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| **enabled** | Enable cross-alert detection | true |
| **trigger_drift_on_anomaly** | Automatically trigger drift analysis when anomalies detected | true |
| **trigger_anomaly_on_drift** | Automatically trigger anomaly detection when drift detected | true |
| **anomaly_rate_threshold** | Minimum anomaly rate to trigger correlation | 0.05 |
| **drift_percentage_threshold** | Minimum drift percentage to trigger correlation | 0.1 |
| **cooldown_seconds** | Time between auto-triggers for same source | 300 |

### Correlation Strength

Correlations are classified by strength:

| Strength | Criteria |
|----------|----------|
| **Strong** | High confidence score, small time delta, multiple common columns |
| **Moderate** | Medium confidence score, reasonable time delta |
| **Weak** | Low confidence score, large time delta, few common elements |

### Data Persistence

Cross-alert data persists across server restarts:

- Configuration settings are stored in `CrossAlertConfig`
- Historical correlations are preserved in `CrossAlertCorrelation`
- Trigger events and their status are logged in `CrossAlertTriggerEvent`

## Alert Workflow

### Recommended Triage Process

1. **Review**: Scan new alerts prioritized by severity
2. **Acknowledge**: Mark alerts under investigation
3. **Investigate**: Determine root cause and impact
4. **Remediate**: Address underlying issues
5. **Resolve**: Close alerts with resolution notes
6. **Review**: Analyze patterns for prevention

### Best Practices

| Practice | Description |
|----------|-------------|
| **Prompt Acknowledgment** | Acknowledge critical alerts within minutes |
| **Documentation** | Include detailed resolution notes |
| **Root Cause Analysis** | Investigate patterns across related alerts |
| **Automation** | Configure notification rules for critical alerts |

## Alert Statistics

### Summary Cards

| Card | Content |
|------|---------|
| **Total Alerts** | All-time alert count |
| **Active Alerts** | Currently open or acknowledged |
| **By Severity** | Distribution across severity levels |
| **By Source** | Distribution across source types |
| **By Status** | Distribution across statuses |
| **24h Trend** | Volume change over 24 hours |
| **Top Sources** | Data sources generating most alerts |

### Trend Analysis

Review alert patterns:

- Daily/weekly/monthly volumes
- Severity distribution changes
- Source-based patterns
- Resolution time metrics

## Integration with Other Modules

### Validation Integration

Validation failures generate alerts with:

- Validation ID reference
- Failed validator details
- Issue summary
- Link to validation results

### Drift Monitoring Integration

Drift detection generates alerts with:

- Monitor configuration reference
- Drift magnitude
- Affected columns
- Link to drift details

### Anomaly Detection Integration

Anomaly detection generates alerts with:

- Detection results reference
- Anomaly count and rate
- Algorithm used
- Link to anomaly details

### Model Monitoring Integration

Model performance issues generate alerts with:

- Model reference
- Affected metric
- Threshold violation details
- Link to model dashboard

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/alerts` | GET | List alerts with filters |
| `/alerts/summary` | GET | Retrieve alert statistics |
| `/alerts/{id}` | GET | Retrieve alert details |
| `/alerts/{id}/acknowledge` | POST | Acknowledge an alert |
| `/alerts/{id}/resolve` | POST | Resolve an alert |
| `/alerts/{id}/correlations` | GET | Retrieve correlated alerts |
| `/alerts/bulk/acknowledge` | POST | Bulk acknowledge alerts |
| `/alerts/bulk/resolve` | POST | Bulk resolve alerts |
| `/alerts/count` | GET | Get alert count by status |

### Cross-Alert API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cross-alerts/config` | GET | Get cross-alert configuration |
| `/cross-alerts/config` | PUT | Update cross-alert configuration |
| `/cross-alerts/correlations` | GET | List recorded correlations |
| `/cross-alerts/triggers` | GET | List auto-trigger events |
| `/cross-alerts/summary` | GET | Get cross-alert statistics |
