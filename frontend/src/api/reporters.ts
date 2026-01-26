/**
 * Reporter API client module.
 *
 * Provides typed API functions for the truthound reporter system.
 * Based on truthound reporters documentation with support for:
 * - Multiple formats (HTML, JSON, CSV, Markdown, PDF, JUnit, YAML, NDJSON, Table)
 * - CI platform reporters (GitHub Actions, GitLab CI, Azure DevOps, Jenkins)
 * - i18n (15 languages)
 * - Themes (light, dark, professional, minimal, high_contrast)
 * - Custom reporters via SDK (decorator or builder pattern)
 * - Report history management
 * - ValidationResult-based full reporter functionality
 */

import type {
  ReportFormatType,
  ReportThemeType,
  ReportLocale,
  ReporterConfig,
  GeneratedReport,
  ReportStatistics,
  ReportCreateOptions,
  ReportUpdateOptions,
  AvailableFormatsResponse,
  ReportListResponse,
  BulkReportRequest,
  BulkReportResponse,
  CustomReporter,
  CustomReporterCreateOptions,
  LocaleInfo,
  ReportOutput,
  CIPlatformType,
  ValidationResult,
  GenerateReportRequest,
  GenerateReportResponse,
} from '@/types/reporters'

// Re-export types for convenience
export type {
  ReportFormatType,
  ReportThemeType,
  ReportLocale,
  ReporterConfig,
  GeneratedReport,
  ReportStatistics,
  CustomReporter,
  LocaleInfo,
  CIPlatformType,
  ValidationResult,
}

// =============================================================================
// API Configuration
// =============================================================================

const API_BASE = '/api/v1'

/**
 * API Error class for typed error handling.
 */
export class ReporterApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail?: string
  ) {
    super(detail || `${status} ${statusText}`)
    this.name = 'ReporterApiError'
  }
}

/**
 * Generic request function with error handling.
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    let detail: string | undefined
    try {
      const errorData = await response.json()
      detail = errorData.detail
    } catch {
      // Ignore JSON parse errors
    }
    throw new ReporterApiError(response.status, response.statusText, detail)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

// =============================================================================
// Format & Configuration API
// =============================================================================

/**
 * Get available report formats, themes, and locales.
 */
export async function getAvailableFormats(): Promise<AvailableFormatsResponse> {
  return request<AvailableFormatsResponse>('/reports/formats')
}

/**
 * Get available report locales (15 languages).
 */
export async function getAvailableLocales(): Promise<LocaleInfo[]> {
  return request<LocaleInfo[]>('/reports/locales')
}

// =============================================================================
// Report Generation API
// =============================================================================

/**
 * Options for generating a report.
 */
export interface ReportGenerateOptions extends ReporterConfig {
  /** Custom reporter ID (for using custom reporters) */
  reporterId?: string
}

/**
 * Report metadata response.
 */
export interface ReportMetadataResponse {
  filename: string
  contentType: string
  sizeBytes: number
  generationTimeMs: number
  metadata: {
    title: string
    generatedAt: string
    sourceName?: string
    sourceId?: string
    validationId?: string
    theme: string
    format: string
  }
}

/**
 * Generate report metadata (use download for actual content).
 */
export async function generateReportMetadata(
  validationId: string,
  options?: ReportGenerateOptions
): Promise<ReportMetadataResponse> {
  const body = options
    ? {
        format: options.theme,
        theme: options.theme,
        locale: options.locale,
        title: options.title,
        include_samples: options.includeSamples,
        include_statistics: options.includeStatistics,
        custom_metadata: options.customOptions,
      }
    : {}

  const response = await request<{
    filename: string
    content_type: string
    size_bytes: number
    generation_time_ms: number
    metadata: {
      title: string
      generated_at: string
      source_name?: string
      source_id?: string
      validation_id?: string
      theme: string
      format: string
    }
  }>(`/reports/validations/${validationId}/report`, {
    method: 'POST',
    body: JSON.stringify(body),
  })

  return {
    filename: response.filename,
    contentType: response.content_type,
    sizeBytes: response.size_bytes,
    generationTimeMs: response.generation_time_ms,
    metadata: {
      title: response.metadata.title,
      generatedAt: response.metadata.generated_at,
      sourceName: response.metadata.source_name,
      sourceId: response.metadata.source_id,
      validationId: response.metadata.validation_id,
      theme: response.metadata.theme,
      format: response.metadata.format,
    },
  }
}

