/**
 * Checkpoint API client
 *
 * Provides typed API methods for checkpoint operations:
 * - CRUD operations for checkpoints
 * - Run management and history
 * - Action, trigger, and routing configuration
 * - Throttling, deduplication, and escalation management
 */

import { apiClient, type RequestOptions } from './base'

import type {
  Checkpoint,
  CheckpointConfig,
  CheckpointResult,
  CheckpointRunSummary,
  CheckpointStatistics,
  CreateCheckpointRequest,
  UpdateCheckpointRequest,
  RunCheckpointRequest,
  RunCheckpointResponse,
  ListCheckpointsResponse,
  ListCheckpointRunsResponse,
  ListCheckpointsParams,
  ListCheckpointRunsParams,
} from '../types/checkpoint'

import type {
  ActionConfig,
  ActionResult,
  ActionType,
  ActionTypeInfo,
} from '../types/actions'

import type {
  TriggerConfig,
  Trigger,
  TriggerType,
  TriggerResult,
} from '../types/triggers'

import type {
  Route,
  Router,
  RoutingRule,
} from '../types/routing'

import type {
  ThrottlingConfig,
  ThrottlingStats,
} from '../types/throttling'

import type {
  DeduplicationConfig,
  DeduplicationStats,
} from '../types/deduplication'

import type {
  EscalationPolicy,
  EscalationRecord,
  EscalationStats,
  CreateEscalationPolicyRequest,
  TriggerEscalationRequest,
  AcknowledgeEscalationRequest,
  ResolveEscalationRequest,
} from '../types/escalation'

// ============================================================================
// Checkpoint CRUD
// ============================================================================

/**
 * List all checkpoints.
 */
export async function listCheckpoints(
  params?: ListCheckpointsParams,
  options?: RequestOptions
): Promise<ListCheckpointsResponse> {
  return apiClient.get<ListCheckpointsResponse>('/checkpoints', {
    ...options,
    params: params as Record<string, string | number | boolean | undefined>,
  })
}

/**
 * Get a checkpoint by ID.
 */
export async function getCheckpoint(
  id: string,
  options?: RequestOptions
): Promise<Checkpoint> {
  return apiClient.get<Checkpoint>(`/checkpoints/${id}`, options)
}

/**
 * Get a checkpoint by name.
 */
export async function getCheckpointByName(
  name: string,
  options?: RequestOptions
): Promise<Checkpoint> {
  return apiClient.get<Checkpoint>(`/checkpoints/by-name/${encodeURIComponent(name)}`, options)
}

/**
 * Create a new checkpoint.
 */
export async function createCheckpoint(
  data: CreateCheckpointRequest,
  options?: RequestOptions
): Promise<Checkpoint> {
  return apiClient.post<Checkpoint>('/checkpoints', data, options)
}

/**
 * Update a checkpoint.
 */
export async function updateCheckpoint(
  id: string,
  data: UpdateCheckpointRequest,
  options?: RequestOptions
): Promise<Checkpoint> {
  return apiClient.put<Checkpoint>(`/checkpoints/${id}`, data, options)
}

/**
 * Delete a checkpoint.
 */
export async function deleteCheckpoint(
  id: string,
  options?: RequestOptions
): Promise<void> {
  return apiClient.delete(`/checkpoints/${id}`, options)
}

/**
 * Enable a checkpoint.
 */
export async function enableCheckpoint(
  id: string,
  options?: RequestOptions
): Promise<Checkpoint> {
  return apiClient.post<Checkpoint>(`/checkpoints/${id}/enable`, undefined, options)
}

/**
 * Disable a checkpoint.
 */
export async function disableCheckpoint(
  id: string,
  options?: RequestOptions
): Promise<Checkpoint> {
  return apiClient.post<Checkpoint>(`/checkpoints/${id}/disable`, undefined, options)
}

// ============================================================================
// Checkpoint Execution
// ============================================================================

/**
 * Run a checkpoint.
 */
export async function runCheckpoint(
  id: string,
  data?: RunCheckpointRequest,
  options?: RequestOptions
): Promise<RunCheckpointResponse> {
  return apiClient.post<RunCheckpointResponse>(
    `/checkpoints/${id}/run`,
    data,
    { ...options, timeout: (data?.timeout_seconds ?? 300) * 1000 + 5000 }
  )
}

/**
 * Run a checkpoint by name.
 */
