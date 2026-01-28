/**
 * ReporterConfigForm - Advanced configuration form for reports.
 *
 * Provides detailed configuration options including:
 * - Title customization
 * - Include/exclude options (samples, statistics, metadata)
 * - Custom options for specific formats
 */

import { useState } from 'react'
import { Settings2, ChevronDown, ChevronRight, Info } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
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
import { cn } from '@/lib/utils'
import type { ReporterConfig, ReportFormatType } from '@/types/reporters'
import { DEFAULT_REPORTER_CONFIG, formatSupportsTheme, formatSupportsI18n } from '@/types/reporters'

interface ReporterConfigFormProps {
  /** Current configuration */
  value: ReporterConfig
  /** Callback when configuration changes */
  onChange: (config: ReporterConfig) => void
  /** Current format (for format-specific options) */
  format?: ReportFormatType
  /** Show as collapsible card */
  collapsible?: boolean
  /** Initial collapsed state */
  defaultCollapsed?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Additional class names */
  className?: string
}

export function ReporterConfigForm({
  value,
  onChange,
  format = 'html',
  collapsible = true,
  defaultCollapsed = true,
  disabled = false,
  className,
}: ReporterConfigFormProps) {
  const [isOpen, setIsOpen] = useState(!defaultCollapsed)

  const handleChange = <K extends keyof ReporterConfig>(
    key: K,
    newValue: ReporterConfig[K]
  ) => {
    onChange({ ...value, [key]: newValue })
  }

  const handleCustomOptionChange = (key: string, optionValue: unknown) => {
    onChange({
      ...value,
      customOptions: {
        ...(value.customOptions || {}),
        [key]: optionValue,
      },
    })
  }

  const handleReset = () => {
    onChange(DEFAULT_REPORTER_CONFIG)
  }

  const content = (
    <div className="space-y-6">
      {/* Title */}
      <div className="space-y-2">
        <Label htmlFor="report-title" className="flex items-center gap-2">
          Report Title
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-3 w-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p>The title displayed at the top of the report</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </Label>
        <Input
          id="report-title"
          value={value.title || ''}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="Validation Report"
          disabled={disabled}
        />
      </div>

      {/* Include Options */}
      <div className="space-y-4">
        <Label className="text-sm font-medium">Include in Report</Label>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="include-samples" className="text-sm font-normal">
                Sample Values
              </Label>
              <p className="text-xs text-muted-foreground">
                Show example values that failed validation
              </p>
            </div>
            <Switch
              id="include-samples"
              checked={value.includeSamples ?? DEFAULT_REPORTER_CONFIG.includeSamples}
              onCheckedChange={(checked) => handleChange('includeSamples', checked)}
              disabled={disabled}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="include-statistics" className="text-sm font-normal">
                Statistics
              </Label>
              <p className="text-xs text-muted-foreground">
                Include summary statistics and metrics
              </p>
            </div>
            <Switch
              id="include-statistics"
              checked={value.includeStatistics ?? DEFAULT_REPORTER_CONFIG.includeStatistics}
              onCheckedChange={(checked) => handleChange('includeStatistics', checked)}
              disabled={disabled}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="include-metadata" className="text-sm font-normal">
                Metadata
              </Label>
              <p className="text-xs text-muted-foreground">
                Include report generation metadata
              </p>
            </div>
            <Switch
              id="include-metadata"
              checked={value.includeMetadata ?? DEFAULT_REPORTER_CONFIG.includeMetadata}
              onCheckedChange={(checked) => handleChange('includeMetadata', checked)}
              disabled={disabled}
            />
          </div>
        </div>
      </div>

      {/* Max Sample Values */}
      <div className="space-y-2">
        <Label htmlFor="max-samples" className="flex items-center gap-2">
          Max Sample Values
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-3 w-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Maximum number of sample values to show per issue</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </Label>
        <Input
          id="max-samples"
          type="number"
          min={1}
          max={50}
          value={value.maxSampleValues ?? DEFAULT_REPORTER_CONFIG.maxSampleValues}
          onChange={(e) => handleChange('maxSampleValues', parseInt(e.target.value, 10))}
          disabled={disabled || !(value.includeSamples ?? true)}
          className="w-24"
        />
      </div>

      {/* Timestamp Format */}
      <div className="space-y-2">
        <Label htmlFor="timestamp-format" className="flex items-center gap-2">
          Timestamp Format
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-3 w-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Python strftime format string for dates</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </Label>
        <Input
          id="timestamp-format"
          value={value.timestampFormat ?? DEFAULT_REPORTER_CONFIG.timestampFormat}
          onChange={(e) => handleChange('timestampFormat', e.target.value)}
          placeholder="%Y-%m-%d %H:%M:%S"
          disabled={disabled}
          className="font-mono text-sm"
        />
      </div>

      {/* Format-specific options */}
      {format === 'html' && (
        <div className="space-y-4 pt-4 border-t">
          <Label className="text-sm font-medium">HTML Options</Label>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="inline-css" className="text-sm font-normal">
                Inline CSS
              </Label>
              <p className="text-xs text-muted-foreground">
                Embed styles in the HTML file
              </p>
            </div>
            <Switch
              id="inline-css"
              checked={value.customOptions?.inlineCss as boolean ?? true}
              onCheckedChange={(checked) => handleCustomOptionChange('inlineCss', checked)}
              disabled={disabled}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="include-charts" className="text-sm font-normal">
                Include Charts
              </Label>
              <p className="text-xs text-muted-foreground">
                Add visual charts for statistics
              </p>
            </div>
            <Switch
              id="include-charts"
              checked={value.customOptions?.includeCharts as boolean ?? false}
              onCheckedChange={(checked) => handleCustomOptionChange('includeCharts', checked)}
              disabled={disabled}
            />
          </div>
        </div>
      )}

      {format === 'json' && (
        <div className="space-y-4 pt-4 border-t">
          <Label className="text-sm font-medium">JSON Options</Label>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="indent" className="text-sm font-normal">
                Pretty Print
              </Label>
              <p className="text-xs text-muted-foreground">
                Format JSON with indentation
              </p>
            </div>
            <Switch
              id="indent"
              checked={(value.customOptions?.indent as number ?? 2) > 0}
              onCheckedChange={(checked) =>
                handleCustomOptionChange('indent', checked ? 2 : 0)
              }
              disabled={disabled}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="sort-keys" className="text-sm font-normal">
                Sort Keys
              </Label>
              <p className="text-xs text-muted-foreground">
                Sort object keys alphabetically
              </p>
            </div>
            <Switch
              id="sort-keys"
              checked={value.customOptions?.sortKeys as boolean ?? false}
              onCheckedChange={(checked) => handleCustomOptionChange('sortKeys', checked)}
              disabled={disabled}
            />
          </div>
        </div>
      )}

      {format === 'csv' && (
        <div className="space-y-4 pt-4 border-t">
          <Label className="text-sm font-medium">CSV Options</Label>

          <div className="space-y-2">
            <Label htmlFor="delimiter" className="text-sm font-normal">
              Delimiter
            </Label>
            <Input
              id="delimiter"
              value={value.customOptions?.delimiter as string ?? ','}
              onChange={(e) => handleCustomOptionChange('delimiter', e.target.value)}
              placeholder=","
              disabled={disabled}
              className="w-16"
              maxLength={1}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="include-header" className="text-sm font-normal">
                Include Header
              </Label>
              <p className="text-xs text-muted-foreground">
                Add column headers as first row
              </p>
            </div>
            <Switch
              id="include-header"
              checked={value.customOptions?.includeHeader as boolean ?? true}
              onCheckedChange={(checked) => handleCustomOptionChange('includeHeader', checked)}
              disabled={disabled}
            />
          </div>
        </div>
      )}


      {/* Reset Button */}
      <div className="pt-4 border-t">
        <Button
          variant="outline"
          size="sm"
          onClick={handleReset}
          disabled={disabled}
        >
          Reset to Defaults
        </Button>
      </div>
    </div>
  )

  if (!collapsible) {
    return <div className={className}>{content}</div>
  }

  return (
    <Card className={className}>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Settings2 className="h-5 w-5" />
                <div>
                  <CardTitle className="text-base">Advanced Options</CardTitle>
                  <CardDescription>
                    Configure report generation settings
                  </CardDescription>
                </div>
              </div>
              {isOpen ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent>{content}</CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}
