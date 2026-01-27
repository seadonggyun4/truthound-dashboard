/**
 * DataSources API client
 *
 * Handles all data source related API operations.
 * Based on truthound framework datasources module.
 */

import { apiClient } from './base'
import type {
  SourceType,
  DataSource,
  DataSourceCapability,
  ColumnType,
  ConnectionTestResult,
  ConnectionTestMetadata,
  CreateSourceRequest,
  UpdateSourceRequest,
  TestConnectionRequest,
  TestConnectionResponse,
  SourceTypeDefinition,
  SourceCategoryDefinition,
} from '@/types/datasources'

// ============================================================================
// Types for API Responses
// ============================================================================

export interface SourceListResponse {
  items: DataSource[]
  total: number
  page: number
  page_size: number
}

export interface SourceListParams {
  /** Search by name */
  search?: string
  /** Filter by type */
  type?: SourceType
  /** Filter by tags */
  tags?: string[]
  /** Page number (1-indexed) */
  page?: number
  /** Items per page */
  page_size?: number
  /** Sort field */
  sort_by?: 'name' | 'created_at' | 'updated_at' | 'type'
  /** Sort order */
  sort_order?: 'asc' | 'desc'
}

export interface SchemaResponse {
  columns: Array<{
    name: string
    type: ColumnType
    nullable: boolean
    description?: string
  }>
  row_count?: number
  sampled?: boolean
  sample_size?: number
}

export interface ProfileResponse {
  columns: Record<
    string,
    {
      type: ColumnType
      null_count: number
      null_percentage: number
      distinct_count: number
      min_value?: unknown
      max_value?: unknown
      mean?: number
      std_dev?: number
      sample_values?: unknown[]
    }
  >
  row_count: number
  profiled_at: string
}

// ============================================================================
// Source Types API
// ============================================================================

/**
 * Get all available source type definitions.
 */
export async function getSourceTypes(): Promise<SourceTypeDefinition[]> {
  return apiClient.get<SourceTypeDefinition[]>('/sources/types')
}

/**
 * Get source type definition by type.
 */
export async function getSourceTypeDefinition(
  type: SourceType
): Promise<SourceTypeDefinition> {
  return apiClient.get<SourceTypeDefinition>(`/sources/types/${type}`)
}

/**
 * Get all source categories.
 */
export async function getSourceCategories(): Promise<SourceCategoryDefinition[]> {
  return apiClient.get<SourceCategoryDefinition[]>('/sources/categories')
}

/**
 * Get capabilities for a source type.
 */
export async function getSourceTypeCapabilities(
  type: SourceType
): Promise<DataSourceCapability[]> {
  const definition = await getSourceTypeDefinition(type)
  return definition.capabilities
}

// ============================================================================
// Sources CRUD API
// ============================================================================

/**
 * List all data sources with optional filters.
 */
export async function listSources(
  params?: SourceListParams
): Promise<SourceListResponse> {
  return apiClient.get<SourceListResponse>('/sources', {
    params: params as Record<string, string | number | boolean | string[] | undefined | null> | undefined
  })
}

/**
 * Get a single data source by ID.
 */
export async function getSource(id: string): Promise<DataSource> {
  return apiClient.get<DataSource>(`/sources/${id}`)
}

/**
 * Create a new data source.
 */
export async function createSource(data: CreateSourceRequest): Promise<DataSource> {
  return apiClient.post<DataSource>('/sources', data)
}

/**
 * Update an existing data source.
 */
export async function updateSource(
  id: string,
  data: UpdateSourceRequest
): Promise<DataSource> {
  return apiClient.patch<DataSource>(`/sources/${id}`, data)
}

/**
 * Delete a data source.
 */
export async function deleteSource(id: string): Promise<void> {
  return apiClient.delete(`/sources/${id}`)
}

// ============================================================================
// Connection Testing API
// ============================================================================

/**
 * Test a connection without saving.
 */
