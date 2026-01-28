/**
 * Lineage API - Data lineage tracking and OpenLineage export.
 */
import { request } from '../core'
import type { MessageResponse } from '../core'

// ============================================================================
// Basic Lineage Types
// ============================================================================

export type LineageNodeType = 'source' | 'transform' | 'sink'
export type LineageEdgeType = 'derives_from' | 'transforms_to' | 'feeds_into'

export interface LineageNode {
  id: string
  name: string
  node_type: LineageNodeType
  source_id: string | null
  metadata: Record<string, unknown> | null
  position_x: number | null
  position_y: number | null
  created_at: string
  updated_at: string
}

export interface LineageEdge {
  id: string
  source_node_id: string
  target_node_id: string
  edge_type: LineageEdgeType
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface LineageGraph {
  nodes: LineageNode[]
  edges: LineageEdge[]
  total_nodes: number
  total_edges: number
}

export interface ImpactAnalysisResponse {
  node_id: string
  node_name: string
  upstream: LineageNode[]
  downstream: LineageNode[]
  upstream_count: number
  downstream_count: number
  depth: number
}

export interface NodePositionUpdate {
  id: string
  x: number
  y: number
}

export interface LineageNodeCreate {
  name: string
  node_type: LineageNodeType
  source_id?: string
  metadata?: Record<string, unknown>
  position_x?: number
  position_y?: number
}

export interface LineageNodeUpdate {
  name?: string
  node_type?: LineageNodeType
  source_id?: string | null
  metadata?: Record<string, unknown> | null
  position_x?: number | null
  position_y?: number | null
}

export interface LineageEdgeCreate {
  source_node_id: string
  target_node_id: string
  edge_type: LineageEdgeType
  metadata?: Record<string, unknown>
}

// ============================================================================
// OpenLineage Types
// ============================================================================

export type OpenLineageRunState = 'START' | 'RUNNING' | 'COMPLETE' | 'FAIL' | 'ABORT'
export type OpenLineageExportFormat = 'json' | 'ndjson'
export type WebhookEventType = 'job' | 'dataset' | 'all'

export interface OpenLineageDataset {
  namespace: string
  name: string
  facets: Record<string, unknown>
}

export interface OpenLineageJob {
  namespace: string
  name: string
  facets: Record<string, unknown>
}

export interface OpenLineageRun {
  run_id: string
  facets: Record<string, unknown>
}

export interface OpenLineageEvent {
  event_time: string
  eventType: OpenLineageRunState
  producer: string
  schemaURL: string
  run: OpenLineageRun
  job: OpenLineageJob
  inputs: OpenLineageDataset[]
  outputs: OpenLineageDataset[]
}

export interface OpenLineageExportRequest {
  job_namespace?: string
  job_name?: string
  source_id?: string
  include_schema?: boolean
  include_quality_metrics?: boolean
  format?: OpenLineageExportFormat
}

export interface OpenLineageExportResponse {
  events: OpenLineageEvent[]
  total_events: number
  total_datasets: number
  total_jobs: number
  export_time: string
}

export interface OpenLineageWebhookConfig {
  url: string
  api_key?: string
  headers?: Record<string, string>
  batch_size?: number
  timeout_seconds?: number
}

export interface OpenLineageEmitRequest {
  webhook: OpenLineageWebhookConfig
  source_id?: string
  job_namespace?: string
  job_name?: string
}

export interface OpenLineageEmitResponse {
  success: boolean
  events_sent: number
  failed_events: number
  error_message?: string
}

export interface OpenLineageSpec {
  spec_version: string
  producer: string
  supported_facets: {
    dataset: string[]
    job: string[]
    run: string[]
  }
  supported_event_types: string[]
  export_formats: string[]
  documentation_url: string
}

export interface OpenLineageWebhook {
  id: string
  name: string
  url: string
  is_active: boolean
  headers: Record<string, string>
  event_types: WebhookEventType
  batch_size: number
  timeout_seconds: number
  last_sent_at: string | null
  success_count: number
  failure_count: number
  last_error: string | null
  created_at: string
  updated_at: string | null
}

export interface CreateWebhookRequest {
  name: string
  url: string
  is_active?: boolean
  headers?: Record<string, string>
  api_key?: string
  event_types?: WebhookEventType
  batch_size?: number
  timeout_seconds?: number
}

export interface UpdateWebhookRequest {
  name?: string
  url?: string
  is_active?: boolean
  headers?: Record<string, string>
  api_key?: string
  event_types?: WebhookEventType
  batch_size?: number
  timeout_seconds?: number
}

export interface WebhookListResponse {
  data: OpenLineageWebhook[]
  total: number
}

export interface WebhookTestRequest {
  url: string
  headers?: Record<string, string>
  api_key?: string
  timeout_seconds?: number
}

export interface WebhookTestResult {
  success: boolean
  status_code: number | null
  response_time_ms: number | null
  error_message: string | null
  response_body: string | null
}

// ============================================================================
// Basic Lineage API
// ============================================================================

export async function getLineageGraph(): Promise<LineageGraph> {
  return request<LineageGraph>('/lineage', { dedupe: 'lineage-graph' })
}

export async function getSourceLineage(
  sourceId: string,
  params?: { depth?: number }
): Promise<LineageGraph> {
  const dedupeKey = `lineage-source-${sourceId}-${params?.depth ?? 'default'}`
  return request<LineageGraph>(`/lineage/sources/${sourceId}`, { params, dedupe: dedupeKey })
}

export async function createLineageNode(data: LineageNodeCreate): Promise<LineageNode> {
  return request<LineageNode>('/lineage/nodes', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getLineageNode(nodeId: string): Promise<LineageNode> {
  return request<LineageNode>(`/lineage/nodes/${nodeId}`, { dedupe: `lineage-node-${nodeId}` })
}

export async function updateLineageNode(
  nodeId: string,
  data: LineageNodeUpdate
): Promise<LineageNode> {
  return request<LineageNode>(`/lineage/nodes/${nodeId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteLineageNode(nodeId: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/lineage/nodes/${nodeId}`, { method: 'DELETE' })
}

export async function createLineageEdge(data: LineageEdgeCreate): Promise<LineageEdge> {
  return request<LineageEdge>('/lineage/edges', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteLineageEdge(edgeId: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/lineage/edges/${edgeId}`, { method: 'DELETE' })
}

export async function analyzeLineageImpact(
  nodeId: string,
  params?: { depth?: number }
): Promise<ImpactAnalysisResponse> {
  return request<ImpactAnalysisResponse>(`/lineage/nodes/${nodeId}/impact`, { params })
}

export async function updateNodePositions(
  positions: NodePositionUpdate[]
): Promise<{ updated_count: number }> {
  return request<{ updated_count: number }>('/lineage/positions', {
    method: 'POST',
    body: JSON.stringify({ positions }),
  })
}

// ============================================================================
// OpenLineage API
// ============================================================================

export async function exportOpenLineage(
  req?: OpenLineageExportRequest
): Promise<OpenLineageExportResponse> {
  return request<OpenLineageExportResponse>('/lineage/openlineage/export', {
    method: 'POST',
    body: JSON.stringify(req || {}),
  })
}

export async function exportOpenLineageGranular(
  req?: OpenLineageExportRequest
): Promise<OpenLineageExportResponse> {
  return request<OpenLineageExportResponse>('/lineage/openlineage/export/granular', {
    method: 'POST',
    body: JSON.stringify(req || {}),
  })
}

export async function emitOpenLineage(
  req: OpenLineageEmitRequest
): Promise<OpenLineageEmitResponse> {
  return request<OpenLineageEmitResponse>('/lineage/openlineage/emit', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export async function getOpenLineageSpec(): Promise<OpenLineageSpec> {
  return request<OpenLineageSpec>('/lineage/openlineage/spec')
}

export function downloadOpenLineageJson(
  events: OpenLineageEvent[],
  filename = 'openlineage-events.json'
): void {
  const blob = new Blob([JSON.stringify(events, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function downloadOpenLineageNdjson(
  events: OpenLineageEvent[],
  filename = 'openlineage-events.ndjson'
): void {
  const ndjson = events.map((e) => JSON.stringify(e)).join('\n')
  const blob = new Blob([ndjson], { type: 'application/x-ndjson' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ============================================================================
// OpenLineage Webhooks API
// ============================================================================

export async function listWebhooks(activeOnly = false): Promise<WebhookListResponse> {
  return request<WebhookListResponse>('/lineage/openlineage/webhooks', {
    params: activeOnly ? { active_only: true } : undefined,
  })
}

export async function getWebhook(webhookId: string): Promise<OpenLineageWebhook> {
  return request<OpenLineageWebhook>(`/lineage/openlineage/webhooks/${webhookId}`)
}

export async function createWebhook(data: CreateWebhookRequest): Promise<OpenLineageWebhook> {
  return request<OpenLineageWebhook>('/lineage/openlineage/webhooks', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateWebhook(
  webhookId: string,
  data: UpdateWebhookRequest
): Promise<OpenLineageWebhook> {
  return request<OpenLineageWebhook>(`/lineage/openlineage/webhooks/${webhookId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteWebhook(webhookId: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/lineage/openlineage/webhooks/${webhookId}`, {
    method: 'DELETE',
  })
}

export async function testWebhook(data: WebhookTestRequest): Promise<WebhookTestResult> {
  return request<WebhookTestResult>('/lineage/openlineage/webhooks/test', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
