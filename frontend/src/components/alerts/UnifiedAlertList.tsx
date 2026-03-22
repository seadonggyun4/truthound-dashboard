/**
 * UnifiedAlertList Component
 *
 * Displays a filterable, sortable list of queue-aware operational alerts.
 */

import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import { formatDistanceToNow } from 'date-fns'
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Clock,
  Eye,
  ExternalLink,
  MoreHorizontal,
  Search,
} from 'lucide-react'
import { cn, parseUTC } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'

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
  queue_id?: string | null
  queue_name?: string | null
  assignee_user_id?: string | null
  assignee_name?: string | null
  acknowledged_at: string | null
  acknowledged_by: string | null
  resolved_at: string | null
  resolved_by: string | null
  created_at: string
  updated_at: string
}

interface UnifiedAlertListProps {
  alerts: UnifiedAlert[]
  loading?: boolean
  sourceFilter: AlertSource | null
  severityFilter: AlertSeverity | null
  statusFilter: AlertStatus | null
  search: string
  queueFilter: string
  assigneeFilter: string
  queues: Array<{ id: string; name: string }>
  assignees: Array<{ id: string; name: string }>
  onSourceFilterChange: (source: AlertSource | null) => void
  onSeverityFilterChange: (severity: AlertSeverity | null) => void
  onStatusFilterChange: (status: AlertStatus | null) => void
  onSearchChange: (value: string) => void
  onQueueFilterChange: (queueId: string) => void
  onAssigneeFilterChange: (userId: string) => void
  onViewDetails: (alert: UnifiedAlert) => void
  onViewCorrelations?: (alert: UnifiedAlert) => void
}

