/**
 * Notifications API - Channels, rules, logs, and advanced notifications.
 *
 * This module includes:
 * - Basic notification channels, rules, and logs
 * - Advanced notifications: routing rules, deduplication, throttling, escalation
 * - Config import/export functionality
 */
import { request } from '../core'

// ============================================================================
// Basic Notification Types
// ============================================================================

export interface NotificationChannel {
  id: string
  name: string
  type: 'slack' | 'email' | 'webhook' | 'discord' | 'telegram' | 'pagerduty' | 'opsgenie' | 'teams' | 'github'
  is_active: boolean
  config_summary: string
  config?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface NotificationRule {
  id: string
  name: string
  condition: string
  condition_config?: Record<string, unknown>
  channel_ids: string[]
  source_ids?: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface NotificationLog {
  id: string
  channel_id: string
  rule_id?: string
  event_type: string
  status: 'pending' | 'sent' | 'failed'
  message_preview: string
  error_message?: string
  created_at: string
  sent_at?: string
}

export interface NotificationStats {
  period_hours: number
  total: number
  by_status: Record<string, number>
  by_channel: Record<string, number>
  success_rate: number
}

export interface NotificationLogDetail extends NotificationLog {
  message: string
  event_data?: unknown
}

// List response types for basic notifications
export interface NotificationChannelListResponse {
  data: NotificationChannel[]
  count: number
}

export interface NotificationRuleListResponse {
  data: NotificationRule[]
  count: number
}

export interface NotificationLogListResponse {
  data: NotificationLog[]
  count: number
}

export interface NotificationChannelTypeInfo {
  type: string
  name: string
  description: string
  config_schema: Record<string, unknown>
}

export interface NotificationRuleConditionInfo {
  type: string
  name: string
  description: string
  config_schema?: Record<string, unknown>
}

export interface TestChannelResponse {
  success: boolean
  message: string
  error?: string
}

export interface MessageResponse {
  message: string
}

// ============================================================================
// Routing Rules Types
// ============================================================================

export interface RoutingRule {
  id: string
  name: string
  rule_config: Record<string, unknown>
  actions: string[]
  priority: number
  is_active: boolean
  stop_on_match: boolean
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface RuleTypeInfo {
  type: string
  name: string
  description: string
  param_schema: Record<string, unknown>
}

export interface RoutingRuleListResponse {
  items: RoutingRule[]
  total: number
  offset: number
  limit: number
}

// ============================================================================
// Deduplication Types
// ============================================================================

export type DeduplicationStrategy = 'sliding' | 'tumbling' | 'session' | 'adaptive'
export type DeduplicationPolicy = 'none' | 'basic' | 'severity' | 'issue_based' | 'strict' | 'custom'

export interface DeduplicationConfig {
  id: string
  name: string
  strategy: DeduplicationStrategy
  policy: DeduplicationPolicy
  window_seconds: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DeduplicationStats {
  total_received: number
  total_deduplicated: number
  total_passed: number
  dedup_rate: number
  active_fingerprints: number
}

export interface DeduplicationConfigListResponse {
  items: DeduplicationConfig[]
  total: number
  offset: number
  limit: number
}

// ============================================================================
// Throttling Types
// ============================================================================

export interface ThrottlingConfig {
  id: string
  name: string
  per_minute: number | null
  per_hour: number | null
  per_day: number | null
  burst_allowance: number
  channel_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ThrottlingStats {
  total_received: number
  total_throttled: number
  total_passed: number
  throttle_rate: number
  current_window_count: number
}

export interface ThrottlingConfigListResponse {
  items: ThrottlingConfig[]
  total: number
  offset: number
  limit: number
}

// ============================================================================
// Escalation Types
// ============================================================================

export type EscalationState = 'pending' | 'triggered' | 'acknowledged' | 'escalated' | 'resolved'
export type EscalationTargetType = 'user' | 'group' | 'oncall' | 'channel'

export interface EscalationTarget {
  type: EscalationTargetType
  identifier: string
  channel: string
}

export interface EscalationLevel {
  level: number
  delay_minutes: number
  targets: EscalationTarget[]
}

export interface EscalationPolicy {
  id: string
  name: string
  description: string
  levels: EscalationLevel[]
  auto_resolve_on_success: boolean
  max_escalations: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EscalationEvent {
  from_state: string | null
  to_state: string
  actor: string | null
  message: string
  timestamp: string
}

export interface EscalationIncident {
  id: string
  policy_id: string
  incident_ref: string
  state: EscalationState
  current_level: number
  escalation_count: number
  context: Record<string, unknown>
  acknowledged_by: string | null
  acknowledged_at: string | null
  resolved_by: string | null
  resolved_at: string | null
  next_escalation_at: string | null
  events: EscalationEvent[]
  created_at: string
  updated_at: string
}

export interface EscalationStats {
  total_incidents: number
  by_state: Record<string, number>
  active_count: number
  total_policies: number
  avg_resolution_time_minutes: number | null
}

export interface EscalationPolicyListResponse {
  items: EscalationPolicy[]
  total: number
  offset: number
  limit: number
}

export interface EscalationIncidentListResponse {
  items: EscalationIncident[]
  total: number
  offset: number
  limit: number
}

export interface EscalationSchedulerStatus {
  is_running: boolean
  check_interval_seconds: number
  last_check_at: string | null
  next_check_at: string | null
  total_checks: number
  total_escalations_triggered: number
  errors_count: number
}

export interface EscalationSchedulerConfig {
  check_interval_seconds: number
}

// ============================================================================
// Rule Testing Types
// ============================================================================

export interface RuleTestContext {
  checkpoint_name?: string
  status?: 'success' | 'failure' | 'error'
  severity?: 'critical' | 'high' | 'medium' | 'low' | 'info'
  issue_count?: number
  pass_rate?: number
  tags?: string[]
  data_asset?: string
  metadata?: Record<string, unknown>
  timestamp?: string
}

export interface RuleTestResult {
  matched: boolean
  rule_type: string
  evaluation_time_ms: number
  match_details: Record<string, unknown>
  error?: string
}

// ============================================================================
// Expression Validation Types
// ============================================================================

export interface ExpressionValidateRequest {
  expression: string
  timeout_seconds?: number
}

export interface ExpressionValidateResponse {
  valid: boolean
  error: string | null
  error_line: number | null
  preview_result: boolean | null
  preview_error: string | null
  warnings: string[]
}

export interface Jinja2ValidateRequest {
  template: string
  sample_data?: Record<string, unknown>
  expected_result?: string
}

export interface Jinja2ValidateResponse {
  valid: boolean
  error: string | null
  error_line: number | null
  rendered_output: string | null
  matches_expected?: boolean
  render_error?: string
}

// ============================================================================
// Config Import/Export Types
// ============================================================================

export type ConfigType = 'routing_rule' | 'deduplication' | 'throttling' | 'escalation'
export type ConflictResolution = 'skip' | 'overwrite' | 'rename'

export interface NotificationConfigBundle {
  version: string
  exported_at: string
  routing_rules: RoutingRule[]
  deduplication_configs: DeduplicationConfig[]
  throttling_configs: ThrottlingConfig[]
  escalation_policies: EscalationPolicy[]
}

export interface ConfigImportItem {
  config_type: ConfigType
  config_id: string
  action: 'create' | 'skip' | 'overwrite'
}

export interface ConfigImportRequest {
  bundle: NotificationConfigBundle
  conflict_resolution: ConflictResolution
  selected_items?: ConfigImportItem[] | null
}

export interface ConfigImportConflict {
  config_type: ConfigType
  config_id: string
  config_name: string
  existing_name: string
  suggested_action: ConflictResolution
}

export interface ConfigImportPreview {
  total_configs: number
  new_configs: number
  conflicts: ConfigImportConflict[]
  routing_rules_count: number
  deduplication_configs_count: number
  throttling_configs_count: number
  escalation_policies_count: number
}

export interface ConfigImportResult {
  success: boolean
  message: string
  created_count: number
  skipped_count: number
  overwritten_count: number
  errors: string[]
  created_ids: Record<string, string[]>
}

export interface ConfigExportOptions {
  include_routing_rules?: boolean
  include_deduplication?: boolean
  include_throttling?: boolean
  include_escalation?: boolean
}

// ============================================================================
// Advanced Stats Types
// ============================================================================

export interface AdvancedNotificationStats {
  routing: Record<string, number>
  deduplication: DeduplicationStats
  throttling: ThrottlingStats
  escalation: EscalationStats
}

// ============================================================================
// Notification Channels API
// ============================================================================

export async function listNotificationChannels(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  channel_type?: string
}): Promise<NotificationChannelListResponse> {
  return request<NotificationChannelListResponse>('/notifications/channels', { params })
}

export async function getNotificationChannel(
  id: string
): Promise<NotificationChannel> {
  return request<NotificationChannel>(`/notifications/channels/${id}`)
}

export async function createNotificationChannel(data: {
  name: string
  type: string
  config: Record<string, unknown>
  is_active?: boolean
}): Promise<NotificationChannel> {
  return request<NotificationChannel>('/notifications/channels', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateNotificationChannel(
  id: string,
  data: {
    name?: string
    config?: Record<string, unknown>
    is_active?: boolean
  }
): Promise<NotificationChannel> {
  return request<NotificationChannel>(`/notifications/channels/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteNotificationChannel(
  id: string
): Promise<MessageResponse> {
  return request<MessageResponse>(`/notifications/channels/${id}`, { method: 'DELETE' })
}

export async function testNotificationChannel(
  id: string
): Promise<TestChannelResponse> {
  return request<TestChannelResponse>(`/notifications/channels/${id}/test`, { method: 'POST' })
}

export async function getNotificationChannelTypes(): Promise<NotificationChannelTypeInfo[]> {
  return request<NotificationChannelTypeInfo[]>('/notifications/channels/types')
}

// ============================================================================
// Notification Rules API
// ============================================================================

export async function listNotificationRules(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  condition?: string
}): Promise<NotificationRuleListResponse> {
  return request<NotificationRuleListResponse>('/notifications/rules', { params })
}

export async function getNotificationRule(
  id: string
): Promise<NotificationRule> {
  return request<NotificationRule>(`/notifications/rules/${id}`)
}

export async function createNotificationRule(data: {
  name: string
  condition: string
  channel_ids: string[]
  condition_config?: Record<string, unknown>
  source_ids?: string[]
  is_active?: boolean
}): Promise<NotificationRule> {
  return request<NotificationRule>('/notifications/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateNotificationRule(
  id: string,
  data: {
    name?: string
    condition?: string
    channel_ids?: string[]
    condition_config?: Record<string, unknown>
    source_ids?: string[]
    is_active?: boolean
  }
): Promise<NotificationRule> {
  return request<NotificationRule>(`/notifications/rules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteNotificationRule(
  id: string
): Promise<MessageResponse> {
  return request<MessageResponse>(`/notifications/rules/${id}`, { method: 'DELETE' })
}

export async function getNotificationRuleConditions(): Promise<NotificationRuleConditionInfo[]> {
  return request<NotificationRuleConditionInfo[]>('/notifications/rules/conditions')
}

// ============================================================================
// Notification Logs API
// ============================================================================

export async function listNotificationLogs(params?: {
  offset?: number
  limit?: number
  channel_id?: string
  status?: string
  hours?: number
}): Promise<NotificationLogListResponse> {
  return request<NotificationLogListResponse>('/notifications/logs', { params })
}

export async function getNotificationLog(
  id: string
): Promise<NotificationLogDetail> {
  return request<NotificationLogDetail>(`/notifications/logs/${id}`)
}

export async function getNotificationStats(params?: {
  hours?: number
}): Promise<NotificationStats> {
  return request<NotificationStats>('/notifications/logs/stats', { params })
}

// ============================================================================
// Routing Rules API
// ============================================================================

export async function listRoutingRules(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<RoutingRuleListResponse> {
  return request('/notifications/routing/rules', { params })
}

export async function getRoutingRule(id: string): Promise<RoutingRule> {
  return request(`/notifications/routing/rules/${id}`)
}

export async function createRoutingRule(data: {
  name: string
  rule_config: Record<string, unknown>
  actions: string[]
  priority?: number
  is_active?: boolean
  stop_on_match?: boolean
  metadata?: Record<string, unknown>
}): Promise<RoutingRule> {
  return request('/notifications/routing/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateRoutingRule(
  id: string,
  data: {
    name?: string
    rule_config?: Record<string, unknown>
    actions?: string[]
    priority?: number
    is_active?: boolean
    stop_on_match?: boolean
    metadata?: Record<string, unknown>
  }
): Promise<RoutingRule> {
  return request(`/notifications/routing/rules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteRoutingRule(id: string): Promise<void> {
  return request(`/notifications/routing/rules/${id}`, { method: 'DELETE' })
}

export async function getRuleTypes(): Promise<{ rule_types: RuleTypeInfo[] }> {
  return request('/notifications/routing/rules/types')
}

export async function testRoutingRule(
  ruleConfig: Record<string, unknown>,
  context: RuleTestContext
): Promise<RuleTestResult> {
  return request('/notifications/routing/rules/test', {
    method: 'POST',
    body: JSON.stringify({ rule_config: ruleConfig, context }),
  })
}

export async function validateExpression(
  data: ExpressionValidateRequest
): Promise<ExpressionValidateResponse> {
  return request('/notifications/routing/rules/validate-expression', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function validateJinja2Template(
  data: Jinja2ValidateRequest
): Promise<Jinja2ValidateResponse> {
  return request('/notifications/routing/rules/validate-jinja2', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ============================================================================
// Deduplication API
// ============================================================================

export async function listDeduplicationConfigs(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<DeduplicationConfigListResponse> {
  return request('/notifications/deduplication/configs', { params })
}

export async function getDeduplicationConfig(id: string): Promise<DeduplicationConfig> {
  return request(`/notifications/deduplication/configs/${id}`)
}

export async function createDeduplicationConfig(data: {
  name: string
  strategy?: DeduplicationStrategy
  policy?: DeduplicationPolicy
  window_seconds?: number
  is_active?: boolean
}): Promise<DeduplicationConfig> {
  return request('/notifications/deduplication/configs', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateDeduplicationConfig(
  id: string,
  data: {
    name?: string
    strategy?: DeduplicationStrategy
    policy?: DeduplicationPolicy
    window_seconds?: number
    is_active?: boolean
  }
): Promise<DeduplicationConfig> {
  return request(`/notifications/deduplication/configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteDeduplicationConfig(id: string): Promise<void> {
  return request(`/notifications/deduplication/configs/${id}`, { method: 'DELETE' })
}

export async function getDeduplicationStats(): Promise<DeduplicationStats> {
  return request('/notifications/deduplication/stats')
}

// ============================================================================
// Throttling API
// ============================================================================

export async function listThrottlingConfigs(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  channel_id?: string
}): Promise<ThrottlingConfigListResponse> {
  return request('/notifications/throttling/configs', { params })
}

export async function getThrottlingConfig(id: string): Promise<ThrottlingConfig> {
  return request(`/notifications/throttling/configs/${id}`)
}

export async function createThrottlingConfig(data: {
  name: string
  per_minute?: number | null
  per_hour?: number | null
  per_day?: number | null
  burst_allowance?: number
  channel_id?: string | null
  is_active?: boolean
}): Promise<ThrottlingConfig> {
  return request('/notifications/throttling/configs', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateThrottlingConfig(
  id: string,
  data: {
    name?: string
    per_minute?: number | null
    per_hour?: number | null
    per_day?: number | null
    burst_allowance?: number
    channel_id?: string | null
    is_active?: boolean
  }
): Promise<ThrottlingConfig> {
  return request(`/notifications/throttling/configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteThrottlingConfig(id: string): Promise<void> {
  return request(`/notifications/throttling/configs/${id}`, { method: 'DELETE' })
}

export async function getThrottlingStats(): Promise<ThrottlingStats> {
  return request('/notifications/throttling/stats')
}

// ============================================================================
// Escalation Policies API
// ============================================================================

export async function listEscalationPolicies(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<EscalationPolicyListResponse> {
  return request('/notifications/escalation/policies', { params })
}

export async function getEscalationPolicy(id: string): Promise<EscalationPolicy> {
  return request(`/notifications/escalation/policies/${id}`)
}

export async function createEscalationPolicy(data: {
  name: string
  description?: string
  levels: EscalationLevel[]
  auto_resolve_on_success?: boolean
  max_escalations?: number
  is_active?: boolean
}): Promise<EscalationPolicy> {
  return request('/notifications/escalation/policies', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateEscalationPolicy(
  id: string,
  data: {
    name?: string
    description?: string
    levels?: EscalationLevel[]
    auto_resolve_on_success?: boolean
    max_escalations?: number
    is_active?: boolean
  }
): Promise<EscalationPolicy> {
  return request(`/notifications/escalation/policies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteEscalationPolicy(id: string): Promise<void> {
  return request(`/notifications/escalation/policies/${id}`, { method: 'DELETE' })
}

// ============================================================================
// Escalation Incidents API
// ============================================================================

export async function listEscalationIncidents(params?: {
  offset?: number
  limit?: number
  state?: EscalationState
  policy_id?: string
}): Promise<EscalationIncidentListResponse> {
  return request('/notifications/escalation/incidents', { params })
}

export async function getEscalationIncident(id: string): Promise<EscalationIncident> {
  return request(`/notifications/escalation/incidents/${id}`)
}

export async function listActiveEscalationIncidents(): Promise<EscalationIncidentListResponse> {
  return request('/notifications/escalation/incidents/active')
}

export async function acknowledgeEscalationIncident(
  id: string,
  data: { actor: string; message?: string }
): Promise<EscalationIncident> {
  return request(`/notifications/escalation/incidents/${id}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function resolveEscalationIncident(
  id: string,
  data: { actor?: string; message?: string }
): Promise<EscalationIncident> {
  return request(`/notifications/escalation/incidents/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getEscalationStats(): Promise<EscalationStats> {
  return request('/notifications/escalation/stats')
}

// ============================================================================
// Escalation Scheduler API
// ============================================================================

export async function getEscalationSchedulerStatus(): Promise<EscalationSchedulerStatus> {
  return request('/notifications/escalation/scheduler/status')
}

export async function startEscalationScheduler(): Promise<{ message: string; status: EscalationSchedulerStatus }> {
  return request('/notifications/escalation/scheduler/start', { method: 'POST' })
}

export async function stopEscalationScheduler(): Promise<{ message: string; status: EscalationSchedulerStatus }> {
  return request('/notifications/escalation/scheduler/stop', { method: 'POST' })
}

export async function triggerEscalationCheck(): Promise<{
  message: string
  incidents_checked: number
  escalations_triggered: number
}> {
  return request('/notifications/escalation/scheduler/trigger', { method: 'POST' })
}

export async function updateEscalationSchedulerConfig(
  config: EscalationSchedulerConfig
): Promise<{ message: string; status: EscalationSchedulerStatus }> {
  return request('/notifications/escalation/scheduler/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  })
}

// ============================================================================
// Advanced Stats API
// ============================================================================

export async function getAdvancedNotificationStats(): Promise<AdvancedNotificationStats> {
  return request('/notifications/advanced/stats')
}

// ============================================================================
// Config Import/Export API
// ============================================================================

export async function exportNotificationConfig(
  options?: ConfigExportOptions
): Promise<NotificationConfigBundle> {
  const params: Record<string, string> = {}
  if (options?.include_routing_rules !== undefined) {
    params.include_routing_rules = String(options.include_routing_rules)
  }
  if (options?.include_deduplication !== undefined) {
    params.include_deduplication = String(options.include_deduplication)
  }
  if (options?.include_throttling !== undefined) {
    params.include_throttling = String(options.include_throttling)
  }
  if (options?.include_escalation !== undefined) {
    params.include_escalation = String(options.include_escalation)
  }
  return request('/notifications/config/export', { params })
}

export async function downloadNotificationConfigAsFile(
  options?: ConfigExportOptions
): Promise<Blob> {
  const bundle = await exportNotificationConfig(options)
  const json = JSON.stringify(bundle, null, 2)
  return new Blob([json], { type: 'application/json' })
}

export async function previewNotificationConfigImport(
  bundle: NotificationConfigBundle
): Promise<ConfigImportPreview> {
  return request('/notifications/config/import/preview', {
    method: 'POST',
    body: JSON.stringify(bundle),
  })
}

export async function importNotificationConfig(
  request_data: ConfigImportRequest
): Promise<ConfigImportResult> {
  return request('/notifications/config/import', {
    method: 'POST',
    body: JSON.stringify(request_data),
  })
}

export async function parseNotificationConfigFile(file: File): Promise<NotificationConfigBundle> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const bundle = JSON.parse(content) as NotificationConfigBundle

        // Basic validation
        if (!bundle.version || !bundle.exported_at) {
          reject(new Error('Invalid config file: missing version or exported_at'))
          return
        }

        // Ensure arrays exist
        bundle.routing_rules = bundle.routing_rules || []
        bundle.deduplication_configs = bundle.deduplication_configs || []
        bundle.throttling_configs = bundle.throttling_configs || []
        bundle.escalation_policies = bundle.escalation_policies || []

        resolve(bundle)
      } catch (err) {
        reject(new Error(`Failed to parse config file: ${err instanceof Error ? err.message : 'Unknown error'}`))
      }
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsText(file)
  })
}
