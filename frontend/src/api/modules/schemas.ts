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

/**
 * Options for schema learning.
 */
export interface LearnSchemaOptions {
  /** Infer constraints (min/max, allowed values) from data statistics */
  infer_constraints?: boolean
  /** Maximum unique values for categorical detection (1-1000). Default: 20 */
  categorical_threshold?: number
  /** Number of rows to sample for large datasets. If null, uses all rows. */
  sample_size?: number
}

export async function learnSchema(
  sourceId: string,
  options?: LearnSchemaOptions
): Promise<Schema> {
  return request<Schema>(`/sources/${sourceId}/learn`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
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
