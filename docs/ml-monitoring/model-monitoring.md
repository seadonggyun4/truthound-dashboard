# Model Monitoring

The Model Monitoring module provides comprehensive lifecycle monitoring for machine learning models in production environments. This module integrates with the **truthound.ml.monitoring** framework to deliver enterprise-grade performance tracking, drift detection, quality metrics, and intelligent alerting capabilities.

## Overview

Machine learning models require continuous monitoring to ensure they maintain performance over time. Unlike traditional software systems, ML models can degrade silently due to data drift, concept drift, or changes in the underlying data distribution. This module addresses these challenges by providing:

- **Performance Metrics Collection**: Latency, throughput, and error rate tracking
- **Drift Detection**: Statistical methods for detecting distribution changes
- **Quality Metrics**: Classification and regression performance measurement
- **Intelligent Alerting**: Threshold, statistical, and trend-based alert rules

## Theoretical Foundation

### Data Drift

Data drift occurs when the statistical properties of the input data change over time. The module employs multiple statistical tests from the truthound framework:

| Method | Mathematical Basis | Interpretation |
|--------|-------------------|----------------|
| **PSI** (Population Stability Index) | $PSI = \sum_{i} (A_i - E_i) \times \ln(A_i / E_i)$ | <0.1 stable, 0.1-0.25 slight drift, >0.25 significant |
| **KS** (Kolmogorov-Smirnov) | $D_n = \sup_x |F_n(x) - F(x)|$ | p-value based significance testing |
| **JS** (Jensen-Shannon) | $JS(P \| Q) = \frac{1}{2}KL(P \| M) + \frac{1}{2}KL(Q \| M)$ | Bounded [0,1], symmetric divergence |
| **Wasserstein** | $W_p(P, Q) = \left(\inf_{\gamma \in \Gamma(P,Q)} \int \|x-y\|^p d\gamma(x,y)\right)^{1/p}$ | Earth Mover's Distance |

### Concept Drift

Concept drift occurs when the relationship between input features and target variable changes. The module supports detection methods including:

- **DDM** (Drift Detection Method): Monitors error rate with warning and drift thresholds
- **ADWIN** (Adaptive Windowing): Automatically adjusts window size based on change detection
- **Page-Hinkley**: Cumulative sum test for detecting gradual changes

### Quality Metrics

For **classification** models:
- **Accuracy**: $\frac{TP + TN}{TP + TN + FP + FN}$
- **Precision**: $\frac{TP}{TP + FP}$
- **Recall**: $\frac{TP}{TP + FN}$
- **F1 Score**: $2 \times \frac{Precision \times Recall}{Precision + Recall}$

For **regression** models:
- **MAE**: $\frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$
- **MSE**: $\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2$
- **RMSE**: $\sqrt{MSE}$

## Model Monitoring Interface

### Statistics Dashboard

The interface displays aggregate model monitoring metrics:

| Metric | Description |
|--------|-------------|
| **Total Models** | Count of registered models |
| **Active Models** | Models currently in production |
| **Degraded Models** | Models exhibiting performance degradation |
| **Predictions (24h)** | Total predictions across all models |
| **Active Alerts** | Unresolved model-related alerts |
| **Models with Drift** | Models where input/output drift detected |
| **Average Latency** | Mean inference latency across models |

## Model Registration

### Registering a New Model

1. Click **Register Model**
2. Complete the registration form across three tabs:

#### Basic Info Tab

| Field | Description | Required |
|-------|-------------|----------|
| **Model Name** | Unique identifier for the model | Yes |
| **Version** | Semantic version (e.g., 1.0.0) | Yes |
| **Description** | Model purpose and documentation | No |
| **Metadata** | Custom key-value pairs | No |

#### Configuration Tab

The configuration maps directly to the truthound `MonitorConfig` parameters:

**Feature Toggles**

