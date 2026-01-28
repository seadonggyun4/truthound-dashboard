/**
 * Quality Reporter API - Quality scoring and reporting for validation rules.
 *
 * Based on truthound's QualityReporter module:
 * - Rule quality scoring (F1, precision, recall, accuracy)
 * - Quality levels (excellent, good, acceptable, poor, unacceptable)
 * - Multiple report formats (console, json, html, markdown, junit)
 * - Filtering and comparison capabilities
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export type QualityLevel =
  | 'excellent'
  | 'good'
  | 'acceptable'
  | 'poor'
  | 'unacceptable'

export type QualityReportFormat =
  | 'console'
  | 'json'
  | 'html'
  | 'markdown'
  | 'junit'

export type QualityReportStatus =
  | 'pending'
  | 'generating'
  | 'completed'
  | 'failed'

export type ReportSortOrder =
  | 'f1_desc'
  | 'f1_asc'
  | 'precision_desc'
  | 'precision_asc'
  | 'recall_desc'
  | 'recall_asc'
  | 'level_desc'
  | 'level_asc'
  | 'name_asc'
  | 'name_desc'

// ============================================================================
// Request/Response Types
// ============================================================================

export interface ConfusionMatrix {
  true_positive: number
  true_negative: number
  false_positive: number
  false_negative: number
  precision?: number
  recall?: number
  f1_score?: number
  accuracy?: number
}

export interface QualityMetrics {
  f1_score: number
  precision: number
  recall: number
  accuracy: number
  confidence: number
  quality_level: QualityLevel
}

export interface QualityThresholds {
  excellent: number
  good: number
  acceptable: number
  poor: number
}

export interface QualityScore {
  rule_name: string
  rule_type?: string
  column?: string
  metrics: QualityMetrics
  confusion_matrix?: ConfusionMatrix
  test_sample_size: number
  evaluation_time_ms: number
  recommendation?: string
  should_use: boolean
  issues: Array<Record<string, unknown>>
}

export interface QualityStatistics {
  total_count: number
  excellent_count: number
  good_count: number
  acceptable_count: number
  poor_count: number
  unacceptable_count: number
  should_use_count: number
  avg_f1: number
  min_f1: number
  max_f1: number
  avg_precision: number
  avg_recall: number
  avg_confidence: number
}

export interface QualityLevelDistribution {
  level: QualityLevel
  count: number
  percentage: number
}

// Request Types
export interface QualityScoreRequest {
  source_id?: string
  validation_id?: string
  rule_names?: string[]
  sample_size?: number
  thresholds?: QualityThresholds
}

export interface QualityFilterRequest {
  min_level?: QualityLevel
  max_level?: QualityLevel
  min_f1?: number
  max_f1?: number
  min_confidence?: number
  should_use_only?: boolean
  include_columns?: string[]
  exclude_columns?: string[]
  rule_types?: string[]
}

export interface QualityReportConfig {
  title?: string
  description?: string
  include_metrics?: boolean
  include_confusion_matrix?: boolean
  include_recommendations?: boolean
  include_statistics?: boolean
  include_summary?: boolean
  include_charts?: boolean
  metric_precision?: number
  percentage_format?: boolean
  sort_order?: ReportSortOrder
  max_scores?: number
  theme?: 'light' | 'dark' | 'professional'
}

export interface QualityReportGenerateRequest {
  source_id?: string
  validation_id?: string
  format?: QualityReportFormat
  config?: QualityReportConfig
  filter?: QualityFilterRequest
  score_rules?: boolean
  sample_size?: number
}

export interface QualityCompareRequest {
  score_ids?: string[]
  source_ids?: string[]
  sort_by?: 'f1_score' | 'precision' | 'recall' | 'confidence'
  descending?: boolean
  group_by?: 'column' | 'level' | 'rule_type'
  max_results?: number
}

// Response Types
export interface QualityScoreResponse {
  id: string
  source_id: string
  source_name?: string
  validation_id?: string
  status: QualityReportStatus
  scores: QualityScore[]
  statistics?: QualityStatistics
  level_distribution?: QualityLevelDistribution[]
  sample_size: number
  evaluation_time_ms: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface QualityReportResponse {
  id: string
  source_id?: string
  source_name?: string
  validation_id?: string
  format: QualityReportFormat
  status: QualityReportStatus
  filename?: string
  file_path?: string
  file_size_bytes?: number
  content_type?: string
  generation_time_ms?: number
  scores_count: number
  statistics?: QualityStatistics
  error_message?: string
  download_count: number
  expires_at?: string
  created_at: string
  updated_at: string
}

export interface QualityCompareResponse {
  scores: QualityScore[]
  ranked_by: string
  best_rule?: QualityScore
  worst_rule?: QualityScore
  groups?: Record<string, QualityScore[]>
  statistics?: QualityStatistics
}

export interface QualitySummaryResponse {
  total_rules: number
  statistics: QualityStatistics
  level_distribution: QualityLevelDistribution[]
  recommendations: {
    should_use: number
    should_not_use: number
  }
  metric_averages: {
    f1_score: { avg: number; min: number; max: number }
    precision: { avg: number; min: number; max: number }
    recall: { avg: number; min: number; max: number }
    confidence: { avg: number; min: number; max: number }
  }
}

export interface QualityFormatsResponse {
  formats: string[]
  sort_orders: string[]
  themes: string[]
  default_thresholds: QualityThresholds
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get available quality report formats and options.
 */
