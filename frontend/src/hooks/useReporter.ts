/**
 * Reporter hooks for report generation and management.
 *
 * Provides React hooks for:
 * - Report generation with progress tracking
 * - Report history management
 * - Built-in report configuration
 */

import { useState, useCallback, useEffect } from 'react'
import { useToast } from './use-toast'
import type {
  ReportFormatType,
  ReportThemeType,
  ReportLocale,
  ReporterConfig,
  LocaleInfo,
} from '@/types/reporters'
import {
  downloadArtifact,
  generateReportArtifact,
  getArtifactCapabilities,
  type ArtifactFormat as ReportFormat,
  type ArtifactTheme as ReportTheme,
  type ArtifactLocale as ModuleReportLocale,
} from '@/api/modules/artifacts'
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
      const capabilities = await getArtifactCapabilities()
      setFormats(capabilities.formats)
      setThemes(capabilities.themes)
      setLocales(
        capabilities.locales.map((l) => ({
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
      await generateReportArtifact(validationId, {
        format: format as ReportFormat,
        theme,
        locale,
        title: config?.title,
        include_samples: config?.includeSamples,
        include_statistics: config?.includeStatistics,
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
      const artifact = await generateReportArtifact(validationId, {
        format: format as ReportFormat,
        theme: theme as ReportTheme,
        locale: locale as ModuleReportLocale,
        include_samples: config?.includeSamples,
        include_statistics: config?.includeStatistics,
      })
      const blob = await downloadArtifact(artifact.id)

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
      const artifact = await generateReportArtifact(validationId, {
        format: format as ReportFormat,
        theme: theme as ReportTheme,
        locale: locale as ModuleReportLocale,
        include_samples: config?.includeSamples,
        include_statistics: config?.includeStatistics,
      })
      const blob = await downloadArtifact(artifact.id)
      const content = await blob.text()
      setPreviewContent(content)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Preview failed')
      setError(error)
    } finally {
      setIsGenerating(false)
    }
  }, [validationId, format, theme, locale, config])

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