/**
 * Download validation report as file.
 */
export async function downloadReport(
  validationId: string,
  options?: {
    format?: ReportFormatType
    theme?: ReportThemeType
    locale?: ReportLocale
    includeSamples?: boolean
    includeStatistics?: boolean
  }
): Promise<Blob> {
  const params = new URLSearchParams()
  if (options?.format) params.append('format', options.format)
  if (options?.theme) params.append('theme', options.theme)
  if (options?.locale) params.append('locale', options.locale)
  if (options?.includeSamples !== undefined)
    params.append('include_samples', String(options.includeSamples))
  if (options?.includeStatistics !== undefined)
    params.append('include_statistics', String(options.includeStatistics))

  const url = `${API_BASE}/reports/validations/${validationId}/download?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ReporterApiError(response.status, response.statusText)
  }

  return response.blob()
}

/**
 * Preview validation report (inline viewing).
 */
export async function previewReport(
  validationId: string,
  options?: {
    format?: ReportFormatType
    theme?: ReportThemeType
    locale?: ReportLocale
  }
): Promise<string> {
  const params = new URLSearchParams()
  if (options?.format) params.append('format', options.format)
  if (options?.theme) params.append('theme', options.theme ?? 'professional')
  if (options?.locale) params.append('locale', options.locale ?? 'en')

  const url = `${API_BASE}/reports/validations/${validationId}/preview?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ReporterApiError(response.status, response.statusText)
  }

  return response.text()
}

// =============================================================================
// Report History API
// =============================================================================

/**
 * Query parameters for listing report history.
 */
export interface ReportHistoryQuery {
  sourceId?: string
  validationId?: string
  reporterId?: string
  format?: string
  status?: string
  includeExpired?: boolean
  search?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  page?: number
  pageSize?: number
}

/**
 * List generated reports with filtering and pagination.
 */
export async function listReportHistory(
  query?: ReportHistoryQuery
): Promise<ReportListResponse> {
  const params = new URLSearchParams()

  if (query) {
    if (query.sourceId) params.append('source_id', query.sourceId)
    if (query.validationId) params.append('validation_id', query.validationId)
    if (query.reporterId) params.append('reporter_id', query.reporterId)
    if (query.format) params.append('format', query.format)
    if (query.status) params.append('status', query.status)
    if (query.includeExpired !== undefined)
      params.append('include_expired', String(query.includeExpired))
    if (query.search) params.append('search', query.search)
    if (query.sortBy) params.append('sort_by', query.sortBy)
    if (query.sortOrder) params.append('sort_order', query.sortOrder)
    if (query.page !== undefined) params.append('page', String(query.page))
    if (query.pageSize !== undefined) params.append('page_size', String(query.pageSize))
  }

  const response = await request<{
    items: Array<{
      id: string
      name: string
      format: string
      description?: string
      theme?: string
      locale?: string
      config?: Record<string, unknown>
      metadata?: Record<string, unknown>
      validation_id?: string
      source_id?: string
      reporter_id?: string
      status: string
      file_path?: string
      file_size?: number
      generation_time_ms?: number
      downloaded_count: number
      expires_at?: string
      created_at: string
      updated_at: string
      source_name?: string
      reporter_name?: string
      download_url?: string
    }>
    total: number
    page: number
    page_size: number
  }>(`/reports/history?${params}`)

  return {
    items: response.items.map(transformReportResponse),
    total: response.total,
    page: response.page,
    pageSize: response.page_size,
  }
}

/**
 * Get report statistics.
 */
