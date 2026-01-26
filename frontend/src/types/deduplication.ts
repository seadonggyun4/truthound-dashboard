/**
 * Deduplication types for preventing duplicate notifications.
 *
 * The deduplication system suppresses repeated delivery of identical
 * notifications based on time windows and fingerprinting strategies.
 *
 * Features:
 * - Multiple fingerprinting strategies
 * - Configurable time windows
 * - Window strategies (sliding, tumbling, session)
 * - Per-action and per-severity configuration
 * - Store backends (memory, Redis)
 */

import type { TimeWindow } from './throttling'

// =============================================================================
// Deduplication Policy
// =============================================================================

/**
 * Deduplication policies.
 */
export type DeduplicationPolicy =
  | 'none'         // No deduplication
  | 'basic'        // Differentiate by checkpoint + action_type
  | 'severity'     // + differentiate by severity
  | 'issue_based'  // + differentiate by issue types
  | 'strict'       // Use full fingerprint
  | 'custom'       // User-defined function

/**
 * Policy metadata.
 */
export interface DeduplicationPolicyInfo {
  type: DeduplicationPolicy
  label: string
  description: string
  complexity: 'low' | 'medium' | 'high'
}

/**
 * Metadata for all policies.
 */
export const DEDUPLICATION_POLICY_INFO: Record<DeduplicationPolicy, DeduplicationPolicyInfo> = {
  none: {
    type: 'none',
    label: 'None',
    description: 'No deduplication - all notifications are sent',
    complexity: 'low',
  },
  basic: {
    type: 'basic',
    label: 'Basic',
    description: 'Group by checkpoint name and action type',
    complexity: 'low',
  },
  severity: {
    type: 'severity',
    label: 'Severity-based',
    description: 'Basic + differentiate by issue severity',
    complexity: 'medium',
  },
  issue_based: {
    type: 'issue_based',
    label: 'Issue-based',
    description: 'Severity + differentiate by specific issue types',
    complexity: 'medium',
  },
  strict: {
    type: 'strict',
    label: 'Strict',
    description: 'Full fingerprint including all details',
    complexity: 'high',
  },
  custom: {
    type: 'custom',
    label: 'Custom',
    description: 'User-defined fingerprint function',
    complexity: 'high',
  },
}

// =============================================================================
// Window Strategy
// =============================================================================

/**
 * Window strategy types.
 */
export type WindowStrategyType =
  | 'sliding'    // Fixed time window from last notification
  | 'tumbling'   // Non-overlapping fixed buckets
  | 'session'    // Event-based sessions
  | 'adaptive'   // Dynamically adjusts based on frequency

/**
 * Window strategy metadata.
 */
export interface WindowStrategyInfo {
  type: WindowStrategyType
  label: string
  description: string
}

/**
 * Metadata for all window strategies.
 */
export const WINDOW_STRATEGY_INFO: Record<WindowStrategyType, WindowStrategyInfo> = {
  sliding: {
    type: 'sliding',
    label: 'Sliding Window',
    description: 'Suppress duplicates within a fixed time after the first notification',
  },
  tumbling: {
    type: 'tumbling',
    label: 'Tumbling Window',
    description: 'Suppress duplicates within non-overlapping time buckets',
  },
  session: {
    type: 'session',
    label: 'Session Window',
    description: 'New session starts after a gap of no notifications',
  },
  adaptive: {
    type: 'adaptive',
    label: 'Adaptive Window',
    description: 'Dynamically adjust window size based on notification frequency',
  },
}

// =============================================================================
// Notification Fingerprint
// =============================================================================

/**
 * Notification fingerprint for deduplication.
 */
export interface NotificationFingerprint {
  /** Hash key (unique identifier) */
  key: string
  /** Checkpoint name */
  checkpoint_name: string
  /** Action type */
  action_type: string
  /** Components used for fingerprint generation */
  components: Record<string, unknown>
  /** Creation time (ISO string) */
  created_at: string
  /** Additional metadata */
  metadata?: Record<string, unknown>
}

/**
 * Fingerprint generation options.
 */
export interface FingerprintOptions {
  /** Include severity in fingerprint */
  include_severity?: boolean
  /** Include data asset in fingerprint */
  include_data_asset?: boolean
  /** Include issue types in fingerprint */
  include_issue_types?: boolean
  /** Include specific metadata keys */
  include_metadata_keys?: string[]
  /** Custom key override */
  custom_key?: string
  /** Hash algorithm */
  algorithm?: 'sha256' | 'md5' | 'sha1'
}

// =============================================================================
// Deduplication Configuration
// =============================================================================

/**
 * Deduplication configuration.
 */
export interface DeduplicationConfig {
  /** Enable deduplication */
  enabled: boolean
  /** Deduplication policy */
  policy: DeduplicationPolicy
  /** Default time window */
  default_window: TimeWindow
  /** Window strategy */
  window_strategy?: WindowStrategyType
  /** Per-action windows */
  action_windows?: Record<string, TimeWindow>
  /** Per-severity windows */
  severity_windows?: Record<string, TimeWindow>
  /** Fingerprint options */
  fingerprint_options?: FingerprintOptions
  /** Store type */
  store_type?: 'memory' | 'redis' | 'sqlite'
  /** Store configuration */
  store_config?: DeduplicationStoreConfig
  /** Custom fingerprint template (Jinja2) */
  custom_fingerprint_template?: string
}

/**
 * Deduplication store configuration.
 */
export interface DeduplicationStoreConfig {
  /** Maximum record count (for memory store) */
  max_size?: number
  /** Auto cleanup interval (seconds) */
  auto_cleanup_interval?: number
  /** Redis URL (for redis store) */
  redis_url?: string
  /** Stream key prefix (for redis store) */
  stream_key?: string
  /** Max stream length (for redis store) */
  max_stream_length?: number
}

