# Quality Reporter

The Quality Reporter is a module designed to quantitatively assess the quality of validation rules and generate reports in a variety of formats.

## Overview

The Quality Reporter measures the accuracy of validation rules through the quality assessment framework provided by truthound. It computes confusion matrix-based metrics, including F1 Score, Precision, Recall, and Accuracy, to classify each rule into a corresponding quality level.

### Quality Assessment Metrics

| Metric | Definition | Formula |
|--------|------------|---------|
| **F1 Score** | Harmonic mean of Precision and Recall | 2 × (Precision × Recall) / (Precision + Recall) |
| **Precision** | Proportion of true positives among all predicted positives | TP / (TP + FP) |
| **Recall** | Proportion of true positives among all actual positives | TP / (TP + FN) |
| **Accuracy** | Proportion of correct predictions among all predictions | (TP + TN) / (TP + TN + FP + FN) |

### Confusion Matrix

Quality metrics are derived from the four fundamental elements of the confusion matrix:

| Element | Definition |
|---------|------------|
| **TP (True Positive)** | The rule correctly identifies conforming data as conforming |
| **TN (True Negative)** | The rule correctly identifies anomalous data as anomalous |
| **FP (False Positive)** | The rule incorrectly classifies conforming data as anomalous (false alarm) |
| **FN (False Negative)** | The rule incorrectly classifies anomalous data as conforming (missed detection) |

## Quality Level Classification

Rules are classified into quality levels based on their F1 Score:

| Level | F1 Score Range | Description |
|-------|----------------|-------------|
| **Excellent** | >= 0.9 | Superior quality; suitable for production environments |
| **Good** | 0.7 -- 0.9 | Satisfactory quality; appropriate for most operational contexts |
| **Acceptable** | 0.5 -- 0.7 | Tolerable quality; improvement is recommended |
| **Poor** | 0.3 -- 0.5 | Insufficient quality; rule revision is required |
| **Unacceptable** | < 0.3 | Inadequate; immediate remediation is necessary |

### Quality Threshold Configuration

The default threshold values may be customized by the user:

```json
{
  "thresholds": {
    "excellent": 0.9,
    "good": 0.7,
    "acceptable": 0.5,
    "poor": 0.3
  }
}
```

## Quality Score Calculation

### Score Calculation Settings

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| **sample_size** | Number of data samples used for evaluation | 10,000 | 100 -- 1,000,000 |
| **rule_names** | Specific list of rules to evaluate (optional) | All rules | -- |

### Score Calculation Results

Upon completion of score calculation, the following information is provided:

| Field | Description |
|-------|-------------|
| **scores** | List of quality scores for individual rules |
| **statistics** | Aggregate statistics (mean, minimum, and maximum F1, etc.) |
| **level_distribution** | Distribution of rules across quality levels |

## Report Generation

### Supported Formats

| Format | Extension | Intended Use |
|--------|-----------|--------------|
| **Console** | .txt | Terminal output, logging |
| **JSON** | .json | API integration, automation |
| **HTML** | .html | Dashboards, documentation |
| **Markdown** | .md | Git repositories, wikis |
| **JUnit** | .xml | CI/CD pipelines |

### Report Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| **title** | Report title | -- |
| **description** | Report description | -- |
| **include_metrics** | Include detailed metrics | true |
| **include_confusion_matrix** | Include confusion matrix | false |
| **include_recommendations** | Include recommendations | true |
| **include_statistics** | Include statistics section | true |
| **include_summary** | Include summary section | true |
| **include_charts** | Include charts (HTML format only) | true |
| **sort_order** | Sorting criterion | f1_desc |
| **max_scores** | Maximum number of scores to include | All |
| **theme** | HTML theme | professional |

### Sorting Options

| Option | Description |
|--------|-------------|
| **f1_desc** | F1 Score, descending |
| **f1_asc** | F1 Score, ascending |
| **precision_desc** | Precision, descending |
| **recall_desc** | Recall, descending |
| **name_asc** | Rule name, ascending |
| **name_desc** | Rule name, descending |

### HTML Themes

| Theme | Description |
|-------|-------------|
| **light** | Light background theme |
| **dark** | Dark background theme |
| **professional** | Professional business theme |

## Score Filtering

### Filter Options

