/**
 * Schedules API - Validation scheduling.
 */
import { request } from '../core'
import type { PaginatedResponse, MessageResponse } from '../core'

// ============================================================================
// Types
// ============================================================================

export type TriggerType =
  | 'cron'
  | 'interval'
  | 'data_change'
  | 'composite'
  | 'event'
  | 'manual'

export interface Schedule {
  id: string
  name: string
  source_id: string
  cron_expression: string
  trigger_type?: TriggerType
  trigger_config?: Record<string, unknown>
  trigger_count?: number
  last_trigger_result?: Record<string, unknown>
  is_active: boolean
  notify_on_failure: boolean
  last_run_at?: string
  next_run_at?: string
  config?: Record<string, unknown>
  created_at: string
  updated_at?: string
  source_name?: string
}

export interface ScheduleCreateRequest {
  source_id: string
  name: string
  cron_expression?: string
  trigger_type?: TriggerType
  trigger_config?: Record<string, unknown>
  notify_on_failure?: boolean
  config?: Record<string, unknown>
}

export interface ScheduleUpdateRequest {
  name?: string
  cron_expression?: string
  trigger_type?: TriggerType
  trigger_config?: Record<string, unknown>
  notify_on_failure?: boolean
  config?: Record<string, unknown>
}

export type ScheduleListResponse = PaginatedResponse<Schedule>

export interface ScheduleActionResponse {
  message: string
  schedule: Schedule
}

export interface ScheduleRunResponse {
  message: string
  validation_id: string
  passed: boolean
}

// ============================================================================
// API Functions
// ============================================================================

export async function listSchedules(params?: {
  source_id?: string
  active_only?: boolean
  offset?: number
  limit?: number
}): Promise<ScheduleListResponse> {
  return request<ScheduleListResponse>('/schedules', { params })
}

export async function createSchedule(
  data: ScheduleCreateRequest
): Promise<Schedule> {
  return request<Schedule>('/schedules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getSchedule(id: string): Promise<Schedule> {
  return request<Schedule>(`/schedules/${id}`)
}

export async function updateSchedule(
  id: string,
  data: ScheduleUpdateRequest
): Promise<Schedule> {
  return request<Schedule>(`/schedules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteSchedule(id: string): Promise<MessageResponse> {
  return request<MessageResponse>(`/schedules/${id}`, { method: 'DELETE' })
}

export async function pauseSchedule(id: string): Promise<ScheduleActionResponse> {
  return request<ScheduleActionResponse>(`/schedules/${id}/pause`, { method: 'POST' })
}

export async function resumeSchedule(id: string): Promise<ScheduleActionResponse> {
  return request<ScheduleActionResponse>(`/schedules/${id}/resume`, { method: 'POST' })
}

export async function runScheduleNow(id: string): Promise<ScheduleRunResponse> {
  return request<ScheduleRunResponse>(`/schedules/${id}/run`, { method: 'POST' })
}
