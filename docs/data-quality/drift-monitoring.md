# Drift Monitoring

The Drift Monitoring module implements automated, continuous drift surveillance with alerting capabilities, root cause analysis, and remediation guidance.

## Overview

Whereas ad-hoc drift comparisons yield point-in-time analyses, the Drift Monitoring subsystem establishes persistent monitoring configurations that are executed automatically, generates alerts upon drift detection, and furnishes analytical instrumentation for the comprehension and remediation of distribution changes.

## Drift Monitor Lifecycle Management

### Monitor Statistics Dashboard

The monitoring interface presents aggregate statistics as enumerated below:

| Metric | Description |
|--------|-------------|
| **Total Monitors** | Count of all configured drift monitors |
| **Active Monitors** | Count of monitors currently executing on schedule |
| **Paused Monitors** | Count of monitors temporarily suspended |
| **Monitors with Drift** | Count of monitors that detected drift in their latest run |
| **Open Alerts** | Total unresolved drift alerts |
| **Critical Alerts** | Alerts with critical severity |
| **High Alerts** | Alerts with high severity |

### Creating a Drift Monitor

The following procedure is employed to instantiate a new drift monitor:

1. The **Create Monitor** button is selected
2. The monitor parameters are configured as follows:
   - **Name**: A descriptive identifier assigned to the monitor
   - **Baseline Source**: The reference dataset against which comparisons are conducted
   - **Current Source**: The dataset to be monitored for distributional drift
   - **Detection Method**: The statistical method employed for drift detection
   - **Threshold**: The sensitivity threshold governing drift detection
   - **Schedule**: The execution frequency, expressed as a cron expression or interval
   - **Columns**: Specific columns designated for monitoring (optional)
3. The monitor configuration is persisted

### Monitor Lifecycle Operations

| Action | Description |
|--------|-------------|
| **Run Now** | Execute the monitor immediately, independent of schedule |
| **Pause** | Suspend scheduled execution while preserving configuration |
| **Resume** | Reactivate a paused monitor |
| **Edit** | Modify monitor configuration |
| **Delete** | Remove the monitor and its history |

## Alerts Tab

### Alert Listing

The Alerts tab enumerates all drift-related alerts and provides the following filtering capabilities:

#### Filter Options

- **Status**: Open, Acknowledged, Resolved, Ignored
- **Severity**: Critical, High, Medium, Low

#### Alert Information

| Attribute | Description |
|-----------|-------------|
| **Monitor Name** | The monitor that generated the alert |
| **Severity** | Alert severity level |
| **Status** | Current alert status |
| **Drift Percentage** | Proportion of columns with detected drift |
| **Created At** | Timestamp when alert was generated |

### Alert Actions

| Action | Description |
|--------|-------------|
| **Acknowledge** | Mark alert as seen and under investigation |
| **Resolve** | Mark alert as addressed and closed |
| **Ignore** | Dismiss alert as non-actionable |

## Trends Tab

### Historical Drift Analysis

The Trends tab provides temporal visualization of drift evolution. The following analytical workflow is prescribed:

1. A monitor is selected from the dropdown
2. The time-series chart of drift percentage is examined
3. Patterns and trends in drift behavior are identified
4. Drift events are correlated with external factors

### Trend Visualization

- **X-Axis**: Time (default 30-day window)
- **Y-Axis**: Drift percentage
- **Data Points**: Individual monitor run results
- **Threshold Line**: Configured drift threshold for reference

## Column Drilldown

### Column-Level Analysis

Detailed column-level drift information may be accessed through the following procedure:

1. A monitor or alert is selected to view its details
2. The column drilldown panel is accessed
3. Per-column drift statistics are reviewed:
   - Column name
   - Drift detected (boolean)
   - Drift magnitude
   - Statistical method used
   - P-value (where applicable)

### Column Comparison

For each column exhibiting drift, the following diagnostic artifacts are examined:

- Distribution histograms (baseline vs current)
- Statistical summary (mean, median, std, percentiles)
- Drift direction (increase/decrease)

## Root Cause Analysis Framework

### ML-Based Root Cause Identification

Automated root cause analysis is provided for drift events through the following methodology:

1. Navigation is performed to a specific monitor run in which drift was detected
2. The Root Cause Analysis panel is accessed
3. The identified contributing factors are reviewed:
   - Columns exhibiting the highest drift contribution
   - Correlation patterns observed between drifted columns
   - Potential upstream causal factors
   - Temporal patterns

### Root Cause Report

| Section | Content |
|---------|---------|
| **Primary Factors** | Columns contributing most significantly to drift |
| **Correlation Analysis** | Relationships between drifted columns |
| **Temporal Patterns** | Time-based drift characteristics |
| **Recommended Actions** | Suggested investigation paths |

## Remediation Guidance Framework

### Suggested Actions

The Remediation Guidance Framework furnishes actionable recommendations as categorized below:

| Recommendation Type | Description |
|--------------------|-------------|
| **Investigation Steps** | Recommended analysis to understand root cause |
| **Data Actions** | Potential data corrections or transformations |
| **Process Actions** | Upstream process modifications to consider |
| **Monitoring Actions** | Threshold or configuration adjustments |

### Remediation Workflow

The prescribed remediation workflow is conducted as follows:

1. The drift alert and root cause analysis are reviewed
2. Remediation suggestions are accessed
3. Appropriate corrective actions are implemented
4. Drift resolution is verified in subsequent monitoring runs
5. The alert is resolved upon confirmation

## Related Alerts

### Alert Correlation

Correlations between drift alerts and other alert types are identified by the system:

