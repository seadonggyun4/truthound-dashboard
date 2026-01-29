/**
 * Observability API client
 *
 * Provides functions for audit logging, metrics, and tracing
 * using truthound's observability module.
 */

import { request } from '../core'

// =============================================================================
// Types
// =============================================================================

export type AuditEventType =
  | 'create'
  | 'read'
  | 'update'
  | 'delete'
  | 'query'
  | 'list'
  | 'count'
  | 'initialize'
  | 'close'
  | 'flush'
  | 'batch_create'
  | 'batch_delete'
  | 'replicate'
  | 'sync'
  | 'migrate'
  | 'rollback'
  | 'access_denied'
  | 'access_granted'
  | 'error'
  | 'validation_error'

export type AuditStatus = 'success' | 'failure' | 'partial' | 'denied'

export type MetricType = 'counter' | 'gauge' | 'histogram' | 'summary'

export type SpanKind = 'internal' | 'server' | 'client' | 'producer' | 'consumer'

export type SpanStatus = 'unset' | 'ok' | 'error'

export interface ObservabilityConfig {
  enable_audit: boolean
  enable_metrics: boolean
  enable_tracing: boolean
  audit_log_path: string | null
  audit_rotate_daily: boolean
  audit_max_events: number
  redact_fields: string[]
  metrics_prefix: string
  tracing_service_name: string
  tracing_endpoint: string | null
}

export interface AuditEvent {
  event_id: string
  event_type: AuditEventType
  timestamp: string
  status: AuditStatus
  store_type: string
  store_id: string
  item_id: string | null
  user_id: string | null
  session_id: string | null
  duration_ms: number | null
  metadata: Record<string, unknown> | null
  error_message: string | null
  ip_address: string | null
  user_agent: string | null
}

export interface AuditEventListResponse {
  items: AuditEvent[]
  total: number
  page: number
  page_size: number
}

export interface AuditStats {
  total_events: number
  events_today: number
  events_this_week: number
  by_event_type: Record<string, number>
  by_status: Record<string, number>
  error_rate: number
  avg_duration_ms: number | null
}

export interface MetricValue {
  name: string
  value: number
  labels: Record<string, string>
  timestamp: string | null
  metric_type?: MetricType
}

export interface HistogramBucket {
  le: number
  count: number
}

export interface HistogramValue {
  name: string
  count: number
  sum: number
  buckets: HistogramBucket[]
  labels: Record<string, string>
}

export interface SummaryQuantile {
  quantile: number
  value: number
}

export interface SummaryValue {
  name: string
  count: number
  sum: number
  quantiles: SummaryQuantile[]
  labels: Record<string, string>
}

export interface MetricsResponse {
  counters: MetricValue[]
  gauges: MetricValue[]
  histograms: HistogramValue[]
  summaries: SummaryValue[]
  timestamp: string
}

export interface StoreMetrics {
  operations_total: number
  operations_by_type: Record<string, number>
  bytes_read_total: number
  bytes_written_total: number
  active_connections: number
  cache_hits: number
  cache_misses: number
  cache_hit_rate: number
  errors_total: number
  errors_by_type: Record<string, number>
  avg_operation_duration_ms: number | null
}

export interface SpanContext {
  trace_id: string
  span_id: string
  parent_span_id: string | null
  trace_flags: number
  trace_state: Record<string, string>
}

export interface SpanEvent {
  name: string
  timestamp: string
  attributes: Record<string, unknown>
}

export interface Span {
  name: string
  kind: SpanKind
  context: SpanContext
  start_time: string
  end_time: string | null
  duration_ms: number | null
  status: SpanStatus
  status_message: string | null
  attributes: Record<string, unknown>
  events: SpanEvent[]
}

export interface SpanListResponse {
  items: Span[]
  total: number
  page: number
  page_size: number
}

export interface TracingStats {
  enabled: boolean
  total_traces: number
  total_spans: number
  avg_trace_duration_ms: number | null
  traces_today: number
  error_rate: number
  by_service: Record<string, number>
}

export interface ObservabilityStats {
  audit: AuditStats
  store_metrics: StoreMetrics
  tracing: TracingStats | null
  last_updated: string
}

export interface AuditQueryParams {
  event_type?: AuditEventType
  status?: AuditStatus
  start_time?: string
  end_time?: string
  item_id?: string
  limit?: number
  offset?: number
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get observability configuration
 */
export async function getObservabilityConfig(): Promise<ObservabilityConfig> {
  return request<ObservabilityConfig>('/observability/config')
}

/**
 * Update observability configuration
 */
export async function updateObservabilityConfig(
  config: Partial<ObservabilityConfig>
): Promise<ObservabilityConfig> {
  return request<ObservabilityConfig>('/observability/config', {
    method: 'PUT',
    body: JSON.stringify(config),
    headers: { 'Content-Type': 'application/json' },
  })
}

/**
 * Get combined observability statistics
 */
export async function getObservabilityStats(): Promise<ObservabilityStats> {
  return request<ObservabilityStats>('/observability/stats')
}

// =============================================================================
// Audit API
// =============================================================================

/**
 * List audit events with optional filters
 */
export async function listAuditEvents(
  params?: AuditQueryParams
): Promise<AuditEventListResponse> {
  const queryParams: Record<string, string | number | boolean | undefined | null> = {}
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams[key] = value
      }
    })
  }
  return request<AuditEventListResponse>('/observability/audit/events', { params: queryParams })
}

/**
 * Get audit statistics
 */
export async function getAuditStats(): Promise<AuditStats> {
  return request<AuditStats>('/observability/audit/stats')
}

// =============================================================================
// Metrics API
// =============================================================================

/**
 * Get all metrics
 */
export async function getMetrics(): Promise<MetricsResponse> {
  return request<MetricsResponse>('/observability/metrics')
}

/**
 * Get store-specific metrics
 */
export async function getStoreMetrics(): Promise<StoreMetrics> {
  return request<StoreMetrics>('/observability/metrics/store')
}

// =============================================================================
// Tracing API
// =============================================================================

/**
 * Get tracing statistics
 */
export async function getTracingStats(): Promise<TracingStats> {
  return request<TracingStats>('/observability/tracing/stats')
}

/**
 * List spans
 */
export async function listSpans(params?: {
  limit?: number
  offset?: number
}): Promise<SpanListResponse> {
  return request<SpanListResponse>('/observability/tracing/spans', { params })
}