export async function testConnection(
  data: TestConnectionRequest
): Promise<TestConnectionResponse> {
  return apiClient.post<TestConnectionResponse>('/sources/test', data)
}

/**
 * Test connection for an existing source.
 */
export async function testSourceConnection(
  id: string
): Promise<ConnectionTestResult> {
  return apiClient.post<ConnectionTestResult>(`/sources/${id}/test`)
}

// ============================================================================
// Schema & Profile API
// ============================================================================

/**
 * Get schema for a data source.
 */
export async function getSourceSchema(id: string): Promise<SchemaResponse> {
  return apiClient.get<SchemaResponse>(`/sources/${id}/schema`)
}

/**
 * Learn/infer schema for a data source.
 */
export async function learnSourceSchema(
  id: string,
  options?: {
    infer_constraints?: boolean
    sample_size?: number
  }
): Promise<SchemaResponse> {
  return apiClient.post<SchemaResponse>(`/sources/${id}/learn`, options)
}

/**
 * Update schema for a data source.
 */
export async function updateSourceSchema(
  id: string,
  schema: SchemaResponse
): Promise<SchemaResponse> {
  return apiClient.put<SchemaResponse>(`/sources/${id}/schema`, schema)
}

/**
 * Get profile for a data source.
 */
export async function getSourceProfile(id: string): Promise<ProfileResponse> {
  return apiClient.get<ProfileResponse>(`/sources/${id}/profile`)
}

/**
 * Run profiling on a data source.
 */
export async function profileSource(
  id: string,
  options?: {
    sample_size?: number
    columns?: string[]
  }
): Promise<ProfileResponse> {
  return apiClient.post<ProfileResponse>(`/sources/${id}/profile`, options)
}

// ============================================================================
// Validation API
// ============================================================================

export interface ValidatorConfig {
  name: string
  enabled: boolean
  params?: Record<string, unknown>
  severity?: 'critical' | 'error' | 'warning' | 'info'
}

export interface ValidationRequest {
  /** Validators to run */
  validators?: string[]
  /** Validator configurations */
  validator_configs?: ValidatorConfig[]
  /** Columns to validate */
  columns?: string[]
  /** Minimum severity to report */
  min_severity?: 'critical' | 'error' | 'warning' | 'info'
  /** Raise exception on failure */
  strict?: boolean
  /** Run validators in parallel */
  parallel?: boolean
  /** Max parallel workers */
  max_workers?: number
  /** Push operations to database */
  pushdown?: boolean
  /** Sample size for large datasets */
  sample_size?: number
}

export interface ValidationResult {
  run_id: string
  source_id: string
  status: 'success' | 'failure' | 'error'
  issues: ValidationIssue[]
  statistics: {
    total_validators: number
    passed: number
    failed: number
    errors: number
    duration_ms: number
  }
  run_at: string
}

export interface ValidationIssue {
  validator: string
  column?: string
  severity: 'critical' | 'error' | 'warning' | 'info'
  message: string
  details?: Record<string, unknown>
  row_count?: number
  sample_values?: unknown[]
}

/**
 * Run validation on a data source.
 */
export async function runValidation(
  id: string,
  options?: ValidationRequest
): Promise<ValidationResult> {
  return apiClient.post<ValidationResult>(`/sources/${id}/validate`, options)
}

// ============================================================================
// Drift Detection API
// ============================================================================

export interface DriftCompareRequest {
  /** Reference source ID */
  reference_id: string
  /** Current source ID */
  current_id: string
  /** Detection method */
  method?: 'auto' | 'ks' | 'psi' | 'chi2' | 'js' | 'kl' | 'wasserstein' | 'cvm' | 'anderson'
  /** Columns to compare */
  columns?: string[]
  /** Drift threshold */
  threshold?: number
  /** Multiple testing correction */
  correction?: 'none' | 'bonferroni' | 'holm' | 'bh'
  /** Sample size */
  sample_size?: number
}

