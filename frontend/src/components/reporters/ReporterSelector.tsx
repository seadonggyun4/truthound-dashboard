/**
 * ReporterSelector - Format and configuration selector for reports.
 *
 * Provides UI for selecting report format, theme, and locale with
 * visual feedback and format-specific options.
 */

import { useState, useEffect, useCallback } from 'react'
import { Check, ChevronDown, Palette, Globe, Settings2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { FormatIcon } from './FormatIcon'
import type {
  ReportFormatType,
  ReportThemeType,
  ReportLocale,
  ReporterConfig,
  LocaleInfo,
} from '@/types/reporters'
import {
  REPORT_FORMATS,
  REPORT_THEMES,
  REPORT_LOCALES,
  getFormatInfo,
  formatSupportsTheme,
  formatSupportsI18n,
  createDefaultConfig,
} from '@/types/reporters'
import { getReportFormats, getReportLocales } from '@/api/modules/reports'

interface ReporterSelectorProps {
  /** Current configuration */
  value: ReporterConfig
  /** Callback when configuration changes */
  onChange: (config: ReporterConfig) => void
  /** Selected format */
  format: ReportFormatType
  /** Callback when format changes */
  onFormatChange: (format: ReportFormatType) => void
  /** Show format selector */
  showFormatSelector?: boolean
  /** Show theme selector */
  showThemeSelector?: boolean
  /** Show locale selector */
  showLocaleSelector?: boolean
  /** Show advanced options */
  showAdvancedOptions?: boolean
  /** Compact mode (inline selectors) */
  compact?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Additional class names */
  className?: string
}

export function ReporterSelector({
  value,
  onChange,
  format,
  onFormatChange,
  showFormatSelector = true,
  showThemeSelector = true,
  showLocaleSelector = true,
  showAdvancedOptions = false,
  compact = false,
  disabled = false,
  className,
}: ReporterSelectorProps) {
  const [availableFormats, setAvailableFormats] = useState<string[]>([])
  const [availableLocales, setAvailableLocales] = useState<LocaleInfo[]>(REPORT_LOCALES)
  const [isLoading, setIsLoading] = useState(false)

  // Fetch available formats and locales from server
  const fetchAvailableOptions = useCallback(async () => {
    setIsLoading(true)
    try {
      const [formatsResponse, localesResponse] = await Promise.all([
        getReportFormats(),
        getReportLocales(),
      ])
      setAvailableFormats(formatsResponse.formats)
      if (localesResponse.length > 0) {
        setAvailableLocales(
          localesResponse.map((l) => ({
            code: (l as unknown as { code: string }).code as ReportLocale,
            englishName: (l as unknown as { englishName?: string; english_name?: string }).englishName || (l as unknown as { english_name?: string }).english_name || '',
            nativeName: (l as unknown as { nativeName?: string; native_name?: string }).nativeName || (l as unknown as { native_name?: string }).native_name || '',
            flag: (l as unknown as { flag: string }).flag || '',
            rtl: (l as unknown as { rtl: boolean }).rtl || false,
          }))
        )
      }
    } catch (error) {
      // Use defaults on error
      console.error('Failed to fetch available formats:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAvailableOptions()
  }, [fetchAvailableOptions])

  const formatInfo = getFormatInfo(format)
  const showTheme = showThemeSelector && formatSupportsTheme(format)
  const showLocale = showLocaleSelector && formatSupportsI18n(format)

  const handleFormatChange = (newFormat: ReportFormatType) => {
    onFormatChange(newFormat)
    // Reset theme and locale if not supported by new format
    const newConfig = { ...value }
    if (!formatSupportsTheme(newFormat)) {
      newConfig.theme = undefined
    }
    if (!formatSupportsI18n(newFormat)) {
      newConfig.locale = undefined
    }
    onChange(newConfig)
  }

  const handleThemeChange = (theme: ReportThemeType) => {
    onChange({ ...value, theme })
  }

  const handleLocaleChange = (locale: ReportLocale) => {
    onChange({ ...value, locale })
  }

  // Filter formats to only available ones
  const displayFormats = REPORT_FORMATS.filter(
    (f) => availableFormats.length === 0 || availableFormats.includes(f.value)
  )

  if (compact) {
    return (
      <div className={cn('flex flex-wrap gap-2 items-center', className)}>
        {showFormatSelector && (
          <Select
            value={format}
            onValueChange={(v) => handleFormatChange(v as ReportFormatType)}
            disabled={disabled || isLoading}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Format" />
            </SelectTrigger>
            <SelectContent>
              {displayFormats.map((f) => (
                <SelectItem key={f.value} value={f.value}>
                  <div className="flex items-center gap-2">
                    <FormatIcon format={f.value} className="h-4 w-4" />
                    <span>{f.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {showTheme && (
          <Select
            value={value.theme || 'professional'}
            onValueChange={(v) => handleThemeChange(v as ReportThemeType)}
            disabled={disabled}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Theme" />
            </SelectTrigger>
            <SelectContent>
              {REPORT_THEMES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  <div className="flex items-center gap-2">
                    <Palette className="h-4 w-4" />
                    <span>{t.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {showLocale && (
          <Select
            value={value.locale || 'en'}
            onValueChange={(v) => handleLocaleChange(v as ReportLocale)}
            disabled={disabled}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Language" />
            </SelectTrigger>
            <SelectContent>
              {availableLocales.map((l) => (
                <SelectItem key={l.code} value={l.code}>
                  <div className="flex items-center gap-2">
                    <span>{l.flag}</span>
                    <span>{l.englishName}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Format Selection */}
      {showFormatSelector && (
        <div className="space-y-2">
          <label className="text-sm font-medium">Report Format</label>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {displayFormats.map((f) => (
              <Button
                key={f.value}
                variant={format === f.value ? 'default' : 'outline'}
                className={cn(
                  'h-auto py-3 px-4 justify-start',
                  format === f.value && 'ring-2 ring-primary'
                )}
                onClick={() => handleFormatChange(f.value)}
                disabled={disabled || isLoading}
              >
                <div className="flex items-center gap-3">
                  <FormatIcon format={f.value} className="h-5 w-5" />
                  <div className="text-left">
                    <div className="font-medium">{f.label}</div>
                    <div className="text-xs text-muted-foreground">{f.extension}</div>
                  </div>
                  {format === f.value && (
                    <Check className="h-4 w-4 ml-auto" />
                  )}
                </div>
              </Button>
            ))}
          </div>
          {formatInfo && (
            <p className="text-sm text-muted-foreground mt-1">
              {formatInfo.description}
            </p>
          )}
        </div>
      )}

      {/* Theme Selection */}
      {showTheme && (
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <Palette className="h-4 w-4" />
            Theme
          </label>
          <div className="flex flex-wrap gap-2">
            {REPORT_THEMES.map((t) => (
              <Button
                key={t.value}
                variant={value.theme === t.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleThemeChange(t.value)}
                disabled={disabled}
              >
                {t.label}
                {value.theme === t.value && (
                  <Check className="h-3 w-3 ml-1" />
                )}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Locale Selection */}
      {showLocale && (
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Language
          </label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                className="w-[200px] justify-between"
                disabled={disabled}
              >
                {value.locale ? (
                  <span className="flex items-center gap-2">
                    <span>
                      {availableLocales.find((l) => l.code === value.locale)?.flag}
                    </span>
                    <span>
                      {availableLocales.find((l) => l.code === value.locale)?.englishName}
                    </span>
                  </span>
                ) : (
                  'Select language...'
                )}
                <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px] p-0">
              <div className="max-h-[300px] overflow-y-auto">
                {availableLocales.map((locale) => (
                  <Button
                    key={locale.code}
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => handleLocaleChange(locale.code)}
                  >
                    <span className="mr-2">{locale.flag}</span>
                    <span className="flex-1 text-left">{locale.englishName}</span>
                    {value.locale === locale.code && (
                      <Check className="h-4 w-4" />
                    )}
                  </Button>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        </div>
      )}

      {/* Format-specific badges */}
      {formatInfo && (
        <div className="flex flex-wrap gap-2">
          {formatInfo.supportsTheme && (
            <Badge variant="secondary">
              <Palette className="h-3 w-3 mr-1" />
              Themeable
            </Badge>
          )}
          {formatInfo.supportsI18n && (
            <Badge variant="secondary">
              <Globe className="h-3 w-3 mr-1" />
              Multi-language
            </Badge>
          )}
          {formatInfo.requiresDependency && (
            <Badge variant="outline">
              Requires: {formatInfo.requiresDependency}
            </Badge>
          )}
        </div>
      )}
    </div>
  )
}