| Setting | Description | Default |
|---------|-------------|---------|
| **Enable Performance Metrics** | Track latency, throughput, error rates | Enabled |
| **Enable Drift Detection** | Monitor distribution changes using `th.compare()` | Enabled |
| **Enable Quality Metrics** | Track accuracy, precision, recall, F1 (requires actual values) | Enabled |

**Drift Detection Settings** (when enabled)

| Setting | Description | Default |
|---------|-------------|---------|
| **Drift Method** | Statistical method for drift detection | Auto |
| **Drift Threshold** | Score threshold for triggering alerts | 10% |

Available drift methods:
- **Auto**: Automatically selects optimal method based on column type
- **PSI**: Population Stability Index (recommended for tabular data)
- **KS**: Kolmogorov-Smirnov test (distribution comparison)
- **JS**: Jensen-Shannon divergence (symmetric, bounded)
- **Wasserstein**: Earth Mover's Distance (geometry-aware)
- **Chi-squared**: For categorical features
- **KL**: Kullback-Leibler divergence
- **Hellinger**: Bounded distance metric

**Collection Settings**

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| **Batch Size** | Metrics collection batch size | 100 | 1-10,000 |
| **Retention Hours** | Data retention period | 24 | 1-720 |
| **Collection Interval** | Metric collection frequency (seconds) | 60 | 1-3,600 |
| **Alert Evaluation Interval** | Rule evaluation frequency (seconds) | 30 | 1-3,600 |

#### Alerts Tab

Displays default alert rules that will be created:
- High Latency Alert (P95 > 500ms)
- Drift Detection Alert (exceeds configured threshold)
- Error Rate Alert (> 5%)

### Model Types

| Type | Description | Key Metrics |
|------|-------------|-------------|
| **Classification** | Categorical prediction | Accuracy, precision, recall, F1 |
| **Regression** | Continuous value prediction | MAE, MSE, RMSE |
| **Ranking** | Ordered list generation | NDCG, MAP, MRR |

## Metrics Tab

### Viewing Model Metrics

1. Select a model from the dropdown
2. Choose time range (1h, 6h, 24h, 7d)
3. Review metrics display and time-series charts

### Performance Metrics

| Metric | Description | Applicable To |
|--------|-------------|---------------|
| **Accuracy** | Correct predictions / total predictions | Classification |
| **Precision** | True positives / predicted positives | Classification |
| **Recall** | True positives / actual positives | Classification |
| **F1 Score** | Harmonic mean of precision and recall | Classification |
| **MAE** | Mean absolute error | Regression |
| **MSE** | Mean squared error | Regression |
| **RMSE** | Root mean squared error | Regression |

### Operational Metrics

| Metric | Description |
|--------|-------------|
| **Latency (p50)** | Median inference time |
| **Latency (p95)** | 95th percentile inference time |
| **Latency (p99)** | 99th percentile inference time |
| **Predictions Count** | Total predictions in period |
| **Error Rate** | Percentage of failed predictions |
| **Throughput** | Predictions per second |

## Drift Detection

### Using truthound th.compare()

The drift detection feature leverages truthound's `th.compare()` function to detect distribution changes between reference and current datasets.

**Workflow**:
1. Select reference data source (baseline distribution)
2. Select current data source (production distribution)
3. Choose drift detection method
4. Review per-column drift scores

**Interpretation Guidelines**:

| PSI Score | Interpretation | Action |
|-----------|----------------|--------|
| < 0.10 | No significant drift | Continue monitoring |
| 0.10 - 0.25 | Slight drift | Investigate root cause |
| > 0.25 | Significant drift | Consider model retraining |

### Drift Alert Generation

When drift score exceeds the configured threshold:
1. System creates an alert with severity based on score magnitude
2. Alert includes drifted columns and individual scores
3. Model status may transition to "Degraded" if score > 0.3

## Quality Metrics

### Computing Quality Metrics

Quality metrics are computed from predictions that have associated actual (ground truth) values.

**For Classification Models**:
- Automatically detects binary vs. multi-class classification
- Computes accuracy for all classification types
- Computes precision, recall, F1 for binary classification

