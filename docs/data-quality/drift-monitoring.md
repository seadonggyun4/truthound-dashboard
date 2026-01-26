# Drift Monitoring

The Drift Monitoring module provides automated, continuous drift detection with alerting capabilities, root cause analysis, and remediation guidance.

## Overview

While ad-hoc drift comparisons provide point-in-time analysis, Drift Monitoring establishes persistent monitoring configurations that execute automatically, generate alerts when drift is detected, and provide analytical tools to understand and address distribution changes.

## Drift Monitor Management

### Monitor Statistics Dashboard

The monitoring interface displays aggregate statistics:

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

1. Click the **Create Monitor** button
2. Configure the monitor parameters:
   - **Name**: Descriptive identifier for the monitor
   - **Baseline Source**: Reference dataset for comparison
   - **Current Source**: Dataset to monitor for drift
   - **Detection Method**: Statistical method for drift detection
   - **Threshold**: Sensitivity threshold for drift detection
   - **Schedule**: Execution frequency (cron expression or interval)
   - **Columns**: Specific columns to monitor (optional)
3. Save the monitor configuration

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

The Alerts tab displays all drift-related alerts with filtering capabilities:

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

The Trends tab provides visualization of drift evolution over time:

1. Select a monitor from the dropdown
2. View the time-series chart of drift percentage
3. Identify patterns and trends in drift behavior
4. Correlate drift events with external factors

### Trend Visualization

- **X-Axis**: Time (default 30-day window)
- **Y-Axis**: Drift percentage
- **Data Points**: Individual monitor run results
- **Threshold Line**: Configured drift threshold for reference

## Column Drilldown

### Column-Level Analysis

Access detailed column-level drift information:

1. Click on a monitor or alert to view details
2. Access the column drilldown panel
3. Review per-column drift statistics:
   - Column name
   - Drift detected (boolean)
   - Drift magnitude
   - Statistical method used
   - P-value (where applicable)

### Column Comparison

For each drifted column, examine:

- Distribution histograms (baseline vs current)
- Statistical summary (mean, median, std, percentiles)
- Drift direction (increase/decrease)

## Root Cause Analysis

### ML-Based Root Cause Identification

The system provides automated root cause analysis for drift events:

1. Navigate to a specific monitor run with detected drift
2. Access the Root Cause Analysis panel
3. Review identified contributing factors:
   - Columns with highest drift contribution
   - Correlation patterns between drifted columns
   - Potential upstream causes
   - Temporal patterns

### Root Cause Report

| Section | Content |
|---------|---------|
| **Primary Factors** | Columns contributing most significantly to drift |
| **Correlation Analysis** | Relationships between drifted columns |
| **Temporal Patterns** | Time-based drift characteristics |
| **Recommended Actions** | Suggested investigation paths |

## Remediation Panel

### Suggested Actions

The Remediation Panel provides actionable guidance:

| Recommendation Type | Description |
|--------------------|-------------|
| **Investigation Steps** | Recommended analysis to understand root cause |
| **Data Actions** | Potential data corrections or transformations |
| **Process Actions** | Upstream process modifications to consider |
| **Monitoring Actions** | Threshold or configuration adjustments |

### Remediation Workflow

1. Review drift alert and root cause analysis
2. Access remediation suggestions
3. Implement appropriate actions
4. Verify drift resolution in subsequent runs
5. Resolve the alert

## Related Alerts

### Alert Correlation

The system identifies correlations between drift alerts and other alert types:

- **Anomaly Alerts**: Concurrent anomaly detections that may relate to drift
- **Validation Alerts**: Data quality issues that correlate with drift
- **Cross-Source Correlations**: Drift in related data sources

### Correlation Analysis

1. View a drift alert
2. Access the Related Alerts section
3. Review correlated alerts from other modules
4. Investigate common root causes

## Auto-Trigger Configuration

### Automated Response

Configure automated actions when drift is detected:

| Trigger Type | Description |
|--------------|-------------|
| **Notification** | Send alerts to configured channels |
| **Validation** | Trigger validation on affected sources |
| **Report Generation** | Generate detailed drift report |
| **Webhook** | Call external systems for integration |

### Configuration Options

1. Access the Auto-Trigger panel
2. Enable desired trigger types
3. Configure trigger parameters
4. Save configuration

## Monitor Configuration Reference

### Schedule Configuration

Monitors support multiple scheduling approaches:

| Schedule Type | Example | Description |
|--------------|---------|-------------|
| **Cron** | `0 0 * * *` | Daily at midnight |
| **Interval** | `6h` | Every 6 hours |
| **Data Change** | On new data | Trigger when source data updates |

### Detection Method Selection

Choose detection method based on data characteristics:

| Data Type | Recommended Methods |
|-----------|-------------------|
| Continuous numerical | ks, wasserstein, cvm |
| Categorical | chi2, psi |
| Mixed | auto (automatic selection) |
| High-dimensional | js, kl |

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
| `/drift/monitors/{id}/latest-run` | GET | Retrieve most recent run results |
| `/drift/monitors/{id}/runs/{runId}/root-cause` | GET | Retrieve root cause analysis |
| `/drift/alerts` | GET | List drift alerts |
| `/drift/alerts/{id}` | PUT | Update alert status |
| `/drift/monitors/summary` | GET | Retrieve aggregate statistics |
