# Anomaly Detection

The Anomaly Detection module provides machine learning-based identification of unusual patterns and outliers within data sources, supporting multiple detection algorithms and batch processing capabilities.

## Overview

Anomaly detection identifies data points, records, or patterns that deviate significantly from expected behavior. This module implements multiple ML algorithms to detect various types of anomalies, enabling users to select the most appropriate method for their data characteristics.

> **Technical Note**: The dashboard uses `truthound.datasources.get_datasource()` to load data from various source types (files, databases, etc.) for anomaly detection.

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

The Streaming tab provides real-time anomaly detection for continuous data streams. Unlike batch detection, which operates on static datasets, streaming detection applies online learning algorithms to data points as they arrive, enabling immediate identification of anomalous observations.

#### Operational Workflow

1. Select a data source to associate with the streaming session
2. Choose a streaming detection algorithm
3. Configure window size and detection threshold
4. Click **Start Streaming** to create and activate a session
5. Push data points via the API, WebSocket, or the dashboard interface
6. Monitor anomalies and alerts in real time
7. Click **Stop** to terminate the session

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

Streaming sessions follow a defined state machine:

| State | Description | Transitions |
|-------|-------------|-------------|
| **Created** | Session initialized, awaiting start | → Running |
| **Running** | Actively receiving and processing data points | → Paused, Stopped, Error |
| **Paused** | Temporarily suspended, retains internal state | → Running, Stopped |
| **Stopped** | Explicitly terminated by user | → *(terminal)* |
| **Error** | Terminated due to an internal error | → *(terminal)* |

### Session Lifecycle Management and Automatic Cleanup

Streaming sessions are maintained in server memory for the duration of their use. Since sessions are ephemeral and not persisted to the database, a TTL (Time-To-Live) based automatic cleanup mechanism prevents orphaned sessions from accumulating and consuming memory indefinitely.

#### Cleanup Policy Architecture

The cleanup system employs a **strategy pattern**, allowing the cleanup behavior to be defined, composed, and extended independently of the detection logic.

| Policy | Description |
|--------|-------------|
| **IdleTTLPolicy** | Removes sessions that have been idle (no data pushed, no API interaction) beyond a configurable TTL. Supports per-status TTL configuration. |
| **CompositeCleanupPolicy** | Combines multiple policies using AND or OR logic, enabling complex cleanup rules. |

#### Per-Status TTL Defaults

Different session states have different idle tolerances, reflecting their expected usage patterns:

| Session Status | Default TTL | Rationale |
|----------------|-------------|-----------|
| **Stopped** | 5 minutes | Terminal state; retained briefly for final result retrieval |
| **Error** | 10 minutes | Terminal state; longer retention for diagnostic inspection |
| **Created** | 15 minutes | Session was created but never started; likely abandoned |
| **Paused** | 30 minutes | May be resumed; moderate retention period |
| **Running** | 60 minutes | Active session; longest retention to tolerate temporary inactivity |

#### Activity Tracking

Each session maintains a `last_active_at` timestamp that is updated whenever the session receives data (`push_data_point`, `push_batch`) or transitions state (`start_session`). The cleanup policy evaluates the elapsed time since this timestamp to determine expiration.

#### Background Cleanup Process

A background asyncio task runs at a configurable interval (default: 60 seconds), iterating over all sessions and removing those that satisfy the active cleanup policy. The cleanup process is integrated into the application lifecycle:

- **Startup**: The cleanup task is started automatically when the server starts.
- **Shutdown**: The cleanup task is gracefully cancelled during server shutdown.

#### Extending Cleanup Policies

Custom cleanup policies can be implemented by extending the `SessionCleanupPolicy` interface. For example:

- **MaxSessionsPolicy**: Enforce a maximum number of concurrent sessions by evicting the least recently active sessions.
- **MaxBufferSizePolicy**: Evict sessions whose internal buffer exceeds a memory threshold.

Multiple policies can be combined using `CompositeCleanupPolicy` with either AND (all policies must agree) or OR (any policy is sufficient) semantics.

### WebSocket Real-Time Interface

For low-latency streaming, a WebSocket endpoint is available per session:

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

### Viewing Batch Results

To inspect the detailed results of a completed batch job:

1. Navigate to the **History** tab within the Anomaly Detection page
2. Click on a batch job entry in the list
3. The interface automatically transitions to the **Batch** tab and displays the `BatchResults` component, which presents:
   - Per-source anomaly counts and rates
   - Sortable results table
   - High anomaly rate warnings
   - Navigation links to individual source detection details

Clicking **View Details** on a specific source result transitions to the **Single** tab, pre-selecting the corresponding source for in-depth analysis.

