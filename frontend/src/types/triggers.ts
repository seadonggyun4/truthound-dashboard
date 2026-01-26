/**
 * Trigger types for checkpoint-based validation pipelines.
 *
 * Triggers determine when checkpoints should run. They support various
 * scheduling patterns and event-based execution.
 *
 * Supported trigger types:
 * - Cron: Standard cron expressions
 * - Interval: Run every N seconds/minutes/hours
 * - Event: Run on external events (webhook, message queue)
 * - File Watch: Run when files change
 * - Data Change: Run when data changes detected
 * - Manual: On-demand execution only
 */

// =============================================================================
// Trigger Types
// =============================================================================

/**
 * Available trigger types.
 */
export type TriggerType =
  | 'cron'
  | 'interval'
  | 'event'
  | 'file_watch'
  | 'data_change'
  | 'webhook'
  | 'manual'
  | 'one_time'
  | 'pipeline'

/**
 * Trigger type metadata.
 */
export interface TriggerTypeInfo {
  type: TriggerType
  label: string
  description: string
  icon?: string
}

/**
 * Metadata for all trigger types.
 */
export const TRIGGER_TYPE_INFO: Record<TriggerType, TriggerTypeInfo> = {
  cron: {
    type: 'cron',
    label: 'Cron Schedule',
    description: 'Run on a cron schedule (e.g., "0 0 * * *" for daily)',
    icon: 'calendar',
  },
  interval: {
    type: 'interval',
    label: 'Interval',
    description: 'Run every N seconds/minutes/hours',
    icon: 'repeat',
  },
  event: {
    type: 'event',
    label: 'Event',
    description: 'Run when specific events occur',
    icon: 'zap',
  },
  file_watch: {
    type: 'file_watch',
    label: 'File Watch',
    description: 'Run when files change in a directory',
    icon: 'file',
  },
  data_change: {
    type: 'data_change',
    label: 'Data Change',
    description: 'Run when data changes are detected',
    icon: 'database',
  },
  webhook: {
    type: 'webhook',
    label: 'Webhook',
    description: 'Run when webhook endpoint is called',
    icon: 'globe',
  },
  manual: {
    type: 'manual',
    label: 'Manual',
    description: 'Run only when triggered manually',
    icon: 'hand',
  },
  one_time: {
    type: 'one_time',
    label: 'One-time',
    description: 'Run once at a specific time',
    icon: 'clock',
  },
  pipeline: {
    type: 'pipeline',
    label: 'Pipeline',
    description: 'Run as part of a data pipeline',
    icon: 'git-branch',
  },
}

// =============================================================================
// Trigger Status
// =============================================================================

/**
 * Status of a trigger.
 */
export type TriggerStatus =
  | 'active'      // Trigger is active and scheduled
  | 'paused'      // Trigger is paused
  | 'disabled'    // Trigger is disabled
  | 'completed'   // One-time trigger has completed
  | 'error'       // Trigger has an error

/**
 * Labels for trigger statuses.
 */
export const TRIGGER_STATUS_LABELS: Record<TriggerStatus, string> = {
  active: 'Active',
  paused: 'Paused',
  disabled: 'Disabled',
  completed: 'Completed',
  error: 'Error',
}

// =============================================================================
// Trigger Configurations
// =============================================================================

/**
 * Base trigger configuration.
 */
export interface TriggerConfigBase {
  /** Trigger type */
  type: TriggerType
  /** Trigger name */
  name: string
  /** Description */
  description?: string
  /** Whether trigger is enabled */
  enabled?: boolean
  /** Start time (ISO string) - trigger won't fire before this */
  start_time?: string
  /** End time (ISO string) - trigger won't fire after this */
  end_time?: string
  /** Timezone for scheduling */
  timezone?: string
  /** Max concurrent runs */
  max_concurrent?: number
  /** Context to pass to checkpoint */
  context?: Record<string, unknown>
  /** Jitter (random delay) in seconds */
  jitter_seconds?: number
}

/**
 * Cron trigger configuration.
 */
export interface CronTriggerConfig extends TriggerConfigBase {
  type: 'cron'
  /** Cron expression */
  cron_expression: string
  /** Catch up missed runs */
  catch_up?: boolean
  /** Misfire grace time in seconds */
  misfire_grace_time?: number
}

/**
 * Interval trigger configuration.
 */
export interface IntervalTriggerConfig extends TriggerConfigBase {
  type: 'interval'
  /** Interval value */
  interval: number
  /** Interval unit */
  unit: 'seconds' | 'minutes' | 'hours' | 'days'
  /** Start immediately */
  run_immediately?: boolean
}

/**
 * Event trigger configuration.
 */
export interface EventTriggerConfig extends TriggerConfigBase {
  type: 'event'
  /** Event type to listen for */
  event_type: string
  /** Event source (queue, topic, etc.) */
  event_source?: string
  /** Filter expression for events */
  filter_expression?: string
  /** Debounce time in seconds */
  debounce_seconds?: number
}

/**
 * File watch trigger configuration.
 */
