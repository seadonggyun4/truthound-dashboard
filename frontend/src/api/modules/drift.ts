/**
 * Drift API - comparison-only Truthound 3.0 surface.
 */
import { request } from '../core'
import type { PaginatedResponse } from '../core'

export type DriftMethod =
  | 'auto'
  | 'ks'
  | 'psi'
  | 'chi2'
  | 'js'
  | 'kl'
  | 'wasserstein'
  | 'cvm'
  | 'anderson'
  | 'hellinger'
  | 'bhattacharyya'
  | 'tv'
  | 'energy'
  | 'mmd'

export const DRIFT_METHODS: { value: DriftMethod; label: string; description: string }[] = [
  { value: 'auto', label: 'Auto', description: 'Smart selection based on data type' },
  { value: 'js', label: 'Jensen-Shannon', description: 'Symmetric divergence, bounded 0-1' },
  { value: 'hellinger', label: 'Hellinger', description: 'Bounded metric (0-1), satisfies triangle inequality' },
  { value: 'bhattacharyya', label: 'Bhattacharyya', description: 'Classification error bounds estimation' },
  { value: 'tv', label: 'Total Variation', description: 'Maximum probability difference' },
  { value: 'ks', label: 'Kolmogorov-Smirnov', description: 'Best for continuous distributions' },
  { value: 'psi', label: 'PSI', description: 'Population Stability Index - industry standard' },
  { value: 'kl', label: 'Kullback-Leibler', description: 'Information loss measure (asymmetric)' },
  { value: 'wasserstein', label: 'Wasserstein', description: "Earth Mover's Distance" },
  { value: 'cvm', label: 'Cramer-von Mises', description: 'More sensitive to tails than KS' },
  { value: 'anderson', label: 'Anderson-Darling', description: 'Most sensitive to tail differences' },
  { value: 'energy', label: 'Energy', description: 'Location and scale sensitive' },
  { value: 'mmd', label: 'MMD', description: 'Maximum Mean Discrepancy - kernel-based, high-dimensional' },
  { value: 'chi2', label: 'Chi-Square', description: 'Best for categorical data' },
]

export const DEFAULT_THRESHOLDS: Record<DriftMethod, number> = {
  auto: 0.05,
  ks: 0.05,
  psi: 0.1,
  chi2: 0.05,
  js: 0.1,
  kl: 0.1,
  wasserstein: 0.1,
  cvm: 0.05,
  anderson: 0.05,
  hellinger: 0.1,
  bhattacharyya: 0.1,
  tv: 0.1,
  energy: 0.1,
  mmd: 0.1,
}

export interface DriftCompareRequest {
  baseline_source_id: string
  current_source_id: string
  columns?: string[]
  method?: DriftMethod
  threshold?: number
  sample_size?: number
}

export interface ColumnDriftResult {
  column: string
  dtype: string
  drifted: boolean
  level: string
  method: string
  statistic?: number
  p_value?: number
  baseline_stats: Record<string, unknown>
  current_stats: Record<string, unknown>
}

export interface DriftResult {
  comparison_id?: string
  baseline_source: string
  current_source: string
  baseline_rows: number
  current_rows: number
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: string[]
  columns: ColumnDriftResult[]
}

export interface DriftComparison {
  id: string
  baseline_source_id: string
  current_source_id: string
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: number
  drift_percentage: number
  result?: DriftResult
  config?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export type DriftComparisonListResponse = PaginatedResponse<DriftComparison>

export async function compareDrift(data: DriftCompareRequest): Promise<DriftComparison> {
  return request<DriftComparison>('/drift/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function listDriftComparisons(params?: {
  baseline_source_id?: string
  current_source_id?: string
  offset?: number
  limit?: number
}): Promise<DriftComparisonListResponse> {
  return request<DriftComparisonListResponse>('/drift/comparisons', { params })
}

export async function getDriftComparison(id: string): Promise<DriftComparison> {
  return request<DriftComparison>(`/drift/comparisons/${id}`)
}
