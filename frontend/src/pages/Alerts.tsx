/**
 * Alerts Page
 *
 * Queue-aware incident workbench for operational alerts.
 */

import { useState, useEffect, useCallback } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, BellRing } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  UnifiedAlertList,
  AlertSummaryCards,
  AlertCorrelation,
} from '@/components/alerts'
import { SavedViewBar } from '@/components/control-plane/SavedViewBar'
import { request } from '@/api/core'
import { listUsers } from '@/api/modules/control-plane'
import { listIncidentQueues } from '@/api/modules/notifications'

type AlertSource = 'anomaly' | 'validation'
type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
type AlertStatus = 'open' | 'acknowledged' | 'resolved' | 'ignored'

interface UnifiedAlert {
  id: string
  source: AlertSource
  source_id: string
  source_name: string
  severity: AlertSeverity
  status: AlertStatus
  title: string
  message: string
  details: Record<string, unknown>
  workspace_id?: string | null
  queue_id?: string | null
  queue_name?: string | null
  assignee_user_id?: string | null
  assignee_name?: string | null
  assigned_at?: string | null
  assigned_by?: string | null
  timeline?: Array<Record<string, unknown>>
  acknowledged_at: string | null
  acknowledged_by: string | null
  resolved_at: string | null
  resolved_by: string | null
  created_at: string
  updated_at: string
}

interface AlertSummary {
  total_alerts: number
  active_alerts: number
  by_severity: {
    critical: number
    high: number
    medium: number
    low: number
    info: number
  }
  by_source: {
    anomaly: number
    validation: number
  }
  by_status: {
    open: number
    acknowledged: number
    resolved: number
    ignored: number
  }
  trend_24h: Array<{
    timestamp: string
    count: number
  }>
  top_sources: Array<{
    name: string
    count: number
  }>
}

interface AlertCorrelationData {
  alert_id: string
  related_alerts: UnifiedAlert[]
  correlation_type: string
  correlation_score: number
  common_factors: string[]
}

interface QueueOption {
  id: string
  name: string
}

interface UserOption {
  id: string
  display_name: string
}

