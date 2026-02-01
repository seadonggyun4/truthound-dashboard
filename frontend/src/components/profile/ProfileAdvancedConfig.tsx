/**
 * Profile Advanced Configuration Component.
 *
 * Provides extensible UI for configuring advanced profiling options.
 * Supports truthound's ProfilerConfig options.
 */

import { useState, useCallback } from 'react'
import { useSafeIntlayer as useIntlayer } from '@/hooks/useSafeIntlayer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Badge } from '@/components/ui/badge'
import {
  Settings2,
  ChevronDown,
  ChevronUp,
  Zap,
  BarChart3,
  Network,
  Hash,
  Info,
  RotateCcw,
} from 'lucide-react'

/**
 * ProfilerConfig options matching backend truthound ProfilerConfig.
 */
export interface ProfileAdvancedConfigData {
  // Sampling
  sampleSize: number | null
  randomSeed: number

  // Feature toggles
  includePatterns: boolean
  includeCorrelations: boolean
  includeDistributions: boolean

  // Pattern detection
  patternSampleSize: number
  minPatternMatchRatio: number

  // Correlation
  correlationThreshold: number

  // Output
  topNValues: number

  // Performance
  nJobs: number
}

const DEFAULT_CONFIG: ProfileAdvancedConfigData = {
  sampleSize: null,
  randomSeed: 42,
  includePatterns: true,
  includeCorrelations: false,
  includeDistributions: true,
  patternSampleSize: 1000,
  minPatternMatchRatio: 0.8,
  correlationThreshold: 0.7,
  topNValues: 10,
  nJobs: 1,
}

// Presets for quick configuration
const PRESETS = {
  quick: {
    label: 'Quick Scan',
    description: 'Fast profiling with minimal options',
    config: {
      sampleSize: 10000,
      randomSeed: 42,
      includePatterns: false,
      includeCorrelations: false,
      includeDistributions: false,
      patternSampleSize: 500,
      minPatternMatchRatio: 0.8,
      correlationThreshold: 0.7,
      topNValues: 5,
      nJobs: 1,
    },
  },
  balanced: {
    label: 'Balanced',
    description: 'Good balance of speed and detail',
    config: {
      sampleSize: 50000,
      randomSeed: 42,
      includePatterns: true,
      includeCorrelations: false,
      includeDistributions: true,
      patternSampleSize: 1000,
      minPatternMatchRatio: 0.8,
      correlationThreshold: 0.7,
      topNValues: 10,
      nJobs: 2,
    },
  },
  thorough: {
    label: 'Thorough',
    description: 'Complete profiling with all features',
    config: {
      sampleSize: null,
      randomSeed: 42,
      includePatterns: true,
      includeCorrelations: true,
      includeDistributions: true,
      patternSampleSize: 2000,
      minPatternMatchRatio: 0.7,
      correlationThreshold: 0.5,
      topNValues: 20,
      nJobs: 4,
    },
  },
} as const

type PresetKey = keyof typeof PRESETS | 'custom'

interface ProfileAdvancedConfigProps {
  config: ProfileAdvancedConfigData
  onChange: (config: ProfileAdvancedConfigData) => void
  onRunProfile?: (config: ProfileAdvancedConfigData) => void
  isLoading?: boolean
  className?: string
}

