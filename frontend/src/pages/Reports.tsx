/**
 * Reports page component.
 *
 * Displays report history with statistics, filtering, and management actions.
 * Uses the new reporter component system for improved maintainability.
 */
import { useEffect, useState, useCallback } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { Link } from 'react-router-dom'
import {
  FileText,
  Download,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  Clock,
  HardDrive,
  BarChart3,
  Settings,
  ExternalLink,
  AlertCircle,
  Eye,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'

// New reporter components
import {
  ReportStatusBadge,
  ReportDownloadButton,
  FormatIcon,
  ReportPreview,
} from '@/components/reporters'
import { useReportHistory } from '@/hooks/useReporter'
import type { GeneratedReport, ReportStatistics } from '@/types/reporters'
import { formatFileSize, formatGenerationTime } from '@/types/reporters'

// Format date for display
function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

// Statistics cards component
function StatisticsCards({
  stats,
  t,
}: {
  stats: ReportStatistics | null
  t: ReturnType<typeof useSafeIntlayer<'reports'>>
}) {
  if (!stats) return null

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.totalReports)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.totalReports}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <HardDrive className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.totalSize)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{formatFileSize(stats.totalSizeBytes)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.totalDownloads)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.totalDownloads}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.avgGenerationTime)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">
            {formatGenerationTime(stats.avgGenerationTimeMs)}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.expiredReports)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.expiredCount}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{str(t.reportersUsed)}</span>
          </div>
          <p className="text-2xl font-bold mt-1">{stats.reportersUsed}</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default function Reports() {
  const t = useSafeIntlayer('reports')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  // Use the new report history hook
  const {
    reports,
    total,
    page,
    pageSize,
    statistics,
    isLoading,
    error,
    refetch,
    setPage,
    updateQuery,
    deleteReport,
    cleanupExpired,
  } = useReportHistory({ autoFetch: true })

  // Local filter state
  const [search, setSearch] = useState('')
  const [formatFilter, setFormatFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [includeExpired, setIncludeExpired] = useState(false)

  // Dialogs
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean
    report: GeneratedReport | null
  }>({
    open: false,
    report: null,
  })
  const [cleanupDialog, setCleanupDialog] = useState(false)
  const [previewDialog, setPreviewDialog] = useState<{
    open: boolean
    report: GeneratedReport | null
  }>({
    open: false,
    report: null,
  })

  // Update query when filters change
  useEffect(() => {
    updateQuery({
      search: search || undefined,
      format: formatFilter !== 'all' ? formatFilter : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      includeExpired,
    })
  }, [search, formatFilter, statusFilter, includeExpired, updateQuery])

  // Handle delete
  const handleDelete = async () => {
    if (!deleteDialog.report) return

    try {
      await deleteReport(deleteDialog.report.id)
      setDeleteDialog({ open: false, report: null })
    } catch {
      // Error handled by hook
    }
  }

  // Handle cleanup
  const handleCleanup = async () => {
    try {
      await cleanupExpired()
      setCleanupDialog(false)
    } catch {
      // Error handled by hook
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{str(t.pageTitle)}</h1>
          <p className="text-muted-foreground">{str(t.pageDescription)}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/plugins">
              <Settings className="h-4 w-4 mr-2" />
              {str(t.manageReporters)}
            </Link>
          </Button>
          {statistics && statistics.expiredCount > 0 && (
            <Button variant="outline" onClick={() => setCleanupDialog(true)}>
              <Trash2 className="h-4 w-4 mr-2" />
              {str(t.cleanupExpired)}
            </Button>
          )}
        </div>
      </div>

      {/* Statistics */}
      <StatisticsCards stats={statistics} t={t} />

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            {str(t.reportHistory)}
          </CardTitle>
          <CardDescription>{str(t.historyDescription)}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={str(t.searchPlaceholder)}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <Select value={formatFilter} onValueChange={setFormatFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder={str(t.filterByFormat)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{str(t.allFormats)}</SelectItem>
                <SelectItem value="html">{str(t.formatHtml)}</SelectItem>
                <SelectItem value="pdf">{str(t.formatPdf)}</SelectItem>
                <SelectItem value="csv">{str(t.formatCsv)}</SelectItem>
                <SelectItem value="json">{str(t.formatJson)}</SelectItem>
                <SelectItem value="markdown">{str(t.formatMarkdown)}</SelectItem>
                <SelectItem value="excel">{str(t.formatExcel)}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder={str(t.filterByStatus)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{str(t.allStatuses)}</SelectItem>
                <SelectItem value="pending">{str(t.statusPending)}</SelectItem>
                <SelectItem value="generating">{str(t.statusGenerating)}</SelectItem>
                <SelectItem value="completed">{str(t.statusCompleted)}</SelectItem>
                <SelectItem value="failed">{str(t.statusFailed)}</SelectItem>
                <SelectItem value="expired">{str(t.statusExpired)}</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2">
              <Checkbox
                id="includeExpired"
                checked={includeExpired}
                onCheckedChange={(checked) => setIncludeExpired(checked === true)}
              />
              <label htmlFor="includeExpired" className="text-sm">
                {str(t.includeExpired)}
              </label>
            </div>
          </div>

          {/* Reports Table */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : reports.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">{str(t.noReports)}</h3>
              <p className="text-muted-foreground">{str(t.noReportsDescription)}</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{str(t.reportName)}</TableHead>
                    <TableHead>{str(t.format)}</TableHead>
                    <TableHead>{str(t.status)}</TableHead>
                    <TableHead>{str(t.source)}</TableHead>
                    <TableHead>{str(t.fileSize)}</TableHead>
                    <TableHead>{str(t.downloadCount)}</TableHead>
                    <TableHead>{str(t.createdAt)}</TableHead>
                    <TableHead className="text-right">{str(common.actions)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell className="font-medium">{report.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="flex items-center gap-1 w-fit">
                          <FormatIcon format={report.format} className="h-3 w-3" />
                          {report.format.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <ReportStatusBadge status={report.status} />
                      </TableCell>
                      <TableCell>
                        {report.sourceName ? (
                          <Link
                            to={`/sources/${report.sourceId}`}
                            className="text-primary hover:underline flex items-center gap-1"
                          >
                            {report.sourceName}
                            <ExternalLink className="h-3 w-3" />
                          </Link>
                        ) : (
                          <span className="text-muted-foreground">{str(t.noSource)}</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {report.fileSize ? formatFileSize(report.fileSize) : '-'}
                      </TableCell>
                      <TableCell>{report.downloadCount}</TableCell>
                      <TableCell>{formatDate(report.createdAt)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          {/* Preview button for HTML reports */}
                          {report.status === 'completed' &&
                            report.validationId &&
                            (report.format === 'html' || report.format === 'json') && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setPreviewDialog({ open: true, report })}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            )}
                          <ReportDownloadButton
                            report={report}
                            variant="ghost"
                            size="sm"
                            onSuccess={refetch}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeleteDialog({ open: true, report })}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    {str(common.showing)} {(page - 1) * pageSize + 1}-
                    {Math.min(page * pageSize, total)} {str(common.of)} {total}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page === 1}
                    >
                      {str(common.previous)}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(Math.min(totalPages, page + 1))}
                      disabled={page === totalPages}
                    >
                      {str(common.next)}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, report: null })}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.deleteConfirmTitle)}</DialogTitle>
            <DialogDescription>{str(t.deleteConfirmMessage)}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialog({ open: false, report: null })}
            >
              {str(common.cancel)}
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              {str(t.delete)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cleanup Confirmation Dialog */}
      <Dialog open={cleanupDialog} onOpenChange={setCleanupDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.cleanupTitle)}</DialogTitle>
            <DialogDescription>
              {str(t.cleanupDescription)}
              <br />
              <br />
              {str(t.cleanupConfirm)}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCleanupDialog(false)}>
              {str(common.cancel)}
            </Button>
            <Button variant="destructive" onClick={handleCleanup}>
              {str(t.cleanupExpired)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog
        open={previewDialog.open}
        onOpenChange={(open) => setPreviewDialog({ open, report: null })}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {previewDialog.report && (
                <>
                  <FormatIcon format={previewDialog.report.format} />
                  {previewDialog.report.name}
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          {previewDialog.report && previewDialog.report.validationId && (
            <ReportPreview
              validationId={previewDialog.report.validationId}
              format={previewDialog.report.format}
              theme={previewDialog.report.theme}
              locale={previewDialog.report.locale}
              title=""
              maxHeight="60vh"
              showControls={true}
              autoLoad={true}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
