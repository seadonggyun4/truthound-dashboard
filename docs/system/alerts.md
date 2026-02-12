# Unified Alert Management System

The Dashboard Alerts module provides a centralized interface for the management of alerts originating from all dashboard monitoring components, including validation failure detection, distribution drift analysis, anomaly identification, and model performance monitoring.

> **Note**: The Dashboard Alerts system constitutes a dashboard-level aggregation framework that collects alerts from various monitoring subsystems within the truthound-dashboard application. It is to be distinguished from the truthound library's checkpoint alert system, which provides lower-level programmatic alerting capabilities.

## System Overview

The alert system aggregates notifications from multiple heterogeneous sources into a unified interface, thereby enabling efficient triage, acknowledgment, and resolution workflows. This consolidated approach obviates the necessity of monitoring multiple alert sources independently.

### Architectural Design

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

## Alert Interface Specifications

### Summary Dashboard

The interface presents aggregate alert statistics as follows:

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

The primary alert listing presents all alerts with comprehensive filtering capabilities:

| Column | Description |
|--------|-------------|
| **Alert ID** | Unique identifier |
| **Source Type** | Origin module (validation, drift, anomaly, model) |
| **Severity** | Critical, high, medium, low, info |
| **Status** | Open, acknowledged, resolved, ignored |
| **Message** | Alert description |
| **Created At** | Alert generation timestamp |
| **Actions** | Available operations |

## Alert Source Classification

### Source Types

| Source | Description |
|--------|-------------|
| **Validation** | Data quality validation failures |
| **Drift** | Distribution drift detection alerts |
| **Anomaly** | Anomaly detection alerts |
| **Model** | ML model performance alerts |

### Source Filtering

Alerts may be filtered by their originating source through the following procedure:

1. Click the **Source** filter dropdown
2. Select one or more sources
3. Alert list updates to show matching alerts

## Severity Level Taxonomy

### Severity Classifications

| Severity | Color | Description |
|----------|-------|-------------|
| **Critical** | Red | Immediate action required |
| **High** | Orange | Urgent attention needed |
| **Medium** | Yellow | Should be addressed soon |
| **Low** | Blue | Minor issue for awareness |
| **Info** | Gray | Informational notification |

### Severity Filtering

Alerts may be filtered by severity level through the following procedure:

1. Click the **Severity** filter dropdown
2. Select one or more severity levels
3. Alert list updates to show matching alerts

## Alert Status Model

### Status State Definitions

| Status | Description |
|--------|-------------|
| **Open** | Alert generated, not yet addressed |
| **Acknowledged** | Alert seen, investigation in progress |
| **Resolved** | Alert addressed and closed |
| **Ignored** | Alert dismissed as non-actionable |

### Status Filtering

Alerts may be filtered by their current status through the following procedure:

1. Click the **Status** filter dropdown
2. Select one or more statuses
3. Alert list updates to show matching alerts

## Alert Lifecycle Operations

### Individual Alert Operations

#### Acknowledgment

An alert is marked as being under active investigation through the following procedure:

1. Click **Acknowledge** on the alert
2. Enter optional acknowledgment details:
   - **Actor Name**: Person acknowledging
   - **Message**: Investigation notes
3. Confirm acknowledgment
4. Alert status changes to "Acknowledged"

#### Resolution

An alert is marked as having been addressed through the following procedure:

1. Click **Resolve** on the alert
2. Enter resolution details:
   - **Actor Name**: Person resolving
   - **Resolution Notes**: How the issue was addressed
3. Confirm resolution
4. Alert status changes to "Resolved"

#### Detailed Inspection

Comprehensive alert information may be accessed through the following procedure:

1. Click **View Details** on the alert
2. Review full alert data:
   - Complete alert message
   - Source information
   - Timestamps (created, acknowledged, resolved)
   - Actor information
   - Related data

### Bulk Operations

#### Bulk Acknowledgment

Multiple alerts may be acknowledged simultaneously through the following procedure:

1. Select alerts using checkboxes
2. Click **Bulk Acknowledge**
3. Enter acknowledgment details
4. Confirm to acknowledge all selected alerts

#### Bulk Resolution

Multiple alerts may be resolved simultaneously through the following procedure:

1. Select alerts using checkboxes
2. Click **Bulk Resolve**
3. Enter resolution details
4. Confirm to resolve all selected alerts

## Alert Detail Inspection Panel

### Accessing Alert Details

The alert details panel is accessed by clicking **View Details**:

