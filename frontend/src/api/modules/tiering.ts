/**
 * Storage Tiering API - Tiers, policies, configs, and migrations.
 *
 * This module provides API client functions for storage tiering features
 * based on truthound 1.2.10+ capabilities.
 */
import { request } from '../core'

// ============================================================================
// Enums
// ============================================================================

export type TierType = 'hot' | 'warm' | 'cold' | 'archive'
export type MigrationDirection = 'demote' | 'promote'
export type TierPolicyType =
  | 'age_based'
  | 'access_based'
  | 'size_based'
  | 'scheduled'
  | 'composite'
  | 'custom'
export type MigrationStatus = 'pending' | 'in_progress' | 'completed' | 'failed'

// ============================================================================
// Storage Tier Types
// ============================================================================

export interface StorageTier {
  id: string
  name: string
  tier_type: TierType
  store_type: string
  store_config: Record<string, unknown>
  priority: number
  cost_per_gb: number | null
  retrieval_time_ms: number | null
  metadata: Record<string, unknown> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StorageTierCreate {
  name: string
  tier_type?: TierType
  store_type: string
  store_config?: Record<string, unknown>
  priority?: number
  cost_per_gb?: number
  retrieval_time_ms?: number
  metadata?: Record<string, unknown>
  is_active?: boolean
}

export interface StorageTierUpdate {
  name?: string
  tier_type?: TierType
  store_type?: string
  store_config?: Record<string, unknown>
  priority?: number
  cost_per_gb?: number
  retrieval_time_ms?: number
  metadata?: Record<string, unknown>
  is_active?: boolean
}

export interface StorageTierListResponse {
  items: StorageTier[]
  total: number
  offset: number
  limit: number
}

// ============================================================================
// Policy Config Types
// ============================================================================

export interface AgeBasedPolicyConfig {
  after_days?: number
  after_hours?: number
}

export interface AccessBasedPolicyConfig {
  inactive_days?: number
  min_access_count?: number
  access_window_days?: number
}

export interface SizeBasedPolicyConfig {
  min_size_bytes?: number
  min_size_kb?: number
  min_size_mb?: number
  min_size_gb?: number
  tier_max_size_bytes?: number
  tier_max_size_gb?: number
}

export interface ScheduledPolicyConfig {
  on_days?: number[]
  at_hour?: number
  min_age_days?: number
}

export interface CompositePolicyConfig {
  require_all?: boolean
  child_policy_ids?: string[]
}

export interface CustomPolicyConfig {
  predicate_expression: string
  description?: string
}

export type PolicyConfig =
  | AgeBasedPolicyConfig
  | AccessBasedPolicyConfig
  | SizeBasedPolicyConfig
  | ScheduledPolicyConfig
  | CompositePolicyConfig
  | CustomPolicyConfig

// ============================================================================
// Tier Policy Types
// ============================================================================

export interface TierPolicy {
  id: string
  name: string
  description: string | null
  policy_type: TierPolicyType
  from_tier_id: string
  to_tier_id: string
  direction: MigrationDirection
  config: PolicyConfig
  is_active: boolean
  priority: number
  parent_id: string | null
  child_count: number
  from_tier_name: string | null
  to_tier_name: string | null
  created_at: string
  updated_at: string
}

export interface TierPolicyCreate {
  name: string
  description?: string
  policy_type: TierPolicyType
  from_tier_id: string
  to_tier_id: string
  direction?: MigrationDirection
  config?: PolicyConfig
  is_active?: boolean
  priority?: number
  parent_id?: string
}

export interface TierPolicyUpdate {
  name?: string
  description?: string
  policy_type?: TierPolicyType
  from_tier_id?: string
  to_tier_id?: string
  direction?: MigrationDirection
  config?: PolicyConfig
  is_active?: boolean
  priority?: number
  parent_id?: string
}

export interface TierPolicyListResponse {
  items: TierPolicy[]
  total: number
  offset: number
  limit: number
}

export interface TierPolicyWithChildren extends TierPolicy {
  children: TierPolicyWithChildren[]
}

// ============================================================================
// Tiering Config Types
// ============================================================================

export interface TieringConfig {
  id: string
  name: string
  description: string | null
  default_tier_id: string | null
  enable_promotion: boolean
  promotion_threshold: number
  check_interval_hours: number
  batch_size: number
  enable_parallel_migration: boolean
  max_parallel_migrations: number
  is_active: boolean
  default_tier_name: string | null
  created_at: string
  updated_at: string
}

export interface TieringConfigCreate {
  name: string
  description?: string
  default_tier_id?: string
  enable_promotion?: boolean
  promotion_threshold?: number
  check_interval_hours?: number
  batch_size?: number
  enable_parallel_migration?: boolean
  max_parallel_migrations?: number
  is_active?: boolean
}

export interface TieringConfigUpdate {
  name?: string
  description?: string
  default_tier_id?: string
  enable_promotion?: boolean
  promotion_threshold?: number
  check_interval_hours?: number
  batch_size?: number
  enable_parallel_migration?: boolean
  max_parallel_migrations?: number
  is_active?: boolean
}

export interface TieringConfigListResponse {
  items: TieringConfig[]
  total: number
  offset: number
  limit: number
}

// ============================================================================
// Migration History Types
// ============================================================================

export interface MigrationHistory {
  id: string
  policy_id: string | null
  item_id: string
  from_tier_id: string
  to_tier_id: string
  size_bytes: number
  status: MigrationStatus
  error_message: string | null
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  from_tier_name: string | null
  to_tier_name: string | null
  policy_name: string | null
}

export interface MigrationHistoryListResponse {
  items: MigrationHistory[]
  total: number
  offset: number
  limit: number
}

// ============================================================================
// Statistics Types
// ============================================================================

export interface TierStatistics {
  tier_id: string
  tier_name: string
  tier_type: TierType
  item_count: number
  total_size_bytes: number
  total_size_gb: number
  estimated_cost: number | null
  policy_count: number
}

export interface TieringStatistics {
  total_tiers: number
  active_tiers: number
  total_policies: number
  active_policies: number
  composite_policies: number
  total_migrations: number
  successful_migrations: number
  failed_migrations: number
  total_bytes_migrated: number
  tier_stats: TierStatistics[]
}

export interface PolicyTypeInfo {
  type: TierPolicyType
  name: string
  description: string
  config_schema: Record<string, unknown>
}

export interface PolicyTypesResponse {
  policy_types: PolicyTypeInfo[]
}

export interface MessageResponse {
  message: string
}

// ============================================================================
// Policy Execution Types
// ============================================================================

export interface PolicyExecutionRequest {
  dry_run?: boolean
  batch_size?: number
}

export interface MigrationItemResponse {
  item_id: string
  from_tier: string
  to_tier: string
  success: boolean
  size_bytes: number
  error_message: string | null
  duration_ms: number
}

export interface PolicyExecutionResponse {
  policy_id: string
  dry_run: boolean
  start_time: string
  end_time: string
  duration_seconds: number
  items_scanned: number
  items_migrated: number
  items_failed: number
  bytes_migrated: number
  success_rate: number
  errors: string[]
  migrations: MigrationItemResponse[]
}

export interface MigrateItemRequest {
  from_tier_id: string
  to_tier_id: string
}

export interface PolicyExecutionSummary {
  items_scanned: number
  items_migrated: number
  items_failed: number
  bytes_migrated: number
  duration_seconds: number
  success_rate: number
  errors: string[]
}

export interface ProcessPoliciesResponse {
  policies_executed: number
  total_items_scanned: number
  total_items_migrated: number
  total_items_failed: number
  total_bytes_migrated: number
  errors: string[]
  policy_results: PolicyExecutionSummary[]
}

export interface TieringStatusResponse {
  truthound_available: boolean
  tiering_enabled: boolean
  active_config_id: string | null
  active_config_name: string | null
  check_interval_hours: number | null
  active_tiers: number
  active_policies: number
  migrations_last_24h: number
}

// ============================================================================
// Storage Tier API Functions
// ============================================================================

export interface ListTiersParams {
  offset?: number
  limit?: number
  active_only?: boolean
  tier_type?: TierType
}

export async function listStorageTiers(
  params?: ListTiersParams
): Promise<StorageTierListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.offset !== undefined) searchParams.set('offset', String(params.offset))
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params?.active_only) searchParams.set('active_only', 'true')
  if (params?.tier_type) searchParams.set('tier_type', params.tier_type)

  const query = searchParams.toString()
  return request<StorageTierListResponse>(`/tiering/tiers${query ? `?${query}` : ''}`)
}

