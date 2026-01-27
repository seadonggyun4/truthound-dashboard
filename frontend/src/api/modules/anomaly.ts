/**
 * Anomaly API - ML-based anomaly detection.
 */
import { request } from '../core'
import type { PaginatedResponse } from '../core'

// ============================================================================
// Types
// ============================================================================

export type AnomalyAlgorithm =
  | 'isolation_forest'
  | 'lof'
  | 'one_class_svm'
  | 'dbscan'
  | 'statistical'
  | 'autoencoder'

export type AnomalyStatus = 'pending' | 'running' | 'success' | 'error'
export type AlgorithmCategory = 'tree' | 'density' | 'svm' | 'clustering' | 'statistical' | 'neural'

export const ANOMALY_ALGORITHMS: {
  value: AnomalyAlgorithm
  label: string
  description: string
  category: AlgorithmCategory
}[] = [
  {
    value: 'isolation_forest',
    label: 'Isolation Forest',
    description: 'Tree-based algorithm that isolates anomalies by random partitioning',
    category: 'tree',
  },
  {
    value: 'lof',
    label: 'Local Outlier Factor',
    description: 'Density-based algorithm comparing local density with neighbors',
    category: 'density',
  },
  {
    value: 'one_class_svm',
    label: 'One-Class SVM',
    description: 'SVM trained on normal data to create a decision boundary',
    category: 'svm',
  },
  {
    value: 'dbscan',
    label: 'DBSCAN',
    description: 'Density-based clustering that identifies outliers',
    category: 'clustering',
  },
  {
    value: 'statistical',
    label: 'Statistical',
    description: 'Z-score, IQR, or MAD based detection',
    category: 'statistical',
  },
  {
    value: 'autoencoder',
    label: 'Autoencoder',
    description: 'Neural network with high reconstruction error for anomalies',
    category: 'neural',
  },
]

export interface AnomalyRecord {
  row_index: number
  anomaly_score: number
  column_values: Record<string, unknown>
  is_anomaly: boolean
}

export interface ColumnAnomalySummary {
  column: string
  dtype: string
  anomaly_count: number
  anomaly_rate: number
  mean_anomaly_score: number
  min_value: number | null
  max_value: number | null
  top_anomaly_indices: number[]
}

