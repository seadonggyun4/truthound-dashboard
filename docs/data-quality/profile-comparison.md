# Profile Comparison

The Profile Comparison module provides systematic longitudinal analysis of data profiles by comparing statistical summaries of a data source across different points in time. This capability is considered essential for the detection of gradual data drift, the monitoring of data volume trends, and the establishment of quantitative baselines for data quality expectations.

## Overview

Data profiling produces a statistical summary of a dataset -- row counts, null percentages, unique value counts, cardinality, average string lengths, and other descriptive metrics. While an individual profile yields a useful snapshot, the substantive analytical value is realized when profiles are compared over time. Profile Comparison transforms isolated snapshots into a continuous quality signal through the computation of deltas, the identification of trends, and the highlighting of columns whose characteristics have undergone measurable shifts.

## Foundational Concepts

### Data Profile

A data profile is defined as a statistical summary captured at a specific point in time. Profiles are generated through the `th.profile()` function and are persisted in the dashboard database. Each profile is composed of the following attributes:

| Attribute | Description |
|-----------|-------------|
| **Row Count** | Total number of rows in the dataset |
| **Column Count** | Total number of columns |
| **Null Count** | Total null values across all columns |
| **Data Size** | Estimated size of the dataset |
| **Per-Column Metrics** | Statistical summaries for each individual column |

### Per-Column Metrics

Each column within a profile is characterized by the following statistical measures:

| Metric | Description | Applicable Types |
|--------|-------------|------------------|
| **Null Percentage** | Proportion of null values | All |
| **Unique Percentage** | Proportion of distinct values | All |
| **Cardinality** | Number of distinct values | All |
| **Average Length** | Mean string length | String |
| **Min / Max** | Minimum and maximum values | Numeric, Datetime |
| **Mean / Std Dev** | Mean and standard deviation | Numeric |
| **Top Values** | Most frequent values and their counts | Categorical |

### Delta Computation

When two profiles are subjected to comparison, the system computes the delta (difference) for each metric. Deltas are expressed both as absolute values and as percentages, thereby enabling analysts to rapidly assess the magnitude and direction of change.

| Delta Direction | Indicator | Interpretation |
|-----------------|-----------|----------------|
| **Increase** | ↑ (green or red depending on metric) | Metric value has grown |
| **Decrease** | ↓ (red or green depending on metric) | Metric value has declined |
| **Stable** | — | No significant change detected |

It should be noted that the color interpretation is context-dependent. For instance, an increase in null percentage is generally considered negative (red), whereas an increase in row count is typically regarded as positive (green).

## Profile Comparison Interface Specifications

### Selection Controls

The interface provides the following controls for the definition of the comparison scope:

| Control | Description |
|---------|-------------|
| **Source Selector** | Choose the data source to analyze |
| **Period Selector** | Filter profiles by time range (7, 30, 90 days) |
| **Baseline Profile** | Select the reference profile for comparison |
| **Comparison Profile** | Select the profile to compare against the baseline |
| **Comparison Mode** | Manual selection or automatic latest-vs-previous |

### Summary Statistics Cards

Four summary cards are presented, displaying the current profile's key metrics alongside change indicators:

| Card | Metric | Change Indicator |
|------|--------|------------------|
| **Row Count** | Total rows in the latest profile | ↑/↓ with absolute and percentage delta |
| **Column Count** | Total columns | ↑/↓ with delta |
| **Null Values** | Total null values across all columns | ↑/↓ with delta |
| **Data Size** | Estimated dataset size | ↑/↓ with delta |

### Trend Charts

The trend visualization section displays time-series charts of key metrics:

1. **Row Count Trend**: A line/area chart depicting row count over time is rendered, facilitating the identification of data volume patterns (growth, drops, seasonality).
2. **Quality Metrics Trend**: A composite chart is provided, tracking null percentage, unique percentage, and other quality indicators over time.

### Column Comparison Table

A detailed table is presented containing per-column comparison results:

