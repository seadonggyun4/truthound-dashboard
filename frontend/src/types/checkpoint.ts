/**
 * Checkpoint types for validation pipeline orchestration.
 *
 * A Checkpoint represents a complete data validation pipeline that
 * combines data sources, validators, actions, triggers, and routing.
 *
 * Based on truthound's checkpoint module with enterprise-grade features:
 * - Data source binding
 * - Validator configuration
 * - Action orchestration (notifications, storage, webhooks)
 * - Trigger management (schedule, cron, event, file watch)
 * - Result routing with rule-based conditions
 * - Async execution strategies
 */

import type { ActionConfig, ActionResult, ActionStatus } from './actions'
import type { TriggerConfig, TriggerType } from './triggers'
import type { Route, RouteMode, RoutingRule } from './routing'

// =============================================================================
// Checkpoint Status
// =============================================================================

/**
 * Status of a checkpoint run.
 */
export type CheckpointStatus =
  | 'pending'    // Not yet started
  | 'running'    // Currently executing
  | 'success'    // Validation passed
  | 'failure'    // Validation failed (issues found)
  | 'error'      // System error occurred
  | 'warning'    // Passed with warnings
  | 'skipped'    // Skipped (e.g., no data)
  | 'timeout'    // Execution timed out

/**
 * Human-readable labels for checkpoint statuses.
 */
export const CHECKPOINT_STATUS_LABELS: Record<CheckpointStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  success: 'Success',
  failure: 'Failure',
  error: 'Error',
  warning: 'Warning',
  skipped: 'Skipped',
  timeout: 'Timeout',
}

/**
 * Badge variants for checkpoint statuses.
 */
export const CHECKPOINT_STATUS_VARIANTS: Record<CheckpointStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  running: 'default',
  success: 'default',
  failure: 'destructive',
  error: 'destructive',
  warning: 'outline',
  skipped: 'secondary',
  timeout: 'destructive',
}

// =============================================================================
// Checkpoint Configuration
// =============================================================================

/**
 * Configuration for a checkpoint.
 */
export interface CheckpointConfig {
  /** Checkpoint name for identification */
  name: string
  /** Human-readable description */
  description?: string
  /** ID of the data source to validate */
  source_id?: string
  /** Name of the data source */
  source_name?: string
  /** List of validator names to run */
  validators?: string[]
  /** Per-validator configuration */
  validator_config?: Record<string, Record<string, unknown>>
  /** Path to schema file for validation */
  schema_path?: string
  /** Auto-learn schema for validation */
  auto_schema?: boolean
  /** Tags for categorization and routing */
  tags?: Record<string, string>
  /** Whether this checkpoint is enabled */
  enabled?: boolean
  /** Maximum execution time in seconds */
  timeout_seconds?: number
  /** Retry on system errors */
  retry_on_error?: boolean
  /** Number of retries */
  retry_count?: number
  /** Additional metadata */
  metadata?: Record<string, unknown>
  /** Minimum pass rate for success (0-1) */
  success_threshold?: number
  /** Pass rate below which is warning (0-1) */
  warning_threshold?: number
  /** Sample size for validation */
  sample_size?: number
  /** Run name template (strftime format) */
  run_name_template?: string
  /** Fail on critical issues */
  fail_on_critical?: boolean
  /** Fail on high issues */
  fail_on_high?: boolean
}

/**
 * Default checkpoint configuration.
 */
export const DEFAULT_CHECKPOINT_CONFIG: Partial<CheckpointConfig> = {
  enabled: true,
  timeout_seconds: 300,
  retry_on_error: false,
  retry_count: 0,
  success_threshold: 1.0,
  warning_threshold: 0.9,
  auto_schema: false,
  fail_on_critical: true,
  fail_on_high: false,
}

// =============================================================================
// Checkpoint Result
// =============================================================================

/**
 * Result of a checkpoint run.
 */
