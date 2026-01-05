/**
 * Schedule factory - generates scheduled job mock data
 */

import type { Schedule } from '@/api/client'
import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

export interface ScheduleFactoryOptions {
  id?: string
  sourceId?: string
  isActive?: boolean
}

const CRON_EXPRESSIONS = [
  { expr: '0 0 * * *', desc: 'Daily at midnight' },
  { expr: '0 6 * * *', desc: 'Daily at 6 AM' },
  { expr: '0 */4 * * *', desc: 'Every 4 hours' },
  { expr: '0 0 * * 1', desc: 'Weekly on Monday' },
  { expr: '0 0 1 * *', desc: 'Monthly on 1st' },
  { expr: '*/30 * * * *', desc: 'Every 30 minutes' },
  { expr: '0 9,18 * * 1-5', desc: 'Weekdays at 9 AM and 6 PM' },
]

const SCHEDULE_NAMES = [
  'Daily Quality Check',
  'Hourly Validation',
  'Weekly Data Audit',
  'Real-time Monitor',
  'Nightly Scan',
  'Business Hours Check',
  'End-of-Day Validation',
]

function calculateNextRun(): string {
  // Simplified: just return a time in the near future
  const next = new Date()
  next.setHours(next.getHours() + randomInt(1, 24))
  return next.toISOString()
}

export function createSchedule(options: ScheduleFactoryOptions = {}): Schedule {
  const cron = randomChoice(CRON_EXPRESSIONS)
  const isActive = options.isActive ?? faker.datatype.boolean(0.8)
  const hasRun = faker.datatype.boolean(0.7)

  return {
    id: options.id ?? createId(),
    name: randomChoice(SCHEDULE_NAMES) + ` (${faker.string.alphanumeric(3)})`,
    source_id: options.sourceId ?? createId(),
    cron_expression: cron.expr,
    is_active: isActive,
    notify_on_failure: faker.datatype.boolean(0.6),
    last_run_at: hasRun ? createTimestamp(randomInt(0, 7)) : undefined,
    next_run_at: isActive ? calculateNextRun() : undefined,
    config: {
      validators: ['schema', 'null_check', 'type_check'],
      auto_schema: true,
    },
    created_at: createTimestamp(randomInt(14, 60)),
    updated_at: createTimestamp(randomInt(0, 14)),
    source_name: faker.commerce.productName() + ' Data',
  }
}

export function createSchedules(count: number): Schedule[] {
  return Array.from({ length: count }, () => createSchedule())
}
