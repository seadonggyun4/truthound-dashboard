/**
 * Enterprise Sampling API - Large-scale sampling for 100M+ row datasets.
 *
 * This module provides API client functions for truthound 1.2.10's enterprise
 * sampling capabilities including:
 * - Block Sampling
 * - Multi-Stage Sampling
 * - Column-Aware Sampling
 * - Progressive Sampling
 * - Probabilistic Data Structures (HyperLogLog, Count-Min Sketch, Bloom Filter)
 */
import { request as apiRequest } from '../core'

// ============================================================================
// Enums
// ============================================================================

export type ScaleCategory = 'small' | 'medium' | 'large' | 'xlarge' | 'xxlarge'

export type EnterpriseSamplingStrategy =
  | 'none'
  | 'random'
  | 'head'
  | 'tail'
  | 'stratified'
  | 'reservoir'
  | 'systematic'
  | 'adaptive'
  | 'hash'
  | 'block'
  | 'multi_stage'
  | 'column_aware'
  | 'progressive'
  | 'parallel_block'

export type SamplingQuality = 'sketch' | 'quick' | 'standard' | 'high' | 'exact'

export type SketchType = 'hyperloglog' | 'countmin' | 'bloom'

export type SchedulingPolicy = 'round_robin' | 'work_stealing' | 'adaptive'

// ============================================================================
// Configuration Types
// ============================================================================

export interface MemoryBudgetConfig {
  max_memory_mb?: number
  reserved_memory_mb?: number
  gc_threshold_mb?: number | null
  backpressure_enabled?: boolean
}

export interface ParallelSamplingConfig {
  max_workers?: number
  enable_work_stealing?: boolean
  scheduling_policy?: SchedulingPolicy
  backpressure_threshold?: number
  chunk_timeout_seconds?: number
}

export interface BlockSamplingConfig {
  block_size?: number
  sample_per_block?: number | null
  parallel?: ParallelSamplingConfig
}

export interface MultiStageSamplingConfig {
  num_stages?: number
  stage_reduction_factor?: number | null
  early_stop_enabled?: boolean
}

export interface ColumnAwareSamplingConfig {
  string_multiplier?: number
  categorical_multiplier?: number
  complex_multiplier?: number
  numeric_multiplier?: number
}

export interface ProgressiveSamplingConfig {
  convergence_threshold?: number
  max_stages?: number
  initial_sample_ratio?: number
  growth_factor?: number
}

export interface SketchConfig {
  sketch_type?: SketchType
  hll_precision?: number
  cms_width?: number
  cms_depth?: number
  cms_epsilon?: number | null
  cms_delta?: number | null
  bloom_capacity?: number
  bloom_error_rate?: number
}

// ============================================================================
// Request/Response Types
// ============================================================================

export interface EnterpriseSamplingRequest {
  source_id: string
  target_rows?: number
  quality?: SamplingQuality
  strategy?: EnterpriseSamplingStrategy
  memory_budget?: MemoryBudgetConfig
  time_budget_seconds?: number
  confidence_level?: number
  margin_of_error?: number
  min_sample_ratio?: number
  max_sample_ratio?: number
  seed?: number | null
  block_config?: BlockSamplingConfig | null
  multi_stage_config?: MultiStageSamplingConfig | null
  column_aware_config?: ColumnAwareSamplingConfig | null
  progressive_config?: ProgressiveSamplingConfig | null
  sketch_config?: SketchConfig | null
}

export interface SamplingMetrics {
  original_rows: number
  sampled_rows: number
  sampling_ratio: number
  strategy_used: EnterpriseSamplingStrategy
  scale_category: ScaleCategory
  is_sampled: boolean
  sampling_time_ms: number
  throughput_rows_per_sec: number
  speedup_factor: number
  peak_memory_mb: number
  workers_used: number
  worker_utilization: number
  blocks_processed?: number | null
  time_per_block_ms?: number | null
  stages_completed?: number | null
  converged_early?: boolean | null
  backpressure_events: number
  margin_of_error_actual?: number | null
  confidence_achieved?: number | null
}

