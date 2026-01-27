/**
 * Schemas API - Schema learning and management.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export interface Schema {
  id: string
  source_id: string
  schema_yaml: string
  schema_json?: Record<string, unknown>
  row_count?: number
  column_count?: number
  columns: string[]
  version?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// ============================================================================
// API Functions
// ============================================================================

export async function getSourceSchema(sourceId: string): Promise<Schema | null> {
  return request<Schema | null>(`/sources/${sourceId}/schema`)
}

export async function learnSchema(
  sourceId: string,
  data?: { infer_constraints?: boolean }
): Promise<Schema> {
  return request<Schema>(`/sources/${sourceId}/learn`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
}

export async function updateSchema(
  sourceId: string,
  schemaYaml: string
): Promise<Schema> {
  return request<Schema>(`/sources/${sourceId}/schema`, {
    method: 'PUT',
    body: JSON.stringify({ schema_yaml: schemaYaml }),
  })
}
