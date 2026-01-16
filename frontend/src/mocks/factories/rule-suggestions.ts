/**
 * Rule Suggestions factory - generates suggested validation rules based on profile data
 */

import { createId, randomChoice, randomInt, faker } from './base'

// Types matching backend schemas
export interface SuggestedRule {
  id: string
  validator_name: string
  column_name: string | null
  confidence: number
  reason: string
  parameters: Record<string, unknown>
  priority: number
  category: string
}

export interface RuleSuggestionResponse {
  source_id: string
  source_name: string
  profile_id: string
  total_suggestions: number
  high_confidence_count: number
  suggestions: SuggestedRule[]
  generated_at: string
}

export interface ApplyRulesResponse {
  source_id: string
  applied_count: number
  applied_rules: Array<{
    validator_name: string
    column_name: string | null
    parameters: Record<string, unknown>
  }>
}

// Validator templates for rule generation
const VALIDATOR_TEMPLATES = [
  // Null rules
  {
    validator: 'NotNull',
    category: 'completeness',
    reasonTemplate: 'Column has 0% null values',
    priority: 1,
    confidenceRange: [85, 98],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'Null',
    category: 'completeness',
    reasonTemplate: 'Column has less than 1% null values',
    priority: 2,
    confidenceRange: [75, 90],
    requiresColumn: true,
    params: () => ({ mostly: faker.number.float({ min: 0.95, max: 0.99, fractionDigits: 2 }) }),
  },
  // Uniqueness rules
  {
    validator: 'Unique',
    category: 'uniqueness',
    reasonTemplate: 'Column has 100% unique values',
    priority: 1,
    confidenceRange: [90, 99],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'DistinctSet',
    category: 'uniqueness',
    reasonTemplate: 'Column has low cardinality with limited distinct values',
    priority: 2,
    confidenceRange: [70, 85],
    requiresColumn: true,
    params: () => ({
      values: faker.helpers.shuffle(['active', 'inactive', 'pending', 'completed', 'cancelled']).slice(0, randomInt(2, 5)),
    }),
  },
  // Range rules
  {
    validator: 'Range',
    category: 'distribution',
    reasonTemplate: 'Column values fall within a defined numeric range',
    priority: 2,
    confidenceRange: [75, 92],
    requiresColumn: true,
    params: () => {
      const min = faker.number.int({ min: 0, max: 100 })
      const max = faker.number.int({ min: min + 10, max: min + 1000 })
      return { min, max }
    },
  },
  {
    validator: 'Positive',
    category: 'distribution',
    reasonTemplate: 'Column contains only positive values',
    priority: 2,
    confidenceRange: [80, 95],
    requiresColumn: true,
    params: () => ({}),
  },
  // Type-specific rules
  {
    validator: 'Email',
    category: 'string',
    reasonTemplate: 'Column name suggests email format',
    priority: 1,
    confidenceRange: [85, 98],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'Phone',
    category: 'string',
    reasonTemplate: 'Column name suggests phone number format',
    priority: 2,
    confidenceRange: [70, 88],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'URL',
    category: 'string',
    reasonTemplate: 'Column name suggests URL format',
    priority: 2,
    confidenceRange: [75, 90],
    requiresColumn: true,
    params: () => ({}),
  },
  // String length rules
  {
    validator: 'StrLen',
    category: 'string',
    reasonTemplate: 'Column values have consistent string length range',
    priority: 3,
    confidenceRange: [65, 80],
    requiresColumn: true,
    params: () => ({
      min_length: faker.number.int({ min: 1, max: 5 }),
      max_length: faker.number.int({ min: 50, max: 255 }),
    }),
  },
  // Datetime rules
  {
    validator: 'DatetimeRange',
    category: 'datetime',
    reasonTemplate: 'Column contains datetime values within expected range',
    priority: 2,
    confidenceRange: [70, 85],
    requiresColumn: true,
    params: () => ({
      min_date: '2020-01-01',
      max_date: new Date().toISOString().split('T')[0],
    }),
  },
]

// Column names to assign validators to
const COLUMN_NAMES = [
  'user_id',
  'email',
  'name',
  'phone',
  'amount',
  'price',
  'status',
  'category',
  'created_at',
  'updated_at',
  'is_active',
  'description',
  'url',
  'address',
  'quantity',
]

