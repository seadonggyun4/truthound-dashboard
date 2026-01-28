/**
 * Drift API - Drift detection and comparison.
 */
import { request } from '../core'
import type { PaginatedResponse } from '../core'

// ============================================================================
// Types
// ============================================================================

/**
 * Drift detection methods (14 methods supported by truthound v1.2.9+).
 */
export type DriftMethod =
  | 'auto'
  | 'ks'
  | 'psi'
  | 'chi2'
  | 'js'
  | 'kl'
  | 'wasserstein'
  | 'cvm'
  | 'anderson'
  // New in v1.2.9
  | 'hellinger'
  | 'bhattacharyya'
  | 'tv'
  | 'energy'
  | 'mmd'

/**
 * All drift methods for UI selection (14 methods).
 *
 * Categories:
 * - General purpose (any column type): auto, js, hellinger, bhattacharyya, tv
 * - Numeric columns only: ks, psi, kl, wasserstein, cvm, anderson, energy, mmd
 * - Categorical columns: chi2
 */
export const DRIFT_METHODS: { value: DriftMethod; label: string; description: string }[] = [
  // General purpose
  { value: 'auto', label: 'Auto', description: 'Smart selection based on data type' },
  { value: 'js', label: 'Jensen-Shannon', description: 'Symmetric divergence, bounded 0-1' },
  { value: 'hellinger', label: 'Hellinger', description: 'Bounded metric (0-1), satisfies triangle inequality' },
  { value: 'bhattacharyya', label: 'Bhattacharyya', description: 'Classification error bounds estimation' },
  { value: 'tv', label: 'Total Variation', description: 'Maximum probability difference' },
  // Numeric columns
  { value: 'ks', label: 'Kolmogorov-Smirnov', description: 'Best for continuous distributions' },
  { value: 'psi', label: 'PSI', description: 'Population Stability Index - industry standard' },
  { value: 'kl', label: 'Kullback-Leibler', description: 'Information loss measure (asymmetric)' },
  { value: 'wasserstein', label: 'Wasserstein', description: "Earth Mover's Distance" },
  { value: 'cvm', label: 'Cramér-von Mises', description: 'More sensitive to tails than KS' },
  { value: 'anderson', label: 'Anderson-Darling', description: 'Most sensitive to tail differences' },
  { value: 'energy', label: 'Energy', description: 'Location and scale sensitive' },
  { value: 'mmd', label: 'MMD', description: 'Maximum Mean Discrepancy - kernel-based, high-dimensional' },
  // Categorical columns
  { value: 'chi2', label: 'Chi-Square', description: 'Best for categorical data' },
]

/**
 * Default thresholds for each detection method.
 */
export const DEFAULT_THRESHOLDS: Record<DriftMethod, number> = {
  auto: 0.05,
  ks: 0.05,
  psi: 0.1,
  chi2: 0.05,
  js: 0.1,
  kl: 0.1,
  wasserstein: 0.1,
  cvm: 0.05,
  anderson: 0.05,
  // New in v1.2.9
  hellinger: 0.1,
  bhattacharyya: 0.1,
  tv: 0.1,
  energy: 0.1,
  mmd: 0.1,
}

export interface DriftCompareRequest {
  baseline_source_id: string
  current_source_id: string
  columns?: string[]
  method?: DriftMethod
  threshold?: number
  sample_size?: number
}

export interface ColumnDriftResult {
  column: string
  dtype: string
  drifted: boolean
  level: string
  method: string
  statistic?: number
  p_value?: number
  baseline_stats: Record<string, unknown>
  current_stats: Record<string, unknown>
}

export interface DriftResult {
  comparison_id?: string
  baseline_source: string
  current_source: string
  baseline_rows: number
  current_rows: number
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: string[]
  columns: ColumnDriftResult[]
}

