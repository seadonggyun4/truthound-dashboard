/**
 * Report Download Button component
 *
 * Provides a dropdown button for downloading validation reports
 * in multiple formats (HTML, CSV, JSON) with theme selection.
 * Supports 15 languages for report content (per truthound documentation).
 * Also supports custom reporters from the plugin system.
 */

import { useState, useEffect, useRef, useCallback, useSyncExternalStore } from 'react'
import { Download, FileText, FileSpreadsheet, FileJson, ChevronDown, Loader2, Globe } from 'lucide-react'
import { useIntlayer } from '@/providers'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  downloadValidationReport,
  getReportLocales,
  type ReportFormat,
  type ReportTheme,
  type ReportLocale,
  type LocaleInfo,
} from '@/api/modules/reports'
import { listCustomReporters, type CustomReporter } from '@/api/modules/plugins'
import { CustomReporterSection } from './CustomReporterSection'

export interface ReportDownloadButtonProps {
  validationId: string
  disabled?: boolean
  className?: string
}

const FORMAT_ICONS: Record<ReportFormat, typeof FileText> = {
  html: FileText,
  csv: FileSpreadsheet,
  json: FileJson,
}

const FORMAT_LABELS: Record<ReportFormat, string> = {
  html: 'HTML',
  csv: 'CSV',
  json: 'JSON',
}

const THEME_LABELS: Record<ReportTheme, string> = {
  light: 'Light',
  dark: 'Dark',
  professional: 'Professional',
  minimal: 'Minimal',
  high_contrast: 'High Contrast',
}

const FORMATS: ReportFormat[] = ['html', 'csv', 'json']
const THEMES: ReportTheme[] = ['professional', 'light', 'dark', 'minimal', 'high_contrast']

// Default locales in case API call fails
const DEFAULT_LOCALES: LocaleInfo[] = [
  { code: 'en', english_name: 'English', native_name: 'English', flag: '🇺🇸', rtl: false },
  { code: 'ko', english_name: 'Korean', native_name: '한국어', flag: '🇰🇷', rtl: false },
  { code: 'ja', english_name: 'Japanese', native_name: '日本語', flag: '🇯🇵', rtl: false },
  { code: 'zh', english_name: 'Chinese', native_name: '中文', flag: '🇨🇳', rtl: false },
  { code: 'de', english_name: 'German', native_name: 'Deutsch', flag: '🇩🇪', rtl: false },
  { code: 'fr', english_name: 'French', native_name: 'Français', flag: '🇫🇷', rtl: false },
  { code: 'es', english_name: 'Spanish', native_name: 'Español', flag: '🇪🇸', rtl: false },
  { code: 'pt', english_name: 'Portuguese', native_name: 'Português', flag: '🇧🇷', rtl: false },
  { code: 'it', english_name: 'Italian', native_name: 'Italiano', flag: '🇮🇹', rtl: false },
  { code: 'ru', english_name: 'Russian', native_name: 'Русский', flag: '🇷🇺', rtl: false },
  { code: 'ar', english_name: 'Arabic', native_name: 'العربية', flag: '🇸🇦', rtl: true },
  { code: 'th', english_name: 'Thai', native_name: 'ไทย', flag: '🇹🇭', rtl: false },
  { code: 'vi', english_name: 'Vietnamese', native_name: 'Tiếng Việt', flag: '🇻🇳', rtl: false },
  { code: 'id', english_name: 'Indonesian', native_name: 'Bahasa Indonesia', flag: '🇮🇩', rtl: false },
  { code: 'tr', english_name: 'Turkish', native_name: 'Türkçe', flag: '🇹🇷', rtl: false },
]

/**
 * Module-level store for async data (locales + custom reporters).
 *
 * By keeping this outside React state, async API responses never trigger
 * re-renders on the DropdownMenu tree, which would cause Radix UI's
 * DropdownMenuSub to lose its internal open state and close immediately.
 *
 * We use useSyncExternalStore so the component picks up the initial snapshot
 * synchronously and only re-renders once (when data arrives before the
 * dropdown is opened by the user).
 */
let _locales: LocaleInfo[] = DEFAULT_LOCALES
let _customReporters: CustomReporter[] = []
let _dataVersion = 0
let _dataLoaded = false
const _listeners = new Set<() => void>()

function subscribeData(cb: () => void) {
  _listeners.add(cb)
  return () => { _listeners.delete(cb) }
}
function getDataSnapshot() { return _dataVersion }

