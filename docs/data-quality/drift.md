# Drift Detection

The Drift Detection module provides systematic comparison of data distributions between baseline and current datasets, facilitating the identification of statistical changes that may be indicative of data quality degradation or modifications to upstream processes.

## Overview

Data drift is observed when the statistical properties of a dataset undergo transformation over time. The Drift Detection module implements multiple statistical methods to quantify distribution differences between a reference (baseline) dataset and a comparison (current) dataset, thereby providing actionable insights into the temporal evolution of data characteristics.

## Drift Comparison Interface Specifications

### Initiating a Comparison

The following procedural steps are to be followed when initiating a drift comparison:

1. The **New Comparison** button is to be selected
2. The **Baseline Source** is designated: this constitutes the reference dataset representing the expected data characteristics
3. The **Current Source** is designated: this constitutes the dataset to be compared against the baseline
4. Detection parameters are configured according to analytical requirements
5. The comparison is executed

#### Source Selection Constraint

A constraint is enforced by the system whereby the baseline source and the current source must constitute distinct datasets. When an identical data source is selected for both, the following safeguards are applied:

- The **Compare** button is rendered inactive, thereby preventing the submission of an invalid comparison request
- An inline validation message is displayed beneath the Current Source selector, indicating that distinct sources must be selected

This constraint is imposed because drift detection is defined as a comparison between two distinct data distributions. A comparison of a dataset against itself would yield no meaningful statistical information and would trivially return zero drift across all columns and metrics.

### Configuration Parameters

#### Detection Method

Multiple statistical methods for drift detection are supported by the system:

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

The sensitivity of drift detection may be configured as follows:

- Lower thresholds result in increased sensitivity (a greater number of drift instances are detected)
- Higher thresholds result in decreased sensitivity (only statistically significant drift is detected)
- The default threshold is determined by the selected method

#### Column Selection

The comparison may optionally be restricted to a specified subset of columns:

- By default, all common columns are included in the comparison
- Specific columns may be selected when the analysis is focused on critical attributes
- Column selection is determined by the source schema

## Comparative Analysis Results

### Summary Statistics

Upon completion of the comparison, the following summary statistics are presented:

| Metric | Description |
|--------|-------------|
| **Total Columns Compared** | Number of columns included in the analysis |
| **Drifted Columns** | Number of columns exhibiting statistically significant drift |
| **Drift Percentage** | Proportion of columns with detected drift |
| **Detection Method** | The statistical method employed for the comparison |

### Drift Status Indicators

| Status | Description |
|--------|-------------|
| **High Drift** | Significant distribution changes have been detected |
| **Drift Detected** | Moderate distribution changes have been detected |
| **No Drift** | Distributions are determined to be statistically similar |

### Column-Level Details

For each column subjected to comparison, the following results are reported:

| Attribute | Description |
|-----------|-------------|
| **Column Name** | The column identifier |
| **Drift Detected** | Boolean indicator of drift presence |
| **Method** | Statistical method applied to the given column |
| **Drift Level** | Quantitative measure of drift magnitude |
| **P-Value** | Statistical significance of the observed drift (where applicable) |

## Comparison History

A persistent history of executed comparisons is maintained on the Drift page:

- Previously executed comparisons and their associated results may be reviewed
- Different temporal periods may be compared through examination of historical comparisons
- The evolution of drift over time may be tracked and analyzed

## Statistical Methodology Reference

### Kolmogorov-Smirnov (KS) Test

The KS test is employed to measure the maximum difference between cumulative distribution functions:

- **Null Hypothesis**: The samples are drawn from the same underlying distribution
- **Statistic**: Maximum absolute difference between CDFs
- **Interpretation**: Higher values are indicative of greater distribution divergence

### Population Stability Index (PSI)

The PSI is utilized to quantify distribution shift and is commonly employed in credit risk assessment:

- **Formula**: PSI = Σ (Actual% - Expected%) × ln(Actual% / Expected%)
- **Thresholds**: PSI < 0.1 (no significant shift), 0.1-0.25 (moderate shift), > 0.25 (significant shift)
- **Application**: Model monitoring and scorecard stability assessment

### Chi-Squared Test

The Chi-squared test is applied to compare observed versus expected frequencies:

- **Application**: Categorical variables
- **Null Hypothesis**: Observed frequencies conform to expected frequencies
- **Interpretation**: Higher chi-squared values are indicative of greater divergence between distributions

### Jensen-Shannon Divergence