| Section | Content |
|---------|---------|
| **Alert Information** | ID, source, severity, status |
| **Message** | Full alert description |
| **Timestamps** | Created, acknowledged, resolved times |
| **Actor Information** | Who acknowledged/resolved |
| **Source Details** | Data source, validation, or model information |
| **Related Data** | Context-specific information |

## Alert Correlation Analysis

### Viewing Correlations

The system is designed to identify related alerts through correlation analysis:

1. Click **View Correlations** on an alert
2. Review correlated alerts:
   - Same data source
   - Same time period
   - Related failure patterns
   - Cross-module correlations

### Correlation Type Classification

| Correlation Type | Description |
|-----------------|-------------|
| **Temporal** | Alerts occurring near the same time |
| **Source-based** | Alerts from the same data source |
| **Causal** | Alerts that may share root cause |
| **Cross-module** | Drift correlating with anomalies |

## Cross-Alert Correlation System

### Overview

The Cross-Alert system provides persistent correlation capabilities between disparate alert types across the dashboard. This subsystem enables the automatic detection of relationships between anomaly alerts and drift alerts, thereby facilitating root cause analysis.

### Database-Backed Persistence Layer

All cross-alert configurations, correlations, and trigger events are persisted in the database:

| Table | Description |
|-------|-------------|
| **CrossAlertConfig** | Global and source-specific configuration settings |
| **CrossAlertCorrelation** | Recorded correlation relationships between alerts |
| **CrossAlertTriggerEvent** | Auto-trigger event history and status |

### Configuration Parameters

| Setting | Description | Default |
|---------|-------------|---------|
| **enabled** | Enable cross-alert detection | true |
| **trigger_drift_on_anomaly** | Automatically trigger drift analysis when anomalies detected | true |
| **trigger_anomaly_on_drift** | Automatically trigger anomaly detection when drift detected | true |
| **anomaly_rate_threshold** | Minimum anomaly rate to trigger correlation | 0.05 |
| **drift_percentage_threshold** | Minimum drift percentage to trigger correlation | 0.1 |
| **cooldown_seconds** | Time between auto-triggers for same source | 300 |

### Correlation Strength Classification

Correlations are classified according to their computed strength:

| Strength | Criteria |
|----------|----------|
| **Strong** | High confidence score, small time delta, multiple common columns |
| **Moderate** | Medium confidence score, reasonable time delta |
| **Weak** | Low confidence score, large time delta, few common elements |

### Data Persistence Guarantees

Cross-alert data is maintained across server restarts through the following mechanisms:

- Configuration settings are stored in `CrossAlertConfig`
- Historical correlations are preserved in `CrossAlertCorrelation`
- Trigger events and their status are logged in `CrossAlertTriggerEvent`

## Alert Triage Workflow

### Recommended Triage Procedure

1. **Review**: Scan new alerts prioritized by severity
2. **Acknowledge**: Mark alerts under investigation
3. **Investigate**: Determine root cause and impact
4. **Remediate**: Address underlying issues
5. **Resolve**: Close alerts with resolution notes
6. **Review**: Analyze patterns for prevention

### Recommended Operational Practices

| Practice | Description |
|----------|-------------|
| **Prompt Acknowledgment** | Acknowledge critical alerts within minutes |
| **Documentation** | Include detailed resolution notes |
| **Root Cause Analysis** | Investigate patterns across related alerts |
| **Automation** | Configure notification rules for critical alerts |

## Alert Statistical Analysis

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

Alert patterns may be reviewed across the following dimensions:

- Daily/weekly/monthly volumes
- Severity distribution changes
- Source-based patterns
- Resolution time metrics

## Integration with Adjacent Modules

### Validation Module Integration

Validation failures generate alerts containing the following metadata:

- Validation ID reference
- Failed validator details
- Issue summary
- Link to validation results

### Drift Monitoring Module Integration

Drift detection generates alerts containing the following metadata:

- Monitor configuration reference
- Drift magnitude
- Affected columns
- Link to drift details

### Anomaly Detection Module Integration

Anomaly detection generates alerts containing the following metadata:

- Detection results reference
- Anomaly count and rate
- Algorithm used
- Link to anomaly details

### Model Monitoring Module Integration

Model performance degradation generates alerts containing the following metadata:

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

### Cross-Alert API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cross-alerts/config` | GET | Get cross-alert configuration |
| `/cross-alerts/config` | PUT | Update cross-alert configuration |
| `/cross-alerts/correlations` | GET | List recorded correlations |
| `/cross-alerts/triggers` | GET | List auto-trigger events |
| `/cross-alerts/summary` | GET | Get cross-alert statistics |