export async function getReportStatistics(): Promise<ReportStatistics> {
  const response = await request<{
    total_reports: number
    total_size_bytes: number
    reports_by_format: Record<string, number>
    reports_by_status: Record<string, number>
    total_downloads: number
    avg_generation_time_ms?: number
    expired_count: number
    reporters_used: number
  }>('/reports/history/statistics')

  return {
    totalReports: response.total_reports,
    totalSizeBytes: response.total_size_bytes,
    reportsByFormat: response.reports_by_format,
    reportsByStatus: response.reports_by_status,
    totalDownloads: response.total_downloads,
    avgGenerationTimeMs: response.avg_generation_time_ms,
    expiredCount: response.expired_count,
    reportersUsed: response.reporters_used,
  }
}

/**
 * Get a specific report by ID.
 */
export async function getReport(reportId: string): Promise<GeneratedReport> {
  const response = await request<{
    id: string
    name: string
    format: string
    description?: string
    theme?: string
    locale?: string
    config?: Record<string, unknown>
    metadata?: Record<string, unknown>
    validation_id?: string
    source_id?: string
    reporter_id?: string
    status: string
    file_path?: string
    file_size?: number
    generation_time_ms?: number
    downloaded_count: number
    expires_at?: string
    created_at: string
    updated_at: string
    source_name?: string
    reporter_name?: string
    download_url?: string
  }>(`/reports/history/${reportId}`)

  return transformReportResponse(response)
}

/**
 * Create a new report record.
 */
export async function createReport(
  options: ReportCreateOptions
): Promise<GeneratedReport> {
  const body = {
    name: options.name,
    format: options.format,
    validation_id: options.validationId,
    source_id: options.sourceId,
    reporter_id: options.reporterId,
    description: options.description,
    theme: options.theme,
    locale: options.locale,
    config: options.config,
    metadata: options.metadata,
    expires_in_days: options.expiresInDays,
  }

  const response = await request<{
    id: string
    name: string
    format: string
    description?: string
    theme?: string
    locale?: string
    config?: Record<string, unknown>
    metadata?: Record<string, unknown>
    validation_id?: string
    source_id?: string
    reporter_id?: string
    status: string
    file_path?: string
    file_size?: number
    generation_time_ms?: number
    downloaded_count: number
    expires_at?: string
    created_at: string
    updated_at: string
    source_name?: string
    reporter_name?: string
    download_url?: string
  }>('/reports/history', {
    method: 'POST',
    body: JSON.stringify(body),
  })

  return transformReportResponse(response)
}

/**
 * Update a report record.
 */
export async function updateReport(
  reportId: string,
  options: ReportUpdateOptions
): Promise<GeneratedReport> {
  const response = await request<{
    id: string
    name: string
    format: string
    description?: string
    theme?: string
    locale?: string
    config?: Record<string, unknown>
    metadata?: Record<string, unknown>
    validation_id?: string
    source_id?: string
    reporter_id?: string
    status: string
    file_path?: string
    file_size?: number
    generation_time_ms?: number
    downloaded_count: number
    expires_at?: string
    created_at: string
    updated_at: string
    source_name?: string
    reporter_name?: string
    download_url?: string
  }>(`/reports/history/${reportId}`, {
    method: 'PATCH',
    body: JSON.stringify(options),
  })

  return transformReportResponse(response)
}

/**
 * Delete a report record.
 */
export async function deleteReport(reportId: string): Promise<void> {
  await request<void>(`/reports/history/${reportId}`, { method: 'DELETE' })
}

/**
 * Download a saved report.
 */
export async function downloadSavedReport(reportId: string): Promise<Blob> {
  const url = `${API_BASE}/reports/history/${reportId}/download`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ReporterApiError(response.status, response.statusText)
  }

  return response.blob()
}

/**
 * Generate content for an existing report record.
 */
export async function generateReportContent(
  reportId: string
): Promise<GeneratedReport> {
  const response = await request<{
    id: string
    name: string
    format: string
    description?: string
    theme?: string
    locale?: string
    config?: Record<string, unknown>
    metadata?: Record<string, unknown>
    validation_id?: string
    source_id?: string
    reporter_id?: string
    status: string
    file_path?: string
    file_size?: number
    generation_time_ms?: number
    downloaded_count: number
    expires_at?: string
    created_at: string
    updated_at: string
    source_name?: string
    reporter_name?: string
    download_url?: string
  }>(`/reports/history/${reportId}/generate`, { method: 'POST' })

  return transformReportResponse(response)
}

