/**
 * Profile factory - generates data profiling results
 */

import type { ProfileResult, ColumnProfile } from '@/api/client'
import { randomInt, faker } from './base'

const COLUMN_SPECS: Array<{
  name: string
  dtype: string
  hasStats: boolean
}> = [
  { name: 'id', dtype: 'int64', hasStats: true },
  { name: 'user_id', dtype: 'int64', hasStats: true },
  { name: 'email', dtype: 'object', hasStats: false },
  { name: 'phone', dtype: 'object', hasStats: false },
  { name: 'name', dtype: 'object', hasStats: false },
  { name: 'amount', dtype: 'float64', hasStats: true },
  { name: 'quantity', dtype: 'int64', hasStats: true },
  { name: 'price', dtype: 'float64', hasStats: true },
  { name: 'status', dtype: 'object', hasStats: false },
  { name: 'category', dtype: 'object', hasStats: false },
  { name: 'date', dtype: 'datetime64[ns]', hasStats: false },
  { name: 'created_at', dtype: 'datetime64[ns]', hasStats: false },
  { name: 'is_active', dtype: 'bool', hasStats: false },
  { name: 'score', dtype: 'float64', hasStats: true },
  { name: 'rating', dtype: 'float64', hasStats: true },
]

function createColumnProfile(spec: (typeof COLUMN_SPECS)[0]): ColumnProfile {
  const nullPct = faker.number.float({ min: 0, max: 15, fractionDigits: 1 })
  const uniquePct = faker.number.float({ min: 20, max: 100, fractionDigits: 1 })

  const profile: ColumnProfile = {
    name: spec.name,
    dtype: spec.dtype,
    null_pct: `${nullPct}%`,
    unique_pct: `${uniquePct}%`,
  }

  if (spec.hasStats) {
    const mean = faker.number.float({ min: 0, max: 10000, fractionDigits: 2 })
    const std = faker.number.float({ min: 0, max: mean * 0.3, fractionDigits: 2 })
    profile.min = mean - std * 2
    profile.max = mean + std * 2
    profile.mean = mean
    profile.std = std
  }

  return profile
}

export function createProfileResult(sourceName?: string): ProfileResult {
  const columnCount = randomInt(6, 12)
  const selectedSpecs = faker.helpers
    .shuffle([...COLUMN_SPECS])
    .slice(0, columnCount)

  return {
    source: sourceName ?? faker.system.fileName(),
    row_count: randomInt(10000, 1000000),
    column_count: columnCount,
    size_bytes: randomInt(1000000, 100000000),
    columns: selectedSpecs.map(createColumnProfile),
  }
}
