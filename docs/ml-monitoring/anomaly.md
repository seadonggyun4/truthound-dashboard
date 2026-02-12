# Anomaly Detection

The Anomaly Detection module implements machine learning-based identification of unusual patterns and outliers within data sources, supporting multiple detection algorithms and batch processing capabilities.

## Overview

Anomaly detection is concerned with the identification of data points, records, or patterns that deviate significantly from expected behavior. This module implements multiple ML algorithms to detect various types of anomalies, thereby enabling practitioners to select the most appropriate method for their data characteristics.

> **Technical Note**: The dashboard employs `truthound.datasources.get_datasource()` to load data from various source types (files, databases, etc.) for anomaly detection.

## Anomaly Detection Interface

### Statistical Summary Dashboard

The interface presents aggregate anomaly metrics as follows:

| Metric | Description |
|--------|-------------|
| **Total Sources** | Count of data sources available for analysis |
| **Sources with Anomalies** | Count of sources where anomalies have been detected |
| **Anomaly Count** | Total number of anomalous records identified |
| **Anomaly Rate** | Percentage of records classified as anomalous |

## Single Source Detection Tab

### Executing Anomaly Detection

The following procedure is employed to initiate detection on a single data source:

1. A data source is selected from the dropdown
2. A detection algorithm is chosen
3. Algorithm-specific parameters are configured
4. The sensitivity level is set
5. **Run Detection** is invoked
6. Results are reviewed with the accompanying visualization

### Detection Algorithm Taxonomy

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

The sensitivity level governs the detection threshold and is specified as follows:

| Level | Description | Effect |
|-------|-------------|--------|
| **Low** | Conservative detection | Fewer anomalies are identified, with higher confidence |
| **Medium** | Balanced detection | Standard threshold is applied |
| **High** | Aggressive detection | More anomalies are identified, with lower confidence |

### Detection Results

Upon completion of the detection process, results are presented as described below.

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
| **Record ID** | Identifier of the anomalous record |
| **Anomaly Score** | Quantitative anomaly measure |
| **Contributing Columns** | Columns driving the anomaly classification |
| **Visualization** | Graphical representation of the anomaly |

## Streaming Tab

### Real-Time Anomaly Detection

The Streaming tab facilitates real-time anomaly detection for continuous data streams. In contrast to batch detection, which operates on static datasets, streaming detection applies online learning algorithms to data points as they arrive, thereby enabling immediate identification of anomalous observations.

#### Operational Workflow

The following procedure is employed to establish and operate a streaming detection session:

1. A data source is selected to associate with the streaming session
2. A streaming detection algorithm is chosen
3. Window size and detection threshold are configured
4. **Start Streaming** is invoked to create and activate a session
5. Data points are pushed via the API, WebSocket, or the dashboard interface
6. Anomalies and alerts are monitored in real time
7. **Stop** is invoked to terminate the session

### Streaming Algorithms

| Algorithm | Description | Characteristics |
|-----------|-------------|-----------------|
| **Z-Score Rolling** | Rolling z-score computation over a sliding window | Low latency, interpretable, suitable for univariate stationary data |
| **Exponential Moving Average (EMA)** | Weighted moving average with exponential decay | Responsive to recent changes, smooths noise |
| **Isolation Forest (Incremental)** | Incremental variant of tree-based isolation | Handles multivariate data, higher computational cost |
| **Half-Space Trees** | Lightweight streaming tree ensemble | Memory-efficient, fast updates |
| **Robust Random Cut Forest (RRCF)** | Robust tree-based streaming detector | Resilient to concept drift, handles high-dimensional data |

### Stream Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Window Size** | Number of records retained in the sliding window buffer | 100 |
| **Threshold** | Anomaly score threshold for triggering alerts | 3.0 |
| **Columns** | Specific columns to monitor (empty = all numeric columns) | All |

### Session Lifecycle

Streaming sessions adhere to a defined state machine, whose transitions are enumerated below:

| State | Description | Transitions |
|-------|-------------|-------------|
| **Created** | Session initialized, awaiting start | → Running |
| **Running** | Actively receiving and processing data points | → Paused, Stopped, Error |
| **Paused** | Temporarily suspended, retains internal state | → Running, Stopped |
| **Stopped** | Explicitly terminated by user | → *(terminal)* |
| **Error** | Terminated due to an internal error | → *(terminal)* |

