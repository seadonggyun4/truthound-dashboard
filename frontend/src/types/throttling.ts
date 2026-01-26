/**
 * Throttling types for controlling action execution rate.
 *
 * Throttling prevents action flooding by limiting how often actions
 * can be executed within a given time window.
 *
 * Features:
 * - Time-based rate limiting
 * - Token bucket algorithm
 * - Sliding window algorithm
 * - Per-action and global throttling
 * - Priority-based queue management
 */

// =============================================================================
// Throttling Algorithm Types
// =============================================================================

/**
 * Throttling algorithm types.
 */
export type ThrottlingAlgorithm =
  | 'token_bucket'    // Fixed rate with burst capacity
  | 'sliding_window'  // Count-based sliding window
  | 'fixed_window'    // Count-based fixed window
  | 'leaky_bucket'    // Constant rate output

/**
 * Algorithm metadata.
 */
export interface ThrottlingAlgorithmInfo {
  type: ThrottlingAlgorithm
  label: string
  description: string
  supports_burst?: boolean
}

/**
 * Metadata for all algorithms.
 */
export const THROTTLING_ALGORITHM_INFO: Record<ThrottlingAlgorithm, ThrottlingAlgorithmInfo> = {
  token_bucket: {
    type: 'token_bucket',
    label: 'Token Bucket',
    description: 'Allow bursts up to bucket size, then throttle to steady rate',
    supports_burst: true,
  },
  sliding_window: {
    type: 'sliding_window',
    label: 'Sliding Window',
    description: 'Limit requests within a sliding time window',
    supports_burst: false,
  },
  fixed_window: {
    type: 'fixed_window',
    label: 'Fixed Window',
    description: 'Limit requests within fixed time buckets',
    supports_burst: true,
  },
  leaky_bucket: {
    type: 'leaky_bucket',
    label: 'Leaky Bucket',
    description: 'Process requests at a constant rate',
    supports_burst: false,
  },
}

// =============================================================================
// Time Window
// =============================================================================

/**
 * Time window unit.
 */
export type WindowUnit = 'seconds' | 'minutes' | 'hours' | 'days'

/**
 * Time window definition.
 */
export interface TimeWindow {
  /** Value */
  value: number
  /** Unit */
  unit: WindowUnit
}

/**
 * Convert time window to seconds.
 */
export function timeWindowToSeconds(window: TimeWindow): number {
  switch (window.unit) {
    case 'seconds':
      return window.value
    case 'minutes':
      return window.value * 60
    case 'hours':
      return window.value * 3600
    case 'days':
      return window.value * 86400
    default:
      return window.value
  }
}

/**
 * Format time window for display.
 */
export function formatTimeWindow(window: TimeWindow): string {
  if (window.value === 1) {
    // Singular
    const unit = window.unit.replace(/s$/, '')
    return `1 ${unit}`
  }
  return `${window.value} ${window.unit}`
}

/**
 * Common time windows.
 */
export const COMMON_TIME_WINDOWS: TimeWindow[] = [
  { value: 30, unit: 'seconds' },
  { value: 1, unit: 'minutes' },
  { value: 5, unit: 'minutes' },
  { value: 15, unit: 'minutes' },
  { value: 30, unit: 'minutes' },
  { value: 1, unit: 'hours' },
  { value: 6, unit: 'hours' },
  { value: 12, unit: 'hours' },
  { value: 1, unit: 'days' },
]

// =============================================================================
// Throttling Configuration
// =============================================================================

/**
 * Throttling configuration.
 */
export interface ThrottlingConfig {
  /** Enable throttling */
  enabled: boolean
  /** Throttling algorithm */
  algorithm: ThrottlingAlgorithm
  /** Maximum requests per window */
  max_requests: number
  /** Time window */
  window: TimeWindow
  /** Burst size (for token_bucket) */
  burst_size?: number
  /** Refill rate (tokens per second, for token_bucket) */
  refill_rate?: number
  /** Key function to group throttling (e.g., by action, checkpoint) */
  key_by?: 'action' | 'checkpoint' | 'action_type' | 'global' | 'custom'
  /** Custom key template (Jinja2) */
  custom_key_template?: string
  /** Behavior when throttled */
  on_throttle: ThrottleBehavior
  /** Priority queue for throttled requests */
  enable_priority_queue?: boolean
  /** Maximum queue size */
  max_queue_size?: number
  /** Queue timeout (seconds) */
  queue_timeout_seconds?: number
}

/**
 * Behavior when throttled.
 */
export type ThrottleBehavior = 'drop' | 'queue' | 'delay' | 'raise_error'

/**
 * Labels for throttle behaviors.
 */
export const THROTTLE_BEHAVIOR_LABELS: Record<ThrottleBehavior, string> = {
  drop: 'Drop (discard silently)',
  queue: 'Queue (process later)',
  delay: 'Delay (wait and retry)',
  raise_error: 'Raise Error',
}

/**
 * Default throttling configuration.
 */
export const DEFAULT_THROTTLING_CONFIG: ThrottlingConfig = {
  enabled: false,
  algorithm: 'sliding_window',
  max_requests: 10,
  window: { value: 1, unit: 'minutes' },
  key_by: 'action',
  on_throttle: 'queue',
  enable_priority_queue: false,
  max_queue_size: 100,
  queue_timeout_seconds: 300,
}

