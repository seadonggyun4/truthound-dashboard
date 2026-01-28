/**
 * Drift monitoring types.
 *
 * Shared type definitions for drift monitoring components.
 */

// Preview result type matching backend schema
export interface DriftPreviewData {
  baseline_source_id: string
  current_source_id: string
  baseline_source_name: string | null
  current_source_name: string | null
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: number
  drift_percentage: number
  baseline_rows: number
  current_rows: number
  method: string
  threshold: number
  columns: ColumnPreviewResult[]
  most_affected: string[]
}

export interface ColumnPreviewResult {
  column: string
  dtype: string
  drifted: boolean
  level: string
  method: string
  statistic: number | null
  p_value: number | null
  baseline_stats: Record<string, number>
  current_stats: Record<string, number>
  baseline_distribution: DistributionData | null
  current_distribution: DistributionData | null
}

export interface DistributionData {
  values: number[]
  bins: string[]
  counts: number[]
  percentages: number[]
}
