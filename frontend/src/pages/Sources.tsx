import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import {
  Database,
  Plus,
  Trash2,
  Play,
  FileText,
  CheckSquare,
  Square,
  MinusSquare,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationFirst,
  PaginationLast,
} from '@/components/ui/pagination'
import {
  listSources,
  deleteSource,
  runValidation,
  type Source,
} from '@/api/client'
import { deleteSources } from '@/api/datasources'
import { formatDate } from '@/lib/utils'
import { str } from '@/lib/intlayer-utils'
import { useToast } from '@/hooks/use-toast'
import { useConfirm } from '@/components/ConfirmDialog'
import { AddSourceDialog } from '@/components/sources'

const PAGE_SIZE_OPTIONS = [10, 15, 25, 50, 100]
const DEFAULT_PAGE_SIZE = 15

export default function Sources() {
  const nav = useSafeIntlayer('nav')
  const sources_t = useSafeIntlayer('sources')
  const common = useSafeIntlayer('common')
  const validation = useSafeIntlayer('validation')

  const [searchParams, setSearchParams] = useSearchParams()
  const [sources, setSources] = useState<Source[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isDeleting, setIsDeleting] = useState(false)
  const { toast } = useToast()
  const { confirm, ConfirmDialog } = useConfirm()

  // Get pagination params from URL
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10))
  const pageSize = PAGE_SIZE_OPTIONS.includes(parseInt(searchParams.get('size') || '', 10))
    ? parseInt(searchParams.get('size') || '', 10)
    : DEFAULT_PAGE_SIZE

  const totalPages = Math.ceil(total / pageSize)
  const offset = (page - 1) * pageSize

  // Helper to get validation status label
  const getValidationLabel = (status: string | null | undefined) => {
    if (!status) return null
    switch (status) {
      case 'passed': return validation.passed
      case 'success': return validation.success
      case 'failed': return validation.failed
      case 'error': return validation.error
      case 'pending': return validation.pending
      case 'warning': return validation.warning
      default: return status
    }
  }

  const loadSources = useCallback(async () => {
    try {
      setLoading(true)
      const response = await listSources({ offset, limit: pageSize })
      setSources(response.data)
      setTotal(response.total)
      setSelectedIds(new Set()) // Clear selection on reload
    } catch {
      toast({
        title: str(common.error),
        description: str(sources_t.loadError),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [toast, common, sources_t, offset, pageSize])

  useEffect(() => {
    loadSources()
  }, [loadSources])

  // Pagination handlers
  const setPage = (newPage: number) => {
    const params = new URLSearchParams(searchParams)
    params.set('page', String(newPage))
    setSearchParams(params)
  }

  const setPageSize = (newSize: number) => {
    const params = new URLSearchParams(searchParams)
    params.set('size', String(newSize))
    params.set('page', '1') // Reset to first page when changing page size
    setSearchParams(params)
  }

  // Selection handlers
  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === sources.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(sources.map((s) => s.id)))
    }
  }

  const isAllSelected = sources.length > 0 && selectedIds.size === sources.length
  const isSomeSelected = selectedIds.size > 0 && selectedIds.size < sources.length

  async function handleDelete(id: string) {
    const confirmed = await confirm({
      title: str(sources_t.deleteSource),
      description: str(sources_t.confirmDelete),
      confirmText: str(common.delete),
      variant: 'destructive',
    })
    if (!confirmed) return

    try {
      await deleteSource(id)
      await loadSources() // Reload to update pagination
      toast({
        title: str(common.success),
        description: str(sources_t.deleteSuccess),
      })
    } catch {
      toast({
        title: str(common.error),
        description: str(sources_t.deleteFailed),
        variant: 'destructive',
      })
    }
  }

  async function handleBulkDelete() {
    if (selectedIds.size === 0) return

    const confirmed = await confirm({
      title: str(sources_t.bulkDelete?.title || 'Delete Sources'),
      description: str(sources_t.bulkDelete?.description || `Are you sure you want to delete ${selectedIds.size} sources? This action cannot be undone.`).replace('{count}', String(selectedIds.size)),
      confirmText: str(common.delete),
      variant: 'destructive',
    })
    if (!confirmed) return

    setIsDeleting(true)
    try {
      const result = await deleteSources(Array.from(selectedIds))
      await loadSources() // Reload to update pagination

      if (result.failed_ids.length > 0) {
        toast({
          title: str(sources_t.bulkDelete?.partialSuccess || 'Partial Success'),
          description: `${result.deleted_count} deleted, ${result.failed_ids.length} failed`,
          variant: 'warning',
        })
      } else {
        toast({
          title: str(common.success),
          description: str(sources_t.bulkDelete?.success || `${result.deleted_count} sources deleted`).replace('{count}', String(result.deleted_count)),
        })
      }
    } catch {
      toast({
        title: str(common.error),
        description: str(sources_t.bulkDelete?.error || 'Failed to delete sources'),
        variant: 'destructive',
      })
    } finally {
      setIsDeleting(false)
    }
  }

  async function handleValidate(id: string) {
    try {
      toast({
        title: str(sources_t.validationStarted),
        description: str(sources_t.runningValidation),
      })
      const result = await runValidation(id, {})
      setSources((prev) =>
        prev.map((s) =>
          s.id === id
            ? { ...s, latest_validation_status: result.status }
            : s
        )
      )
      toast({
        title: str(result.passed ? sources_t.validationPassed : sources_t.validationFailed),
        description: `${result.total_issues} issues found`,
        variant: result.passed ? 'default' : 'destructive',
      })
    } catch {
      toast({
        title: str(common.error),
        description: str(sources_t.validationError),
        variant: 'destructive',
      })
    }
  }

  // Generate pagination items
  const getPaginationItems = () => {
    const items: (number | 'ellipsis')[] = []
    const showPages = 5 // Number of page buttons to show

    if (totalPages <= showPages + 2) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) {
        items.push(i)
      }
    } else {
      // Always show first page
      items.push(1)

      if (page > 3) {
        items.push('ellipsis')
      }

      // Show pages around current page
      const start = Math.max(2, page - 1)
      const end = Math.min(totalPages - 1, page + 1)

      for (let i = start; i <= end; i++) {
        items.push(i)
      }

      if (page < totalPages - 2) {
        items.push('ellipsis')
      }

      // Always show last page
      if (totalPages > 1) {
        items.push(totalPages)
      }
    }

    return items
  }

  if (loading && sources.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{nav.sources}</h1>
          <p className="text-muted-foreground">
            {sources_t.subtitle}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
            <Button
              variant="destructive"
              onClick={handleBulkDelete}
              disabled={isDeleting}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {isDeleting ? str(sources_t.bulkDelete?.deleting || 'Deleting...') : `Delete (${selectedIds.size})`}
            </Button>
          )}
          <Button onClick={() => setShowAddDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            {sources_t.addSource}
          </Button>
        </div>
      </div>

      {/* Sources List */}
      {total === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Database className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">{sources_t.noSourcesYet}</h3>
            <p className="text-muted-foreground text-center mb-4">
              {sources_t.noSourcesDesc}
            </p>
            <Button onClick={() => setShowAddDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              {sources_t.addFirstSource}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Select All Header & Page Size */}
          <div className="flex items-center justify-between px-4 py-2 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-3">
              <button
                onClick={toggleSelectAll}
                className="flex items-center justify-center hover:opacity-80 transition-opacity"
                aria-label={isAllSelected ? 'Deselect all' : 'Select all'}
              >
                {isAllSelected ? (
                  <CheckSquare className="h-5 w-5 text-primary" />
                ) : isSomeSelected ? (
                  <MinusSquare className="h-5 w-5 text-primary" />
                ) : (
                  <Square className="h-5 w-5 text-muted-foreground" />
                )}
              </button>
              <span className="text-sm text-muted-foreground">
                {selectedIds.size > 0
                  ? `${selectedIds.size} of ${sources.length} selected`
                  : `${sources.length} items on this page`}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Show:</span>
              <Select
                value={String(pageSize)}
                onValueChange={(value) => setPageSize(parseInt(value, 10))}
              >
                <SelectTrigger className="w-[80px] h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <SelectItem key={size} value={String(size)}>
                      {size}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Sources Cards */}
          <div className="grid gap-4">
            {sources.map((source) => (
              <Card
                key={source.id}
                className={`transition-all ${
                  selectedIds.has(source.id)
                    ? 'ring-2 ring-primary bg-primary/5'
                    : ''
                }`}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Checkbox */}
                      <Checkbox
                        checked={selectedIds.has(source.id)}
                        onCheckedChange={() => toggleSelect(source.id)}
                        aria-label={`Select ${source.name}`}
                      />

                      <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Database className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <Link
                          to={`/sources/${source.id}`}
                          className="font-semibold hover:text-primary transition-colors"
                        >
                          {source.name}
                        </Link>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="outline">{source.type}</Badge>
                          <span>•</span>
                          <span>
                            {sources_t.lastValidated}: {formatDate(source.last_validated_at)}
                          </span>
                        </div>
                        {source.description && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {source.description}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {source.latest_validation_status && (
                        <Badge
                          variant={
                            source.latest_validation_status === 'success' || source.latest_validation_status === 'passed'
                              ? 'success'
                              : source.latest_validation_status === 'failed'
                              ? 'destructive'
                              : source.latest_validation_status === 'warning'
                              ? 'warning'
                              : 'secondary'
                          }
                        >
                          {getValidationLabel(source.latest_validation_status)}
                        </Badge>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleValidate(source.id)}
                      >
                        <Play className="mr-2 h-4 w-4" />
                        {sources_t.validate}
                      </Button>

                      <Button variant="ghost" size="icon" asChild>
                        <Link to={`/sources/${source.id}`}>
                          <FileText className="h-4 w-4" />
                        </Link>
                      </Button>

                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(source.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Showing {offset + 1}-{Math.min(offset + pageSize, total)} of {total}
              </p>

              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationFirst
                      onClick={() => setPage(1)}
                      disabled={page === 1}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                    />
                  </PaginationItem>

                  {getPaginationItems().map((item, idx) =>
                    item === 'ellipsis' ? (
                      <PaginationItem key={`ellipsis-${idx}`}>
                        <PaginationEllipsis />
                      </PaginationItem>
                    ) : (
                      <PaginationItem key={item}>
                        <PaginationLink
                          isActive={page === item}
                          onClick={() => setPage(item)}
                        >
                          {item}
                        </PaginationLink>
                      </PaginationItem>
                    )
                  )}

                  <PaginationItem>
                    <PaginationNext
                      onClick={() => setPage(page + 1)}
                      disabled={page === totalPages}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationLast
                      onClick={() => setPage(totalPages)}
                      disabled={page === totalPages}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </div>
      )}

      <ConfirmDialog />

      {/* Add Source Dialog */}
      <AddSourceDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        onSuccess={loadSources}
      />
    </div>
  )
}
