/**
 * Drift detection factory - generates drift comparison results
 */

import type { DriftComparison, ColumnDriftResult, DriftResult } from '@/api/client'
import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

export interface DriftFactoryOptions {
  id?: string
  baselineSourceId?: string
  currentSourceId?: string
  hasDrift?: boolean
}

const DRIFT_METHODS = ['ks', 'psi', 'chi2', 'js'] as const
const DTYPES = ['int64', 'float64', 'object', 'datetime64', 'bool'] as const

const COLUMN_NAMES = [
  'revenue',
  'user_count',
  'transaction_amount',
  'conversion_rate',
  'avg_order_value',
  'churn_rate',
  'lifetime_value',
  'engagement_score',
  'satisfaction_index',
  'response_time',
]

function createColumnDriftResult(drifted: boolean): ColumnDriftResult {
  const method = randomChoice([...DRIFT_METHODS])
  const level = drifted
    ? randomChoice(['medium', 'high'] as const)
    : randomChoice(['none', 'low'] as const)

  return {
    column: randomChoice(COLUMN_NAMES),
    dtype: randomChoice([...DTYPES]),
    drifted,
    level,
    method,
    statistic: faker.number.float({ min: 0, max: 1, fractionDigits: 4 }),
    p_value: faker.number.float({ min: 0, max: 1, fractionDigits: 4 }),
    baseline_stats: {
      mean: faker.number.float({ min: 0, max: 1000, fractionDigits: 2 }),
      std: faker.number.float({ min: 0, max: 100, fractionDigits: 2 }),
      min: faker.number.float({ min: 0, max: 100, fractionDigits: 2 }),
      max: faker.number.float({ min: 500, max: 2000, fractionDigits: 2 }),
    },
    current_stats: {
      mean: faker.number.float({ min: 0, max: 1000, fractionDigits: 2 }),
      std: faker.number.float({ min: 0, max: 100, fractionDigits: 2 }),
      min: faker.number.float({ min: 0, max: 100, fractionDigits: 2 }),
      max: faker.number.float({ min: 500, max: 2000, fractionDigits: 2 }),
    },
  }
}

export function createDriftResult(
  baselineSourceId: string,
  currentSourceId: string,
  hasDrift: boolean
): DriftResult {
  const totalColumns = randomInt(5, 15)
  const driftedCount = hasDrift ? randomInt(1, Math.floor(totalColumns / 2)) : 0

  const columns: ColumnDriftResult[] = []
  for (let i = 0; i < totalColumns; i++) {
    columns.push(createColumnDriftResult(i < driftedCount))
  }

  return {
    baseline_source: baselineSourceId,
    current_source: currentSourceId,
    baseline_rows: randomInt(10000, 100000),
    current_rows: randomInt(10000, 100000),
    has_drift: hasDrift,
    has_high_drift: hasDrift && columns.some((c) => c.level === 'high'),
    total_columns: totalColumns,
    drifted_columns: columns.filter((c) => c.drifted).map((c) => c.column),
    columns,
  }
}

export function createDriftComparison(
  options: DriftFactoryOptions = {}
): DriftComparison {
  const baselineSourceId = options.baselineSourceId ?? createId()
  const currentSourceId = options.currentSourceId ?? createId()
  const hasDrift = options.hasDrift ?? faker.datatype.boolean(0.4)

  const result = createDriftResult(baselineSourceId, currentSourceId, hasDrift)

  return {
    id: options.id ?? createId(),
    baseline_source_id: baselineSourceId,
    current_source_id: currentSourceId,
    has_drift: result.has_drift,
    has_high_drift: result.has_high_drift,
    total_columns: result.total_columns,
    drifted_columns: result.drifted_columns.length,
    drift_percentage:
      (result.drifted_columns.length / result.total_columns) * 100,
    result,
    config: {
      method: 'auto',
      threshold: 0.05,
    },
    created_at: createTimestamp(randomInt(0, 14)),
    updated_at: createTimestamp(randomInt(0, 7)),
  }
}

export function createDriftComparisons(count: number): DriftComparison[] {
  return Array.from({ length: count }, () => createDriftComparison())
}
