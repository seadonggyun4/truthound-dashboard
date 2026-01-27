/**
 * Profile API - Data profiling.
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

export interface SamplingMetadata {
  strategyUsed: string
  sampleSize: number
  totalRows: number
  samplingRatio: number
  seed?: number | null
  confidenceLevel?: number | null
  marginOfError?: number | null
}

export interface ProfileResult {
  source: string
  row_count: number
  column_count: number
  size_bytes: number
  columns: ColumnProfile[]
  sampling?: SamplingMetadata | null
  detected_patterns_summary?: Record<string, number> | null
  profiled_at?: string | null
  profiling_duration_ms?: number | null
}

export type SamplingStrategy =
  | 'none'
  | 'head'
  | 'random'
  | 'systematic'
  | 'stratified'
  | 'reservoir'
  | 'adaptive'
  | 'hash'

export interface SamplingConfig {
  strategy: SamplingStrategy
  sample_size?: number | null
  confidence_level?: number
  margin_of_error?: number
  strata_column?: string | null
  seed?: number | null
}

export interface PatternDetectionConfig {
  enabled: boolean
  sample_size?: number
  min_confidence?: number
  patterns_to_detect?: string[] | null
}

export interface ProfileOptions {
  sample_size?: number
  sampling?: SamplingConfig
  pattern_detection?: PatternDetectionConfig
  include_histograms?: boolean
  include_correlations?: boolean
  include_cardinality?: boolean
}

// ============================================================================
// API Functions
// ============================================================================

export async function profileSource(
  sourceId: string,
  options?: ProfileOptions
): Promise<ProfileResult> {
  return request<ProfileResult>(`/sources/${sourceId}/profile`, {
    method: 'POST',
    body: options ? JSON.stringify(options) : undefined,
  })
}
