/**
 * Schema Watcher API - Continuous schema monitoring.
 */
import { request } from '../core'
import type { PaginatedResponse } from '../core'

// ============================================================================
// Types - Enums
// ============================================================================

export type SchemaWatcherStatus = 'active' | 'paused' | 'stopped' | 'error'
export type SchemaWatcherAlertStatus = 'open' | 'acknowledged' | 'resolved' | 'suppressed'
export type SchemaWatcherAlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type VersionStrategy = 'semantic' | 'incremental' | 'timestamp' | 'git'
export type ImpactScope = 'local' | 'downstream' | 'system'
export type SchemaWatcherRunStatus = 'pending' | 'running' | 'completed' | 'failed'

// ============================================================================
// Types - Watcher
// ============================================================================

export interface SchemaWatcherCreate {
  name: string
  source_id: string
  poll_interval_seconds?: number
  only_breaking?: boolean
  enable_rename_detection?: boolean
  rename_similarity_threshold?: number
  version_strategy?: VersionStrategy
  notify_on_change?: boolean
  track_history?: boolean
  config?: Record<string, unknown>
}

export interface SchemaWatcherUpdate {
  name?: string
  poll_interval_seconds?: number
  only_breaking?: boolean
  enable_rename_detection?: boolean
  rename_similarity_threshold?: number
  version_strategy?: VersionStrategy
  notify_on_change?: boolean
  track_history?: boolean
  config?: Record<string, unknown>
}

export interface SchemaWatcher {
  id: string
  name: string
  source_id: string
  status: SchemaWatcherStatus
  poll_interval_seconds: number
  only_breaking: boolean
  enable_rename_detection: boolean
  rename_similarity_threshold: number
  version_strategy: VersionStrategy
  notify_on_change: boolean
  track_history: boolean
  last_check_at?: string
  last_change_at?: string
  next_check_at?: string
  check_count: number
  change_count: number
  error_count: number
  last_error?: string
  config?: Record<string, unknown>
  is_active: boolean
  is_healthy: boolean
  detection_rate: number
  source_name?: string
  created_at: string
  updated_at: string
}

export interface SchemaWatcherSummary {
  id: string
  name: string
  source_id: string
  source_name?: string
  status: SchemaWatcherStatus
  poll_interval_seconds: number
  check_count: number
  change_count: number
  last_check_at?: string
  next_check_at?: string
  created_at: string
}

export interface SchemaWatcherStatistics {
  total_watchers: number
  active_watchers: number
  paused_watchers: number
  error_watchers: number
  total_alerts: number
  open_alerts: number
  acknowledged_alerts: number
  resolved_alerts: number
  total_runs: number
  successful_runs: number
  failed_runs: number
  total_changes_detected: number
  total_breaking_changes: number
  avg_detection_rate: number
  avg_time_to_acknowledge?: number
  avg_time_to_resolve?: number
}

export interface SchemaWatcherCheckNowResponse {
  watcher_id: string
  run_id: string
  status: SchemaWatcherRunStatus
  changes_detected: number
  breaking_detected: number
  alert_created_id?: string
  version_created_id?: string
  duration_ms?: number
  message: string
}

// ============================================================================
// Types - Alert
// ============================================================================

export interface SchemaWatcherAlert {
  id: string
  watcher_id: string
  source_id: string
  from_version_id?: string
  to_version_id: string
  title: string
  severity: SchemaWatcherAlertSeverity
  status: SchemaWatcherAlertStatus
  total_changes: number
  breaking_changes: number
  changes_summary?: {
    total: number
    breaking: number
    from_version?: number
    to_version: number
    changes: Array<{
      type: string
      column: string
      old_value?: string
      new_value?: string
      severity: string
    }>
  }
  impact_scope?: ImpactScope
  affected_consumers?: string[]
  recommendations?: string[]
  acknowledged_at?: string
  acknowledged_by?: string
  resolved_at?: string
  resolved_by?: string
  resolution_notes?: string
  is_open: boolean
  has_breaking_changes: boolean
  time_to_acknowledge?: number
  time_to_resolve?: number
  source_name?: string
  watcher_name?: string
  created_at: string
  updated_at: string
}