export async function createStorageTier(data: StorageTierCreate): Promise<StorageTier> {
  return request<StorageTier>('/tiering/tiers', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getStorageTier(tierId: string): Promise<StorageTier> {
  return request<StorageTier>(`/tiering/tiers/${tierId}`)
}

export async function updateStorageTier(
  tierId: string,
  data: StorageTierUpdate
): Promise<StorageTier> {
  return request<StorageTier>(`/tiering/tiers/${tierId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteStorageTier(tierId: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/tiering/tiers/${tierId}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Tier Policy API Functions
// ============================================================================

export interface ListPoliciesParams {
  offset?: number
  limit?: number
  active_only?: boolean
  policy_type?: TierPolicyType
  from_tier_id?: string
  to_tier_id?: string
  parent_id?: string
  root_only?: boolean
}

export async function listTierPolicies(
  params?: ListPoliciesParams
): Promise<TierPolicyListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.offset !== undefined) searchParams.set('offset', String(params.offset))
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params?.active_only) searchParams.set('active_only', 'true')
  if (params?.policy_type) searchParams.set('policy_type', params.policy_type)
  if (params?.from_tier_id) searchParams.set('from_tier_id', params.from_tier_id)
  if (params?.to_tier_id) searchParams.set('to_tier_id', params.to_tier_id)
  if (params?.parent_id) searchParams.set('parent_id', params.parent_id)
  if (params?.root_only) searchParams.set('root_only', 'true')

  const query = searchParams.toString()
  return request<TierPolicyListResponse>(`/tiering/policies${query ? `?${query}` : ''}`)
}

export async function createTierPolicy(data: TierPolicyCreate): Promise<TierPolicy> {
  return request<TierPolicy>('/tiering/policies', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getTierPolicy(policyId: string): Promise<TierPolicy> {
  return request<TierPolicy>(`/tiering/policies/${policyId}`)
}

export async function getTierPolicyTree(policyId: string): Promise<TierPolicyWithChildren> {
  return request<TierPolicyWithChildren>(`/tiering/policies/${policyId}/tree`)
}

export async function updateTierPolicy(
  policyId: string,
  data: TierPolicyUpdate
): Promise<TierPolicy> {
  return request<TierPolicy>(`/tiering/policies/${policyId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteTierPolicy(policyId: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/tiering/policies/${policyId}`, {
    method: 'DELETE',
  })
}

export async function getPolicyTypes(): Promise<PolicyTypesResponse> {
  return request<PolicyTypesResponse>('/tiering/policies/types')
}

// ============================================================================
// Tiering Config API Functions
// ============================================================================

export interface ListConfigsParams {
  offset?: number
  limit?: number
  active_only?: boolean
}

export async function listTieringConfigs(
  params?: ListConfigsParams
): Promise<TieringConfigListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.offset !== undefined) searchParams.set('offset', String(params.offset))
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params?.active_only) searchParams.set('active_only', 'true')

  const query = searchParams.toString()
  return request<TieringConfigListResponse>(`/tiering/configs${query ? `?${query}` : ''}`)
}

export async function createTieringConfig(data: TieringConfigCreate): Promise<TieringConfig> {
  return request<TieringConfig>('/tiering/configs', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getTieringConfig(configId: string): Promise<TieringConfig> {
  return request<TieringConfig>(`/tiering/configs/${configId}`)
}

export async function updateTieringConfig(
  configId: string,
  data: TieringConfigUpdate
): Promise<TieringConfig> {
  return request<TieringConfig>(`/tiering/configs/${configId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteTieringConfig(configId: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/tiering/configs/${configId}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Migration History API Functions
// ============================================================================

export interface ListMigrationsParams {
  offset?: number
  limit?: number
  policy_id?: string
  status?: MigrationStatus
  from_tier_id?: string
  to_tier_id?: string
}

export async function listMigrationHistory(
  params?: ListMigrationsParams
): Promise<MigrationHistoryListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.offset !== undefined) searchParams.set('offset', String(params.offset))
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params?.policy_id) searchParams.set('policy_id', params.policy_id)
  if (params?.status) searchParams.set('status', params.status)
  if (params?.from_tier_id) searchParams.set('from_tier_id', params.from_tier_id)
  if (params?.to_tier_id) searchParams.set('to_tier_id', params.to_tier_id)

  const query = searchParams.toString()
  return request<MigrationHistoryListResponse>(`/tiering/migrations${query ? `?${query}` : ''}`)
}

export async function getMigrationHistory(migrationId: string): Promise<MigrationHistory> {
  return request<MigrationHistory>(`/tiering/migrations/${migrationId}`)
}

// ============================================================================
// Statistics API Functions
// ============================================================================

export async function getTieringStatistics(): Promise<TieringStatistics> {
  return request<TieringStatistics>('/tiering/stats')
}

// ============================================================================
// Policy Execution API Functions
// ============================================================================

/**
 * Execute a tier policy to migrate eligible items.
 */
export async function executePolicy(
  policyId: string,
  options?: PolicyExecutionRequest
): Promise<PolicyExecutionResponse> {
  return request<PolicyExecutionResponse>(`/tiering/policies/${policyId}/execute`, {
    method: 'POST',
    body: options ? JSON.stringify(options) : undefined,
  })
}

/**
 * Migrate a single item between tiers.
 */
export async function migrateItem(
  itemId: string,
  req: MigrateItemRequest
): Promise<MigrationItemResponse> {
  return request<MigrationItemResponse>(`/tiering/items/${itemId}/migrate`, {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

/**
 * Record an access to an item for intelligent tiering.
 */
export async function recordItemAccess(
  itemId: string,
  tierId: string
): Promise<MessageResponse> {
  return request<MessageResponse>(
    `/tiering/items/${itemId}/access?tier_id=${encodeURIComponent(tierId)}`,
    { method: 'POST' }
  )
}

/**
 * Process all active tiering policies.
 */
export async function processAllPolicies(): Promise<ProcessPoliciesResponse> {
  return request<ProcessPoliciesResponse>('/tiering/process', {
    method: 'POST',
  })
}

/**
 * Get tiering system status.
 */
export async function getTieringStatus(): Promise<TieringStatusResponse> {
  return request<TieringStatusResponse>('/tiering/status')
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get human-readable tier type label
 */
export function getTierTypeLabel(type: TierType): string {
  const labels: Record<TierType, string> = {
    hot: 'Hot',
    warm: 'Warm',
    cold: 'Cold',
    archive: 'Archive',
  }
  return labels[type] || type
}

/**
 * Get human-readable policy type label
 */
export function getPolicyTypeLabel(type: TierPolicyType): string {
  const labels: Record<TierPolicyType, string> = {
    age_based: 'Age-Based',
    access_based: 'Access-Based',
    size_based: 'Size-Based',
    scheduled: 'Scheduled',
    composite: 'Composite',
    custom: 'Custom',
  }
  return labels[type] || type
}

/**
 * Get human-readable migration status label
 */
export function getMigrationStatusLabel(status: MigrationStatus): string {
  const labels: Record<MigrationStatus, string> = {
    pending: 'Pending',
    in_progress: 'In Progress',
    completed: 'Completed',
    failed: 'Failed',
  }
  return labels[status] || status
}

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

/**
 * Get policy config summary for display
 */
export function getPolicyConfigSummary(
  type: TierPolicyType,
  config: PolicyConfig
): string {
  switch (type) {
    case 'age_based': {
      const c = config as AgeBasedPolicyConfig
      const parts: string[] = []
      if (c.after_days) parts.push(`${c.after_days}d`)
      if (c.after_hours) parts.push(`${c.after_hours}h`)
      return `After ${parts.join(' ') || '0'}`
    }
    case 'access_based': {
      const c = config as AccessBasedPolicyConfig
      if (c.inactive_days) return `Inactive ${c.inactive_days} days`
      if (c.min_access_count) return `${c.min_access_count}+ accesses in ${c.access_window_days || 7} days`
      return 'Access-based'
    }
    case 'size_based': {
      const c = config as SizeBasedPolicyConfig
      if (c.min_size_gb) return `>= ${c.min_size_gb} GB`
      if (c.min_size_mb) return `>= ${c.min_size_mb} MB`
      if (c.min_size_kb) return `>= ${c.min_size_kb} KB`
      if (c.tier_max_size_gb) return `Tier max ${c.tier_max_size_gb} GB`
      return 'Size-based'
    }
    case 'scheduled': {
      const c = config as ScheduledPolicyConfig
      const days = c.on_days?.map((d) => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d]).join(', ')
      const hour = c.at_hour !== undefined ? `${c.at_hour}:00` : ''
      return `${days || 'Every day'} ${hour}`.trim()
    }
    case 'composite': {
      const c = config as CompositePolicyConfig
      return c.require_all ? 'All conditions (AND)' : 'Any condition (OR)'
    }
    case 'custom': {
      const c = config as CustomPolicyConfig
      return c.description || 'Custom expression'
    }
    default:
      return type
  }
}