**For Regression Models**:
- Computes MAE (Mean Absolute Error)
- Computes MSE (Mean Squared Error)
- Computes RMSE (Root Mean Squared Error)

### Recording Predictions with Actuals

To enable quality metrics, record predictions with the `actual` field:

```json
POST /model-monitoring/models/{id}/predictions
{
  "features": {"amount": 150.0, "merchant_type": "online"},
  "prediction": 0.85,
  "actual": 1,
  "latency_ms": 5.2
}
```

## Alert Rules Tab

### Alert Rule Types

The module supports three rule types mapping to truthound's alerting framework:

#### Threshold Rules

Simple threshold-based alerting:
- **Metric Name**: Target metric to monitor
- **Threshold**: Trigger value
- **Comparison**: gt, lt, gte, lte, eq
- **Duration**: Time condition must persist

#### Statistical Rules (Anomaly Rules)

Anomaly-based alerting using statistical methods:
- **Window Size**: Sample size for statistics
- **Std Devs**: Number of standard deviations for threshold
- Triggers when metric exceeds expected range

#### Trend Rules

Trend-based alerting for gradual changes:
- **Direction**: "increasing" or "decreasing"
- **Slope Threshold**: Minimum rate of change
- **Lookback Minutes**: Time window for trend calculation
- Uses linear regression to detect degradation trends

### Rule Examples

| Rule | Type | Metric | Condition | Severity |
|------|------|--------|-----------|----------|
| Low Accuracy | threshold | accuracy | < 0.85 | High |
| High Latency | threshold | latency_p95 | > 500ms | Medium |
| Error Spike | statistical | error_rate | > 3 std devs | Critical |
| Drift Detected | threshold | drift_score | > 0.1 | High |
| Degrading Performance | trend | accuracy | decreasing, slope > 0.01 | Warning |

## Alert Handlers Tab

### Handler Types

The module supports handlers mapping to truthound's alert handler framework:

| Handler | truthound Mapping | Use Case |
|---------|-------------------|----------|
| **Slack** | SlackAlertHandler | Team notifications |
| **Webhook** | WebhookAlertHandler | External integrations |
| **Email** | - | Stakeholder notifications |
| **PagerDuty** | PagerDutyAlertHandler | On-call escalation |

### Handler Configuration

#### Slack Handler

| Parameter | Description |
|-----------|-------------|
| **Webhook URL** | Slack incoming webhook URL |
| **Channel** | Target channel (optional override) |
| **Mention** | Users/groups to mention |

#### Webhook Handler

| Parameter | Description |
|-----------|-------------|
| **URL** | Webhook endpoint |
| **Method** | HTTP method (POST, PUT) |
| **Headers** | Custom HTTP headers |

#### PagerDuty Handler

| Parameter | Description |
|-----------|-------------|
| **Routing Key** | PagerDuty integration key |
| **Severity Mapping** | Map alert severity to PagerDuty severity |

## Model Lifecycle Management

### Status Transitions

| Status | Color | Description | Automatic Transition |
|--------|-------|-------------|---------------------|
| **Active** | Green | Operating within parameters | - |
| **Paused** | Gray | Monitoring suspended | Manual |
| **Degraded** | Yellow | Performance below threshold | When drift_score > 0.3 |
| **Error** | Red | Experiencing errors | On repeated failures |

### Health Score Calculation

The health score (0-100) is computed based on:
- Drift score contribution (weighted)
- Error rate contribution
- Latency threshold violations
- Active alert count

## Integration with truthound

### Framework Mapping

| Dashboard Feature | truthound Component |
|------------------|---------------------|
| Model Config | `MonitorConfig` |
| Performance Metrics | `PerformanceCollector` |
| Drift Detection | `th.compare()`, `DriftCollector` |
| Quality Metrics | `QualityCollector` |
| Threshold Rules | `ThresholdRule` |
| Statistical Rules | `AnomalyRule` |
| Trend Rules | `TrendRule` |
| Slack Alerts | `SlackAlertHandler` |
| Webhook Alerts | `WebhookAlertHandler` |
| PagerDuty Alerts | `PagerDutyAlertHandler` |