### Session Lifecycle Management and Automatic Cleanup

Streaming sessions are maintained in server memory for the duration of their use. Since sessions are ephemeral and are not persisted to the database, a TTL (Time-To-Live) based automatic cleanup mechanism is employed to prevent orphaned sessions from accumulating and consuming memory indefinitely.

#### Cleanup Policy Architecture

The cleanup system employs a **strategy pattern**, whereby cleanup behavior is defined, composed, and extended independently of the detection logic.

| Policy | Description |
|--------|-------------|
| **IdleTTLPolicy** | Removes sessions that have been idle (no data pushed, no API interaction) beyond a configurable TTL. Per-status TTL configuration is supported. |
| **CompositeCleanupPolicy** | Combines multiple policies using AND or OR logic, thereby enabling the construction of complex cleanup rules. |

#### Per-Status TTL Defaults

Different session states are assigned different idle tolerances, reflecting their expected usage patterns:

| Session Status | Default TTL | Rationale |
|----------------|-------------|-----------|
| **Stopped** | 5 minutes | Terminal state; retained briefly for final result retrieval |
| **Error** | 10 minutes | Terminal state; longer retention for diagnostic inspection |
| **Created** | 15 minutes | Session was created but never started; likely abandoned |
| **Paused** | 30 minutes | May be resumed; moderate retention period |
| **Running** | 60 minutes | Active session; longest retention to tolerate temporary inactivity |

#### Activity Tracking

Each session maintains a `last_active_at` timestamp that is updated whenever the session receives data (`push_data_point`, `push_batch`) or transitions state (`start_session`). The cleanup policy evaluates the elapsed time since this timestamp to determine whether expiration has occurred.

#### Background Cleanup Process

A background asyncio task is executed at a configurable interval (default: 60 seconds), iterating over all sessions and removing those that satisfy the active cleanup policy. The cleanup process is integrated into the application lifecycle as follows:

- **Startup**: The cleanup task is initiated automatically when the server starts.
- **Shutdown**: The cleanup task is gracefully cancelled during server shutdown.

#### Extending Cleanup Policies

Custom cleanup policies may be implemented by extending the `SessionCleanupPolicy` interface. Illustrative examples include:

- **MaxSessionsPolicy**: Enforces a maximum number of concurrent sessions by evicting the least recently active sessions.
- **MaxBufferSizePolicy**: Evicts sessions whose internal buffer exceeds a specified memory threshold.

Multiple policies may be combined using `CompositeCleanupPolicy` with either AND (all policies must agree) or OR (any single policy is sufficient) semantics.

### WebSocket Real-Time Interface

For low-latency streaming, a WebSocket endpoint is made available on a per-session basis:

| Message Type (Client → Server) | Payload | Description |
|-------------------------------|---------|-------------|
| `data` | `{"type": "data", "data": {...}, "timestamp": "..."}` | Push a data point for detection |
| `ping` | `{"type": "ping"}` | Keep-alive heartbeat |

| Message Type (Server → Client) | Payload | Description |
|-------------------------------|---------|-------------|
| `alert` | `{"type": "alert", "alert": {...}}` | Anomaly alert notification |
| `ack` | `{"type": "ack", "has_alert": bool}` | Acknowledgement with alert status |
| `pong` | `{"type": "pong"}` | Heartbeat response |

## Batch Detection Tab

### Multi-Source Batch Processing Framework

Anomaly detection may be executed across multiple sources simultaneously through the following procedure:

1. **Run Batch Detection** is invoked
2. Target sources are selected
3. A detection algorithm is chosen
4. Common parameters are configured
5. The batch job is submitted
6. Progress is monitored

### Batch Configuration

| Parameter | Description |
|-----------|-------------|
| **Sources** | List of data sources to be processed |
| **Algorithm** | Detection algorithm to be applied |
| **Parameters** | Algorithm-specific configuration |
| **Parallel Jobs** | Number of concurrent executions |

### Batch Progress

The progress of a batch job may be monitored through the following attributes:

| Attribute | Description |
|-----------|-------------|
| **Job ID** | Unique batch job identifier |
| **Status** | Current execution status |
| **Progress** | Percentage completion |
| **Completed Sources** | Sources that have finished processing |
| **Errors** | Any sources that failed processing |

