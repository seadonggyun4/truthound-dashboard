/**
 * Notification factory - generates notification channels, rules, and logs
 */

import type {
  NotificationChannel,
  NotificationRule,
  NotificationLog,
  NotificationStats,
} from '@/api/client'
import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

// ============================================================================
// Channels
// ============================================================================

export interface ChannelFactoryOptions {
  id?: string
  type?: NotificationChannel['type']
  isActive?: boolean
}

const CHANNEL_CONFIGS: Record<string, () => { summary: string }> = {
  slack: () => ({
    summary: `Slack: ${faker.helpers.arrayElement(['#alerts', '#data-quality', '#monitoring'])}`,
  }),
  email: () => {
    const emails = Array.from(
      { length: randomInt(1, 3) },
      () => faker.internet.email()
    )
    return {
      summary: `Email: ${emails.slice(0, 2).join(', ')}${emails.length > 2 ? '...' : ''}`,
    }
  },
  webhook: () => ({
    summary: `Webhook: ${faker.internet.domainName()}`,
  }),
}

export function createNotificationChannel(
  options: ChannelFactoryOptions = {}
): NotificationChannel {
  const type = options.type ?? randomChoice(['slack', 'email', 'webhook'] as const)
  const { summary } = CHANNEL_CONFIGS[type]()

  return {
    id: options.id ?? createId(),
    name: `${type.charAt(0).toUpperCase() + type.slice(1)} - ${faker.company.name()}`,
    type,
    is_active: options.isActive ?? faker.datatype.boolean(0.85),
    config_summary: summary,
    created_at: createTimestamp(randomInt(14, 90)),
    updated_at: createTimestamp(randomInt(0, 14)),
  }
}

export function createNotificationChannels(count: number): NotificationChannel[] {
  return Array.from({ length: count }, () => createNotificationChannel())
}

// ============================================================================
// Rules
// ============================================================================

export interface RuleFactoryOptions {
  id?: string
  condition?: string
  channelIds?: string[]
  isActive?: boolean
}

const CONDITIONS = [
  'on_failure',
  'on_critical',
  'on_high',
  'on_drift',
  'on_success',
  'always',
]

const RULE_NAMES = [
  'Critical Alert',
  'Failure Notification',
  'Daily Summary',
  'Drift Detection Alert',
  'Success Confirmation',
  'High Priority Issues',
]

export function createNotificationRule(
  options: RuleFactoryOptions = {}
): NotificationRule {
  const condition = options.condition ?? randomChoice(CONDITIONS)

  return {
    id: options.id ?? createId(),
    name: options.channelIds
      ? randomChoice(RULE_NAMES)
      : `${randomChoice(RULE_NAMES)} (${faker.string.alphanumeric(3)})`,
    condition,
    condition_config:
      condition === 'on_critical'
        ? { min_issues: randomInt(1, 5) }
        : undefined,
    channel_ids: options.channelIds ?? [createId(), createId()],
    source_ids: faker.datatype.boolean(0.3) ? [createId()] : undefined,
    is_active: options.isActive ?? faker.datatype.boolean(0.8),
    created_at: createTimestamp(randomInt(7, 60)),
    updated_at: createTimestamp(randomInt(0, 7)),
  }
}

export function createNotificationRules(count: number): NotificationRule[] {
  return Array.from({ length: count }, () => createNotificationRule())
}

// ============================================================================
// Logs
// ============================================================================

export interface LogFactoryOptions {
  id?: string
  channelId?: string
  status?: NotificationLog['status']
}

const EVENT_TYPES = [
  'validation_failed',
  'validation_success',
  'drift_detected',
  'critical_issue',
  'scheduled_run',
]

export function createNotificationLog(
  options: LogFactoryOptions = {}
): NotificationLog {
  const status = options.status ?? randomChoice(['sent', 'sent', 'sent', 'failed', 'pending'] as const)
  const eventType = randomChoice(EVENT_TYPES)

  const createdAt = createTimestamp(randomInt(0, 7))

  return {
    id: options.id ?? createId(),
    channel_id: options.channelId ?? createId(),
    rule_id: faker.datatype.boolean(0.8) ? createId() : undefined,
    event_type: eventType,
    status,
    message_preview: `[${eventType.replace('_', ' ').toUpperCase()}] ${faker.lorem.sentence()}`,
    error_message: status === 'failed' ? faker.lorem.sentence() : undefined,
    created_at: createdAt,
    sent_at: status === 'sent' ? createdAt : undefined,
  }
}

export function createNotificationLogs(count: number): NotificationLog[] {
  return Array.from({ length: count }, () => createNotificationLog()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}

// ============================================================================
// Stats
// ============================================================================

export function createNotificationStats(hours = 24): NotificationStats {
  const total = randomInt(50, 200)
  const sent = Math.floor(total * 0.85)
  const failed = Math.floor(total * 0.1)
  const pending = total - sent - failed

  return {
    period_hours: hours,
    total,
    by_status: { sent, failed, pending },
    by_channel: {
      slack: randomInt(20, 80),
      email: randomInt(10, 50),
      webhook: randomInt(5, 30),
    },
    success_rate: (sent / total) * 100,
  }
}