export interface FileWatchTriggerConfig extends TriggerConfigBase {
  type: 'file_watch'
  /** Directory or file path to watch */
  watch_path: string
  /** File patterns to match (glob) */
  patterns?: string[]
  /** Events to watch for */
  events?: ('created' | 'modified' | 'deleted')[]
  /** Recursive watch */
  recursive?: boolean
  /** Debounce time in seconds */
  debounce_seconds?: number
  /** Ignore patterns */
  ignore_patterns?: string[]
}

/**
 * Data change trigger configuration.
 */
export interface DataChangeTriggerConfig extends TriggerConfigBase {
  type: 'data_change'
  /** Data source to monitor */
  data_source: string
  /** Change detection method */
  detection_method: 'row_count' | 'checksum' | 'timestamp' | 'custom'
  /** Polling interval in seconds */
  poll_interval?: number
  /** Minimum change threshold */
  min_change_threshold?: number
  /** Custom detection query */
  detection_query?: string
}

/**
 * Webhook trigger configuration.
 */
export interface WebhookTriggerConfig extends TriggerConfigBase {
  type: 'webhook'
  /** Webhook path (will be appended to base URL) */
  path?: string
  /** Allowed HTTP methods */
  methods?: ('GET' | 'POST' | 'PUT')[]
  /** Authentication type */
  auth_type?: 'none' | 'token' | 'signature' | 'basic'
  /** Auth secret (env var reference) */
  auth_secret?: string
  /** Validate payload schema */
  payload_schema?: Record<string, unknown>
}

/**
 * Manual trigger configuration.
 */
export interface ManualTriggerConfig extends TriggerConfigBase {
  type: 'manual'
  /** Require confirmation */
  require_confirmation?: boolean
  /** Allowed users/roles */
  allowed_users?: string[]
}

/**
 * One-time trigger configuration.
 */
export interface OneTimeTriggerConfig extends TriggerConfigBase {
  type: 'one_time'
  /** Run time (ISO string) */
  run_time: string
}

/**
 * Pipeline trigger configuration.
 */
export interface PipelineTriggerConfig extends TriggerConfigBase {
  type: 'pipeline'
  /** Pipeline/DAG ID */
  pipeline_id?: string
  /** Task/step ID within pipeline */
  task_id?: string
  /** Dependencies (other checkpoint names) */
  depends_on?: string[]
  /** Dependency type */
  dependency_type?: 'all' | 'any'
}

/**
 * Union type for all trigger configurations.
 */
export type TriggerConfig =
  | CronTriggerConfig
  | IntervalTriggerConfig
  | EventTriggerConfig
  | FileWatchTriggerConfig
  | DataChangeTriggerConfig
  | WebhookTriggerConfig
  | ManualTriggerConfig
  | OneTimeTriggerConfig
  | PipelineTriggerConfig

// =============================================================================
// Trigger Instance
// =============================================================================

/**
 * A trigger instance with state.
 */
export interface Trigger {
  /** Unique identifier */
  id: string
  /** Trigger configuration */
  config: TriggerConfig
  /** Current status */
  status: TriggerStatus
  /** Next scheduled run time (ISO string) */
  next_run_at?: string
  /** Last run time (ISO string) */
  last_run_at?: string
  /** Last run status */
  last_run_status?: 'success' | 'failure' | 'error'
  /** Run count */
  run_count: number
  /** Error count */
  error_count: number
  /** Last error message */
  last_error?: string
  /** Creation time */
  created_at: string
  /** Last update time */
  updated_at: string
}

// =============================================================================
// Trigger Result
// =============================================================================

/**
 * Result from a trigger execution.
 */
export interface TriggerResult {
  /** Trigger ID */
  trigger_id: string
  /** Trigger type */
  trigger_type: TriggerType
  /** Trigger name */
  trigger_name: string
  /** Execution status */
  status: 'fired' | 'skipped' | 'error'
  /** Checkpoint run ID (if fired) */
  run_id?: string
  /** Fire time (ISO string) */
  fired_at: string
  /** Duration to trigger checkpoint (ms) */
  duration_ms?: number
  /** Skip reason (if skipped) */
  skip_reason?: string
  /** Error message (if error) */
  error?: string
  /** Context passed to checkpoint */
  context?: Record<string, unknown>
}

// =============================================================================
// Cron Expression Helpers
// =============================================================================

/**
 * Common cron expressions.
 */
export const COMMON_CRON_EXPRESSIONS = {
  every_minute: { expression: '* * * * *', label: 'Every minute' },
  every_5_minutes: { expression: '*/5 * * * *', label: 'Every 5 minutes' },
  every_15_minutes: { expression: '*/15 * * * *', label: 'Every 15 minutes' },
  every_30_minutes: { expression: '*/30 * * * *', label: 'Every 30 minutes' },
  hourly: { expression: '0 * * * *', label: 'Every hour' },
  every_6_hours: { expression: '0 */6 * * *', label: 'Every 6 hours' },
  daily_midnight: { expression: '0 0 * * *', label: 'Daily at midnight' },
  daily_6am: { expression: '0 6 * * *', label: 'Daily at 6 AM' },
  daily_noon: { expression: '0 12 * * *', label: 'Daily at noon' },
  daily_6pm: { expression: '0 18 * * *', label: 'Daily at 6 PM' },
  weekly_monday: { expression: '0 0 * * 1', label: 'Weekly on Monday' },
  weekly_friday: { expression: '0 18 * * 5', label: 'Weekly on Friday 6 PM' },
  monthly_first: { expression: '0 0 1 * *', label: 'Monthly on 1st' },
  monthly_last: { expression: '0 0 L * *', label: 'Monthly on last day' },
}