### Batch Results

Completed batch results are presented with the following attributes:

| Attribute | Description |
|-----------|-------------|
| **Source** | Data source name |
| **Anomalies** | Count of anomalies detected |
| **Anomaly Rate** | Percentage of anomalous records |
| **Status** | Success or failure |
| **Duration** | Processing time |

## Batch History

### Historical Batch Job Records

All batch job executions are recorded and may be reviewed through the following interface:

| Column | Description |
|--------|-------------|
| **Job ID** | Unique identifier |
| **Timestamp** | Execution start time |
| **Sources** | Number of sources processed |
| **Status** | Final job status |
| **Total Anomalies** | Aggregate anomaly count |

### Viewing Batch Results

To inspect the detailed results of a completed batch job, the following procedure is followed:

1. Navigate to the **History** tab within the Anomaly Detection page
2. Click on a batch job entry in the list
3. The interface automatically transitions to the **Batch** tab and displays the `BatchResults` component, which presents:
   - Per-source anomaly counts and rates
   - Sortable results table
   - High anomaly rate warnings
   - Navigation links to individual source detection details

Clicking **View Details** on a specific source result transitions to the **Single** tab, with the corresponding source pre-selected for in-depth analysis.

> **Note**: Batch results are state-driven and do not support direct URL access (deep linking). Navigation must be performed through the History tab interaction.

## Algorithm Comparison

### Comparative Detection Algorithm Taxonomy

Multiple algorithms may be compared on the same dataset through the following procedure:

1. **Compare Algorithms** is invoked
2. A data source is selected
3. Algorithms to be compared are chosen
4. The comparison is executed
5. Comparative results are reviewed

### Comparison Results Interface Specifications

| Metric | Description |
|--------|-------------|
| **Algorithm** | Detection method name |
| **Anomalies Detected** | Count per algorithm |
| **Detection Time** | Execution duration |
| **Precision** | Accuracy if ground truth is available |
| **Agreement** | Overlap with other algorithms |

## Related Alerts

### Alert Correlation

Drift alerts that may correlate with anomaly detections are presented, including:

- Drift alerts from the same time period
- Drift in columns where anomalies were detected
- Cross-source correlation patterns

## Auto-Trigger Configuration

### Automated Response Actions

Automated responses to anomaly detection may be configured as follows:

| Trigger | Description |
|---------|-------------|
| **Alert Generation** | An alert is created when anomalies exceed the specified threshold |
| **Notification** | Notifications are sent to configured channels |
| **Validation Trigger** | Validation is executed on the affected source |
| **Report Generation** | An anomaly report is generated |

## Algorithm Selection Guide

### Recommended Operational Practices

| Scenario | Recommended Algorithm |
|----------|----------------------|
| Unknown data distribution | Isolation Forest |
| Local density variations | LOF |
| Well-defined normal class | One-Class SVM |
| Spatial/clustered data | DBSCAN |
| Simple univariate data | Statistical |
| Complex temporal patterns | Autoencoder |

### Analytical Application Scenarios

| Data Characteristic | Implication |
|--------------------|-------------|
| High dimensionality | Isolation Forest is observed to perform well |
| Sparse data | DBSCAN may exhibit degraded performance |
| Time series | Autoencoder or Statistical methods are recommended |
| Categorical heavy | Statistical methods are preferred |

## Technical Notes

### Data Loading

The dashboard employs `truthound.datasources.get_datasource()` to load data from various source types (CSV, Parquet, JSON, databases, etc.) for anomaly detection. This mechanism provides a unified interface for accessing data regardless of the underlying storage format.

### Truthound Integration

The anomaly detection algorithms implemented in the dashboard are built upon truthound's ML module (`truthound.ml.anomaly_models`):

| Algorithm | Truthound Implementation |
|-----------|--------------------------|
| Statistical | `truthound.ml.anomaly_models.statistical.StatisticalAnomalyDetector` |
| Isolation Forest | `truthound.ml.anomaly_models.isolation_forest.IsolationForestDetector` |
| Ensemble | `truthound.ml.anomaly_models.ensemble.EnsembleAnomalyDetector` |

#### Statistical Anomaly Detector

The `StatisticalAnomalyDetector` provides configurable methods for the detection of point anomalies:

