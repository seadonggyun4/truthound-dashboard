/**
 * Enterprise Sampling Configuration Component.
 *
 * Provides a comprehensive UI for configuring enterprise-scale sampling
 * operations on 100M+ row datasets.
 *
 * Features:
 * - Strategy selection (Block, Multi-Stage, Column-Aware, Progressive)
 * - Quality presets (Sketch, Quick, Standard, High, Exact)
 * - Memory budget configuration
 * - Parallel processing settings
 * - Real-time sample size estimation
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  AlertTriangle,
  ChevronDown,
  Clock,
  Cpu,
  Database,
  HelpCircle,
  Layers,
  MemoryStick,
  Settings2,
  Sparkles,
  Zap,
} from 'lucide-react'
import type {
  BlockSamplingConfig,
  ColumnAwareSamplingConfig,
  EnterpriseSamplingRequest,
  EnterpriseSamplingStrategy,
  MultiStageSamplingConfig,
  ProgressiveSamplingConfig,
  SampleSizeEstimateResponse,
  SamplingQuality,
  ScaleCategory,
} from '@/api/modules/enterprise-sampling'
import {
  classifyDatasetScale,
  DEFAULT_SAMPLING_CONFIG,
  formatDuration,
  formatMemory,
  formatRowCount,
  getRecommendedStrategy,
} from '@/api/modules/enterprise-sampling'

// ============================================================================
// Types
// ============================================================================

export interface EnterpriseSamplingConfigData {
  enabled: boolean
  quality: SamplingQuality
  strategy: EnterpriseSamplingStrategy
  targetRows: number
  confidenceLevel: number
  marginOfError: number
  seed: number | null

  // Memory settings
  maxMemoryMb: number
  backpressureEnabled: boolean

  // Block sampling
  blockSize: number
  samplesPerBlock: number | null
  maxWorkers: number

  // Multi-stage
  numStages: number
  earlyStopEnabled: boolean

  // Column-aware
  stringMultiplier: number
  categoricalMultiplier: number
  complexMultiplier: number

  // Progressive
  convergenceThreshold: number
  progressiveMaxStages: number
  initialSampleRatio: number
  growthFactor: number
}

interface EnterpriseSamplingConfigProps {
  config: EnterpriseSamplingConfigData
  onChange: (config: EnterpriseSamplingConfigData) => void
  estimate?: SampleSizeEstimateResponse | null
  populationSize?: number
  columns?: string[]
  onEstimateRequest?: () => void
}

// ============================================================================
// Default Values
// ============================================================================

export const DEFAULT_ENTERPRISE_CONFIG: EnterpriseSamplingConfigData = {
  enabled: false,
  quality: 'standard',
  strategy: 'adaptive',
  targetRows: 100_000,
  confidenceLevel: 0.95,
  marginOfError: 0.05,
  seed: null,

  maxMemoryMb: 1024,
  backpressureEnabled: true,

  blockSize: 0,
  samplesPerBlock: null,
  maxWorkers: 4,

  numStages: 3,
  earlyStopEnabled: true,

  stringMultiplier: 2.0,
  categoricalMultiplier: 0.5,
  complexMultiplier: 3.0,

  convergenceThreshold: 0.01,
  progressiveMaxStages: 5,
  initialSampleRatio: 0.01,
  growthFactor: 2.0,
}

// ============================================================================
// Strategy Definitions
// ============================================================================

const STRATEGIES: Array<{
  value: EnterpriseSamplingStrategy
  icon: React.ReactNode
  bestFor: string
}> = [
  {
    value: 'adaptive',
    icon: <Sparkles className="h-4 w-4" />,
    bestFor: 'Auto-selection based on data',
  },
  {
    value: 'block',
    icon: <Layers className="h-4 w-4" />,
    bestFor: '10M-100M rows, parallel processing',
  },
  {
    value: 'multi_stage',
    icon: <Database className="h-4 w-4" />,
    bestFor: '100M-1B rows, hierarchical sampling',
  },
  {
    value: 'column_aware',
    icon: <Settings2 className="h-4 w-4" />,
    bestFor: 'Mixed column types',
  },
  {
    value: 'progressive',
    icon: <Zap className="h-4 w-4" />,
    bestFor: 'Early stopping, convergence detection',
  },
]

const QUALITY_PRESETS: Array<{
  value: SamplingQuality
  rows: string
  confidence: string
}> = [
  { value: 'sketch', rows: '10K', confidence: '80%' },
  { value: 'quick', rows: '50K', confidence: '90%' },
  { value: 'standard', rows: '100K', confidence: '95%' },
  { value: 'high', rows: '500K', confidence: '99%' },
  { value: 'exact', rows: 'Full', confidence: '100%' },
]

// ============================================================================
// Component
// ============================================================================

export function EnterpriseSamplingConfig({
  config,
  onChange,
  estimate,
  populationSize,
  columns = [],
  onEstimateRequest,
}: EnterpriseSamplingConfigProps) {
  const t = useIntlayer('enterpriseSampling')
  const [advancedOpen, setAdvancedOpen] = useState(false)

  const updateConfig = useCallback(
    (updates: Partial<EnterpriseSamplingConfigData>) => {
      onChange({ ...config, ...updates })
    },
    [config, onChange]
  )

  // Determine scale category if population size is known
  const scaleCategory = populationSize ? classifyDatasetScale(populationSize) : null
  const isLargeDataset = scaleCategory && ['large', 'xlarge', 'xxlarge'].includes(scaleCategory)
  const recommendedStrategy = scaleCategory ? getRecommendedStrategy(scaleCategory) : 'adaptive'

  // Auto-enable sampling for large datasets
  useEffect(() => {
    if (isLargeDataset && !config.enabled) {
      updateConfig({ enabled: true })
    }
  }, [isLargeDataset, config.enabled, updateConfig])

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              {t.title}
            </CardTitle>
            <CardDescription>{t.description}</CardDescription>
          </div>
          <Switch
            checked={config.enabled}
            onCheckedChange={(enabled) => updateConfig({ enabled })}
          />
        </div>
      </CardHeader>

      {config.enabled && (
        <CardContent className="space-y-6">
          {/* Scale Category Warning */}
          {isLargeDataset && populationSize && (
            <div className="flex items-start gap-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-yellow-500" />
              <div className="text-sm">
                <div className="font-medium text-yellow-600 dark:text-yellow-400">
                  {t.largeDatasetDetected}
                </div>
                <div className="text-muted-foreground">
                  {t.largeDatasetDescription
                    .replace('{rows}', formatRowCount(populationSize))
                    .replace('{scale}', scaleCategory || 'unknown')}
                </div>
              </div>
            </div>
          )}

          {/* Estimation Summary */}
          {estimate && (
            <div className="grid grid-cols-4 gap-4 rounded-lg bg-muted/50 p-4">
              <div className="text-center">
                <Database className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                <div className="text-lg font-semibold">
                  {formatRowCount(estimate.recommended_size)}
                </div>
                <div className="text-xs text-muted-foreground">{t.recommendedSamples}</div>
              </div>
              <div className="text-center">
                <Clock className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                <div className="text-lg font-semibold">
                  {formatDuration(estimate.estimated_time_seconds)}
                </div>
                <div className="text-xs text-muted-foreground">{t.estimatedTime}</div>
              </div>
              <div className="text-center">
                <MemoryStick className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                <div className="text-lg font-semibold">
                  {formatMemory(estimate.estimated_memory_mb)}
                </div>
                <div className="text-xs text-muted-foreground">{t.estimatedMemory}</div>
              </div>
              <div className="text-center">
                <Zap className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                <div className="text-lg font-semibold">{estimate.speedup_factor.toFixed(0)}x</div>
                <div className="text-xs text-muted-foreground">{t.speedup}</div>
              </div>
            </div>
          )}

          <Tabs defaultValue="basic" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="basic">{t.tabs.basic}</TabsTrigger>
              <TabsTrigger value="strategy">{t.tabs.strategy}</TabsTrigger>
              <TabsTrigger value="advanced">{t.tabs.advanced}</TabsTrigger>
            </TabsList>

            {/* Basic Tab */}
            <TabsContent value="basic" className="space-y-4">
              {/* Quality Preset */}
              <div className="space-y-2">
                <Label>{t.qualityPreset}</Label>
                <div className="grid grid-cols-5 gap-2">
                  {QUALITY_PRESETS.map((preset) => (
                    <Button
                      key={preset.value}
                      variant={config.quality === preset.value ? 'default' : 'outline'}
                      size="sm"
                      className="flex-col h-auto py-2"
                      onClick={() => updateConfig({ quality: preset.value })}
                    >
                      <span className="text-xs font-medium capitalize">{preset.value}</span>
                      <span className="text-[10px] text-muted-foreground">{preset.rows}</span>
                    </Button>
                  ))}
                </div>
              </div>

              {/* Target Rows */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{t.targetRows}</Label>
                  <Badge variant="secondary">{formatRowCount(config.targetRows)}</Badge>
                </div>
                <Input
                  type="number"
                  value={config.targetRows}
                  onChange={(e) =>
                    updateConfig({ targetRows: Math.max(1000, parseInt(e.target.value) || 100000) })
                  }
                  min={1000}
                  max={10_000_000}
                />
              </div>

              {/* Confidence Level */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{t.confidenceLevel}</Label>
                  <span className="text-sm font-medium">
                    {(config.confidenceLevel * 100).toFixed(0)}%
                  </span>
                </div>
                <Select
                  value={config.confidenceLevel.toString()}
                  onValueChange={(value) => updateConfig({ confidenceLevel: parseFloat(value) })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.90">90%</SelectItem>
                    <SelectItem value="0.95">95% (Recommended)</SelectItem>
                    <SelectItem value="0.99">99%</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Margin of Error */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{t.marginOfError}</Label>
                  <span className="text-sm font-medium">
                    {(config.marginOfError * 100).toFixed(0)}%
                  </span>
                </div>
                <Slider
                  value={[config.marginOfError]}
                  onValueChange={([value]) => updateConfig({ marginOfError: value })}
                  min={0.01}
                  max={0.1}
                  step={0.01}
                />
              </div>
            </TabsContent>

            {/* Strategy Tab */}
            <TabsContent value="strategy" className="space-y-4">
              {/* Strategy Selection */}
              <div className="space-y-2">
                <Label>{t.strategy}</Label>
                <div className="grid grid-cols-1 gap-2">
                  {STRATEGIES.map((strategy) => (
                    <Button
                      key={strategy.value}
                      variant={config.strategy === strategy.value ? 'default' : 'outline'}
                      className="justify-start h-auto py-3"
                      onClick={() => updateConfig({ strategy: strategy.value })}
                    >
                      <div className="flex items-center gap-3">
                        {strategy.icon}
                        <div className="text-left">
                          <div className="font-medium capitalize">
                            {strategy.value.replace('_', ' ')}
                            {strategy.value === recommendedStrategy && (
                              <Badge variant="secondary" className="ml-2 text-xs">
                                {t.recommended}
                              </Badge>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground">{strategy.bestFor}</div>
                        </div>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>

              {/* Strategy-specific settings */}
              {config.strategy === 'block' && (
                <div className="space-y-4 rounded-lg border p-4">
                  <div className="text-sm font-medium">{t.blockSettings}</div>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.blockSize}</Label>
                        <span className="text-sm text-muted-foreground">
                          {config.blockSize === 0 ? 'Auto' : formatRowCount(config.blockSize)}
                        </span>
                      </div>
                      <Input
                        type="number"
                        value={config.blockSize}
                        onChange={(e) =>
                          updateConfig({ blockSize: Math.max(0, parseInt(e.target.value) || 0) })
                        }
                        placeholder="0 = Auto-detect"
                        min={0}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.maxWorkers}</Label>
                        <span className="text-sm text-muted-foreground">{config.maxWorkers}</span>
                      </div>
                      <Slider
                        value={[config.maxWorkers]}
                        onValueChange={([value]) => updateConfig({ maxWorkers: value })}
                        min={1}
                        max={16}
                        step={1}
                      />
                    </div>
                  </div>
                </div>
              )}

              {config.strategy === 'multi_stage' && (
                <div className="space-y-4 rounded-lg border p-4">
                  <div className="text-sm font-medium">{t.multiStageSettings}</div>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.numStages}</Label>
                        <span className="text-sm text-muted-foreground">{config.numStages}</span>
                      </div>
                      <Slider
                        value={[config.numStages]}
                        onValueChange={([value]) => updateConfig({ numStages: value })}
                        min={2}
                        max={5}
                        step={1}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="text-sm">{t.earlyStop}</Label>
                      <Switch
                        checked={config.earlyStopEnabled}
                        onCheckedChange={(enabled) => updateConfig({ earlyStopEnabled: enabled })}
                      />
                    </div>
                  </div>
                </div>
              )}

              {config.strategy === 'column_aware' && (
                <div className="space-y-4 rounded-lg border p-4">
                  <div className="text-sm font-medium">{t.columnAwareSettings}</div>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.stringMultiplier}</Label>
                        <span className="text-sm text-muted-foreground">
                          {config.stringMultiplier}x
                        </span>
                      </div>
                      <Slider
                        value={[config.stringMultiplier]}
                        onValueChange={([value]) => updateConfig({ stringMultiplier: value })}
                        min={1}
                        max={5}
                        step={0.5}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.categoricalMultiplier}</Label>
                        <span className="text-sm text-muted-foreground">
                          {config.categoricalMultiplier}x
                        </span>
                      </div>
                      <Slider
                        value={[config.categoricalMultiplier]}
                        onValueChange={([value]) => updateConfig({ categoricalMultiplier: value })}
                        min={0.1}
                        max={2}
                        step={0.1}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.complexMultiplier}</Label>
                        <span className="text-sm text-muted-foreground">
                          {config.complexMultiplier}x
                        </span>
                      </div>
                      <Slider
                        value={[config.complexMultiplier]}
                        onValueChange={([value]) => updateConfig({ complexMultiplier: value })}
                        min={1}
                        max={10}
                        step={0.5}
                      />
                    </div>
                  </div>
                </div>
              )}

              {config.strategy === 'progressive' && (
                <div className="space-y-4 rounded-lg border p-4">
                  <div className="text-sm font-medium">{t.progressiveSettings}</div>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.convergenceThreshold}</Label>
                        <span className="text-sm text-muted-foreground">
                          {(config.convergenceThreshold * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Slider
                        value={[config.convergenceThreshold]}
                        onValueChange={([value]) => updateConfig({ convergenceThreshold: value })}
                        min={0.001}
                        max={0.1}
                        step={0.001}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">{t.growthFactor}</Label>
                        <span className="text-sm text-muted-foreground">
                          {config.growthFactor}x
                        </span>
                      </div>
                      <Slider
                        value={[config.growthFactor]}
                        onValueChange={([value]) => updateConfig({ growthFactor: value })}
                        min={1.5}
                        max={4}
                        step={0.5}
                      />
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>

            {/* Advanced Tab */}
            <TabsContent value="advanced" className="space-y-4">
              {/* Memory Settings */}
              <div className="space-y-4 rounded-lg border p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <MemoryStick className="h-4 w-4" />
                  {t.memorySettings}
                </div>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm">{t.maxMemory}</Label>
                      <span className="text-sm text-muted-foreground">
                        {formatMemory(config.maxMemoryMb)}
                      </span>
                    </div>
                    <Slider
                      value={[config.maxMemoryMb]}
                      onValueChange={([value]) => updateConfig({ maxMemoryMb: value })}
                      min={256}
                      max={8192}
                      step={256}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Label className="text-sm">{t.backpressure}</Label>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <HelpCircle className="h-3 w-3 text-muted-foreground" />
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="max-w-xs text-xs">{t.backpressureTooltip}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <Switch
                      checked={config.backpressureEnabled}
                      onCheckedChange={(enabled) =>
                        updateConfig({ backpressureEnabled: enabled })
                      }
                    />
                  </div>
                </div>
              </div>

              {/* Reproducibility */}
              <div className="space-y-4 rounded-lg border p-4">
                <div className="text-sm font-medium">{t.reproducibility}</div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">{t.randomSeed}</Label>
                    <Switch
                      checked={config.seed !== null}
                      onCheckedChange={(enabled) =>
                        updateConfig({ seed: enabled ? 42 : null })
                      }
                    />
                  </div>
                  {config.seed !== null && (
                    <Input
                      type="number"
                      value={config.seed}
                      onChange={(e) =>
                        updateConfig({ seed: parseInt(e.target.value) || 42 })
                      }
                      min={0}
                    />
                  )}
                </div>
              </div>

              {/* Estimate Button */}
              {onEstimateRequest && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={onEstimateRequest}
                >
                  <Cpu className="mr-2 h-4 w-4" />
                  {t.estimateSize}
                </Button>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      )}
    </Card>
  )
}

// ============================================================================
// Helper Functions for Converting Config
// ============================================================================

/**
 * Convert UI config to API request format.
 */
export function configToRequest(
  sourceId: string,
  config: EnterpriseSamplingConfigData
): EnterpriseSamplingRequest {
  const request: EnterpriseSamplingRequest = {
    source_id: sourceId,
    target_rows: config.targetRows,
    quality: config.quality,
    strategy: config.strategy,
    confidence_level: config.confidenceLevel,
    margin_of_error: config.marginOfError,
    seed: config.seed,
    memory_budget: {
      max_memory_mb: config.maxMemoryMb,
      backpressure_enabled: config.backpressureEnabled,
    },
  }

  // Add strategy-specific config
  if (config.strategy === 'block') {
    request.block_config = {
      block_size: config.blockSize,
      sample_per_block: config.samplesPerBlock,
      parallel: {
        max_workers: config.maxWorkers,
      },
    }
  } else if (config.strategy === 'multi_stage') {
    request.multi_stage_config = {
      num_stages: config.numStages,
      early_stop_enabled: config.earlyStopEnabled,
    }
  } else if (config.strategy === 'column_aware') {
    request.column_aware_config = {
      string_multiplier: config.stringMultiplier,
      categorical_multiplier: config.categoricalMultiplier,
      complex_multiplier: config.complexMultiplier,
    }
  } else if (config.strategy === 'progressive') {
    request.progressive_config = {
      convergence_threshold: config.convergenceThreshold,
      max_stages: config.progressiveMaxStages,
      initial_sample_ratio: config.initialSampleRatio,
      growth_factor: config.growthFactor,
    }
  }

  return request
}

export default EnterpriseSamplingConfig