/**
 * Parse a cron expression into human-readable format.
 */
export function describeCronExpression(expression: string): string {
  // Find matching common expression
  for (const [, info] of Object.entries(COMMON_CRON_EXPRESSIONS)) {
    if (info.expression === expression) {
      return info.label
    }
  }

  // Basic parsing for custom expressions
  const parts = expression.split(' ')
  if (parts.length !== 5) return expression

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

  const descriptions: string[] = []

  // Minute
  if (minute === '*') {
    descriptions.push('Every minute')
  } else if (minute.startsWith('*/')) {
    descriptions.push(`Every ${minute.slice(2)} minutes`)
  } else if (minute === '0') {
    // At the start of the hour
  }

  // Hour
  if (hour !== '*' && !hour.startsWith('*/')) {
    descriptions.push(`at ${hour}:${minute === '0' ? '00' : minute}`)
  } else if (hour.startsWith('*/')) {
    descriptions.push(`every ${hour.slice(2)} hours`)
  }

  // Day of month
  if (dayOfMonth !== '*') {
    if (dayOfMonth === 'L') {
      descriptions.push('on the last day of the month')
    } else {
      descriptions.push(`on day ${dayOfMonth}`)
    }
  }

  // Month
  if (month !== '*') {
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const monthNum = parseInt(month, 10)
    if (monthNum >= 1 && monthNum <= 12) {
      descriptions.push(`in ${monthNames[monthNum - 1]}`)
    }
  }

  // Day of week
  if (dayOfWeek !== '*') {
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const dayNum = parseInt(dayOfWeek, 10)
    if (dayNum >= 0 && dayNum <= 6) {
      descriptions.push(`on ${dayNames[dayNum]}`)
    }
  }

  return descriptions.join(' ') || expression
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get trigger type info.
 */
export function getTriggerTypeInfo(type: TriggerType): TriggerTypeInfo {
  return TRIGGER_TYPE_INFO[type]
}

/**
 * Create a default trigger config for a type.
 */
export function createDefaultTriggerConfig(type: TriggerType, name: string): TriggerConfig {
  const base = {
    name,
    enabled: true,
  }

  switch (type) {
    case 'cron':
      return { ...base, type: 'cron', cron_expression: '0 0 * * *' }
    case 'interval':
      return { ...base, type: 'interval', interval: 60, unit: 'minutes' }
    case 'event':
      return { ...base, type: 'event', event_type: '' }
    case 'file_watch':
      return { ...base, type: 'file_watch', watch_path: '.', events: ['modified'] }
    case 'data_change':
      return { ...base, type: 'data_change', data_source: '', detection_method: 'row_count' }
    case 'webhook':
      return { ...base, type: 'webhook' }
    case 'manual':
      return { ...base, type: 'manual' }
    case 'one_time':
      return { ...base, type: 'one_time', run_time: new Date().toISOString() }
    case 'pipeline':
      return { ...base, type: 'pipeline' }
    default:
      return { ...base, type: 'manual' }
  }
}

/**
 * Validate a trigger configuration.
 */
export function validateTriggerConfig(config: TriggerConfig): string[] {
  const errors: string[] = []

  if (!config.name?.trim()) {
    errors.push('Trigger name is required')
  }

  switch (config.type) {
    case 'cron':
      if (!config.cron_expression?.trim()) {
        errors.push('Cron expression is required')
      }
      break
    case 'interval':
      if (!config.interval || config.interval <= 0) {
        errors.push('Interval must be greater than 0')
      }
      break
    case 'event':
      if (!config.event_type?.trim()) {
        errors.push('Event type is required')
      }
      break
    case 'file_watch':
      if (!config.watch_path?.trim()) {
        errors.push('Watch path is required')
      }
      break
    case 'data_change':
      if (!config.data_source?.trim()) {
        errors.push('Data source is required')
      }
      break
    case 'one_time':
      if (!config.run_time) {
        errors.push('Run time is required')
      }
      break
  }

  return errors
}

/**
 * Calculate next run time from cron expression.
 * Note: This is a simplified version - use a proper cron library for production.
 */
export function getNextCronRun(expression: string, from: Date = new Date()): Date | null {
  // This is a placeholder - in production, use a library like cron-parser
  try {
    // Basic implementation for common cases
    const parts = expression.split(' ')
    if (parts.length !== 5) return null

    const next = new Date(from)
    next.setSeconds(0)
    next.setMilliseconds(0)

    // Add 1 minute minimum
    next.setMinutes(next.getMinutes() + 1)

    return next
  } catch {
    return null
  }
}
