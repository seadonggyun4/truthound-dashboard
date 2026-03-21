/**
 * Plugins API - registry, lifecycle, and documentation surface.
 */
import { request } from '../core'
import type { PaginatedResponse } from '../core'

export type PluginType = 'validator' | 'reporter' | 'connector' | 'transformer'
export type PluginStatus = 'available' | 'installed' | 'enabled' | 'disabled' | 'update_available' | 'error'
export type PluginSource = 'official' | 'community' | 'local' | 'private'
export type SecurityLevel = 'trusted' | 'verified' | 'unverified' | 'sandboxed'

export interface PluginAuthor {
  name: string
  email?: string
  url?: string
}

export interface PluginDependency {
  plugin_id: string
  version_constraint: string
  optional?: boolean
}

export interface Plugin {
  id: string
  name: string
  display_name: string
  description: string
  version: string
  latest_version?: string
  type: PluginType
  source: PluginSource
  status: PluginStatus
  security_level: SecurityLevel
  author?: PluginAuthor
  license?: string
  homepage?: string
  repository?: string
  keywords: string[]
  categories: string[]
  dependencies: PluginDependency[]
  permissions: string[]
  python_version?: string
  dashboard_version?: string
  icon_url?: string
  banner_url?: string
  documentation_url?: string
  changelog?: string
  readme?: string
  is_enabled: boolean
  install_count: number
  rating?: number
  rating_count: number
  validators_count: number
  reporters_count: number
  installed_at?: string
  last_updated?: string
  created_at: string
  updated_at: string
}

export type PluginListResponse = PaginatedResponse<Plugin>

export interface MarketplaceStats {
  total_plugins: number
  total_validators: number
  total_reporters: number
  total_installs: number
  categories: Array<{
    name: string
    display_name: string
    description: string
    icon?: string
    plugin_count: number
  }>
  featured_plugins: Plugin[]
  popular_plugins: Plugin[]
  recent_plugins: Plugin[]
}

export interface PluginInstallResponse {
  success: boolean
  plugin_id: string
  installed_version?: string
  message?: string
  warnings: string[]
}

export interface PluginUninstallResponse {
  success: boolean
  plugin_id: string
  message?: string
}

export interface DependencyGraphNode {
  plugin_id: string
  plugin_name: string
  version: string
  installed: boolean
  enabled: boolean
  dependencies: string[]
  dependents: string[]
}

export interface DependencyGraphResponse {
  nodes: DependencyGraphNode[]
  edges: Array<{
    source: string
    target: string
    optional: boolean
    version_constraint: string
  }>
}

export interface PluginDocsResponse {
  plugin_id: string
  content: string
  format: 'markdown' | 'html'
  generated_at: string
}

export interface PluginLifecycleResponse {
  plugin_id: string
  current_state: 'discovered' | 'loaded' | 'active' | 'error'
  available_transitions: Array<'load' | 'activate' | 'deactivate' | 'unload'>
  history: Array<{
    event_type: string
    from_state: string
    to_state: string
    timestamp: string
    success: boolean
    message?: string
  }>
  last_transition_at?: string
}

export interface PluginTransitionResponse {
  success: boolean
  plugin_id: string
  previous_state: string
  current_state: string
  message?: string
}

export async function listPlugins(params?: {
  type?: PluginType
  status?: PluginStatus
  search?: string
  offset?: number
  limit?: number
}): Promise<PluginListResponse> {
  return request<PluginListResponse>('/plugins', {
    params: params as Record<string, string | number | boolean>,
  })
}

export async function getMarketplaceStats(): Promise<MarketplaceStats> {
  return request<MarketplaceStats>('/plugins/stats')
}

export async function searchPlugins(query: {
  query?: string
  types?: PluginType[]
  categories?: string[]
  offset?: number
  limit?: number
}): Promise<PluginListResponse> {
  return request<PluginListResponse>('/plugins/search', {
    method: 'POST',
    body: JSON.stringify(query),
  })
}

export async function getPlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}`)
}

export async function installPlugin(pluginId: string, options?: {
  version?: string
  force?: boolean
  enable_after_install?: boolean
}): Promise<PluginInstallResponse> {
  return request<PluginInstallResponse>(`/plugins/${pluginId}/install`, {
    method: 'POST',
    body: JSON.stringify({ plugin_id: pluginId, ...options }),
  })
}

export async function uninstallPlugin(pluginId: string, removeData?: boolean): Promise<PluginUninstallResponse> {
  return request<PluginUninstallResponse>(`/plugins/${pluginId}/uninstall`, {
    method: 'POST',
    body: JSON.stringify({ plugin_id: pluginId, remove_data: removeData }),
  })
}

export async function enablePlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}/enable`, { method: 'POST' })
}

export async function disablePlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}/disable`, { method: 'POST' })
}

export async function getPluginDependencies(pluginId: string): Promise<DependencyGraphResponse> {
  return request<DependencyGraphResponse>(`/plugins/${pluginId}/dependencies`)
}

export async function getPluginDocumentation(pluginId: string): Promise<PluginDocsResponse> {
  return request<PluginDocsResponse>(`/plugins/${pluginId}/docs`)
}

export async function getPluginLifecycle(pluginId: string): Promise<PluginLifecycleResponse> {
  return request<PluginLifecycleResponse>(`/plugins/${pluginId}/lifecycle`)
}

export async function transitionPluginLifecycle(
  pluginId: string,
  transition: 'load' | 'activate' | 'deactivate' | 'unload'
): Promise<PluginTransitionResponse> {
  return request<PluginTransitionResponse>(`/plugins/${pluginId}/lifecycle`, {
    method: 'POST',
    body: JSON.stringify({ transition }),
  })
}
