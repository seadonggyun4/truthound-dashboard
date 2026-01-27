import { useState, useEffect, useCallback, forwardRef, useImperativeHandle, memo } from 'react'
import { Link } from 'react-router-dom'
import { History, CheckCircle2, XCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { listSourceValidations, type Validation } from '@/api/modules/validations'
import { formatDate, formatDuration, formatNumber } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'

const PAGE_SIZE = 10

export interface ValidationHistoryListHandle {
  /**
   * Add a new validation to the top of the list without refetching
   */
  addValidation: (validation: Validation) => void
  /**
   * Refresh the list from the server
   */
  refresh: () => Promise<void>
}

interface ValidationHistoryListProps {
  sourceId: string
}

/**
 * ValidationHistoryList - A paginated validation history list component
 *
 * This component manages its own state and fetches data independently,
 * preventing unnecessary re-renders of parent components.
 *
 * Use the imperative handle to add new validations without triggering a full refresh.
 */
const ValidationHistoryList = forwardRef<ValidationHistoryListHandle, ValidationHistoryListProps>(
  function ValidationHistoryList({ sourceId }, ref) {
    const [validations, setValidations] = useState<Validation[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [loading, setLoading] = useState(true)
    const { toast } = useToast()
    const common = useSafeIntlayer('common')

    const totalPages = Math.ceil(total / PAGE_SIZE)
    const offset = (page - 1) * PAGE_SIZE

    const loadValidations = useCallback(async () => {
      try {
        setLoading(true)
        const response = await listSourceValidations(sourceId, {
          offset,
          limit: PAGE_SIZE,
        })
        setValidations(response.data)
        setTotal(response.total)
      } catch {
        toast({
          title: str(common.error),
          description: 'Failed to load validation history',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }, [sourceId, offset, toast, common])

    useEffect(() => {
      loadValidations()
    }, [loadValidations])

    // Expose imperative methods to parent
    useImperativeHandle(
      ref,
      () => ({
        addValidation: (validation: Validation) => {
          // If we're on page 1, prepend the new validation
          if (page === 1) {
            setValidations((prev) => {
              // Keep only PAGE_SIZE items
              const newList = [validation, ...prev].slice(0, PAGE_SIZE)
              return newList
            })
            setTotal((prev) => prev + 1)
          } else {
            // If not on page 1, just increment total and let user navigate
            setTotal((prev) => prev + 1)
          }
        },
        refresh: loadValidations,
      }),
      [page, loadValidations]
    )

    const handlePrevPage = () => {
      if (page > 1) {
        setPage(page - 1)
      }
    }

    const handleNextPage = () => {
      if (page < totalPages) {
        setPage(page + 1)
      }
    }

    // Generate page numbers to display
    const getPageNumbers = () => {
      const pages: (number | 'ellipsis')[] = []
      const maxVisible = 5

      if (totalPages <= maxVisible + 2) {
        // Show all pages if total is small
        for (let i = 1; i <= totalPages; i++) {
          pages.push(i)
        }
      } else {
        // Always show first page
        pages.push(1)

        if (page > 3) {
          pages.push('ellipsis')
        }

        // Show pages around current page
        const start = Math.max(2, page - 1)
        const end = Math.min(totalPages - 1, page + 1)

        for (let i = start; i <= end; i++) {
          pages.push(i)
        }

        if (page < totalPages - 2) {
          pages.push('ellipsis')
        }

        // Always show last page
        pages.push(totalPages)
      }

      return pages
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Validation History
            {total > 0 && (
              <span className="text-sm font-normal text-muted-foreground">
                ({total})
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && validations.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
            </div>
          ) : validations.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No validations yet. Run your first validation to see results here.
            </p>
          ) : (
            <div className="space-y-3">
              {validations.map((validation) => (
                <ValidationHistoryItem key={validation.id} validation={validation} />
              ))}
            </div>
          )}

          {/* Bottom pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between pt-4 mt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Showing {offset + 1}-{Math.min(offset + PAGE_SIZE, total)} of {total}
              </p>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={handlePrevPage}
                  disabled={page === 1 || loading}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                {getPageNumbers().map((pageNum, idx) =>
                  pageNum === 'ellipsis' ? (
                    <span key={`ellipsis-${idx}`} className="px-2 text-muted-foreground">
                      ...
                    </span>
                  ) : (
                    <Button
                      key={pageNum}
                      variant={page === pageNum ? 'default' : 'outline'}
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setPage(pageNum)}
                      disabled={loading}
                    >
                      {pageNum}
                    </Button>
                  )
                )}
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={handleNextPage}
                  disabled={page === totalPages || loading}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }
)

/**
 * Memoized validation history item to prevent unnecessary re-renders
 */
const ValidationHistoryItem = memo(function ValidationHistoryItem({
  validation,
}: {
  validation: Validation
}) {
  return (
    <Link
      to={`/validations/${validation.id}`}
      className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors"
    >
      <div className="flex items-center gap-3">
        {validation.passed ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-600" />
        )}
        <div>
          <p className="font-medium">
            {validation.passed ? 'Passed' : 'Failed'} -{' '}
            {formatNumber(validation.total_issues)} issues
          </p>
          <p className="text-sm text-muted-foreground">
            {formatDate(validation.created_at)} • {formatDuration(validation.duration_ms)}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {validation.critical_issues > 0 && (
          <Badge variant="critical">{validation.critical_issues} critical</Badge>
        )}
        {validation.high_issues > 0 && (
          <Badge variant="high">{validation.high_issues} high</Badge>
        )}
      </div>
    </Link>
  )
})

export default ValidationHistoryList
