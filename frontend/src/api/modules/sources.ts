/**
 * Sources API - Data source management.
 */
import { request } from '../core'
import type { PaginatedResponse, MessageResponse } from '../core'

// ============================================================================
// Source Types and Definitions
// ============================================================================

/**
 * All supported source types.
 */
export type SourceType =
  // File-based
  | 'file'
  | 'csv'
  | 'parquet'
  | 'json'
  | 'ndjson'
  | 'jsonl'
  // DataFrame
  | 'polars'
  | 'pandas'
  // Core SQL
  | 'sqlite'
  | 'postgresql'
  | 'mysql'
  // Cloud Data Warehouses
  | 'bigquery'
  | 'snowflake'
  | 'redshift'
  | 'databricks'
  // Enterprise
  | 'oracle'
  | 'sqlserver'
  // NoSQL (async)
  | 'mongodb'
  | 'elasticsearch'
  // Streaming (async)
  | 'kafka'
  // Big Data
  | 'spark'

/**
 * Source type categories for UI grouping.
 */
export type SourceCategory = 'file' | 'database' | 'warehouse' | 'bigdata' | 'nosql' | 'streaming'

/**
 * Data source capabilities.
 */
export type DataSourceCapability =
  | 'lazy_evaluation'
  | 'sql_pushdown'
  | 'sampling'
  | 'streaming'
  | 'schema_inference'
  | 'row_count'

/**
 * Field types for dynamic form rendering.
 */
export type FieldType = 'text' | 'password' | 'number' | 'select' | 'boolean' | 'file_path' | 'textarea'

export interface FieldOption {
  value: string
  label: string
}

export interface FieldDefinition {
  name: string
  label: string
  type: FieldType
  required: boolean
  placeholder: string
  description: string
  default?: unknown
  options?: FieldOption[]
  min_value?: number
  max_value?: number
  depends_on?: string
  depends_value?: unknown
}

export interface SourceTypeDefinition {
  type: SourceType
  name: string
  description: string
  icon: string
  category: SourceCategory
  fields: FieldDefinition[]
  required_fields: string[]
  optional_fields: string[]
  docs_url?: string
  capabilities?: DataSourceCapability[]
  required_package?: string
  is_async?: boolean
}

export interface SourceCategoryDefinition {
  value: SourceCategory
  label: string
  description: string
}

export interface SourceTypesResponse {
  types: SourceTypeDefinition[]
  categories: SourceCategoryDefinition[]
}

// ============================================================================
// Source Model
// ============================================================================

export interface Source {
  id: string
  name: string
  type: SourceType
  config: Record<string, unknown>
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_validated_at?: string
  has_schema: boolean
  latest_validation_status?: string
}

export type SourceListResponse = PaginatedResponse<Source>

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get capabilities for a source type.
 */
export function getSourceTypeCapabilities(type: string): DataSourceCapability[] {
  const lowerType = type.toLowerCase()

  if (['csv', 'ndjson', 'jsonl', 'parquet'].includes(lowerType)) {
    return ['lazy_evaluation', 'sampling', 'schema_inference']
  }
  if (lowerType === 'parquet') {
    return ['lazy_evaluation', 'sampling', 'schema_inference', 'row_count']
  }
  if (lowerType === 'json') {
    return ['schema_inference']
  }
  if (lowerType === 'file') {
    return ['lazy_evaluation', 'sampling', 'schema_inference']
  }
  if (isSqlSourceType(lowerType)) {
    return ['sql_pushdown', 'sampling', 'schema_inference', 'row_count']
  }
  if (['mongodb', 'elasticsearch'].includes(lowerType)) {
    return ['sampling', 'schema_inference', 'streaming']
  }
  if (['kafka'].includes(lowerType)) {
    return ['streaming', 'sampling']
  }

  return ['schema_inference']
}

/**
 * Human-readable labels for capabilities.
 */
export const CAPABILITY_LABELS: Record<DataSourceCapability, { label: string; description: string }> = {
  lazy_evaluation: {
    label: 'Lazy Evaluation',
    description: 'Supports deferred execution for efficient processing',
  },
  sql_pushdown: {
    label: 'SQL Pushdown',
    description: 'Can push validation operations to the database server',
  },
  sampling: {
    label: 'Efficient Sampling',
    description: 'Supports efficient random sampling for large datasets',
  },
  streaming: {
    label: 'Streaming',
    description: 'Supports streaming/chunked reads for real-time data',
  },
  schema_inference: {
    label: 'Schema Inference',
    description: 'Can automatically detect column types',
  },
  row_count: {
    label: 'Fast Row Count',
    description: 'Can get row count without full scan',
  },
}

export function isFileSourceType(type: string): boolean {
  return ['file', 'csv', 'parquet', 'json', 'ndjson', 'jsonl'].includes(type.toLowerCase())
}

export function isSqlSourceType(type: string): boolean {
  return [
    'sqlite',
    'postgresql',
    'mysql',
    'bigquery',
    'snowflake',
    'redshift',
    'databricks',
    'oracle',
    'sqlserver',
  ].includes(type.toLowerCase())
}

export function isAsyncSourceType(type: string): boolean {
  return ['mongodb', 'elasticsearch', 'kafka'].includes(type.toLowerCase())
}

// ============================================================================
// Test Connection
// ============================================================================

export interface TestConnectionResult {
  connected: boolean
  message?: string
  error?: string
}

// ============================================================================
// API Functions
// ============================================================================

export async function listSources(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<SourceListResponse> {
  return request<SourceListResponse>('/sources', { params })
}

export async function getSource(id: string): Promise<Source> {
  return request<Source>(`/sources/${id}`)
}

export async function createSource(data: {
  name: string
  type: string
  config: Record<string, unknown>
  description?: string
}): Promise<Source> {
  return request<Source>('/sources', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateSource(
  id: string,
  data: {
    name?: string
    config?: Record<string, unknown>
    description?: string
    is_active?: boolean
  }
): Promise<Source> {
  return request<Source>(`/sources/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteSource(id: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/sources/${id}`, {
    method: 'DELETE',
  })
}

export interface BulkDeleteResponse {
  deleted_count: number
  failed_ids: string[]
  total_requested: number
}

export async function deleteSources(ids: string[]): Promise<BulkDeleteResponse> {
  return request<BulkDeleteResponse>('/sources/bulk-delete', {
    method: 'POST',
    body: JSON.stringify({ ids }),
  })
}

export async function testSourceConnection(
  sourceId: string
): Promise<TestConnectionResult> {
  return request<TestConnectionResult>(`/sources/${sourceId}/test`, { method: 'POST' })
}

export async function getSupportedSourceTypes(): Promise<SourceTypesResponse> {
  return request<SourceTypesResponse>('/sources/types/supported')
}

export async function testConnectionConfig(
  type: SourceType,
  config: Record<string, unknown>
): Promise<TestConnectionResult> {
  return request<TestConnectionResult>('/sources/test-connection', {
    method: 'POST',
    body: JSON.stringify({ type, config }),
  })
}
