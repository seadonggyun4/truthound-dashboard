/**
 * Reporter hooks for report generation and management.
 *
 * Provides React hooks for:
 * - Report generation with progress tracking
 * - Report history management
 * - Custom reporter configuration
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useToast } from './use-toast'
import type {
  ReportFormatType,
  ReportThemeType,
  ReportLocale,
  ReporterConfig,
  GeneratedReport,
  CustomReporter,
  LocaleInfo,
} from '@/types/reporters'
import {
  getReportFormats,
  getReportLocales,
  generateReportMetadata,
  downloadValidationReport,
  previewValidationReport,
  listReportHistory,
  getReportStatistics,
  deleteReportRecord,
  cleanupExpiredReports,
  type ReportFormat,
  type ReportTheme,
  type ReportLocale as ModuleReportLocale,
  type ReportStatus,
  type ReportStatistics,
} from '@/api/modules/reports'
import { listCustomReporters } from '@/api/modules/plugins'

// Type alias for report history query params
interface ReportHistoryQuery {
  search?: string
  format?: ReportFormat
  status?: ReportStatus
  source_id?: string
  include_expired?: boolean
  page?: number
  pageSize?: number
}
import { createDefaultConfig } from '@/types/reporters'

// =============================================================================
// Format and Configuration Hook
// =============================================================================

interface UseReporterFormatsResult {
  formats: string[]
  themes: string[]
  locales: LocaleInfo[]
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * Hook for fetching available report formats, themes, and locales.
 */
export function useReporterFormats(): UseReporterFormatsResult {
  const [formats, setFormats] = useState<string[]>([])
  const [themes, setThemes] = useState<string[]>([])
  const [locales, setLocales] = useState<LocaleInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchFormats = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const [formatsResponse, localesResponse] = await Promise.all([
        getReportFormats(),
        getReportLocales(),
      ])

      setFormats(formatsResponse.formats)
      setThemes(formatsResponse.themes)
      setLocales(
        localesResponse.map((l) => ({
          code: (l as unknown as { code: string }).code as ReportLocale,
          englishName: (l as unknown as { englishName?: string; english_name?: string }).englishName || (l as unknown as { english_name?: string }).english_name || '',
          nativeName: (l as unknown as { nativeName?: string; native_name?: string }).nativeName || (l as unknown as { native_name?: string }).native_name || '',
          flag: (l as unknown as { flag: string }).flag || '',
          rtl: (l as unknown as { rtl: boolean }).rtl || false,
        }))
      )
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch formats'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFormats()
  }, [fetchFormats])

  return {
    formats,
    themes,
    locales,
    isLoading,
    error,
    refetch: fetchFormats,
  }
}

// =============================================================================
// Report Generation Hook
// =============================================================================

interface UseReportGenerationOptions {
  validationId: string
  format?: ReportFormatType
  theme?: ReportThemeType
  locale?: ReportLocale
  config?: ReporterConfig
  autoGenerate?: boolean
}

interface UseReportGenerationResult {
  isGenerating: boolean
  isDownloading: boolean
  previewContent: string | null
  error: Error | null
  generate: () => Promise<void>
  download: () => Promise<void>
  preview: () => Promise<void>
  reset: () => void
}

/**
 * Hook for report generation, download, and preview.
 */
export function useReportGeneration(
  options: UseReportGenerationOptions
): UseReportGenerationResult {
  const { toast } = useToast()
  const {
    validationId,
    format = 'html',
    theme = 'professional',
    locale = 'en',
    config,
    autoGenerate = false,
  } = options

  const [isGenerating, setIsGenerating] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [previewContent, setPreviewContent] = useState<string | null>(null)
  const [error, setError] = useState<Error | null>(null)

  const generate = useCallback(async () => {
    setIsGenerating(true)
    setError(null)

    try {
      await generateReportMetadata(validationId, {
        theme,
        locale,
        ...config,
      })

      toast({
        title: 'Report Generated',
        description: 'Your report has been generated successfully',
      })
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Generation failed')
      setError(error)
      toast({
        title: 'Generation Failed',
        description: error.message,
        variant: 'destructive',
      })
    } finally {
      setIsGenerating(false)
    }
  }, [validationId, theme, locale, config, toast])

  const download = useCallback(async () => {
    setIsDownloading(true)
    setError(null)

    try {
      const blob = await downloadValidationReport(validationId, {
        format: format as ReportFormat,
        theme: theme as ReportTheme,
        locale: locale as ModuleReportLocale,
        include_samples: config?.includeSamples,
        include_statistics: config?.includeStatistics,
      })

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${validationId.slice(0, 8)}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      toast({
        title: 'Download Started',
        description: 'Your report is being downloaded',
      })
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Download failed')
      setError(error)
      toast({
        title: 'Download Failed',
        description: error.message,
        variant: 'destructive',
      })
    } finally {
      setIsDownloading(false)
    }
  }, [validationId, format, theme, locale, config, toast])

  const preview = useCallback(async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const content = await previewValidationReport(validationId, format as ReportFormat, theme as ReportTheme, locale as ModuleReportLocale)
      setPreviewContent(content)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Preview failed')
      setError(error)
    } finally {
      setIsGenerating(false)
    }
  }, [validationId, format, theme, locale])

  const reset = useCallback(() => {
    setPreviewContent(null)
    setError(null)
  }, [])

  useEffect(() => {
    if (autoGenerate) {
      preview()
    }
  }, [autoGenerate, preview])

  return {
    isGenerating,
    isDownloading,
    previewContent,
    error,
    generate,
    download,
    preview,
    reset,
  }
}

// =============================================================================
// Report History Hook
// =============================================================================

