# Model Monitoring

The Model Monitoring module implements comprehensive lifecycle monitoring for machine learning models deployed in production environments. This module is integrated with the **truthound.ml.monitoring** framework to provide enterprise-grade performance tracking, drift detection, quality metrics computation, and intelligent alerting capabilities.

## Overview

Machine learning models necessitate continuous monitoring to ensure that predictive performance is sustained over time. In contrast to traditional software systems, ML models are susceptible to silent degradation resulting from data drift, concept drift, or alterations in the underlying data distribution. These challenges are addressed by the present module through the provision of:

- **Performance Metrics Collection**: Systematic tracking of latency, throughput, and error rate measurements
- **Drift Detection**: Application of statistical methods for the identification of distribution changes
- **Quality Metrics**: Quantitative assessment of classification and regression model performance
- **Intelligent Alerting**: Implementation of threshold-based, statistical, and trend-based alert rule evaluation

## Theoretical Foundation

### Statistical Characterization of Data Drift

Data drift is observed when the statistical properties of input data undergo temporal change. Multiple statistical tests derived from the truthound framework are employed by this module:

| Method | Mathematical Basis | Interpretation |
|--------|-------------------|----------------|
| **PSI** (Population Stability Index) | $PSI = \sum_{i} (A_i - E_i) \times \ln(A_i / E_i)$ | <0.1 stable, 0.1-0.25 slight drift, >0.25 significant |
| **KS** (Kolmogorov-Smirnov) | $D_n = \sup_x |F_n(x) - F(x)|$ | p-value based significance testing |
| **JS** (Jensen-Shannon) | $JS(P \| Q) = \frac{1}{2}KL(P \| M) + \frac{1}{2}KL(Q \| M)$ | Bounded [0,1], symmetric divergence |
| **Wasserstein** | $W_p(P, Q) = \left(\inf_{\gamma \in \Gamma(P,Q)} \int \|x-y\|^p d\gamma(x,y)\right)^{1/p}$ | Earth Mover's Distance |

### Concept Drift Detection Methodologies

Concept drift is characterized by a temporal change in the relationship between input features and the target variable. The module incorporates the following detection methods:

- **DDM** (Drift Detection Method): Error rate is monitored against warning and drift thresholds
- **ADWIN** (Adaptive Windowing): Window size is automatically adjusted based on change detection outcomes
- **Page-Hinkley**: A cumulative sum test is applied for the detection of gradual distributional changes

### Quality Metrics Definitions

For **classification** models, the following metrics are computed:
- **Accuracy**: $\frac{TP + TN}{TP + TN + FP + FN}$
- **Precision**: $\frac{TP}{TP + FP}$
- **Recall**: $\frac{TP}{TP + FN}$
- **F1 Score**: $2 \times \frac{Precision \times Recall}{Precision + Recall}$

For **regression** models, the following metrics are computed:
- **MAE**: $\frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$
- **MSE**: $\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2$
- **RMSE**: $\sqrt{MSE}$

## Model Monitoring Interface

### Aggregate Statistics Dashboard

The interface presents aggregate model monitoring metrics as summarized below:

| Metric | Description |
|--------|-------------|
| **Total Models** | Count of registered models |
| **Active Models** | Models currently in production |
| **Degraded Models** | Models exhibiting performance degradation |
| **Predictions (24h)** | Total predictions across all models |
| **Active Alerts** | Unresolved model-related alerts |
| **Models with Drift** | Models where input/output drift detected |
| **Average Latency** | Mean inference latency across models |

## Model Registration and Version Management

### Registration of a New Model

1. Click **Register Model**
2. Complete the registration form across three tabs:

#### Basic Information Tab

| Field | Description | Required |
|-------|-------------|----------|
| **Model Name** | Unique identifier for the model | Yes |
| **Version** | Semantic version (e.g., 1.0.0) | Yes |
| **Description** | Model purpose and documentation | No |
| **Metadata** | Custom key-value pairs | No |

#### Configuration Tab

The configuration parameters correspond directly to the truthound `MonitorConfig` specification:

**Feature Toggles**

| Setting | Description | Default |
|---------|-------------|---------|
| **Enable Performance Metrics** | Track latency, throughput, error rates | Enabled |
| **Enable Drift Detection** | Monitor distribution changes using `th.compare()` | Enabled |
| **Enable Quality Metrics** | Track accuracy, precision, recall, F1 (requires actual values) | Enabled |

