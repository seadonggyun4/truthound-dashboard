/**
 * Maintenance API - Retention policies and cleanup.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export type RetentionPolicyType = 'time' | 'count' | 'size' | 'status' | 'tag' | 'composite'

export interface RetentionPolicy {
  policy_type: RetentionPolicyType
  value: unknown
  target: string
  priority: number
  enabled: boolean
}

export interface RetentionPolicyConfig {
  validation_retention_days: number
  profile_keep_per_source: number
  notification_log_retention_days: number
  run_vacuum: boolean
  enabled: boolean
  max_storage_mb?: number | null
  keep_failed_validations?: boolean
  failed_retention_days?: number
  protected_tags?: string[]
  delete_tags?: string[]
  active_policies?: RetentionPolicy[]
}

export interface CleanupResult {
  task_name: string
  records_deleted: number
  duration_ms: number
  success: boolean
  error?: string
}

export interface MaintenanceReport {
  started_at: string
  completed_at?: string
  results: CleanupResult[]
  total_deleted: number
  total_duration_ms: number
  vacuum_performed: boolean
  vacuum_error?: string
  success: boolean
}

export interface MaintenanceStatus {
  enabled: boolean
  last_run_at?: string
  next_scheduled_at?: string
  config: RetentionPolicyConfig
  available_tasks: string[]
}

export interface CacheStats {
  total_entries: number
  expired_entries: number
  valid_entries: number
  max_size: number
  hit_rate?: number
}

// ============================================================================
// API Functions
// ============================================================================

export async function getRetentionPolicy(): Promise<RetentionPolicyConfig> {
  return request<RetentionPolicyConfig>('/maintenance/retention')
}

export async function updateRetentionPolicy(
  config: Partial<RetentionPolicyConfig>
): Promise<RetentionPolicyConfig> {
  return request<RetentionPolicyConfig>('/maintenance/retention', {
    method: 'PUT',
    body: JSON.stringify(config),
  })
}

export async function getMaintenanceStatus(): Promise<MaintenanceStatus> {
  return request<MaintenanceStatus>('/maintenance/status')
}

export async function triggerCleanup(options?: {
  tasks?: string[]
  run_vacuum?: boolean
}): Promise<MaintenanceReport> {
  return request<MaintenanceReport>('/maintenance/cleanup', {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function runVacuum(): Promise<MaintenanceReport> {
  return request<MaintenanceReport>('/maintenance/vacuum', {
    method: 'POST',
  })
}

export async function getCacheStats(): Promise<CacheStats> {
  return request<CacheStats>('/maintenance/cache/stats')
}

export async function clearCache(options?: {
  pattern?: string
  namespace?: string
}): Promise<CacheStats> {
  return request<CacheStats>('/maintenance/cache/clear', {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}
