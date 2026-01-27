/**
 * Validators API - Validator registry and custom validators.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export type ValidatorCategory =
  | 'schema'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  | 'string'
  | 'datetime'
  | 'aggregate'
  | 'drift'
  | 'anomaly'
  | 'cross_table'
  | 'multi_column'
  | 'query'
  | 'table'
  | 'geospatial'
  | 'privacy'
  | 'business_rule'
  | 'profiling'
  | 'localization'
  | 'ml_feature'
  | 'timeseries'
  | 'referential'

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

export interface SelectOption {
  value: string
  label: string
}

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

export interface CategoryInfo {
  value: string
  label: string
}

export type ValidatorSource = 'builtin' | 'custom'

export interface UnifiedValidatorDefinition {
  id: string | null
  name: string
  display_name: string
  category: string
  description: string
  parameters: ParameterDefinition[]
  tags: string[]
  severity_default: 'low' | 'medium' | 'high' | 'critical'
  source: ValidatorSource
  is_enabled: boolean
  requires_extra: string | null
  experimental: boolean
  deprecated: boolean
  usage_count: number
  is_verified: boolean
}

export interface ValidatorCategorySummary {
  name: string
  label: string
  builtin_count: number
  custom_count: number
  total: number
}

export interface UnifiedValidatorListResponse {
  data: UnifiedValidatorDefinition[]
  total: number
  builtin_count: number
  custom_count: number
  categories: ValidatorCategorySummary[]
}

export interface CustomValidatorExecuteRequest {
  source_id: string
  column_name: string
  param_values?: Record<string, unknown>
  sample_size?: number
}

export interface CustomValidatorExecuteResponse {
  success: boolean
  passed: boolean | null
  execution_time_ms: number
  issues: Array<{
    row?: number
    message: string
    severity?: string
  }>
  message: string
  details: Record<string, unknown>
  error?: string
}

// ============================================================================
// API Functions
// ============================================================================

export async function listValidators(params?: {
  category?: ValidatorCategory
  search?: string
}): Promise<ValidatorDefinition[]> {
  return request<ValidatorDefinition[]>('/validators', { params })
}

export async function listValidatorCategories(): Promise<CategoryInfo[]> {
  return request<CategoryInfo[]>('/validators/categories')
}

export async function getValidator(name: string): Promise<ValidatorDefinition | null> {
  return request<ValidatorDefinition | null>(`/validators/${name}`)
}

export async function listUnifiedValidators(params?: {
  category?: string
  source?: ValidatorSource
  search?: string
  enabled_only?: boolean
  offset?: number
  limit?: number
}): Promise<UnifiedValidatorListResponse> {
  return request<UnifiedValidatorListResponse>('/validators/unified', {
    params: params as Record<string, string | number | boolean>,
  })
}

export async function executeCustomValidator(
  validatorId: string,
  executeRequest: CustomValidatorExecuteRequest
): Promise<CustomValidatorExecuteResponse> {
  return request<CustomValidatorExecuteResponse>(
    `/validators/custom/${validatorId}/execute`,
    {
      method: 'POST',
      body: JSON.stringify(executeRequest),
    }
  )
}

export async function previewCustomValidatorExecution(
  validatorId: string,
  testData: {
    column_name: string
    values: unknown[]
    params?: Record<string, unknown>
    schema?: Record<string, unknown>
  }
): Promise<CustomValidatorExecuteResponse> {
  return request<CustomValidatorExecuteResponse>(
    `/validators/custom/${validatorId}/execute-preview`,
    {
      method: 'POST',
      body: JSON.stringify(testData),
    }
  )
}