**Drift Detection Parameters** (when enabled)

| Setting | Description | Default |
|---------|-------------|---------|
| **Drift Method** | Statistical method for drift detection | Auto |
| **Drift Threshold** | Score threshold for triggering alerts | 10% |

Available drift methods are enumerated below:
- **Auto**: The optimal method is automatically selected based on column type
- **PSI**: Population Stability Index (recommended for tabular data)
- **KS**: Kolmogorov-Smirnov test (distribution comparison)
- **JS**: Jensen-Shannon divergence (symmetric, bounded)
- **Wasserstein**: Earth Mover's Distance (geometry-aware)
- **Chi-squared**: Applicable to categorical features
- **KL**: Kullback-Leibler divergence
- **Hellinger**: Bounded distance metric

**Collection Parameters**

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| **Batch Size** | Metrics collection batch size | 100 | 1-10,000 |
| **Retention Hours** | Data retention period | 24 | 1-720 |
| **Collection Interval** | Metric collection frequency (seconds) | 60 | 1-3,600 |
| **Alert Evaluation Interval** | Rule evaluation frequency (seconds) | 30 | 1-3,600 |

#### Alerts Tab

The default alert rules that are automatically instantiated upon model registration are displayed:
- High Latency Alert (P95 > 500ms)
- Drift Detection Alert (exceeds configured threshold)
- Error Rate Alert (> 5%)

### Supported Model Types

| Type | Description | Key Metrics |
|------|-------------|-------------|
| **Classification** | Categorical prediction | Accuracy, precision, recall, F1 |
| **Regression** | Continuous value prediction | MAE, MSE, RMSE |
| **Ranking** | Ordered list generation | NDCG, MAP, MRR |

## Metrics Inspection Tab

### Examination of Model Metrics

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

### Application of truthound th.compare()

The drift detection capability is implemented through truthound's `th.compare()` function, which is employed to identify distribution changes between reference and current datasets.

**Operational Workflow**:
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

### Drift Alert Generation Mechanism

When the drift score exceeds the configured threshold, the following sequence is initiated:
1. An alert is created by the system with severity determined by score magnitude
2. The alert includes identification of drifted columns and their individual scores
3. The model status may be transitioned to "Degraded" if the score exceeds 0.3

## Quality Metrics Assessment

### Computation of Quality Metrics

Quality metrics are derived from predictions for which associated actual (ground truth) values have been recorded.

**For Classification Models**:
- Binary versus multi-class classification is automatically detected
- Accuracy is computed for all classification types
- Precision, recall, and F1 are computed for binary classification

**For Regression Models**:
- MAE (Mean Absolute Error) is computed
- MSE (Mean Squared Error) is computed
- RMSE (Root Mean Squared Error) is computed

### Recording Predictions with Ground Truth Values

To enable quality metrics computation, predictions must be recorded with the `actual` field:

```json
POST /model-monitoring/models/{id}/predictions
{
  "features": {"amount": 150.0, "merchant_type": "online"},
  "prediction": 0.85,
  "actual": 1,
  "latency_ms": 5.2
}
```

## Alert Rule Configuration

### Classification of Alert Rule Types

The module supports three distinct rule types, each corresponding to components within truthound's alerting framework:

#### Threshold-Based Rules

Threshold-based alerting is configured through the following parameters:
- **Metric Name**: Target metric to be monitored
- **Threshold**: Trigger value
- **Comparison**: gt, lt, gte, lte, eq
- **Duration**: Time period over which the condition must persist

#### Statistical Rules (Anomaly Detection Rules)

Anomaly-based alerting is performed using statistical methods:
- **Window Size**: Sample size utilized for statistical computation
- **Std Devs**: Number of standard deviations defining the threshold boundary
- An alert is triggered when the metric value exceeds the expected statistical range

#### Trend-Based Rules

Trend-based alerting is designed for the detection of gradual changes:
- **Direction**: "increasing" or "decreasing"
- **Slope Threshold**: Minimum rate of change required for activation
- **Lookback Minutes**: Time window employed for trend calculation
- Linear regression is utilized to detect degradation trends

### Exemplary Rule Configurations

