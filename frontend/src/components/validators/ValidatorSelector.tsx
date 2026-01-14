/**
 * ValidatorSelector - Main component for selecting and configuring validators.
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
import { Button } from '@/components/ui/button'
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
import type { ValidatorDefinition, ValidatorConfig, ValidatorCategory } from '@/api/client'
import {
  createEmptyConfig,
  validateConfig,
} from '@/types/validators'

// =============================================================================
// Types
// =============================================================================

interface ValidatorSelectorProps {
  /** All available validator definitions */
  validators: ValidatorDefinition[]
  /** Current validator configurations */
  configs: ValidatorConfig[]
  /** Callback when configs change */
  onChange: (configs: ValidatorConfig[]) => void
  /** Available columns from data source (for column picker) */
  columns?: string[]
  /** Validation errors by validator name */
  errors?: Record<string, Record<string, string>>
}

interface CategoryGroup {
  category: ValidatorCategory
  label: string
  validators: ValidatorDefinition[]
  enabledCount: number
}

// =============================================================================
// Presets
// =============================================================================

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
    filter: (v: ValidatorDefinition) =>
      ['Null', 'Duplicate', 'ColumnExists', 'RowCount'].includes(v.name),
  },
  {
    id: 'schema',
    label: 'Schema Only',
    icon: Database,
    description: 'Structure and type validation',
    filter: (v: ValidatorDefinition) => v.category === 'schema',
  },
  {
    id: 'completeness',
    label: 'Data Quality',
    icon: Shield,
    description: 'Completeness and uniqueness checks',
    filter: (v: ValidatorDefinition) =>
      v.category === 'completeness' || v.category === 'uniqueness',
  },
]

// =============================================================================
// Category Labels
// =============================================================================

const CATEGORY_LABELS: Record<ValidatorCategory, string> = {
  schema: 'Schema',
  completeness: 'Completeness',
  uniqueness: 'Uniqueness',
  distribution: 'Distribution',
  string: 'String',
  datetime: 'Datetime',
  aggregate: 'Aggregate',
  cross_table: 'Cross-Table',
  query: 'Query',
  multi_column: 'Multi-Column',
  table: 'Table',
  geospatial: 'Geospatial',
  drift: 'Drift',
  anomaly: 'Anomaly',
}

// =============================================================================
// Component
// =============================================================================

