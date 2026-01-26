/**
 * SourceTypeSelector - Grid-based source type selection
 *
 * Supports all source types from truthound's datasources module:
 * - File-based: CSV, Parquet, JSON, NDJSON, JSONL
 * - Core SQL: PostgreSQL, MySQL, SQLite
 * - Cloud DW: BigQuery, Snowflake, Redshift, Databricks
 * - Enterprise: Oracle, SQL Server
 * - Big Data: Apache Spark
 * - NoSQL: MongoDB, Elasticsearch
 * - Streaming: Apache Kafka
 */

import { useMemo } from 'react'
import {
  Database,
  FileSpreadsheet,
  FileJson,
  FileCode,
  Cloud,
  Layers,
  Snowflake,
  Zap,
  Radio,
  Search,
  Server,
  HardDrive,
  Warehouse,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SourceTypeDefinition, SourceCategory } from '@/api/client'

interface SourceTypeSelectorProps {
  sourceTypes: SourceTypeDefinition[]
  selectedType: string | null
  onSelect: (type: string) => void
  categoryFilter?: SourceCategory | null
  /** Compact mode for smaller spaces */
  compact?: boolean
}

/**
 * Icon mapping for source types.
 * Maps the icon name from the backend to a Lucide icon component.
 * Backend icon names come from connections.py SourceTypeDefinition.icon field.
 */
const SOURCE_ICONS: Record<string, LucideIcon> = {
  // File types (from backend: 'file')
  file: FileSpreadsheet,
  file_json: FileJson,
  file_code: FileCode,
  // Database types (from backend: 'database')
  database: Database,
  server: Server,
  hard_drive: HardDrive,
  // Cloud/Warehouse types (from backend: 'cloud', 'snowflake')
  cloud: Cloud,
  snowflake: Snowflake,
  warehouse: Warehouse,
  // Big Data (from backend: 'layers', 'zap')
  layers: Layers,
  zap: Zap,
  // NoSQL (from backend: 'search')
  search: Search,
  // Streaming (from backend: 'radio')
  radio: Radio,
}

/**
 * Fallback icon based on source type category
 */
function getFallbackIcon(category: SourceCategory): LucideIcon {
  return CATEGORY_CONFIG[category]?.icon || Database
}

// Category labels and icons
const CATEGORY_CONFIG: Record<
  SourceCategory,
  { label: string; icon: LucideIcon; color: string }
> = {
  file: { label: 'Files', icon: FileSpreadsheet, color: 'text-blue-500' },
  database: { label: 'Databases', icon: Database, color: 'text-green-500' },
  warehouse: { label: 'Data Warehouses', icon: Cloud, color: 'text-purple-500' },
  bigdata: { label: 'Big Data', icon: Layers, color: 'text-orange-500' },
  nosql: { label: 'NoSQL', icon: Search, color: 'text-cyan-500' },
  streaming: { label: 'Streaming', icon: Radio, color: 'text-red-500' },
}

export function SourceTypeSelector({
  sourceTypes,
  selectedType,
  onSelect,
  categoryFilter,
  compact = false,
}: SourceTypeSelectorProps) {
  // Group source types by category
  const groupedTypes = useMemo(() => {
    const groups: Record<SourceCategory, SourceTypeDefinition[]> = {
      file: [],
      database: [],
      warehouse: [],
      bigdata: [],
      nosql: [],
      streaming: [],
    }

    for (const sourceType of sourceTypes) {
      if (groups[sourceType.category]) {
        groups[sourceType.category].push(sourceType)
      }
    }

    return groups
  }, [sourceTypes])

  // Filter by category if specified
  const categoriesToShow = categoryFilter
    ? [categoryFilter]
    : (Object.keys(CATEGORY_CONFIG) as SourceCategory[])

  return (
    <div className="space-y-6">
      {categoriesToShow.map((category) => {
        const types = groupedTypes[category]
        if (types.length === 0) return null

        const config = CATEGORY_CONFIG[category]
        const CategoryIcon = config.icon

        return (
          <div key={category} className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <CategoryIcon className={cn('h-4 w-4', config.color)} />
              <span>{config.label}</span>
              <span className="text-xs">({types.length})</span>
            </div>

            <div
              className={cn(
                'grid gap-2',
                compact
                  ? 'grid-cols-2 sm:grid-cols-3'
                  : 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4'
              )}
            >
              {types.map((sourceType) => {
                const Icon = SOURCE_ICONS[sourceType.icon] || getFallbackIcon(sourceType.category)
                const isSelected = selectedType === sourceType.type

                return (
                  <button
                    key={sourceType.type}
                    type="button"
                    onClick={() => onSelect(sourceType.type)}
                    className={cn(
                      'group relative flex flex-col items-center gap-2 rounded-lg border transition-all',
                      compact ? 'p-3' : 'p-4',
                      'hover:border-primary/50 hover:bg-accent/50',
                      isSelected
                        ? 'border-primary bg-primary/10 ring-1 ring-primary'
                        : 'border-border bg-card'
                    )}
                  >
                    <div
                      className={cn(
                        'flex items-center justify-center rounded-lg',
                        compact ? 'h-8 w-8' : 'h-10 w-10',
                        isSelected
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground group-hover:bg-primary/20'
                      )}
                    >
                      <Icon className={cn(compact ? 'h-4 w-4' : 'h-5 w-5')} />
                    </div>

                    <div className="text-center">
                      <div className={cn('font-medium', compact ? 'text-xs' : 'text-sm')}>
                        {sourceType.name}
                      </div>
                      {!compact && (
                        <div className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                          {sourceType.description}
                        </div>
                      )}
                    </div>

                    {/* Selected indicator */}
                    {isSelected && (
                      <div className="absolute right-2 top-2 h-2 w-2 rounded-full bg-primary" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
