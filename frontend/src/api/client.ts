/**
 * API client for truthound-dashboard backend
 */

const API_BASE = '/api/v1'

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>
}

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'ApiError'
  }
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, ...init } = options

  // Build URL with query params
  let url = `${API_BASE}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += `?${queryString}`
    }
  }

  // Set default headers
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(url, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let data
    try {
      data = await response.json()
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(response.status, response.statusText, data)
  }

  // Handle empty responses
  const contentType = response.headers.get('Content-Type')
  if (!contentType || !contentType.includes('application/json')) {
    return {} as T
  }

  return response.json()
}

// Health
export async function getHealth() {
  return request<{
    status: string
    version: string
    timestamp: string
  }>('/health')
}

// Sources
export interface Source {
  id: string
  name: string
  type: string
  config: Record<string, unknown>
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_validated_at?: string
  has_schema: boolean
  latest_validation_status?: string
}

export interface SourceListResponse {
  success: boolean
  data: Source[]
  total: number
  offset: number
  limit: number
}

export async function listSources(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<SourceListResponse> {
  return request<SourceListResponse>('/sources', { params })
}

export async function getSource(id: string): Promise<Source> {
  return request<Source>(`/sources/${id}`)
}

export async function createSource(data: {
  name: string
  type: string
  config: Record<string, unknown>
  description?: string
}): Promise<Source> {
  return request<Source>('/sources', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateSource(
  id: string,
  data: {
    name?: string
    config?: Record<string, unknown>
    description?: string
    is_active?: boolean
  }
): Promise<Source> {
  return request<Source>(`/sources/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteSource(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/sources/${id}`, {
    method: 'DELETE',
  })
}

// Validations
export interface ValidationIssue {
  column: string
  issue_type: string
  count: number
  severity: 'critical' | 'high' | 'medium' | 'low'
  details?: string
  expected?: unknown
  actual?: unknown
}

export interface Validation {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  passed: boolean
  has_critical: boolean
  has_high: boolean
  total_issues: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
  row_count?: number
  column_count?: number
  issues: ValidationIssue[]
  error_message?: string
  duration_ms?: number
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface ValidationListResponse {
  success: boolean
  data: Validation[]
  total: number
  limit: number
}

export async function runValidation(
  sourceId: string,
  data?: {
    validators?: string[]
    schema_path?: string
    auto_schema?: boolean
  }
): Promise<Validation> {
  return request<Validation>(`/validations/sources/${sourceId}/validate`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
}

export async function getValidation(id: string): Promise<Validation> {
  return request<Validation>(`/validations/${id}`)
}

export async function listSourceValidations(
  sourceId: string,
  params?: { limit?: number }
): Promise<ValidationListResponse> {
  return request<ValidationListResponse>(
    `/validations/sources/${sourceId}/validations`,
    { params }
  )
}

// Schemas
export interface Schema {
  id: string
  source_id: string
  schema_yaml: string
  schema_json?: Record<string, unknown>
  row_count?: number
  column_count?: number
  columns: string[]
  version?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export async function getSourceSchema(sourceId: string): Promise<Schema | null> {
  return request<Schema | null>(`/sources/${sourceId}/schema`)
}

export async function learnSchema(
  sourceId: string,
  data?: { infer_constraints?: boolean }
): Promise<Schema> {
  return request<Schema>(`/sources/${sourceId}/learn`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
}

export async function updateSchema(
  sourceId: string,
  schemaYaml: string
): Promise<Schema> {
  return request<Schema>(`/sources/${sourceId}/schema`, {
    method: 'PUT',
    body: JSON.stringify({ schema_yaml: schemaYaml }),
  })
}

// Profile
export interface ColumnProfile {
  name: string
  dtype: string
  null_pct: string
  unique_pct: string
  min?: unknown
  max?: unknown
  mean?: number
  std?: number
}

export interface ProfileResult {
  source: string
  row_count: number
  column_count: number
  size_bytes: number
  columns: ColumnProfile[]
}

export async function profileSource(sourceId: string): Promise<ProfileResult> {
  return request<ProfileResult>(`/sources/${sourceId}/profile`, {
    method: 'POST',
  })
}

// Test source connection
export async function testSourceConnection(
  sourceId: string
): Promise<{ success: boolean; data: { success: boolean; message?: string; error?: string } }> {
  return request(`/sources/${sourceId}/test`, { method: 'POST' })
}

// Get supported source types
export async function getSupportedSourceTypes(): Promise<{
  success: boolean
  data: {
    type: string
    name: string
    description: string
    required_fields: string[]
    optional_fields: string[]
  }[]
}> {
  return request('/sources/types/supported')
}

// History
export interface HistorySummary {
  total_runs: number
  passed_runs: number
  failed_runs: number
  success_rate: number
}

export interface TrendDataPoint {
  date: string
  success_rate: number
  run_count: number
  passed_count: number
  failed_count: number
}

export interface FailureFrequencyItem {
  issue: string
  count: number
}

export interface RecentValidation {
  id: string
  status: string
  passed: boolean
  has_critical: boolean
  has_high: boolean
  total_issues: number
  created_at: string
}

export interface HistoryResponse {
  success: boolean
  data: {
    summary: HistorySummary
    trend: TrendDataPoint[]
    failure_frequency: FailureFrequencyItem[]
    recent_validations: RecentValidation[]
  }
}

export async function getValidationHistory(
  sourceId: string,
  params?: {
    period?: '7d' | '30d' | '90d'
    granularity?: 'hourly' | 'daily' | 'weekly'
  }
): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/sources/${sourceId}/history`, { params })
}

