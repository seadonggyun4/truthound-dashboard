/**
 * Plugins API - Plugin marketplace and custom validators/reporters.
 */
import { request, ApiError } from '../core'
import type { PaginatedResponse } from '../core'

// ============================================================================
// Types
// ============================================================================

export type PluginType = 'validator' | 'reporter' | 'connector' | 'transformer'
export type PluginStatus = 'available' | 'installed' | 'enabled' | 'disabled' | 'update_available' | 'error'
export type PluginSource = 'official' | 'community' | 'local' | 'private'
export type SecurityLevel = 'trusted' | 'verified' | 'unverified' | 'sandboxed'
export type ValidatorParamType = 'string' | 'integer' | 'float' | 'boolean' | 'column' | 'column_list' | 'select' | 'multi_select' | 'regex' | 'json'
export type ReporterOutputFormat = 'html' | 'json' | 'csv' | 'markdown' | 'custom'

export interface PluginAuthor {
  name: string
  email?: string
  url?: string
}

export interface PluginDependency {
  plugin_id: string
  version_constraint: string
  optional?: boolean
}

export interface Plugin {
  id: string
  name: string
  display_name: string
  description: string
  version: string
  latest_version?: string
  type: PluginType
  source: PluginSource
  status: PluginStatus
  security_level: SecurityLevel
  author?: PluginAuthor
  license?: string
  homepage?: string
  repository?: string
  keywords: string[]
  categories: string[]
  dependencies: PluginDependency[]
  permissions: string[]
  python_version?: string
  dashboard_version?: string
  icon_url?: string
  banner_url?: string
  documentation_url?: string
  changelog?: string
  readme?: string
  is_enabled: boolean
  install_count: number
  rating?: number
  rating_count: number
  validators_count: number
  reporters_count: number
  installed_at?: string
  last_updated?: string
  created_at: string
  updated_at: string
}

export type PluginListResponse = PaginatedResponse<Plugin>

export interface MarketplaceStats {
  total_plugins: number
  total_validators: number
  total_reporters: number
  total_installs: number
  categories: Array<{
    name: string
    display_name: string
    description: string
    icon?: string
    plugin_count: number
  }>
  featured_plugins: Plugin[]
  popular_plugins: Plugin[]
  recent_plugins: Plugin[]
}

export interface PluginInstallResponse {
  success: boolean
  plugin_id: string
  installed_version?: string
  message?: string
  warnings: string[]
}

export interface PluginUninstallResponse {
  success: boolean
  plugin_id: string
  message?: string
}

export interface ValidatorParamDefinition {
  name: string
  type: ValidatorParamType
  description: string
  required?: boolean
  default?: unknown
  options?: string[]
  min_value?: number
  max_value?: number
  pattern?: string
}

export interface ValidatorTestCase {
  name: string
  input: Record<string, unknown>
  expected_passed: boolean
  [key: string]: unknown
}

export interface CustomValidator {
  id: string
  plugin_id?: string
  name: string
  display_name: string
  description: string
  category: string
  severity: 'error' | 'warning' | 'info'
  tags: string[]
  parameters: ValidatorParamDefinition[]
  code: string
  test_cases: ValidatorTestCase[]
  is_enabled: boolean
  is_verified: boolean
  usage_count: number
  last_used_at?: string
  created_at: string
  updated_at: string
}

export type CustomValidatorListResponse = PaginatedResponse<CustomValidator>

export interface ValidatorTestRequest {
  code: string
  parameters: ValidatorParamDefinition[]
  test_data: Record<string, unknown>
  param_values?: Record<string, unknown>
}

export interface ValidatorTestResultDetail {
  passed: boolean
  issues: Array<{
    message: string
    severity: string
    row?: number
  }>
  message: string
  details?: Record<string, unknown>
}

export interface ValidatorTestResponse {
  success: boolean
  passed?: boolean
  execution_time_ms: number
  result?: ValidatorTestResultDetail
  error?: string
  warnings: string[]
}

export interface ReporterFieldDefinition {
  name: string
  type: string
  label: string
  description?: string
  required?: boolean
  default?: unknown
  options?: Array<{ label: string; value: string }>
}

export interface CustomReporter {
  id: string
  plugin_id?: string
  name: string
  display_name: string
  description: string
  output_formats: ReporterOutputFormat[]
  config_fields: ReporterFieldDefinition[]
  template?: string
  code?: string
  preview_image_url?: string
  is_enabled: boolean
  is_verified: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

export type CustomReporterListResponse = PaginatedResponse<CustomReporter>

export interface ReporterGenerateResponse {
  success: boolean
  report_id?: string
  download_url?: string
  preview_html?: string
  error?: string
  generation_time_ms: number
}

// ============================================================================
// Plugin API Functions
// ============================================================================

const API_BASE = '/api/v1'

export async function listPlugins(params?: {
  type?: PluginType
  status?: PluginStatus
  search?: string
  offset?: number
  limit?: number
}): Promise<PluginListResponse> {
  return request<PluginListResponse>('/plugins', { params: params as Record<string, string | number | boolean> })
}

export async function getMarketplaceStats(): Promise<MarketplaceStats> {
  return request<MarketplaceStats>('/plugins/stats')
}

export async function searchPlugins(query: {
  query?: string
  types?: PluginType[]
  sources?: PluginSource[]
  categories?: string[]
  min_rating?: number
  verified_only?: boolean
  sort_by?: 'relevance' | 'rating' | 'installs' | 'updated' | 'name'
  sort_order?: 'asc' | 'desc'
  offset?: number
  limit?: number
}): Promise<PluginListResponse> {
  return request<PluginListResponse>('/plugins/search', {
    method: 'POST',
    body: JSON.stringify(query),
  })
}

export async function getPlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}`)
}

export async function registerPlugin(data: Partial<Plugin>): Promise<Plugin> {
  return request<Plugin>('/plugins', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updatePlugin(pluginId: string, data: Partial<Plugin>): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function installPlugin(pluginId: string, options?: {
  version?: string
  force?: boolean
  enable_after_install?: boolean
}): Promise<PluginInstallResponse> {
  return request<PluginInstallResponse>(`/plugins/${pluginId}/install`, {
    method: 'POST',
    body: JSON.stringify({ plugin_id: pluginId, ...options }),
  })
}

export async function uninstallPlugin(pluginId: string, removeData?: boolean): Promise<PluginUninstallResponse> {
  return request<PluginUninstallResponse>(`/plugins/${pluginId}/uninstall`, {
    method: 'POST',
    body: JSON.stringify({ plugin_id: pluginId, remove_data: removeData }),
  })
}

export async function enablePlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}/enable`, { method: 'POST' })
}

