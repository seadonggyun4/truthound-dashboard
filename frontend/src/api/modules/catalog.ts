/**
 * Catalog API - Data assets management.
 */
import { request } from '../core'
import type { OkResponse } from '../core'
import type { GlossaryTermSummary } from './glossary'

// ============================================================================
// Types
// ============================================================================

export type AssetType = 'table' | 'file' | 'api'
export type SensitivityLevel = 'public' | 'internal' | 'confidential' | 'restricted'

export interface AssetTag {
  id: string
  asset_id: string
  tag_name: string
  tag_value?: string
  created_at: string
}

export interface AssetColumn {
  id: string
  asset_id: string
  name: string
  data_type?: string
  description?: string
  is_nullable: boolean
  is_primary_key: boolean
  term_id?: string
  sensitivity_level?: SensitivityLevel
  created_at: string
  term?: GlossaryTermSummary
}

export interface SourceSummary {
  id: string
  name: string
  type: string
}

export interface CatalogAsset {
  id: string
  name: string
  asset_type: AssetType
  source_id?: string
  description?: string
  owner_id?: string
  quality_score?: number
  created_at: string
  updated_at: string
  source?: SourceSummary
  columns: AssetColumn[]
  tags: AssetTag[]
}

export interface AssetListItem {
  id: string
  name: string
  asset_type: AssetType
  source_id?: string
  source_name?: string
  quality_score?: number
  tag_count: number
  column_count: number
  updated_at: string
}

export interface AssetCreate {
  name: string
  asset_type: AssetType
  source_id?: string
  description?: string
  owner_id?: string
}

export interface AssetUpdate {
  name?: string
  asset_type?: AssetType
  source_id?: string
  description?: string
  owner_id?: string
  quality_score?: number
}

export interface ColumnCreate {
  name: string
  data_type?: string
  description?: string
  is_nullable?: boolean
  is_primary_key?: boolean
  sensitivity_level?: SensitivityLevel
}

export interface ColumnUpdate {
  name?: string
  data_type?: string
  description?: string
  is_nullable?: boolean
  is_primary_key?: boolean
  sensitivity_level?: SensitivityLevel
}

export interface TagCreate {
  tag_name: string
  tag_value?: string
}

// ============================================================================
// Assets API
// ============================================================================

export interface AssetListResponse {
  data: AssetListItem[]
  total: number
  offset: number
  limit: number
}

export async function getAssets(params?: {
  search?: string
  asset_type?: string
  source_id?: string
  skip?: number
  limit?: number
}): Promise<AssetListItem[]> {
  const response = await request<AssetListResponse>('/catalog/assets', { params })
  return response.data
}

export async function getAsset(id: string): Promise<CatalogAsset> {
  return request<CatalogAsset>(`/catalog/assets/${id}`)
}

export async function createAsset(data: AssetCreate): Promise<CatalogAsset> {
  return request<CatalogAsset>('/catalog/assets', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateAsset(id: string, data: AssetUpdate): Promise<CatalogAsset> {
  return request<CatalogAsset>(`/catalog/assets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteAsset(id: string): Promise<OkResponse> {
  return request<OkResponse>(`/catalog/assets/${id}`, { method: 'DELETE' })
}

// ============================================================================
// Columns API
// ============================================================================

export interface ColumnListResponse {
  data: AssetColumn[]
  total: number
}

export async function getAssetColumns(assetId: string): Promise<AssetColumn[]> {
  const response = await request<ColumnListResponse>(`/catalog/assets/${assetId}/columns`)
  return response.data
}

export async function createColumn(assetId: string, data: ColumnCreate): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/assets/${assetId}/columns`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateColumn(columnId: string, data: ColumnUpdate): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteColumn(columnId: string): Promise<OkResponse> {
  return request<OkResponse>(`/catalog/columns/${columnId}`, { method: 'DELETE' })
}

export async function mapColumnToTerm(columnId: string, termId: string): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}/term`, {
    method: 'PUT',
    body: JSON.stringify({ term_id: termId }),
  })
}

export async function unmapColumnFromTerm(columnId: string): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}/term`, { method: 'DELETE' })
}

// ============================================================================
// Tags API
// ============================================================================

export async function getAssetTags(assetId: string): Promise<AssetTag[]> {
  return request<AssetTag[]>(`/catalog/assets/${assetId}/tags`)
}

export async function addTag(assetId: string, data: TagCreate): Promise<AssetTag> {
  return request<AssetTag>(`/catalog/assets/${assetId}/tags`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function removeTag(tagId: string): Promise<OkResponse> {
  return request<OkResponse>(`/catalog/tags/${tagId}`, { method: 'DELETE' })
}