export interface CheckpointResult {
  /** Name of the checkpoint */
  checkpoint_name: string
  /** Unique run identifier */
  run_id: string
  /** Execution status */
  status: CheckpointStatus
  /** When execution started (ISO string) */
  started_at?: string
  /** When execution completed (ISO string) */
  completed_at?: string
  /** Execution duration in milliseconds */
  duration_ms: number
  /** Data source name */
  source_name?: string
  /** Number of rows validated */
  row_count?: number
  /** Number of columns */
  column_count?: number
  /** Total number of issues */
  issue_count: number
  /** Number of critical issues */
  critical_count: number
  /** Number of high severity issues */
  high_count: number
  /** Number of medium severity issues */
  medium_count: number
  /** Number of low severity issues */
  low_count: number
  /** Number of info severity issues */
  info_count: number
  /** Whether critical issues were found */
  has_critical: boolean
  /** Whether high severity issues were found */
  has_high: boolean
  /** Pass rate (0-1) */
  pass_rate?: number
  /** List of validation issues */
  issues?: ValidationIssue[]
  /** Results from action execution */
  action_results?: ActionResult[]
  /** Context from the trigger (if any) */
  trigger_context?: Record<string, unknown>
  /** Error message if status is ERROR */
  error_message?: string
  /** Additional result metadata */
  metadata?: Record<string, unknown>
}

/**
 * A validation issue from a checkpoint run.
 */
export interface ValidationIssue {
  /** Issue identifier */
  id?: string
  /** Validator that raised the issue */
  validator: string
  /** Affected column */
  column?: string
  /** Severity level */
  severity: IssueSeverity
  /** Issue message */
  message: string
  /** Additional details */
  details?: Record<string, unknown>
  /** Row index if applicable */
  row_index?: number
  /** Actual value */
  actual_value?: unknown
  /** Expected value */
  expected_value?: unknown
}

/**
 * Issue severity levels.
 */
export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'

/**
 * Severity level ordering (higher = more severe).
 */
export const SEVERITY_ORDER: Record<IssueSeverity, number> = {
  critical: 5,
  high: 4,
  medium: 3,
  low: 2,
  info: 1,
}

// =============================================================================
// Checkpoint Definition (Full entity)
// =============================================================================

/**
 * Full checkpoint definition including all configuration.
 */
export interface Checkpoint {
  /** Unique identifier */
  id: string
  /** Checkpoint configuration */
  config: CheckpointConfig
  /** Actions to execute after validation */
  actions: ActionConfig[]
  /** Triggers for automatic execution */
  triggers: TriggerConfig[]
  /** Router for conditional action execution */
  router?: RouterConfig
  /** Creation timestamp */
  created_at: string
  /** Last update timestamp */
  updated_at: string
  /** Last run timestamp */
  last_run_at?: string
  /** Last run status */
  last_run_status?: CheckpointStatus
  /** Total run count */
  run_count: number
  /** Success run count */
  success_count: number
  /** Failure run count */
  failure_count: number
}

/**
 * Router configuration.
 */
export interface RouterConfig {
  /** Routing mode */
  mode: RouteMode
  /** Routes for conditional action execution */
  routes: Route[]
}

// =============================================================================
// Checkpoint Statistics
// =============================================================================

/**
 * Statistics for checkpoint runs.
 */
export interface CheckpointStatistics {
  /** Total number of runs */
  total_runs: number
  /** Number of successful runs */
  success_count: number
  /** Number of failed runs */
  failure_count: number
  /** Number of error runs */
  error_count: number
  /** Number of warning runs */
  warning_count: number
  /** Success rate (0-1) */
  success_rate: number
  /** Average duration in milliseconds */
  avg_duration_ms: number
  /** Average issue count */
  avg_issue_count: number
  /** Average pass rate */
  avg_pass_rate: number
  /** Last run timestamp */
  last_run_at?: string
  /** Time window for statistics */
  time_window?: {
    start: string
    end: string
  }
}

// =============================================================================
// Checkpoint Run History
// =============================================================================

/**
 * Summary of a checkpoint run for history lists.
 */
export interface CheckpointRunSummary {
  /** Unique run identifier */
  run_id: string
  /** Checkpoint name */
  checkpoint_name: string
  /** Execution status */
  status: CheckpointStatus
  /** When execution started */
  started_at: string
  /** Execution duration in milliseconds */
  duration_ms: number
  /** Total number of issues */
  issue_count: number
  /** Number of critical issues */
  critical_count: number
  /** Number of high severity issues */
  high_count: number
  /** Trigger type that initiated the run */
  trigger_type?: TriggerType
  /** Source of the trigger */
  trigger_source?: string
}