export function ProfileAdvancedConfig({
  config,
  onChange,
  onRunProfile,
  isLoading = false,
  className = '',
}: ProfileAdvancedConfigProps) {
  const t = useIntlayer('profiler')
  const common = useIntlayer('common')

  const [isExpanded, setIsExpanded] = useState(false)
  const [activePreset, setActivePreset] = useState<PresetKey>('custom')

  const updateConfig = useCallback(
    (updates: Partial<ProfileAdvancedConfigData>) => {
      onChange({ ...config, ...updates })
      setActivePreset('custom')
    },
    [config, onChange]
  )

  const applyPreset = useCallback(
    (preset: PresetKey) => {
      if (preset === 'custom') return
      setActivePreset(preset)
      onChange(PRESETS[preset].config)
    },
    [onChange]
  )

  const resetToDefaults = useCallback(() => {
    onChange(DEFAULT_CONFIG)
    setActivePreset('custom')
  }, [onChange])

  const handleRunProfile = useCallback(() => {
    onRunProfile?.(config)
  }, [config, onRunProfile])

  return (
    <Card className={className}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-primary" />
              <div>
                <CardTitle className="text-base">{t.advancedOptions}</CardTitle>
                <CardDescription className="text-xs">
                  Configure advanced profiling settings
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Preset badges */}
              <div className="hidden sm:flex gap-1">
                {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map((key) => (
                  <Badge
                    key={key}
                    variant={activePreset === key ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => applyPreset(key)}
                  >
                    {PRESETS[key].label}
                  </Badge>
                ))}
              </div>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm">
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="space-y-6">
            {/* Presets (mobile) */}
            <div className="sm:hidden">
              <Label>{t.presets.label}</Label>
              <Select
                value={activePreset}
                onValueChange={(value) => applyPreset(value as PresetKey)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map((key) => (
                    <SelectItem key={key} value={key}>
                      {PRESETS[key].label}
                    </SelectItem>
                  ))}
                  <SelectItem value="custom">{t.presets.custom}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sampling Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <BarChart3 className="h-4 w-4" />
                {t.samplingConfig}
              </div>

              {/* Sample Size */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="sample-size">{t.sampleSize}</Label>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info className="h-3.5 w-3.5 text-muted-foreground" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="max-w-xs text-xs">
                            Maximum rows to sample. Leave empty for all rows.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <Switch
                    checked={config.sampleSize !== null}
                    onCheckedChange={(checked) =>
                      updateConfig({ sampleSize: checked ? 50000 : null })
                    }
                  />
                </div>
                {config.sampleSize !== null && (
                  <Input
                    id="sample-size"
                    type="number"
                    value={config.sampleSize}
                    onChange={(e) =>
                      updateConfig({ sampleSize: parseInt(e.target.value) || 10000 })
                    }
                    min={100}
                    max={10000000}
                    placeholder="50000"
                  />
                )}
              </div>

              {/* Random Seed */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="random-seed">{t.randomSeed}</Label>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-3.5 w-3.5 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs text-xs">{t.tooltips.randomSeed}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <Input
                  id="random-seed"
                  type="number"
                  value={config.randomSeed}
                  onChange={(e) =>
                    updateConfig({ randomSeed: parseInt(e.target.value) || 42 })
                  }
                  min={0}
                  placeholder="42"
                />
              </div>
            </div>

            {/* Feature Toggles */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Zap className="h-4 w-4" />
                Features
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                {/* Include Patterns */}
                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <Label className="text-sm">{t.enablePatternDetection}</Label>
                    <p className="text-xs text-muted-foreground">
                      Detect data patterns
                    </p>
                  </div>
                  <Switch
                    checked={config.includePatterns}
                    onCheckedChange={(checked) =>
                      updateConfig({ includePatterns: checked })
                    }
                  />
                </div>

                {/* Include Distributions */}
                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <Label className="text-sm">{t.includeHistograms}</Label>
                    <p className="text-xs text-muted-foreground">
                      Value distributions
                    </p>
                  </div>
                  <Switch
                    checked={config.includeDistributions}
                    onCheckedChange={(checked) =>
                      updateConfig({ includeDistributions: checked })
                    }
                  />
                </div>

                {/* Include Correlations */}
                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <Label className="text-sm">{t.includeCorrelations}</Label>
                    <p className="text-xs text-muted-foreground">
                      Column correlations
                    </p>
                  </div>
                  <Switch
                    checked={config.includeCorrelations}
                    onCheckedChange={(checked) =>
                      updateConfig({ includeCorrelations: checked })
                    }
                  />
                </div>
              </div>
            </div>

            {/* Pattern Detection Settings */}
            {config.includePatterns && (
              <div className="space-y-4 rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Hash className="h-4 w-4" />
                  {t.patternDetection}
                </div>

                {/* Pattern Sample Size */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>{t.patternSampleSize}</Label>
                    <span className="text-sm text-muted-foreground">
                      {config.patternSampleSize.toLocaleString()}
                    </span>
                  </div>
                  <Slider
                    value={[config.patternSampleSize]}
                    onValueChange={([value]) =>
                      updateConfig({ patternSampleSize: value })
                    }
                    min={100}
                    max={5000}
                    step={100}
                  />
                </div>

                {/* Min Pattern Match Ratio */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>{t.minPatternConfidence}</Label>
                    <span className="text-sm text-muted-foreground">
                      {(config.minPatternMatchRatio * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    value={[config.minPatternMatchRatio]}
                    onValueChange={([value]) =>
                      updateConfig({ minPatternMatchRatio: value })
                    }
                    min={0.5}
                    max={1}
                    step={0.05}
                  />
                </div>
              </div>
            )}

            {/* Correlation Settings */}
            {config.includeCorrelations && (
              <div className="space-y-4 rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Network className="h-4 w-4" />
                  Correlation Settings
                </div>

                {/* Correlation Threshold */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Minimum Correlation</Label>
                    <span className="text-sm text-muted-foreground">
                      {config.correlationThreshold.toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    value={[config.correlationThreshold]}
                    onValueChange={([value]) =>
                      updateConfig({ correlationThreshold: value })
                    }
                    min={0.1}
                    max={0.99}
                    step={0.05}
                  />
                </div>
              </div>
            )}

            {/* Output & Performance */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Settings2 className="h-4 w-4" />
                Output & Performance
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {/* Top N Values */}
                <div className="space-y-2">
                  <Label>Top N Values</Label>
                  <Select
                    value={config.topNValues.toString()}
                    onValueChange={(value) =>
                      updateConfig({ topNValues: parseInt(value) })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[5, 10, 15, 20, 30, 50].map((n) => (
                        <SelectItem key={n} value={n.toString()}>
                          {n}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Parallel Jobs */}
                <div className="space-y-2">
                  <Label>Parallel Workers</Label>
                  <Select
                    value={config.nJobs.toString()}
                    onValueChange={(value) =>
                      updateConfig({ nJobs: parseInt(value) })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[1, 2, 4, 8].map((n) => (
                        <SelectItem key={n} value={n.toString()}>
                          {n} {n === 1 ? 'worker' : 'workers'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-2 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={resetToDefaults}
                className="text-muted-foreground"
              >
                <RotateCcw className="mr-2 h-4 w-4" />
                {t.resetToDefaults}
              </Button>

              {onRunProfile && (
                <Button onClick={handleRunProfile} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <BarChart3 className="mr-2 h-4 w-4 animate-spin" />
                      Profiling...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="mr-2 h-4 w-4" />
                      {t.runProfileWithConfig}
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}

export { DEFAULT_CONFIG as DEFAULT_PROFILE_CONFIG }
export type { PresetKey as ProfilePresetKey }
