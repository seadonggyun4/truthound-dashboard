# Anomaly Detection

The Anomaly Detection module provides machine learning-based identification of unusual patterns and outliers within data sources, supporting multiple detection algorithms and batch processing capabilities.

## Overview

Anomaly detection identifies data points, records, or patterns that deviate significantly from expected behavior. This module implements multiple ML algorithms to detect various types of anomalies, enabling users to select the most appropriate method for their data characteristics.

## Anomaly Detection Interface

### Statistics Dashboard

The interface displays aggregate anomaly metrics:

| Metric | Description |
|--------|-------------|
| **Total Sources** | Count of data sources available for analysis |
| **Sources with Anomalies** | Count of sources where anomalies have been detected |
| **Anomaly Count** | Total number of anomalous records identified |
| **Anomaly Rate** | Percentage of records classified as anomalous |

## Single Source Detection Tab

### Executing Anomaly Detection

1. Select a data source from the dropdown
2. Choose a detection algorithm
3. Configure algorithm-specific parameters
4. Set sensitivity level
5. Click **Run Detection**
6. Review results with visualization

### Detection Algorithms

| Algorithm | Description | Best For |
|-----------|-------------|----------|
| **Isolation Forest** | Tree-based isolation of anomalies | High-dimensional data, mixed types |
| **LOF (Local Outlier Factor)** | Density-based local outlier detection | Clustered data, local anomalies |
| **One-Class SVM** | Support vector machine for novelty detection | Well-defined normal class |
| **DBSCAN** | Density-based spatial clustering | Spatial data, arbitrary cluster shapes |
| **Statistical** | Z-score and IQR-based detection | Normally distributed data |
| **Autoencoder** | Neural network reconstruction error | Complex patterns, temporal data |

### Algorithm Parameters

#### Isolation Forest

| Parameter | Description | Default |
|-----------|-------------|---------|
| **n_estimators** | Number of isolation trees | 100 |
| **contamination** | Expected proportion of outliers | auto |
| **max_samples** | Samples for building each tree | auto |

#### Local Outlier Factor (LOF)

| Parameter | Description | Default |
|-----------|-------------|---------|
| **n_neighbors** | Number of neighbors for density estimation | 20 |
| **contamination** | Expected proportion of outliers | auto |
| **algorithm** | Nearest neighbor algorithm | auto |

#### One-Class SVM

| Parameter | Description | Default |
|-----------|-------------|---------|
| **kernel** | Kernel function (rbf, linear, poly) | rbf |
| **nu** | Upper bound on fraction of outliers | 0.1 |
| **gamma** | Kernel coefficient | scale |

#### DBSCAN

| Parameter | Description | Default |
|-----------|-------------|---------|
| **eps** | Maximum distance between samples | 0.5 |
| **min_samples** | Minimum samples in neighborhood | 5 |

#### Statistical

| Parameter | Description | Default |
|-----------|-------------|---------|
| **method** | Detection method (zscore, iqr, mad) | zscore |
| **threshold** | Number of standard deviations | 3.0 |

#### Autoencoder

| Parameter | Description | Default |
|-----------|-------------|---------|
| **encoding_dim** | Latent space dimension | 8 |
| **epochs** | Training epochs | 50 |
| **threshold_percentile** | Reconstruction error threshold | 95 |

### Sensitivity Configuration

Sensitivity level affects detection threshold:

| Level | Description | Effect |
|-------|-------------|--------|
| **Low** | Conservative detection | Fewer anomalies, higher confidence |
| **Medium** | Balanced detection | Standard threshold |
| **High** | Aggressive detection | More anomalies, lower confidence |

### Detection Results

Upon completion, results display:

#### Summary Statistics

| Metric | Description |
|--------|-------------|
| **Total Records** | Number of records analyzed |
| **Anomalies Detected** | Count of anomalous records |
| **Anomaly Rate** | Percentage of anomalous records |
| **Algorithm Used** | Detection algorithm applied |

#### Anomaly Details

| Attribute | Description |
|-----------|-------------|
| **Record ID** | Identifier of anomalous record |
| **Anomaly Score** | Quantitative anomaly measure |
| **Contributing Columns** | Columns driving the anomaly classification |
| **Visualization** | Graphical representation of anomaly |

