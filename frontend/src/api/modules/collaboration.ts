/**
 * Collaboration API - Comments and activities.
 */
import { request } from '../core'
import type { OkResponse } from '../core'

// ============================================================================
// Types
// ============================================================================

export type ResourceType = 'term' | 'asset' | 'column'
export type ActivityAction = 'created' | 'updated' | 'deleted' | 'commented'

export interface Comment {
  id: string
  resource_type: ResourceType
  resource_id: string
  content: string
  author_id?: string
  parent_id?: string
  created_at: string
  updated_at: string
  replies: Comment[]
}

export interface Activity {
  id: string
  resource_type: string
  resource_id: string
  action: ActivityAction
  actor_id?: string
  description?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface CommentCreate {
  resource_type: ResourceType
  resource_id: string
  content: string
  author_id?: string
  parent_id?: string
}

export interface CommentUpdate {
  content: string
}

// ============================================================================
// Comments API
// ============================================================================

export async function getComments(
  resourceType: ResourceType,
  resourceId: string
): Promise<Comment[]> {
  return request<Comment[]>('/comments', {
    params: { resource_type: resourceType, resource_id: resourceId },
  })
}

export async function createComment(data: CommentCreate): Promise<Comment> {
  return request<Comment>('/comments', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateComment(id: string, data: CommentUpdate): Promise<Comment> {
  return request<Comment>(`/comments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteComment(id: string): Promise<OkResponse> {
  return request<OkResponse>(`/comments/${id}`, { method: 'DELETE' })
}

// ============================================================================
// Activities API
// ============================================================================

export async function getActivities(params?: {
  resource_type?: string
  resource_id?: string
  skip?: number
  limit?: number
}): Promise<Activity[]> {
  return request<Activity[]>('/activities', { params })
}
