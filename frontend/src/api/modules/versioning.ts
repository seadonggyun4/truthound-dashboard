/**
 * Versioning API - Validation result versioning and rollback.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export type VersioningStrategy = 'incremental' | 'semantic' | 'timestamp' | 'gitlike'

export interface VersionInfo {
  version_id: string
  version_number: string
  validation_id: string
  source_id: string
  strategy: VersioningStrategy
  created_at: string
  parent_version_id: string | null
  metadata: Record<string, unknown>
  content_hash: string | null
}

export interface VersionListResponse {
  data: VersionInfo[]
  total: number
  source_id: string
}

export interface VersionDiff {
  from_version: VersionInfo
  to_version: VersionInfo
  issues_added: Array<Record<string, unknown>>
  issues_removed: Array<Record<string, unknown>>
  issues_changed: Array<{
    key: string
    from: Record<string, unknown>
    to: Record<string, unknown>
  }>
  summary_changes: Record<string, unknown>
  has_changes: boolean
}

export interface VersionHistoryResponse {
  data: VersionInfo[]
  depth: number
}

export interface CreateVersionResponse {
  version: VersionInfo
  message: string
}

export interface RollbackAvailabilityResponse {
  can_rollback: boolean
  current_version_id: string | null
  available_versions: number
  rollback_targets: VersionInfo[]
}

export interface RollbackResponse {
  source_id: string
  from_version: VersionInfo | null
  to_version: VersionInfo | null
  new_validation_id: string | null
  message: string
  rolled_back_at: string
}

// ============================================================================
// API Functions
// ============================================================================

export async function listVersions(
  sourceId: string,
  params?: { limit?: number }
): Promise<VersionListResponse> {
  return request<VersionListResponse>(`/versions/sources/${sourceId}`, { params })
}

export async function getVersion(versionId: string): Promise<VersionInfo> {
  return request<VersionInfo>(`/versions/${versionId}`)
}

export async function getLatestVersion(sourceId: string): Promise<VersionInfo> {
  return request<VersionInfo>(`/versions/sources/${sourceId}/latest`)
}

export async function compareVersions(
  fromVersionId: string,
  toVersionId: string
): Promise<VersionDiff> {
  return request<VersionDiff>('/versions/compare', {
    method: 'POST',
    body: JSON.stringify({
      from_version_id: fromVersionId,
      to_version_id: toVersionId,
    }),
  })
}

export async function getVersionHistory(
  versionId: string,
  params?: { depth?: number }
): Promise<VersionHistoryResponse> {
  return request<VersionHistoryResponse>(`/versions/${versionId}/history`, { params })
}

export async function createVersion(data: {
  validation_id: string
  strategy?: VersioningStrategy
  metadata?: Record<string, unknown>
}): Promise<CreateVersionResponse> {
  return request<CreateVersionResponse>('/versions/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function checkRollbackAvailability(
  sourceId: string
): Promise<RollbackAvailabilityResponse> {
  return request<RollbackAvailabilityResponse>(
    `/versions/sources/${sourceId}/rollback-availability`
  )
}

export async function rollbackToVersion(
  sourceId: string,
  targetVersionId: string,
  createNewValidation = true
): Promise<RollbackResponse> {
  return request<RollbackResponse>(`/versions/sources/${sourceId}/rollback`, {
    method: 'POST',
    body: JSON.stringify({
      target_version_id: targetVersionId,
      create_new_validation: createNewValidation,
    }),
  })
}