// =============================================================================
// Per-Action Throttling
// =============================================================================

/**
 * Throttling configuration for a specific action.
 */
export interface ActionThrottleConfig {
  /** Action name or type */
  action: string
  /** Maximum requests per window */
  max_requests: number
  /** Time window */
  window: TimeWindow
  /** Override global behavior */
  on_throttle?: ThrottleBehavior
  /** Priority (higher = processed first when queued) */
  priority?: number
}

/**
 * Common presets for action throttling.
 */
export const ACTION_THROTTLE_PRESETS: Record<string, ActionThrottleConfig[]> = {
  conservative: [
    { action: 'pagerduty', max_requests: 5, window: { value: 1, unit: 'hours' } },
    { action: 'opsgenie', max_requests: 5, window: { value: 1, unit: 'hours' } },
    { action: 'slack', max_requests: 30, window: { value: 1, unit: 'minutes' } },
    { action: 'email', max_requests: 10, window: { value: 1, unit: 'hours' } },
    { action: 'webhook', max_requests: 60, window: { value: 1, unit: 'minutes' } },
  ],
  moderate: [
    { action: 'pagerduty', max_requests: 10, window: { value: 1, unit: 'hours' } },
    { action: 'opsgenie', max_requests: 10, window: { value: 1, unit: 'hours' } },
    { action: 'slack', max_requests: 60, window: { value: 1, unit: 'minutes' } },
    { action: 'email', max_requests: 30, window: { value: 1, unit: 'hours' } },
    { action: 'webhook', max_requests: 120, window: { value: 1, unit: 'minutes' } },
  ],
  aggressive: [
    { action: 'pagerduty', max_requests: 30, window: { value: 1, unit: 'hours' } },
    { action: 'opsgenie', max_requests: 30, window: { value: 1, unit: 'hours' } },
    { action: 'slack', max_requests: 120, window: { value: 1, unit: 'minutes' } },
    { action: 'email', max_requests: 60, window: { value: 1, unit: 'hours' } },
    { action: 'webhook', max_requests: 300, window: { value: 1, unit: 'minutes' } },
  ],
}

// =============================================================================
// Throttling Statistics
// =============================================================================

/**
 * Throttling statistics.
 */
export interface ThrottlingStats {
  /** Total requests processed */
  total_requests: number
  /** Requests allowed */
  allowed_count: number
  /** Requests throttled */
  throttled_count: number
  /** Requests queued */
  queued_count: number
  /** Requests dropped */
  dropped_count: number
  /** Current queue size */
  current_queue_size: number
  /** Average wait time (ms) for queued requests */
  avg_queue_wait_ms: number
  /** Current token count (for token_bucket) */
  current_tokens?: number
  /** Last reset time (ISO string) */
  last_reset_at?: string
  /** Stats per action/checkpoint */
  by_key?: Record<string, {
    allowed: number
    throttled: number
    queued: number
  }>
}

// =============================================================================
// Throttling Result
// =============================================================================

/**
 * Result of throttling check.
 */
export interface ThrottleResult {
  /** Whether request is allowed */
  allowed: boolean
  /** If not allowed, reason */
  reason?: 'rate_limited' | 'queue_full' | 'timeout'
  /** If queued, queue position */
  queue_position?: number
  /** Estimated wait time (ms) */
  estimated_wait_ms?: number
  /** Retry after (ISO string) */
  retry_after?: string
  /** Current count in window */
  current_count?: number
  /** Limit */
  limit?: number
  /** Remaining requests in window */
  remaining?: number
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Validate throttling configuration.
 */
export function validateThrottlingConfig(config: ThrottlingConfig): string[] {
  const errors: string[] = []

  if (config.max_requests <= 0) {
    errors.push('Max requests must be greater than 0')
  }

  if (config.window.value <= 0) {
    errors.push('Window value must be greater than 0')
  }

  if (config.algorithm === 'token_bucket') {
    if (config.burst_size !== undefined && config.burst_size < config.max_requests) {
      errors.push('Burst size should be at least max_requests')
    }
  }

  if (config.on_throttle === 'queue') {
    if (config.max_queue_size !== undefined && config.max_queue_size <= 0) {
      errors.push('Max queue size must be greater than 0')
    }
  }

  return errors
}

/**
 * Calculate effective rate per second.
 */
export function calculateRatePerSecond(config: ThrottlingConfig): number {
  const windowSeconds = timeWindowToSeconds(config.window)
  return config.max_requests / windowSeconds
}

/**
 * Format rate limit for display.
 */
export function formatRateLimit(config: ThrottlingConfig): string {
  return `${config.max_requests} per ${formatTimeWindow(config.window)}`
}

/**
 * Create throttling config from preset.
 */
export function createThrottlingConfigFromPreset(
  preset: keyof typeof ACTION_THROTTLE_PRESETS,
  algorithm: ThrottlingAlgorithm = 'sliding_window',
  onThrottle: ThrottleBehavior = 'queue'
): ThrottlingConfig & { action_configs: ActionThrottleConfig[] } {
  return {
    ...DEFAULT_THROTTLING_CONFIG,
    enabled: true,
    algorithm,
    on_throttle: onThrottle,
    action_configs: ACTION_THROTTLE_PRESETS[preset],
  }
}
