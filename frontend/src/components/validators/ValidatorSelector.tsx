/**
 * ValidatorSelector - Built-in Truthound validator selection UI.
 *
 * Features:
 * - Category-based grouping
 * - Search and filter
 * - Per-validator parameter configuration
 * - Preset templates (All, Quick Check, Schema Only, etc.)
 */

import { useState, useMemo, useCallback, useEffect } from 'react'
import { Search, Filter, ChevronDown, ChevronRight, Zap, Shield, Database } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ValidatorConfigCard } from './ValidatorConfigCard'
import type { ValidatorDefinition, ValidatorCategory } from '@/api/modules/validators'
import type { ValidatorConfig } from '@/api/modules/validations'
import { createEmptyConfig, validateConfig } from '@/types/validators'

interface ValidatorSelectorProps {
  validators: ValidatorDefinition[]
  configs: ValidatorConfig[]
  onChange: (configs: ValidatorConfig[]) => void
  columns?: string[]
  errors?: Record<string, Record<string, string>>
}

interface CategoryGroup {
  category: ValidatorCategory
  label: string
  validators: ValidatorDefinition[]
  enabledCount: number
}

const PRESETS = [
  {
    id: 'all',
    label: 'All Validators',
    icon: Zap,
    description: 'Run all available validators',
    filter: () => true,
  },
  {
    id: 'quick',
    label: 'Quick Check',
    icon: Zap,
    description: 'Fast validation for common issues',
    filter: (validator: ValidatorDefinition) =>
      ['Null', 'Duplicate', 'ColumnExists', 'RowCount'].includes(validator.name),
  },
  {
    id: 'schema',
    label: 'Schema Only',
    icon: Database,
    description: 'Structure and type validation',
    filter: (validator: ValidatorDefinition) => validator.category === 'schema',
  },
  {
    id: 'completeness',
    label: 'Data Quality',
    icon: Shield,
    description: 'Completeness and uniqueness checks',
    filter: (validator: ValidatorDefinition) =>
      validator.category === 'completeness' || validator.category === 'uniqueness',
  },
]

const CATEGORY_LABELS: Record<ValidatorCategory, string> = {
  schema: 'Schema',
  completeness: 'Completeness',
  uniqueness: 'Uniqueness',
  distribution: 'Distribution',
  string: 'String',
  datetime: 'Datetime',
  aggregate: 'Aggregate',
  drift: 'Drift',
  anomaly: 'Anomaly',
  cross_table: 'Cross-Table',
  multi_column: 'Multi-Column',
  query: 'Query',
  table: 'Table',
  geospatial: 'Geospatial',
  privacy: 'Privacy',
  business_rule: 'Business Rule',
  profiling: 'Profiling',
  localization: 'Localization',
  ml_feature: 'ML Feature',
  timeseries: 'Time Series',
  referential: 'Referential',
}

