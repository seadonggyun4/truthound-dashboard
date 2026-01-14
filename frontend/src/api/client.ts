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
  const response = await request<{ success: boolean; data: Source }>(`/sources/${id}`)
  return response.data
}

export async function createSource(data: {
  name: string
  type: string
  config: Record<string, unknown>
  description?: string
}): Promise<Source> {
  const response = await request<{ success: boolean; data: Source }>('/sources', {
    method: 'POST',
    body: JSON.stringify(data),
  })
  return response.data
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
  const response = await request<{ success: boolean; data: Source }>(`/sources/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
  return response.data
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

/**
 * Configuration for a single validator with its parameters.
 */
export interface ValidatorConfig {
  /** Validator name */
  name: string
  /** Whether to run this validator */
  enabled: boolean
  /** Parameter values */
  params: Record<string, unknown>
  /** Override default severity */
  severity_override?: 'low' | 'medium' | 'high' | 'critical'
}

/**
 * Options for running validation - maps to th.check() parameters.
 *
 * Supports two modes:
 * 1. Simple mode: Use `validators` list with validator names (backward compatible)
 * 2. Advanced mode: Use `validator_configs` for per-validator parameter configuration
 *
 * @see https://github.com/truthound/truthound - th.check() documentation
 */
export interface ValidationRunOptions {
  /** Simple mode: Specific validators to run by name. If not provided, all validators run. */
  validators?: string[]
  /** Advanced mode: Per-validator configuration with parameters. Takes precedence over validators. */
  validator_configs?: ValidatorConfig[]
  /** Path to schema YAML file for schema validation. */
  schema_path?: string
  /** Auto-learn and cache schema for validation. */
  auto_schema?: boolean
  /** Columns to validate. If not provided, all columns are validated. */
  columns?: string[]
  /** Minimum severity level to report ('low' | 'medium' | 'high' | 'critical'). */
  min_severity?: 'low' | 'medium' | 'high' | 'critical'
  /** If true, raises exception on validation failures. */
  strict?: boolean
  /** If true, uses DAG-based parallel execution. */
  parallel?: boolean
  /** Max threads for parallel execution (1-32). Only used when parallel=true. */
  max_workers?: number
  /** Enable query pushdown for SQL sources. Undefined uses auto-detection. */
  pushdown?: boolean
}

export async function runValidation(
  sourceId: string,
  options?: ValidationRunOptions
): Promise<Validation> {
  const response = await request<{ success: boolean; data: Validation }>(`/validations/sources/${sourceId}/validate`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
  return response.data
}

export async function getValidation(id: string): Promise<Validation> {
  const response = await request<{ success: boolean; data: Validation }>(`/validations/${id}`)
  return response.data
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
  const response = await request<{ success: boolean; data: Schema | null }>(`/sources/${sourceId}/schema`)
  return response.data
}

export async function learnSchema(
  sourceId: string,
  data?: { infer_constraints?: boolean }
): Promise<Schema> {
  const response = await request<{ success: boolean; data: Schema }>(`/sources/${sourceId}/learn`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
  return response.data
}

export async function updateSchema(
  sourceId: string,
  schemaYaml: string
): Promise<Schema> {
  const response = await request<{ success: boolean; data: Schema }>(`/sources/${sourceId}/schema`, {
    method: 'PUT',
    body: JSON.stringify({ schema_yaml: schemaYaml }),
  })
  return response.data
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

/**
 * Options for data profiling.
 */
export interface ProfileOptions {
  /**
   * Maximum number of rows to sample for profiling.
   * If undefined, profiles all data. Useful for large datasets.
   */
  sample_size?: number
}

export async function profileSource(
  sourceId: string,
  options?: ProfileOptions
): Promise<ProfileResult> {
  const response = await request<{ success: boolean; data: ProfileResult }>(`/sources/${sourceId}/profile`, {
    method: 'POST',
    body: options ? JSON.stringify(options) : undefined,
  })
  return response.data
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

/**
 * Drift detection methods supported by truthound.
 *
 * Each method has different characteristics and use cases:
 * - auto: Smart selection based on data type (numeric → PSI, categorical → chi2)
 * - ks: Kolmogorov-Smirnov test - best for continuous distributions
 * - psi: Population Stability Index - industry standard, any distribution
 * - chi2: Chi-Square test - best for categorical data
 * - js: Jensen-Shannon divergence - symmetric, bounded (0-1)
 * - kl: Kullback-Leibler divergence - information loss measure
 * - wasserstein: Earth Mover's Distance - metric, meaningful for non-overlapping
 * - cvm: Cramér-von Mises - more sensitive to tail differences than KS
 * - anderson: Anderson-Darling - weighted for tail sensitivity
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

/**
 * Multiple testing correction methods.
 *
 * When comparing multiple columns, correction adjusts p-values to control
 * false discovery rate:
 * - none: No correction (use with caution)
 * - bonferroni: Conservative, suitable for independent tests
 * - holm: Sequential adjustment, less conservative than Bonferroni
 * - bh: Benjamini-Hochberg (FDR control), default for multiple columns
 */
export type CorrectionMethod = 'none' | 'bonferroni' | 'holm' | 'bh'

/**
 * All drift methods for UI selection.
 */
export const DRIFT_METHODS: { value: DriftMethod; label: string; description: string }[] = [
  { value: 'auto', label: 'Auto', description: 'Smart selection based on data type' },
  { value: 'ks', label: 'Kolmogorov-Smirnov', description: 'Best for continuous distributions' },
  { value: 'psi', label: 'PSI', description: 'Population Stability Index - industry standard' },
  { value: 'chi2', label: 'Chi-Square', description: 'Best for categorical data' },
  { value: 'js', label: 'Jensen-Shannon', description: 'Symmetric divergence, bounded 0-1' },
  { value: 'kl', label: 'Kullback-Leibler', description: 'Information loss measure' },
  { value: 'wasserstein', label: 'Wasserstein', description: 'Earth Mover\'s Distance' },
  { value: 'cvm', label: 'Cramér-von Mises', description: 'More sensitive to tails than KS' },
  { value: 'anderson', label: 'Anderson-Darling', description: 'Tail-weighted sensitivity' },
]

/**
 * Correction methods for UI selection.
 */
export const CORRECTION_METHODS: { value: CorrectionMethod | ''; label: string; description: string }[] = [
  { value: '', label: 'Default (BH)', description: 'Benjamini-Hochberg FDR control for multiple columns' },
  { value: 'none', label: 'None', description: 'No correction (use with caution)' },
  { value: 'bonferroni', label: 'Bonferroni', description: 'Conservative, independent tests' },
  { value: 'holm', label: 'Holm', description: 'Sequential adjustment, less conservative' },
  { value: 'bh', label: 'Benjamini-Hochberg', description: 'FDR control' },
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
}

export interface DriftCompareRequest {
  baseline_source_id: string
  current_source_id: string
  columns?: string[]
  /** Detection method (see DriftMethod type for details) */
  method?: DriftMethod
  /** Custom threshold (default varies by method) */
  threshold?: number
  /** Multiple testing correction method */
  correction?: CorrectionMethod
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
// PII Scan
// ============================================================================

/**
 * PII types commonly detected by th.scan()
 */
export const PII_TYPES = [
  'email',
  'phone',
  'ssn',
  'credit_card',
  'ip_address',
  'date_of_birth',
  'address',
  'name',
  'passport',
  'driver_license',
  'national_id',
  'bank_account',
  'medical_record',
  'biometric',
] as const

/**
 * Supported privacy regulations for compliance checking.
 */
export type Regulation = 'gdpr' | 'ccpa' | 'lgpd'

export const REGULATIONS: { value: Regulation; label: string; description: string }[] = [
  { value: 'gdpr', label: 'GDPR', description: 'General Data Protection Regulation (EU)' },
  { value: 'ccpa', label: 'CCPA', description: 'California Consumer Privacy Act (US)' },
  { value: 'lgpd', label: 'LGPD', description: 'Lei Geral de Proteção de Dados (Brazil)' },
]

export interface PIIFinding {
  column: string
  pii_type: string
  confidence: number
  sample_count: number
  sample_values?: string[]
}

export interface RegulationViolation {
  regulation: Regulation
  column: string
  pii_type: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export interface PIIScan {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  total_columns_scanned: number
  columns_with_pii: number
  total_findings: number
  has_violations: boolean
  total_violations: number
  row_count?: number
  column_count?: number
  min_confidence: number
  regulations_checked?: string[] | null
  findings: PIIFinding[]
  violations: RegulationViolation[]
  error_message?: string
  duration_ms?: number
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface PIIScanListResponse {
  data: PIIScan[]
  total: number
  limit: number
}

/**
 * Options for running PII scan - maps to th.scan() parameters.
 */
export interface PIIScanOptions {
  /** Specific columns to scan. If not provided, all columns are scanned. */
  columns?: string[]
  /** Privacy regulations to check compliance (gdpr, ccpa, lgpd). */
  regulations?: Regulation[]
  /** Minimum confidence threshold for PII detection (0.0-1.0). Default: 0.8 */
  min_confidence?: number
}

export async function runPIIScan(
  sourceId: string,
  options?: PIIScanOptions
): Promise<PIIScan> {
  return request<PIIScan>(`/scans/sources/${sourceId}/scan`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getPIIScan(id: string): Promise<PIIScan> {
  return request<PIIScan>(`/scans/${id}`)
}

export async function listSourcePIIScans(
  sourceId: string,
  params?: { limit?: number }
): Promise<PIIScanListResponse> {
  return request<PIIScanListResponse>(
    `/scans/sources/${sourceId}/scans`,
    { params }
  )
}

export async function getLatestPIIScan(sourceId: string): Promise<PIIScan> {
  return request<PIIScan>(`/scans/sources/${sourceId}/scans/latest`)
}

// ============================================================================
// Data Masking (th.mask())
// ============================================================================

/**
 * Masking strategies for th.mask():
 * - redact: Replace values with asterisks
 * - hash: Replace values with SHA256 hash (deterministic)
 * - fake: Replace values with realistic fake data
 */
export type MaskingStrategy = 'redact' | 'hash' | 'fake'

export interface DataMask {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  strategy: MaskingStrategy
  output_path?: string
  columns_masked?: string[]
  auto_detected: boolean
  row_count?: number
  column_count?: number
  duration_ms?: number
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface DataMaskListItem {
  id: string
  source_id: string
  source_name?: string
  status: string
  strategy: string
  columns_masked: number
  row_count?: number
  duration_ms?: number
  created_at: string
}

export interface DataMaskListResponse {
  data: DataMaskListItem[]
  total: number
  limit: number
}

export interface MaskOptions {
  /** Columns to mask. If not provided, auto-detects PII columns. */
  columns?: string[]
  /** Masking strategy: redact, hash, or fake. Default: redact */
  strategy?: MaskingStrategy
  /** Output file format: csv, parquet, json. Default: csv */
  output_format?: 'csv' | 'parquet' | 'json'
}

export async function runDataMask(
  sourceId: string,
  options?: MaskOptions
): Promise<DataMask> {
  return request<DataMask>(`/masks/sources/${sourceId}/mask`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getDataMask(id: string): Promise<DataMask> {
  return request<DataMask>(`/masks/${id}`)
}

export async function listSourceDataMasks(
  sourceId: string,
  params?: { limit?: number }
): Promise<DataMaskListResponse> {
  return request<DataMaskListResponse>(
    `/masks/sources/${sourceId}/masks`,
    { params }
  )
}

export async function getLatestDataMask(sourceId: string): Promise<DataMask> {
  return request<DataMask>(`/masks/sources/${sourceId}/masks/latest`)
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

// ============================================================================
// Glossary (Phase 5)
// ============================================================================

export interface GlossaryCategory {
  id: string
  name: string
  description?: string
  parent_id?: string
  created_at: string
  updated_at: string
  children?: GlossaryCategory[]
}

export interface GlossaryTermSummary {
  id: string
  name: string
  definition: string
}

export interface GlossaryTerm {
  id: string
  name: string
  definition: string
  category_id?: string
  status: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
  created_at: string
  updated_at: string
  category?: GlossaryCategory
  synonyms: GlossaryTermSummary[]
  related_terms: GlossaryTermSummary[]
}

export interface TermRelationship {
  id: string
  source_term_id: string
  target_term_id: string
  relationship_type: 'synonym' | 'related' | 'parent' | 'child'
  created_at: string
  source_term: GlossaryTermSummary
  target_term: GlossaryTermSummary
}

export interface TermHistory {
  id: string
  term_id: string
  field_name: string
  old_value?: string
  new_value?: string
  changed_by?: string
  changed_at: string
}

export interface TermCreate {
  name: string
  definition: string
  category_id?: string
  status?: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
}

export interface TermUpdate {
  name?: string
  definition?: string
  category_id?: string
  status?: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
}

export interface CategoryCreate {
  name: string
  description?: string
  parent_id?: string
}

export interface CategoryUpdate {
  name?: string
  description?: string
  parent_id?: string
}

export interface RelationshipCreate {
  source_term_id: string
  target_term_id: string
  relationship_type: 'synonym' | 'related' | 'parent' | 'child'
}

// Glossary Terms
export async function getTerms(params?: {
  search?: string
  category_id?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<GlossaryTerm[]> {
  return request<GlossaryTerm[]>('/glossary/terms', { params })
}

export async function getTerm(id: string): Promise<GlossaryTerm> {
  return request<GlossaryTerm>(`/glossary/terms/${id}`)
}

export async function createTerm(data: TermCreate): Promise<GlossaryTerm> {
  return request<GlossaryTerm>('/glossary/terms', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateTerm(id: string, data: TermUpdate): Promise<GlossaryTerm> {
  return request<GlossaryTerm>(`/glossary/terms/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteTerm(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/glossary/terms/${id}`, { method: 'DELETE' })
}

export async function getTermHistory(id: string): Promise<TermHistory[]> {
  return request<TermHistory[]>(`/glossary/terms/${id}/history`)
}

export async function getTermRelationships(id: string): Promise<TermRelationship[]> {
  return request<TermRelationship[]>(`/glossary/terms/${id}/relationships`)
}

// Glossary Categories
export async function getCategories(): Promise<GlossaryCategory[]> {
  return request<GlossaryCategory[]>('/glossary/categories')
}

export async function createCategory(data: CategoryCreate): Promise<GlossaryCategory> {
  return request<GlossaryCategory>('/glossary/categories', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCategory(id: string, data: CategoryUpdate): Promise<GlossaryCategory> {
  return request<GlossaryCategory>(`/glossary/categories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteCategory(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/glossary/categories/${id}`, { method: 'DELETE' })
}

// Glossary Relationships
export async function createRelationship(data: RelationshipCreate): Promise<TermRelationship> {
  return request<TermRelationship>('/glossary/relationships', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteRelationship(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/glossary/relationships/${id}`, { method: 'DELETE' })
}

// ============================================================================
// Catalog (Phase 5)
// ============================================================================

export type AssetType = 'table' | 'file' | 'api'
export type SensitivityLevel = 'public' | 'internal' | 'confidential' | 'restricted'

export interface AssetTag {
  id: string
  asset_id: string
  tag_name: string
  tag_value?: string
  created_at: string
}

export interface AssetColumn {
  id: string
  asset_id: string
  name: string
  data_type?: string
  description?: string
  is_nullable: boolean
  is_primary_key: boolean
  term_id?: string
  sensitivity_level?: SensitivityLevel
  created_at: string
  term?: GlossaryTermSummary
}

export interface SourceSummary {
  id: string
  name: string
  type: string
}

export interface CatalogAsset {
  id: string
  name: string
  asset_type: AssetType
  source_id?: string
  description?: string
  owner_id?: string
  quality_score?: number
  created_at: string
  updated_at: string
  source?: SourceSummary
  columns: AssetColumn[]
  tags: AssetTag[]
}

export interface AssetListItem {
  id: string
  name: string
  asset_type: AssetType
  source_id?: string
  source_name?: string
  quality_score?: number
  tag_count: number
  column_count: number
  updated_at: string
}

export interface AssetCreate {
  name: string
  asset_type: AssetType
  source_id?: string
  description?: string
  owner_id?: string
}

export interface AssetUpdate {
  name?: string
  asset_type?: AssetType
  source_id?: string
  description?: string
  owner_id?: string
  quality_score?: number
}

export interface ColumnCreate {
  name: string
  data_type?: string
  description?: string
  is_nullable?: boolean
  is_primary_key?: boolean
  sensitivity_level?: SensitivityLevel
}

export interface ColumnUpdate {
  name?: string
  data_type?: string
  description?: string
  is_nullable?: boolean
  is_primary_key?: boolean
  sensitivity_level?: SensitivityLevel
}

export interface TagCreate {
  tag_name: string
  tag_value?: string
}

// Catalog Assets
export async function getAssets(params?: {
  search?: string
  asset_type?: string
  source_id?: string
  skip?: number
  limit?: number
}): Promise<AssetListItem[]> {
  return request<AssetListItem[]>('/catalog/assets', { params })
}

export async function getAsset(id: string): Promise<CatalogAsset> {
  return request<CatalogAsset>(`/catalog/assets/${id}`)
}

export async function createAsset(data: AssetCreate): Promise<CatalogAsset> {
  return request<CatalogAsset>('/catalog/assets', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateAsset(id: string, data: AssetUpdate): Promise<CatalogAsset> {
  return request<CatalogAsset>(`/catalog/assets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteAsset(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/catalog/assets/${id}`, { method: 'DELETE' })
}

// Asset Columns
export async function getAssetColumns(assetId: string): Promise<AssetColumn[]> {
  return request<AssetColumn[]>(`/catalog/assets/${assetId}/columns`)
}

export async function createColumn(assetId: string, data: ColumnCreate): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/assets/${assetId}/columns`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateColumn(columnId: string, data: ColumnUpdate): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteColumn(columnId: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/catalog/columns/${columnId}`, { method: 'DELETE' })
}

export async function mapColumnToTerm(columnId: string, termId: string): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}/term`, {
    method: 'PUT',
    body: JSON.stringify({ term_id: termId }),
  })
}

export async function unmapColumnFromTerm(columnId: string): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}/term`, { method: 'DELETE' })
}

