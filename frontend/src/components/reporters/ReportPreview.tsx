/**
 * ReportPreview - Inline report preview component.
 *
 * Displays report content inline with format-specific rendering:
 * - HTML: iframe rendering
 * - Markdown: converted to HTML
 * - JSON/YAML: syntax highlighted code
 * - CSV: table view
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Loader2,
  RefreshCw,
  ExternalLink,
  Maximize2,
  Minimize2,
  Copy,
  Check,
  AlertCircle,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { FormatIcon } from './FormatIcon'
import type { ReportFormatType, ReportThemeType, ReportLocale } from '@/types/reporters'
import { previewValidationReport } from '@/api/modules/reports'

interface ReportPreviewProps {
  /** Validation ID to preview */
  validationId: string
  /** Report format */
  format: ReportFormatType
  /** Report theme */
  theme?: ReportThemeType
  /** Report locale */
  locale?: ReportLocale
  /** Preview title */
  title?: string
  /** Max height for preview */
  maxHeight?: string | number
  /** Show controls (refresh, fullscreen, etc.) */
  showControls?: boolean
  /** Auto-load on mount */
  autoLoad?: boolean
  /** Callback when preview is loaded */
  onLoad?: (content: string) => void
  /** Callback when preview fails */
  onError?: (error: Error) => void
  /** Additional class names */
  className?: string
}

export function ReportPreview({
  validationId,
  format,
  theme = 'professional',
  locale = 'en',
  title = 'Report Preview',
  maxHeight = '600px',
  showControls = true,
  autoLoad = true,
  onLoad,
  onError,
  className,
}: ReportPreviewProps) {
  const { toast } = useToast()
  const [content, setContent] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [copied, setCopied] = useState(false)

  const loadPreview = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await previewValidationReport(validationId, format as 'html' | 'csv' | 'json' | 'markdown' | 'pdf' | 'junit', theme as 'light' | 'dark' | 'professional' | 'minimal' | 'high_contrast', locale as 'en' | 'ko' | 'ja' | 'zh' | 'de' | 'fr' | 'es' | 'pt' | 'it' | 'ru' | 'ar' | 'th' | 'vi' | 'id' | 'tr')
      setContent(result)
      onLoad?.(result)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to load preview')
      setError(error)
      onError?.(error)
      toast({
        title: 'Preview Failed',
        description: error.message,
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [validationId, format, theme, locale, onLoad, onError, toast])

  useEffect(() => {
    if (autoLoad) {
      loadPreview()
    }
  }, [autoLoad, loadPreview])

  const handleCopy = async () => {
    if (!content) return

    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      toast({
        title: 'Copied',
        description: 'Report content copied to clipboard',
      })
    } catch {
      toast({
        title: 'Copy Failed',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      })
    }
  }

  const handleOpenInNewTab = () => {
    if (!content) return

    if (format === 'html') {
      const blob = new Blob([content], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    } else {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    }
  }

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <p className="text-lg font-medium">Failed to Load Preview</p>
          <p className="text-sm text-muted-foreground mt-1">{error.message}</p>
          <Button variant="outline" onClick={loadPreview} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      )
    }

    if (!content) {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <FormatIcon format={format} className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium">No Preview Available</p>
          <p className="text-sm text-muted-foreground mt-1">
            Click refresh to load the preview
          </p>
          <Button variant="outline" onClick={loadPreview} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Load Preview
          </Button>
        </div>
      )
    }

    // Render based on format
    switch (format) {
      case 'html':
        return (
          <iframe
            srcDoc={content}
            className="w-full border-0"
            style={{
              height: isFullscreen ? '100vh' : maxHeight,
              minHeight: '400px',
            }}
            sandbox="allow-same-origin"
            title="Report Preview"
          />
        )

      case 'json':
      case 'yaml':
        return (
          <ScrollArea
            style={{
              height: isFullscreen ? '100vh' : maxHeight,
            }}
          >
            <pre className="p-4 text-sm font-mono bg-muted/50 rounded-lg overflow-x-auto">
              <code>{content}</code>
            </pre>
          </ScrollArea>
        )

      case 'csv':
        return (
          <ScrollArea
            style={{
              height: isFullscreen ? '100vh' : maxHeight,
            }}
          >
            <div className="p-4">
              <table className="w-full text-sm">
                <tbody>
                  {content.split('\n').map((row, rowIdx) => (
                    <tr key={rowIdx} className={rowIdx === 0 ? 'font-medium bg-muted' : ''}>
                      {row.split(',').map((cell, cellIdx) => (
                        <td
                          key={cellIdx}
                          className="border px-2 py-1 whitespace-nowrap"
                        >
                          {cell.replace(/^"|"$/g, '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ScrollArea>
        )

      case 'markdown':
        return (
          <ScrollArea
            style={{
              height: isFullscreen ? '100vh' : maxHeight,
            }}
          >
            <div className="p-4 prose prose-sm dark:prose-invert max-w-none">
              <pre className="whitespace-pre-wrap font-sans">{content}</pre>
            </div>
          </ScrollArea>
        )

      default:
        return (
          <ScrollArea
            style={{
              height: isFullscreen ? '100vh' : maxHeight,
            }}
          >
            <pre className="p-4 text-sm font-mono whitespace-pre-wrap">
              {content}
            </pre>
          </ScrollArea>
        )
    }
  }

  return (
    <Card
      className={cn(
        'transition-all duration-200',
        isFullscreen && 'fixed inset-4 z-50',
        className
      )}
    >
      <CardHeader className="py-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FormatIcon format={format} />
            <CardTitle className="text-base">{title}</CardTitle>
            <Badge variant="outline">{format.toUpperCase()}</Badge>
          </div>
          {showControls && (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={loadPreview}
                disabled={isLoading}
              >
                <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleCopy}
                disabled={!content}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleOpenInNewTab}
                disabled={!content}
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                {isFullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">{renderContent()}</CardContent>
    </Card>
  )
}