export interface SchemaWatcherAlertSummary {
  id: string
  watcher_id: string
  source_id: string
  title: string
  severity: SchemaWatcherAlertSeverity
  status: SchemaWatcherAlertStatus
  total_changes: number
  breaking_changes: number
  created_at: string
  source_name?: string
}

export interface SchemaWatcherAlertAcknowledge {
  acknowledged_by?: string
}

export interface SchemaWatcherAlertResolve {
  resolved_by?: string
  resolution_notes?: string
}

// ============================================================================
// Types - Run
// ============================================================================

export interface SchemaWatcherRun {
  id: string
  watcher_id: string
  source_id: string
  started_at: string
  completed_at?: string
  status: SchemaWatcherRunStatus
  changes_detected: number
  breaking_detected: number
  version_created_id?: string
  alert_created_id?: string
  duration_ms?: number
  error_message?: string
  metadata?: Record<string, unknown>
  is_successful: boolean
  has_changes: boolean
  source_name?: string
  watcher_name?: string
}

export interface SchemaWatcherRunSummary {
  id: string
  watcher_id: string
  source_id: string
  started_at: string
  status: SchemaWatcherRunStatus
  changes_detected: number
  breaking_detected: number
  duration_ms?: number
}

// ============================================================================
// Types - List Responses
// ============================================================================

export type SchemaWatcherListResponse = PaginatedResponse<SchemaWatcherSummary>
export type SchemaWatcherAlertListResponse = PaginatedResponse<SchemaWatcherAlertSummary>
export type SchemaWatcherRunListResponse = PaginatedResponse<SchemaWatcherRunSummary>

// ============================================================================
// API Functions - Watchers
// ============================================================================