export interface EnterpriseSamplingResponse {
  source_id: string
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  started_at: string
  completed_at?: string | null
  metrics?: SamplingMetrics | null
  sampled_data_path?: string | null
  error_message?: string | null
}

export interface SampleSizeEstimateRequest {
  population_size: number
  confidence_level?: number
  margin_of_error?: number
  quality?: SamplingQuality
}

export interface SampleSizeEstimateResponse {
  population_size: number
  scale_category: ScaleCategory
  recommended_size: number
  min_size: number
  max_size: number
  estimated_time_seconds: number
  estimated_memory_mb: number
  speedup_factor: number
  recommended_strategy: EnterpriseSamplingStrategy
  strategy_rationale: string
}

export interface SketchEstimateRequest {
  source_id: string
  columns: string[]
  sketch_type: SketchType
  sketch_config?: SketchConfig | null
}

export interface SketchEstimateResult {
  column: string
  sketch_type: SketchType
  cardinality_estimate?: number | null
  cardinality_error?: number | null
  heavy_hitters?: Array<{ value: string; count: number }> | null
  membership_tests?: Record<string, boolean> | null
  memory_used_bytes: number
  processing_time_ms: number
}

export interface SketchEstimateResponse {
  source_id: string
  results: SketchEstimateResult[]
  total_time_ms: number
  total_memory_mb: number
}

export interface SamplingJobStatus {
  job_id: string
  source_id: string
  status: string
  progress: number
  current_stage?: string | null
  started_at: string
  estimated_completion?: string | null
  rows_processed: number
  blocks_completed?: number | null
  blocks_total?: number | null
}

export interface SamplingJobListResponse {
  jobs: SamplingJobStatus[]
  total: number
  active_count: number
}

export interface StrategyInfo {
  name: string
  value: EnterpriseSamplingStrategy
  description: string
  best_for: string
  supports_parallel: boolean
  supports_streaming: boolean
}

export interface QualityPreset {
  name: SamplingQuality
  description: string
  target_rows: number | null
  confidence_level: number
  margin_of_error: number
}

export interface ScaleCategoryInfo {
  name: ScaleCategory
  row_count_range: string
  recommended_strategy: EnterpriseSamplingStrategy
  description: string
}

