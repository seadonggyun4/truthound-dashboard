import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Columns,
  Rows3,
  GitBranch,
  Loader2,
  BarChart3,
  ShieldAlert,
  SkipForward,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Bug,
  Info,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ReportDownloadButton } from '@/components/reports'
import {
  getValidation,
  type Validation,
  type ValidationIssue,
  type ValidationDetailResult,
  type ValidationReportStatistics,
  type ExceptionSummary,
  type ValidatorExecutionSummary,
} from '@/api/modules/validations'
import { createVersion } from '@/api/modules/versioning'
import { formatDate, formatDuration, formatNumber } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

// ============================================================================
// Sub-components
// ============================================================================

/** Collapsible section wrapper */
function CollapsibleSection({
  title,
  icon: Icon,
  defaultOpen = false,
  badge,
  children,
}: {
  title: string
  icon: React.ElementType
  defaultOpen?: boolean
  badge?: React.ReactNode
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <Card>
      <CardHeader
        className="cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">{title}</CardTitle>
            {badge}
          </div>
          {open ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </CardHeader>
      {open && <CardContent>{children}</CardContent>}
    </Card>
  )
}

/** Display structured ValidationDetail for an issue */
function IssueDetailPanel({ result }: { result: ValidationDetailResult }) {
  return (
    <div className="mt-3 grid gap-2 text-sm border-t pt-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div>
          <span className="text-muted-foreground">Total Rows</span>
          <p className="font-medium">{formatNumber(result.element_count)}</p>
        </div>
        <div>
          <span className="text-muted-foreground">Failed Rows</span>
          <p className="font-medium text-destructive">
            {formatNumber(result.unexpected_count)}
          </p>
        </div>
        <div>
          <span className="text-muted-foreground">Failure Rate</span>
          <p className="font-medium">
            {result.unexpected_percent.toFixed(1)}%
          </p>
        </div>
        <div>
          <span className="text-muted-foreground">Missing</span>
          <p className="font-medium">{formatNumber(result.missing_count)}</p>
        </div>
      </div>

      {result.partial_unexpected_list && result.partial_unexpected_list.length > 0 && (
        <div className="mt-2">
          <span className="text-muted-foreground text-xs">Sample Failed Values</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {result.partial_unexpected_list.slice(0, 10).map((val, i) => (
              <code key={i} className="bg-muted px-1.5 py-0.5 rounded text-xs">
                {val === null ? 'null' : String(val)}
              </code>
            ))}
          </div>
        </div>
      )}

      {result.partial_unexpected_counts && result.partial_unexpected_counts.length > 0 && (
        <div className="mt-2">
          <span className="text-muted-foreground text-xs">Value Frequency</span>
          <div className="mt-1 space-y-1">
            {result.partial_unexpected_counts.slice(0, 5).map((item, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <code className="bg-muted px-1.5 py-0.5 rounded">
                  {item.value === null ? 'null' : String(item.value)}
                </code>
                <span className="text-muted-foreground">
                  {formatNumber(item.count)} times
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.debug_query && (
        <div className="mt-2">
          <span className="text-muted-foreground text-xs">Debug Query</span>
          <pre className="mt-1 bg-muted p-2 rounded text-xs overflow-x-auto">
            {result.debug_query}
          </pre>
        </div>
      )}
    </div>
  )
}

/** Report statistics panel (PHASE 2) */
function StatisticsPanel({ statistics }: { statistics: ValidationReportStatistics }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-3 bg-muted/50 rounded-lg">
          <p className="text-2xl font-bold">{statistics.total_validations || '-'}</p>
          <p className="text-xs text-muted-foreground">Total Checks</p>
        </div>
        <div className="text-center p-3 bg-green-50 dark:bg-green-950/20 rounded-lg">
          <p className="text-2xl font-bold text-green-600">
            {statistics.successful_validations}
          </p>
          <p className="text-xs text-muted-foreground">Passed</p>
        </div>
        <div className="text-center p-3 bg-red-50 dark:bg-red-950/20 rounded-lg">
          <p className="text-2xl font-bold text-red-600">
            {statistics.unsuccessful_validations}
          </p>
          <p className="text-xs text-muted-foreground">Failed</p>
        </div>
        <div className="text-center p-3 bg-muted/50 rounded-lg">
          <p className="text-2xl font-bold">
            {statistics.success_percent.toFixed(1)}%
          </p>
          <p className="text-xs text-muted-foreground">Success Rate</p>
        </div>
      </div>

      {Object.keys(statistics.issues_by_validator).length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Issues by Validator</h4>
          <div className="space-y-1">
            {Object.entries(statistics.issues_by_validator)
              .sort(([, a], [, b]) => b - a)
              .map(([name, count]) => (
                <div key={name} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{name}</span>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
          </div>
        </div>
      )}

      {statistics.most_problematic_columns.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Most Problematic Columns</h4>
          <div className="space-y-1">
            {statistics.most_problematic_columns.slice(0, 5).map(([col, count]) => (
              <div key={col} className="flex items-center justify-between text-sm">
                <code className="text-primary">{col}</code>
                <Badge variant="outline">{count} issues</Badge>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/** Execution summary panel (PHASE 4) */
function ExecutionSummaryPanel({ summary }: { summary: ValidatorExecutionSummary }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="text-center p-2 bg-muted/50 rounded-lg">
          <p className="text-xl font-bold">{summary.total_validators}</p>
          <p className="text-xs text-muted-foreground">Total</p>
        </div>
        <div className="text-center p-2 bg-green-50 dark:bg-green-950/20 rounded-lg">
          <p className="text-xl font-bold text-green-600">{summary.executed}</p>
          <p className="text-xs text-muted-foreground">Executed</p>
        </div>
        <div className="text-center p-2 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
          <p className="text-xl font-bold text-yellow-600">{summary.skipped}</p>
          <p className="text-xs text-muted-foreground">Skipped</p>
        </div>
        <div className="text-center p-2 bg-red-50 dark:bg-red-950/20 rounded-lg">
          <p className="text-xl font-bold text-red-600">{summary.failed}</p>
          <p className="text-xs text-muted-foreground">Failed</p>
        </div>
      </div>

      {summary.skipped_details && summary.skipped_details.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Skipped Validators</h4>
          <div className="space-y-1">
            {summary.skipped_details.map((info, i) => (
              <div
                key={i}
                className="flex items-start gap-2 text-sm p-2 bg-yellow-50 dark:bg-yellow-950/10 rounded"
              >
                <SkipForward className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium">{info.validator_name}</span>
                  {info.reason && (
                    <p className="text-xs text-muted-foreground">{info.reason}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/** Exception summary panel (PHASE 5) */
function ExceptionSummaryPanel({ summary }: { summary: ExceptionSummary }) {
  if (summary.total_exceptions === 0) return null

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="text-center p-2 bg-red-50 dark:bg-red-950/20 rounded-lg">
          <p className="text-xl font-bold text-red-600">{summary.total_exceptions}</p>
          <p className="text-xs text-muted-foreground">Exceptions</p>
        </div>
        <div className="text-center p-2 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
          <p className="text-xl font-bold text-yellow-600">{summary.total_retries}</p>
          <p className="text-xs text-muted-foreground">Retries</p>
        </div>
        <div className="text-center p-2 bg-muted/50 rounded-lg">
          <p className="text-xl font-bold">{summary.retryable_count}</p>
          <p className="text-xs text-muted-foreground">Retryable</p>
        </div>
        <div className="text-center p-2 bg-muted/50 rounded-lg">
          <p className="text-xl font-bold">
            {summary.total_exceptions - summary.retryable_count}
          </p>
          <p className="text-xs text-muted-foreground">Permanent</p>
        </div>
      </div>

      {Object.keys(summary.exceptions_by_type).length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">By Exception Type</h4>
          <div className="space-y-1">
            {Object.entries(summary.exceptions_by_type).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between text-sm">
                <code className="text-xs">{type}</code>
                <Badge variant="destructive">{count}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export default function Validations() {
  const { id } = useParams<{ id: string }>()
  const [validation, setValidation] = useState<Validation | null>(null)
  const [loading, setLoading] = useState(true)
  const [creatingVersion, setCreatingVersion] = useState(false)
  const { toast } = useToast()

  const loadValidation = useCallback(async () => {
    if (!id) return
    try {
      setLoading(true)
      const data = await getValidation(id)
      setValidation(data)
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load validation details',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [id, toast])

  useEffect(() => {
    loadValidation()
  }, [loadValidation])

  async function handleCreateVersion() {
    if (!validation) return
    try {
      setCreatingVersion(true)
      const result = await createVersion({
        validation_id: validation.id,
        strategy: 'incremental',
      })
      toast({
        title: 'Version Created',
        description: `Created version ${result.version.version_number}`,
      })
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to create version',
        variant: 'destructive',
      })
    } finally {
      setCreatingVersion(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!validation) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <XCircle className="h-12 w-12 text-destructive mb-4" />
        <p className="text-muted-foreground">Validation not found</p>
        <Button asChild className="mt-4">
          <Link to="/">Back to Dashboard</Link>
        </Button>
      </div>
    )
  }

  // Group issues by severity
  const issuesBySeverity = {
    critical: validation.issues.filter((i) => i.severity === 'critical'),
    high: validation.issues.filter((i) => i.severity === 'high'),
    medium: validation.issues.filter((i) => i.severity === 'medium'),
    low: validation.issues.filter((i) => i.severity === 'low'),
  }

  // Separate system error issues from data validation issues
  const systemErrors = validation.issues.filter((i) => i.exception_info)
  const dataIssues = validation.issues.filter((i) => !i.exception_info)

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to={`/sources/${validation.source_id}`}
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Source
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            {validation.passed ? (
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            ) : (
              <XCircle className="h-8 w-8 text-red-600" />
            )}
            <h1 className="text-3xl font-bold">
              Validation {validation.passed ? 'Passed' : 'Failed'}
            </h1>
          </div>
          <div className="flex items-center gap-3 mt-2">
            <p className="text-muted-foreground">
              {formatDate(validation.created_at)}
            </p>
            {validation.result_format && (
              <Badge variant="outline" className="text-xs">
                {validation.result_format.replace('_', ' ')}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={handleCreateVersion}
            disabled={creatingVersion || (validation.status !== 'success' && validation.status !== 'failed')}
          >
            {creatingVersion ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <GitBranch className="mr-2 h-4 w-4" />
            )}
            Create Version
          </Button>
          <ReportDownloadButton
            validationId={validation.id}
            disabled={validation.status !== 'success' && validation.status !== 'failed'}
          />
          <Badge
            variant={validation.passed ? 'success' : 'destructive'}
            className="text-lg px-4 py-1"
          >
            {validation.status}
          </Badge>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Total Issues</p>
                <p className="text-2xl font-bold">{validation.total_issues}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Rows3 className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Rows</p>
                <p className="text-2xl font-bold">
                  {formatNumber(validation.row_count)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Columns className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Columns</p>
                <p className="text-2xl font-bold">
                  {formatNumber(validation.column_count)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="text-2xl font-bold">
                  {formatDuration(validation.duration_ms)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Issue Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-red-200 dark:border-red-900">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Critical</span>
              <Badge variant="critical">{validation.critical_issues}</Badge>
            </div>
          </CardContent>
        </Card>
        <Card className="border-orange-200 dark:border-orange-900">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">High</span>
              <Badge variant="high">{validation.high_issues}</Badge>
            </div>
          </CardContent>
        </Card>
        <Card className="border-yellow-200 dark:border-yellow-900">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Medium</span>
              <Badge variant="medium">{validation.medium_issues}</Badge>
            </div>
          </CardContent>
        </Card>
        <Card className="border-green-200 dark:border-green-900">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Low</span>
              <Badge variant="low">{validation.low_issues}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* PHASE 2: Report Statistics */}
      {validation.statistics && (
        <CollapsibleSection
          title="Validation Statistics"
          icon={BarChart3}
          defaultOpen={false}
          badge={
            <Badge variant="outline" className="text-xs">
              {validation.statistics.success_percent.toFixed(0)}% pass rate
            </Badge>
          }
        >
          <StatisticsPanel statistics={validation.statistics} />
        </CollapsibleSection>
      )}

      {/* PHASE 4: Execution Summary */}
      {validation.validator_execution_summary && (
        <CollapsibleSection
          title="Execution Summary"
          icon={RefreshCw}
          defaultOpen={false}
          badge={
            validation.validator_execution_summary.skipped > 0 ? (
              <Badge variant="outline" className="text-xs text-yellow-600">
                {validation.validator_execution_summary.skipped} skipped
              </Badge>
            ) : undefined
          }
        >
          <ExecutionSummaryPanel summary={validation.validator_execution_summary} />
        </CollapsibleSection>
      )}

      {/* PHASE 5: Exception Summary */}
      {validation.exception_summary && validation.exception_summary.total_exceptions > 0 && (
        <CollapsibleSection
          title="Exception Summary"
          icon={Bug}
          defaultOpen={true}
          badge={
            <Badge variant="destructive" className="text-xs">
              {validation.exception_summary.total_exceptions} errors
            </Badge>
          }
        >
          <ExceptionSummaryPanel summary={validation.exception_summary} />
        </CollapsibleSection>
      )}

      {/* System Errors (PHASE 5) */}
      {systemErrors.length > 0 && (
        <Card className="border-amber-200 dark:border-amber-900">
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-600" />
              <CardTitle className="text-base">
                System Errors ({systemErrors.length})
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {systemErrors.map((issue, index) => (
                <div
                  key={index}
                  className="p-3 rounded-lg border border-amber-200 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-950/10"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-sm">
                        {issue.exception_info?.validator_name || issue.validator_name || issue.issue_type}
                        {issue.exception_info?.column && (
                          <span className="text-muted-foreground">
                            {' '}on <code className="text-primary">{issue.exception_info.column}</code>
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
                        {issue.exception_info?.exception_type}: {issue.exception_info?.exception_message}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {issue.exception_info?.is_retryable && (
                        <Badge variant="outline" className="text-xs">
                          <RefreshCw className="h-3 w-3 mr-1" />
                          Retried {issue.exception_info.retry_count}x
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs capitalize">
                        {issue.exception_info?.failure_category}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Issues Detail */}
      {dataIssues.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Issues Detail</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(['critical', 'high', 'medium', 'low'] as const).map((severity) => {
                const issues = issuesBySeverity[severity].filter((i) => !i.exception_info)
                if (issues.length === 0) return null

                return (
                  <div key={severity}>
                    <h3 className="font-semibold capitalize mb-2 flex items-center gap-2">
                      <Badge variant={severity}>{severity}</Badge>
                      <span className="text-muted-foreground">
                        ({issues.length})
                      </span>
                    </h3>
                    <div className="space-y-2">
                      {issues.map((issue, index) => (
                        <IssueCard key={index} issue={issue} />
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      ) : validation.issues.length === 0 ? (
        <Card>
          <CardContent className="py-16 flex flex-col items-center justify-center">
            <CheckCircle2 className="h-16 w-16 text-green-600 mb-4" />
            <h3 className="text-lg font-semibold">No Issues Found</h3>
            <p className="text-muted-foreground">
              All validation checks passed successfully.
            </p>
          </CardContent>
        </Card>
      ) : null}

      {/* Error Message */}
      {validation.error_message && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm text-destructive whitespace-pre-wrap">
              {validation.error_message}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

/** Individual issue card with expandable detail */
function IssueCard({ issue }: { issue: ValidationIssue }) {
  const [expanded, setExpanded] = useState(false)
  const hasDetail = issue.result && issue.result.element_count > 0

  return (
    <div className="p-4 rounded-lg border bg-card">
      <div
        className={`flex items-start justify-between ${hasDetail ? 'cursor-pointer' : ''}`}
        onClick={() => hasDetail && setExpanded(!expanded)}
      >
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="font-medium">
              <span className="text-primary">{issue.column}</span>
              {' - '}
              {issue.issue_type}
            </p>
            {issue.validator_name && issue.validator_name !== issue.issue_type && (
              <Badge variant="outline" className="text-xs">
                {issue.validator_name}
              </Badge>
            )}
          </div>
          {issue.details && (
            <p className="text-sm text-muted-foreground mt-1">
              {issue.details}
            </p>
          )}
          {(issue.expected !== undefined || issue.actual !== undefined) && (
            <div className="flex gap-4 mt-2 text-sm">
              {issue.expected !== undefined && (
                <span>
                  Expected:{' '}
                  <code className="bg-muted px-1 rounded">
                    {String(issue.expected)}
                  </code>
                </span>
              )}
              {issue.actual !== undefined && (
                <span>
                  Actual:{' '}
                  <code className="bg-muted px-1 rounded">
                    {String(issue.actual)}
                  </code>
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <span className="text-sm text-muted-foreground whitespace-nowrap">
            {formatNumber(issue.count)} occurrences
          </span>
          {hasDetail && (
            <Info className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {expanded && issue.result && (
        <IssueDetailPanel result={issue.result} />
      )}
    </div>
  )
}