export interface DriftResult {
  has_drift: boolean
  columns: Record<
    string,
    {
      has_drift: boolean
      method: string
      statistic: number
      p_value: number
      threshold: number
    }
  >
  summary: {
    total_columns: number
    drifted_columns: number
    drift_percentage: number
  }
  compared_at: string
}

/**
 * Compare two data sources for drift.
 */
export async function compareDrift(
  request: DriftCompareRequest
): Promise<DriftResult> {
  return apiClient.post<DriftResult>('/drift/compare', request)
}

// ============================================================================
// PII Scanning API
// ============================================================================

export interface ScanRequest {
  /** Columns to scan */
  columns?: string[]
  /** Regulations to check */
  regulations?: ('gdpr' | 'ccpa' | 'lgpd')[]
  /** Minimum confidence score */
  min_confidence?: number
}

export interface ScanResult {
  findings: PIIFinding[]
  summary: {
    total_columns_scanned: number
    columns_with_pii: number
    pii_types_found: string[]
  }
  scanned_at: string
}

export interface PIIFinding {
  column: string
  pii_type: string
  confidence: number
  regulations: string[]
  sample_matches?: string[]
  recommendation?: string
}

/**
 * Scan a data source for PII.
 */
export async function scanSource(
  id: string,
  options?: ScanRequest
): Promise<ScanResult> {
  return apiClient.post<ScanResult>(`/sources/${id}/scan`, options)
}

// ============================================================================
// Data Masking API
// ============================================================================

export interface MaskRequest {
  /** Columns to mask */
  columns?: string[]
  /** Masking strategy */
  strategy?: 'redact' | 'hash' | 'fake'
  /** Output format */
  output_format?: 'csv' | 'parquet' | 'json'
  /** Output path */
  output_path?: string
}

export interface MaskResult {
  output_path: string
  columns_masked: string[]
  row_count: number
  masked_at: string
}

/**
 * Mask sensitive data in a source.
 */
export async function maskSource(
  id: string,
  options: MaskRequest
): Promise<MaskResult> {
  return apiClient.post<MaskResult>(`/masks/sources/${id}/mask`, options)
}

// ============================================================================
// Bulk Operations
// ============================================================================

/**
 * Delete multiple sources.
 */
export async function deleteSources(ids: string[]): Promise<{
  deleted_count: number
  failed_ids: string[]
  total_requested: number
}> {
  const response = await apiClient.post<{
    success: boolean
    data: {
      deleted_count: number
      failed_ids: string[]
      total_requested: number
    }
  }>('/sources/bulk-delete', { ids })
  return response.data
}

/**
 * Tag multiple sources.
 */
export async function tagSources(
  ids: string[],
  tags: string[],
  action: 'add' | 'remove' | 'set'
): Promise<void> {
  return apiClient.post('/sources/bulk/tag', { ids, tags, action })
}

/**
 * Test connections for multiple sources.
 */
export async function testSourcesConnections(
  ids: string[]
): Promise<Record<string, ConnectionTestResult>> {
  return apiClient.post<Record<string, ConnectionTestResult>>(
    '/sources/bulk/test',
    { ids }
  )
}

// ============================================================================
// Export for convenience
// ============================================================================

export const datasourcesApi = {
  // Source types
  getSourceTypes,
  getSourceTypeDefinition,
  getSourceCategories,
  getSourceTypeCapabilities,

  // CRUD
  list: listSources,
  get: getSource,
  create: createSource,
  update: updateSource,
  delete: deleteSource,

  // Connection
  testConnection,
  testSourceConnection,

  // Schema & Profile
  getSchema: getSourceSchema,
  learnSchema: learnSourceSchema,
  updateSchema: updateSourceSchema,
  getProfile: getSourceProfile,
  profile: profileSource,

  // Validation
  validate: runValidation,

  // Drift
  compareDrift,

  // Privacy
  scan: scanSource,
  mask: maskSource,

  // Bulk
  bulkDelete: deleteSources,
  bulkTag: tagSources,
  bulkTest: testSourcesConnections,
}

export default datasourcesApi
