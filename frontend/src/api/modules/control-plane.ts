import { request, setStoredSessionToken } from '../core'

export type SavedViewScope = 'sources' | 'alerts' | 'artifacts' | 'history'

export interface Workspace {
  id: string
  name: string
  slug: string
  description?: string | null
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Role {
  id: string
  name: string
  description?: string | null
  permissions: string[]
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface Permission {
  id: string
  key: string
  category: string
  description?: string | null
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  email: string
  display_name: string
  is_active: boolean
  is_system: boolean
  preferences: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface SessionContext {
  token?: string | null
  expires_at?: string | null
  user: User
  workspace: Workspace
  role: Role
}

export interface SavedView {
  id: string
  scope: SavedViewScope
  name: string
  description?: string | null
  filters: Record<string, unknown>
  is_default: boolean
  owner_id: string
  owner_name?: string | null
  workspace_id: string
  created_at: string
  updated_at: string
}

export interface SavedViewListResponse {
  data: SavedView[]
  total: number
  offset: number
  limit: number
}

export interface OverviewSlice {
  total: number
  active?: number | null
  healthy?: number | null
  unhealthy?: number | null
  failed?: number | null
  fresh_24h?: number | null
  stale?: number | null
  unowned?: number | null
}

export interface OverviewSavedView {
  id: string
  name: string
  scope: SavedViewScope
  description?: string | null
  is_default: boolean
  owner_name?: string | null
}

export interface OverviewQueueBacklog {
  queue_id: string
  queue_name: string
  count: number
}

export interface OverviewAssigneeLoad {
  user_id?: string | null
  user_name: string
  count: number
}

export interface OverviewArtifactTypeCount {
  artifact_type: string
  count: number
}

export interface OverviewNamedCount {
  id?: string | null
  name: string
  count: number
}

export interface OverviewOwnershipFreshness {
  ownership_type: string
  ownership_id?: string | null
  ownership_name: string
  fresh_24h: number
  stale: number
}

export interface OverviewWorkspaceSummary {
  id: string
  name?: string | null
  slug?: string | null
}

export interface OverviewResponse {
  workspace: OverviewWorkspaceSummary
  sources: OverviewSlice
  incidents: OverviewSlice
  artifacts: OverviewSlice
  incident_backlog: OverviewQueueBacklog[]
  assignee_workload: OverviewAssigneeLoad[]
  artifact_types: OverviewArtifactTypeCount[]
  sources_by_owner: OverviewNamedCount[]
  sources_by_team: OverviewNamedCount[]
  sources_by_domain: OverviewNamedCount[]
  artifact_freshness_by_ownership: OverviewOwnershipFreshness[]
  saved_views: OverviewSavedView[]
}

export async function getSession(): Promise<SessionContext> {
  const session = await request<SessionContext>('/auth/session')
  if (session.token) {
    setStoredSessionToken(session.token)
  }
  return session
}

export async function createSession(password?: string, workspace_id?: string): Promise<SessionContext> {
  const session = await request<SessionContext>('/auth/session', {
    method: 'POST',
    body: JSON.stringify({ password, workspace_id }),
  })
  if (session.token) {
    setStoredSessionToken(session.token)
  }
  return session
}

export async function logoutSession(): Promise<void> {
  await request<{ message: string }>('/auth/session', { method: 'DELETE' })
  setStoredSessionToken(null)
}

export async function getCurrentUser(): Promise<SessionContext> {
  return request<SessionContext>('/me')
}

export async function listWorkspaces(): Promise<Workspace[]> {
  return request<Workspace[]>('/workspaces')
}

export async function listUsers(): Promise<User[]> {
  return request<User[]>('/users')
}

export async function listRoles(): Promise<Role[]> {
  return request<Role[]>('/roles')
}

export async function listPermissions(): Promise<Permission[]> {
  return request<Permission[]>('/permissions')
}

export async function listSavedViews(scope?: SavedViewScope): Promise<SavedViewListResponse> {
  return request<SavedViewListResponse>('/views', {
    params: scope ? { scope } : undefined,
  })
}

export async function createSavedView(payload: {
  scope: SavedViewScope
  name: string
  description?: string
  filters: Record<string, unknown>
  is_default?: boolean
}): Promise<SavedView> {
  return request<SavedView>('/views', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateSavedView(
  viewId: string,
  payload: {
    name?: string
    description?: string
    filters?: Record<string, unknown>
    is_default?: boolean
  }
): Promise<SavedView> {
  return request<SavedView>(`/views/${viewId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function deleteSavedView(viewId: string): Promise<void> {
  await request<{ message: string }>(`/views/${viewId}`, { method: 'DELETE' })
}

export async function getOverview(): Promise<OverviewResponse> {
  return request<OverviewResponse>('/overview')
}