// Asset Tags
export async function getAssetTags(assetId: string): Promise<AssetTag[]> {
  return request<AssetTag[]>(`/catalog/assets/${assetId}/tags`)
}

export async function addTag(assetId: string, data: TagCreate): Promise<AssetTag> {
  return request<AssetTag>(`/catalog/assets/${assetId}/tags`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function removeTag(tagId: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/catalog/tags/${tagId}`, { method: 'DELETE' })
}

// ============================================================================
// Collaboration (Phase 5)
// ============================================================================

export type ResourceType = 'term' | 'asset' | 'column'
export type ActivityAction = 'created' | 'updated' | 'deleted' | 'commented'

export interface Comment {
  id: string
  resource_type: ResourceType
  resource_id: string
  content: string
  author_id?: string
  parent_id?: string
  created_at: string
  updated_at: string
  replies: Comment[]
}

export interface Activity {
  id: string
  resource_type: string
  resource_id: string
  action: ActivityAction
  actor_id?: string
  description?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface CommentCreate {
  resource_type: ResourceType
  resource_id: string
  content: string
  author_id?: string
  parent_id?: string
}

export interface CommentUpdate {
  content: string
}

// Comments
export async function getComments(
  resourceType: ResourceType,
  resourceId: string
): Promise<Comment[]> {
  return request<Comment[]>('/comments', {
    params: { resource_type: resourceType, resource_id: resourceId },
  })
}

export async function createComment(data: CommentCreate): Promise<Comment> {
  return request<Comment>('/comments', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateComment(id: string, data: CommentUpdate): Promise<Comment> {
  return request<Comment>(`/comments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteComment(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/comments/${id}`, { method: 'DELETE' })
}

// Activities
export async function getActivities(params?: {
  resource_type?: string
  resource_id?: string
  skip?: number
  limit?: number
}): Promise<Activity[]> {
  return request<Activity[]>('/activities', { params })
}

// ============================================================================
// Validators Registry
// ============================================================================

/**
 * Validator categories.
 */
export type ValidatorCategory =
  | 'schema'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  | 'string'
  | 'datetime'
  | 'aggregate'
  | 'cross_table'
  | 'query'
  | 'multi_column'
  | 'table'
  | 'geospatial'
  | 'drift'
  | 'anomaly'

/**
 * Parameter types for validator configuration.
 */
export type ParameterType =
  | 'string'
  | 'string_list'
  | 'integer'
  | 'float'
  | 'boolean'
  | 'select'
  | 'multi_select'
  | 'column'
  | 'column_list'
  | 'schema'
  | 'expression'
  | 'regex'

/**
 * Option for select/multi_select parameters.
 */
export interface SelectOption {
  value: string
  label: string
}

/**
 * Definition of a validator parameter.
 */
export interface ParameterDefinition {
  name: string
  label: string
  type: ParameterType
  description?: string
  required?: boolean
  default?: unknown
  options?: SelectOption[]
  min_value?: number
  max_value?: number
  placeholder?: string
  validation_pattern?: string
  depends_on?: string
  depends_value?: unknown
}

/**
 * Complete definition of a validator including its parameters.
 */
export interface ValidatorDefinition {
  name: string
  display_name: string
  category: ValidatorCategory
  description: string
  parameters: ParameterDefinition[]
  tags: string[]
  severity_default: 'low' | 'medium' | 'high' | 'critical'
  requires_extra?: string
}

/**
 * Category info for UI display.
 */
export interface CategoryInfo {
  value: string
  label: string
}

/**
 * Get all available validators.
 */
export async function listValidators(params?: {
  category?: ValidatorCategory
  search?: string
}): Promise<ValidatorDefinition[]> {
  return request<ValidatorDefinition[]>('/validators', { params })
}

/**
 * Get all validator categories.
 */
export async function listValidatorCategories(): Promise<CategoryInfo[]> {
  return request<CategoryInfo[]>('/validators/categories')
}

/**
 * Get a specific validator by name.
 */
export async function getValidator(name: string): Promise<ValidatorDefinition | null> {
  return request<ValidatorDefinition | null>(`/validators/${name}`)
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
