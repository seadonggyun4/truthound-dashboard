/**
 * Escalation types for multi-level notification policies.
 *
 * The escalation system manages notification lifecycle with scheduled
 * escalation to higher-level responders when issues are not acknowledged.
 *
 * Features:
 * - Multi-level escalation chains
 * - State machine for escalation lifecycle
 * - APScheduler-based scheduling
 * - Acknowledgement and resolution tracking
 * - Business hours support
 * - Multiple target types (user, team, channel, schedule)
 */

// =============================================================================
// Escalation State
// =============================================================================

/**
 * Escalation states.
 */
export type EscalationState =
  | 'pending'       // Initial state, waiting to start
  | 'active'        // Currently notifying at level
  | 'escalating'    // Escalating to next level
  | 'acknowledged'  // Responder acknowledged
  | 'resolved'      // Issue resolved
  | 'cancelled'     // Manually cancelled
  | 'timed_out'     // Max escalation reached or timed out
  | 'failed'        // System error during escalation

/**
 * State metadata.
 */
export interface EscalationStateInfo {
  state: EscalationState
  label: string
  description: string
  isTerminal: boolean
  color: string
}

/**
 * Metadata for all states.
 */
export const ESCALATION_STATE_INFO: Record<EscalationState, EscalationStateInfo> = {
  pending: {
    state: 'pending',
    label: 'Pending',
    description: 'Waiting to start escalation',
    isTerminal: false,
    color: 'gray',
  },
  active: {
    state: 'active',
    label: 'Active',
    description: 'Currently notifying responders',
    isTerminal: false,
    color: 'blue',
  },
  escalating: {
    state: 'escalating',
    label: 'Escalating',
    description: 'Moving to next level',
    isTerminal: false,
    color: 'yellow',
  },
  acknowledged: {
    state: 'acknowledged',
    label: 'Acknowledged',
    description: 'Responder has acknowledged',
    isTerminal: false,
    color: 'green',
  },
  resolved: {
    state: 'resolved',
    label: 'Resolved',
    description: 'Issue has been resolved',
    isTerminal: true,
    color: 'green',
  },
  cancelled: {
    state: 'cancelled',
    label: 'Cancelled',
    description: 'Escalation was cancelled',
    isTerminal: true,
    color: 'gray',
  },
  timed_out: {
    state: 'timed_out',
    label: 'Timed Out',
    description: 'Maximum escalation reached',
    isTerminal: true,
    color: 'red',
  },
  failed: {
    state: 'failed',
    label: 'Failed',
    description: 'System error occurred',
    isTerminal: true,
    color: 'red',
  },
}

// =============================================================================
// Target Types
// =============================================================================

/**
 * Escalation target types.
 */
export type TargetType =
  | 'user'       // Individual user
  | 'team'       // Team
  | 'channel'    // Channel (Slack, etc.)
  | 'schedule'   // On-call schedule
  | 'webhook'    // Webhook URL
  | 'email'      // Email address
  | 'phone'      // Phone number
  | 'custom'     // Custom target

/**
 * Target type metadata.
 */
export interface TargetTypeInfo {
  type: TargetType
  label: string
  description: string
  icon?: string
}

/**
 * Metadata for all target types.
 */
export const TARGET_TYPE_INFO: Record<TargetType, TargetTypeInfo> = {
  user: { type: 'user', label: 'User', description: 'Individual user', icon: 'user' },
  team: { type: 'team', label: 'Team', description: 'Team group', icon: 'users' },
  channel: { type: 'channel', label: 'Channel', description: 'Slack/Teams channel', icon: 'hash' },
  schedule: { type: 'schedule', label: 'On-Call Schedule', description: 'On-call rotation', icon: 'calendar' },
  webhook: { type: 'webhook', label: 'Webhook', description: 'Webhook URL', icon: 'globe' },
  email: { type: 'email', label: 'Email', description: 'Email address', icon: 'mail' },
  phone: { type: 'phone', label: 'Phone', description: 'Phone number', icon: 'phone' },
  custom: { type: 'custom', label: 'Custom', description: 'Custom target', icon: 'settings' },
}

