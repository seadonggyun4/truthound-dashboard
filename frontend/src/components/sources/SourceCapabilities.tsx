/**
 * SourceCapabilities - Display data source capabilities with tooltips
 *
 * Shows what features a data source supports based on truthound framework:
 * - Lazy evaluation
 * - SQL pushdown
 * - Efficient sampling
 * - Streaming
 * - Schema inference
 * - Fast row count
 */

import {
  Zap,
  Filter,
  Shuffle,
  Radio,
  FileSearch,
  Hash,
  type LucideIcon,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import {
  type DataSourceCapability,
  type SourceType,
  CAPABILITY_INFO,
  getDefaultCapabilities,
} from '@/types/datasources'

// ============================================================================
// Types
// ============================================================================

interface SourceCapabilitiesProps {
  /** Source type to show capabilities for */
  sourceType?: SourceType | string
  /** Or directly pass capabilities array */
  capabilities?: DataSourceCapability[]
  /** Show labels or just icons */
  showLabels?: boolean
  /** Custom class name */
  className?: string
  /** Badge variant */
  variant?: 'default' | 'outline' | 'secondary'
  /** Size */
  size?: 'xs' | 'sm' | 'md'
  /** Interactive - show hover effects */
  interactive?: boolean
  /** Color scheme */
  colorScheme?: 'default' | 'success' | 'muted'
}

// ============================================================================
// Icon Mapping
// ============================================================================

const CAPABILITY_ICONS: Record<DataSourceCapability, LucideIcon> = {
  lazy_evaluation: Zap,
  sql_pushdown: Filter,
  sampling: Shuffle,
  streaming: Radio,
  schema_inference: FileSearch,
  row_count: Hash,
}

/**
 * Get icon component for a capability.
 */
function getCapabilityIcon(capability: DataSourceCapability): LucideIcon {
  return CAPABILITY_ICONS[capability] || Zap
}

// ============================================================================
// Main Component
// ============================================================================

export function SourceCapabilities({
  sourceType,
  capabilities: capabilitiesProp,
  showLabels = true,
  className,
  variant = 'secondary',
  size = 'sm',
  interactive = true,
  colorScheme = 'default',
}: SourceCapabilitiesProps) {
  // Get capabilities from props or derive from source type
  const capabilities =
    capabilitiesProp ||
    (sourceType ? getDefaultCapabilities(sourceType as SourceType) : [])

  if (capabilities.length === 0) return null

  // Size classes
  const sizeClasses = {
    xs: 'text-[9px] px-1 py-0 h-4',
    sm: 'text-[10px] px-1.5 py-0 h-5',
    md: 'text-xs px-2 py-0.5 h-6',
  }

  const iconSizes = {
    xs: 'h-2.5 w-2.5',
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
  }

  // Color scheme classes
  const colorClasses = {
    default: '',
    success:
      'bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20 hover:bg-green-500/20',
    muted:
      'bg-muted/50 text-muted-foreground border-muted hover:bg-muted',
  }

  return (
    <TooltipProvider>
      <div className={cn('flex flex-wrap gap-1.5', className)}>
        {capabilities.map((cap) => {
          const Icon = getCapabilityIcon(cap)
          const info = CAPABILITY_INFO[cap]

          if (!info) return null

          return (
            <Tooltip key={cap}>
              <TooltipTrigger asChild>
                <Badge
                  variant={variant}
                  className={cn(
                    'gap-1',
                    sizeClasses[size],
                    colorClasses[colorScheme],
                    interactive && 'cursor-help transition-colors'
                  )}
                >
                  <Icon className={iconSizes[size]} />
                  {showLabels && <span>{info.label}</span>}
                </Badge>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[240px]">
                <div className="space-y-1">
                  <p className="font-medium text-xs">{info.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {info.description}
                  </p>
                </div>
              </TooltipContent>
            </Tooltip>
          )
        })}
      </div>
    </TooltipProvider>
  )
}

// ============================================================================
// Variant Components
// ============================================================================

/**
 * Compact version showing only icons.
 */
export function SourceCapabilitiesCompact(
  props: Omit<SourceCapabilitiesProps, 'showLabels'>
) {
  return <SourceCapabilities {...props} showLabels={false} />
}

/**
 * Inline version for use in tables or lists.
 */
export function SourceCapabilitiesInline({
  capabilities,
  sourceType,
  maxShow = 3,
  className,
}: {
  capabilities?: DataSourceCapability[]
  sourceType?: SourceType | string
  maxShow?: number
  className?: string
}) {
  const caps =
    capabilities ||
    (sourceType ? getDefaultCapabilities(sourceType as SourceType) : [])

  if (caps.length === 0) return null

  const visibleCaps = caps.slice(0, maxShow)
  const hiddenCount = caps.length - maxShow

  return (
    <TooltipProvider>
      <div className={cn('flex items-center gap-1', className)}>
        {visibleCaps.map((cap) => {
          const Icon = getCapabilityIcon(cap)
          const info = CAPABILITY_INFO[cap]

          return (
            <Tooltip key={cap}>
              <TooltipTrigger asChild>
                <span className="text-muted-foreground hover:text-foreground transition-colors cursor-help">
                  <Icon className="h-3.5 w-3.5" />
                </span>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs">{info?.label}</p>
              </TooltipContent>
            </Tooltip>
          )
        })}
        {hiddenCount > 0 && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="text-[10px] text-muted-foreground cursor-help">
                +{hiddenCount}
              </span>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <div className="space-y-1">
                {caps.slice(maxShow).map((cap) => (
                  <p key={cap} className="text-xs">
                    {CAPABILITY_INFO[cap]?.label}
                  </p>
                ))}
              </div>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  )
}

/**
 * List version showing capabilities vertically.
 */
export function SourceCapabilitiesList({
  capabilities,
  sourceType,
  className,
}: {
  capabilities?: DataSourceCapability[]
  sourceType?: SourceType | string
  className?: string
}) {
  const caps =
    capabilities ||
    (sourceType ? getDefaultCapabilities(sourceType as SourceType) : [])

  if (caps.length === 0) return null

  return (
    <ul className={cn('space-y-1.5', className)}>
      {caps.map((cap) => {
        const Icon = getCapabilityIcon(cap)
        const info = CAPABILITY_INFO[cap]

        return (
          <li key={cap} className="flex items-start gap-2 text-sm">
            <Icon className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
            <div>
              <span className="font-medium">{info?.label}</span>
              <p className="text-xs text-muted-foreground">
                {info?.description}
              </p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}

// ============================================================================
// Utility Components
// ============================================================================

/**
 * Single capability badge component.
 */
export function CapabilityBadge({
  capability,
  showLabel = true,
  size = 'sm',
  variant = 'secondary',
  colorScheme = 'default',
}: {
  capability: DataSourceCapability
  showLabel?: boolean
  size?: 'xs' | 'sm' | 'md'
  variant?: 'default' | 'outline' | 'secondary'
  colorScheme?: 'default' | 'success' | 'muted'
}) {
  const Icon = getCapabilityIcon(capability)
  const info = CAPABILITY_INFO[capability]

  if (!info) return null

  const sizeClasses = {
    xs: 'text-[9px] px-1 py-0 h-4',
    sm: 'text-[10px] px-1.5 py-0 h-5',
    md: 'text-xs px-2 py-0.5 h-6',
  }

  const iconSizes = {
    xs: 'h-2.5 w-2.5',
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
  }

  const colorClasses = {
    default: '',
    success:
      'bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20',
    muted: 'bg-muted/50 text-muted-foreground border-muted',
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant={variant}
            className={cn(
              'gap-1 cursor-help',
              sizeClasses[size],
              colorClasses[colorScheme]
            )}
          >
            <Icon className={iconSizes[size]} />
            {showLabel && <span>{info.label}</span>}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-[200px]">
          <p className="text-xs">{info.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// ============================================================================
// Exports
// ============================================================================

export { getCapabilityIcon, CAPABILITY_ICONS }
export default SourceCapabilities
