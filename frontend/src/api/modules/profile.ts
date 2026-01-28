/**
 * Profile API - Data profiling.
 *
 * Note: truthound's th.profile() only supports (data, source) parameters.
 * Advanced options like sampling strategies, pattern detection configuration,
 * and correlation analysis are NOT supported by the underlying library.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export interface ColumnProfile {
  name: string
  dtype: string
  null_pct: string
  unique_pct: string
  min?: unknown
  max?: unknown
  mean?: number
  std?: number
}

export interface DetectedPattern {
  patternType: string
  confidence: number
  matchCount: number
  matchPercentage: number
  sampleMatches?: string[] | null
}

export interface HistogramBucket {
  bucket: string
  count: number
  percentage: number
}

export interface EnhancedColumnProfile extends ColumnProfile {
  inferredType?: string | null
  nullCount?: number | null
  isUnique?: boolean | null
  median?: number | null
  q1?: number | null
  q3?: number | null
  skewness?: number | null
  kurtosis?: number | null
  minLength?: number | null
  maxLength?: number | null
  avgLength?: number | null
  patterns?: DetectedPattern[] | null
  primaryPattern?: string | null
  mostCommon?: Array<{ value: string; count: number }> | null
  histogram?: HistogramBucket[] | null
  cardinalityEstimate?: number | null
}

export interface ProfileResult {
  source: string
  row_count: number
  column_count: number
  size_bytes: number
  columns: ColumnProfile[]
  detected_patterns_summary?: Record<string, number> | null
  profiled_at?: string | null
  profiling_duration_ms?: number | null
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Run data profiling on a source.
 *
 * Note: truthound's th.profile() does not support advanced configuration options.
 * The profiling is run with default settings.
 */
export async function profileSource(sourceId: string): Promise<ProfileResult> {
  return request<ProfileResult>(`/sources/${sourceId}/profile`, {
    method: 'POST',
  })
}