| Method | Description | Configuration |
|--------|-------------|---------------|
| zscore | Standard deviation-based detection | `n_std`: threshold in standard deviations |
| iqr | Interquartile range-based detection | `iqr_factor`: multiplier for IQR bounds |
| mad | Median absolute deviation detection | `mad_factor`: multiplier for MAD |

#### Isolation Forest Detector

The `IsolationForestDetector` implements the isolation forest algorithm, optimized for high-dimensional data:

| Parameter | Description | Default |
|-----------|-------------|---------|
| n_estimators | Number of isolation trees | 100 |
| max_samples | Samples per tree | "auto" |
| contamination | Expected anomaly proportion | "auto" |
| columns | Target columns for detection | All numeric |

#### Ensemble Anomaly Detector

The `EnsembleAnomalyDetector` combines multiple detection methods with configurable voting strategies:

| Voting Mode | Description |
|-------------|-------------|
| majority | An anomaly is flagged if a majority of detectors agree |
| unanimous | An anomaly is flagged only if all detectors agree |
| any | An anomaly is flagged if any detector identifies it |
| weighted | A weighted combination of detector scores is computed |

### Anomaly Type Classification

Truthound classifies anomalies into the following taxonomic categories:

| Type | Description |
|------|-------------|
| POINT | Single point anomaly — an individual outlier |
| CONTEXTUAL | Contextual anomaly — a value that is normal in isolation but anomalous in its temporal or spatial context |
| COLLECTIVE | A group of related anomalies exhibiting collective behavior |
| PATTERN | Pattern violation — a sequence that deviates from a learned pattern |
| TREND | Trend deviation — an unexpected directional change |
| SEASONAL | Seasonal violation — deviation from expected periodicity |

### Performance Characteristics

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Statistical fit | O(n) | Single pass through data |
| Statistical score | O(m) | m = number of test rows |
| Isolation Forest fit | O(n log n × k) | k = number of trees |
| Isolation Forest score | O(m × k × d) | d = tree depth |

### Thread Safety

All anomaly detection models employ `threading.RLock()` for concurrent access, thereby enabling safe utilization in multi-threaded environments such as the dashboard's async API handlers.

## API Reference

### Detection Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{source_id}/anomaly/detect` | POST | Execute anomaly detection on a source |
| `/sources/{source_id}/anomaly/detections` | GET | Retrieve detection history for a source |
| `/sources/{source_id}/anomaly/latest` | GET | Retrieve the latest detection result |
| `/anomaly/detection/{detection_id}` | GET | Retrieve a specific detection result |

### Batch Detection Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anomaly/batch` | POST | Create a batch detection job |
| `/anomaly/batch` | GET | List all batch jobs |
| `/anomaly/batch/{batch_id}` | GET | Retrieve batch job details |
| `/anomaly/batch/{batch_id}/results` | GET | Retrieve detailed results for each source |
| `/anomaly/batch/{batch_id}/cancel` | POST | Cancel a running batch job |
| `/anomaly/batch/{batch_id}` | DELETE | Delete a batch job |

### Algorithm Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anomaly/algorithms` | GET | List available algorithms |
| `/anomaly/compare` | POST | Execute algorithm comparison (query param: source_id) |

### Explainability Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anomaly/detection/{detection_id}/explain` | POST | Generate SHAP/LIME explanations |
| `/anomaly/detection/{detection_id}/explanations` | GET | Retrieve cached explanations |

### Streaming Detection Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anomaly/streaming/start` | POST | Initiate a streaming detection session |
| `/anomaly/streaming/sessions` | GET | List all streaming sessions |
| `/anomaly/streaming/algorithms` | GET | List available streaming algorithms |
| `/anomaly/streaming/{session_id}/data` | POST | Push a data point for detection |
| `/anomaly/streaming/{session_id}/batch` | POST | Push a batch of data points |
| `/anomaly/streaming/{session_id}/status` | GET | Retrieve session status and statistics |
| `/anomaly/streaming/{session_id}/alerts` | GET | List session alerts |
| `/anomaly/streaming/{session_id}/data` | GET | Retrieve recent data points |
| `/anomaly/streaming/{session_id}/stop` | POST | Stop a streaming session |
| `/anomaly/streaming/{session_id}` | DELETE | Delete a streaming session |
| `/anomaly/streaming/{session_id}/ws` | WebSocket | Real-time streaming connection |