function _notifyListeners() {
  _dataVersion++
  _listeners.forEach((cb) => cb())
}

// Fetch once at module load time (runs before any dropdown interaction)
if (!_dataLoaded) {
  _dataLoaded = true
  getReportLocales()
    .then((data) => { _locales = data; _notifyListeners() })
    .catch(() => {})
  listCustomReporters({ is_enabled: true })
    .then((result) => { _customReporters = result.data; _notifyListeners() })
    .catch(() => {})
}

export function ReportDownloadButton({
  validationId,
  disabled = false,
  className,
}: ReportDownloadButtonProps) {
  const reports = useIntlayer('reports')
  const common = useIntlayer('common')
  const { toast } = useToast()
  const [isDownloading, setIsDownloading] = useState(false)
  const [selectedLocale, setSelectedLocale] = useState<ReportLocale>('en')

  // Subscribe to module-level data store without causing re-renders
  // while the dropdown is open (data is loaded at module init time)
  useSyncExternalStore(subscribeData, getDataSnapshot)

  // Read current values from module-level store
  const locales = _locales
  const customReporters = _customReporters

  const handleDownload = async (format: ReportFormat, theme?: ReportTheme, locale?: ReportLocale) => {
    setIsDownloading(true)
    try {
      const blob = await downloadValidationReport(validationId, {
        format,
        theme: theme || 'professional',
        locale: locale || selectedLocale,
      })

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const ext = format
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      a.download = `validation_report_${timestamp}.${ext}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      toast({
        title: str(reports.downloadSuccess),
        description: `${FORMAT_LABELS[format]} ${str(reports.reportDownloaded)}`,
      })
    } catch (error) {
      console.error('Failed to download report:', error)
      toast({
        title: str(common.error),
        description: str(reports.downloadFailed),
        variant: 'destructive',
      })
    } finally {
      setIsDownloading(false)
    }
  }

  // Get selected locale info for display
  const selectedLocaleInfo = locales.find(l => l.code === selectedLocale) || locales[0]

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled || isDownloading}
          className={className}
        >
          {isDownloading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          {reports.downloadReport}
          <ChevronDown className="ml-2 h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        {/* Language Selection - at the top */}
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>
            <Globe className="mr-2 h-4 w-4" />
            <span className="flex-1">{reports.selectLanguage}</span>
            <span className="ml-2 text-xs text-muted-foreground">
              {selectedLocaleInfo?.flag} {selectedLocaleInfo?.native_name}
            </span>
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent className="max-h-80 overflow-y-auto">
            <DropdownMenuLabel>{reports.selectLanguage}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {locales.map((locale) => (
              <DropdownMenuItem
                key={locale.code}
                onClick={() => setSelectedLocale(locale.code)}
                className={selectedLocale === locale.code ? 'bg-accent' : ''}
              >
                <span className="mr-2">{locale.flag}</span>
                <span className="flex-1">{locale.native_name}</span>
                <span className="ml-2 text-xs text-muted-foreground">{locale.english_name}</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuSubContent>
        </DropdownMenuSub>

        <DropdownMenuSeparator />
        <DropdownMenuLabel>{reports.selectFormat}</DropdownMenuLabel>
        <DropdownMenuSeparator />

        {FORMATS.map((format) => {
          const Icon = FORMAT_ICONS[format]
          // For HTML, allow theme selection
          if (format === 'html') {
            return (
              <DropdownMenuSub key={format}>
                <DropdownMenuSubTrigger>
                  <Icon className="mr-2 h-4 w-4" />
                  {FORMAT_LABELS[format]}
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  <DropdownMenuLabel>{reports.selectTheme}</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {THEMES.map((theme) => (
                    <DropdownMenuItem
                      key={theme}
                      onClick={() => handleDownload(format, theme, selectedLocale)}
                    >
                      {THEME_LABELS[theme]}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuSubContent>
              </DropdownMenuSub>
            )
          }
          return (
            <DropdownMenuItem
              key={format}
              onClick={() => handleDownload(format, undefined, selectedLocale)}
            >
              <Icon className="mr-2 h-4 w-4" />
              {FORMAT_LABELS[format]}
            </DropdownMenuItem>
          )
        })}

          {/* Custom Reporters Section */}
          <CustomReporterSection
            validationId={validationId}
            disabled={disabled || isDownloading}
            reporters={customReporters}
          />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default ReportDownloadButton