// =============================================================================
// API Request/Response Types
// =============================================================================

/**
 * Request to create a new checkpoint.
 */
export interface CreateCheckpointRequest {
  config: CheckpointConfig
  actions?: ActionConfig[]
  triggers?: TriggerConfig[]
  router?: RouterConfig
}

/**
 * Request to update a checkpoint.
 */
export interface UpdateCheckpointRequest {
  config?: Partial<CheckpointConfig>
  actions?: ActionConfig[]
  triggers?: TriggerConfig[]
  router?: RouterConfig
}

/**
 * Request to run a checkpoint.
 */
export interface RunCheckpointRequest {
  /** Optional trigger context */
  trigger_context?: Record<string, unknown>
  /** Run synchronously (wait for result) */
  sync?: boolean
  /** Timeout for sync runs */
  timeout_seconds?: number
}

/**
 * Response from running a checkpoint.
 */
export interface RunCheckpointResponse {
  /** Run ID for tracking */
  run_id: string
  /** Current status */
  status: CheckpointStatus
  /** Result if sync=true */
  result?: CheckpointResult
}

/**
 * List checkpoints response.
 */
export interface ListCheckpointsResponse {
  items: Checkpoint[]
  total: number
  page: number
  page_size: number
}

/**
 * List checkpoint runs response.
 */
export interface ListCheckpointRunsResponse {
  items: CheckpointRunSummary[]
  total: number
  page: number
  page_size: number
}

/**
 * Query parameters for listing checkpoints.
 */
export interface ListCheckpointsParams {
  /** Filter by name (partial match) */
  name?: string
  /** Filter by enabled status */
  enabled?: boolean
  /** Filter by tags */
  tags?: Record<string, string>
  /** Sort field */
  sort_by?: 'name' | 'created_at' | 'updated_at' | 'last_run_at'
  /** Sort order */
  sort_order?: 'asc' | 'desc'
  /** Page number */
  page?: number
  /** Page size */
  page_size?: number
}

/**
 * Query parameters for listing checkpoint runs.
 */
export interface ListCheckpointRunsParams {
  /** Filter by checkpoint name */
  checkpoint_name?: string
  /** Filter by status */
  status?: CheckpointStatus | CheckpointStatus[]
  /** Filter by start time (ISO string) */
  started_after?: string
  /** Filter by end time (ISO string) */
  started_before?: string
  /** Filter by trigger type */
  trigger_type?: TriggerType
  /** Sort field */
  sort_by?: 'started_at' | 'duration_ms' | 'issue_count'
  /** Sort order */
  sort_order?: 'asc' | 'desc'
  /** Page number */
  page?: number
  /** Page size */
  page_size?: number
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Check if a checkpoint status indicates success.
 */
export function isCheckpointSuccess(status: CheckpointStatus): boolean {
  return status === 'success'
}

/**
 * Check if a checkpoint status indicates failure or error.
 */
export function isCheckpointFailed(status: CheckpointStatus): boolean {
  return status === 'failure' || status === 'error' || status === 'timeout'
}

/**
 * Check if a checkpoint status is terminal (not pending or running).
 */
export function isCheckpointTerminal(status: CheckpointStatus): boolean {
  return status !== 'pending' && status !== 'running'
}

/**
 * Get the variant for a checkpoint status badge.
 */
export function getStatusBadgeVariant(status: CheckpointStatus): 'default' | 'secondary' | 'destructive' | 'outline' {
  return CHECKPOINT_STATUS_VARIANTS[status] ?? 'secondary'
}

/**
 * Calculate pass rate from issue counts.
 */
export function calculatePassRate(rowCount: number, issueCount: number): number {
  if (rowCount === 0) return 1
  return Math.max(0, 1 - (issueCount / rowCount))
}

/**
 * Format duration in human-readable form.
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
  return `${Math.floor(ms / 3600000)}h ${Math.floor((ms % 3600000) / 60000)}m`
}

/**
 * Sort issues by severity.
 */
export function sortIssuesBySeverity(issues: ValidationIssue[]): ValidationIssue[] {
  return [...issues].sort((a, b) => SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity])
}