export async function runCheckpointByName(
  name: string,
  data?: RunCheckpointRequest,
  options?: RequestOptions
): Promise<RunCheckpointResponse> {
  return apiClient.post<RunCheckpointResponse>(
    `/checkpoints/by-name/${encodeURIComponent(name)}/run`,
    data,
    { ...options, timeout: (data?.timeout_seconds ?? 300) * 1000 + 5000 }
  )
}

/**
 * Get the status of a checkpoint run.
 */
export async function getRunStatus(
  runId: string,
  options?: RequestOptions
): Promise<CheckpointResult> {
  return apiClient.get<CheckpointResult>(`/checkpoints/runs/${runId}`, options)
}

/**
 * Cancel a running checkpoint.
 */
export async function cancelRun(
  runId: string,
  options?: RequestOptions
): Promise<void> {
  return apiClient.post(`/checkpoints/runs/${runId}/cancel`, undefined, options)
}

// ============================================================================
// Checkpoint History
// ============================================================================

/**
 * List checkpoint runs.
 */
export async function listCheckpointRuns(
  params?: ListCheckpointRunsParams,
  options?: RequestOptions
): Promise<ListCheckpointRunsResponse> {
  return apiClient.get<ListCheckpointRunsResponse>('/checkpoints/runs', {
    ...options,
    params: params as Record<string, string | number | boolean | undefined>,
  })
}

/**
 * Get checkpoint run detail.
 */
export async function getCheckpointRun(
  runId: string,
  options?: RequestOptions
): Promise<CheckpointResult> {
  return apiClient.get<CheckpointResult>(`/checkpoints/runs/${runId}`, options)
}

/**
 * Get runs for a specific checkpoint.
 */
export async function getCheckpointRunHistory(
  checkpointId: string,
  params?: Omit<ListCheckpointRunsParams, 'checkpoint_name'>,
  options?: RequestOptions
): Promise<ListCheckpointRunsResponse> {
  return apiClient.get<ListCheckpointRunsResponse>(`/checkpoints/${checkpointId}/runs`, {
    ...options,
    params: params as Record<string, string | number | boolean | undefined>,
  })
}

/**
 * Get the latest run for a checkpoint.
 */
export async function getLatestRun(
  checkpointId: string,
  options?: RequestOptions
): Promise<CheckpointResult | null> {
  return apiClient.get<CheckpointResult | null>(`/checkpoints/${checkpointId}/runs/latest`, options)
}

// ============================================================================
// Checkpoint Statistics
// ============================================================================

/**
 * Get checkpoint statistics.
 */
export async function getCheckpointStatistics(
  checkpointId: string,
  params?: {
    start_time?: string
    end_time?: string
  },
  options?: RequestOptions
): Promise<CheckpointStatistics> {
  return apiClient.get<CheckpointStatistics>(`/checkpoints/${checkpointId}/statistics`, {
    ...options,
    params,
  })
}

/**
 * Get global checkpoint statistics.
 */
export async function getGlobalStatistics(
  params?: {
    start_time?: string
    end_time?: string
  },
  options?: RequestOptions
): Promise<CheckpointStatistics> {
  return apiClient.get<CheckpointStatistics>('/checkpoints/statistics', {
    ...options,
    params,
  })
}

// ============================================================================
// Actions Management
// ============================================================================

/**
 * Get available action types.
 */
export async function getActionTypes(
  options?: RequestOptions
): Promise<ActionTypeInfo[]> {
  return apiClient.get<ActionTypeInfo[]>('/checkpoints/actions/types', options)
}

/**
 * Get actions for a checkpoint.
 */
export async function getCheckpointActions(
  checkpointId: string,
  options?: RequestOptions
): Promise<ActionConfig[]> {
  return apiClient.get<ActionConfig[]>(`/checkpoints/${checkpointId}/actions`, options)
}

/**
 * Add an action to a checkpoint.
 */
export async function addCheckpointAction(
  checkpointId: string,
  action: ActionConfig,
  options?: RequestOptions
): Promise<ActionConfig> {
  return apiClient.post<ActionConfig>(`/checkpoints/${checkpointId}/actions`, action, options)
}

/**
 * Update an action on a checkpoint.
 */
export async function updateCheckpointAction(
  checkpointId: string,
  actionName: string,
  action: Partial<ActionConfig>,
  options?: RequestOptions
): Promise<ActionConfig> {
  return apiClient.put<ActionConfig>(
    `/checkpoints/${checkpointId}/actions/${encodeURIComponent(actionName)}`,
    action,
    options
  )
}

/**
 * Remove an action from a checkpoint.
 */