// =============================================================================
// Escalation Trigger
// =============================================================================

/**
 * Escalation trigger conditions.
 */
export type EscalationTrigger =
  | 'unacknowledged'      // Not acknowledged within time
  | 'unresolved'          // Not resolved within time
  | 'severity_upgrade'    // Issue severity increased
  | 'repeated_failure'    // Multiple consecutive failures
  | 'threshold_breach'    // Metric threshold exceeded
  | 'manual'              // Manual escalation
  | 'scheduled'           // Time-based scheduled escalation
  | 'custom'              // Custom trigger condition

/**
 * Trigger metadata.
 */
export const ESCALATION_TRIGGER_INFO: Record<EscalationTrigger, { label: string; description: string }> = {
  unacknowledged: {
    label: 'Unacknowledged',
    description: 'Escalate when not acknowledged within time limit',
  },
  unresolved: {
    label: 'Unresolved',
    description: 'Escalate when not resolved within time limit',
  },
  severity_upgrade: {
    label: 'Severity Upgrade',
    description: 'Escalate when issue severity increases',
  },
  repeated_failure: {
    label: 'Repeated Failure',
    description: 'Escalate after multiple consecutive failures',
  },
  threshold_breach: {
    label: 'Threshold Breach',
    description: 'Escalate when a metric exceeds threshold',
  },
  manual: {
    label: 'Manual',
    description: 'Manual escalation by user',
  },
  scheduled: {
    label: 'Scheduled',
    description: 'Time-based scheduled escalation',
  },
  custom: {
    label: 'Custom',
    description: 'Custom trigger condition',
  },
}

// =============================================================================
// Escalation Target
// =============================================================================

/**
 * Escalation target definition.
 */
export interface EscalationTarget {
  /** Target type */
  type: TargetType
  /** Target identifier */
  identifier: string
  /** Display name */
  name?: string
  /** Priority (lower = higher priority) */
  priority?: number
  /** Additional metadata */
  metadata?: Record<string, unknown>
}

// =============================================================================
// Escalation Level
// =============================================================================

/**
 * Escalation level definition.
 */
export interface EscalationLevel {
  /** Level number (1 = first) */
  level: number
  /** Delay time in minutes (0 = immediate) */
  delay_minutes: number
  /** Notification targets */
  targets: EscalationTarget[]
  /** Repeat count (0 = once only) */
  repeat_count?: number
  /** Repeat interval in minutes */
  repeat_interval_minutes?: number
  /** Require acknowledgement to stop repeating */
  require_ack?: boolean
  /** Auto resolve time in minutes (0 = none) */
  auto_resolve_minutes?: number
  /** Additional conditions for this level */
  conditions?: Record<string, unknown>
  /** Description */
  description?: string
}

// =============================================================================
// Escalation Policy
// =============================================================================

/**
 * Escalation policy definition.
 */
export interface EscalationPolicy {
  /** Unique identifier */
  id?: string
  /** Policy name */
  name: string
  /** Description */
  description?: string
  /** Escalation levels */
  levels: EscalationLevel[]
  /** Whether policy is enabled */
  enabled?: boolean
  /** Trigger conditions */
  triggers?: EscalationTrigger[]
  /** Severity filter (only apply to these severities) */
  severity_filter?: string[]
  /** Maximum escalation count */
  max_escalations?: number
  /** Cooldown time for same incident (minutes) */
  cooldown_minutes?: number
  /** Business hours only */
  business_hours_only?: boolean
  /** Business hours start (0-23) */
  business_hours_start?: number
  /** Business hours end (0-23) */
  business_hours_end?: number
  /** Business days (0=Monday, 6=Sunday) */
  business_days?: number[]
  /** Timezone */
  timezone?: string
  /** Tags */
  tags?: Record<string, string>
  /** Metadata */
  metadata?: Record<string, unknown>
  /** Creation time */
  created_at?: string
  /** Update time */
  updated_at?: string
}