| Rule | Type | Metric | Condition | Severity |
|------|------|--------|-----------|----------|
| Low Accuracy | threshold | accuracy | < 0.85 | High |
| High Latency | threshold | latency_p95 | > 500ms | Medium |
| Error Spike | statistical | error_rate | > 3 std devs | Critical |
| Drift Detected | threshold | drift_score | > 0.1 | High |
| Degrading Performance | trend | accuracy | decreasing, slope > 0.01 | Warning |

## Alert Handler Configuration Tab

### Supported Handler Types

The module supports handlers that correspond to truthound's alert handler framework:

| Handler | truthound Mapping | Use Case |
|---------|-------------------|----------|
| **Slack** | SlackAlertHandler | Team notifications |
| **Webhook** | WebhookAlertHandler | External integrations |
| **Email** | - | Stakeholder notifications |
| **PagerDuty** | PagerDutyAlertHandler | On-call escalation |

### Handler Configuration Parameters

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

### Status Transition Model

| Status | Color | Description | Automatic Transition |
|--------|-------|-------------|---------------------|
| **Active** | Green | Operating within parameters | - |
| **Paused** | Gray | Monitoring suspended | Manual |
| **Degraded** | Yellow | Performance below threshold | When drift_score > 0.3 |
| **Error** | Red | Experiencing errors | On repeated failures |

### Health Score Computation

The health score (0-100) is computed as a weighted composite of the following factors:
- Drift score contribution (weighted)
- Error rate contribution
- Latency threshold violations
- Active alert count

## Integration with the truthound Framework

### Component Mapping

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

### Model Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/model-monitoring/models` | GET | List registered models |
| `/model-monitoring/models` | POST | Register a new model |
| `/model-monitoring/models/{id}` | GET | Retrieve model details |
| `/model-monitoring/models/{id}` | PUT | Update model configuration |
| `/model-monitoring/models/{id}` | DELETE | Delete a model |
| `/model-monitoring/models/{id}/pause` | POST | Pause monitoring |
| `/model-monitoring/models/{id}/resume` | POST | Resume monitoring |

### Metrics and Analysis Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/model-monitoring/models/{id}/metrics` | GET | Retrieve performance metrics |
| `/model-monitoring/models/{id}/quality-metrics` | GET | Retrieve quality metrics |
| `/model-monitoring/models/{id}/detect-drift` | POST | Run drift detection |
| `/model-monitoring/models/{id}/predictions` | POST | Record prediction |

### Alert and Rule Management Endpoints

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

### Dashboard Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/model-monitoring/overview` | GET | Retrieve monitoring overview |
| `/model-monitoring/models/{id}/dashboard` | GET | Model-specific dashboard |

## Recommended Operational Practices

### Monitoring Strategy

1. **Establish a baseline**: Reference metrics should be established prior to production deployment
2. **Configure appropriate thresholds**: Thresholds should be determined based on business requirements and historical data analysis
3. **Enable drift detection**: Drift detection is considered essential for identifying silent model degradation
4. **Implement alerting**: Alert handlers should be configured to ensure timely notification of operational issues

### Drift Detection

1. **Select an appropriate method**: PSI is recommended for general use; KS is preferred when distributional sensitivity is required
2. **Define reasonable thresholds**: It is advisable to begin with conservative thresholds (0.1) and adjust based on observed drift patterns
3. **Monitor at the per-column level**: Individual features contributing to drift should be identified
4. **Correlate with performance metrics**: It should be noted that not all drift impacts model performance with equal magnitude

### Alert Configuration

1. **Prioritize critical metrics**: Alerting should be focused on metrics that directly impact business outcomes
2. **Mitigate alert fatigue**: Thresholds should be calibrated to minimize false positive rates
3. **Employ trend-based rules**: Trend rules are recommended for detecting gradual degradation before it reaches a critical state
4. **Configure escalation pathways**: Critical alerts should be routed to the appropriate operational channels

## Diagnostic and Troubleshooting Procedures

*This section is reserved for the documentation of common diagnostic procedures, known failure modes, and their corresponding resolution strategies. Practitioners are advised to consult the truthound ML Module Documentation for framework-level troubleshooting guidance.*

## References

- truthound ML Module Documentation: `.truthound_docs/advanced/ml-anomaly.md`
- Statistical Drift Detection Methods: Population Stability Index (PSI), Kolmogorov-Smirnov Test
- Concept Drift Detection: Gama, J., et al. (2014). A survey on concept drift adaptation
