/**
 * Source factory - generates realistic data source mock data
 */

import type { Source } from '@/api/client'
import {
  createId,
  createTimestamp,
  createRecentTimestamp,
  randomChoice,
  faker,
} from './base'

export interface SourceFactoryOptions {
  id?: string
  name?: string
  type?: string
  isActive?: boolean
  hasSchema?: boolean
  validated?: boolean
}

const SOURCE_TYPES = ['csv', 'parquet', 'excel', 'json', 'database'] as const

const SOURCE_CONFIGS: Record<string, () => Record<string, unknown>> = {
  csv: () => ({
    path: faker.system.filePath().replace(/\.[^.]+$/, '.csv'),
    delimiter: ',',
    encoding: 'utf-8',
  }),
  parquet: () => ({
    path: faker.system.filePath().replace(/\.[^.]+$/, '.parquet'),
  }),
  excel: () => ({
    path: faker.system.filePath().replace(/\.[^.]+$/, '.xlsx'),
    sheet: 'Sheet1',
  }),
  json: () => ({
    path: faker.system.filePath().replace(/\.[^.]+$/, '.json'),
  }),
  database: () => ({
    connection_string: 'postgresql://localhost:5432/mydb',
    table: faker.database.column(),
  }),
}

const SOURCE_NAMES = [
  'Sales Transactions',
  'Customer Master Data',
  'Product Inventory',
  'Order History',
  'User Analytics',
  'Financial Reports',
  'Marketing Campaigns',
  'Employee Records',
  'Supplier Data',
  'Shipping Logs',
]

const VALIDATION_STATUSES = ['passed', 'failed', 'warning', null] as const

export function createSource(options: SourceFactoryOptions = {}): Source {
  const type = options.type ?? randomChoice([...SOURCE_TYPES])
  const configGenerator = SOURCE_CONFIGS[type] ?? SOURCE_CONFIGS.csv

  const createdAt = createTimestamp(faker.number.int({ min: 7, max: 90 }))
  const validated = options.validated ?? faker.datatype.boolean(0.7)

  return {
    id: options.id ?? createId(),
    name: options.name ?? randomChoice(SOURCE_NAMES) + ` (${faker.string.alphanumeric(4)})`,
    type,
    config: configGenerator(),
    description: faker.lorem.sentence(),
    is_active: options.isActive ?? faker.datatype.boolean(0.85),
    created_at: createdAt,
    updated_at: createRecentTimestamp(),
    last_validated_at: validated ? createRecentTimestamp() : undefined,
    has_schema: options.hasSchema ?? faker.datatype.boolean(0.6),
    latest_validation_status: validated
      ? randomChoice(VALIDATION_STATUSES.filter((s) => s !== null)) ?? undefined
      : undefined,
  }
}

export function createSources(count: number): Source[] {
  return Array.from({ length: count }, () => createSource())
}
