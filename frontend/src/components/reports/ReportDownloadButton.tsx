/**
 * Report Download Button component
 *
 * Provides a dropdown button for downloading validation reports
 * in multiple formats (HTML, CSV, JSON, Markdown) with theme selection.
 */

import { useState } from 'react'
import { Download, FileText, FileSpreadsheet, FileJson, FileCode, ChevronDown, Loader2, File, TestTube2 } from 'lucide-react'
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
  type ReportFormat,
  type ReportTheme,
} from '@/api/client'

export interface ReportDownloadButtonProps {
  validationId: string
  disabled?: boolean
  className?: string
}

const FORMAT_ICONS: Record<ReportFormat, typeof FileText> = {
  html: FileText,
  csv: FileSpreadsheet,
  json: FileJson,
  markdown: FileCode,
  pdf: File,
  junit: TestTube2,
}

const FORMAT_LABELS: Record<ReportFormat, string> = {
  html: 'HTML',
  csv: 'CSV',
  json: 'JSON',
  markdown: 'Markdown',
  pdf: 'PDF',
  junit: 'JUnit XML (CI/CD)',
}

const THEME_LABELS: Record<ReportTheme, string> = {
  light: 'Light',
  dark: 'Dark',
  professional: 'Professional',
  minimal: 'Minimal',
  high_contrast: 'High Contrast',
}

const FORMATS: ReportFormat[] = ['html', 'pdf', 'csv', 'json', 'markdown', 'junit']
const THEMES: ReportTheme[] = ['professional', 'light', 'dark', 'minimal', 'high_contrast']

export function ReportDownloadButton({
  validationId,
  disabled = false,
  className,
}: ReportDownloadButtonProps) {
  const reports = useIntlayer('reports')
  const common = useIntlayer('common')
  const { toast } = useToast()
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownload = async (format: ReportFormat, theme?: ReportTheme) => {
    setIsDownloading(true)
    try {
      const blob = await downloadValidationReport(validationId, {
        format,
        theme: theme || 'professional',
      })

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const ext = format === 'markdown' ? 'md' : format === 'junit' ? 'xml' : format
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
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>{reports.selectFormat}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {FORMATS.map((format) => {
          const Icon = FORMAT_ICONS[format]
          // For HTML and PDF, allow theme selection
          if (format === 'html' || format === 'pdf') {
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
                      onClick={() => handleDownload(format, theme)}
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
              onClick={() => handleDownload(format)}
            >
              <Icon className="mr-2 h-4 w-4" />
              {FORMAT_LABELS[format]}
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default ReportDownloadButton