/**
 * Default escalation policy.
 */
export const DEFAULT_ESCALATION_POLICY: Partial<EscalationPolicy> = {
  enabled: true,
  triggers: ['unacknowledged'],
  max_escalations: 5,
  cooldown_minutes: 60,
  business_hours_only: false,
  timezone: 'UTC',
}

// =============================================================================
// Escalation Record
// =============================================================================

/**
 * Escalation record - tracks escalation progress.
 */
export interface EscalationRecord {
  /** Record ID */
  id: string
  /** External incident ID */
  incident_id: string
  /** Policy name */
  policy_name: string
  /** Current level */
  current_level: number
  /** Current state */
  state: EscalationState
  /** Creation time (ISO string) */
  created_at: string
  /** Update time (ISO string) */
  updated_at: string
  /** Acknowledgement time (ISO string) */
  acknowledged_at?: string
  /** Acknowledger */
  acknowledged_by?: string
  /** Resolution time (ISO string) */
  resolved_at?: string
  /** Resolver */
  resolved_by?: string
  /** Next escalation time (ISO string) */
  next_escalation_at?: string
  /** Escalation count */
  escalation_count: number
  /** Notification count */
  notification_count: number
  /** Event history */
  history: EscalationEvent[]
  /** Trigger context */
  context: Record<string, unknown>
  /** Metadata */
  metadata?: Record<string, unknown>
}

/**
 * Escalation event.
 */
export interface EscalationEvent {
  /** Event type */
  type: 'created' | 'escalated' | 'notified' | 'acknowledged' | 'resolved' | 'cancelled' | 'error'
  /** Event time (ISO string) */
  timestamp: string
  /** Event level */
  level?: number
  /** Actor (user who performed action) */
  actor?: string
  /** Message */
  message?: string
  /** Additional details */
  details?: Record<string, unknown>
}

// =============================================================================
// Escalation Statistics
// =============================================================================

/**
 * Escalation statistics.
 */
export interface EscalationStats {
  /** Total escalations */
  total_escalations: number
  /** Active escalations */
  active_escalations: number
  /** Acknowledged count */
  acknowledged_count: number
  /** Resolved count */
  resolved_count: number
  /** Timed out count */
  timed_out_count: number
  /** Acknowledgement rate (0-1) */
  acknowledgment_rate: number
  /** Resolution rate (0-1) */
  resolution_rate: number
  /** Average time to acknowledge (seconds) */
  avg_time_to_acknowledge_seconds: number
  /** Average time to resolve (seconds) */
  avg_time_to_resolve_seconds: number
  /** Notifications sent */
  notifications_sent: number
  /** Stats by policy */
  by_policy?: Record<string, {
    total: number
    active: number
    acknowledged: number
    resolved: number
  }>
  /** Stats by level */
  by_level?: Record<number, {
    reached: number
    acknowledged_at: number
    resolved_at: number
  }>
}

// =============================================================================
// API Types
// =============================================================================

/**
 * Request to create an escalation policy.
 */
export interface CreateEscalationPolicyRequest {
  name: string
  description?: string
  levels: EscalationLevel[]
  enabled?: boolean
  triggers?: EscalationTrigger[]
  severity_filter?: string[]
  max_escalations?: number
  cooldown_minutes?: number
  business_hours_only?: boolean
  business_hours_start?: number
  business_hours_end?: number
  business_days?: number[]
  timezone?: string
}

/**
 * Request to trigger an escalation.
 */
export interface TriggerEscalationRequest {
  /** Incident ID */
  incident_id: string
  /** Policy name */
  policy_name: string
  /** Context */
  context: Record<string, unknown>
}

/**
 * Request to acknowledge an escalation.
 */
export interface AcknowledgeEscalationRequest {
  /** Record ID */
  record_id: string
  /** Acknowledger */
  acknowledged_by: string
  /** Optional message */
  message?: string
}

/**
 * Request to resolve an escalation.
 */