export interface DriftComparison {
  id: string
  baseline_source_id: string
  current_source_id: string
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: number
  drift_percentage: number
  result?: DriftResult
  config?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export type DriftComparisonListResponse = PaginatedResponse<DriftComparison>

// ============================================================================
// API Functions
// ============================================================================

export async function compareDrift(
  data: DriftCompareRequest
): Promise<DriftComparison> {
  return request<DriftComparison>('/drift/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function listDriftComparisons(params?: {
  baseline_source_id?: string
  current_source_id?: string
  offset?: number
  limit?: number
}): Promise<DriftComparisonListResponse> {
  return request<DriftComparisonListResponse>('/drift/comparisons', { params })
}

export async function getDriftComparison(
  id: string
): Promise<DriftComparison> {
  return request<DriftComparison>(`/drift/comparisons/${id}`)
}

// ============================================================================
// Drift Monitor Types
// ============================================================================

export interface DriftMonitor {
  id: string
  name: string
  baseline_source_id: string
  current_source_id: string
  baseline_source_name?: string
  current_source_name?: string
  cron_expression?: string
  method: string
  threshold: number
  columns?: string[]
  alert_on_drift?: boolean
  alert_threshold_critical?: number
  alert_threshold_high?: number
  notification_channel_ids?: string[]
  status: 'active' | 'paused' | 'error'
  last_run_at?: string | null
  last_drift_detected?: boolean | null
  total_runs: number
  drift_detected_count: number
  consecutive_drift_count: number
  created_at: string
  updated_at?: string
}

export interface DriftMonitorCreate {
  name: string
  baseline_source_id: string
  current_source_id: string
  cron_expression?: string
  method?: DriftMethod | string
  threshold?: number
  columns?: string[]
  alert_on_drift?: boolean
  alert_threshold_critical?: number
  alert_threshold_high?: number
  notification_channel_ids?: string[]
  // Large dataset optimization (from form)
  sampling_enabled?: boolean
  sampling_config?: unknown
  // Allow additional form properties
  [key: string]: unknown
}

export interface DriftMonitorUpdate {
  name?: string
  baseline_source_id?: string
  current_source_id?: string
  cron_expression?: string
  method?: DriftMethod | string
  threshold?: number
  columns?: string[]
  alert_on_drift?: boolean
  alert_threshold_critical?: number
  alert_threshold_high?: number
  notification_channel_ids?: string[]
  status?: 'active' | 'paused'
  // Large dataset optimization (from form)
  sampling_enabled?: boolean
  sampling_config?: unknown
  // Allow additional form properties
  [key: string]: unknown
}

export interface DriftMonitorSummary {
  total_monitors: number
  active_monitors: number
  paused_monitors: number
  monitors_with_drift: number
  total_open_alerts: number
  critical_alerts: number
  high_alerts: number
}

export interface DriftAlert {
  id: string
  monitor_id: string
  comparison_id: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  drift_percentage: number
  drifted_columns: string[]
  message: string
  status: 'open' | 'acknowledged' | 'resolved' | 'ignored'
  acknowledged_at: string | null
  acknowledged_by?: string
  resolved_at: string | null
  notes: string | null
  created_at: string
  updated_at?: string
}

export interface DriftTrendData {
  dates: string[]
  drift_percentages: number[]
  drifted_column_counts: number[]
  has_drift_flags: boolean[]
}

export interface MonitorRunResult {
  comparison_id?: string
  has_drift: boolean
  drift_percentage: number
  drifted_columns?: string[]
}

export type DriftMonitorListResponse = PaginatedResponse<DriftMonitor>
export type DriftAlertListResponse = PaginatedResponse<DriftAlert>

// ============================================================================
// Drift Monitor API Functions
// ============================================================================

export async function listDriftMonitors(params?: {
  status?: string
  limit?: number
  offset?: number
}): Promise<DriftMonitorListResponse> {
  const dedupeKey = `drift-monitors-${JSON.stringify(params ?? {})}`
  return request<DriftMonitorListResponse>('/drift/monitors', { params, dedupe: dedupeKey })
}

export async function getDriftMonitorsSummary(): Promise<DriftMonitorSummary> {
  return request<DriftMonitorSummary>('/drift/monitors/summary', { dedupe: 'drift-monitors-summary' })
}

export async function createDriftMonitor(
  data: DriftMonitorCreate
): Promise<DriftMonitor> {
  return request<DriftMonitor>('/drift/monitors', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getDriftMonitor(id: string): Promise<DriftMonitor> {
  return request<DriftMonitor>(`/drift/monitors/${id}`, { dedupe: `drift-monitor-${id}` })
}

export async function updateDriftMonitor(
  id: string,
  data: DriftMonitorUpdate
): Promise<DriftMonitor> {
  return request<DriftMonitor>(`/drift/monitors/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteDriftMonitor(id: string): Promise<void> {
  await request(`/drift/monitors/${id}`, { method: 'DELETE' })
}

export async function runDriftMonitor(id: string): Promise<MonitorRunResult> {
  return request<MonitorRunResult>(`/drift/monitors/${id}/run`, {
    method: 'POST',
  })
}

export async function getDriftMonitorTrend(
  id: string,
  days: number = 30
): Promise<DriftTrendData> {
  return request<DriftTrendData>(`/drift/monitors/${id}/trend`, {
    params: { days },
  })
}

export async function getDriftMonitorLatestRun(
  id: string
): Promise<DriftResult | null> {
  try {
    return await request<DriftResult>(`/drift/monitors/${id}/latest-run`)
  } catch {
    return null
  }
}

export async function getDriftRootCauseAnalysis(
  monitorId: string,
  runId: string
): Promise<unknown> {
  try {
    return await request(`/drift/monitors/${monitorId}/runs/${runId}/root-cause`)
  } catch {
    return null
  }
}

// ============================================================================
// Drift Alert API Functions
// ============================================================================

export async function listDriftAlerts(params?: {
  monitor_id?: string
  status?: string
  severity?: string
  limit?: number
  offset?: number
}): Promise<DriftAlertListResponse> {
  const dedupeKey = `drift-alerts-${JSON.stringify(params ?? {})}`
  return request<DriftAlertListResponse>('/drift/alerts', { params, dedupe: dedupeKey })
}

export async function getDriftAlert(id: string): Promise<DriftAlert> {
  return request<DriftAlert>(`/drift/alerts/${id}`, { dedupe: `drift-alert-${id}` })
}

export async function updateDriftAlert(
  id: string,
  data: { status?: string; notes?: string }
): Promise<DriftAlert> {
  return request<DriftAlert>(`/drift/alerts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

// ============================================================================
// Drift Preview API Functions
// ============================================================================

export interface DriftPreviewRequest {
  baseline_source_id: string
  current_source_id: string
  columns?: string[]
  method?: DriftMethod
  threshold?: number
}

export interface DriftPreviewData {
  has_drift: boolean
  drift_percentage: number
  total_columns: number
  drifted_columns: string[]
  columns: ColumnDriftResult[]
}

export async function previewDrift(
  data: DriftPreviewRequest
): Promise<DriftPreviewData> {
  return request<DriftPreviewData>('/drift/preview', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
