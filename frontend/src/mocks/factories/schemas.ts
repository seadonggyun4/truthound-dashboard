/**
 * Schema factory - generates realistic schema definitions
 */

import type { Schema } from '@/api/client'
import { createId, createTimestamp, randomInt, faker } from './base'

export interface SchemaFactoryOptions {
  id?: string
  sourceId?: string
  columns?: string[]
}

const COLUMN_DEFINITIONS = [
  { name: 'id', dtype: 'integer', constraints: ['not_null', 'unique'] },
  { name: 'user_id', dtype: 'integer', constraints: ['not_null'] },
  { name: 'email', dtype: 'string', constraints: ['not_null', 'email_format'] },
  { name: 'phone', dtype: 'string', constraints: ['phone_format'] },
  { name: 'name', dtype: 'string', constraints: ['not_null', 'min_length:2'] },
  { name: 'amount', dtype: 'float', constraints: ['min:0'] },
  { name: 'quantity', dtype: 'integer', constraints: ['min:0', 'max:10000'] },
  { name: 'price', dtype: 'float', constraints: ['min:0'] },
  { name: 'status', dtype: 'string', constraints: ['enum:active,inactive,pending'] },
  { name: 'category', dtype: 'string', constraints: [] },
  { name: 'date', dtype: 'date', constraints: ['date_format:YYYY-MM-DD'] },
  { name: 'created_at', dtype: 'datetime', constraints: ['not_null'] },
  { name: 'updated_at', dtype: 'datetime', constraints: [] },
  { name: 'is_active', dtype: 'boolean', constraints: [] },
  { name: 'description', dtype: 'string', constraints: ['max_length:500'] },
]

function generateSchemaYaml(columns: typeof COLUMN_DEFINITIONS): string {
  const lines = ['schema:', '  version: "1.0"', '  columns:']

  columns.forEach((col) => {
    lines.push(`    ${col.name}:`)
    lines.push(`      dtype: ${col.dtype}`)
    if (col.constraints.length > 0) {
      lines.push('      constraints:')
      col.constraints.forEach((c) => lines.push(`        - ${c}`))
    }
  })

  return lines.join('\n')
}

export function createSchema(options: SchemaFactoryOptions = {}): Schema {
  const columnCount = randomInt(5, 12)
  const selectedColumns = faker.helpers
    .shuffle([...COLUMN_DEFINITIONS])
    .slice(0, columnCount)
  const columns = options.columns ?? selectedColumns.map((c) => c.name)

  const createdAt = createTimestamp(randomInt(7, 60))

  return {
    id: options.id ?? createId(),
    source_id: options.sourceId ?? createId(),
    schema_yaml: generateSchemaYaml(selectedColumns),
    schema_json: {
      version: '1.0',
      columns: selectedColumns.reduce(
        (acc, col) => {
          acc[col.name] = { dtype: col.dtype, constraints: col.constraints }
          return acc
        },
        {} as Record<string, unknown>
      ),
    },
    row_count: randomInt(1000, 500000),
    column_count: columns.length,
    columns,
    version: '1.0',
    is_active: true,
    created_at: createdAt,
    updated_at: createdAt,
  }
}
