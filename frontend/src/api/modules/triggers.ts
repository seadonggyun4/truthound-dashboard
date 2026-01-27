/**
 * Triggers API - Schedule triggers and webhook endpoints.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export interface TriggerEvaluation {
  source_id: string
  triggered: boolean
  reason: string
}

export interface TriggerCheckStatus {
  schedule_id: string
  schedule_name: string
  source_id: string
  trigger_type: string
  is_active: boolean
  last_check_at: string | null
  next_check_at: string | null
  last_trigger_at: string | null
  last_result: TriggerEvaluation | null
  cooldown_remaining_seconds: number | null
  is_due_for_check: boolean
  check_count?: number
  trigger_count?: number
  priority?: number
  last_evaluation?: unknown
}

export interface TriggerMonitoringStats {
  total_schedules: number
  active_triggers: number
  triggers_by_type: Record<string, number>
  triggered_last_24h: number
  last_check_at: string | null
  active_data_change_triggers?: number
  active_webhook_triggers?: number
  active_composite_triggers?: number
  total_checks_last_hour?: number
  total_triggers_last_hour?: number
  next_scheduled_check_at?: string | null
}

export interface ScheduleStatus {
  id: string
  name: string
  source_id: string
  source_name: string
  trigger_type: string
  is_active: boolean
  last_run_at: string | null
  next_run_at: string | null
  cooldown_remaining_seconds: number | null
}

export interface TriggerMonitoringResponse {
  stats: TriggerMonitoringStats
  trigger_statuses: TriggerCheckStatus[]
  schedules?: ScheduleStatus[]
  checker_running?: boolean
  checker_interval_seconds?: number
  last_checker_run_at?: string | null
}

export interface WebhookTriggerRequest {
  source?: string
  event_type?: string
  source_ids?: string[]
  metadata?: Record<string, unknown>
}

export interface WebhookTriggerResponse {
  success: boolean
  message: string
  triggered_schedules: string[]
  validations_started: Array<{
    schedule_id: string
    validation_id: string
  }>
  source: string
  event_type: string
}

// ============================================================================
// API Functions
// ============================================================================

export async function getTriggerMonitoring(): Promise<TriggerMonitoringResponse> {
  return request<TriggerMonitoringResponse>('/triggers/monitoring')
}

export async function getScheduleTriggerStatus(
  scheduleId: string
): Promise<TriggerCheckStatus> {
  return request<TriggerCheckStatus>(`/triggers/schedule/${scheduleId}`)
}

export async function sendWebhookTrigger(
  data: WebhookTriggerRequest
): Promise<WebhookTriggerResponse> {
  return request<WebhookTriggerResponse>('/triggers/webhook', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function testWebhookEndpoint(
  source: string = 'test',
  eventType: string = 'test_event'
): Promise<{ success: boolean; message: string; received: { source: string; event_type: string } }> {
  return request('/triggers/webhook/test', {
    method: 'POST',
    params: { source, event_type: eventType },
  })
}
