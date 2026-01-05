/**
 * Validation factory - generates realistic validation results
 */

import type { Validation, ValidationIssue } from '@/api/client'
import {
  createId,
  createTimestamp,
  randomChoice,
  randomInt,
  faker,
} from './base'

export interface ValidationFactoryOptions {
  id?: string
  sourceId?: string
  status?: Validation['status']
  passed?: boolean
}

const ISSUE_TYPES = [
  'null_values',
  'type_mismatch',
  'out_of_range',
  'format_error',
  'duplicate_values',
  'missing_required',
  'constraint_violation',
  'pattern_mismatch',
  'referential_integrity',
  'encoding_error',
]

const COLUMN_NAMES = [
  'id',
  'user_id',
  'email',
  'phone',
  'amount',
  'quantity',
  'price',
  'date',
  'status',
  'category',
  'name',
  'address',
  'created_at',
  'updated_at',
]

const SEVERITIES: ValidationIssue['severity'][] = [
  'critical',
  'high',
  'medium',
  'low',
]

function createIssue(): ValidationIssue {
  const severity = randomChoice(SEVERITIES)
  const issueType = randomChoice(ISSUE_TYPES)

  return {
    column: randomChoice(COLUMN_NAMES),
    issue_type: issueType,
    count: randomInt(1, 500),
    severity,
    details: faker.lorem.sentence(),
    expected: issueType === 'type_mismatch' ? 'integer' : undefined,
    actual: issueType === 'type_mismatch' ? 'string' : undefined,
  }
}

function createIssues(count: number): ValidationIssue[] {
  return Array.from({ length: count }, () => createIssue())
}

export function createValidation(
  options: ValidationFactoryOptions = {}
): Validation {
  const status = options.status ?? randomChoice(['success', 'failed', 'error'])
  const passed = options.passed ?? status === 'success'
  const issueCount = passed ? randomInt(0, 2) : randomInt(3, 15)
  const issues = createIssues(issueCount)

  const criticalIssues = issues.filter((i) => i.severity === 'critical').length
  const highIssues = issues.filter((i) => i.severity === 'high').length
  const mediumIssues = issues.filter((i) => i.severity === 'medium').length
  const lowIssues = issues.filter((i) => i.severity === 'low').length

  const durationMs = randomInt(500, 15000)
  const startedAt = createTimestamp(randomInt(0, 30))
  const completedAt = new Date(
    new Date(startedAt).getTime() + durationMs
  ).toISOString()

  return {
    id: options.id ?? createId(),
    source_id: options.sourceId ?? createId(),
    status,
    passed,
    has_critical: criticalIssues > 0,
    has_high: highIssues > 0,
    total_issues: issues.length,
    critical_issues: criticalIssues,
    high_issues: highIssues,
    medium_issues: mediumIssues,
    low_issues: lowIssues,
    row_count: randomInt(1000, 1000000),
    column_count: randomInt(5, 50),
    issues,
    error_message: status === 'error' ? faker.lorem.sentence() : undefined,
    duration_ms: durationMs,
    started_at: startedAt,
    completed_at: completedAt,
    created_at: startedAt,
  }
}

export function createValidations(
  count: number,
  sourceId?: string
): Validation[] {
  return Array.from({ length: count }, () =>
    createValidation({ sourceId })
  ).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}