export default function Alerts() {
  const content = useSafeIntlayer('alerts')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  const [alerts, setAlerts] = useState<UnifiedAlert[]>([])
  const [summary, setSummary] = useState<AlertSummary | null>(null)
  const [queues, setQueues] = useState<QueueOption[]>([])
  const [users, setUsers] = useState<UserOption[]>([])
  const [loading, setLoading] = useState(true)
  const [summaryLoading, setSummaryLoading] = useState(true)

  const [sourceFilter, setSourceFilter] = useState<AlertSource | null>(null)
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | null>(null)
  const [statusFilter, setStatusFilter] = useState<AlertStatus | null>(null)
  const [searchFilter, setSearchFilter] = useState('')
  const [queueFilter, setQueueFilter] = useState<string>('all')
  const [assigneeFilter, setAssigneeFilter] = useState<string>('all')

  const [selectedAlert, setSelectedAlert] = useState<UnifiedAlert | null>(null)
  const [correlations, setCorrelations] = useState<AlertCorrelationData[]>([])
  const [correlationsLoading, setCorrelationsLoading] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [assignQueueId, setAssignQueueId] = useState<string>('unassigned')
  const [assignUserId, setAssignUserId] = useState<string>('unassigned')

  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (sourceFilter) params.set('source', sourceFilter)
      if (severityFilter) params.set('severity', severityFilter)
      if (statusFilter) params.set('status', statusFilter)
      if (searchFilter.trim()) params.set('search', searchFilter.trim())
      if (queueFilter !== 'all') params.set('queue_id', queueFilter)
      if (assigneeFilter !== 'all') params.set('assignee_user_id', assigneeFilter)
      params.set('limit', '100')

      const response = await request<{ items: UnifiedAlert[] }>(`/alerts?${params.toString()}`)
      setAlerts(response.items)
    } catch {
      toast({
        title: str(common.error),
        description: 'Failed to load alerts',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [sourceFilter, severityFilter, statusFilter, searchFilter, queueFilter, assigneeFilter, toast, common.error])

  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true)
    try {
      const response = await request<AlertSummary>('/alerts/summary')
      setSummary(response)
    } catch (error) {
      console.error('Failed to load summary:', error)
    } finally {
      setSummaryLoading(false)
    }
  }, [])

  const fetchQueuesAndUsers = useCallback(async () => {
    try {
      const [queueResponse, userResponse] = await Promise.all([
        listIncidentQueues(),
        listUsers(),
      ])
      setQueues(queueResponse.items)
      setUsers(userResponse)
    } catch (error) {
      console.error('Failed to load queue metadata:', error)
    }
  }, [])

  const fetchCorrelations = useCallback(async (alertId: string) => {
    setCorrelationsLoading(true)
    try {
      const response = await request<{ correlations: AlertCorrelationData[] }>(`/alerts/${alertId}/correlations`)
      setCorrelations(response.correlations)
    } catch (error) {
      console.error('Failed to load correlations:', error)
      setCorrelations([])
    } finally {
      setCorrelationsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAlerts()
    fetchSummary()
    fetchQueuesAndUsers()
  }, [fetchAlerts, fetchSummary, fetchQueuesAndUsers])

  const handleViewDetails = (alert: UnifiedAlert) => {
    setSelectedAlert(alert)
    setAssignQueueId(alert.queue_id ?? 'unassigned')
    setAssignUserId(alert.assignee_user_id ?? 'unassigned')
    setDetailsOpen(true)
    fetchCorrelations(alert.id)
  }

  const handleViewCorrelations = (alert: UnifiedAlert) => {
    handleViewDetails(alert)
  }

  const handleRefresh = () => {
    fetchAlerts()
    fetchSummary()
    fetchQueuesAndUsers()
  }

  const handleAcknowledge = async () => {
    if (!selectedAlert) return
    await request(`/alerts/${selectedAlert.id}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ message: 'Acknowledged from incident workbench' }),
    })
    await handleRefresh()
    setSelectedAlert((current) => current ? { ...current, status: 'acknowledged' } : current)
  }

  const handleResolve = async () => {
    if (!selectedAlert) return
    await request(`/alerts/${selectedAlert.id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ message: 'Resolved from incident workbench' }),
    })
    await handleRefresh()
    setSelectedAlert((current) => current ? { ...current, status: 'resolved' } : current)
  }

  const handleAssign = async () => {
    if (!selectedAlert) return
    await request(`/alerts/${selectedAlert.id}/assign`, {
      method: 'POST',
      body: JSON.stringify({
        queue_id: assignQueueId === 'unassigned' ? null : assignQueueId,
        assignee_user_id: assignUserId === 'unassigned' ? null : assignUserId,
        message: 'Assignment updated from incident workbench',
      }),
    })
    await handleRefresh()
    const updated = await request<UnifiedAlert>(`/alerts/${selectedAlert.id}`)
    setSelectedAlert(updated)
  }

  const applySavedView = (filters: Record<string, unknown>) => {
    setSourceFilter((filters.source as AlertSource) ?? null)
    setSeverityFilter((filters.severity as AlertSeverity) ?? null)
    setStatusFilter((filters.status as AlertStatus) ?? null)
    setSearchFilter(String(filters.search ?? ''))
    setQueueFilter((filters.queue_id as string) ?? 'all')
    setAssigneeFilter((filters.assignee_user_id as string) ?? 'all')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BellRing className="h-6 w-6 text-primary" />
            {str(content.title)}
          </h1>
          <p className="text-muted-foreground">{str(content.subtitle)}</p>
        </div>
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          {str(content.actions.refresh)}
        </Button>
      </div>

      <AlertSummaryCards summary={summary} loading={summaryLoading} />

      <div className="space-y-4">
        <SavedViewBar
          scope="alerts"
          currentFilters={{
            source: sourceFilter,
            severity: severityFilter,
            status: statusFilter,
            search: searchFilter,
            queue_id: queueFilter,
            assignee_user_id: assigneeFilter,
          }}
          onApply={applySavedView}
        />

        <h2 className="text-lg font-semibold">Incident Workbench</h2>
        <UnifiedAlertList
          alerts={alerts}
          loading={loading}
          sourceFilter={sourceFilter}
          severityFilter={severityFilter}
          statusFilter={statusFilter}
          search={searchFilter}
          queueFilter={queueFilter}
          assigneeFilter={assigneeFilter}
          queues={queues}
          assignees={users.map((user) => ({ id: user.id, name: user.display_name }))}
          onSourceFilterChange={setSourceFilter}
          onSeverityFilterChange={setSeverityFilter}
          onStatusFilterChange={setStatusFilter}
          onSearchChange={setSearchFilter}
          onQueueFilterChange={setQueueFilter}
          onAssigneeFilterChange={setAssigneeFilter}
          onViewDetails={handleViewDetails}
          onViewCorrelations={handleViewCorrelations}
        />
      </div>

      <Sheet open={detailsOpen} onOpenChange={setDetailsOpen}>
        <SheetContent className="sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>{str(content.details.title)}</SheetTitle>
            <SheetDescription>
              {selectedAlert?.title}
            </SheetDescription>
          </SheetHeader>

          {selectedAlert && (
            <div className="mt-6 space-y-6">
              <div className="space-y-4">
                <div>
                  <Label className="text-muted-foreground">{str(content.details.message)}</Label>
                  <p className="mt-1">{selectedAlert.message}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">{str(content.details.source)}</Label>
                    <p className="mt-1">{selectedAlert.source_name}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">{str(content.columns.status)}</Label>
                    <p className="mt-1 capitalize">{selectedAlert.status}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">Queue</Label>
                    <p className="mt-1">{selectedAlert.queue_name ?? 'Unassigned'}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Assignee</Label>
                    <p className="mt-1">{selectedAlert.assignee_name ?? 'Unassigned'}</p>
                  </div>
                </div>

                <div>
                  <Label className="text-muted-foreground">{str(content.details.createdAt)}</Label>
                  <p className="mt-1">{new Date(selectedAlert.created_at).toLocaleString()}</p>
                </div>
              </div>

              <div className="space-y-3">
                <Label className="text-muted-foreground">Assignment</Label>
                <div className="grid grid-cols-2 gap-3">
                  <Select value={assignQueueId} onValueChange={setAssignQueueId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Queue" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unassigned">Unassigned</SelectItem>
                      {queues.map((queue) => (
                        <SelectItem key={queue.id} value={queue.id}>{queue.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Select value={assignUserId} onValueChange={setAssignUserId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Assignee" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unassigned">Unassigned</SelectItem>
                      {users.map((user) => (
                        <SelectItem key={user.id} value={user.id}>{user.display_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleAssign}>Save Assignment</Button>
                  <Button variant="outline" onClick={handleAcknowledge} disabled={selectedAlert.status === 'acknowledged' || selectedAlert.status === 'resolved'}>
                    Acknowledge
                  </Button>
                  <Button onClick={handleResolve} disabled={selectedAlert.status === 'resolved'}>
                    Resolve
                  </Button>
                </div>
              </div>

              <AlertCorrelation
                alertId={selectedAlert.id}
                correlations={correlations}
                loading={correlationsLoading}
                onViewAlert={handleViewDetails}
              />
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}