/**
 * Clean up expired reports.
 */
export async function cleanupExpiredReports(): Promise<{ deleted: number }> {
  return request<{ deleted: number }>('/reports/history/cleanup', { method: 'POST' })
}

/**
 * Generate reports in bulk.
 */
export async function generateBulkReports(
  request_: BulkReportRequest
): Promise<BulkReportResponse> {
  const body = {
    validation_ids: request_.validationIds,
    format: request_.format,
    theme: request_.theme,
    locale: request_.locale,
    reporter_id: request_.reporterId,
    config: request_.config,
    save_to_history: request_.saveToHistory,
    expires_in_days: request_.expiresInDays,
  }

  const response = await request<{
    total: number
    successful: number
    failed: number
    reports: Array<{
      id: string
      name: string
      format: string
      description?: string
      theme?: string
      locale?: string
      config?: Record<string, unknown>
      metadata?: Record<string, unknown>
      validation_id?: string
      source_id?: string
      reporter_id?: string
      status: string
      file_path?: string
      file_size?: number
      generation_time_ms?: number
      downloaded_count: number
      expires_at?: string
      created_at: string
      updated_at: string
      source_name?: string
      reporter_name?: string
      download_url?: string
    }>
    errors: Array<{ validation_id: string; error: string }>
  }>('/reports/bulk', {
    method: 'POST',
    body: JSON.stringify(body),
  })

  return {
    total: response.total,
    successful: response.successful,
    failed: response.failed,
    reports: response.reports.map(transformReportResponse),
    errors: response.errors.map((e) => ({
      validationId: e.validation_id,
      error: e.error,
    })),
  }
}

// =============================================================================
// Custom Reporters API
// =============================================================================

/**
 * List custom reporters.
 */
export async function listCustomReporters(params?: {
  pluginId?: string
  enabled?: boolean
  search?: string
  offset?: number
  limit?: number
}): Promise<{ items: CustomReporter[]; total: number }> {
  const queryParams = new URLSearchParams()

  if (params) {
    if (params.pluginId) queryParams.append('plugin_id', params.pluginId)
    if (params.enabled !== undefined) queryParams.append('enabled', String(params.enabled))
    if (params.search) queryParams.append('search', params.search)
    if (params.offset !== undefined) queryParams.append('offset', String(params.offset))
    if (params.limit !== undefined) queryParams.append('limit', String(params.limit))
  }

  const response = await request<{
    items: Array<{
      id: string
      plugin_id?: string
      name: string
      display_name: string
      description?: string
      version: string
      category?: string
      file_extension: string
      content_type: string
      supports_theme: boolean
      supports_i18n: boolean
      template?: string
      code?: string
      config_schema?: Record<string, unknown>
      default_config?: Record<string, unknown>
      enabled: boolean
      built_in: boolean
      created_at: string
      updated_at: string
    }>
    total: number
  }>(`/reporters/custom?${queryParams}`)

  return {
    items: response.items.map(transformCustomReporterResponse),
    total: response.total,
  }
}

/**
 * Get reporter templates.
 */
export async function getReporterTemplates(): Promise<{
  codeTemplate: string
  jinja2Template: string
}> {
  const response = await request<{
    code_template: string
    jinja2_template: string
  }>('/reporters/custom/templates')

  return {
    codeTemplate: response.code_template,
    jinja2Template: response.jinja2_template,
  }
}

/**
 * Get a custom reporter by ID.
 */
export async function getCustomReporter(reporterId: string): Promise<CustomReporter> {
  const response = await request<{
    id: string
    plugin_id?: string
    name: string
    display_name: string
    description?: string
    version: string
    category?: string
    file_extension: string
    content_type: string
    supports_theme: boolean
    supports_i18n: boolean
    template?: string
    code?: string
    config_schema?: Record<string, unknown>
    default_config?: Record<string, unknown>
    enabled: boolean
    built_in: boolean
    created_at: string
    updated_at: string
  }>(`/reporters/custom/${reporterId}`)

  return transformCustomReporterResponse(response)
}

