/**
 * Drift Method Selector component.
 *
 * A reusable component for selecting drift detection methods with descriptions,
 * recommended badges, and default threshold information.
 *
 * Supports all 14 truthound drift detection methods (v1.2.9+):
 * - General purpose: auto, js, hellinger, bhattacharyya, tv
 * - Numeric only: ks, psi, kl, wasserstein, cvm, anderson, energy, mmd
 * - Categorical: chi2
 */

import { useCallback, useMemo } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
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
import {
  type DriftMethod,
  DRIFT_METHODS,
  DEFAULT_THRESHOLDS,
} from '@/api/modules/drift'
import { Info, Sparkles, BarChart3, Target, Hash, Divide, Truck, TrendingUp, Scale, Circle, Layers, Activity, Zap, Brain } from 'lucide-react'

/**
 * Method metadata including icons and categories.
 * All 14 methods supported by truthound v1.2.9+.
 */
const METHOD_ICONS: Record<DriftMethod, React.ElementType> = {
  // General purpose
  auto: Sparkles,
  js: Divide,
  hellinger: Circle,
  bhattacharyya: Layers,
  tv: Activity,
  // Numeric columns
  ks: TrendingUp,
  psi: BarChart3,
  kl: Divide,
  wasserstein: Truck,
  cvm: Scale,
  anderson: Target,
  energy: Zap,
  mmd: Brain,
  // Categorical
  chi2: Hash,
}

const METHOD_CATEGORIES: Record<DriftMethod, 'recommended' | 'statistical' | 'divergence' | 'distribution'> = {
  // Recommended
  auto: 'recommended',
  // Statistical tests
  ks: 'statistical',
  psi: 'statistical',
  chi2: 'statistical',
  cvm: 'statistical',
  anderson: 'statistical',
  // Divergence measures
  js: 'divergence',
  kl: 'divergence',
  hellinger: 'divergence',
  bhattacharyya: 'divergence',
  tv: 'divergence',
  // Distribution analysis
  wasserstein: 'distribution',
  energy: 'distribution',
  mmd: 'distribution',
}

export type DriftMethodSelectorVariant = 'compact' | 'detailed' | 'cards'

export interface DriftMethodSelectorProps {
  /** Currently selected method */
  value: DriftMethod
  /** Callback when method changes */
  onChange: (method: DriftMethod) => void
  /** Display variant */
  variant?: DriftMethodSelectorVariant
  /** Whether to show threshold hints */
  showThresholdHints?: boolean
  /** Whether to show method descriptions */
  showDescriptions?: boolean
  /** Custom class name */
  className?: string
  /** Disabled state */
  disabled?: boolean
  /** List of allowed methods (defaults to all) */
  allowedMethods?: DriftMethod[]
}


/**
 * Compact dropdown selector for drift methods.
 */
function CompactSelector({
  value,
  onChange,
  showThresholdHints,
  disabled,
  allowedMethods,
}: Pick<DriftMethodSelectorProps, 'value' | 'onChange' | 'showThresholdHints' | 'disabled' | 'allowedMethods'>) {
  const t = useSafeIntlayer('drift')

  const methods = useMemo(() => {
    return DRIFT_METHODS.filter(
      (m) => !allowedMethods || allowedMethods.includes(m.value)
    )
  }, [allowedMethods])

  const getMethodLabel = (method: DriftMethod): string => {
    const methodLabels = t.methods as Record<string, unknown>
    return str(methodLabels[method])
  }

  return (
    <Select value={value} onValueChange={(v) => onChange(v as DriftMethod)} disabled={disabled}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent position="popper" className="max-h-80">
        {methods.map((method) => {
          const Icon = METHOD_ICONS[method.value]
          return (
            <SelectItem key={method.value} value={method.value}>
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <span>{getMethodLabel(method.value)}</span>
                {method.value === 'auto' && (
                  <Badge variant="secondary" className="ml-1 text-xs">
                    {str(t.methodSelector.recommended)}
                  </Badge>
                )}
                {showThresholdHints && (
                  <span className="text-xs text-muted-foreground ml-auto">
                    ({DEFAULT_THRESHOLDS[method.value]})
                  </span>
                )}
              </div>
            </SelectItem>
          )
        })}
      </SelectContent>
    </Select>
  )
}

/**
 * Detailed list selector with descriptions.
 */
