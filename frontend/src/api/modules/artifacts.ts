import { request, ApiError, getStoredSessionToken } from '../core'

export type ArtifactFormat = 'html' | 'csv' | 'json'
export type ArtifactTheme = 'light' | 'dark' | 'professional' | 'minimal' | 'high_contrast'
export type ArtifactLocale =
  | 'en' | 'ko' | 'ja' | 'zh' | 'de' | 'fr' | 'es' | 'pt'
  | 'it' | 'ru' | 'ar' | 'th' | 'vi' | 'id' | 'tr'
export type ArtifactStatus = 'pending' | 'generating' | 'completed' | 'failed' | 'expired'

const API_BASE = '/api/v1'

export interface ArtifactRecord {
  id: string
  workspace_id?: string
  source_id?: string
  source_name?: string
  validation_id?: string
  validation_status?: string
  artifact_type: string
  format: ArtifactFormat
  status: ArtifactStatus
  title: string
  description?: string
  file_path?: string
  external_url?: string
  file_size?: number
  content_hash?: string
  metadata: Record<string, unknown>
  error_message?: string
  generation_time_ms?: number
  expires_at?: string
  downloaded_count: number
  last_downloaded_at?: string
  locale: ArtifactLocale
  theme?: ArtifactTheme
  is_expired: boolean
  download_url?: string
  created_at: string
  updated_at: string
}

export interface ArtifactListResponse {
  data: ArtifactRecord[]
  total: number
  offset: number
  limit: number
}

export interface ArtifactStatistics {
  total_artifacts: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  total_downloads: number
  total_size_bytes: number
}

export interface ArtifactLocaleInfo {
  code: ArtifactLocale
  english_name: string
  native_name: string
  flag: string
  rtl: boolean
}

export interface ArtifactCapabilities {
  formats: ArtifactFormat[]
  themes: ArtifactTheme[]
  locales: ArtifactLocaleInfo[]
  artifact_types: Array<'report' | 'datadocs'>
}

export interface ArtifactGenerateOptions {
  format?: ArtifactFormat
  theme?: ArtifactTheme
  locale?: ArtifactLocale
  title?: string
  include_samples?: boolean
  include_statistics?: boolean
}

export async function listArtifacts(params?: {
  workspace_id?: string
  saved_view_id?: string
  search?: string
  status?: ArtifactStatus
  source_id?: string
  validation_id?: string
  artifact_type?: string
  format?: ArtifactFormat
  include_expired?: boolean
  offset?: number
  limit?: number
}): Promise<ArtifactListResponse> {
  const limit = params?.limit ?? 20
  const offset = params?.offset ?? 0
  const page = Math.floor(offset / limit) + 1

  return request<ArtifactListResponse>('/artifacts', {
    params: {
      workspace_id: params?.workspace_id,
      saved_view_id: params?.saved_view_id,
      search: params?.search,
      status: params?.status,
      source_id: params?.source_id,
      validation_id: params?.validation_id,
      artifact_type: params?.artifact_type,
      format: params?.format,
      include_expired: params?.include_expired,
      page,
      page_size: limit,
      offset,
      limit,
    },
  })
}

export async function getArtifactStatistics(): Promise<ArtifactStatistics> {
  return request<ArtifactStatistics>('/artifacts/statistics')
}

export async function getArtifactCapabilities(): Promise<ArtifactCapabilities> {
  return request<ArtifactCapabilities>('/artifacts/capabilities')
}

export async function getArtifact(artifactId: string): Promise<ArtifactRecord> {
  return request<ArtifactRecord>(`/artifacts/${artifactId}`)
}

export async function deleteArtifact(artifactId: string): Promise<void> {
  await request<void>(`/artifacts/${artifactId}`, { method: 'DELETE' })
}

export async function cleanupExpiredArtifacts(): Promise<{ deleted: number }> {
  return request<{ deleted: number }>('/artifacts/cleanup', { method: 'POST' })
}

export async function downloadArtifact(artifactId: string): Promise<Blob> {
  const url = `${API_BASE}/artifacts/${artifactId}/download`
  const headers = new Headers()
  const sessionToken = getStoredSessionToken()
  if (sessionToken) {
    headers.set('X-Truthound-Session', sessionToken)
  }
  const response = await fetch(url, { headers })
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText)
  }
  return response.blob()
}

export async function generateReportArtifact(
  validationId: string,
  options?: ArtifactGenerateOptions
): Promise<ArtifactRecord> {
  return request<ArtifactRecord>(`/artifacts/validations/${validationId}/report`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function generateDataDocsArtifact(
  validationId: string,
  options?: { title?: string; theme?: ArtifactTheme }
): Promise<ArtifactRecord> {
  return request<ArtifactRecord>(`/artifacts/validations/${validationId}/datadocs`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}
