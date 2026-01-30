# Profile Comparison

The Profile Comparison module enables longitudinal analysis of data profiles by comparing statistical summaries of a data source across different points in time. This capability is essential for detecting gradual data drift, monitoring data volume trends, and establishing quantitative baselines for data quality expectations.

## Overview

Data profiling produces a statistical summary of a dataset—row counts, null percentages, unique value counts, cardinality, average string lengths, and other descriptive metrics. While a single profile provides a useful snapshot, the true analytical value emerges when profiles are compared over time. Profile Comparison transforms isolated snapshots into a continuous quality signal by computing deltas, identifying trends, and highlighting columns whose characteristics have shifted.

## Core Concepts

### Data Profile

A data profile is a statistical summary captured at a specific point in time. Profiles are generated through the `th.profile()` function and stored in the dashboard database. Each profile contains:

| Attribute | Description |
|-----------|-------------|
| **Row Count** | Total number of rows in the dataset |
| **Column Count** | Total number of columns |
| **Null Count** | Total null values across all columns |
| **Data Size** | Estimated size of the dataset |
| **Per-Column Metrics** | Statistical summaries for each individual column |

### Per-Column Metrics

Each column in a profile includes the following statistical measures:

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

When two profiles are compared, the system computes the delta (difference) for each metric. Deltas are expressed both as absolute values and as percentages, enabling analysts to quickly assess the magnitude and direction of change.

| Delta Direction | Indicator | Interpretation |
|-----------------|-----------|----------------|
| **Increase** | ↑ (green or red depending on metric) | Metric value has grown |
| **Decrease** | ↓ (red or green depending on metric) | Metric value has declined |
| **Stable** | — | No significant change detected |

The color interpretation is context-dependent. For example, an increase in null percentage is typically negative (red), while an increase in row count is typically positive (green).

## Profile Comparison Interface

### Selection Controls

The interface provides the following controls for defining the comparison scope:

| Control | Description |
|---------|-------------|
| **Source Selector** | Choose the data source to analyze |
| **Period Selector** | Filter profiles by time range (7, 30, 90 days) |
| **Baseline Profile** | Select the reference profile for comparison |
| **Comparison Profile** | Select the profile to compare against the baseline |
| **Comparison Mode** | Manual selection or automatic latest-vs-previous |

### Summary Statistics Cards

Four summary cards display the current profile's key metrics alongside change indicators:

| Card | Metric | Change Indicator |
|------|--------|------------------|
| **Row Count** | Total rows in the latest profile | ↑/↓ with absolute and percentage delta |
| **Column Count** | Total columns | ↑/↓ with delta |
| **Null Values** | Total null values across all columns | ↑/↓ with delta |
| **Data Size** | Estimated dataset size | ↑/↓ with delta |

### Trend Charts

The trend visualization section displays time-series charts of key metrics:

1. **Row Count Trend**: Line/area chart showing row count over time, enabling identification of data volume patterns (growth, drops, seasonality)
2. **Quality Metrics Trend**: Composite chart tracking null percentage, unique percentage, and other quality indicators over time

### Column Comparison Table

A detailed table presents per-column comparison results:

| Column | Description |
|--------|-------------|
| **Column Name** | Name of the data column |
| **Null %** | Null percentage with delta from baseline |
| **Unique %** | Unique value percentage with delta |
| **Average Length** | Mean string length with delta (string columns) |
| **Cardinality** | Distinct value count with delta |
| **Change Magnitude** | Overall degree of change for the column |

## Analytical Applications

### Data Volume Monitoring

Profile comparison reveals trends in data volume that may indicate upstream pipeline issues:

- **Sudden drops** in row count may indicate failed ingestion jobs
- **Unexpected growth** may indicate duplicate ingestion or scope changes
- **Plateaus** may indicate stale data sources that are no longer being updated

### Quality Trend Analysis

By tracking null percentages and uniqueness over time, analysts can identify gradual quality degradation before it reaches critical thresholds:

1. Select a 90-day period for broad trend visibility
2. Monitor the null percentage trend for upward drift
3. Monitor uniqueness percentages for columns expected to have high cardinality
4. Investigate any column showing sustained movement in quality metrics

### Baseline Establishment

Profile comparison supports the establishment of quantitative baselines for data quality expectations:

1. Generate profiles at regular intervals (daily or weekly)
2. Identify stable metric ranges over a sufficient observation period
3. Use the established baselines to configure [anomaly detection](../ml-monitoring/anomaly.md) thresholds
4. Monitor deviations from baseline using the trend charts

### Pre/Post Change Validation

When significant changes are made to data pipelines or source systems, profile comparison provides a mechanism for validating that the change had the intended effect without introducing regressions:

1. Generate a profile immediately before the change (baseline)
2. Implement the change
3. Generate a new profile
4. Compare the two profiles to verify expected differences and identify unintended side effects

## Integration Points

| Integration | Description |
|-------------|-------------|
| **[Drift Detection](./drift.md)** | Statistical drift methods provide more rigorous comparison; profile comparison offers a broader overview |
| **[Anomaly Detection](../ml-monitoring/anomaly.md)** | Baselines established through profile comparison can inform anomaly detection thresholds |
| **[Schema Evolution](./schema-evolution.md)** | Column count changes in profiles may correlate with schema evolution events |
| **[Validation History](./validations.md)** | Quality trends from profile comparison complement pass/fail trends from validation history |

## Best Practices

| Practice | Recommendation |
|----------|----------------|
| **Regular Profiling** | Generate profiles at consistent intervals for meaningful trend analysis |
| **Use Appropriate Periods** | Select longer periods (90 days) for trend identification; shorter periods (7 days) for recent change detection |
| **Investigate Anomalies** | Any unexpected delta warrants investigation, even if validation continues to pass |
| **Combine with Drift Detection** | Use profile comparison for broad monitoring and drift detection for statistically rigorous change detection |
| **Document Baselines** | Record expected metric ranges in the Business Glossary for organizational knowledge |

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
