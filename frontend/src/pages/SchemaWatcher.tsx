/**
 * Schema Watcher Page.
 *
 * Provides continuous schema monitoring with alerts and run history.
 * Uses truthound's Schema Evolution APIs for change detection, rename detection,
 * and version management.
 */

import { useCallback, useEffect, useState } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Textarea } from '@/components/ui/textarea'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from '@/components/ui/sheet'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useToast } from '@/hooks/use-toast'
import { confirm } from '@/components/ConfirmDialog'
import {
  Loader2,
  Plus,
  RefreshCw,
  Play,
  Pause,
  Eye,
  Trash2,
  Edit,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Bell,
  History,
  GitBranch,
  Activity,
  ArrowRight,
  RotateCcw,
  GitCompare,
  Tag,
  Info,
} from 'lucide-react'
import { listSources, type Source } from '@/api/modules/sources'
import {
  listSchemaWatchers,
  getSchemaWatcher,
  createSchemaWatcher,
  updateSchemaWatcher,
  deleteSchemaWatcher,
  setSchemaWatcherStatus,
  checkSchemaWatcherNow,
  getSchemaWatcherStatistics,
  listSchemaWatcherAlerts,
  acknowledgeSchemaWatcherAlert,
  resolveSchemaWatcherAlert,
  getSchemaWatcherAlert,
  listSchemaWatcherRuns,
  watcherListSchemaVersions,
  watcherGetSchemaVersion,
  watcherDiffSchemaVersions,
  watcherRollbackSchemaVersion,
  type SchemaWatcher,
  type SchemaWatcherSummary,
  type SchemaWatcherStatistics,
  type SchemaWatcherAlert,
  type SchemaWatcherAlertSummary,
  type SchemaWatcherRunSummary,
  type SchemaWatcherStatus,
  type SchemaWatcherAlertStatus,
  type VersionStrategy,
  type SimilarityAlgorithm,
  type WatcherSchemaVersionSummary,
  type WatcherSchemaVersionResponse,
  type SchemaDiffResponse,
  type SchemaChangeDetail,
  type WatcherSchemaChangeSeverity,
  type CompatibilityLevel,
  WATCHER_STATUS_OPTIONS,
  ALERT_STATUS_OPTIONS,
  ALERT_SEVERITY_OPTIONS,
  VERSION_STRATEGY_OPTIONS,
  POLL_INTERVAL_OPTIONS,
  SIMILARITY_ALGORITHM_OPTIONS,
  WATCHER_CHANGE_TYPE_LABELS,
  WATCHER_CHANGE_SEVERITY_COLORS,
  COMPATIBILITY_LEVEL_LABELS,
} from '@/api/modules/schema-watcher'
import { formatDistanceToNow, format } from 'date-fns'

// ============================================================================
// Helper Functions
// ============================================================================

function getStatusBadge(status: SchemaWatcherStatus) {
  const colors: Record<SchemaWatcherStatus, string> = {
    active: 'bg-green-500/10 text-green-500 border-green-500/20',
    paused: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    stopped: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    error: 'bg-red-500/10 text-red-500 border-red-500/20',
  }
  return (
    <Badge variant="outline" className={colors[status]}>
      {status}
    </Badge>
  )
}

function getAlertSeverityBadge(severity: string) {
  const colors: Record<string, string> = {
    critical: 'bg-red-500/10 text-red-500 border-red-500/20',
    high: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    low: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    info: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  }
  return (
    <Badge variant="outline" className={colors[severity] || colors.info}>
      {severity}
    </Badge>
  )
}

function getAlertStatusBadge(status: SchemaWatcherAlertStatus) {
  const colors: Record<SchemaWatcherAlertStatus, string> = {
    open: 'bg-red-500/10 text-red-500 border-red-500/20',
    acknowledged: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    resolved: 'bg-green-500/10 text-green-500 border-green-500/20',
    suppressed: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  }
  return (
    <Badge variant="outline" className={colors[status]}>
      {status}
    </Badge>
  )
}

function getRunStatusBadge(status: string) {
  const colors: Record<string, string> = {
    completed: 'bg-green-500/10 text-green-500 border-green-500/20',
    running: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    pending: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    failed: 'bg-red-500/10 text-red-500 border-red-500/20',
  }
  return (
    <Badge variant="outline" className={colors[status] || colors.pending}>
      {status}
    </Badge>
  )
}

function getChangeSeverityBadge(severity: WatcherSchemaChangeSeverity) {
  const colors: Record<WatcherSchemaChangeSeverity, string> = {
    info: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    warning: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    critical: 'bg-red-500/10 text-red-500 border-red-500/20',
  }
  return (
    <Badge variant="outline" className={colors[severity]}>
      {severity}
    </Badge>
  )
}

function getCompatibilityBadge(level: CompatibilityLevel) {
  const colors: Record<CompatibilityLevel, string> = {
    compatible: 'bg-green-500/10 text-green-500 border-green-500/20',
    minor: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    breaking: 'bg-red-500/10 text-red-500 border-red-500/20',
  }
  return (
    <Badge variant="outline" className={colors[level]}>
      {COMPATIBILITY_LEVEL_LABELS[level]}
    </Badge>
  )
}

