/**
 * PII Scan panel component.
 *
 * Provides interface for running PII scans.
 *
 * Note: truthound's th.scan() does not support min_confidence, columns,
 * or regulations parameters. These options have been removed from the UI.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Play, Eye, AlertTriangle, Shield } from 'lucide-react'
import { PIIFindingsTable } from './PIIFindingsTable'
import type { PIIScan } from '@/api/modules/privacy'
import { runPIIScan, getPIIScan } from '@/api/modules/privacy'

interface PIIScanPanelProps {
  sourceId: string
  initialScan?: PIIScan | null
  onScanComplete?: (scan: PIIScan) => void
}

export function PIIScanPanel({ sourceId, initialScan, onScanComplete }: PIIScanPanelProps) {
  const t = useIntlayer('privacy')
  void useIntlayer('common')
  const { toast } = useToast()

  // State
  const [isScanning, setIsScanning] = useState(false)
  const [currentScan, setCurrentScan] = useState<PIIScan | null>(initialScan ?? null)

  // Sync with parent when initialScan or sourceId changes
  useEffect(() => {
    setCurrentScan(initialScan ?? null)
  }, [initialScan, sourceId])

  const handleRunScan = useCallback(async () => {
    setIsScanning(true)

    try {
      const scan = await runPIIScan(sourceId)

      // Poll for completion
      const pollResult = async () => {
        const result = await getPIIScan(scan.id)
        if (result.status === 'running' || result.status === 'pending') {
          setTimeout(pollResult, 1000)
        } else {
          setCurrentScan(result)
          setIsScanning(false)
          onScanComplete?.(result)

          if (result.status === 'success') {
            toast({
              title: str(t.scan.scanComplete),
              description: `Found ${result.columns_with_pii} columns with PII`,
            })
          } else if (result.status === 'error') {
            toast({
              title: str(t.scan.scanFailed),
              description: result.error_message || undefined,
              variant: 'destructive',
            })
          }
        }
      }

      pollResult()
    } catch (error) {
      setIsScanning(false)
      toast({
        title: str(t.scan.scanFailed),
        variant: 'destructive',
      })
    }
  }, [sourceId, toast, t, onScanComplete])

  return (
    <div className="space-y-6">
      {/* Run Button */}
      <div className="flex justify-end">
        <Button onClick={handleRunScan} disabled={isScanning} className="gap-2">
          {isScanning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isScanning ? t.scan.scanning : t.scan.runScan}
        </Button>
      </div>

      {/* Results */}
      {currentScan && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.columnsScanned}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Eye className="h-5 w-5 text-muted-foreground" />
                  <span className="text-2xl font-bold">{currentScan.total_columns_scanned}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.columnsWithPII}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <AlertTriangle
                    className={`h-5 w-5 ${
                      currentScan.columns_with_pii > 0 ? 'text-orange-500' : 'text-green-500'
                    }`}
                  />
                  <span
                    className={`text-2xl font-bold ${
                      currentScan.columns_with_pii > 0 ? 'text-orange-500' : 'text-green-500'
                    }`}
                  >
                    {currentScan.columns_with_pii}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.totalFindings}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-muted-foreground" />
                  <span className="text-2xl font-bold">{currentScan.findings?.length ?? 0}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.avgConfidence}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-2xl font-bold">
                  {currentScan.findings && currentScan.findings.length > 0
                    ? (
                        (currentScan.findings.reduce((sum, f) => sum + f.confidence, 0) /
                          currentScan.findings.length) *
                        100
                      ).toFixed(0)
                    : 0}
                  %
                </span>
              </CardContent>
            </Card>
          </div>

          {/* Findings Table */}
          <div>
            <h3 className="mb-3 text-sm font-medium">{t.scan.totalFindings}</h3>
            <PIIFindingsTable findings={currentScan.findings ?? []} />
          </div>
        </div>
      )}
    </div>
  )
}