export interface ClassifyScaleResponse {
  row_count: number
  scale_category: ScaleCategory
  recommended_strategy: EnterpriseSamplingStrategy
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Run enterprise-scale sampling on a data source.
 *
 * Supports datasets from 100M to billions of rows with:
 * - Block sampling for parallel processing
 * - Multi-stage hierarchical sampling
 * - Column-aware adaptive sampling
 * - Progressive sampling with convergence detection
 */
export async function runEnterpriseSampling(
  req: EnterpriseSamplingRequest
): Promise<EnterpriseSamplingResponse> {
  return apiRequest<EnterpriseSamplingResponse>('/sampling/enterprise', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

/**
 * Estimate optimal sample size using Cochran's formula.
 *
 * Returns recommended sample size with statistical confidence,
 * processing estimates, and strategy recommendations.
 */
export async function estimateSampleSize(
  req: SampleSizeEstimateRequest
): Promise<SampleSizeEstimateResponse> {
  return apiRequest<SampleSizeEstimateResponse>('/sampling/estimate-size', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

/**
 * Run sketch-based estimation using probabilistic data structures.
 *
 * Supported sketch types:
 * - HyperLogLog: Cardinality estimation (distinct count)
 * - Count-Min Sketch: Frequency estimation (heavy hitters)
 * - Bloom Filter: Membership testing
 */
export async function runSketchEstimation(
  req: SketchEstimateRequest
): Promise<SketchEstimateResponse> {
  return apiRequest<SketchEstimateResponse>('/sampling/sketch', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

/**
 * List all active and recent sampling jobs.
 */
export async function listSamplingJobs(params?: {
  status?: string
  limit?: number
}): Promise<SamplingJobListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status_filter', params.status)
  if (params?.limit) searchParams.set('limit', params.limit.toString())

  const query = searchParams.toString()
  return apiRequest<SamplingJobListResponse>(`/sampling/jobs${query ? `?${query}` : ''}`)
}

/**
 * Get status of a specific sampling job.
 */
export async function getSamplingJobStatus(jobId: string): Promise<SamplingJobStatus> {
  return apiRequest<SamplingJobStatus>(`/sampling/jobs/${jobId}`)
}

/**
 * Cancel an active sampling job.
 */
export async function cancelSamplingJob(
  jobId: string
): Promise<{ job_id: string; status: string; message: string }> {
  return apiRequest<{ job_id: string; status: string; message: string }>(
    `/sampling/jobs/${jobId}/cancel`,
    { method: 'POST' }
  )
}

/**
 * List all available enterprise sampling strategies.
 */
export async function listStrategies(): Promise<StrategyInfo[]> {
  return apiRequest<StrategyInfo[]>('/sampling/strategies')
}

/**
 * List available sampling quality presets.
 */
export async function listQualityPresets(): Promise<QualityPreset[]> {
  return apiRequest<QualityPreset[]>('/sampling/quality-presets')
}

/**
 * List dataset scale categories with recommended strategies.
 */
export async function listScaleCategories(): Promise<ScaleCategoryInfo[]> {
  return apiRequest<ScaleCategoryInfo[]>('/sampling/scale-categories')
}

/**
 * Classify a dataset by row count into a scale category.
 */
export async function classifyScale(rowCount: number): Promise<ClassifyScaleResponse> {
  return apiRequest<ClassifyScaleResponse>(`/sampling/classify-scale?row_count=${rowCount}`, {
    method: 'POST',
  })
}

// ============================================================================
// Utility Types for UI Components
// ============================================================================

/**
 * Default configuration values for UI forms.
 */
export const DEFAULT_SAMPLING_CONFIG: Partial<EnterpriseSamplingRequest> = {
  target_rows: 100_000,
  quality: 'standard',
  strategy: 'adaptive',
  confidence_level: 0.95,
  margin_of_error: 0.05,
  min_sample_ratio: 0.001,
  max_sample_ratio: 0.1,
  memory_budget: {
    max_memory_mb: 1024,
    reserved_memory_mb: 256,
    backpressure_enabled: true,
  },
}

/**
 * Scale category thresholds for client-side classification.
 */
export const SCALE_THRESHOLDS = {
  small: 1_000_000,
  medium: 10_000_000,
  large: 100_000_000,
  xlarge: 1_000_000_000,
} as const

/**
 * Classify dataset scale on the client side.
 */
export function classifyDatasetScale(rowCount: number): ScaleCategory {
  if (rowCount < SCALE_THRESHOLDS.small) return 'small'
  if (rowCount < SCALE_THRESHOLDS.medium) return 'medium'
  if (rowCount < SCALE_THRESHOLDS.large) return 'large'
  if (rowCount < SCALE_THRESHOLDS.xlarge) return 'xlarge'
  return 'xxlarge'
}

/**
 * Get recommended strategy for a scale category.
 */
export function getRecommendedStrategy(scale: ScaleCategory): EnterpriseSamplingStrategy {
  const strategyMap: Record<ScaleCategory, EnterpriseSamplingStrategy> = {
    small: 'none',
    medium: 'column_aware',
    large: 'block',
    xlarge: 'multi_stage',
    xxlarge: 'multi_stage',
  }
  return strategyMap[scale]
}

/**
 * Format large numbers for display.
 */
export function formatRowCount(count: number): string {
  if (count >= 1_000_000_000) {
    return `${(count / 1_000_000_000).toFixed(1)}B`
  }
  if (count >= 1_000_000) {
    return `${(count / 1_000_000).toFixed(1)}M`
  }
  if (count >= 1_000) {
    return `${(count / 1_000).toFixed(1)}K`
  }
  return count.toString()
}

/**
 * Format time duration for display.
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`
  }
  if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)}m`
  }
  return `${(seconds / 3600).toFixed(1)}h`
}

/**
 * Format memory size for display.
 */
export function formatMemory(mb: number): string {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(1)} GB`
  }
  return `${mb.toFixed(0)} MB`
}