export async function removeCheckpointAction(
  checkpointId: string,
  actionName: string,
  options?: RequestOptions
): Promise<void> {
  return apiClient.delete(
    `/checkpoints/${checkpointId}/actions/${encodeURIComponent(actionName)}`,
    options
  )
}

/**
 * Test an action configuration.
 */
export async function testAction(
  action: ActionConfig,
  options?: RequestOptions
): Promise<ActionResult> {
  return apiClient.post<ActionResult>('/checkpoints/actions/test', action, options)
}

// ============================================================================
// Triggers Management
// ============================================================================

/**
 * Get triggers for a checkpoint.
 */
export async function getCheckpointTriggers(
  checkpointId: string,
  options?: RequestOptions
): Promise<Trigger[]> {
  return apiClient.get<Trigger[]>(`/checkpoints/${checkpointId}/triggers`, options)
}

/**
 * Add a trigger to a checkpoint.
 */
export async function addCheckpointTrigger(
  checkpointId: string,
  trigger: TriggerConfig,
  options?: RequestOptions
): Promise<Trigger> {
  return apiClient.post<Trigger>(`/checkpoints/${checkpointId}/triggers`, trigger, options)
}

/**
 * Update a trigger on a checkpoint.
 */
export async function updateCheckpointTrigger(
  checkpointId: string,
  triggerId: string,
  trigger: Partial<TriggerConfig>,
  options?: RequestOptions
): Promise<Trigger> {
  return apiClient.put<Trigger>(
    `/checkpoints/${checkpointId}/triggers/${triggerId}`,
    trigger,
    options
  )
}

/**
 * Remove a trigger from a checkpoint.
 */
export async function removeCheckpointTrigger(
  checkpointId: string,
  triggerId: string,
  options?: RequestOptions
): Promise<void> {
  return apiClient.delete(`/checkpoints/${checkpointId}/triggers/${triggerId}`, options)
}

/**
 * Pause a trigger.
 */
export async function pauseTrigger(
  checkpointId: string,
  triggerId: string,
  options?: RequestOptions
): Promise<Trigger> {
  return apiClient.post<Trigger>(
    `/checkpoints/${checkpointId}/triggers/${triggerId}/pause`,
    undefined,
    options
  )
}

/**
 * Resume a trigger.
 */
export async function resumeTrigger(
  checkpointId: string,
  triggerId: string,
  options?: RequestOptions
): Promise<Trigger> {
  return apiClient.post<Trigger>(
    `/checkpoints/${checkpointId}/triggers/${triggerId}/resume`,
    undefined,
    options
  )
}

/**
 * Get trigger history.
 */
export async function getTriggerHistory(
  checkpointId: string,
  triggerId: string,
  params?: {
    limit?: number
    offset?: number
  },
  options?: RequestOptions
): Promise<{ items: TriggerResult[]; total: number }> {
  return apiClient.get<{ items: TriggerResult[]; total: number }>(
    `/checkpoints/${checkpointId}/triggers/${triggerId}/history`,
    { ...options, params }
  )
}

// ============================================================================
// Routing Management
// ============================================================================

/**
 * Get router configuration for a checkpoint.
 */
export async function getCheckpointRouter(
  checkpointId: string,
  options?: RequestOptions
): Promise<Router | null> {
  return apiClient.get<Router | null>(`/checkpoints/${checkpointId}/router`, options)
}

/**
 * Set router configuration for a checkpoint.
 */
export async function setCheckpointRouter(
  checkpointId: string,
  router: Router,
  options?: RequestOptions
): Promise<Router> {
  return apiClient.put<Router>(`/checkpoints/${checkpointId}/router`, router, options)
}

/**
 * Add a route to a checkpoint's router.
 */
export async function addCheckpointRoute(
  checkpointId: string,
  route: Route,
  options?: RequestOptions
): Promise<Route> {
  return apiClient.post<Route>(`/checkpoints/${checkpointId}/router/routes`, route, options)
}

/**
 * Update a route in a checkpoint's router.
 */
export async function updateCheckpointRoute(
  checkpointId: string,
  routeName: string,
  route: Partial<Route>,
  options?: RequestOptions
): Promise<Route> {
  return apiClient.put<Route>(
    `/checkpoints/${checkpointId}/router/routes/${encodeURIComponent(routeName)}`,
    route,
    options
  )
}

/**
 * Remove a route from a checkpoint's router.
 */
