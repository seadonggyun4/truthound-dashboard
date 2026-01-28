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

| Method | Description | Best For | Column Type |
|--------|-------------|----------|-------------|
| **auto** | Automatic method selection based on data characteristics | General use when unsure which method to apply | Any |
| **ks** | Kolmogorov-Smirnov test | Continuous numerical distributions | Numeric only |
| **psi** | Population Stability Index | Credit scoring and risk modeling | Numeric only |
| **chi2** | Chi-squared test | Categorical variables | Categorical |
| **js** | Jensen-Shannon divergence | Probability distributions (symmetric, bounded 0-1) | Any |
| **kl** | Kullback-Leibler divergence | Information-theoretic comparison (asymmetric) | Numeric only |
| **wasserstein** | Wasserstein distance (Earth Mover's Distance) | Comparing distributions with different supports | Numeric only |
| **cvm** | Cramér-von Mises criterion | More sensitive to tails than KS test | Numeric only |
| **anderson** | Anderson-Darling test | Most sensitive to tail differences | Numeric only |
| **hellinger** | Hellinger distance | Bounded metric with triangle inequality | Any |
| **bhattacharyya** | Bhattacharyya distance | Classification error bounds | Any |
| **tv** | Total Variation distance | Maximum probability difference | Any |
| **energy** | Energy distance | Location and scale sensitivity | Numeric only |
| **mmd** | Maximum Mean Discrepancy | High-dimensional kernel-based comparison | Numeric only |

> **Note**: All 14 methods are fully supported by truthound v1.2.9+. For categorical columns, use `auto`, `chi2`, `js`, `hellinger`, `bhattacharyya`, or `tv`. For numeric columns, all methods are available.

#### Threshold Override

Configure the sensitivity of drift detection:

- Lower thresholds increase sensitivity (more drift detected)
- Higher thresholds decrease sensitivity (only significant drift detected)
- Default threshold varies by method

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
- **Properties**: Asymmetric (KL(P||Q) ≠ KL(Q||P))
- **Interpretation**: Lower values indicate better approximation
- **Tip**: Use `method="js"` for a symmetric variant

### Wasserstein Distance

Also known as Earth Mover's Distance, measures the minimum cost of transforming one distribution into another:

- **Interpretation**: Accounts for distance between distribution supports
- **Use Case**: Distributions with different supports or shifted means
- **Properties**: Intuitive physical interpretation, normalized by baseline std

### Cramér-von Mises Test

The CvM test is more sensitive to differences in the tails than the KS test:

- **Properties**: Integrates squared differences between CDFs
- **Use Case**: When tail behavior is important
- **Interpretation**: Lower p-values indicate greater distribution difference

### Anderson-Darling Test

The AD test is the most sensitive to tail differences:

- **Properties**: Weights tail differences more heavily than center
- **Use Case**: Detecting subtle changes in distribution tails
- **Interpretation**: Higher statistic values indicate greater difference

### Hellinger Distance

Hellinger distance is a bounded metric for comparing probability distributions:

- **Range**: 0 (identical) to 1 (no overlap)
- **Properties**: Symmetric, satisfies triangle inequality, true metric
- **Formula**: H(P,Q) = (1/√2) × √(Σ(√p_i - √q_i)²)
- **Use Case**: When you need a proper metric with bounded range

### Bhattacharyya Distance

Measures overlap between two probability distributions:

- **Range**: 0 to ∞ (0 = identical)
- **Properties**: Related to classification error bounds
- **Formula**: D_B = -ln(Σ√(p_i × q_i))
- **Use Case**: Classification problems, measuring distribution overlap

### Total Variation Distance

Measures the maximum probability difference between distributions:

- **Range**: 0 (identical) to 1 (completely different)
- **Properties**: Symmetric, bounded, triangle inequality
- **Formula**: TV(P,Q) = (1/2) × Σ|p_i - q_i|
- **Use Case**: Simple interpretation - "largest probability difference"

### Energy Distance

Measures differences in location and scale of distributions:

- **Range**: 0 to ∞ (0 = identical)
- **Properties**: Characterizes distributions, consistent statistical test
- **Formula**: E(P,Q) = 2E[|X-Y|] - E[|X-X'|] - E[|Y-Y'|]
- **Use Case**: Detecting shifts in mean or variance

### Maximum Mean Discrepancy (MMD)

Kernel-based method for comparing distributions:

- **Range**: 0 to ∞ (0 = identical in RKHS)
- **Properties**: Non-parametric, works in high dimensions
- **Kernel**: Gaussian RBF (default), with automatic bandwidth selection
- **Use Case**: High-dimensional data where density estimation fails

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
