/**
 * RuleBuilder - Visual rule composition for notification routing.
 *
 * Provides a guided interface for building routing rules with:
 * - Rule type selection with descriptions
 * - Type-specific parameter inputs
 * - Combinator support (all_of, any_of, not)
 * - Real-time validation
 */

import { useState, useCallback } from 'react'
import { Plus, Trash2, AlertTriangle, CheckCircle2, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

export type RuleType =
  | 'severity'
  | 'issue_count'
  | 'pass_rate'
  | 'time_window'
  | 'tag'
  | 'data_asset'
  | 'metadata'
  | 'status'
  | 'error'
  | 'always'
  | 'never'
  | 'all_of'
  | 'any_of'
  | 'not'

export interface RuleConfig {
  type: RuleType
  params?: Record<string, unknown>
  rules?: RuleConfig[] // For combinators
}

interface RuleBuilderProps {
  value: RuleConfig
  onChange: (config: RuleConfig) => void
  depth?: number
  maxDepth?: number
}

const RULE_TYPE_INFO: Record<
  RuleType,
  {
    label: string
    description: string
    category: 'basic' | 'condition' | 'combinator' | 'static'
    params?: Array<{
      name: string
      type: 'string' | 'number' | 'select' | 'array'
      label: string
      options?: string[]
      min?: number
      max?: number
      placeholder?: string
    }>
  }
> = {
  severity: {
    label: 'Severity',
    description: 'Match notifications by severity level',
    category: 'basic',
    params: [
      {
        name: 'min_severity',
        type: 'select',
        label: 'Minimum Severity',
        options: ['info', 'low', 'medium', 'high', 'critical'],
      },
    ],
  },
  issue_count: {
    label: 'Issue Count',
    description: 'Match when issue count exceeds threshold',
    category: 'condition',
    params: [
      {
        name: 'min_count',
        type: 'number',
        label: 'Minimum Count',
        min: 1,
        placeholder: '10',
      },
    ],
  },
  pass_rate: {
    label: 'Pass Rate',
    description: 'Match when pass rate is below threshold',
    category: 'condition',
    params: [
      {
        name: 'max_rate',
        type: 'number',
        label: 'Maximum Pass Rate (%)',
        min: 0,
        max: 100,
        placeholder: '80',
      },
    ],
  },
  time_window: {
    label: 'Time Window',
    description: 'Match during specific hours (UTC)',
    category: 'condition',
    params: [
      {
        name: 'start_hour',
        type: 'number',
        label: 'Start Hour',
        min: 0,
        max: 23,
        placeholder: '9',
      },
      {
        name: 'end_hour',
        type: 'number',
        label: 'End Hour',
        min: 0,
        max: 23,
        placeholder: '17',
      },
    ],
  },
  tag: {
    label: 'Tag',
    description: 'Match by notification tags',
    category: 'basic',
    params: [
      {
        name: 'tags',
        type: 'string',
        label: 'Tags (comma-separated)',
        placeholder: 'production, critical',
      },
    ],
  },
  data_asset: {
    label: 'Data Asset',
    description: 'Match by data asset name or pattern',
    category: 'basic',
    params: [
      {
        name: 'pattern',
        type: 'string',
        label: 'Asset Pattern',
        placeholder: '*_production_*',
      },
    ],
  },
  metadata: {
    label: 'Metadata',
    description: 'Match by notification metadata field',
    category: 'condition',
    params: [
      {
        name: 'field',
        type: 'string',
        label: 'Field Name',
        placeholder: 'source_type',
      },
      {
        name: 'value',
        type: 'string',
        label: 'Expected Value',
        placeholder: 'database',
      },
    ],
  },
  status: {
    label: 'Status',
    description: 'Match by validation status',
    category: 'basic',
    params: [
      {
        name: 'status',
        type: 'select',
        label: 'Status',
        options: ['passed', 'failed', 'warning', 'error'],
      },
    ],
  },
  error: {
    label: 'Error',
    description: 'Match failed/errored notifications',
    category: 'condition',
    params: [],
  },
  always: {
    label: 'Always Match',
    description: 'Always matches (catch-all)',
    category: 'static',
    params: [],
  },
  never: {
    label: 'Never Match',
    description: 'Never matches (disabled)',
    category: 'static',
    params: [],
  },
  all_of: {
    label: 'All Of (AND)',
    description: 'Match when ALL sub-rules match',
    category: 'combinator',
    params: [],
  },
  any_of: {
    label: 'Any Of (OR)',
    description: 'Match when ANY sub-rule matches',
    category: 'combinator',
    params: [],
  },
  not: {
    label: 'Not',
    description: 'Negate the sub-rule',
    category: 'combinator',
    params: [],
  },
}

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  basic: { label: 'Basic', color: 'bg-blue-500' },
  condition: { label: 'Condition', color: 'bg-purple-500' },
  combinator: { label: 'Combinator', color: 'bg-orange-500' },
  static: { label: 'Static', color: 'bg-gray-500' },
}

