/**
 * Glossary API - Business terms management.
 */
import { request } from '../core'
import type { OkResponse } from '../core'

// ============================================================================
// Types
// ============================================================================

export interface GlossaryCategory {
  id: string
  name: string
  description?: string
  parent_id?: string
  created_at: string
  updated_at: string
  children?: GlossaryCategory[]
}

export interface GlossaryTermSummary {
  id: string
  name: string
  definition: string
}

export interface GlossaryTerm {
  id: string
  name: string
  definition: string
  category_id?: string
  status: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
  created_at: string
  updated_at: string
  category?: GlossaryCategory
  synonyms: GlossaryTermSummary[]
  related_terms: GlossaryTermSummary[]
}

export interface TermRelationship {
  id: string
  source_term_id: string
  target_term_id: string
  relationship_type: 'synonym' | 'related' | 'parent' | 'child'
  created_at: string
  source_term: GlossaryTermSummary
  target_term: GlossaryTermSummary
}

export interface TermHistory {
  id: string
  term_id: string
  field_name: string
  old_value?: string
  new_value?: string
  changed_by?: string
  changed_at: string
}

export interface TermCreate {
  name: string
  definition: string
  category_id?: string
  status?: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
}

export interface TermUpdate {
  name?: string
  definition?: string
  category_id?: string
  status?: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
}

export interface CategoryCreate {
  name: string
  description?: string
  parent_id?: string
}

export interface CategoryUpdate {
  name?: string
  description?: string
  parent_id?: string
}

export interface RelationshipCreate {
  source_term_id: string
  target_term_id: string
  relationship_type: 'synonym' | 'related' | 'parent' | 'child'
}

// ============================================================================
// Terms API
// ============================================================================

export interface TermListResponse {
  data: GlossaryTerm[]
  total: number
  offset: number
  limit: number
}

export async function getTerms(params?: {
  search?: string
  category_id?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<GlossaryTerm[]> {
  const response = await request<TermListResponse>('/glossary/terms', { params })
  return response.data
}

export async function getTerm(id: string): Promise<GlossaryTerm> {
  return request<GlossaryTerm>(`/glossary/terms/${id}`)
}

export async function createTerm(data: TermCreate): Promise<GlossaryTerm> {
  return request<GlossaryTerm>('/glossary/terms', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateTerm(id: string, data: TermUpdate): Promise<GlossaryTerm> {
  return request<GlossaryTerm>(`/glossary/terms/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteTerm(id: string): Promise<OkResponse> {
  return request<OkResponse>(`/glossary/terms/${id}`, { method: 'DELETE' })
}

export interface TermHistoryListResponse {
  data: TermHistory[]
  total: number
}

export async function getTermHistory(id: string): Promise<TermHistory[]> {
  const response = await request<TermHistoryListResponse>(`/glossary/terms/${id}/history`)
  return response.data
}

export interface RelationshipListResponse {
  data: TermRelationship[]
  total: number
}

export async function getTermRelationships(id: string): Promise<TermRelationship[]> {
  const response = await request<RelationshipListResponse>(`/glossary/terms/${id}/relationships`)
  return response.data
}

// ============================================================================
// Categories API
// ============================================================================

export interface CategoryListResponse {
  data: GlossaryCategory[]
  total: number
}

export async function getCategories(): Promise<GlossaryCategory[]> {
  const response = await request<CategoryListResponse>('/glossary/categories')
  return response.data
}

export async function createCategory(data: CategoryCreate): Promise<GlossaryCategory> {
  return request<GlossaryCategory>('/glossary/categories', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCategory(id: string, data: CategoryUpdate): Promise<GlossaryCategory> {
  return request<GlossaryCategory>(`/glossary/categories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteCategory(id: string): Promise<OkResponse> {
  return request<OkResponse>(`/glossary/categories/${id}`, { method: 'DELETE' })
}

// ============================================================================
// Relationships API
// ============================================================================

export async function createRelationship(data: RelationshipCreate): Promise<TermRelationship> {
  return request<TermRelationship>('/glossary/relationships', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteRelationship(id: string): Promise<OkResponse> {
  return request<OkResponse>(`/glossary/relationships/${id}`, { method: 'DELETE' })
}