function formatDuration(ms: number | undefined | null): string {
  if (!ms) return '-'
  if (ms < 1000) return `${Math.round(ms)}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

// ============================================================================
// Main Component
// ============================================================================

export default function SchemaWatcherPage() {
  const t = useSafeIntlayer('schemaWatcher')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  // State
  const [activeTab, setActiveTab] = useState('watchers')
  const [isLoading, setIsLoading] = useState(true)
  const [watchers, setWatchers] = useState<SchemaWatcherSummary[]>([])
  const [alerts, setAlerts] = useState<SchemaWatcherAlertSummary[]>([])
  const [runs, setRuns] = useState<SchemaWatcherRunSummary[]>([])
  const [statistics, setStatistics] = useState<SchemaWatcherStatistics | null>(null)
  const [sources, setSources] = useState<Source[]>([])

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [alertStatusFilter, setAlertStatusFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')

  // Form state
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingWatcher, setEditingWatcher] = useState<SchemaWatcher | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    source_id: '',
    poll_interval_seconds: 60,
    only_breaking: false,
    enable_rename_detection: true,
    rename_similarity_threshold: 0.8,
    similarity_algorithm: 'composite' as SimilarityAlgorithm,
    version_strategy: 'semantic' as VersionStrategy,
    notify_on_change: true,
    track_history: true,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Alert detail state
  const [selectedAlert, setSelectedAlert] = useState<SchemaWatcherAlert | null>(null)
  const [showAlertDetail, setShowAlertDetail] = useState(false)
  const [isLoadingAlertDetail, setIsLoadingAlertDetail] = useState(false)

  // Version history state
  const [selectedWatcherForVersions, setSelectedWatcherForVersions] = useState<string | null>(null)
  const [versions, setVersions] = useState<WatcherSchemaVersionSummary[]>([])
  const [isLoadingVersions, setIsLoadingVersions] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<WatcherSchemaVersionResponse | null>(null)
  const [showVersionDetail, setShowVersionDetail] = useState(false)

  // Diff state
  const [showDiffDialog, setShowDiffDialog] = useState(false)
  const [diffFromVersion, setDiffFromVersion] = useState<string>('')
  const [diffToVersion, setDiffToVersion] = useState<string>('')
  const [diffResult, setDiffResult] = useState<SchemaDiffResponse | null>(null)
  const [isLoadingDiff, setIsLoadingDiff] = useState(false)

  // Rollback state
  const [showRollbackDialog, setShowRollbackDialog] = useState(false)
  const [rollbackToVersion, setRollbackToVersion] = useState<string>('')
  const [rollbackReason, setRollbackReason] = useState<string>('')
  const [isRollingBack, setIsRollingBack] = useState(false)

  // ============================================================================
  // Data Loading
  // ============================================================================

  const loadData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [watchersRes, alertsRes, runsRes, statsRes, sourcesRes] = await Promise.all([
        listSchemaWatchers({ limit: 100 }),
        listSchemaWatcherAlerts({ limit: 100 }),
        listSchemaWatcherRuns({ limit: 100 }),
        getSchemaWatcherStatistics(),
        listSources({ limit: 100 }),
      ])

      setWatchers(watchersRes.data)
      setAlerts(alertsRes.data)
      setRuns(runsRes.data)
      setStatistics(statsRes)
      setSources(sourcesRes.data)
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to load data',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast, common])

  useEffect(() => {
    loadData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ============================================================================
  // Handlers
  // ============================================================================

  const handleCreateWatcher = useCallback(async () => {
    if (!formData.name || !formData.source_id) {
      toast({
        title: str(common.error),
        description: 'Please fill in all required fields',
        variant: 'destructive',
      })
      return
    }

    setIsSubmitting(true)
    try {
      await createSchemaWatcher(formData)
      toast({ title: str(t.messages.watcherCreated) })
      setShowCreateForm(false)
      resetForm()
      loadData()
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to create watcher',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }, [formData, toast, t, common, loadData])

  const handleUpdateWatcher = useCallback(async () => {
    if (!editingWatcher) return

    setIsSubmitting(true)
    try {
      await updateSchemaWatcher(editingWatcher.id, formData)
      toast({ title: str(t.messages.watcherUpdated) })
      setEditingWatcher(null)
      resetForm()
      loadData()
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to update watcher',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }, [editingWatcher, formData, toast, t, common, loadData])

  const handleDeleteWatcher = useCallback(
    async (id: string) => {
      const confirmed = await confirm({
        title: str(t.watcher.deleteWatcher),
        description: str(t.messages.confirmDelete),
      })

      if (!confirmed) return

      try {
        await deleteSchemaWatcher(id)
        toast({ title: str(t.messages.watcherDeleted) })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to delete watcher',
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleStatusChange = useCallback(
    async (id: string, status: SchemaWatcherStatus) => {
      try {
        await setSchemaWatcherStatus(id, status)
        toast({
          title:
            status === 'active'
              ? str(t.messages.watcherResumed)
              : status === 'paused'
                ? str(t.messages.watcherPaused)
                : str(t.messages.watcherStopped),
        })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to change status',
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleCheckNow = useCallback(
    async (id: string) => {
      try {
        toast({ title: str(t.messages.checkStarted) })
        const result = await checkSchemaWatcherNow(id)
        toast({
          title: str(t.messages.checkCompleted),
          description: result.message,
        })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to run check',
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleAcknowledgeAlert = useCallback(
    async (id: string) => {
      try {
        await acknowledgeSchemaWatcherAlert(id)
        toast({ title: str(t.messages.alertAcknowledged) })
        loadData()
        if (selectedAlert?.id === id) {
          const updated = await getSchemaWatcherAlert(id)
          setSelectedAlert(updated)
        }
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to acknowledge alert',
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData, selectedAlert]
  )

  const handleResolveAlert = useCallback(
    async (id: string, notes?: string) => {
      try {
        await resolveSchemaWatcherAlert(id, { resolution_notes: notes })
        toast({ title: str(t.messages.alertResolved) })
        loadData()
        setShowAlertDetail(false)
        setSelectedAlert(null)
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to resolve alert',
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleViewAlertDetail = useCallback(async (alertId: string) => {
    setIsLoadingAlertDetail(true)
    setShowAlertDetail(true)
    try {
      const alert = await getSchemaWatcherAlert(alertId)
      setSelectedAlert(alert)
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to load alert details',
        variant: 'destructive',
      })
    } finally {
      setIsLoadingAlertDetail(false)
    }
  }, [toast, common])

  const handleEditWatcher = useCallback(async (id: string) => {
    try {
      const watcher = await getSchemaWatcher(id)
      setEditingWatcher(watcher)
      setFormData({
        name: watcher.name,
        source_id: watcher.source_id,
        poll_interval_seconds: watcher.poll_interval_seconds,
        only_breaking: watcher.only_breaking,
        enable_rename_detection: watcher.enable_rename_detection,
        rename_similarity_threshold: watcher.rename_similarity_threshold,
        similarity_algorithm: (watcher.config?.similarity_algorithm as SimilarityAlgorithm) || 'composite',
        version_strategy: watcher.version_strategy,
        notify_on_change: watcher.notify_on_change,
        track_history: watcher.track_history,
      })
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to load watcher',
        variant: 'destructive',
      })
    }
  }, [toast, common])

  const resetForm = useCallback(() => {
    setFormData({
      name: '',
      source_id: '',
      poll_interval_seconds: 60,
      only_breaking: false,
      enable_rename_detection: true,
      rename_similarity_threshold: 0.8,
      similarity_algorithm: 'composite',
      version_strategy: 'semantic',
      notify_on_change: true,
      track_history: true,
    })
  }, [])

  // ============================================================================
  // Version History Handlers (truthound integration)
  // ============================================================================

  const handleLoadVersions = useCallback(
    async (watcherId: string) => {
      setSelectedWatcherForVersions(watcherId)
      setIsLoadingVersions(true)
      try {
        const versionList = await watcherListSchemaVersions(watcherId, { limit: 50 })
        setVersions(versionList)
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to load version history',
          variant: 'destructive',
        })
      } finally {
        setIsLoadingVersions(false)
      }
    },
    [toast, common]
  )

  const handleViewVersion = useCallback(
    async (watcherId: string, version: string) => {
      try {
        const versionDetail = await watcherGetSchemaVersion(watcherId, version)
        setSelectedVersion(versionDetail)
        setShowVersionDetail(true)
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to load version details',
          variant: 'destructive',
        })
      }
    },
    [toast, common]
  )

  const handleDiff = useCallback(async () => {
    if (!selectedWatcherForVersions || !diffFromVersion) return

    setIsLoadingDiff(true)
    try {
      const result = await watcherDiffSchemaVersions(selectedWatcherForVersions, {
        from_version: diffFromVersion,
        to_version: diffToVersion || undefined,
      })
      setDiffResult(result)
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to generate diff',
        variant: 'destructive',
      })
    } finally {
      setIsLoadingDiff(false)
    }
  }, [selectedWatcherForVersions, diffFromVersion, diffToVersion, toast, common])

  const handleRollback = useCallback(async () => {
    if (!selectedWatcherForVersions || !rollbackToVersion) return

    const confirmed = await confirm({
      title: str(t.versions?.rollback || 'Rollback'),
      description: str(t.versions?.confirmRollback || 'Are you sure you want to rollback to this version?'),
    })

    if (!confirmed) return

    setIsRollingBack(true)
    try {
      await watcherRollbackSchemaVersion(selectedWatcherForVersions, {
        to_version: rollbackToVersion,
        reason: rollbackReason || undefined,
      })
      toast({ title: str(t.versions?.rollbackSuccess || 'Rollback successful') })
      setShowRollbackDialog(false)
      setRollbackToVersion('')
      setRollbackReason('')
      // Reload versions
      handleLoadVersions(selectedWatcherForVersions)
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to rollback',
        variant: 'destructive',
      })
    } finally {
      setIsRollingBack(false)
    }
  }, [selectedWatcherForVersions, rollbackToVersion, rollbackReason, toast, t, common, handleLoadVersions])

  // ============================================================================
  // Filtered Data
  // ============================================================================

  const filteredWatchers = watchers.filter((w) => {
    if (statusFilter !== 'all' && w.status !== statusFilter) return false
    return true
  })

  const filteredAlerts = alerts.filter((a) => {
    if (alertStatusFilter !== 'all' && a.status !== alertStatusFilter) return false
    if (severityFilter !== 'all' && a.severity !== severityFilter) return false
    return true
  })

  // ============================================================================
  // Render
  // ============================================================================

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{str(t.title)}</h1>
          <p className="text-muted-foreground">{str(t.subtitle)}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            {str(common.refresh)}
          </Button>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            {str(t.watcher.createWatcher)}
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {str(t.stats.totalWatchers)}
              </CardTitle>
              <Eye className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_watchers}</div>
              <p className="text-xs text-muted-foreground">
                {statistics.active_watchers} {str(t.status.active).toLowerCase()}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {str(t.stats.openAlerts)}
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.open_alerts}</div>
              <p className="text-xs text-muted-foreground">
                {statistics.total_alerts} {str(t.stats.totalAlerts).toLowerCase()}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {str(t.stats.totalChangesDetected)}
              </CardTitle>
              <GitBranch className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_changes_detected}</div>
              <p className="text-xs text-muted-foreground">
                {statistics.total_breaking_changes} {str(t.stats.totalBreakingChanges).toLowerCase()}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {str(t.stats.totalRuns)}
              </CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_runs}</div>
              <p className="text-xs text-muted-foreground">
                {statistics.successful_runs} {str(t.stats.successfulRuns).toLowerCase()}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="watchers">
            <Eye className="h-4 w-4 mr-2" />
            {str(t.tabs.watchers)}
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <Bell className="h-4 w-4 mr-2" />
            {str(t.tabs.alerts)}
            {statistics && statistics.open_alerts > 0 && (
              <Badge variant="destructive" className="ml-2">
                {statistics.open_alerts}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="runs">
            <History className="h-4 w-4 mr-2" />
            {str(t.tabs.runs)}
          </TabsTrigger>
          <TabsTrigger value="versions">
            <GitBranch className="h-4 w-4 mr-2" />
            {str(t.tabs?.versions || 'Versions')}
          </TabsTrigger>
        </TabsList>

        {/* Watchers Tab */}
        <TabsContent value="watchers" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={str(t.filters.status)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{str(t.filters.allStatuses)}</SelectItem>
                {WATCHER_STATUS_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Watchers Table */}
          {filteredWatchers.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Eye className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold">{str(t.messages.noWatchers)}</h3>
                <p className="text-muted-foreground">{str(t.messages.noWatchersDesc)}</p>
                <Button className="mt-4" onClick={() => setShowCreateForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  {str(t.watcher.createWatcher)}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{str(t.watcher.name)}</TableHead>
                    <TableHead>{str(t.watcher.source)}</TableHead>
                    <TableHead>{str(t.filters.status)}</TableHead>
                    <TableHead>{str(t.watcher.pollInterval)}</TableHead>
                    <TableHead>{str(t.stats.checkCount)}</TableHead>
                    <TableHead>{str(t.stats.changeCount)}</TableHead>
                    <TableHead>{str(t.stats.lastCheck)}</TableHead>
                    <TableHead>{str(common.actions)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredWatchers.map((watcher) => (
                    <TableRow key={watcher.id}>
                      <TableCell className="font-medium">{watcher.name}</TableCell>
                      <TableCell>{watcher.source_name || watcher.source_id}</TableCell>
                      <TableCell>{getStatusBadge(watcher.status)}</TableCell>
                      <TableCell>
                        {POLL_INTERVAL_OPTIONS.find(
                          (o) => o.value === watcher.poll_interval_seconds
                        )?.label || `${watcher.poll_interval_seconds}s`}
                      </TableCell>
                      <TableCell>{watcher.check_count}</TableCell>
                      <TableCell>{watcher.change_count}</TableCell>
                      <TableCell>
                        {watcher.last_check_at
                          ? formatDistanceToNow(new Date(watcher.last_check_at), {
                              addSuffix: true,
                            })
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleCheckNow(watcher.id)}
                            title={str(t.watcher.checkNow)}
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                          {watcher.status === 'active' ? (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleStatusChange(watcher.id, 'paused')}
                              title={str(t.watcher.pause)}
                            >
                              <Pause className="h-4 w-4" />
                            </Button>
                          ) : watcher.status === 'paused' ? (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleStatusChange(watcher.id, 'active')}
                              title={str(t.watcher.resume)}
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          ) : null}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEditWatcher(watcher.id)}
                            title={str(t.watcher.editWatcher)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteWatcher(watcher.id)}
                            title={str(t.watcher.deleteWatcher)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <Select value={alertStatusFilter} onValueChange={setAlertStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={str(t.filters.status)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{str(t.filters.allStatuses)}</SelectItem>
                {ALERT_STATUS_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={str(t.filters.severity)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{str(t.filters.allSeverities)}</SelectItem>
                {ALERT_SEVERITY_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Alerts Table */}
          {filteredAlerts.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bell className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold">{str(t.messages.noAlerts)}</h3>
                <p className="text-muted-foreground">{str(t.messages.noAlertsDesc)}</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{str(t.alertDetails.title)}</TableHead>
                    <TableHead>{str(t.filters.severity)}</TableHead>
                    <TableHead>{str(t.filters.status)}</TableHead>
                    <TableHead>{str(t.alertDetails.totalChanges)}</TableHead>
                    <TableHead>{str(t.alertDetails.breakingChanges)}</TableHead>
                    <TableHead>{str(t.common.createdAt)}</TableHead>
                    <TableHead>{str(common.actions)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAlerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="max-w-[300px] truncate">{alert.title}</TableCell>
                      <TableCell>{getAlertSeverityBadge(alert.severity)}</TableCell>
                      <TableCell>{getAlertStatusBadge(alert.status)}</TableCell>
                      <TableCell>{alert.total_changes}</TableCell>
                      <TableCell>
                        {alert.breaking_changes > 0 ? (
                          <Badge variant="destructive">{alert.breaking_changes}</Badge>
                        ) : (
                          0
                        )}
                      </TableCell>
                      <TableCell>
                        {formatDistanceToNow(new Date(alert.created_at), {
                          addSuffix: true,
                        })}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleViewAlertDetail(alert.id)}
                            title={str(t.alertActions.viewDetails)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {alert.status === 'open' && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleAcknowledgeAlert(alert.id)}
                              title={str(t.alertActions.acknowledge)}
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          {(alert.status === 'open' || alert.status === 'acknowledged') && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleResolveAlert(alert.id)}
                              title={str(t.alertActions.resolve)}
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        {/* Runs Tab */}
        <TabsContent value="runs" className="space-y-4">
          {runs.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <History className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold">{str(t.messages.noRuns)}</h3>
                <p className="text-muted-foreground">{str(t.messages.noRunsDesc)}</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{str(t.filters.watcher)}</TableHead>
                    <TableHead>{str(t.filters.status)}</TableHead>
                    <TableHead>{str(t.alertDetails.totalChanges)}</TableHead>
                    <TableHead>{str(t.alertDetails.breakingChanges)}</TableHead>
                    <TableHead>{str(t.common.duration)}</TableHead>
                    <TableHead>{str(t.common.startedAt)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={run.id}>
                      <TableCell>{run.watcher_id}</TableCell>
                      <TableCell>{getRunStatusBadge(run.status)}</TableCell>
                      <TableCell>{run.changes_detected}</TableCell>
                      <TableCell>
                        {run.breaking_detected > 0 ? (
                          <Badge variant="destructive">{run.breaking_detected}</Badge>
                        ) : (
                          0
                        )}
                      </TableCell>
                      <TableCell>{formatDuration(run.duration_ms)}</TableCell>
                      <TableCell>
                        {formatDistanceToNow(new Date(run.started_at), {
                          addSuffix: true,
                        })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        {/* Versions Tab */}
        <TabsContent value="versions" className="space-y-4">
          {/* Watcher Selector */}
          <div className="flex gap-4 items-end">
            <div className="flex-1 max-w-xs">
              <Label className="mb-2 block">{str(t.filters.watcher)}</Label>
              <Select
                value={selectedWatcherForVersions || ''}
                onValueChange={(value) => handleLoadVersions(value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder={str(t.versions?.selectWatcher || 'Select a watcher')} />
                </SelectTrigger>
                <SelectContent>
                  {watchers.map((w) => (
                    <SelectItem key={w.id} value={w.id}>
                      {w.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedWatcherForVersions && (
              <>
                <Button
                  variant="outline"
                  onClick={() => handleLoadVersions(selectedWatcherForVersions)}
                  disabled={isLoadingVersions}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingVersions ? 'animate-spin' : ''}`} />
                  {str(common.refresh)}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setDiffFromVersion('')
                    setDiffToVersion('')
                    setDiffResult(null)
                    setShowDiffDialog(true)
                  }}
                >
                  <GitCompare className="h-4 w-4 mr-2" />
                  {str(t.versions?.compare || 'Compare Versions')}
                </Button>
              </>
            )}
          </div>

          {!selectedWatcherForVersions ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <GitBranch className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold">{str(t.versions?.selectWatcherPrompt || 'Select a watcher')}</h3>
                <p className="text-muted-foreground">
                  {str(t.versions?.selectWatcherDesc || 'Select a watcher to view its schema version history')}
                </p>
              </CardContent>
            </Card>
          ) : isLoadingVersions ? (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </CardContent>
            </Card>
          ) : versions.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Tag className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold">{str(t.versions?.noVersions || 'No versions yet')}</h3>
                <p className="text-muted-foreground">
                  {str(t.versions?.noVersionsDesc || 'Run schema checks to capture version history')}
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{str(t.versions?.version || 'Version')}</TableHead>
                    <TableHead>{str(t.versions?.columns || 'Columns')}</TableHead>
                    <TableHead>{str(t.versions?.breaking || 'Breaking')}</TableHead>
                    <TableHead>{str(t.common.createdAt)}</TableHead>
                    <TableHead>{str(common.actions)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {versions.map((version, index) => (
                    <TableRow key={version.id}>
                      <TableCell className="font-mono">
                        <div className="flex items-center gap-2">
                          <Tag className="h-4 w-4 text-muted-foreground" />
                          {version.version}
                          {index === 0 && (
                            <Badge variant="secondary" className="text-xs">
                              {str(t.versions?.latest || 'Latest')}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{version.column_count}</TableCell>
                      <TableCell>
                        {version.has_breaking_changes ? (
                          <Badge variant="destructive">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            {str(t.versions?.hasBreaking || 'Yes')}
                          </Badge>
                        ) : (
                          <Badge variant="secondary">{str(t.versions?.noBreaking || 'No')}</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {version.created_at
                          ? formatDistanceToNow(new Date(version.created_at), { addSuffix: true })
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleViewVersion(selectedWatcherForVersions, version.version)}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                {str(t.versions?.viewDetails || 'View Details')}
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          {index > 0 && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => {
                                      setRollbackToVersion(version.version)
                                      setShowRollbackDialog(true)
                                    }}
                                  >
                                    <RotateCcw className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  {str(t.versions?.rollback || 'Rollback')}
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Create/Edit Watcher Sheet */}
      <Sheet
        open={showCreateForm || !!editingWatcher}
        onOpenChange={(open) => {
          if (!open) {
            setShowCreateForm(false)
            setEditingWatcher(null)
            resetForm()
          }
        }}
      >
        <SheetContent className="w-[500px] sm:max-w-[500px]">
          <SheetHeader>
            <SheetTitle>
              {editingWatcher ? str(t.watcher.editWatcher) : str(t.watcher.createWatcher)}
            </SheetTitle>
            <SheetDescription>
              {str(t.subtitle)}
            </SheetDescription>
          </SheetHeader>

          <ScrollArea className="h-[calc(100vh-200px)] mt-6">
            <div className="space-y-6 pr-4">
              {/* Name */}
              <div className="space-y-2">
                <Label htmlFor="name">{str(t.watcher.name)}</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder={str(t.watcher.namePlaceholder)}
                />
              </div>

              {/* Source */}
              <div className="space-y-2">
                <Label>{str(t.watcher.source)}</Label>
                <Select
                  value={formData.source_id}
                  onValueChange={(value) => setFormData({ ...formData, source_id: value })}
                  disabled={!!editingWatcher}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={str(t.watcher.selectSource)} />
                  </SelectTrigger>
                  <SelectContent>
                    {sources.map((source) => (
                      <SelectItem key={source.id} value={source.id}>
                        {source.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Poll Interval */}
              <div className="space-y-2">
                <Label>{str(t.watcher.pollInterval)}</Label>
                <Select
                  value={String(formData.poll_interval_seconds)}
                  onValueChange={(value) =>
                    setFormData({ ...formData, poll_interval_seconds: Number(value) })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {POLL_INTERVAL_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={String(opt.value)}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Version Strategy */}
              <div className="space-y-2">
                <Label>{str(t.watcher.versionStrategy)}</Label>
                <Select
                  value={formData.version_strategy}
                  onValueChange={(value) =>
                    setFormData({ ...formData, version_strategy: value as VersionStrategy })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {VERSION_STRATEGY_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label} - {opt.description}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              {/* Only Breaking */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{str(t.watcher.onlyBreaking)}</Label>
                  <p className="text-sm text-muted-foreground">
                    {str(t.watcher.onlyBreakingDesc)}
                  </p>
                </div>
                <Switch
                  checked={formData.only_breaking}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, only_breaking: checked })
                  }
                />
              </div>

              {/* Enable Rename Detection */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{str(t.watcher.enableRenameDetection)}</Label>
                  <p className="text-sm text-muted-foreground">
                    {str(t.watcher.enableRenameDetectionDesc)}
                  </p>
                </div>
                <Switch
                  checked={formData.enable_rename_detection}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, enable_rename_detection: checked })
                  }
                />
              </div>

              {/* Rename Detection Settings */}
              {formData.enable_rename_detection && (
                <>
                  {/* Similarity Algorithm - truthound supported */}
                  <div className="space-y-2">
                    <Label>{str(t.watcher?.similarityAlgorithm || 'Similarity Algorithm')}</Label>
                    <Select
                      value={formData.similarity_algorithm}
                      onValueChange={(value) =>
                        setFormData({ ...formData, similarity_algorithm: value as SimilarityAlgorithm })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SIMILARITY_ALGORITHM_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            <div className="flex flex-col">
                              <span>{opt.label}</span>
                              <span className="text-xs text-muted-foreground">{opt.description}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {str(t.watcher?.similarityAlgorithmDesc || 'Algorithm used by truthound ColumnRenameDetector')}
                    </p>
                  </div>

                  {/* Similarity Threshold */}
                  <div className="space-y-2">
                    <Label>
                      {str(t.watcher.renameSimilarityThreshold)}: {formData.rename_similarity_threshold}
                    </Label>
                    <Slider
                      value={[formData.rename_similarity_threshold]}
                      onValueChange={([value]) =>
                        setFormData({ ...formData, rename_similarity_threshold: value })
                      }
                      min={0.5}
                      max={1}
                      step={0.05}
                    />
                    <p className="text-xs text-muted-foreground">
                      {str(t.watcher?.similarityThresholdDesc || 'Minimum similarity score to consider as a rename')}
                    </p>
                  </div>
                </>
              )}

              <Separator />

              {/* Notify on Change */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{str(t.watcher.notifyOnChange)}</Label>
                  <p className="text-sm text-muted-foreground">
                    {str(t.watcher.notifyOnChangeDesc)}
                  </p>
                </div>
                <Switch
                  checked={formData.notify_on_change}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, notify_on_change: checked })
                  }
                />
              </div>

              {/* Track History */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{str(t.watcher.trackHistory)}</Label>
                  <p className="text-sm text-muted-foreground">
                    {str(t.watcher.trackHistoryDesc)}
                  </p>
                </div>
                <Switch
                  checked={formData.track_history}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, track_history: checked })
                  }
                />
              </div>
            </div>
          </ScrollArea>

          <SheetFooter className="mt-6">
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateForm(false)
                setEditingWatcher(null)
                resetForm()
              }}
            >
              {str(common.cancel)}
            </Button>
            <Button
              onClick={editingWatcher ? handleUpdateWatcher : handleCreateWatcher}
              disabled={isSubmitting}
            >
              {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingWatcher ? str(common.save) : str(common.create)}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      {/* Alert Detail Dialog */}
      <Dialog open={showAlertDetail} onOpenChange={setShowAlertDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{str(t.alertDetails.title)}</DialogTitle>
          </DialogHeader>

          {isLoadingAlertDetail ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : selectedAlert ? (
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">{selectedAlert.title}</h4>
                <div className="flex gap-2">
                  {getAlertSeverityBadge(selectedAlert.severity)}
                  {getAlertStatusBadge(selectedAlert.status)}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">{str(t.alertDetails.totalChanges)}:</span>
                  <span className="ml-2 font-medium">{selectedAlert.total_changes}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">{str(t.alertDetails.breakingChanges)}:</span>
                  <span className="ml-2 font-medium">{selectedAlert.breaking_changes}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">{str(t.alertDetails.impactScope)}:</span>
                  <span className="ml-2 font-medium">{selectedAlert.impact_scope || '-'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">{str(t.common.createdAt)}:</span>
                  <span className="ml-2 font-medium">
                    {format(new Date(selectedAlert.created_at), 'PPpp')}
                  </span>
                </div>
              </div>

              {selectedAlert.changes_summary?.changes && (
                <div>
                  <h5 className="font-semibold mb-2">{str(t.alertDetails.changesSummary)}</h5>
                  <ScrollArea className="h-[200px] rounded border p-2">
                    <div className="space-y-2">
                      {selectedAlert.changes_summary.changes.map((change, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-sm p-2 rounded bg-muted/50"
                        >
                          <Badge variant="outline">{change.type}</Badge>
                          <span className="font-mono">{change.column}</span>
                          {change.old_value && change.new_value && (
                            <span className="text-muted-foreground">
                              {change.old_value} → {change.new_value}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}

              {selectedAlert.recommendations && selectedAlert.recommendations.length > 0 && (
                <div>
                  <h5 className="font-semibold mb-2">{str(t.alertDetails.recommendations)}</h5>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    {selectedAlert.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedAlert.acknowledged_at && (
                <div className="text-sm">
                  <span className="text-muted-foreground">{str(t.alertDetails.acknowledgedAt)}:</span>
                  <span className="ml-2">
                    {format(new Date(selectedAlert.acknowledged_at), 'PPpp')}
                    {selectedAlert.acknowledged_by && ` by ${selectedAlert.acknowledged_by}`}
                  </span>
                </div>
              )}

              {selectedAlert.resolved_at && (
                <div className="text-sm">
                  <span className="text-muted-foreground">{str(t.alertDetails.resolvedAt)}:</span>
                  <span className="ml-2">
                    {format(new Date(selectedAlert.resolved_at), 'PPpp')}
                    {selectedAlert.resolved_by && ` by ${selectedAlert.resolved_by}`}
                  </span>
                </div>
              )}

              {selectedAlert.resolution_notes && (
                <div className="text-sm">
                  <span className="text-muted-foreground">{str(t.alertDetails.resolutionNotes)}:</span>
                  <p className="mt-1 p-2 rounded bg-muted">{selectedAlert.resolution_notes}</p>
                </div>
              )}
            </div>
          ) : null}

          <DialogFooter>
            {selectedAlert && selectedAlert.status === 'open' && (
              <Button
                variant="outline"
                onClick={() => handleAcknowledgeAlert(selectedAlert.id)}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                {str(t.alertActions.acknowledge)}
              </Button>
            )}
            {selectedAlert &&
              (selectedAlert.status === 'open' || selectedAlert.status === 'acknowledged') && (
                <Button onClick={() => handleResolveAlert(selectedAlert.id)}>
                  <XCircle className="h-4 w-4 mr-2" />
                  {str(t.alertActions.resolve)}
                </Button>
              )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Version Detail Dialog */}
      <Dialog open={showVersionDetail} onOpenChange={setShowVersionDetail}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              {str(t.versions?.versionDetails || 'Version Details')}
            </DialogTitle>
            <DialogDescription>
              {selectedVersion?.version}
            </DialogDescription>
          </DialogHeader>

          {selectedVersion && (
            <div className="space-y-4">
              {/* Version Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">{str(t.versions?.version || 'Version')}:</span>
                  <span className="ml-2 font-mono">{selectedVersion.version}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">{str(t.common.createdAt)}:</span>
                  <span className="ml-2">
                    {selectedVersion.created_at
                      ? format(new Date(selectedVersion.created_at), 'PPpp')
                      : '-'}
                  </span>
                </div>
              </div>

              {/* Breaking Changes Warning */}
              {selectedVersion.has_breaking_changes && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 text-red-500">
                  <AlertTriangle className="h-5 w-5" />
                  <span>{str(t.versions?.containsBreaking || 'This version contains breaking changes')}</span>
                </div>
              )}

              {/* Changes from Parent */}
              {selectedVersion.changes_from_parent && selectedVersion.changes_from_parent.length > 0 && (
                <div>
                  <h5 className="font-semibold mb-2">{str(t.versions?.changesFromParent || 'Changes from Previous')}</h5>
                  <ScrollArea className="h-[200px] rounded border p-2">
                    <div className="space-y-2">
                      {selectedVersion.changes_from_parent.map((change, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-sm p-2 rounded bg-muted/50"
                        >
                          {getChangeSeverityBadge(change.severity)}
                          <Badge variant="outline">{WATCHER_CHANGE_TYPE_LABELS[change.change_type]}</Badge>
                          <span className="font-mono">{change.column_name}</span>
                          {change.breaking && (
                            <Badge variant="destructive" className="text-xs">Breaking</Badge>
                          )}
                          {change.migration_hint && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Info className="h-4 w-4 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="max-w-xs">{change.migration_hint}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}

              {/* Schema Snapshot */}
              <div>
                <h5 className="font-semibold mb-2">{str(t.versions?.schemaSnapshot || 'Schema Snapshot')}</h5>
                <ScrollArea className="h-[200px] rounded border">
                  <pre className="p-3 text-xs font-mono">
                    {JSON.stringify(selectedVersion.schema, null, 2)}
                  </pre>
                </ScrollArea>
              </div>

              {/* Metadata */}
              {selectedVersion.metadata && Object.keys(selectedVersion.metadata).length > 0 && (
                <div>
                  <h5 className="font-semibold mb-2">{str(t.versions?.metadata || 'Metadata')}</h5>
                  <pre className="p-3 rounded bg-muted text-xs font-mono">
                    {JSON.stringify(selectedVersion.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVersionDetail(false)}>
              {str(common.close || 'Close')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Diff Dialog */}
      <Dialog open={showDiffDialog} onOpenChange={setShowDiffDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GitCompare className="h-5 w-5" />
              {str(t.versions?.compareVersions || 'Compare Versions')}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Version Selectors */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{str(t.versions?.fromVersion || 'From Version')}</Label>
                <Select value={diffFromVersion} onValueChange={setDiffFromVersion}>
                  <SelectTrigger>
                    <SelectValue placeholder={str(t.versions?.selectVersion || 'Select version')} />
                  </SelectTrigger>
                  <SelectContent>
                    {versions.map((v) => (
                      <SelectItem key={v.id} value={v.version}>
                        {v.version}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>{str(t.versions?.toVersion || 'To Version')} ({str(t.versions?.optional || 'optional')})</Label>
                <Select value={diffToVersion} onValueChange={setDiffToVersion}>
                  <SelectTrigger>
                    <SelectValue placeholder={str(t.versions?.latestDefault || 'Latest (default)')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">{str(t.versions?.latest || 'Latest')}</SelectItem>
                    {versions.map((v) => (
                      <SelectItem key={v.id} value={v.version}>
                        {v.version}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button onClick={handleDiff} disabled={!diffFromVersion || isLoadingDiff}>
              {isLoadingDiff && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <GitCompare className="h-4 w-4 mr-2" />
              {str(t.versions?.generateDiff || 'Generate Diff')}
            </Button>

            {/* Diff Result */}
            {diffResult && (
              <div className="space-y-4 mt-4">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-mono">{diffResult.from_version}</span>
                  <ArrowRight className="h-4 w-4" />
                  <span className="font-mono">{diffResult.to_version}</span>
                </div>

                {diffResult.changes.length === 0 ? (
                  <div className="p-4 rounded-lg bg-green-500/10 text-green-500 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5" />
                    {str(t.versions?.noChanges || 'No changes between these versions')}
                  </div>
                ) : (
                  <>
                    <div className="text-sm text-muted-foreground">
                      {diffResult.changes.length} {str(t.versions?.changesFound || 'changes found')}
                    </div>
                    <ScrollArea className="h-[300px] rounded border p-2">
                      <div className="space-y-2">
                        {diffResult.changes.map((change, i) => (
                          <div
                            key={i}
                            className="flex flex-col gap-1 text-sm p-3 rounded bg-muted/50"
                          >
                            <div className="flex items-center gap-2">
                              {getChangeSeverityBadge(change.severity)}
                              <Badge variant="outline">{WATCHER_CHANGE_TYPE_LABELS[change.change_type]}</Badge>
                              <span className="font-mono font-semibold">{change.column_name}</span>
                              {change.breaking && (
                                <Badge variant="destructive" className="text-xs">Breaking</Badge>
                              )}
                            </div>
                            <p className="text-muted-foreground">{change.description}</p>
                            {change.migration_hint && (
                              <p className="text-xs text-blue-500">
                                <Info className="h-3 w-3 inline mr-1" />
                                {change.migration_hint}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </ScrollArea>

                    {/* Text Diff */}
                    {diffResult.text_diff && (
                      <div>
                        <Label className="mb-2 block">{str(t.versions?.textDiff || 'Text Diff')}</Label>
                        <ScrollArea className="h-[200px] rounded border">
                          <pre className="p-3 text-xs font-mono whitespace-pre-wrap">
                            {diffResult.text_diff}
                          </pre>
                        </ScrollArea>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDiffDialog(false)}>
              {str(common.close || 'Close')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rollback Dialog */}
      <Dialog open={showRollbackDialog} onOpenChange={setShowRollbackDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="h-5 w-5" />
              {str(t.versions?.rollbackTo || 'Rollback to Version')}
            </DialogTitle>
            <DialogDescription>
              {str(t.versions?.rollbackDesc || 'This will create a new version with the schema from the selected version.')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
              <div className="flex items-center gap-2 text-yellow-500">
                <AlertTriangle className="h-5 w-5" />
                <span className="font-semibold">{str(t.versions?.targetVersion || 'Target Version')}: {rollbackToVersion}</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>{str(t.versions?.rollbackReason || 'Reason')} ({str(t.versions?.optional || 'optional')})</Label>
              <Textarea
                value={rollbackReason}
                onChange={(e) => setRollbackReason(e.target.value)}
                placeholder={str(t.versions?.rollbackReasonPlaceholder || 'Why are you rolling back?')}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRollbackDialog(false)}>
              {str(common.cancel)}
            </Button>
            <Button
              variant="destructive"
              onClick={handleRollback}
              disabled={isRollingBack}
            >
              {isRollingBack && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <RotateCcw className="h-4 w-4 mr-2" />
              {str(t.versions?.confirmRollback || 'Confirm Rollback')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