- **Anomaly Alerts**: Concurrent anomaly detections that may be related to drift
- **Validation Alerts**: Data quality issues that correlate with drift
- **Cross-Source Correlations**: Drift observed in related data sources

### Correlation Analysis

The following procedure is employed to investigate correlated alerts:

1. A drift alert is viewed
2. The Related Alerts section is accessed
3. Correlated alerts from other modules are reviewed
4. Common root causes are investigated

## Cross-Feature Auto-Trigger Configuration

The Auto-Trigger system facilitates cross-feature automation between the drift detection and anomaly detection modules. When an event is detected within one module, the system is capable of automatically initiating diagnostic checks in the complementary module, thereby establishing a bidirectional monitoring loop.

### Accessing the Configuration Panel

The **Configure** button in the Drift Monitoring toolbar is selected to open the Auto-Trigger Configuration dialog. The dialog is implemented with scrollable behavior, ensuring that all settings remain accessible regardless of viewport dimensions.

### Trigger Directions

Two independent trigger directions are supported, each of which may be independently enabled or disabled:

| Trigger Direction | Description |
|-------------------|-------------|
| **Drift → Anomaly** | When drift is detected in a dataset, automatically initiate anomaly detection on the same data source to identify whether the distribution shift has introduced anomalous records |
| **Anomaly → Drift** | When an anomaly spike is detected, automatically initiate drift comparison to determine whether the anomalies are attributable to an underlying distribution change |

### Trigger Thresholds

Thresholds define the minimum conditions that must be satisfied before a cross-feature trigger is activated. These parameters are designed to prevent unnecessary trigger cascades during minor fluctuations:

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Anomaly Rate Threshold** | Minimum anomaly rate (as percentage) required to trigger a drift check | 10% |
| **Anomaly Count Threshold** | Minimum number of detected anomalies required to trigger a drift check | 10 |
| **Drift Percentage Threshold** | Minimum percentage of drifted columns required to trigger an anomaly check | 10% |
| **Drifted Columns Threshold** | Minimum number of drifted columns required to trigger an anomaly check | 2 |

### Additional Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Notify on Correlation** | Send a notification when cross-feature correlation is detected between drift and anomaly events | Enabled |
| **Cooldown (seconds)** | Minimum interval between consecutive auto-triggered checks, to prevent alert storms | 300 |

### Configuration Scope

The Auto-Trigger configuration supports two levels of scope:

- **Global Configuration**: Applied to all data sources by default
- **Source-Specific Configuration**: Overrides global settings for a particular data source, thereby permitting fine-grained control

In the absence of explicitly saved configuration, the system returns default values. Configuration is persisted to the database upon the initial save operation.

## Monitor Configuration Specifications

### Alert Threshold Configuration (Dashboard Feature)

> **Note**: The following alert threshold settings are **dashboard-specific features**, not truthound library parameters. These settings govern how the dashboard generates and categorizes alerts based on drift detection results obtained from `th.compare()`.

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| **Alert on Drift** | Enable/disable alert generation when drift is detected | Enabled | On/Off |
| **Critical Threshold** | Drift percentage threshold for critical severity alerts | 0.5 (50%) | 0.0-1.0 |
| **High Threshold** | Drift percentage threshold for high severity alerts | 0.3 (30%) | 0.0-1.0 |

Alert severity is determined by these thresholds based on the drift percentage returned by truthound:
- **Critical**: Drift percentage ≥ Critical Threshold
- **High**: Drift percentage ≥ High Threshold (but < Critical)
- **Medium**: Drift detected but below High Threshold

### Schedule Configuration

Multiple scheduling approaches are supported by the monitoring subsystem:

| Schedule Type | Example | Description |
|--------------|---------|-------------|
| **Cron** | `0 0 * * *` | Daily at midnight |
| **Interval** | `6h` | Every 6 hours |
| **Data Change** | On new data | Trigger when source data updates |

### Detection Method Selection

The detection method should be selected based on the characteristics of the data under examination (14 methods are available in truthound v1.2.9+):

| Data Type | Recommended Methods |
|-----------|-------------------|
| Continuous numerical | ks, psi, wasserstein, cvm, anderson, energy |
| Categorical | chi2, js, hellinger, bhattacharyya, tv |
| Mixed | auto (automatic selection) |
| High-dimensional | mmd, js, kl |
| Bounded metric needed | hellinger, tv (both 0-1 range) |

> **Note**: Refer to [Drift Detection](drift.md) for comprehensive descriptions of all 14 statistical methods.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/drift/monitors` | GET | List all drift monitors |
| `/drift/monitors` | POST | Create a new drift monitor |
| `/drift/monitors/{id}` | GET | Retrieve monitor details |
| `/drift/monitors/{id}` | PUT | Update monitor configuration |
| `/drift/monitors/{id}` | DELETE | Delete a drift monitor |
| `/drift/monitors/{id}/run` | POST | Execute monitor immediately |
| `/drift/monitors/{id}/trend` | GET | Retrieve drift trend data |
| `/drift/monitors/{id}/runs` | GET | List execution history for a monitor |
| `/drift/monitors/{id}/runs/latest` | GET | Retrieve most recent run results |
| `/drift/monitors/{id}/runs/statistics` | GET | Retrieve aggregated run statistics |
| `/drift/monitors/{id}/runs/{runId}` | GET | Retrieve specific run details |
| `/drift/monitors/{id}/runs/{runId}/root-cause` | GET | Retrieve root cause analysis |
| `/drift/alerts` | GET | List drift alerts |
| `/drift/alerts/{id}` | PUT | Update alert status |
| `/drift/monitors/summary` | GET | Retrieve aggregate statistics |