> **Note**: Batch results are state-driven and do not support direct URL access (deep linking). Navigation must occur through the History tab interaction.

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

## Technical Notes

### Data Loading

The dashboard uses `truthound.datasources.get_datasource()` to load data from various source types (CSV, Parquet, JSON, databases, etc.) for anomaly detection. This provides a unified interface for accessing data regardless of the underlying storage format.

### Truthound Integration

The anomaly detection algorithms in the dashboard leverage truthound's ML module (`truthound.ml.anomaly_models`):

| Algorithm | Truthound Implementation |
|-----------|--------------------------|
| Statistical | `truthound.ml.anomaly_models.statistical.StatisticalAnomalyDetector` |
| Isolation Forest | `truthound.ml.anomaly_models.isolation_forest.IsolationForestDetector` |
| Ensemble | `truthound.ml.anomaly_models.ensemble.EnsembleAnomalyDetector` |

#### Statistical Anomaly Detector

The `StatisticalAnomalyDetector` provides configurable methods for detecting point anomalies:

| Method | Description | Configuration |
|--------|-------------|---------------|
| zscore | Standard deviation-based detection | `n_std`: threshold in standard deviations |
| iqr | Interquartile range-based detection | `iqr_factor`: multiplier for IQR bounds |
| mad | Median absolute deviation detection | `mad_factor`: multiplier for MAD |

#### Isolation Forest Detector

The `IsolationForestDetector` implements the isolation forest algorithm optimized for high-dimensional data:

| Parameter | Description | Default |
|-----------|-------------|---------|
| n_estimators | Number of isolation trees | 100 |
| max_samples | Samples per tree | "auto" |
| contamination | Expected anomaly proportion | "auto" |
| columns | Target columns for detection | All numeric |

#### Ensemble Anomaly Detector

The `EnsembleAnomalyDetector` combines multiple detection methods with configurable voting:

| Voting Mode | Description |
|-------------|-------------|
| majority | Anomaly if majority of detectors agree |
| unanimous | Anomaly only if all detectors agree |
| any | Anomaly if any detector flags it |
| weighted | Weighted combination of detector scores |

### Anomaly Types

Truthound classifies anomalies into the following types:

| Type | Description |
|------|-------------|
| POINT | Single point anomaly - individual outlier |
| CONTEXTUAL | Anomaly in context - normal value at wrong time/place |
| COLLECTIVE | Group of related anomalies |
| PATTERN | Pattern violation - sequence deviates from learned pattern |
| TREND | Trend deviation - unexpected direction change |
| SEASONAL | Seasonal violation - deviates from expected periodicity |

### Performance Characteristics

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Statistical fit | O(n) | Single pass through data |
| Statistical score | O(m) | m = number of test rows |
| Isolation Forest fit | O(n log n × k) | k = number of trees |
| Isolation Forest score | O(m × k × d) | d = tree depth |

### Thread Safety

All anomaly detection models use `threading.RLock()` for concurrent access, enabling safe use in multi-threaded environments like the dashboard's async API handlers.

## API Reference

### Detection Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{source_id}/anomaly/detect` | POST | Execute anomaly detection on a source |
| `/sources/{source_id}/anomaly/detections` | GET | Retrieve detection history for a source |
| `/sources/{source_id}/anomaly/latest` | GET | Get the latest detection result |
| `/anomaly/detection/{detection_id}` | GET | Get a specific detection result |

### Batch Detection Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anomaly/batch` | POST | Create batch detection job |
| `/anomaly/batch` | GET | List all batch jobs |
| `/anomaly/batch/{batch_id}` | GET | Retrieve batch job details |
| `/anomaly/batch/{batch_id}/results` | GET | Get detailed results for each source |
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
| `/anomaly/detection/{detection_id}/explanations` | GET | Get cached explanations |

### Streaming Detection Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anomaly/streaming/start` | POST | Start a streaming detection session |
| `/anomaly/streaming/sessions` | GET | List all streaming sessions |
| `/anomaly/streaming/algorithms` | GET | List available streaming algorithms |
| `/anomaly/streaming/{session_id}/data` | POST | Push data point for detection |
| `/anomaly/streaming/{session_id}/batch` | POST | Push batch of data points |
| `/anomaly/streaming/{session_id}/status` | GET | Get session status and statistics |
| `/anomaly/streaming/{session_id}/alerts` | GET | List session alerts |
| `/anomaly/streaming/{session_id}/data` | GET | Get recent data points |
| `/anomaly/streaming/{session_id}/stop` | POST | Stop a streaming session |
| `/anomaly/streaming/{session_id}` | DELETE | Delete a streaming session |
| `/anomaly/streaming/{session_id}/ws` | WebSocket | Real-time streaming connection |
