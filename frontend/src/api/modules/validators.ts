/**
 * Validators API - built-in Truthound validator registry only.
 */
import { request } from '../core'

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