export async function removeCheckpointRoute(
  checkpointId: string,
  routeName: string,
  options?: RequestOptions
): Promise<void> {
  return apiClient.delete(
    `/checkpoints/${checkpointId}/router/routes/${encodeURIComponent(routeName)}`,
    options
  )
}

/**
 * Test a routing rule.
 */
export async function testRoutingRule(
  rule: RoutingRule,
  context: Record<string, unknown>,
  options?: RequestOptions
): Promise<{ matches: boolean; reason?: string }> {
  return apiClient.post<{ matches: boolean; reason?: string }>(
    '/checkpoints/routing/test',
    { rule, context },
    options
  )
}

// ============================================================================
// Throttling Management
// ============================================================================

/**
 * Get throttling configuration.
 */
export async function getThrottlingConfig(
  options?: RequestOptions
): Promise<ThrottlingConfig> {
  return apiClient.get<ThrottlingConfig>('/checkpoints/throttling/config', options)
}

/**
 * Update throttling configuration.
 */
export async function updateThrottlingConfig(
  config: Partial<ThrottlingConfig>,
  options?: RequestOptions
): Promise<ThrottlingConfig> {
  return apiClient.put<ThrottlingConfig>('/checkpoints/throttling/config', config, options)
}

/**
 * Get throttling statistics.
 */
export async function getThrottlingStats(
  options?: RequestOptions
): Promise<ThrottlingStats> {
  return apiClient.get<ThrottlingStats>('/checkpoints/throttling/stats', options)
}

/**
 * Reset throttling statistics.
 */
export async function resetThrottlingStats(
  options?: RequestOptions
): Promise<void> {
  return apiClient.post('/checkpoints/throttling/stats/reset', undefined, options)
}

// ============================================================================
// Deduplication Management
// ============================================================================

/**
 * Get deduplication configuration.
 */
export async function getDeduplicationConfig(
  options?: RequestOptions
): Promise<DeduplicationConfig> {
  return apiClient.get<DeduplicationConfig>('/checkpoints/deduplication/config', options)
}

/**
 * Update deduplication configuration.
 */
export async function updateDeduplicationConfig(
  config: Partial<DeduplicationConfig>,
  options?: RequestOptions
): Promise<DeduplicationConfig> {
  return apiClient.put<DeduplicationConfig>('/checkpoints/deduplication/config', config, options)
}

/**
 * Get deduplication statistics.
 */
export async function getDeduplicationStats(
  options?: RequestOptions
): Promise<DeduplicationStats> {
  return apiClient.get<DeduplicationStats>('/checkpoints/deduplication/stats', options)
}

/**
 * Clear deduplication cache.
 */
export async function clearDeduplicationCache(
  options?: RequestOptions
): Promise<void> {
  return apiClient.post('/checkpoints/deduplication/cache/clear', undefined, options)
}

// ============================================================================
// Escalation Management
// ============================================================================

/**
 * List escalation policies.
 */
export async function listEscalationPolicies(
  options?: RequestOptions
): Promise<EscalationPolicy[]> {
  return apiClient.get<EscalationPolicy[]>('/checkpoints/escalation/policies', options)
}

/**
 * Get an escalation policy.
 */
export async function getEscalationPolicy(
  policyId: string,
  options?: RequestOptions
): Promise<EscalationPolicy> {
  return apiClient.get<EscalationPolicy>(`/checkpoints/escalation/policies/${policyId}`, options)
}

/**
 * Create an escalation policy.
 */
export async function createEscalationPolicy(
  data: CreateEscalationPolicyRequest,
  options?: RequestOptions
): Promise<EscalationPolicy> {
  return apiClient.post<EscalationPolicy>('/checkpoints/escalation/policies', data, options)
}

/**
 * Update an escalation policy.
 */
export async function updateEscalationPolicy(
  policyId: string,
  data: Partial<EscalationPolicy>,
  options?: RequestOptions
): Promise<EscalationPolicy> {
  return apiClient.put<EscalationPolicy>(
    `/checkpoints/escalation/policies/${policyId}`,
    data,
    options
  )
}

/**
 * Delete an escalation policy.
 */
export async function deleteEscalationPolicy(
  policyId: string,
  options?: RequestOptions
): Promise<void> {
  return apiClient.delete(`/checkpoints/escalation/policies/${policyId}`, options)
}

/**
 * Trigger an escalation.
 */
export async function triggerEscalation(
  data: TriggerEscalationRequest,
  options?: RequestOptions
): Promise<EscalationRecord> {
  return apiClient.post<EscalationRecord>('/checkpoints/escalation/trigger', data, options)
}

