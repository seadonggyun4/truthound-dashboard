/**
 * Validations API - Run and manage validation results.
 */
import { request } from '../core'
import type { PaginatedResponse } from '../core'

// ============================================================================
// Types
// ============================================================================

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

export type ValidationListResponse = PaginatedResponse<Validation>

/**
 * Configuration for a single validator with its parameters.
 */
export interface ValidatorConfig {
  name: string
  enabled: boolean
  params: Record<string, unknown>
  severity_override?: 'low' | 'medium' | 'high' | 'critical'
}

/**
 * Options for running validation - maps to th.check() parameters.
 */
export interface ValidationRunOptions {
  validators?: string[]
  validator_configs?: ValidatorConfig[]
  custom_validators?: Array<{
    validator_id: string
    column?: string
    params?: Record<string, unknown>
  }>
  schema_path?: string
  auto_schema?: boolean
  columns?: string[]
  min_severity?: 'low' | 'medium' | 'high' | 'critical'
  strict?: boolean
  parallel?: boolean
  max_workers?: number
  pushdown?: boolean
}

// ============================================================================
// API Functions
// ============================================================================

export async function runValidation(
  sourceId: string,
  options?: ValidationRunOptions
): Promise<Validation> {
  return request<Validation>(`/validations/sources/${sourceId}/validate`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getValidation(id: string): Promise<Validation> {
  return request<Validation>(`/validations/${id}`)
}

export async function listSourceValidations(
  sourceId: string,
  params?: { offset?: number; limit?: number }
): Promise<ValidationListResponse> {
  return request<ValidationListResponse>(
    `/validations/sources/${sourceId}/validations`,
    { params }
  )
}