/**
 * Create a custom reporter.
 */
export async function createCustomReporter(
  options: CustomReporterCreateOptions
): Promise<CustomReporter> {
  const body = {
    name: options.name,
    display_name: options.displayName,
    description: options.description,
    version: options.version ?? '1.0.0',
    category: options.category,
    file_extension: options.fileExtension,
    content_type: options.contentType,
    supports_theme: options.supportsTheme ?? false,
    supports_i18n: options.supportsI18n ?? false,
    template: options.template,
    code: options.code,
    config_schema: options.configSchema,
    default_config: options.defaultConfig,
  }

  const response = await request<{
    id: string
    plugin_id?: string
    name: string
    display_name: string
    description?: string
    version: string
    category?: string
    file_extension: string
    content_type: string
    supports_theme: boolean
    supports_i18n: boolean
    template?: string
    code?: string
    config_schema?: Record<string, unknown>
    default_config?: Record<string, unknown>
    enabled: boolean
    built_in: boolean
    created_at: string
    updated_at: string
  }>('/reporters/custom', {
    method: 'POST',
    body: JSON.stringify(body),
  })

  return transformCustomReporterResponse(response)
}

/**
 * Update a custom reporter.
 */
export async function updateCustomReporter(
  reporterId: string,
  options: Partial<CustomReporterCreateOptions>
): Promise<CustomReporter> {
  const body: Record<string, unknown> = {}

  if (options.name !== undefined) body.name = options.name
  if (options.displayName !== undefined) body.display_name = options.displayName
  if (options.description !== undefined) body.description = options.description
  if (options.version !== undefined) body.version = options.version
  if (options.category !== undefined) body.category = options.category
  if (options.fileExtension !== undefined) body.file_extension = options.fileExtension
  if (options.contentType !== undefined) body.content_type = options.contentType
  if (options.supportsTheme !== undefined) body.supports_theme = options.supportsTheme
  if (options.supportsI18n !== undefined) body.supports_i18n = options.supportsI18n
  if (options.template !== undefined) body.template = options.template
  if (options.code !== undefined) body.code = options.code
  if (options.configSchema !== undefined) body.config_schema = options.configSchema
  if (options.defaultConfig !== undefined) body.default_config = options.defaultConfig

  const response = await request<{
    id: string
    plugin_id?: string
    name: string
    display_name: string
    description?: string
    version: string
    category?: string
    file_extension: string
    content_type: string
    supports_theme: boolean
    supports_i18n: boolean
    template?: string
    code?: string
    config_schema?: Record<string, unknown>
    default_config?: Record<string, unknown>
    enabled: boolean
    built_in: boolean
    created_at: string
    updated_at: string
  }>(`/reporters/custom/${reporterId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

  return transformCustomReporterResponse(response)
}

/**
 * Delete a custom reporter.
 */
export async function deleteCustomReporter(reporterId: string): Promise<void> {
  await request<void>(`/reporters/custom/${reporterId}`, { method: 'DELETE' })
}

/**
 * Preview a custom reporter output.
 */
export async function previewCustomReporter(options: {
  template?: string
  code?: string
  validationId?: string
  config?: Record<string, unknown>
  format?: string
}): Promise<{
  success: boolean
  reportId?: string
  downloadUrl?: string
  previewHtml?: string
  error?: string
}> {
  const response = await request<{
    success: boolean
    report_id?: string
    download_url?: string
    preview_html?: string
    error?: string
  }>('/reporters/custom/preview', {
    method: 'POST',
    body: JSON.stringify({
      template: options.template,
      code: options.code,
      validation_id: options.validationId,
      config: options.config,
      format: options.format,
    }),
  })

  return {
    success: response.success,
    reportId: response.report_id,
    downloadUrl: response.download_url,
    previewHtml: response.preview_html,
    error: response.error,
  }
}

/**
 * Generate report using a custom reporter.
 */
export async function generateWithCustomReporter(
  reporterId: string,
  options: {
    outputFormat: string
    config?: Record<string, unknown>
    validationId?: string
    data?: Record<string, unknown>
    sourceIds?: string[]
  }
): Promise<{
  success: boolean
  reportId?: string
  downloadUrl?: string
  previewHtml?: string
  error?: string
}> {
  const response = await request<{
    success: boolean
    report_id?: string
    download_url?: string
    preview_html?: string
    error?: string
  }>(`/reporters/custom/${reporterId}/generate`, {
    method: 'POST',
    body: JSON.stringify({
      output_format: options.outputFormat,
      config: options.config,
      validation_id: options.validationId,
      data: options.data,
      source_ids: options.sourceIds,
    }),
  })

  return {
    success: response.success,
    reportId: response.report_id,
    downloadUrl: response.download_url,
    previewHtml: response.preview_html,
    error: response.error,
  }
}

/**
 * Download report generated by custom reporter.
 */
export async function downloadCustomReporterOutput(
  reporterId: string,
  validationId: string,
  options?: {
    outputFormat?: string
    config?: Record<string, unknown>
  }
): Promise<Blob> {
  const params = new URLSearchParams()
  params.append('validation_id', validationId)
  if (options?.outputFormat) params.append('output_format', options.outputFormat)
  if (options?.config) params.append('config', JSON.stringify(options.config))

  const url = `${API_BASE}/reporters/custom/${reporterId}/download?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ReporterApiError(response.status, response.statusText)
  }

  return response.blob()
}