// Drift Detection
export interface DriftCompareRequest {
  baseline_source_id: string
  current_source_id: string
  columns?: string[]
  method?: 'auto' | 'ks' | 'psi' | 'chi2' | 'js'
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

export async function compareDrift(
  data: DriftCompareRequest
): Promise<{ success: boolean; data: DriftComparison }> {
  return request('/drift/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function listDriftComparisons(params?: {
  baseline_source_id?: string
  current_source_id?: string
  limit?: number
}): Promise<{ success: boolean; data: DriftComparison[]; total: number }> {
  return request('/drift/comparisons', { params })
}

export async function getDriftComparison(
  id: string
): Promise<{ success: boolean; data: DriftComparison }> {
  return request(`/drift/comparisons/${id}`)
}

// Schedules
export interface Schedule {
  id: string
  name: string
  source_id: string
  cron_expression: string
  is_active: boolean
  notify_on_failure: boolean
  last_run_at?: string
  next_run_at?: string
  config?: Record<string, unknown>
  created_at: string
  updated_at?: string
  source_name?: string
}

export interface ScheduleCreateRequest {
  source_id: string
  name: string
  cron_expression: string
  notify_on_failure?: boolean
  config?: Record<string, unknown>
}

export interface ScheduleUpdateRequest {
  name?: string
  cron_expression?: string
  notify_on_failure?: boolean
  config?: Record<string, unknown>
}

export async function listSchedules(params?: {
  source_id?: string
  active_only?: boolean
  limit?: number
}): Promise<{ success: boolean; data: Schedule[]; total: number }> {
  return request('/schedules', { params })
}

export async function createSchedule(
  data: ScheduleCreateRequest
): Promise<{ success: boolean; data: Schedule }> {
  return request('/schedules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getSchedule(
  id: string
): Promise<{ success: boolean; data: Schedule }> {
  return request(`/schedules/${id}`)
}

export async function updateSchedule(
  id: string,
  data: ScheduleUpdateRequest
): Promise<{ success: boolean; data: Schedule }> {
  return request(`/schedules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteSchedule(
  id: string
): Promise<{ success: boolean; message: string }> {
  return request(`/schedules/${id}`, { method: 'DELETE' })
}

export async function pauseSchedule(
  id: string
): Promise<{ success: boolean; message: string; schedule: Schedule }> {
  return request(`/schedules/${id}/pause`, { method: 'POST' })
}

export async function resumeSchedule(
  id: string
): Promise<{ success: boolean; message: string; schedule: Schedule }> {
  return request(`/schedules/${id}/resume`, { method: 'POST' })
}

export async function runScheduleNow(
  id: string
): Promise<{ success: boolean; message: string; validation_id: string; passed: boolean }> {
  return request(`/schedules/${id}/run`, { method: 'POST' })
}

// ============================================================================
// Notifications (Phase 3)
// ============================================================================

export interface NotificationChannel {
  id: string
  name: string
  type: 'slack' | 'email' | 'webhook'
  is_active: boolean
  config_summary: string
  created_at: string
  updated_at: string
}

export interface NotificationRule {
  id: string
  name: string
  condition: string
  condition_config?: Record<string, unknown>
  channel_ids: string[]
  source_ids?: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface NotificationLog {
  id: string
  channel_id: string
  rule_id?: string
  event_type: string
  status: 'pending' | 'sent' | 'failed'
  message_preview: string
  error_message?: string
  created_at: string
  sent_at?: string
}

export interface NotificationStats {
  period_hours: number
  total: number
  by_status: Record<string, number>
  by_channel: Record<string, number>
  success_rate: number
}

// Notification Channels
export async function listNotificationChannels(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  channel_type?: string
}): Promise<{ success: boolean; data: NotificationChannel[]; count: number }> {
  return request('/notifications/channels', { params })
}

export async function getNotificationChannel(
  id: string
): Promise<{ success: boolean; data: NotificationChannel }> {
  return request(`/notifications/channels/${id}`)
}

export async function createNotificationChannel(data: {
  name: string
  type: string
  config: Record<string, unknown>
  is_active?: boolean
}): Promise<{ success: boolean; data: NotificationChannel }> {
  return request('/notifications/channels', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateNotificationChannel(
  id: string,
  data: {
    name?: string
    config?: Record<string, unknown>
    is_active?: boolean
  }
): Promise<{ success: boolean; data: NotificationChannel }> {
  return request(`/notifications/channels/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteNotificationChannel(
  id: string
): Promise<{ success: boolean }> {
  return request(`/notifications/channels/${id}`, { method: 'DELETE' })
}

export async function testNotificationChannel(
  id: string
): Promise<{ success: boolean; message: string; error?: string }> {
  return request(`/notifications/channels/${id}/test`, { method: 'POST' })
}

export async function getNotificationChannelTypes(): Promise<{
  success: boolean
  data: Record<string, Record<string, unknown>>
}> {
  return request('/notifications/channels/types')
}

// Notification Rules
export async function listNotificationRules(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  condition?: string
}): Promise<{ success: boolean; data: NotificationRule[]; count: number }> {
  return request('/notifications/rules', { params })
}

export async function getNotificationRule(
  id: string
): Promise<{ success: boolean; data: NotificationRule }> {
  return request(`/notifications/rules/${id}`)
}

export async function createNotificationRule(data: {
  name: string
  condition: string
  channel_ids: string[]
  condition_config?: Record<string, unknown>
  source_ids?: string[]
  is_active?: boolean
}): Promise<{ success: boolean; data: NotificationRule }> {
  return request('/notifications/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateNotificationRule(
  id: string,
  data: {
    name?: string
    condition?: string
    channel_ids?: string[]
    condition_config?: Record<string, unknown>
    source_ids?: string[]
    is_active?: boolean
  }
): Promise<{ success: boolean; data: NotificationRule }> {
  return request(`/notifications/rules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteNotificationRule(
  id: string
): Promise<{ success: boolean }> {
  return request(`/notifications/rules/${id}`, { method: 'DELETE' })
}

export async function getNotificationRuleConditions(): Promise<{
  success: boolean
  data: string[]
}> {
  return request('/notifications/rules/conditions')
}

// Notification Logs
export async function listNotificationLogs(params?: {
  offset?: number
  limit?: number
  channel_id?: string
  status?: string
  hours?: number
}): Promise<{ success: boolean; data: NotificationLog[]; count: number }> {
  return request('/notifications/logs', { params })
}

export async function getNotificationLog(
  id: string
): Promise<{ success: boolean; data: NotificationLog & { message: string; event_data?: unknown } }> {
  return request(`/notifications/logs/${id}`)
}

export async function getNotificationStats(params?: {
  hours?: number
}): Promise<{ success: boolean; data: NotificationStats }> {
  return request('/notifications/logs/stats', { params })
}

// API client helper for direct requests
export const apiClient = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (endpoint: string) => request(endpoint, { method: 'DELETE' }),
}

export { ApiError }