export async function createSchemaWatcher(
  data: SchemaWatcherCreate
): Promise<SchemaWatcher> {
  return request<SchemaWatcher>('/schema-watchers', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function listSchemaWatchers(params?: {
  status?: SchemaWatcherStatus
  source_id?: string
  offset?: number
  limit?: number
}): Promise<SchemaWatcherListResponse> {
  return request<SchemaWatcherListResponse>('/schema-watchers', { params })
}

export async function getSchemaWatcher(id: string): Promise<SchemaWatcher> {
  return request<SchemaWatcher>(`/schema-watchers/${id}`)
}

export async function updateSchemaWatcher(
  id: string,
  data: SchemaWatcherUpdate
): Promise<SchemaWatcher> {
  return request<SchemaWatcher>(`/schema-watchers/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteSchemaWatcher(
  id: string
): Promise<{ message: string }> {
  return request<{ message: string }>(`/schema-watchers/${id}`, {
    method: 'DELETE',
  })
}

export async function setSchemaWatcherStatus(
  id: string,
  status: SchemaWatcherStatus
): Promise<SchemaWatcher> {
  return request<SchemaWatcher>(`/schema-watchers/${id}/status`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  })
}

export async function checkSchemaWatcherNow(
  id: string
): Promise<SchemaWatcherCheckNowResponse> {
  return request<SchemaWatcherCheckNowResponse>(`/schema-watchers/${id}/check`, {
    method: 'POST',
  })
}

export async function getSchemaWatcherStatistics(): Promise<SchemaWatcherStatistics> {
  return request<SchemaWatcherStatistics>('/schema-watchers/statistics')
}

// ============================================================================
// Types - Scheduler Status
// ============================================================================

export interface SchemaWatcherSchedulerStatus {
  enabled: boolean
  checker_running: boolean
  checker_interval_seconds: number
  last_checker_run_at?: string
  total_checks: number
  total_processed: number
}

export async function getSchemaWatcherSchedulerStatus(): Promise<SchemaWatcherSchedulerStatus> {
  return request<SchemaWatcherSchedulerStatus>('/schema-watchers/scheduler/status')
}

// ============================================================================
// API Functions - Alerts
// ============================================================================

export async function listSchemaWatcherAlerts(params?: {
  watcher_id?: string
  source_id?: string
  status?: SchemaWatcherAlertStatus
  severity?: SchemaWatcherAlertSeverity
  offset?: number
  limit?: number
}): Promise<SchemaWatcherAlertListResponse> {
  return request<SchemaWatcherAlertListResponse>('/schema-watchers/alerts', { params })
}

export async function getSchemaWatcherAlert(id: string): Promise<SchemaWatcherAlert> {
  return request<SchemaWatcherAlert>(`/schema-watchers/alerts/${id}`)
}

export async function acknowledgeSchemaWatcherAlert(
  id: string,
  data?: SchemaWatcherAlertAcknowledge
): Promise<SchemaWatcherAlert> {
  return request<SchemaWatcherAlert>(`/schema-watchers/alerts/${id}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
}

export async function resolveSchemaWatcherAlert(
  id: string,
  data?: SchemaWatcherAlertResolve
): Promise<SchemaWatcherAlert> {
  return request<SchemaWatcherAlert>(`/schema-watchers/alerts/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
}

export async function listWatcherAlerts(
  watcherId: string,
  params?: {
    status?: SchemaWatcherAlertStatus
    offset?: number
    limit?: number
  }
): Promise<SchemaWatcherAlertListResponse> {
  return request<SchemaWatcherAlertListResponse>(
    `/schema-watchers/${watcherId}/alerts`,
    { params }
  )
}

// ============================================================================
// API Functions - Runs
// ============================================================================

export async function listSchemaWatcherRuns(params?: {
  watcher_id?: string
  source_id?: string
  status?: SchemaWatcherRunStatus
  offset?: number
  limit?: number
}): Promise<SchemaWatcherRunListResponse> {
  return request<SchemaWatcherRunListResponse>('/schema-watchers/runs', { params })
}

export async function getSchemaWatcherRun(id: string): Promise<SchemaWatcherRun> {
  return request<SchemaWatcherRun>(`/schema-watchers/runs/${id}`)
}

export async function listWatcherRuns(
  watcherId: string,
  params?: {
    status?: SchemaWatcherRunStatus
    offset?: number
    limit?: number
  }
): Promise<SchemaWatcherRunListResponse> {
  return request<SchemaWatcherRunListResponse>(
    `/schema-watchers/${watcherId}/runs`,
    { params }
  )
}

// ============================================================================
// Constants
// ============================================================================

export const WATCHER_STATUS_OPTIONS: {
  value: SchemaWatcherStatus
  label: string
  color: string
}[] = [
  { value: 'active', label: 'Active', color: 'green' },
  { value: 'paused', label: 'Paused', color: 'yellow' },
  { value: 'stopped', label: 'Stopped', color: 'gray' },
  { value: 'error', label: 'Error', color: 'red' },
]

export const ALERT_STATUS_OPTIONS: {
  value: SchemaWatcherAlertStatus
  label: string
  color: string
}[] = [
  { value: 'open', label: 'Open', color: 'red' },
  { value: 'acknowledged', label: 'Acknowledged', color: 'yellow' },
  { value: 'resolved', label: 'Resolved', color: 'green' },
  { value: 'suppressed', label: 'Suppressed', color: 'gray' },
]

export const ALERT_SEVERITY_OPTIONS: {
  value: SchemaWatcherAlertSeverity
  label: string
  color: string
}[] = [
  { value: 'critical', label: 'Critical', color: 'red' },
  { value: 'high', label: 'High', color: 'orange' },
  { value: 'medium', label: 'Medium', color: 'yellow' },
  { value: 'low', label: 'Low', color: 'blue' },
  { value: 'info', label: 'Info', color: 'gray' },
]

export const VERSION_STRATEGY_OPTIONS: {
  value: VersionStrategy
  label: string
  description: string
}[] = [
  { value: 'semantic', label: 'Semantic', description: 'Major.Minor.Patch versioning' },
  { value: 'incremental', label: 'Incremental', description: 'Simple incrementing numbers' },
  { value: 'timestamp', label: 'Timestamp', description: 'Based on detection time' },
  { value: 'git', label: 'Git', description: 'Follows git commit history' },
]

export const POLL_INTERVAL_OPTIONS: { value: number; label: string }[] = [
  { value: 10, label: '10 seconds' },
  { value: 30, label: '30 seconds' },
  { value: 60, label: '1 minute' },
  { value: 300, label: '5 minutes' },
  { value: 600, label: '10 minutes' },
  { value: 1800, label: '30 minutes' },
  { value: 3600, label: '1 hour' },
  { value: 21600, label: '6 hours' },
  { value: 43200, label: '12 hours' },
  { value: 86400, label: '24 hours' },
]

// ============================================================================
// Types - Schema Detection (truthound integration)
// Note: These types are prefixed with "Watcher" to avoid conflicts with
// schema-evolution.ts types. They represent truthound 1.2.10+ Schema Evolution API.
// ============================================================================

export type WatcherSchemaChangeType =
  | 'column_added'
  | 'column_removed'
  | 'column_renamed'
  | 'type_changed'
  | 'nullable_changed'
  | 'constraint_changed'

export type WatcherSchemaChangeSeverity = 'info' | 'warning' | 'critical'
export type CompatibilityLevel = 'compatible' | 'minor' | 'breaking'
export type RenameConfidence = 'high' | 'medium' | 'low'
export type SimilarityAlgorithm =
  | 'composite'
  | 'levenshtein'
  | 'jaro_winkler'
  | 'ngram'
  | 'token'

export interface SchemaChangeDetail {
  change_type: WatcherSchemaChangeType
  column_name: string
  old_value?: unknown
  new_value?: unknown
  severity: WatcherSchemaChangeSeverity
  breaking: boolean
  description: string
  migration_hint?: string
}

export interface RenameDetectionDetail {
  old_name: string
  new_name: string
  similarity: number
  confidence: RenameConfidence
  reasons: string[]
}

export interface SchemaDetectionRequest {
  current_schema: Record<string, unknown>
  baseline_schema: Record<string, unknown>
  detect_renames?: boolean
  rename_similarity_threshold?: number
}

export interface SchemaDetectionResponse {
  total_changes: number
  breaking_changes: number
  compatibility_level: CompatibilityLevel
  changes: SchemaChangeDetail[]
}

export interface RenameDetectionRequest {
  added_columns: Record<string, string>
  removed_columns: Record<string, string>
  similarity_threshold?: number
  require_type_match?: boolean
  allow_compatible_types?: boolean
  algorithm?: SimilarityAlgorithm
}

export interface RenameDetectionResponse {
  confirmed_renames: RenameDetectionDetail[]
  possible_renames: RenameDetectionDetail[]
  unmatched_added: string[]
  unmatched_removed: string[]
}

// ============================================================================
// Types - Schema Version History (truthound integration)
// Note: These types are prefixed with "Watcher" to avoid conflicts with
// schema-evolution.ts types.
// ============================================================================

export interface WatcherSchemaVersionCreate {
  schema: Record<string, unknown>
  version?: string
  metadata?: Record<string, unknown>
}

export interface WatcherSchemaVersionResponse {
  id: string
  version: string
  schema: Record<string, unknown>
  metadata?: Record<string, unknown>
  created_at?: string
  has_breaking_changes: boolean
  changes_from_parent?: SchemaChangeDetail[]
}

export interface WatcherSchemaVersionSummary {
  id: string
  version: string
  column_count: number
  created_at?: string
  has_breaking_changes: boolean
}

export interface SchemaDiffRequest {
  from_version: string
  to_version?: string
}

export interface SchemaDiffResponse {
  from_version: string
  to_version: string
  changes: SchemaChangeDetail[]
  text_diff: string
}

export interface SchemaRollbackRequest {
  to_version: string
  reason?: string
}

// ============================================================================
// Types - Scheduler Status (updated)
// ============================================================================

export interface SchemaWatcherSchedulerStatusV2 {
  is_running: boolean
  active_watchers: number
  next_check_at?: string
  last_run_at?: string
  pending_checks: number
}

// ============================================================================
// API Functions - Schema Detection (truthound integration)
// ============================================================================

/**
 * Detect schema changes between two schemas using truthound's SchemaEvolutionDetector.
 */
export async function watcherDetectSchemaChanges(
  data: SchemaDetectionRequest
): Promise<SchemaDetectionResponse> {
  return request<SchemaDetectionResponse>('/schema-watchers/detect-changes', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Detect column renames using truthound's ColumnRenameDetector.
 */
export async function watcherDetectColumnRenames(
  data: RenameDetectionRequest
): Promise<RenameDetectionResponse> {
  return request<RenameDetectionResponse>('/schema-watchers/detect-renames', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ============================================================================
// API Functions - Schema Version History (truthound integration)
// ============================================================================

/**
 * List schema versions tracked by a watcher.
 */
export async function watcherListSchemaVersions(
  watcherId: string,
  params?: { limit?: number }
): Promise<WatcherSchemaVersionSummary[]> {
  return request<WatcherSchemaVersionSummary[]>(
    `/schema-watchers/${watcherId}/versions`,
    { params }
  )
}

/**
 * Get a specific schema version.
 */
export async function watcherGetSchemaVersion(
  watcherId: string,
  version: string
): Promise<WatcherSchemaVersionResponse> {
  return request<WatcherSchemaVersionResponse>(
    `/schema-watchers/${watcherId}/versions/${version}`
  )
}

/**
 * Manually save a schema version.
 */
export async function watcherSaveSchemaVersion(
  watcherId: string,
  data: WatcherSchemaVersionCreate
): Promise<WatcherSchemaVersionResponse> {
  return request<WatcherSchemaVersionResponse>(
    `/schema-watchers/${watcherId}/versions`,
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  )
}

/**
 * Get the diff between two schema versions.
 */
export async function watcherDiffSchemaVersions(
  watcherId: string,
  data: SchemaDiffRequest
): Promise<SchemaDiffResponse> {
  return request<SchemaDiffResponse>(
    `/schema-watchers/${watcherId}/versions/diff`,
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  )
}

/**
 * Rollback to a previous schema version.
 */
export async function watcherRollbackSchemaVersion(
  watcherId: string,
  data: SchemaRollbackRequest
): Promise<WatcherSchemaVersionResponse> {
  return request<WatcherSchemaVersionResponse>(
    `/schema-watchers/${watcherId}/versions/rollback`,
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  )
}

// ============================================================================
// Constants - Similarity Algorithms
// ============================================================================

export const SIMILARITY_ALGORITHM_OPTIONS: {
  value: SimilarityAlgorithm
  label: string
  description: string
}[] = [
  {
    value: 'composite',
    label: 'Composite',
    description: 'Weighted combination (recommended)',
  },
  {
    value: 'levenshtein',
    label: 'Levenshtein',
    description: 'Edit distance for general names',
  },
  {
    value: 'jaro_winkler',
    label: 'Jaro-Winkler',
    description: 'Short strings and prefixes',
  },
  {
    value: 'ngram',
    label: 'N-gram',
    description: 'Partial matches',
  },
  {
    value: 'token',
    label: 'Token',
    description: 'snake_case and camelCase names',
  },
]

export const WATCHER_CHANGE_TYPE_LABELS: Record<WatcherSchemaChangeType, string> = {
  column_added: 'Column Added',
  column_removed: 'Column Removed',
  column_renamed: 'Column Renamed',
  type_changed: 'Type Changed',
  nullable_changed: 'Nullable Changed',
  constraint_changed: 'Constraint Changed',
}

export const WATCHER_CHANGE_SEVERITY_COLORS: Record<WatcherSchemaChangeSeverity, string> = {
  info: 'blue',
  warning: 'yellow',
  critical: 'red',
}

export const COMPATIBILITY_LEVEL_LABELS: Record<CompatibilityLevel, string> = {
  compatible: 'Fully Compatible',
  minor: 'Minor Changes',
  breaking: 'Breaking Changes',
}

export const RENAME_CONFIDENCE_COLORS: Record<RenameConfidence, string> = {
  high: 'green',
  medium: 'yellow',
  low: 'red',
}