## Streaming Tab

### Real-Time Anomaly Detection

The Streaming tab provides real-time anomaly detection for data streams:

1. Configure stream source connection
2. Set detection parameters
3. Enable streaming detection
4. Monitor anomalies as they occur

### Stream Configuration

| Parameter | Description |
|-----------|-------------|
| **Window Size** | Number of records in sliding window |
| **Update Interval** | Frequency of model updates |
| **Alert Threshold** | Anomaly score threshold for alerts |

## Batch Detection Tab

### Multi-Source Batch Processing

Execute anomaly detection across multiple sources simultaneously:

1. Click **Run Batch Detection**
2. Select target sources
3. Choose detection algorithm
4. Configure common parameters
5. Submit batch job
6. Monitor progress

### Batch Configuration

| Parameter | Description |
|-----------|-------------|
| **Sources** | List of data sources to process |
| **Algorithm** | Detection algorithm to apply |
| **Parameters** | Algorithm-specific configuration |
| **Parallel Jobs** | Number of concurrent executions |

### Batch Progress

Monitor batch job progress:

| Attribute | Description |
|-----------|-------------|
| **Job ID** | Unique batch job identifier |
| **Status** | Current execution status |
| **Progress** | Percentage completion |
| **Completed Sources** | Sources that have finished processing |
| **Errors** | Any sources that failed processing |

### Batch Results

View completed batch results:

| Attribute | Description |
|-----------|-------------|
| **Source** | Data source name |
| **Anomalies** | Count of anomalies detected |
| **Anomaly Rate** | Percentage of anomalous records |
| **Status** | Success or failure |
| **Duration** | Processing time |

## Batch History

### Historical Batch Jobs

View all batch job executions:

| Column | Description |
|--------|-------------|
| **Job ID** | Unique identifier |
| **Timestamp** | Execution start time |
| **Sources** | Number of sources processed |
| **Status** | Final job status |
| **Total Anomalies** | Aggregate anomaly count |

## Algorithm Comparison

### Comparing Detection Methods

Compare multiple algorithms on the same dataset:

1. Click **Compare Algorithms**
2. Select data source
3. Choose algorithms to compare
4. Execute comparison
5. Review comparative results

### Comparison Results

| Metric | Description |
|--------|-------------|
| **Algorithm** | Detection method name |
| **Anomalies Detected** | Count per algorithm |
| **Detection Time** | Execution duration |
| **Precision** | Accuracy if ground truth available |
| **Agreement** | Overlap with other algorithms |

## Related Alerts

### Alert Correlation

View drift alerts that may correlate with anomaly detections:

- Drift alerts from the same time period
- Drift in columns where anomalies were detected
- Cross-source correlation patterns

## Auto-Trigger Configuration

### Automated Actions

Configure automated responses to anomaly detection:

| Trigger | Description |
|---------|-------------|
| **Alert Generation** | Create alert when anomalies exceed threshold |
| **Notification** | Send notifications to configured channels |
| **Validation Trigger** | Execute validation on affected source |
| **Report Generation** | Generate anomaly report |

## Algorithm Selection Guide

### Choosing the Right Algorithm

| Scenario | Recommended Algorithm |
|----------|----------------------|
| Unknown data distribution | Isolation Forest |
| Local density variations | LOF |
| Well-defined normal class | One-Class SVM |
| Spatial/clustered data | DBSCAN |
| Simple univariate data | Statistical |
| Complex temporal patterns | Autoencoder |

### Data Considerations

| Data Characteristic | Implication |
|--------------------|-------------|
| High dimensionality | Isolation Forest performs well |
| Sparse data | DBSCAN may struggle |
| Time series | Autoencoder or Statistical |
| Categorical heavy | Statistical methods preferred |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/anomaly-detect` | POST | Execute anomaly detection |
| `/sources/{id}/anomaly-detections` | GET | Retrieve detection history |
| `/anomaly/batch-jobs` | POST | Create batch detection job |
| `/anomaly/batch-jobs` | GET | List batch jobs |
| `/anomaly/batch-jobs/{id}` | GET | Retrieve batch job details |
| `/anomaly/batch-jobs/{id}/progress` | GET | Retrieve batch progress |
| `/anomaly/algorithms/compare` | POST | Execute algorithm comparison |
