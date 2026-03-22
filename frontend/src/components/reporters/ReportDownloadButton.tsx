/**
 * ReportDownloadButton - Download button for reports.
 *
 * Handles report download with loading state and error handling.
 */

import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import type { ArtifactRecord, ArtifactFormat } from '@/api/modules/artifacts'
import { downloadArtifact, generateReportArtifact } from '@/api/modules/artifacts'
import { getFormatExtension } from '@/types/reporters'

interface ReportDownloadButtonProps {
  /** Saved report to download */
  artifact?: ArtifactRecord
  /** Validation ID for direct generation */
  validationId?: string
  /** Format for direct generation */
  format?: ArtifactFormat
  /** Custom filename (without extension) */
  filename?: string
  /** Button variant */
  variant?: 'default' | 'outline' | 'ghost' | 'secondary' | 'destructive' | 'link'
  /** Button size */
  size?: 'default' | 'sm' | 'lg' | 'icon'
  /** Additional class names */
  className?: string
  /** Callback after successful download */
  onSuccess?: () => void
}

export function ReportDownloadButton({
  artifact,
  validationId,
  format = 'html',
  filename,
  variant = 'ghost',
  size = 'sm',
  className,
  onSuccess,
}: ReportDownloadButtonProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  // Determine if button should be disabled
  const isDisabled = artifact ? artifact.status !== 'completed' : !validationId

  const handleDownload = async () => {
    if (isDisabled) return

    setIsLoading(true)

    try {
      let blob: Blob
      let downloadFilename: string

      if (artifact) {
        blob = await downloadArtifact(artifact.id)
        downloadFilename = filename || artifact.title
        downloadFilename += getFormatExtension(artifact.format)
      } else if (validationId) {
        const generatedArtifact = await generateReportArtifact(validationId, { format })
        blob = await downloadArtifact(generatedArtifact.id)
        downloadFilename = filename || `report_${validationId.slice(0, 8)}`
        downloadFilename += getFormatExtension(format)
      } else {
        return
      }

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = downloadFilename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      toast({
        title: 'Download Started',
        description: `Downloading ${downloadFilename}`,
      })

      onSuccess?.()
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: error instanceof Error ? error.message : 'Failed to download report',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleDownload}
      disabled={isDisabled || isLoading}
      className={className}
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Download className="h-4 w-4" />
      )}
      {size !== 'icon' && <span className="ml-2">Download</span>}
    </Button>
  )
}