The JS divergence constitutes a symmetric measure of distributional similarity:

- **Range**: 0 (identical) to 1 (maximally different)
- **Properties**: Symmetric, always finite
- **Interpretation**: Lower values are indicative of greater distributional similarity

### Kullback-Leibler Divergence

The KL divergence quantifies the information loss incurred when one distribution is approximated by another:

- **Range**: 0 to infinity
- **Properties**: Asymmetric (KL(P||Q) ≠ KL(Q||P))
- **Interpretation**: Lower values are indicative of a more accurate approximation
- **Note**: The `method="js"` parameter may be employed to obtain a symmetric variant

### Wasserstein Distance

The Wasserstein distance, also referred to as the Earth Mover's Distance, measures the minimum cost of transforming one distribution into another:

- **Interpretation**: The distance between distribution supports is accounted for
- **Application**: Distributions characterized by different supports or shifted means
- **Properties**: Intuitive physical interpretation, normalized by baseline standard deviation

### Cramér-von Mises Test

The CvM test exhibits greater sensitivity to differences in the tails of distributions than the KS test:

- **Properties**: Squared differences between CDFs are integrated
- **Application**: Scenarios in which tail behavior is of particular importance
- **Interpretation**: Lower p-values are indicative of greater distributional divergence

### Anderson-Darling Test

The AD test is regarded as the most sensitive to differences in distribution tails:

- **Properties**: Tail differences are weighted more heavily than those in the center of the distribution
- **Application**: Detection of subtle changes in distribution tails
- **Interpretation**: Higher statistic values are indicative of greater distributional difference

### Hellinger Distance

The Hellinger distance constitutes a bounded metric for the comparison of probability distributions:

- **Range**: 0 (identical) to 1 (no overlap)
- **Properties**: Symmetric, satisfies triangle inequality, true metric
- **Formula**: H(P,Q) = (1/√2) × √(Σ(√p_i - √q_i)²)
- **Application**: Scenarios requiring a proper metric with a bounded range

### Bhattacharyya Distance

The Bhattacharyya distance is employed to measure the overlap between two probability distributions:

- **Range**: 0 to ∞ (0 = identical)
- **Properties**: Related to classification error bounds
- **Formula**: D_B = -ln(Σ√(p_i × q_i))
- **Application**: Classification problems and the measurement of distributional overlap

### Total Variation Distance

The Total Variation distance quantifies the maximum probability difference between distributions:

- **Range**: 0 (identical) to 1 (completely different)
- **Properties**: Symmetric, bounded, triangle inequality
- **Formula**: TV(P,Q) = (1/2) × Σ|p_i - q_i|
- **Application**: Contexts requiring straightforward interpretation as the largest probability difference

### Energy Distance

The Energy distance is utilized to measure differences in the location and scale of distributions:

- **Range**: 0 to ∞ (0 = identical)
- **Properties**: Characterizes distributions, consistent statistical test
- **Formula**: E(P,Q) = 2E[|X-Y|] - E[|X-X'|] - E[|Y-Y'|]
- **Application**: Detection of shifts in mean or variance

### Maximum Mean Discrepancy (MMD)

The MMD constitutes a kernel-based method for the comparison of distributions:

- **Range**: 0 to ∞ (0 = identical in RKHS)
- **Properties**: Non-parametric, applicable in high-dimensional settings
- **Kernel**: Gaussian RBF (default), with automatic bandwidth selection
- **Application**: High-dimensional data where density estimation is intractable

## Analytical Application Scenarios

### Model Monitoring

Input feature distributions should be monitored to detect instances in which production data diverges from training data:

1. The training dataset is designated as the baseline
2. Periodic production data samples are compared against the baseline
3. Alerts are generated when drift exceeds established thresholds
4. Root causes are investigated prior to the onset of model degradation

### Data Pipeline Validation

Upstream changes that affect data characteristics may be detected through the following procedure:

1. A baseline is established from validated historical data
2. New data batches are compared upon arrival
3. Columns exhibiting significant changes are identified
4. Upstream process modifications are investigated

### Regulatory Compliance

Distribution stability for regulated models is maintained through the following methodology:

1. Baseline distributions are documented
2. Production data is periodically compared against the baseline
3. Drift reports are generated for audit purposes
4. Review processes are triggered when established thresholds are exceeded

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/drift/compare` | POST | Execute drift comparison |
| `/drift/comparisons` | GET | List comparison history |
| `/drift/comparisons/{id}` | GET | Retrieve comparison details |
