# Drift Detection

The Drift Detection module enables comparison of data distributions between baseline and current datasets to identify statistical changes that may indicate data quality degradation or upstream process modifications.

## Overview

Data drift occurs when the statistical properties of data change over time. The Drift Detection module implements multiple statistical methods to quantify distribution differences between a reference (baseline) dataset and a comparison (current) dataset, providing actionable insights into data evolution.

## Drift Comparison Interface

### Initiating a Comparison

1. Click the **New Comparison** button
2. Select the **Baseline Source**: The reference dataset representing expected data characteristics
3. Select the **Current Source**: The dataset to compare against the baseline
4. Configure detection parameters
5. Execute the comparison

### Configuration Parameters

#### Detection Method

The system supports multiple statistical methods for drift detection:

| Method | Description | Best For |
|--------|-------------|----------|
| **auto** | Automatic method selection based on data characteristics | General use when unsure which method to apply |
| **ks** | Kolmogorov-Smirnov test | Continuous numerical distributions |
| **psi** | Population Stability Index | Credit scoring and risk modeling |
| **chi2** | Chi-squared test | Categorical variables |
| **js** | Jensen-Shannon divergence | Probability distributions |
| **kl** | Kullback-Leibler divergence | Information-theoretic comparison |
| **wasserstein** | Wasserstein distance (Earth Mover's Distance) | Comparing distributions with different supports |
| **cvm** | Cramér-von Mises criterion | Continuous distributions |
| **anderson** | Anderson-Darling test | Distribution tails sensitivity |

#### Threshold Override

Configure the sensitivity of drift detection:

- Lower thresholds increase sensitivity (more drift detected)
- Higher thresholds decrease sensitivity (only significant drift detected)
- Default threshold varies by method

#### Statistical Correction

Apply multiple testing correction to control false positive rate:

| Correction | Description |
|------------|-------------|
| **none** | No correction applied |
| **bonferroni** | Conservative correction, controls family-wise error rate |
| **holm** | Step-down procedure, less conservative than Bonferroni |
| **bh** | Benjamini-Hochberg procedure, controls false discovery rate |

#### Column Selection

Optionally restrict comparison to specific columns:

- By default, all common columns are compared
- Select specific columns when focusing on critical attributes
- Column selection is based on the source schema

## Comparison Results

### Summary Statistics

Upon completion, the comparison displays:

| Metric | Description |
|--------|-------------|
| **Total Columns Compared** | Number of columns included in the analysis |
| **Drifted Columns** | Number of columns exhibiting statistically significant drift |
| **Drift Percentage** | Proportion of columns with detected drift |
| **Detection Method** | The statistical method used for comparison |

### Drift Status Indicators

| Status | Description |
|--------|-------------|
| **High Drift** | Significant distribution changes detected |
| **Drift Detected** | Moderate distribution changes detected |
| **No Drift** | Distributions are statistically similar |

### Column-Level Details

For each column compared, the results include:

| Attribute | Description |
|-----------|-------------|
| **Column Name** | The column identifier |
| **Drift Detected** | Boolean indicator of drift presence |
| **Method** | Statistical method applied to this column |
| **Drift Level** | Quantitative measure of drift magnitude |
| **P-Value** | Statistical significance of the drift (where applicable) |

## Comparison History

The Drift page maintains a history of executed comparisons:

- View past comparisons with their results
- Compare different time periods by reviewing historical comparisons
- Track drift evolution over time

## Statistical Methods Reference

### Kolmogorov-Smirnov (KS) Test

The KS test measures the maximum difference between cumulative distribution functions:

- **Null Hypothesis**: Samples are drawn from the same distribution
- **Statistic**: Maximum absolute difference between CDFs
- **Interpretation**: Higher values indicate greater distribution difference

### Population Stability Index (PSI)

PSI quantifies distribution shift commonly used in credit risk:

- **Formula**: PSI = Σ (Actual% - Expected%) × ln(Actual% / Expected%)
- **Thresholds**: PSI < 0.1 (no significant shift), 0.1-0.25 (moderate shift), > 0.25 (significant shift)
- **Use Case**: Model monitoring, scorecard stability

### Chi-Squared Test

Chi-squared test compares observed vs expected frequencies:

- **Application**: Categorical variables
- **Null Hypothesis**: Observed frequencies match expected frequencies
- **Interpretation**: Higher chi-squared values indicate greater divergence

### Jensen-Shannon Divergence

JS divergence is a symmetric measure of distribution similarity:

- **Range**: 0 (identical) to 1 (maximally different)
- **Properties**: Symmetric, always finite
- **Interpretation**: Lower values indicate more similar distributions

### Kullback-Leibler Divergence

KL divergence measures information loss when approximating one distribution with another:

- **Range**: 0 to infinity
- **Properties**: Asymmetric
- **Interpretation**: Lower values indicate better approximation

### Wasserstein Distance

Also known as Earth Mover's Distance, measures the minimum cost of transforming one distribution into another:

- **Interpretation**: Accounts for distance between distribution supports
- **Use Case**: Distributions with different supports or shifted means

## Use Cases

### Model Monitoring

Monitor input feature distributions to detect when production data diverges from training data:

1. Use training dataset as baseline
2. Compare periodic production data samples
3. Alert when drift exceeds thresholds
4. Investigate root causes before model degradation occurs

### Data Pipeline Validation

Detect upstream changes that affect data characteristics:

1. Establish baseline from validated historical data
2. Compare new data batches upon arrival
3. Identify columns with significant changes
4. Investigate upstream process modifications

### Regulatory Compliance

Maintain distribution stability for regulated models:

1. Document baseline distributions
2. Periodically compare production data
3. Generate drift reports for audit
4. Trigger review processes when thresholds exceeded

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/drift/compare` | POST | Execute drift comparison |
| `/drift/comparisons` | GET | List comparison history |
| `/drift/comparisons/{id}` | GET | Retrieve comparison details |