interface UseReportHistoryOptions {
  query?: ReportHistoryQuery
  autoFetch?: boolean
}

interface UseReportHistoryResult {
  reports: GeneratedReport[]
  total: number
  page: number
  pageSize: number
  statistics: ReportStatistics | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
  fetchStatistics: () => Promise<void>
  setPage: (page: number) => void
  setPageSize: (size: number) => void
  updateQuery: (query: Partial<ReportHistoryQuery>) => void
  deleteReport: (reportId: string) => Promise<void>
  cleanupExpired: () => Promise<number>
}

/**
 * Hook for managing report history with pagination and filtering.
 */
export function useReportHistory(
  options: UseReportHistoryOptions = {}
): UseReportHistoryResult {
  const { toast } = useToast()
  const { query: initialQuery, autoFetch = true } = options

  const [reports, setReports] = useState<GeneratedReport[]>([])
  const [total, setTotal] = useState(0)
  const [statistics, setStatistics] = useState<ReportStatistics | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [query, setQuery] = useState<ReportHistoryQuery>({
    page: 1,
    pageSize: 20,
    ...initialQuery,
  })

  const fetchReports = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await listReportHistory({
        search: query.search,
        format: query.format,
        status: query.status,
        source_id: query.source_id,
        include_expired: query.include_expired,
        page: query.page,
        page_size: query.pageSize,
      })
      setReports((response.data ?? []) as unknown as GeneratedReport[])
      setTotal(response.total ?? 0)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch reports')
      setError(error)
    } finally {
      setIsLoading(false)
    }
  }, [query])

  const fetchStats = useCallback(async () => {
    try {
      const stats = await getReportStatistics()
      setStatistics(stats)
    } catch (err) {
      console.error('Failed to fetch statistics:', err)
    }
  }, [])

  useEffect(() => {
    if (autoFetch) {
      fetchReports()
      fetchStats()
    }
  }, [autoFetch, fetchReports, fetchStats])

  const setPage = useCallback((page: number) => {
    setQuery((prev) => ({ ...prev, page }))
  }, [])

  const setPageSize = useCallback((pageSize: number) => {
    setQuery((prev) => ({ ...prev, pageSize, page: 1 }))
  }, [])

  const updateQuery = useCallback((newQuery: Partial<ReportHistoryQuery>) => {
    setQuery((prev) => ({ ...prev, ...newQuery, page: 1 }))
  }, [])

  const handleDeleteReport = useCallback(
    async (reportId: string) => {
      try {
        await deleteReportRecord(reportId)
        toast({
          title: 'Report Deleted',
          description: 'The report has been deleted successfully',
        })
        fetchReports()
        fetchStats()
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Delete failed')
        toast({
          title: 'Delete Failed',
          description: error.message,
          variant: 'destructive',
        })
        throw error
      }
    },
    [toast, fetchReports, fetchStats]
  )

  const handleCleanupExpired = useCallback(async () => {
    try {
      const result = await cleanupExpiredReports()
      toast({
        title: 'Cleanup Complete',
        description: `Deleted ${result.deleted} expired reports`,
      })
      fetchReports()
      fetchStats()
      return result.deleted
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Cleanup failed')
      toast({
        title: 'Cleanup Failed',
        description: error.message,
        variant: 'destructive',
      })
      throw error
    }
  }, [toast, fetchReports, fetchStats])

  return {
    reports,
    total,
    page: query.page || 1,
    pageSize: query.pageSize || 20,
    statistics,
    isLoading,
    error,
    refetch: fetchReports,
    fetchStatistics: fetchStats,
    setPage,
    setPageSize,
    updateQuery,
    deleteReport: handleDeleteReport,
    cleanupExpired: handleCleanupExpired,
  }
}

// =============================================================================
// Custom Reporters Hook
// =============================================================================

interface UseCustomReportersResult {
  reporters: CustomReporter[]
  total: number
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * Hook for fetching custom reporters.
 */
export function useCustomReporters(params?: {
  pluginId?: string
  enabled?: boolean
  search?: string
}): UseCustomReportersResult {
  const [reporters, setReporters] = useState<CustomReporter[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const paramsRef = useRef(params)
  paramsRef.current = params

  const fetchReporters = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await listCustomReporters({
        plugin_id: paramsRef.current?.pluginId,
        is_enabled: paramsRef.current?.enabled,
        search: paramsRef.current?.search,
      })
      setReporters(response.data as unknown as CustomReporter[])
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch reporters'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchReporters()
  }, [fetchReporters])

  return {
    reporters,
    total,
    isLoading,
    error,
    refetch: fetchReporters,
  }
}

// =============================================================================
// Report Configuration Hook
// =============================================================================

interface UseReporterConfigResult {
  config: ReporterConfig
  format: ReportFormatType
  setConfig: (config: ReporterConfig) => void
  setFormat: (format: ReportFormatType) => void
  updateConfig: (updates: Partial<ReporterConfig>) => void
  resetConfig: () => void
}

/**
 * Hook for managing reporter configuration state.
 */
export function useReporterConfig(
  initialFormat: ReportFormatType = 'html',
  initialConfig?: Partial<ReporterConfig>
): UseReporterConfigResult {
  const [format, setFormat] = useState<ReportFormatType>(initialFormat)
  const [config, setConfig] = useState<ReporterConfig>(() =>
    createDefaultConfig(initialConfig)
  )

  const updateConfig = useCallback((updates: Partial<ReporterConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }))
  }, [])

  const resetConfig = useCallback(() => {
    setConfig(createDefaultConfig())
  }, [])

  return {
    config,
    format,
    setConfig,
    setFormat,
    updateConfig,
    resetConfig,
  }
}