export function ValidatorSelector({
  validators,
  configs,
  onChange,
  columns = [],
  errors = {},
}: ValidatorSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<ValidatorCategory | 'all'>('all')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['schema', 'completeness']))

  // Initialize configs if empty
  useEffect(() => {
    if (configs.length === 0 && validators.length > 0) {
      // Start with all validators enabled by default
      const initialConfigs = validators.map((v) => createEmptyConfig(v))
      onChange(initialConfigs)
    }
  }, [validators, configs.length, onChange])

  // Get config for a validator
  const getConfig = useCallback(
    (name: string): ValidatorConfig => {
      return configs.find((c) => c.name === name) || { name, enabled: false, params: {} }
    },
    [configs]
  )

  // Update a single validator config
  const updateConfig = useCallback(
    (updatedConfig: ValidatorConfig) => {
      const newConfigs = configs.map((c) =>
        c.name === updatedConfig.name ? updatedConfig : c
      )
      // If config doesn't exist, add it
      if (!configs.find((c) => c.name === updatedConfig.name)) {
        newConfigs.push(updatedConfig)
      }
      onChange(newConfigs)
    },
    [configs, onChange]
  )

  // Apply preset
  const applyPreset = useCallback(
    (presetId: string) => {
      const preset = PRESETS.find((p) => p.id === presetId)
      if (!preset) return

      const newConfigs = validators.map((v) => {
        const config = getConfig(v.name)
        return {
          ...config,
          enabled: preset.filter(v),
        }
      })
      onChange(newConfigs)
    },
    [validators, getConfig, onChange]
  )

  // Enable/disable all in category
  const toggleCategory = useCallback(
    (category: ValidatorCategory, enabled: boolean) => {
      const newConfigs = configs.map((c) => {
        const def = validators.find((v) => v.name === c.name)
        if (def?.category === category) {
          return { ...c, enabled }
        }
        return c
      })
      onChange(newConfigs)
    },
    [configs, validators, onChange]
  )

  // Toggle category expansion
  const toggleCategoryExpansion = useCallback((category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }, [])

  // Group validators by category
  const categoryGroups = useMemo((): CategoryGroup[] => {
    const groups: Record<ValidatorCategory, ValidatorDefinition[]> = {} as Record<
      ValidatorCategory,
      ValidatorDefinition[]
    >

    // Filter by search
    const filtered = validators.filter((v) => {
      if (!searchQuery) return true
      const query = searchQuery.toLowerCase()
      return (
        v.name.toLowerCase().includes(query) ||
        v.display_name.toLowerCase().includes(query) ||
        v.description.toLowerCase().includes(query) ||
        v.tags.some((t) => t.toLowerCase().includes(query))
      )
    })

    // Group by category
    for (const v of filtered) {
      if (!groups[v.category]) {
        groups[v.category] = []
      }
      groups[v.category].push(v)
    }

    // Convert to array and add counts
    return Object.entries(groups)
      .map(([category, vals]) => ({
        category: category as ValidatorCategory,
        label: CATEGORY_LABELS[category as ValidatorCategory] || category,
        validators: vals,
        enabledCount: vals.filter((v) => getConfig(v.name).enabled).length,
      }))
      .filter((g) => selectedCategory === 'all' || g.category === selectedCategory)
      .sort((a, b) => {
        // Sort by category order in CATEGORY_LABELS
        const order = Object.keys(CATEGORY_LABELS)
        return order.indexOf(a.category) - order.indexOf(b.category)
      })
  }, [validators, searchQuery, selectedCategory, getConfig])

  // Summary stats
  const stats = useMemo(() => {
    const enabled = configs.filter((c) => c.enabled).length
    const total = validators.length
    return { enabled, total }
  }, [configs, validators])

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search validators..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Category filter */}
        <Select
          value={selectedCategory}
          onValueChange={(v) => setSelectedCategory(v as ValidatorCategory | 'all')}
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

        {/* Stats */}
        <Badge variant="outline" className="h-10 px-3 flex items-center gap-2">
          {stats.enabled} / {stats.total} enabled
        </Badge>
      </div>

      {/* Presets */}
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
          {/* Validator list by category */}
          <div className="space-y-4">
            {categoryGroups.map((group) => (
              <div key={group.category} className="border rounded-lg overflow-hidden">
                {/* Category header */}
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
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleCategory(group.category, true)}
                    >
                      Enable All
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleCategory(group.category, false)}
                    >
                      Disable All
                    </Button>
                  </div>
                </button>

                {/* Validators in category */}
                {expandedCategories.has(group.category) && (
                  <div className="p-3 space-y-2">
                    {group.validators.map((def) => (
                      <ValidatorConfigCard
                        key={def.name}
                        definition={def}
                        config={getConfig(def.name)}
                        onChange={updateConfig}
                        columns={columns}
                        errors={errors[def.name]}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}

            {categoryGroups.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No validators match your search criteria.
              </div>
            )}
          </div>
        </TabsContent>

        {/* Preset tabs just show the same content with presets applied */}
        {PRESETS.map((preset) => (
          <TabsContent key={preset.id} value={preset.id} className="mt-4">
            <div className="p-4 bg-muted/30 rounded-lg mb-4">
              <p className="text-sm text-muted-foreground">{preset.description}</p>
            </div>
            <div className="space-y-4">
              {categoryGroups.map((group) => (
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
                  </button>

                  {expandedCategories.has(group.category) && (
                    <div className="p-3 space-y-2">
                      {group.validators.map((def) => (
                        <ValidatorConfigCard
                          key={def.name}
                          definition={def}
                          config={getConfig(def.name)}
                          onChange={updateConfig}
                          columns={columns}
                          errors={errors[def.name]}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

export { createEmptyConfig, validateConfig }