export function createSuggestedRule(options: {
  columnName?: string
  validator?: string
} = {}): SuggestedRule {
  const template = options.validator
    ? VALIDATOR_TEMPLATES.find((t) => t.validator === options.validator) || randomChoice(VALIDATOR_TEMPLATES)
    : randomChoice(VALIDATOR_TEMPLATES)

  const columnName = options.columnName || randomChoice(COLUMN_NAMES)
  const [minConf, maxConf] = template.confidenceRange

  return {
    id: createId(),
    validator_name: template.validator,
    column_name: template.requiresColumn ? columnName : null,
    confidence: faker.number.float({ min: minConf, max: maxConf, fractionDigits: 0 }),
    reason: template.reasonTemplate.replace('{column}', columnName),
    parameters: template.params(),
    priority: template.priority,
    category: template.category,
  }
}

export function createRuleSuggestionResponse(
  sourceId: string,
  sourceName: string,
  options: {
    suggestionCount?: number
    profileId?: string
  } = {}
): RuleSuggestionResponse {
  const suggestionCount = options.suggestionCount ?? randomInt(5, 15)
  const profileId = options.profileId ?? createId()

  // Generate diverse suggestions
  const usedValidators = new Set<string>()
  const usedColumns = new Set<string>()
  const suggestions: SuggestedRule[] = []

  // Ensure variety by using different validators and columns
  const availableColumns = faker.helpers.shuffle([...COLUMN_NAMES])

  for (let i = 0; i < suggestionCount; i++) {
    // Pick a column, avoiding duplicates where possible
    const columnName = availableColumns[i % availableColumns.length]

    // Pick a validator that hasn't been used with this column
    const availableTemplates = VALIDATOR_TEMPLATES.filter(
      (t) => !usedValidators.has(`${t.validator}:${columnName}`)
    )

    if (availableTemplates.length > 0) {
      const template = randomChoice(availableTemplates)
      const suggestion = createSuggestedRule({
        columnName,
        validator: template.validator,
      })
      suggestions.push(suggestion)
      usedValidators.add(`${template.validator}:${columnName}`)
      usedColumns.add(columnName)
    }
  }

  // Sort by priority and confidence
  suggestions.sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority
    return b.confidence - a.confidence
  })

  const highConfidenceCount = suggestions.filter((s) => s.confidence >= 80).length

  return {
    source_id: sourceId,
    source_name: sourceName,
    profile_id: profileId,
    total_suggestions: suggestions.length,
    high_confidence_count: highConfidenceCount,
    suggestions,
    generated_at: new Date().toISOString(),
  }
}

export function createApplyRulesResponse(
  sourceId: string,
  selectedRules: SuggestedRule[]
): ApplyRulesResponse {
  return {
    source_id: sourceId,
    applied_count: selectedRules.length,
    applied_rules: selectedRules.map((rule) => ({
      validator_name: rule.validator_name,
      column_name: rule.column_name,
      parameters: rule.parameters,
    })),
  }
}

/**
 * Create mock profile-based rule suggestions for specific column types
 */
export function createContextualSuggestions(columns: Array<{ name: string; dtype: string }>): SuggestedRule[] {
  const suggestions: SuggestedRule[] = []

  for (const col of columns) {
    // Type-based suggestions
    if (col.dtype.includes('int') || col.dtype.includes('float')) {
      suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Range' }))
      if (col.name.includes('id')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Unique' }))
      }
    }

    if (col.dtype === 'object') {
      if (col.name.toLowerCase().includes('email')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Email' }))
      }
      if (col.name.toLowerCase().includes('phone')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Phone' }))
      }
      if (col.name.toLowerCase().includes('url') || col.name.toLowerCase().includes('website')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'URL' }))
      }
      if (col.name.toLowerCase().includes('status') || col.name.toLowerCase().includes('category')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'DistinctSet' }))
      }
    }

    if (col.dtype.includes('datetime')) {
      suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'DatetimeRange' }))
    }

    // Add NotNull for most columns
    if (faker.datatype.boolean({ probability: 0.6 })) {
      suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'NotNull' }))
    }
  }

  return suggestions
}