export interface ResolveEscalationRequest {
  /** Record ID */
  record_id: string
  /** Resolver */
  resolved_by: string
  /** Resolution message */
  message?: string
  /** Resolution details */
  details?: Record<string, unknown>
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Check if an escalation state is terminal.
 */
export function isEscalationTerminal(state: EscalationState): boolean {
  return ESCALATION_STATE_INFO[state].isTerminal
}

/**
 * Check if an escalation is active.
 */
export function isEscalationActive(state: EscalationState): boolean {
  return state === 'active' || state === 'escalating' || state === 'pending'
}

/**
 * Get max level number from policy.
 */
export function getMaxLevel(policy: EscalationPolicy): number {
  return Math.max(...policy.levels.map(l => l.level))
}

/**
 * Get level by number.
 */
export function getLevel(policy: EscalationPolicy, levelNumber: number): EscalationLevel | undefined {
  return policy.levels.find(l => l.level === levelNumber)
}

/**
 * Get next level.
 */
export function getNextLevel(policy: EscalationPolicy, currentLevel: number): EscalationLevel | undefined {
  return policy.levels.find(l => l.level > currentLevel)
}

/**
 * Calculate total escalation time (minutes).
 */
export function calculateTotalEscalationTime(policy: EscalationPolicy): number {
  return policy.levels.reduce((total, level) => {
    const repeatTime = (level.repeat_count || 0) * (level.repeat_interval_minutes || 0)
    return total + level.delay_minutes + repeatTime
  }, 0)
}

/**
 * Format duration for display.
 */
export function formatEscalationDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ${minutes % 60}m`
  return `${Math.floor(minutes / 1440)}d ${Math.floor((minutes % 1440) / 60)}h`
}

/**
 * Validate escalation policy.
 */
export function validateEscalationPolicy(policy: EscalationPolicy): string[] {
  const errors: string[] = []

  if (!policy.name?.trim()) {
    errors.push('Policy name is required')
  }

  if (!policy.levels || policy.levels.length === 0) {
    errors.push('At least one escalation level is required')
  }

  policy.levels.forEach((level, index) => {
    if (!level.targets || level.targets.length === 0) {
      errors.push(`Level ${index + 1} must have at least one target`)
    }

    if (level.delay_minutes < 0) {
      errors.push(`Level ${index + 1} delay cannot be negative`)
    }

    if (level.repeat_count && level.repeat_count > 0 && !level.repeat_interval_minutes) {
      errors.push(`Level ${index + 1} repeat interval is required when repeat count is set`)
    }
  })

  // Check for duplicate levels
  const levelNumbers = policy.levels.map(l => l.level)
  const uniqueLevels = new Set(levelNumbers)
  if (uniqueLevels.size !== levelNumbers.length) {
    errors.push('Duplicate level numbers are not allowed')
  }

  // Check business hours configuration
  if (policy.business_hours_only) {
    if (policy.business_hours_start === undefined || policy.business_hours_end === undefined) {
      errors.push('Business hours start and end must be specified when business_hours_only is enabled')
    }
    if (policy.business_hours_start !== undefined && (policy.business_hours_start < 0 || policy.business_hours_start > 23)) {
      errors.push('Business hours start must be between 0 and 23')
    }
    if (policy.business_hours_end !== undefined && (policy.business_hours_end < 0 || policy.business_hours_end > 23)) {
      errors.push('Business hours end must be between 0 and 23')
    }
  }

  return errors
}

/**
 * Create a default escalation level.
 */
export function createDefaultEscalationLevel(levelNumber: number): EscalationLevel {
  return {
    level: levelNumber,
    delay_minutes: levelNumber === 1 ? 0 : 15 * levelNumber,
    targets: [],
    repeat_count: 0,
    repeat_interval_minutes: 5,
    require_ack: true,
    auto_resolve_minutes: 0,
  }
}

/**
 * Create a target from a simple identifier.
 */
export function createTarget(type: TargetType, identifier: string, name?: string): EscalationTarget {
  return {
    type,
    identifier,
    name: name || identifier,
  }
}
