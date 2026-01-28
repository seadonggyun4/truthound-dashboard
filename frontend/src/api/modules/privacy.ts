/**
 * Privacy API - PII scanning and data masking.
 */
import { request } from '../core'

// ============================================================================
// PII Scan Types
// ============================================================================

export const PII_TYPES = [
  'email',
  'phone',
  'ssn',
  'credit_card',
  'ip_address',
  'date_of_birth',
  'address',
  'name',
  'passport',
  'driver_license',
  'national_id',
  'bank_account',
  'medical_record',
  'biometric',
] as const

export type Regulation = 'gdpr' | 'ccpa' | 'lgpd'

export const REGULATIONS: { value: Regulation; label: string; description: string }[] = [
  { value: 'gdpr', label: 'GDPR', description: 'General Data Protection Regulation (EU)' },
  { value: 'ccpa', label: 'CCPA', description: 'California Consumer Privacy Act (US)' },
  { value: 'lgpd', label: 'LGPD', description: 'Lei Geral de Proteção de Dados (Brazil)' },
]

export interface PIIFinding {
  column: string
  pii_type: string
  confidence: number
  sample_count: number
  sample_values?: string[]
}

export interface RegulationViolation {
  regulation: Regulation
  column: string
  pii_type: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export interface PIIScan {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  total_columns_scanned: number
  columns_with_pii: number
  total_findings: number
  has_violations: boolean
  total_violations: number
  row_count?: number
  column_count?: number
  min_confidence: number
  regulations_checked?: string[] | null
  findings: PIIFinding[]
  violations: RegulationViolation[]
  error_message?: string
  duration_ms?: number
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface PIIScanListResponse {
  data: PIIScan[]
  total: number
  limit: number
}

// Note: truthound's th.scan() does not support any configuration parameters.
// The scan runs on all columns with default settings.
// PIIScanOptions interface removed as it was unused.

// ============================================================================
// Data Masking Types
// ============================================================================

export type MaskingStrategy = 'redact' | 'hash' | 'fake'

export interface DataMask {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  strategy: MaskingStrategy
  output_path?: string
  columns_masked?: string[]
  auto_detected: boolean
  row_count?: number
  column_count?: number
  duration_ms?: number
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface DataMaskListItem {
  id: string
  source_id: string
  source_name?: string
  status: string
  strategy: string
  columns_masked: number
  row_count?: number
  duration_ms?: number
  created_at: string
}

export interface DataMaskListResponse {
  data: DataMaskListItem[]
  total: number
  limit: number
}

export interface MaskOptions {
  columns?: string[]
  strategy?: MaskingStrategy
  // Note: output_format removed - truthound's th.mask() does not support this parameter.
  // Output format is determined by the dashboard layer, not by truthound.
}

// ============================================================================
// PII Scan API Functions
// ============================================================================

export async function runPIIScan(sourceId: string): Promise<PIIScan> {
  return request<PIIScan>(`/scans/sources/${sourceId}/scan`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export async function getPIIScan(id: string): Promise<PIIScan> {
  return request<PIIScan>(`/scans/${id}`)
}

export async function listSourcePIIScans(
  sourceId: string,
  params?: { limit?: number }
): Promise<PIIScanListResponse> {
  return request<PIIScanListResponse>(
    `/scans/sources/${sourceId}/scans`,
    { params }
  )
}

export async function getLatestPIIScan(sourceId: string): Promise<PIIScan | null> {
  return request<PIIScan | null>(`/scans/sources/${sourceId}/scans/latest`)
}

// ============================================================================
// Data Masking API Functions
// ============================================================================

export async function runDataMask(
  sourceId: string,
  options?: MaskOptions
): Promise<DataMask> {
  return request<DataMask>(`/masks/sources/${sourceId}/mask`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getDataMask(id: string): Promise<DataMask> {
  return request<DataMask>(`/masks/${id}`)
}

export async function listSourceDataMasks(
  sourceId: string,
  params?: { limit?: number }
): Promise<DataMaskListResponse> {
  return request<DataMaskListResponse>(
    `/masks/sources/${sourceId}/masks`,
    { params }
  )
}

export async function getLatestDataMask(sourceId: string): Promise<DataMask> {
  return request<DataMask>(`/masks/sources/${sourceId}/masks/latest`)
}
