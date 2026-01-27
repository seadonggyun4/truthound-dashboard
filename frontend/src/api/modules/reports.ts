/**
 * Reports API - Report generation and download.
 */
import { request, ApiError } from '../core'

// ============================================================================
// Types
// ============================================================================

export type ReportFormat = 'html' | 'csv' | 'json' | 'markdown' | 'pdf' | 'junit'
export type ReportTheme = 'light' | 'dark' | 'professional' | 'minimal' | 'high_contrast'
export type ReportLocale =
  | 'en' | 'ko' | 'ja' | 'zh' | 'de' | 'fr' | 'es' | 'pt'
  | 'it' | 'ru' | 'ar' | 'th' | 'vi' | 'id' | 'tr'

export interface LocaleInfo {
  code: ReportLocale
  english_name: string
  native_name: string
  flag: string
  rtl: boolean
}

export interface ReportGenerateOptions {
  format?: ReportFormat
  theme?: ReportTheme
  locale?: ReportLocale
  title?: string
  include_samples?: boolean
  include_statistics?: boolean
}

export interface ReportMetadata {
  title: string
  generated_at: string
  source_name?: string
  source_id?: string
  validation_id?: string
  theme: string
  format: string
}

export interface ReportResponse {
  filename: string
  content_type: string
  size_bytes: number
  generation_time_ms: number
  metadata: ReportMetadata
}

export interface AvailableFormatsResponse {
  formats: string[]
  themes: string[]
  locales?: LocaleInfo[]
}

export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed' | 'expired'

export interface GeneratedReport {
  id: string
  name: string
  description?: string
  source_id?: string
  source_name?: string
  validation_id?: string
  format: ReportFormat
  theme: ReportTheme
  locale: ReportLocale
  status: ReportStatus
  filename?: string
  file_path?: string
  file_size_bytes?: number
  content_type?: string
  generation_time_ms?: number
  error_message?: string
  download_count: number
  expires_at?: string
  is_expired: boolean
  created_at: string
  updated_at: string
}

export interface GeneratedReportListResponse {
  data: GeneratedReport[]
  total: number
  page: number
  page_size: number
}

export interface ReportStatistics {
  total_reports: number
  by_format: Record<string, number>
  by_status: Record<string, number>
  total_downloads: number
  total_size_bytes: number
}

export interface BulkReportGenerateRequest {
  validation_ids: string[]
  format?: ReportFormat
  theme?: ReportTheme
  locale?: ReportLocale
  include_samples?: boolean
  include_statistics?: boolean
}

export interface BulkReportGenerateResponse {
  total_requested: number
  reports_created: number
  reports_failed: number
  reports: GeneratedReport[]
  errors: string[]
}

// ============================================================================
// API Functions
// ============================================================================

const API_BASE = '/api/v1'

export async function getReportFormats(): Promise<AvailableFormatsResponse> {
  return request<AvailableFormatsResponse>('/reports/formats')
}

export async function getReportLocales(): Promise<LocaleInfo[]> {
  return request<LocaleInfo[]>('/reports/locales')
}

export async function generateReportMetadata(
  validationId: string,
  options?: ReportGenerateOptions
): Promise<ReportResponse> {
  return request<ReportResponse>(`/reports/validations/${validationId}/report`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function downloadValidationReport(
  validationId: string,
  options?: {
    format?: ReportFormat
    theme?: ReportTheme
    locale?: ReportLocale
    include_samples?: boolean
    include_statistics?: boolean
  }
): Promise<Blob> {
  const params = new URLSearchParams()
  if (options?.format) params.append('format', options.format)
  if (options?.theme) params.append('theme', options.theme)
  if (options?.locale) params.append('locale', options.locale)
  if (options?.include_samples !== undefined)
    params.append('include_samples', String(options.include_samples))
  if (options?.include_statistics !== undefined)
    params.append('include_statistics', String(options.include_statistics))

  const url = `${API_BASE}/reports/validations/${validationId}/download?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText)
  }

  return response.blob()
}

export async function previewValidationReport(
  validationId: string,
  format: ReportFormat = 'html',
  theme: ReportTheme = 'professional',
  locale: ReportLocale = 'en'
): Promise<string> {
  const params = new URLSearchParams({ format, theme, locale })
  const url = `${API_BASE}/reports/validations/${validationId}/preview?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText)
  }

  return response.text()
}

export async function listReportHistory(params?: {
  search?: string
  format?: ReportFormat
  status?: ReportStatus
  source_id?: string
  include_expired?: boolean
  page?: number
  page_size?: number
}): Promise<GeneratedReportListResponse> {
  return request<GeneratedReportListResponse>('/reports', { params })
}

export async function getReportStatistics(): Promise<ReportStatistics> {
  return request<ReportStatistics>('/reports/statistics')
}

export async function getGeneratedReport(reportId: string): Promise<GeneratedReport> {
  return request<GeneratedReport>(`/reports/${reportId}`)
}

export async function createReportRecord(data: {
  name: string
  description?: string
  source_id?: string
  validation_id?: string
  format?: ReportFormat
  theme?: ReportTheme
  locale?: ReportLocale
  include_samples?: boolean
  include_statistics?: boolean
  generate_immediately?: boolean
}): Promise<GeneratedReport> {
  return request<GeneratedReport>('/reports', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateReportRecord(reportId: string, data: {
  name?: string
  description?: string
}): Promise<GeneratedReport> {
  return request<GeneratedReport>(`/reports/${reportId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteReportRecord(reportId: string): Promise<void> {
  await request<void>(`/reports/${reportId}`, { method: 'DELETE' })
}

export async function downloadSavedReport(reportId: string): Promise<Blob> {
  const url = `${API_BASE}/reports/${reportId}/download`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText)
  }

  return response.blob()
}

export async function generateReportContent(reportId: string): Promise<GeneratedReport> {
  return request<GeneratedReport>(`/reports/${reportId}/generate`, {
    method: 'POST',
  })
}

export async function cleanupExpiredReports(): Promise<{ deleted: number }> {
  return request<{ deleted: number }>('/reports/cleanup', { method: 'POST' })
}

export async function generateBulkReports(data: BulkReportGenerateRequest): Promise<BulkReportGenerateResponse> {
  return request<BulkReportGenerateResponse>('/reports/bulk', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