| Filter | Description | Example |
|--------|-------------|---------|
| **min_level** | Minimum quality level | good |
| **max_level** | Maximum quality level | excellent |
| **min_f1** | Minimum F1 Score | 0.7 |
| **max_f1** | Maximum F1 Score | 0.95 |
| **min_confidence** | Minimum confidence score | 0.8 |
| **should_use_only** | Include only recommended rules | true |
| **include_columns** | Columns to include | ["email", "phone"] |
| **exclude_columns** | Columns to exclude | ["internal_id"] |
| **rule_types** | Rule types | ["not_null", "unique"] |

## Score Comparison

Quality scores from multiple sources may be compared using the following configuration:

| Setting | Description |
|---------|-------------|
| **source_ids** | List of source IDs to compare |
| **sort_by** | Sorting criterion (f1_score, precision, recall, confidence) |
| **descending** | Whether to sort in descending order |
| **group_by** | Grouping criterion (column, level, rule_type) |
| **max_results** | Maximum number of results |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/quality/formats` | GET | Retrieve available formats and options |
| `/quality/sources/{id}/score` | POST | Calculate quality scores |
| `/quality/sources/{id}/report` | POST | Generate a report |
| `/quality/sources/{id}/report/download` | GET | Download a report |
| `/quality/sources/{id}/report/preview` | GET | Preview a report |
| `/quality/sources/{id}/summary` | GET | Retrieve quality summary |
| `/quality/compare` | POST | Compare scores across sources |
| `/quality/filter` | POST | Filter scores |

### Request Examples

#### Quality Score Calculation

```json
POST /api/v1/quality/sources/{source_id}/score
{
  "sample_size": 10000,
  "rule_names": ["not_null_email", "unique_id"],
  "thresholds": {
    "excellent": 0.95,
    "good": 0.8,
    "acceptable": 0.6,
    "poor": 0.4
  }
}
```

#### Report Generation

```json
POST /api/v1/quality/sources/{source_id}/report
{
  "format": "html",
  "config": {
    "title": "Data Quality Report",
    "include_metrics": true,
    "include_statistics": true,
    "include_charts": true,
    "theme": "professional",
    "sort_order": "f1_desc",
    "max_scores": 50
  }
}
```

#### Score Filtering

```json
POST /api/v1/quality/filter?source_id={source_id}
{
  "min_level": "good",
  "min_f1": 0.7,
  "should_use_only": true,
  "include_columns": ["email", "phone"]
}
```

## Recommended Operational Guidelines

### Recommended Actions by Quality Level

| Quality Level | Recommended Action |
|---------------|--------------------|
| **Excellent** | Suitable for deployment to production environments |
| **Good** | Appropriate for most environments; ongoing monitoring is recommended |
| **Acceptable** | Suitable for development and testing environments; an improvement plan should be established |
| **Poor** | Rule logic requires thorough review |
| **Unacceptable** | Immediate remediation or deactivation is required |

### Recommended Report Formats by Audience

| Audience | Recommended Format |
|----------|--------------------|
| **Executive leadership** | HTML (with summary included) |
| **Data engineers** | JSON (for automation purposes) |
| **QA teams** | Markdown |
| **CI/CD systems** | JUnit XML |

### Sample Size Guidelines

| Dataset Size | Recommended Sample Size | Remarks |
|--------------|-------------------------|---------|
| < 10,000 rows | Entire dataset | Sampling is unnecessary |
| 10,000 -- 100,000 rows | 10,000 | Default value is appropriate |
| 100,000 -- 1M rows | 50,000 | Ensures statistical significance |
| > 1M rows | 100,000+ | Required to ensure representativeness |

## Troubleshooting

| Issue | Cause | Resolution |
|-------|-------|------------|
| No scores are returned | No validation results available | Execute validation prior to scoring |
| F1 Score is low | Rule is overly strict or overly permissive | Adjust rule threshold parameters |
| Report generation fails | Invalid format specification | Verify the format parameter |
| Report is empty | No scores match the filter criteria | Relax the filter conditions |

## Known Limitations

The following features are not supported in the current version:

| Feature | Status | Remarks |
|---------|--------|---------|
| Cross-validation fold configuration | Not supported | Uses the default truthound scorer |
| Chart type customization | Not supported | Only default HTML charts are provided |
| Display mode configuration | Not supported | Only the default mode is available |
| Confidence interval display | Not supported | Only metric values are displayed |
| Trend analysis | Not supported | Only point-in-time snapshots are provided |

Support for these features may be extended in future updates to the truthound library.