/**
 * Default deduplication configuration.
 */
export const DEFAULT_DEDUPLICATION_CONFIG: DeduplicationConfig = {
  enabled: false,
  policy: 'severity',
  default_window: { value: 5, unit: 'minutes' },
  window_strategy: 'sliding',
  store_type: 'memory',
}

/**
 * Preset configurations for common scenarios.
 */
export const DEDUPLICATION_PRESETS: Record<string, Partial<DeduplicationConfig>> = {
  minimal: {
    enabled: true,
    policy: 'basic',
    default_window: { value: 1, unit: 'minutes' },
  },
  standard: {
    enabled: true,
    policy: 'severity',
    default_window: { value: 5, unit: 'minutes' },
    severity_windows: {
      critical: { value: 1, unit: 'minutes' },
      high: { value: 5, unit: 'minutes' },
      medium: { value: 15, unit: 'minutes' },
      low: { value: 30, unit: 'minutes' },
    },
  },
  aggressive: {
    enabled: true,
    policy: 'issue_based',
    default_window: { value: 15, unit: 'minutes' },
    action_windows: {
      pagerduty: { value: 1, unit: 'hours' },
      slack: { value: 5, unit: 'minutes' },
      email: { value: 1, unit: 'hours' },
    },
    severity_windows: {
      critical: { value: 5, unit: 'minutes' },
      high: { value: 15, unit: 'minutes' },
      medium: { value: 1, unit: 'hours' },
      low: { value: 1, unit: 'hours' },
    },
  },
}

// =============================================================================
// Deduplication Result
// =============================================================================

/**
 * Result of deduplication check.
 */
export interface DeduplicationResult {
  /** Whether notification should be sent */
  should_send: boolean
  /** If suppressed, reason */
  reason?: 'duplicate' | 'within_window' | 'session_active'
  /** The fingerprint used */
  fingerprint: NotificationFingerprint
  /** Previous occurrence (if duplicate) */
  previous_occurrence?: {
    /** When the previous notification was sent */
    sent_at: string
    /** Window expiration time */
    expires_at: string
  }
  /** Time until notification can be sent again (ms) */
  cooldown_remaining_ms?: number
  /** Count of suppressed notifications in current window */
  suppression_count?: number
}

// =============================================================================
// Deduplication Statistics
// =============================================================================

/**
 * Deduplication statistics.
 */
export interface DeduplicationStats {
  /** Total notifications evaluated */
  total_evaluated: number
  /** Notifications sent */
  sent_count: number
  /** Notifications suppressed */
  suppressed_count: number
  /** Suppression ratio (0-1) */
  suppression_ratio: number
  /** Active fingerprints */
  active_fingerprints: number
  /** Stats by action type */
  by_action_type?: Record<string, {
    evaluated: number
    sent: number
    suppressed: number
  }>
  /** Stats by severity */
  by_severity?: Record<string, {
    evaluated: number
    sent: number
    suppressed: number
  }>
  /** Stats by checkpoint */
  by_checkpoint?: Record<string, {
    evaluated: number
    sent: number
    suppressed: number
  }>
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Validate deduplication configuration.
 */
export function validateDeduplicationConfig(config: DeduplicationConfig): string[] {
  const errors: string[] = []

  if (config.default_window.value <= 0) {
    errors.push('Default window value must be greater than 0')
  }

  if (config.policy === 'custom' && !config.custom_fingerprint_template) {
    errors.push('Custom fingerprint template is required for custom policy')
  }

  // Validate action windows
  if (config.action_windows) {
    for (const [action, window] of Object.entries(config.action_windows)) {
      if (window.value <= 0) {
        errors.push(`Window value for action '${action}' must be greater than 0`)
      }
    }
  }

  // Validate severity windows
  if (config.severity_windows) {
    for (const [severity, window] of Object.entries(config.severity_windows)) {
      if (window.value <= 0) {
        errors.push(`Window value for severity '${severity}' must be greater than 0`)
      }
    }
  }

  return errors
}

/**
 * Get effective window for an action and severity.
 */
export function getEffectiveWindow(
  config: DeduplicationConfig,
  actionType: string,
  severity?: string
): TimeWindow {
  // Check action-specific window first
  if (config.action_windows?.[actionType]) {
    return config.action_windows[actionType]
  }

  // Then check severity-specific window
  if (severity && config.severity_windows?.[severity]) {
    return config.severity_windows[severity]
  }

  // Fall back to default
  return config.default_window
}

/**
 * Generate a simple fingerprint key.
 * Note: This is a client-side approximation - actual fingerprinting happens on the server.
 */
export function generateSimpleFingerprint(
  checkpointName: string,
  actionType: string,
  policy: DeduplicationPolicy,
  severity?: string,
  dataAsset?: string
): string {
  const components: string[] = [checkpointName, actionType]

  if (policy === 'severity' || policy === 'issue_based' || policy === 'strict') {
    if (severity) components.push(severity)
  }

  if (policy === 'strict') {
    if (dataAsset) components.push(dataAsset)
  }

  return components.join(':')
}

/**
 * Format suppression count for display.
 */
export function formatSuppressionCount(count: number): string {
  if (count === 0) return 'No suppressions'
  if (count === 1) return '1 suppressed'
  return `${count} suppressed`
}

/**
 * Create deduplication config from preset.
 */
export function createDeduplicationConfigFromPreset(
  preset: keyof typeof DEDUPLICATION_PRESETS
): DeduplicationConfig {
  return {
    ...DEFAULT_DEDUPLICATION_CONFIG,
    ...DEDUPLICATION_PRESETS[preset],
  }
}
