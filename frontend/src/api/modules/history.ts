/**
 * History API - Validation history and trends.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

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
  summary: HistorySummary
  trend: TrendDataPoint[]
  failure_frequency: FailureFrequencyItem[]
  recent_validations: RecentValidation[]
}

// ============================================================================
// API Functions
// ============================================================================

export async function getValidationHistory(
  sourceId: string,
  params?: {
    period?: '7d' | '30d' | '90d'
    granularity?: 'hourly' | 'daily' | 'weekly'
  }
): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/sources/${sourceId}/history`, { params })
}