export async function getQualityFormats(): Promise<QualityFormatsResponse> {
  return request<QualityFormatsResponse>('/quality/formats')
}

/**
 * Score validation rules for a source.
 */
export async function scoreSource(
  sourceId: string,
  options?: QualityScoreRequest
): Promise<QualityScoreResponse> {
  return request<QualityScoreResponse>(`/quality/sources/${sourceId}/score`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

/**
 * Generate a quality report for a source.
 */
export async function generateQualityReport(
  sourceId: string,
  options?: QualityReportGenerateRequest
): Promise<QualityReportResponse> {
  return request<QualityReportResponse>(`/quality/sources/${sourceId}/report`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

/**
 * Download quality report as file.
 */
export async function downloadQualityReport(
  sourceId: string,
  options?: {
    format?: QualityReportFormat
    title?: string
    include_charts?: boolean
    theme?: string
    max_scores?: number
  }
): Promise<Blob> {
  const params = new URLSearchParams()
  if (options?.format) params.append('format', options.format)
  if (options?.title) params.append('title', options.title)
  if (options?.include_charts !== undefined) {
    params.append('include_charts', String(options.include_charts))
  }
  if (options?.theme) params.append('theme', options.theme)
  if (options?.max_scores) {
    params.append('max_scores', String(options.max_scores))
  }

  const url = `/api/v1/quality/sources/${sourceId}/report/download?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Failed to download report: ${response.statusText}`)
  }

  return response.blob()
}

/**
 * Preview quality report inline.
 */
export async function previewQualityReport(
  sourceId: string,
  options?: {
    format?: QualityReportFormat
    theme?: string
    max_scores?: number
  }
): Promise<string> {
  const params = new URLSearchParams()
  if (options?.format) params.append('format', options.format)
  if (options?.theme) params.append('theme', options.theme)
  if (options?.max_scores) {
    params.append('max_scores', String(options.max_scores))
  }

  const url = `/api/v1/quality/sources/${sourceId}/report/preview?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Failed to preview report: ${response.statusText}`)
  }

  return response.text()
}

/**
 * Get quality summary for a source.
 */
export async function getQualitySummary(
  sourceId: string,
  options?: {
    validation_id?: string
    sample_size?: number
  }
): Promise<QualitySummaryResponse> {
  const params: Record<string, string> = {}
  if (options?.validation_id) params.validation_id = options.validation_id
  if (options?.sample_size) params.sample_size = String(options.sample_size)

  return request<QualitySummaryResponse>(
    `/quality/sources/${sourceId}/summary`,
    { params }
  )
}

/**
 * Compare quality scores across sources.
 */
export async function compareQualityScores(
  options: QualityCompareRequest
): Promise<QualityCompareResponse> {
  return request<QualityCompareResponse>('/quality/compare', {
    method: 'POST',
    body: JSON.stringify(options),
  })
}

/**
 * Filter quality scores by criteria.
 */
export async function filterQualityScores(
  sourceId: string,
  filter: QualityFilterRequest
): Promise<QualityScore[]> {
  return request<QualityScore[]>('/quality/filter', {
    method: 'POST',
    params: { source_id: sourceId },
    body: JSON.stringify(filter),
  })
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get color for quality level.
 */
export function getQualityLevelColor(level: QualityLevel): string {
  const colors: Record<QualityLevel, string> = {
    excellent: '#22c55e', // green-500
    good: '#3b82f6', // blue-500
    acceptable: '#f59e0b', // amber-500
    poor: '#ef4444', // red-500
    unacceptable: '#991b1b', // red-800
  }
  return colors[level]
}

/**
 * Get badge variant for quality level.
 */
export function getQualityLevelVariant(
  level: QualityLevel
): 'default' | 'secondary' | 'destructive' | 'outline' {
  const variants: Record<
    QualityLevel,
    'default' | 'secondary' | 'destructive' | 'outline'
  > = {
    excellent: 'default',
    good: 'default',
    acceptable: 'secondary',
    poor: 'destructive',
    unacceptable: 'destructive',
  }
  return variants[level]
}

/**
 * Format quality score as percentage.
 */
export function formatQualityScore(
  score: number,
  precision: number = 1
): string {
  return `${(score * 100).toFixed(precision)}%`
}

/**
 * Get quality level from F1 score using thresholds.
 */
export function getQualityLevelFromScore(
  f1Score: number,
  thresholds?: QualityThresholds
): QualityLevel {
  const t = thresholds || {
    excellent: 0.9,
    good: 0.7,
    acceptable: 0.5,
    poor: 0.3,
  }

  if (f1Score >= t.excellent) return 'excellent'
  if (f1Score >= t.good) return 'good'
  if (f1Score >= t.acceptable) return 'acceptable'
  if (f1Score >= t.poor) return 'poor'
  return 'unacceptable'
}
