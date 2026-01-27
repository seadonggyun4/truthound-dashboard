/**
 * Schema Evolution API - Schema versioning and change detection.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export type SchemaChangeType =
  | 'column_added'
  | 'column_removed'
  | 'type_changed'
  | 'nullable_changed'
  | 'constraint_changed'
  | 'column_renamed'

export type SchemaChangeSeverity = 'breaking' | 'warning' | 'non_breaking'

export interface SchemaVersionSummary {
  id: string
  version_number: number
  column_count: number
  created_at: string
}

export interface SchemaVersionResponse {
  id: string
  source_id: string
  schema_id: string
  version_number: number
  column_count: number
  columns: string[]
  schema_hash: string
  column_snapshot: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface SchemaChangeDetails {
  is_compatible?: boolean
  old_type_normalized?: string
  new_type_normalized?: string
  constraint_type?: string
  nullable?: boolean
  reason?: string
}

export interface SchemaChangeResponse {
  id: string
  source_id: string
  from_version_id: string | null
  to_version_id: string
  change_type: SchemaChangeType
  column_name: string
  old_value: string | null
  new_value: string | null
  severity: SchemaChangeSeverity
  description: string
  details?: SchemaChangeDetails
  created_at: string
}

export interface SchemaEvolutionSummary {
  source_id: string
  current_version: number
  total_versions: number
  total_changes: number
  breaking_changes: number
  last_change_at: string | null
}

export interface SchemaEvolutionResponse {
  source_id: string
  source_name: string
  from_version: number | null
  to_version: number
  has_changes: boolean
  total_changes: number
  breaking_changes: number
  changes: SchemaChangeResponse[]
  detected_at: string
}

// ============================================================================
// API Functions
// ============================================================================

export async function listSchemaVersions(
  sourceId: string,
  params?: { limit?: number; offset?: number }
): Promise<{ versions: SchemaVersionSummary[]; total: number; source_id: string }> {
  return request(`/sources/${sourceId}/schema/versions`, { params })
}

export async function getSchemaVersion(versionId: string): Promise<SchemaVersionResponse> {
  return request(`/schema/versions/${versionId}`)
}

export async function listSchemaChanges(
  sourceId: string,
  params?: { limit?: number; offset?: number }
): Promise<{ changes: SchemaChangeResponse[]; total: number; source_id: string }> {
  return request(`/sources/${sourceId}/schema/changes`, { params })
}

export async function detectSchemaChanges(
  sourceId: string,
  options?: { force_relearn?: boolean }
): Promise<SchemaEvolutionResponse> {
  return request(`/sources/${sourceId}/schema/detect-changes`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getSchemaEvolutionSummary(sourceId: string): Promise<SchemaEvolutionSummary> {
  return request(`/sources/${sourceId}/schema/evolution/summary`)
}
