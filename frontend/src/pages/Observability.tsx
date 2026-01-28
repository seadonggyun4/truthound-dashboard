/**
 * Observability page
 *
 * Displays audit logs, metrics, and tracing information
 * using truthound's observability module.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Activity,
  BarChart3,
  Clock,
  Database,
  Eye,
  FileText,
  Loader2,
  RefreshCw,
  Settings,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Zap,
} from 'lucide-react'
import { useIntlayer } from '@/providers'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  getObservabilityConfig,
  updateObservabilityConfig,
  getObservabilityStats,
  listAuditEvents,
  getAuditStats,
  getStoreMetrics,
  getTracingStats,
  type ObservabilityConfig,
  type ObservabilityStats,
  type AuditEvent,
  type AuditEventType,
  type AuditStatus,
  type StoreMetrics,
} from '@/api/modules/observability'

export default function Observability() {
  const content = useIntlayer('observability')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [activeTab, setActiveTab] = useState('overview')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [config, setConfig] = useState<ObservabilityConfig | null>(null)
  const [stats, setStats] = useState<ObservabilityStats | null>(null)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [storeMetrics, setStoreMetrics] = useState<StoreMetrics | null>(null)

  // Audit filters
  const [auditEventType, setAuditEventType] = useState<AuditEventType | ''>('')
  const [auditStatus, setAuditStatus] = useState<AuditStatus | ''>('')

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [configData, statsData] = await Promise.all([
        getObservabilityConfig(),
        getObservabilityStats(),
      ])
      setConfig(configData)
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load observability data:', error)
      toast({
        title: str(common.error),
        description: 'Failed to load observability data',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast, common])

  const loadAuditEvents = useCallback(async () => {
    try {
      const response = await listAuditEvents({
        event_type: auditEventType || undefined,
        status: auditStatus || undefined,
        limit: 100,
      })
      setAuditEvents(response.items)
    } catch (error) {
      console.error('Failed to load audit events:', error)
    }
  }, [auditEventType, auditStatus])

  const loadStoreMetrics = useCallback(async () => {
    try {
      const metrics = await getStoreMetrics()
      setStoreMetrics(metrics)
    } catch (error) {
      console.error('Failed to load store metrics:', error)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    if (activeTab === 'audit') {
      loadAuditEvents()
    } else if (activeTab === 'metrics') {
      loadStoreMetrics()
    }
  }, [activeTab, loadAuditEvents, loadStoreMetrics])

  // Save config
  const handleSaveConfig = async () => {
    if (!config) return
    setIsSaving(true)
    try {
      const updated = await updateObservabilityConfig(config)
      setConfig(updated)
      toast({
        title: str(common.success),
        description: str(content.config.configSaved),
      })
    } catch (error) {
      console.error('Failed to save config:', error)
      toast({
        title: str(common.error),
        description: str(content.config.configSaveFailed),
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Update config field
  const updateConfig = <K extends keyof ObservabilityConfig>(
    field: K,
    value: ObservabilityConfig[K]
  ) => {
    if (!config) return
    setConfig({ ...config, [field]: value })
  }

  // Format bytes
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Get status badge color
  const getStatusBadge = (status: AuditStatus) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-500">{str(content.audit.statuses.success)}</Badge>
      case 'failure':
        return <Badge variant="destructive">{str(content.audit.statuses.failure)}</Badge>
      case 'partial':
        return <Badge className="bg-yellow-500">{str(content.audit.statuses.partial)}</Badge>
      case 'denied':
        return <Badge className="bg-red-500">{str(content.audit.statuses.denied)}</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{content.title}</h1>
          <p className="text-muted-foreground">{content.description}</p>
        </div>
        <Button variant="outline" onClick={loadData} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          {common.refresh}
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            {content.tabs.overview}
          </TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {content.tabs.audit}
          </TabsTrigger>
          <TabsTrigger value="metrics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            {content.tabs.metrics}
          </TabsTrigger>
          <TabsTrigger value="tracing" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            {content.tabs.tracing}
          </TabsTrigger>
          <TabsTrigger value="config" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            {content.tabs.config}
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.overview.totalEvents}
                </CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.audit.total_events.toLocaleString() ?? 0}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.overview.eventsToday}
                </CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.audit.events_today.toLocaleString() ?? 0}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.overview.errorRate}
                </CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((stats?.audit.error_rate ?? 0) * 100).toFixed(1)}%
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.overview.cacheHitRate}
                </CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((stats?.store_metrics.cache_hit_rate ?? 0) * 100).toFixed(1)}%
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Event types distribution */}
          {stats && Object.keys(stats.audit.by_event_type).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{content.metrics.operationsByType}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(stats.audit.by_event_type).map(([type, count]) => (
                    <Badge key={type} variant="secondary">
                      {type}: {count}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Audit Tab */}
        <TabsContent value="audit" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{content.audit.title}</CardTitle>
              <CardDescription>{content.audit.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Filters */}
              <div className="flex gap-4">
                <div className="w-48">
                  <Label>{content.audit.filterByType}</Label>
                  <Select
                    value={auditEventType}
                    onValueChange={(v) => setAuditEventType(v as AuditEventType)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All types</SelectItem>
                      <SelectItem value="create">{str(content.audit.eventTypes.create)}</SelectItem>
                      <SelectItem value="read">{str(content.audit.eventTypes.read)}</SelectItem>
                      <SelectItem value="update">{str(content.audit.eventTypes.update)}</SelectItem>
                      <SelectItem value="delete">{str(content.audit.eventTypes.delete)}</SelectItem>
                      <SelectItem value="query">{str(content.audit.eventTypes.query)}</SelectItem>
                      <SelectItem value="error">{str(content.audit.eventTypes.error)}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="w-48">
                  <Label>{content.audit.filterByStatus}</Label>
                  <Select
                    value={auditStatus}
                    onValueChange={(v) => setAuditStatus(v as AuditStatus)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All statuses" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All statuses</SelectItem>
                      <SelectItem value="success">{str(content.audit.statuses.success)}</SelectItem>
                      <SelectItem value="failure">{str(content.audit.statuses.failure)}</SelectItem>
                      <SelectItem value="partial">{str(content.audit.statuses.partial)}</SelectItem>
                      <SelectItem value="denied">{str(content.audit.statuses.denied)}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end">
                  <Button variant="outline" onClick={loadAuditEvents}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    {common.refresh}
                  </Button>
                </div>
              </div>

              {/* Events table */}
              {auditEvents.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{content.audit.timestamp}</TableHead>
                      <TableHead>{content.audit.eventType}</TableHead>
                      <TableHead>{content.audit.status}</TableHead>
                      <TableHead>{content.audit.itemId}</TableHead>
                      <TableHead>{content.audit.duration}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditEvents.map((event) => (
                      <TableRow key={event.event_id}>
                        <TableCell className="font-mono text-sm">
                          {new Date(event.timestamp).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{event.event_type}</Badge>
                        </TableCell>
                        <TableCell>{getStatusBadge(event.status)}</TableCell>
                        <TableCell className="font-mono text-sm">
                          {event.item_id || '-'}
                        </TableCell>
                        <TableCell>
                          {event.duration_ms ? `${event.duration_ms.toFixed(1)} ms` : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  {content.audit.noEvents}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.metrics.operationsTotal}
                </CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {storeMetrics?.operations_total.toLocaleString() ?? 0}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.metrics.bytesRead}
                </CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatBytes(storeMetrics?.bytes_read_total ?? 0)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.metrics.bytesWritten}
                </CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatBytes(storeMetrics?.bytes_written_total ?? 0)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {content.metrics.errorsTotal}
                </CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-500">
                  {storeMetrics?.errors_total ?? 0}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{content.metrics.cacheHitRate}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>{content.metrics.cacheHits}</span>
                  <span className="font-bold text-green-500">
                    {storeMetrics?.cache_hits.toLocaleString() ?? 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>{content.metrics.cacheMisses}</span>
                  <span className="font-bold text-red-500">
                    {storeMetrics?.cache_misses.toLocaleString() ?? 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>{content.metrics.cacheHitRate}</span>
                  <span className="font-bold">
                    {((storeMetrics?.cache_hit_rate ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>{content.metrics.avgOperationDuration}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {storeMetrics?.avg_operation_duration_ms?.toFixed(2) ?? '-'}{' '}
                  <span className="text-sm font-normal text-muted-foreground">ms</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tracing Tab */}
        <TabsContent value="tracing" className="space-y-6">
          {!config?.enable_tracing ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Zap className="mx-auto h-12 w-12 text-muted-foreground" />
                <p className="mt-4 text-muted-foreground">{content.tracing.disabled}</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {content.tracing.totalTraces}
                  </CardTitle>
                  <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {stats?.tracing?.total_traces ?? 0}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {content.tracing.totalSpans}
                  </CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {stats?.tracing?.total_spans ?? 0}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {content.tracing.tracesToday}
                  </CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {stats?.tracing?.traces_today ?? 0}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {content.tracing.avgTraceDuration}
                  </CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {stats?.tracing?.avg_trace_duration_ms?.toFixed(2) ?? '-'} ms
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Config Tab */}
        <TabsContent value="config" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{content.config.title}</CardTitle>
              <CardDescription>{content.config.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Audit Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Audit Logging</h3>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>{content.config.enableAudit}</Label>
                    <p className="text-sm text-muted-foreground">
                      {content.config.enableAuditDescription}
                    </p>
                  </div>
                  <Switch
                    checked={config?.enable_audit ?? false}
                    onCheckedChange={(checked) => updateConfig('enable_audit', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>{content.config.auditRotateDaily}</Label>
                    <p className="text-sm text-muted-foreground">
                      {content.config.auditRotateDailyDescription}
                    </p>
                  </div>
                  <Switch
                    checked={config?.audit_rotate_daily ?? false}
                    onCheckedChange={(checked) => updateConfig('audit_rotate_daily', checked)}
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>{content.config.auditLogPath}</Label>
                    <Input
                      value={config?.audit_log_path ?? ''}
                      onChange={(e) => updateConfig('audit_log_path', e.target.value || null)}
                      placeholder=".truthound/audit"
                    />
                    <p className="text-xs text-muted-foreground">
                      {content.config.auditLogPathDescription}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label>{content.config.auditMaxEvents}</Label>
                    <Input
                      type="number"
                      min={1000}
                      max={1000000}
                      value={config?.audit_max_events ?? 10000}
                      onChange={(e) => updateConfig('audit_max_events', parseInt(e.target.value) || 10000)}
                    />
                    <p className="text-xs text-muted-foreground">
                      {content.config.auditMaxEventsDescription}
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{content.config.redactFields}</Label>
                  <Input
                    value={config?.redact_fields?.join(', ') ?? ''}
                    onChange={(e) =>
                      updateConfig(
                        'redact_fields',
                        e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                      )
                    }
                    placeholder="password, api_key, token, secret"
                  />
                  <p className="text-xs text-muted-foreground">
                    {content.config.redactFieldsDescription}
                  </p>
                </div>
              </div>

              {/* Metrics Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Metrics</h3>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>{content.config.enableMetrics}</Label>
                    <p className="text-sm text-muted-foreground">
                      {content.config.enableMetricsDescription}
                    </p>
                  </div>
                  <Switch
                    checked={config?.enable_metrics ?? false}
                    onCheckedChange={(checked) => updateConfig('enable_metrics', checked)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>{content.config.metricsPrefix}</Label>
                  <Input
                    value={config?.metrics_prefix ?? ''}
                    onChange={(e) => updateConfig('metrics_prefix', e.target.value)}
                    placeholder="truthound_dashboard"
                  />
                  <p className="text-xs text-muted-foreground">
                    {content.config.metricsPrefixDescription}
                  </p>
                </div>
              </div>

              {/* Tracing Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Distributed Tracing</h3>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>{content.config.enableTracing}</Label>
                    <p className="text-sm text-muted-foreground">
                      {content.config.enableTracingDescription}
                    </p>
                  </div>
                  <Switch
                    checked={config?.enable_tracing ?? false}
                    onCheckedChange={(checked) => updateConfig('enable_tracing', checked)}
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>{content.config.tracingServiceName}</Label>
                    <Input
                      value={config?.tracing_service_name ?? ''}
                      onChange={(e) => updateConfig('tracing_service_name', e.target.value)}
                      placeholder="truthound-dashboard"
                    />
                    <p className="text-xs text-muted-foreground">
                      {content.config.tracingServiceNameDescription}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label>{content.config.tracingEndpoint}</Label>
                    <Input
                      value={config?.tracing_endpoint ?? ''}
                      onChange={(e) => updateConfig('tracing_endpoint', e.target.value || null)}
                      placeholder="http://localhost:4317"
                    />
                    <p className="text-xs text-muted-foreground">
                      {content.config.tracingEndpointDescription}
                    </p>
                  </div>
                </div>
              </div>

              {/* Save Button */}
              <div className="flex justify-end">
                <Button onClick={handleSaveConfig} disabled={isSaving}>
                  {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {content.config.saveConfig}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
