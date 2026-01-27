/**
 * Profile Comparison API - Profile trends and comparison.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export type TrendDirection = 'up' | 'down' | 'stable'

export interface ProfileSummary {
  id: string
  source_id: string
  row_count: number
  column_count: number
  size_bytes: number
  created_at: string
}

export interface ColumnComparison {
  column: string
  metric: string
  baseline_value: number | string | null
  current_value: number | string | null
  change: number | null
  change_pct: number | null
  is_significant: boolean
  trend: TrendDirection
}

export interface ProfileComparisonSummary {
  total_columns: number
  columns_with_changes: number
  significant_changes: number
  columns_improved: number
  columns_degraded: number
}

export interface ProfileComparisonResponse {
  source_id: string
  source_name: string
  baseline_profile_id: string
  current_profile_id: string
  baseline_timestamp: string
  current_timestamp: string
  row_count_change: number
  row_count_change_pct: number
  column_count_change: number
  column_comparisons: ColumnComparison[]
  significant_changes: number
  summary: ProfileComparisonSummary
  compared_at: string
}

export interface ProfileTrendPoint {
  timestamp: string
  profile_id: string
  row_count: number
  column_count: number
  avg_null_pct: number
  avg_unique_pct: number
  size_bytes: number
}

export interface ColumnTrend {
  column: string
  metric: string
  values: [string, number][]
  trend_direction: TrendDirection
  change_pct: number
  min_value: number | null
  max_value: number | null
  avg_value: number | null
}

export interface ProfileTrendResponse {
  source_id: string
  source_name: string
  period: string
  granularity: string
  data_points: ProfileTrendPoint[]
  column_trends: ColumnTrend[]
  total_profiles: number
  row_count_trend: TrendDirection
  summary: Record<string, unknown>
}

export interface LatestComparisonResponse {
  source_id: string
  has_previous: boolean
  comparison: ProfileComparisonResponse | null
}

// ============================================================================
// API Functions
// ============================================================================

export async function listProfiles(
  sourceId: string,
  params?: { limit?: number; offset?: number }
): Promise<{ profiles: ProfileSummary[]; total: number; source_id: string }> {
  return request(`/sources/${sourceId}/profiles`, { params })
}

export async function compareProfiles(data: {
  baseline_profile_id: string
  current_profile_id: string
  significance_threshold?: number
}): Promise<ProfileComparisonResponse> {
  return request('/profiles/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getProfileTrend(
  sourceId: string,
  options?: {
    period?: '7d' | '30d' | '90d'
    granularity?: 'hourly' | 'daily' | 'weekly' | 'monthly'
    columns?: string[]
    metrics?: string[]
  }
): Promise<ProfileTrendResponse> {
  const params: Record<string, string | number | boolean> = {}
  if (options?.period) params.period = options.period
  if (options?.granularity) params.granularity = options.granularity
  if (options?.columns?.length) params.columns = options.columns.join(',')
  if (options?.metrics?.length) params.metrics = options.metrics.join(',')
  return request(`/sources/${sourceId}/profiles/trend`, { params })
}

export async function getLatestProfileComparison(
  sourceId: string
): Promise<LatestComparisonResponse> {
  return request(`/sources/${sourceId}/profiles/latest-comparison`)
}