export function RuleBuilder({
  value,
  onChange,
  depth = 0,
  maxDepth = 3,
}: RuleBuilderProps) {
  const typeInfo = RULE_TYPE_INFO[value.type]
  const isCombinator = typeInfo?.category === 'combinator'

  const handleTypeChange = useCallback(
    (newType: RuleType) => {
      const info = RULE_TYPE_INFO[newType]
      const newConfig: RuleConfig = { type: newType }

      // Initialize default params
      if (info.params && info.params.length > 0) {
        newConfig.params = {}
        for (const param of info.params) {
          if (param.type === 'select' && param.options?.length) {
            newConfig.params[param.name] = param.options[0]
          }
        }
      }

      // Initialize sub-rules for combinators
      if (info.category === 'combinator') {
        newConfig.rules = newType === 'not' ? [{ type: 'always' }] : []
      }

      onChange(newConfig)
    },
    [onChange]
  )

  const handleParamChange = useCallback(
    (paramName: string, paramValue: unknown) => {
      onChange({
        ...value,
        params: {
          ...value.params,
          [paramName]: paramValue,
        },
      })
    },
    [value, onChange]
  )

  const handleAddSubRule = useCallback(() => {
    onChange({
      ...value,
      rules: [...(value.rules || []), { type: 'always' }],
    })
  }, [value, onChange])

  const handleRemoveSubRule = useCallback(
    (index: number) => {
      const newRules = [...(value.rules || [])]
      newRules.splice(index, 1)
      onChange({
        ...value,
        rules: newRules,
      })
    },
    [value, onChange]
  )

  const handleSubRuleChange = useCallback(
    (index: number, newRule: RuleConfig) => {
      const newRules = [...(value.rules || [])]
      newRules[index] = newRule
      onChange({
        ...value,
        rules: newRules,
      })
    },
    [value, onChange]
  )

  const isValid = validateRule(value)

  return (
    <Card className={cn('relative', depth > 0 && 'border-l-4 border-l-muted-foreground/20')}>
      <CardHeader className="py-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm">
              {depth === 0 ? 'Rule Configuration' : `Sub-rule ${depth}`}
            </CardTitle>
            {typeInfo && (
              <Badge
                variant="secondary"
                className={cn(
                  'text-xs text-white',
                  CATEGORY_LABELS[typeInfo.category].color
                )}
              >
                {CATEGORY_LABELS[typeInfo.category].label}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isValid ? (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="py-3 px-4 space-y-4">
        {/* Rule Type Selector */}
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            Rule Type
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="h-3.5 w-3.5 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">{typeInfo?.description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </Label>
          <Select value={value.type} onValueChange={(v) => handleTypeChange(v as RuleType)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <div className="text-xs font-medium text-muted-foreground px-2 py-1">
                Basic Rules
              </div>
              {Object.entries(RULE_TYPE_INFO)
                .filter(([_, info]) => info.category === 'basic')
                .map(([type, info]) => (
                  <SelectItem key={type} value={type}>
                    {info.label}
                  </SelectItem>
                ))}
              <div className="text-xs font-medium text-muted-foreground px-2 py-1 mt-2">
                Conditions
              </div>
              {Object.entries(RULE_TYPE_INFO)
                .filter(([_, info]) => info.category === 'condition')
                .map(([type, info]) => (
                  <SelectItem key={type} value={type}>
                    {info.label}
                  </SelectItem>
                ))}
              <div className="text-xs font-medium text-muted-foreground px-2 py-1 mt-2">
                Combinators
              </div>
              {Object.entries(RULE_TYPE_INFO)
                .filter(([_, info]) => info.category === 'combinator')
                .map(([type, info]) => (
                  <SelectItem key={type} value={type} disabled={depth >= maxDepth}>
                    {info.label}
                  </SelectItem>
                ))}
              <div className="text-xs font-medium text-muted-foreground px-2 py-1 mt-2">
                Static
              </div>
              {Object.entries(RULE_TYPE_INFO)
                .filter(([_, info]) => info.category === 'static')
                .map(([type, info]) => (
                  <SelectItem key={type} value={type}>
                    {info.label}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </div>

        {/* Parameters */}
        {typeInfo?.params && typeInfo.params.length > 0 && (
          <div className="space-y-3">
            {typeInfo.params.map((param) => (
              <div key={param.name} className="space-y-1">
                <Label className="text-xs">{param.label}</Label>
                {param.type === 'select' && param.options ? (
                  <Select
                    value={String(value.params?.[param.name] || param.options[0])}
                    onValueChange={(v) => handleParamChange(param.name, v)}
                  >
                    <SelectTrigger className="h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {param.options.map((opt) => (
                        <SelectItem key={opt} value={opt}>
                          {opt}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : param.type === 'number' ? (
                  <Input
                    type="number"
                    min={param.min}
                    max={param.max}
                    placeholder={param.placeholder}
                    value={value.params?.[param.name] ?? ''}
                    onChange={(e) =>
                      handleParamChange(
                        param.name,
                        e.target.value ? Number(e.target.value) : undefined
                      )
                    }
                    className="h-8"
                  />
                ) : (
                  <Input
                    placeholder={param.placeholder}
                    value={String(value.params?.[param.name] || '')}
                    onChange={(e) => handleParamChange(param.name, e.target.value)}
                    className="h-8"
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Sub-rules for combinators */}
        {isCombinator && depth < maxDepth && (
          <div className="space-y-3 pl-2 border-l-2 border-muted">
            <div className="flex items-center justify-between">
              <Label className="text-xs">
                {value.type === 'not' ? 'Negate Rule' : 'Sub-rules'}
              </Label>
              {value.type !== 'not' && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleAddSubRule}
                  className="h-6 text-xs"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add
                </Button>
              )}
            </div>

            {(value.rules || []).map((rule, index) => (
              <div key={index} className="relative">
                <RuleBuilder
                  value={rule}
                  onChange={(newRule) => handleSubRuleChange(index, newRule)}
                  depth={depth + 1}
                  maxDepth={maxDepth}
                />
                {value.type !== 'not' && value.rules && value.rules.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveSubRule(index)}
                    className="absolute top-2 right-2 h-6 w-6 p-0"
                  >
                    <Trash2 className="h-3 w-3 text-destructive" />
                  </Button>
                )}
              </div>
            ))}

            {value.type !== 'not' && (!value.rules || value.rules.length === 0) && (
              <p className="text-xs text-muted-foreground text-center py-2">
                No sub-rules. Add at least one rule.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function validateRule(rule: RuleConfig): boolean {
  const info = RULE_TYPE_INFO[rule.type]
  if (!info) return false

  // Check required params
  if (info.params) {
    for (const param of info.params) {
      const val = rule.params?.[param.name]
      if (val === undefined || val === '' || val === null) {
        // Some params may be optional
        continue
      }
    }
  }

  // Check combinator sub-rules
  if (info.category === 'combinator') {
    if (rule.type === 'not') {
      return rule.rules?.length === 1 && validateRule(rule.rules[0])
    }
    if (!rule.rules || rule.rules.length === 0) {
      return false
    }
    return rule.rules.every(validateRule)
  }

  return true
}

export default RuleBuilder