const severityConfig: Record<AlertSeverity, { icon: typeof AlertTriangle; color: string; bgColor: string }> = {
  critical: { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100 dark:bg-red-900/30' },
  high: { icon: AlertCircle, color: 'text-orange-500', bgColor: 'bg-orange-100 dark:bg-orange-900/30' },
  medium: { icon: AlertCircle, color: 'text-yellow-500', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30' },
  low: { icon: Info, color: 'text-blue-500', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  info: { icon: Info, color: 'text-gray-500', bgColor: 'bg-gray-100 dark:bg-gray-900/30' },
}

const statusConfig: Record<AlertStatus, { icon: typeof Clock; color: string }> = {
  open: { icon: AlertCircle, color: 'text-red-500' },
  acknowledged: { icon: Eye, color: 'text-yellow-500' },
  resolved: { icon: CheckCircle, color: 'text-green-500' },
  ignored: { icon: Clock, color: 'text-gray-400' },
}

const sourceLabels: Record<AlertSource, string> = {
  anomaly: 'Anomaly',
  validation: 'Validation',
}

export function UnifiedAlertList({
  alerts,
  loading = false,
  sourceFilter,
  severityFilter,
  statusFilter,
  search,
  queueFilter,
  assigneeFilter,
  queues,
  assignees,
  onSourceFilterChange,
  onSeverityFilterChange,
  onStatusFilterChange,
  onSearchChange,
  onQueueFilterChange,
  onAssigneeFilterChange,
  onViewDetails,
  onViewCorrelations,
}: UnifiedAlertListProps) {
  const content = useIntlayer('alerts')

  const SeverityIcon = ({ severity }: { severity: AlertSeverity }) => {
    const config = severityConfig[severity]
    const Icon = config.icon
    return <Icon className={cn('h-4 w-4', config.color)} />
  }

  const StatusIcon = ({ status }: { status: AlertStatus }) => {
    const config = statusConfig[status]
    const Icon = config.icon
    return <Icon className={cn('h-4 w-4', config.color)} />
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative min-w-[220px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search incidents"
            className="pl-9"
          />
        </div>

        <Select
          value={sourceFilter ?? 'all'}
          onValueChange={(v) => onSourceFilterChange(v === 'all' ? null : v as AlertSource)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={str(content.sources.all)} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{str(content.sources.all)}</SelectItem>
            <SelectItem value="anomaly">{str(content.sources.anomaly)}</SelectItem>
            <SelectItem value="validation">{str(content.sources.validation)}</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={severityFilter ?? 'all'}
          onValueChange={(v) => onSeverityFilterChange(v === 'all' ? null : v as AlertSeverity)}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder={str(content.filters.severity)} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{str(content.filters.severity)}</SelectItem>
            <SelectItem value="critical">{str(content.severity.critical)}</SelectItem>
            <SelectItem value="high">{str(content.severity.high)}</SelectItem>
            <SelectItem value="medium">{str(content.severity.medium)}</SelectItem>
            <SelectItem value="low">{str(content.severity.low)}</SelectItem>
            <SelectItem value="info">{str(content.severity.info)}</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={statusFilter ?? 'all'}
          onValueChange={(v) => onStatusFilterChange(v === 'all' ? null : v as AlertStatus)}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder={str(content.status.all)} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{str(content.status.all)}</SelectItem>
            <SelectItem value="open">{str(content.status.open)}</SelectItem>
            <SelectItem value="acknowledged">{str(content.status.acknowledged)}</SelectItem>
            <SelectItem value="resolved">{str(content.status.resolved)}</SelectItem>
            <SelectItem value="ignored">{str(content.status.ignored)}</SelectItem>
          </SelectContent>
        </Select>

        <Select value={queueFilter} onValueChange={onQueueFilterChange}>
          <SelectTrigger className="w-[170px]">
            <SelectValue placeholder="Queue" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Queues</SelectItem>
            {queues.map((queue) => (
              <SelectItem key={queue.id} value={queue.id}>{queue.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={assigneeFilter} onValueChange={onAssigneeFilterChange}>
          <SelectTrigger className="w-[170px]">
            <SelectValue placeholder="Assignee" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Assignees</SelectItem>
            {assignees.map((assignee) => (
              <SelectItem key={assignee.id} value={assignee.id}>{assignee.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">{str(content.columns.severity)}</TableHead>
              <TableHead className="w-[100px]">{str(content.columns.source)}</TableHead>
              <TableHead>{str(content.columns.title)}</TableHead>
              <TableHead className="w-[120px]">{str(content.columns.status)}</TableHead>
              <TableHead className="w-[150px]">{str(content.columns.createdAt)}</TableHead>
              <TableHead className="w-[80px]">{str(content.columns.actions)}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center">
                  <div className="flex items-center justify-center">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  </div>
                </TableCell>
              </TableRow>
            ) : alerts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  {str(content.empty.noAlerts)}
                </TableCell>
              </TableRow>
            ) : (
              alerts.map((alert) => (
                <TableRow key={alert.id} className="hover:bg-muted/50">
                  <TableCell>
                    <div className={cn(
                      'inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium',
                      severityConfig[alert.severity].bgColor
                    )}>
                      <SeverityIcon severity={alert.severity} />
                      <span className="capitalize">{alert.severity}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-normal">
                      {sourceLabels[alert.source]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium line-clamp-1">{alert.title}</div>
                      <div className="text-xs text-muted-foreground line-clamp-1">
                        {alert.source_name}
                        {alert.queue_name ? ` • ${alert.queue_name}` : ''}
                        {alert.assignee_name ? ` • ${alert.assignee_name}` : ''}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <StatusIcon status={alert.status} />
                      <span className="capitalize text-sm">{alert.status}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDistanceToNow(parseUTC(alert.created_at), { addSuffix: true })}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onViewDetails(alert)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View details
                        </DropdownMenuItem>
                        {onViewCorrelations && (
                          <DropdownMenuItem onClick={() => onViewCorrelations(alert)}>
                            <ExternalLink className="h-4 w-4 mr-2" />
                            View correlations
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