export interface AnomalyDetection {
  id: string
  source_id: string
  status: AnomalyStatus
  algorithm: AnomalyAlgorithm
  config: Record<string, unknown> | null
  total_rows: number | null
  anomaly_count: number | null
  anomaly_rate: number | null
  columns_analyzed: string[] | null
  column_summaries: ColumnAnomalySummary[] | null
  anomalies: AnomalyRecord[] | null
  duration_ms: number | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export type AnomalyDetectionListResponse = PaginatedResponse<AnomalyDetection>

export interface AlgorithmParameter {
  name: string
  label: string
  type: 'integer' | 'float' | 'string' | 'select' | 'boolean'
  default: unknown
  min_value: number | null
  max_value: number | null
  options: string[] | null
  description: string
}

export interface AlgorithmInfo {
  name: AnomalyAlgorithm
  display_name: string
  description: string
  category: AlgorithmCategory
  parameters: AlgorithmParameter[]
  pros: string[]
  cons: string[]
  best_for: string
  requires_scaling: boolean
}

export interface AlgorithmListResponse {
  algorithms: AlgorithmInfo[]
  total: number
}

export interface AnomalyDetectionRequest {
  algorithm?: AnomalyAlgorithm
  columns?: string[]
  config?: Record<string, unknown>
  sample_size?: number
}

export interface AnomalyDetectionConfig {
  algorithm: AnomalyAlgorithm
  columns: string[]
  params?: Record<string, unknown>
  sample_size?: number
}

// Explainability
export interface FeatureContribution {
  feature: string
  value: number
  shap_value: number
  contribution: number
}

export interface AnomalyExplanationResult {
  row_index: number
  anomaly_score: number
  feature_contributions: FeatureContribution[]
  total_shap: number
  summary: string
}

export interface ExplainabilityResponse {
  detection_id: string
  algorithm: string
  row_indices: number[]
  feature_names: string[]
  explanations: AnomalyExplanationResult[]
  generated_at: string
  error?: string | null
}

export interface ExplainabilityRequest {
  row_indices: number[]
  max_features?: number
  sample_background?: number
}

export interface CachedExplanation {
  id: string
  detection_id: string
  row_index: number
  anomaly_score: number
  feature_contributions: FeatureContribution[]
  total_shap: number
  summary: string
  generated_at: string | null
}

export interface CachedExplanationsResponse {
  detection_id: string
  explanations: CachedExplanation[]
  total: number
}

// Batch Detection
export type BatchDetectionStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'partial'
  | 'error'
  | 'cancelled'

export interface BatchSourceResult {
  source_id: string
  source_name: string | null
  detection_id: string | null
  status: string
  anomaly_count: number | null
  anomaly_rate: number | null
  total_rows: number | null
  error_message: string | null
}

export interface BatchDetectionJob {
  id: string
  name: string | null
  status: BatchDetectionStatus
  algorithm: AnomalyAlgorithm
  config: Record<string, unknown> | null
  total_sources: number
  completed_sources: number
  failed_sources: number
  progress_percent: number
  current_source_id: string | null
  total_anomalies: number
  total_rows_analyzed: number
  average_anomaly_rate: number
  results: BatchSourceResult[] | null
  duration_ms: number | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export type BatchDetectionListResponse = PaginatedResponse<BatchDetectionJob>

export interface BatchDetectionRequest {
  source_ids: string[]
  name?: string
  algorithm?: AnomalyAlgorithm
  config?: Record<string, unknown>
  sample_size?: number
}

// Algorithm Comparison
export type AgreementLevel = 'all' | 'majority' | 'some' | 'one'

export interface AlgorithmComparisonRequest {
  algorithms: AnomalyAlgorithm[]
  columns?: string[]
  config?: Record<string, Record<string, unknown>>
  sample_size?: number
}

export interface AlgorithmComparisonResultItem {
  algorithm: AnomalyAlgorithm
  display_name: string
  status: AnomalyStatus
  anomaly_count: number | null
  anomaly_rate: number | null
  duration_ms: number | null
  error_message: string | null
  anomaly_indices: number[]
}

export interface AgreementRecord {
  row_index: number
  detected_by: AnomalyAlgorithm[]
  detection_count: number
  agreement_level: AgreementLevel
  confidence_score: number
  column_values: Record<string, unknown>
}

export interface AgreementSummary {
  total_algorithms: number
  total_unique_anomalies: number
  all_agree_count: number
  majority_agree_count: number
  some_agree_count: number
  one_only_count: number
  agreement_matrix: number[][]
}

export interface AlgorithmComparisonResult {
  id: string
  source_id: string
  status: AnomalyStatus
  total_rows: number | null
  columns_analyzed: string[] | null
  algorithm_results: AlgorithmComparisonResultItem[]
  agreement_summary: AgreementSummary | null
  agreement_records: AgreementRecord[] | null
  total_duration_ms: number | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

// Streaming
export type StreamingAlgorithm =
  | 'zscore_rolling'
  | 'ema'
  | 'isolation_forest_incremental'
  | 'half_space_trees'
  | 'rrcf'

export type StreamingSessionStatus = 'created' | 'running' | 'paused' | 'stopped' | 'error'

export interface StreamingStatistics {
  count: number
  mean: number
  std: number
  min: number | null
  max: number | null
  anomaly_count: number
  anomaly_rate: number
}

export interface StreamingSessionCreate {
  source_id?: string
  algorithm?: StreamingAlgorithm
  window_size?: number
  threshold?: number
  columns?: string[]
  config?: Record<string, unknown>
}

export interface StreamingSession {
  id: string
  source_id: string | null
  algorithm: StreamingAlgorithm
  window_size: number
  threshold: number
  columns: string[]
  status: StreamingSessionStatus
  config: Record<string, unknown> | null
  statistics: Record<string, StreamingStatistics> | null
  total_points: number
  total_anomalies: number
  total_alerts: number
  anomaly_rate: number
  created_at: string
  started_at: string | null
  updated_at: string | null
}

export interface StreamingSessionListResponse {
  data: StreamingSession[]
  total: number
  offset: number
  limit: number
}

export interface StreamingDataPoint {
  timestamp?: string
  values: Record<string, number>
}

export interface StreamingDataBatch {
  data_points: StreamingDataPoint[]
}

export interface StreamingAlert {
  id: string
  session_id: string
  timestamp: string
  column: string
  value: number
  anomaly_score: number
  expected_range: [number, number]
  severity: 'low' | 'medium' | 'high'
  algorithm?: string
  data_point?: StreamingDataPoint
  details?: Record<string, unknown>
}

export interface StreamingAlertListResponse {
  data: StreamingAlert[]
  total: number
  offset: number
  limit: number
}

export interface StreamingStatusResponse {
  session: StreamingSession
  recent_alerts: StreamingAlert[]
  last_data_at: string | null
  points_in_window: number
  total_points: number
  total_alerts: number
  buffer_utilization: number
  statistics: Record<string, StreamingStatistics> | null
}

export interface StreamingRecentDataResponse {
  session_id: string
  data_points: Array<StreamingDataPoint & { is_anomaly: boolean; anomaly_score?: number }>
  total: number
}

export interface StreamingAlgorithmInfo {
  name: StreamingAlgorithm
  display_name: string
  description: string
  parameters: AlgorithmParameter[]
  best_for: string
  supports_online_learning?: boolean
}

export interface StreamingAlgorithmListResponse {
  algorithms: StreamingAlgorithmInfo[]
  total: number
}

// ============================================================================
// API Functions
// ============================================================================

export async function runAnomalyDetection(
  sourceId: string,
  options?: AnomalyDetectionRequest
): Promise<AnomalyDetection> {
  return request<AnomalyDetection>(`/sources/${sourceId}/anomaly/detect`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getAnomalyDetection(detectionId: string): Promise<AnomalyDetection> {
  return request<AnomalyDetection>(`/anomaly/detection/${detectionId}`)
}

export async function listAnomalyDetections(
  sourceId: string,
  params?: { offset?: number; limit?: number }
): Promise<AnomalyDetectionListResponse> {
  return request<AnomalyDetectionListResponse>(`/sources/${sourceId}/anomaly/detections`, {
    params,
  })
}

export async function getLatestAnomalyDetection(sourceId: string): Promise<AnomalyDetection> {
  return request<AnomalyDetection>(`/sources/${sourceId}/anomaly/latest`)
}

export async function listAnomalyAlgorithms(): Promise<AlgorithmListResponse> {
  return request<AlgorithmListResponse>('/anomaly/algorithms')
}

export async function explainAnomaly(
  detectionId: string,
  rowIndices: number[],
  options?: {
    maxFeatures?: number
    sampleBackground?: number
  }
): Promise<ExplainabilityResponse> {
  return request<ExplainabilityResponse>(
    `/anomaly/${detectionId}/explain`,
    {
      method: 'POST',
      body: JSON.stringify({
        row_indices: rowIndices,
        max_features: options?.maxFeatures,
        sample_background: options?.sampleBackground,
      }),
    }
  )
}

export async function getCachedExplanations(
  detectionId: string,
  rowIndices?: number[]
): Promise<CachedExplanationsResponse> {
  const params: Record<string, string> = {}
  if (rowIndices && rowIndices.length > 0) {
    params.row_indices = rowIndices.join(',')
  }
  return request<CachedExplanationsResponse>(
    `/anomaly/${detectionId}/explanations`,
    { params }
  )
}

export async function createBatchDetection(
  batchRequest: BatchDetectionRequest
): Promise<BatchDetectionJob> {
  return request<BatchDetectionJob>('/anomaly/batch', {
    method: 'POST',
    body: JSON.stringify(batchRequest),
  })
}

export async function getBatchDetection(batchId: string): Promise<BatchDetectionJob> {
  return request<BatchDetectionJob>(`/anomaly/batch/${batchId}`)
}

export async function getBatchDetectionResults(batchId: string): Promise<BatchSourceResult[]> {
  return request<BatchSourceResult[]>(`/anomaly/batch/${batchId}/results`)
}

export async function listBatchDetections(params?: {
  offset?: number
  limit?: number
}): Promise<BatchDetectionListResponse> {
  return request<BatchDetectionListResponse>('/anomaly/batch', { params })
}

export async function cancelBatchDetection(batchId: string): Promise<BatchDetectionJob> {
  return request<BatchDetectionJob>(`/anomaly/batch/${batchId}/cancel`, {
    method: 'POST',
  })
}

export async function deleteBatchDetection(batchId: string): Promise<void> {
  await request(`/anomaly/batch/${batchId}`, { method: 'DELETE' })
}

export async function compareAlgorithms(
  sourceId: string,
  comparisonRequest: AlgorithmComparisonRequest
): Promise<AlgorithmComparisonResult> {
  return request<AlgorithmComparisonResult>(`/anomaly/compare?source_id=${sourceId}`, {
    method: 'POST',
    body: JSON.stringify(comparisonRequest),
  })
}

export async function getAlgorithmComparison(comparisonId: string): Promise<AlgorithmComparisonResult> {
  return request<AlgorithmComparisonResult>(`/anomaly/compare/${comparisonId}`)
}

export async function startStreamingSession(
  data: StreamingSessionCreate
): Promise<StreamingSession> {
  return request<StreamingSession>('/anomaly/streaming/sessions', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function pushStreamingData(
  sessionId: string,
  dataPoint: StreamingDataPoint
): Promise<{ is_anomaly: boolean; anomaly_score: number; alerts: StreamingAlert[] }> {
  return request(`/anomaly/streaming/sessions/${sessionId}/data`, {
    method: 'POST',
    body: JSON.stringify(dataPoint),
  })
}

export async function pushStreamingBatch(
  sessionId: string,
  batch: StreamingDataBatch
): Promise<{ anomalies: number; alerts: StreamingAlert[] }> {
  return request(`/anomaly/streaming/sessions/${sessionId}/batch`, {
    method: 'POST',
    body: JSON.stringify(batch),
  })
}

export async function getStreamingStatus(
  sessionId: string
): Promise<StreamingStatusResponse> {
  return request<StreamingStatusResponse>(`/anomaly/streaming/sessions/${sessionId}`)
}

export async function stopStreamingSession(
  sessionId: string
): Promise<StreamingSession> {
  return request<StreamingSession>(`/anomaly/streaming/sessions/${sessionId}/stop`, {
    method: 'POST',
  })
}

export async function deleteStreamingSession(sessionId: string): Promise<void> {
  await request(`/anomaly/streaming/sessions/${sessionId}`, { method: 'DELETE' })
}

export async function listStreamingAlerts(
  sessionId: string,
  params?: { offset?: number; limit?: number }
): Promise<StreamingAlertListResponse> {
  return request<StreamingAlertListResponse>(`/anomaly/streaming/sessions/${sessionId}/alerts`, {
    params,
  })
}

export async function getStreamingRecentData(
  sessionId: string,
  limit = 100
): Promise<StreamingRecentDataResponse> {
  return request<StreamingRecentDataResponse>(`/anomaly/streaming/sessions/${sessionId}/data`, {
    params: { limit },
  })
}

export async function listStreamingSessions(
  params?: { offset?: number; limit?: number }
): Promise<StreamingSessionListResponse> {
  return request<StreamingSessionListResponse>('/anomaly/streaming/sessions', { params })
}

export async function listStreamingAlgorithms(): Promise<StreamingAlgorithmListResponse> {
  return request<StreamingAlgorithmListResponse>('/anomaly/streaming/algorithms')
}

export function getStreamingWebSocketUrl(sessionId: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/v1/anomaly/streaming/sessions/${sessionId}/ws`
}