/**
 * Acknowledge an escalation.
 */
export async function acknowledgeEscalation(
  data: AcknowledgeEscalationRequest,
  options?: RequestOptions
): Promise<EscalationRecord> {
  return apiClient.post<EscalationRecord>('/checkpoints/escalation/acknowledge', data, options)
}

/**
 * Resolve an escalation.
 */
export async function resolveEscalation(
  data: ResolveEscalationRequest,
  options?: RequestOptions
): Promise<EscalationRecord> {
  return apiClient.post<EscalationRecord>('/checkpoints/escalation/resolve', data, options)
}

/**
 * Cancel an escalation.
 */
export async function cancelEscalation(
  recordId: string,
  data: { cancelled_by: string; reason?: string },
  options?: RequestOptions
): Promise<EscalationRecord> {
  return apiClient.post<EscalationRecord>(
    `/checkpoints/escalation/records/${recordId}/cancel`,
    data,
    options
  )
}

/**
 * List active escalations.
 */
export async function listActiveEscalations(
  params?: { policy_name?: string; limit?: number },
  options?: RequestOptions
): Promise<EscalationRecord[]> {
  return apiClient.get<EscalationRecord[]>('/checkpoints/escalation/records/active', {
    ...options,
    params,
  })
}

/**
 * Get escalation record.
 */
export async function getEscalationRecord(
  recordId: string,
  options?: RequestOptions
): Promise<EscalationRecord> {
  return apiClient.get<EscalationRecord>(`/checkpoints/escalation/records/${recordId}`, options)
}

/**
 * Get escalation statistics.
 */
export async function getEscalationStats(
  params?: { policy_name?: string; start_time?: string; end_time?: string },
  options?: RequestOptions
): Promise<EscalationStats> {
  return apiClient.get<EscalationStats>('/checkpoints/escalation/stats', {
    ...options,
    params,
  })
}

// ============================================================================
// Bulk Operations
// ============================================================================

/**
 * Run multiple checkpoints.
 */
export async function runMultipleCheckpoints(
  ids: string[],
  data?: RunCheckpointRequest,
  options?: RequestOptions
): Promise<Record<string, RunCheckpointResponse>> {
  return apiClient.post<Record<string, RunCheckpointResponse>>(
    '/checkpoints/run-multiple',
    { checkpoint_ids: ids, ...data },
    options
  )
}

/**
 * Enable multiple checkpoints.
 */
export async function enableMultipleCheckpoints(
  ids: string[],
  options?: RequestOptions
): Promise<{ updated: number }> {
  return apiClient.post<{ updated: number }>(
    '/checkpoints/bulk/enable',
    { checkpoint_ids: ids },
    options
  )
}

/**
 * Disable multiple checkpoints.
 */
export async function disableMultipleCheckpoints(
  ids: string[],
  options?: RequestOptions
): Promise<{ updated: number }> {
  return apiClient.post<{ updated: number }>(
    '/checkpoints/bulk/disable',
    { checkpoint_ids: ids },
    options
  )
}

/**
 * Delete multiple checkpoints.
 */
export async function deleteMultipleCheckpoints(
  ids: string[],
  options?: RequestOptions
): Promise<{ deleted: number }> {
  return apiClient.post<{ deleted: number }>(
    '/checkpoints/bulk/delete',
    { checkpoint_ids: ids },
    options
  )
}

// ============================================================================
// Export/Import
// ============================================================================

/**
 * Export checkpoint configuration.
 */
export async function exportCheckpoint(
  id: string,
  format: 'json' | 'yaml' = 'json',
  options?: RequestOptions
): Promise<string> {
  return apiClient.get<string>(`/checkpoints/${id}/export`, {
    ...options,
    params: { format },
  })
}

/**
 * Import checkpoint configuration.
 */
export async function importCheckpoint(
  config: string,
  format: 'json' | 'yaml' = 'json',
  options?: RequestOptions
): Promise<Checkpoint> {
  return apiClient.post<Checkpoint>(
    '/checkpoints/import',
    { config, format },
    options
  )
}

/**
 * Validate checkpoint configuration (dry run).
 */
export async function validateCheckpointConfig(
  config: CheckpointConfig,
  options?: RequestOptions
): Promise<{ valid: boolean; errors: string[] }> {
  return apiClient.post<{ valid: boolean; errors: string[] }>(
    '/checkpoints/validate',
    config,
    options
  )
}