export async function disablePlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}/disable`, { method: 'POST' })
}

// ============================================================================
// Custom Validators API
// ============================================================================

export async function listCustomValidators(params?: {
  plugin_id?: string
  category?: string
  enabled_only?: boolean
  search?: string
  offset?: number
  limit?: number
}): Promise<CustomValidatorListResponse> {
  return request<CustomValidatorListResponse>('/validators/custom', { params: params as Record<string, string | number | boolean> })
}

export async function getValidatorCategories(): Promise<string[]> {
  return request<string[]>('/validators/custom/categories')
}

export async function getValidatorTemplate(): Promise<{ template: string }> {
  return request<{ template: string }>('/validators/custom/template')
}

export async function getCustomValidator(validatorId: string): Promise<CustomValidator> {
  return request<CustomValidator>(`/validators/custom/${validatorId}`)
}

export async function createCustomValidator(data: Partial<CustomValidator>): Promise<CustomValidator> {
  return request<CustomValidator>('/validators/custom', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCustomValidator(validatorId: string, data: Partial<CustomValidator>): Promise<CustomValidator> {
  return request<CustomValidator>(`/validators/custom/${validatorId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deleteCustomValidator(validatorId: string): Promise<void> {
  return request<void>(`/validators/custom/${validatorId}`, { method: 'DELETE' })
}

export async function testCustomValidator(data: ValidatorTestRequest): Promise<ValidatorTestResponse> {
  return request<ValidatorTestResponse>('/validators/custom/test', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ============================================================================
// Custom Reporters API
// ============================================================================

export async function listCustomReporters(params?: {
  plugin_id?: string
  is_enabled?: boolean
  enabled_only?: boolean
  search?: string
  offset?: number
  limit?: number
}): Promise<CustomReporterListResponse> {
  const apiParams: Record<string, string | number | boolean> = {}
  if (params) {
    if (params.plugin_id) apiParams.plugin_id = params.plugin_id
    if (params.is_enabled !== undefined) apiParams.enabled_only = params.is_enabled
    if (params.enabled_only !== undefined) apiParams.enabled_only = params.enabled_only
    if (params.search) apiParams.search = params.search
    if (params.offset !== undefined) apiParams.offset = params.offset
    if (params.limit !== undefined) apiParams.limit = params.limit
  }
  return request<CustomReporterListResponse>('/reporters/custom', { params: apiParams })
}

export async function getReporterTemplates(): Promise<{ code_template: string; jinja2_template: string }> {
  return request<{ code_template: string; jinja2_template: string }>('/reporters/custom/templates')
}

export async function getCustomReporter(reporterId: string): Promise<CustomReporter> {
  return request<CustomReporter>(`/reporters/custom/${reporterId}`)
}

export async function createCustomReporter(data: Partial<CustomReporter>): Promise<CustomReporter> {
  return request<CustomReporter>('/reporters/custom', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCustomReporter(reporterId: string, data: Partial<CustomReporter>): Promise<CustomReporter> {
  return request<CustomReporter>(`/reporters/custom/${reporterId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deleteCustomReporter(reporterId: string): Promise<void> {
  return request<void>(`/reporters/custom/${reporterId}`, { method: 'DELETE' })
}

export async function previewCustomReporter(data: {
  template?: string
  code?: string
  sample_data?: Record<string, unknown>
  config?: Record<string, unknown>
  format?: string
}): Promise<ReporterGenerateResponse> {
  return request<ReporterGenerateResponse>('/reporters/custom/preview', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function generateCustomReport(reporterId: string, data: {
  output_format: ReporterOutputFormat
  config?: Record<string, unknown>
  validation_id?: string
  data?: Record<string, unknown>
  source_ids?: string[]
}): Promise<ReporterGenerateResponse> {
  return request<ReporterGenerateResponse>(`/reporters/custom/${reporterId}/generate`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function downloadCustomReport(
  reporterId: string,
  validationId: string,
  options?: {
    output_format?: string
    config?: Record<string, unknown>
  }
): Promise<Blob> {
  const params = new URLSearchParams({
    validation_id: validationId,
    output_format: options?.output_format || 'html',
  })
  if (options?.config) {
    params.append('config', JSON.stringify(options.config))
  }

  const response = await fetch(`${API_BASE}/reporters/custom/${reporterId}/download?${params}`, {
    headers: {
      'Accept': '*/*',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Download failed' }))
    throw new ApiError(response.status, error.detail || 'Download failed')
  }

  return response.blob()
}
