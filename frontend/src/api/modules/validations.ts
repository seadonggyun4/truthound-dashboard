/**
 * Validations API - Run and manage validation results.
 *
 * Supports truthound 1.3.0+ features:
 * - PHASE 1: ResultFormat system (boolean_only/basic/summary/complete)
 * - PHASE 2: Structured results (ValidationDetailResult, ValidationReportStatistics)
 * - PHASE 4: DAG execution info (ValidatorExecutionSummary)
 * - PHASE 5: Exception isolation (ExceptionInfo, ExceptionSummary)
 */
import { request } from '../core'
import type { PaginatedResponse } from '../core'

// ============================================================================
// Result Format (PHASE 1)
// ============================================================================

export type ResultFormatLevel = 'boolean_only' | 'basic' | 'summary' | 'complete'

// ============================================================================
// PHASE 2: Structured validation detail
// ============================================================================

/** Structured validation result detail — maps to truthound's ValidationDetail */
export interface ValidationDetailResult {
  element_count: number
  missing_count: number
  observed_value?: unknown
  unexpected_count: number
  unexpected_percent: number
  unexpected_percent_nonmissing: number
  partial_unexpected_list?: unknown[]
  partial_unexpected_counts?: Array<{ value: unknown; count: number }>
  partial_unexpected_index_list?: number[]
  unexpected_list?: unknown[]
  unexpected_index_list?: number[]
  unexpected_rows?: Record<string, unknown>[]
  debug_query?: string
}

/** Aggregated report statistics */
export interface ValidationReportStatistics {
  total_validations: number
  successful_validations: number
  unsuccessful_validations: number
  success_percent: number
  issues_by_severity: Record<string, number>
  issues_by_column: Record<string, number>
  issues_by_validator: Record<string, number>
  issues_by_type: Record<string, number>
  most_problematic_columns: Array<[string, number]>
}

// ============================================================================
// PHASE 4: DAG execution info
// ============================================================================

/** Info about a skipped validator */
export interface SkippedValidatorInfo {
  validator_name: string
  reason?: string
}

/** Validator execution summary from DAG execution */
export interface ValidatorExecutionSummary {
  total_validators: number
  executed: number
  skipped: number
  failed: number
  skipped_details?: SkippedValidatorInfo[]
}

// ============================================================================
// PHASE 5: Exception info
// ============================================================================

/** Individual validation exception info */
export interface ExceptionInfo {
  exception_type?: string
  exception_message?: string
  retry_count: number
  max_retries: number
  is_retryable: boolean
  failure_category: 'transient' | 'permanent' | 'configuration' | 'data' | 'unknown'
  validator_name?: string
  column?: string
}

/** Session-level exception summary */
export interface ExceptionSummary {
  total_exceptions: number
  total_retries: number
  exceptions_by_type: Record<string, number>
  exceptions_by_category: Record<string, number>
  exceptions_by_validator: Record<string, number>
  retryable_count: number
}

// ============================================================================
// Core Types
// ============================================================================

export interface ValidationIssue {
  column: string
  issue_type: string
  count: number
  severity: 'critical' | 'high' | 'medium' | 'low'
  details?: string
  expected?: unknown
  actual?: unknown
  sample_values?: unknown[]
  // PHASE 2
  validator_name?: string
  success?: boolean
  result?: ValidationDetailResult
  // PHASE 5
  exception_info?: ExceptionInfo
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
  // PHASE 1
  result_format?: ResultFormatLevel
  // PHASE 2
  statistics?: ValidationReportStatistics
  // PHASE 4
  validator_execution_summary?: ValidatorExecutionSummary
  // PHASE 5
  exception_summary?: ExceptionSummary
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
  min_severity?: 'low' | 'medium' | 'high' | 'critical'
  parallel?: boolean
  max_workers?: number
  pushdown?: boolean
  // PHASE 1: result format
  result_format?: ResultFormatLevel
  include_unexpected_rows?: boolean
  max_unexpected_rows?: number
  // PHASE 5: exception control
  catch_exceptions?: boolean
  max_retries?: number
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