// =============================================================================
// Transform Functions
// =============================================================================

/**
 * Transform API response to GeneratedReport type.
 */
function transformReportResponse(response: {
  id: string
  name: string
  format: string
  description?: string
  theme?: string
  locale?: string
  config?: Record<string, unknown>
  metadata?: Record<string, unknown>
  validation_id?: string
  source_id?: string
  reporter_id?: string
  status: string
  file_path?: string
  file_size?: number
  generation_time_ms?: number
  downloaded_count: number
  expires_at?: string
  created_at: string
  updated_at: string
  source_name?: string
  reporter_name?: string
  download_url?: string
}): GeneratedReport {
  return {
    id: response.id,
    name: response.name,
    format: response.format as ReportFormatType,
    description: response.description,
    theme: response.theme as ReportThemeType | undefined,
    locale: response.locale as ReportLocale | undefined,
    config: response.config,
    metadata: response.metadata,
    validationId: response.validation_id,
    sourceId: response.source_id,
    reporterId: response.reporter_id,
    status: response.status as GeneratedReport['status'],
    filePath: response.file_path,
    fileSize: response.file_size,
    generationTimeMs: response.generation_time_ms,
    downloadCount: response.downloaded_count,
    expiresAt: response.expires_at,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
    sourceName: response.source_name,
    reporterName: response.reporter_name,
    downloadUrl: response.download_url,
  }
}

/**
 * Transform API response to CustomReporter type.
 */
function transformCustomReporterResponse(response: {
  id: string
  plugin_id?: string
  name: string
  display_name: string
  description?: string
  version: string
  category?: string
  file_extension: string
  content_type: string
  supports_theme: boolean
  supports_i18n: boolean
  template?: string
  code?: string
  config_schema?: Record<string, unknown>
  default_config?: Record<string, unknown>
  enabled: boolean
  built_in: boolean
  created_at: string
  updated_at: string
}): CustomReporter {
  return {
    id: response.id,
    pluginId: response.plugin_id,
    name: response.name,
    displayName: response.display_name,
    description: response.description,
    version: response.version,
    category: response.category,
    fileExtension: response.file_extension,
    contentType: response.content_type,
    supportsTheme: response.supports_theme,
    supportsI18n: response.supports_i18n,
    template: response.template,
    code: response.code,
    configSchema: response.config_schema,
    defaultConfig: response.default_config,
    enabled: response.enabled,
    builtIn: response.built_in,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
  }
}