### Drift Detection Methods Reference

| Method | Type | Best For | Notes |
|--------|------|----------|-------|
| auto | - | General use | Selects optimal method per column |
| psi | Binned | Tabular data | Industry standard |
| ks | Distribution | Numeric columns | Sensitive to shape |
| js | Divergence | All types | Symmetric, bounded [0,1] |
| wasserstein | Distance | Numeric columns | Geometry-aware |
| chi2 | Statistical | Categorical | Chi-squared test |
| kl | Divergence | All types | Information-theoretic |
| cvm | Statistical | Numeric | Sensitive to tails |
| anderson | Statistical | Numeric | Most sensitive to tails |
| hellinger | Distance | All types | Bounded [0,1] |
| energy | Distance | Numeric | Location/scale sensitive |
| mmd | Kernel | High-dimensional | Maximum Mean Discrepancy |

## API Reference

### Model Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/model-monitoring/models` | GET | List registered models |
| `/model-monitoring/models` | POST | Register a new model |
| `/model-monitoring/models/{id}` | GET | Retrieve model details |
| `/model-monitoring/models/{id}` | PUT | Update model configuration |
| `/model-monitoring/models/{id}` | DELETE | Delete a model |
| `/model-monitoring/models/{id}/pause` | POST | Pause monitoring |
| `/model-monitoring/models/{id}/resume` | POST | Resume monitoring |

### Metrics & Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/model-monitoring/models/{id}/metrics` | GET | Retrieve performance metrics |
| `/model-monitoring/models/{id}/quality-metrics` | GET | Retrieve quality metrics |
| `/model-monitoring/models/{id}/detect-drift` | POST | Run drift detection |
| `/model-monitoring/models/{id}/predictions` | POST | Record prediction |

### Alerts & Rules

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/model-monitoring/alerts` | GET | List model alerts |
| `/model-monitoring/alerts/{id}/acknowledge` | POST | Acknowledge alert |
| `/model-monitoring/alerts/{id}/resolve` | POST | Resolve alert |
| `/model-monitoring/rules` | GET | List alert rules |
| `/model-monitoring/rules` | POST | Create alert rule |
| `/model-monitoring/rules/{id}` | PUT | Update alert rule |
| `/model-monitoring/rules/{id}` | DELETE | Delete alert rule |
| `/model-monitoring/handlers` | GET | List alert handlers |
| `/model-monitoring/handlers` | POST | Create alert handler |
| `/model-monitoring/handlers/{id}/test` | POST | Test alert handler |

### Dashboard

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/model-monitoring/overview` | GET | Retrieve monitoring overview |
| `/model-monitoring/models/{id}/dashboard` | GET | Model-specific dashboard |

## Best Practices

### Monitoring Strategy

1. **Start with baseline**: Establish reference metrics before production deployment
2. **Configure appropriate thresholds**: Based on business requirements and historical data
3. **Enable drift detection**: Essential for detecting silent model degradation
4. **Set up alerting**: Configure handlers for timely notification of issues

### Drift Detection

1. **Choose appropriate method**: PSI for general use, KS for distribution sensitivity
2. **Set reasonable thresholds**: Start conservative (0.1) and adjust based on observed drift
3. **Monitor per-column**: Identify specific features causing drift
4. **Correlate with performance**: Not all drift impacts model performance equally

### Alert Configuration

1. **Prioritize critical metrics**: Focus alerts on metrics that impact business outcomes
2. **Avoid alert fatigue**: Set thresholds that minimize false positives
3. **Use trend rules**: Catch gradual degradation before it becomes critical
4. **Configure escalation**: Route critical alerts to appropriate channels

## References

- truthound ML Module Documentation: `.truthound_docs/advanced/ml-anomaly.md`
- Statistical Drift Detection Methods: Population Stability Index (PSI), Kolmogorov-Smirnov Test
- Concept Drift Detection: Gama, J., et al. (2014). A survey on concept drift adaptation