export function ValidatorSelector({
  validators,
  configs,
  onChange,
  columns = [],
  errors = {},
}: ValidatorSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<ValidatorCategory | 'all'>('all')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['schema', 'completeness'])
  )

  useEffect(() => {
    if (configs.length === 0 && validators.length > 0) {
      onChange(validators.map((validator) => createEmptyConfig(validator)))
    }
  }, [validators, configs.length, onChange])

  const getConfig = useCallback(
    (name: string): ValidatorConfig => {
      return configs.find((config) => config.name === name) || {
        name,
        enabled: false,
        params: {},
      }
    },
    [configs]
  )

  const updateConfig = useCallback(
    (updatedConfig: ValidatorConfig) => {
      const nextConfigs = configs.map((config) =>
        config.name === updatedConfig.name ? updatedConfig : config
      )
      if (!configs.find((config) => config.name === updatedConfig.name)) {
        nextConfigs.push(updatedConfig)
      }
      onChange(nextConfigs)
    },
    [configs, onChange]
  )

  const applyPreset = useCallback(
    (presetId: string) => {
      const preset = PRESETS.find((entry) => entry.id === presetId)
      if (!preset) return

      onChange(
        validators.map((validator) => ({
          ...getConfig(validator.name),
          enabled: preset.filter(validator),
        }))
      )
    },
    [validators, getConfig, onChange]
  )

  const toggleCategory = useCallback(
    (category: ValidatorCategory, enabled: boolean) => {
      onChange(
        configs.map((config) => {
          const definition = validators.find((validator) => validator.name === config.name)
          if (definition?.category === category) {
            return { ...config, enabled }
          }
          return config
        })
      )
    },
    [configs, validators, onChange]
  )

  const toggleCategoryExpansion = useCallback((category: string) => {
    setExpandedCategories((previous) => {
      const next = new Set(previous)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }, [])

  const categoryGroups = useMemo((): CategoryGroup[] => {
    const grouped: Partial<Record<ValidatorCategory, ValidatorDefinition[]>> = {}

    const filtered = validators.filter((validator) => {
      if (!searchQuery) return true
      const query = searchQuery.toLowerCase()
      return (
        validator.name.toLowerCase().includes(query) ||
        validator.display_name.toLowerCase().includes(query) ||
        validator.description.toLowerCase().includes(query) ||
        validator.tags.some((tag) => tag.toLowerCase().includes(query))
      )
    })

    for (const validator of filtered) {
      grouped[validator.category] = [...(grouped[validator.category] || []), validator]
    }

    return Object.entries(grouped)
      .map(([category, items]) => ({
        category: category as ValidatorCategory,
        label: CATEGORY_LABELS[category as ValidatorCategory] || category,
        validators: items || [],
        enabledCount: (items || []).filter((validator) => getConfig(validator.name).enabled)
          .length,
      }))
      .filter((group) => selectedCategory === 'all' || group.category === selectedCategory)
      .sort((left, right) => {
        const order = Object.keys(CATEGORY_LABELS)
        return order.indexOf(left.category) - order.indexOf(right.category)
      })
  }, [validators, searchQuery, selectedCategory, getConfig])

  const enabledCount = useMemo(
    () => configs.filter((config) => config.enabled).length,
    [configs]
  )

  const renderCategoryGroup = (group: CategoryGroup, showActions: boolean) => (
    <div key={group.category} className="border rounded-lg overflow-hidden">
      <button
        onClick={() => toggleCategoryExpansion(group.category)}
        className="w-full flex items-center justify-between p-3 bg-muted/50 hover:bg-muted/80 transition-colors"
      >
        <div className="flex items-center gap-2">
          {expandedCategories.has(group.category) ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <span className="font-medium">{group.label}</span>
          <Badge variant="secondary">
            {group.enabledCount} / {group.validators.length}
          </Badge>
        </div>
        {showActions && (
          <div className="flex gap-2" onClick={(event) => event.stopPropagation()}>
            <span
              role="button"
              tabIndex={0}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium h-8 px-3 hover:bg-accent hover:text-accent-foreground cursor-pointer"
              onClick={() => toggleCategory(group.category, true)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  toggleCategory(group.category, true)
                }
              }}
            >
              Enable All
            </span>
            <span
              role="button"
              tabIndex={0}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium h-8 px-3 hover:bg-accent hover:text-accent-foreground cursor-pointer"
              onClick={() => toggleCategory(group.category, false)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  toggleCategory(group.category, false)
                }
              }}
            >
              Disable All
            </span>
          </div>
        )}
      </button>

      {expandedCategories.has(group.category) && (
        <div className="p-3 space-y-2">
          {group.validators.map((definition) => (
            <ValidatorConfigCard
              key={definition.name}
              definition={definition}
              config={getConfig(definition.name)}
              onChange={updateConfig}
              columns={columns}
              errors={errors[definition.name]}
            />
          ))}
        </div>
      )}
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search validators..."
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            className="pl-9"
          />
        </div>

        <Select
          value={selectedCategory}
          onValueChange={(value) => setSelectedCategory(value as ValidatorCategory | 'all')}
        >
          <SelectTrigger className="w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Badge variant="outline" className="h-10 px-3 flex items-center gap-2">
          {enabledCount} / {validators.length} enabled
        </Badge>
      </div>

      <Tabs defaultValue="custom" className="w-full">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="custom">Custom</TabsTrigger>
          {PRESETS.map((preset) => (
            <TabsTrigger
              key={preset.id}
              value={preset.id}
              onClick={() => applyPreset(preset.id)}
            >
              <preset.icon className="h-4 w-4 mr-1" />
              {preset.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="custom" className="mt-4">
          <div className="space-y-4">
            {categoryGroups.map((group) => renderCategoryGroup(group, true))}
            {categoryGroups.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No validators match your search criteria.
              </div>
            )}
          </div>
        </TabsContent>

        {PRESETS.map((preset) => (
          <TabsContent key={preset.id} value={preset.id} className="mt-4">
            <div className="p-4 bg-muted/30 rounded-lg mb-4">
              <p className="text-sm text-muted-foreground">{preset.description}</p>
            </div>
            <div className="space-y-4">
              {categoryGroups.map((group) => renderCategoryGroup(group, false))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

export { createEmptyConfig, validateConfig }
