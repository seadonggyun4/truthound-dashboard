/**
 * Profile API - Data profiling.
 *
 * Supports both basic profiling (th.profile) and advanced profiling
 * with ProfilerConfig options for fine-grained control.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

/**
 * Advanced profiling configuration.
 * Maps to truthound's ProfilerConfig.
 */
export interface ProfileAdvancedConfig {
  sample_size?: number | null
  random_seed?: number
  include_patterns?: boolean
  include_correlations?: boolean
  include_distributions?: boolean
  top_n_values?: number
  pattern_sample_size?: number
  correlation_threshold?: number
  min_pattern_match_ratio?: number
  n_jobs?: number
}

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
 * Run basic data profiling on a source.
 *
 * Uses truthound's th.profile() with default settings.
 */
export async function profileSource(sourceId: string): Promise<ProfileResult> {
  return request<ProfileResult>(`/sources/${sourceId}/profile`, {
    method: 'POST',
  })
}

/**
 * Run advanced data profiling with custom configuration.
 *
 * Uses truthound's ProfilerConfig for fine-grained control over:
 * - Sampling: sample_size, random_seed
 * - Features: include_patterns, include_correlations, include_distributions
 * - Pattern detection: pattern_sample_size, min_pattern_match_ratio
 * - Output: top_n_values, correlation_threshold
 * - Performance: n_jobs
 */
/**
 * Get the latest profile result for a source.
 *
 * Returns null if no profile has been run yet.
 */
export async function getLatestProfile(sourceId: string): Promise<ProfileResult | null> {
  return request<ProfileResult | null>(`/sources/${sourceId}/profile/latest`)
}

export async function profileSourceAdvanced(
  sourceId: string,
  config: ProfileAdvancedConfig
): Promise<ProfileResult> {
  return request<ProfileResult>(`/sources/${sourceId}/profile/advanced`, {
    method: 'POST',
    body: JSON.stringify(config),
  })
}