function DetailedSelector({
  value,
  onChange,
  showThresholdHints,
  showDescriptions,
  disabled,
  allowedMethods,
}: Pick<DriftMethodSelectorProps, 'value' | 'onChange' | 'showThresholdHints' | 'showDescriptions' | 'disabled' | 'allowedMethods'>) {
  const t = useSafeIntlayer('drift')

  const methods = useMemo(() => {
    return DRIFT_METHODS.filter(
      (m) => !allowedMethods || allowedMethods.includes(m.value)
    )
  }, [allowedMethods])

  const getMethodLabel = (method: DriftMethod): string => {
    const methodLabels = t.methods as Record<string, unknown>
    return str(methodLabels[method])
  }

  const getMethodDescription = (method: DriftMethod): string => {
    const descriptions = t.methodDescriptions as Record<string, unknown>
    return str(descriptions[method])
  }

  const getMethodBestFor = (method: DriftMethod): string => {
    const bestFor = t.methodBestFor as Record<string, unknown>
    return str(bestFor[method])
  }

  return (
    <RadioGroup
      value={value}
      onValueChange={(v: string) => onChange(v as DriftMethod)}
      disabled={disabled}
      className="space-y-2"
    >
      {methods.map((method) => {
        const Icon = METHOD_ICONS[method.value]
        const isSelected = value === method.value

        return (
          <div
            key={method.value}
            className={cn(
              'flex items-start space-x-3 rounded-lg border p-3 transition-colors cursor-pointer',
              isSelected ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/50',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            onClick={() => !disabled && onChange(method.value)}
          >
            <RadioGroupItem value={method.value} id={`method-${method.value}`} className="mt-0.5" />
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <Label
                  htmlFor={`method-${method.value}`}
                  className="font-medium cursor-pointer"
                >
                  {getMethodLabel(method.value)}
                </Label>
                {method.value === 'auto' && (
                  <Badge variant="default" className="text-xs">
                    {str(t.methodSelector.recommended)}
                  </Badge>
                )}
              </div>
              {showDescriptions && (
                <p className="text-sm text-muted-foreground">
                  {getMethodDescription(method.value)}
                </p>
              )}
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span>
                  {str(t.methodSelector.bestFor)}: {getMethodBestFor(method.value)}
                </span>
                {showThresholdHints && (
                  <span>
                    {str(t.methodSelector.defaultThreshold)}: {DEFAULT_THRESHOLDS[method.value]}
                  </span>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </RadioGroup>
  )
}

/**
 * Card-based selector with visual grouping by category.
 */
function CardsSelector({
  value,
  onChange,
  showThresholdHints,
  disabled,
  allowedMethods,
}: Pick<DriftMethodSelectorProps, 'value' | 'onChange' | 'showThresholdHints' | 'disabled' | 'allowedMethods'>) {
  const t = useSafeIntlayer('drift')

  const methods = useMemo(() => {
    return DRIFT_METHODS.filter(
      (m) => !allowedMethods || allowedMethods.includes(m.value)
    )
  }, [allowedMethods])

  const getMethodLabel = (method: DriftMethod): string => {
    const methodLabels = t.methods as Record<string, unknown>
    return str(methodLabels[method])
  }

  const getMethodDescription = (method: DriftMethod): string => {
    const descriptions = t.methodDescriptions as Record<string, unknown>
    return str(descriptions[method])
  }

  // Group methods by category
  const groupedMethods = useMemo(() => {
    const groups: Record<string, typeof methods> = {}
    methods.forEach((method) => {
      const category = METHOD_CATEGORIES[method.value]
      if (!groups[category]) {
        groups[category] = []
      }
      groups[category].push(method)
    })
    return groups
  }, [methods])

  return (
    <TooltipProvider>
      <div className="space-y-4">
        {Object.entries(groupedMethods).map(([category, categoryMethods]) => (
          <div key={category} className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground capitalize">
              {category === 'recommended' ? 'Recommended' :
               category === 'statistical' ? 'Statistical Tests' :
               category === 'divergence' ? 'Divergence Measures' :
               'Distribution Analysis'}
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {categoryMethods.map((method) => {
                const Icon = METHOD_ICONS[method.value]
                const isSelected = value === method.value

                return (
                  <Tooltip key={method.value}>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        disabled={disabled}
                        onClick={() => onChange(method.value)}
                        className={cn(
                          'flex flex-col items-center gap-1 p-3 rounded-lg border transition-all',
                          'hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-primary',
                          isSelected && 'border-primary bg-primary/10 ring-2 ring-primary',
                          !isSelected && 'border-border',
                          disabled && 'opacity-50 cursor-not-allowed'
                        )}
                      >
                        <Icon className={cn(
                          'h-5 w-5',
                          isSelected ? 'text-primary' : 'text-muted-foreground'
                        )} />
                        <span className={cn(
                          'text-sm font-medium',
                          isSelected && 'text-primary'
                        )}>
                          {getMethodLabel(method.value)}
                        </span>
                        {showThresholdHints && (
                          <span className="text-xs text-muted-foreground">
                            {DEFAULT_THRESHOLDS[method.value]}
                          </span>
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="max-w-xs">
                      <p>{getMethodDescription(method.value)}</p>
                    </TooltipContent>
                  </Tooltip>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </TooltipProvider>
  )
}

/**
 * Main DriftMethodSelector component.
 *
 * Provides three variants for selecting drift detection methods:
 * - compact: Simple dropdown (default)
 * - detailed: Radio list with descriptions
 * - cards: Visual grid with tooltips
 */
export function DriftMethodSelector({
  value,
  onChange,
  variant = 'compact',
  showThresholdHints = false,
  showDescriptions = true,
  className,
  disabled = false,
  allowedMethods,
}: DriftMethodSelectorProps) {
  const t = useSafeIntlayer('drift')

  const handleChange = useCallback(
    (method: DriftMethod) => {
      if (!disabled) {
        onChange(method)
      }
    },
    [onChange, disabled]
  )

  const commonProps = {
    value,
    onChange: handleChange,
    showThresholdHints,
    showDescriptions,
    disabled,
    allowedMethods,
  }

  return (
    <div className={cn('space-y-2', className)}>
      {variant === 'detailed' && (
        <div className="flex items-center gap-2 mb-2">
          <Label className="text-sm font-medium">{str(t.methodSelector.title)}</Label>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent>
                <p>{str(t.methodSelector.subtitle)}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}

      {variant === 'compact' && <CompactSelector {...commonProps} />}
      {variant === 'detailed' && <DetailedSelector {...commonProps} />}
      {variant === 'cards' && <CardsSelector {...commonProps} />}
    </div>
  )
}

export default DriftMethodSelector