| Column | Description |
|--------|-------------|
| **Column Name** | Name of the data column |
| **Null %** | Null percentage with delta from baseline |
| **Unique %** | Unique value percentage with delta |
| **Average Length** | Mean string length with delta (string columns) |
| **Cardinality** | Distinct value count with delta |
| **Change Magnitude** | Overall degree of change for the column |

## Analytical Application Scenarios

### Data Volume Monitoring

Profile comparison is observed to reveal trends in data volume that may be indicative of upstream pipeline issues:

- **Sudden drops** in row count may be indicative of failed ingestion jobs
- **Unexpected growth** may be indicative of duplicate ingestion or scope changes
- **Plateaus** may be indicative of stale data sources that are no longer being updated

### Quality Trend Analysis

Through the tracking of null percentages and uniqueness over time, analysts are enabled to identify gradual quality degradation before critical thresholds are reached:

1. A 90-day period should be selected for broad trend visibility
2. The null percentage trend should be monitored for upward drift
3. Uniqueness percentages should be monitored for columns expected to exhibit high cardinality
4. Any column demonstrating sustained movement in quality metrics warrants further investigation

### Baseline Establishment

Profile comparison facilitates the establishment of quantitative baselines for data quality expectations:

1. Profiles should be generated at regular intervals (daily or weekly)
2. Stable metric ranges should be identified over a sufficient observation period
3. The established baselines may then be utilized to configure [anomaly detection](../ml-monitoring/anomaly.md) thresholds
4. Deviations from baseline should be monitored using the trend charts

### Pre/Post Change Validation

When significant changes are introduced to data pipelines or source systems, profile comparison provides a rigorous mechanism for validating that the change produced the intended effect without introducing regressions:

1. A profile should be generated immediately before the change (baseline)
2. The change should be implemented
3. A new profile should be generated
4. The two profiles should be compared to verify expected differences and to identify unintended side effects

## Integration Points

| Integration | Description |
|-------------|-------------|
| **[Drift Detection](./drift.md)** | Statistical drift methods provide more rigorous comparison; profile comparison offers a broader overview |
| **[Anomaly Detection](../ml-monitoring/anomaly.md)** | Baselines established through profile comparison can inform anomaly detection thresholds |
| **[Schema Evolution](./schema-evolution.md)** | Column count changes in profiles may correlate with schema evolution events |
| **[Validation History](./validations.md)** | Quality trends from profile comparison complement pass/fail trends from validation history |

## Recommended Operational Practices

| Practice | Recommendation |
|----------|----------------|
| **Regular Profiling** | Profiles should be generated at consistent intervals to ensure meaningful trend analysis |
| **Use Appropriate Periods** | Longer periods (90 days) are recommended for trend identification; shorter periods (7 days) are recommended for recent change detection |
| **Investigate Anomalies** | Any unexpected delta warrants investigation, even if validation continues to pass |
| **Combine with Drift Detection** | Profile comparison should be employed for broad monitoring, while drift detection should be reserved for statistically rigorous change detection |
| **Document Baselines** | Expected metric ranges should be recorded in the Business Glossary for organizational knowledge retention |

## API Reference

### Profile Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/profile` | POST | Generate a basic data profile |
| `/sources/{id}/profile/advanced` | POST | Generate an advanced profile with ProfilerConfig |
| `/profile-comparison` | GET | Get profile comparison data |
| `/profile-comparison/trends` | GET | Get profile metric trends over time |
| `/profile-comparison/columns` | GET | Get per-column comparison details |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_id` | string | Data source identifier |
| `baseline_id` | string | Baseline profile identifier |
| `comparison_id` | string | Comparison profile identifier |
| `period` | string | Time period (7d, 30d, 90d) |
| `metrics` | string[] | Specific metrics to include |

## Glossary

| Term | Definition |
|------|------------|
| **Data Profile** | A statistical summary of a dataset captured at a specific point in time |
| **Delta** | The computed difference between two profile metrics |
| **Baseline** | The reference profile against which comparisons are made |
| **Cardinality** | The number of distinct values in a column |
| **Quality Regression** | A deterioration in data quality metrics over time |
