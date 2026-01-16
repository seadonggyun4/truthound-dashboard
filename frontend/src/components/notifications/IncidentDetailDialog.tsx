/**
 * IncidentDetailDialog - View escalation incident details.
 *
 * Displays:
 * - Incident metadata
 * - Current state and escalation level
 * - Event timeline
 * - Action buttons (acknowledge, resolve)
 */

import {
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  Bell,
  User,
  ArrowUp,
  Shield,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { formatDate } from '@/lib/utils'
import { cn } from '@/lib/utils'

export type IncidentState =
  | 'pending'
  | 'triggered'
  | 'acknowledged'
  | 'escalated'
  | 'resolved'

export interface IncidentEvent {
  id: string
  event_type: 'created' | 'triggered' | 'escalated' | 'acknowledged' | 'resolved'
  message: string
  user_id?: string
  level?: number
  created_at: string
}

export interface EscalationIncident {
  id: string
  policy_id: string
  policy_name?: string
  notification_id: string
  state: IncidentState
  current_level: number
  max_level: number
  escalation_count: number
  acknowledged_by?: string
  acknowledged_at?: string
  resolved_by?: string
  resolved_at?: string
  resolution_note?: string
  events?: IncidentEvent[]
  created_at: string
  updated_at: string
}

interface IncidentDetailDialogProps {
  incident: EscalationIncident | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onAcknowledge?: (id: string) => void
  onResolve?: (id: string, note?: string) => void
  isAcknowledging?: boolean
  isResolving?: boolean
}

const STATE_CONFIG: Record<
  IncidentState,
  {
    label: string
    icon: typeof Bell
    color: string
    bgColor: string
  }
> = {
  pending: {
    label: 'Pending',
    icon: Clock,
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
  },
  triggered: {
    label: 'Triggered',
    icon: Bell,
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  acknowledged: {
    label: 'Acknowledged',
    icon: CheckCircle2,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  escalated: {
    label: 'Escalated',
    icon: ArrowUp,
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
  },
  resolved: {
    label: 'Resolved',
    icon: Shield,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
}

const EVENT_ICONS: Record<string, typeof Bell> = {
  created: Clock,
  triggered: Bell,
  escalated: ArrowUp,
  acknowledged: CheckCircle2,
  resolved: Shield,
}

export function IncidentDetailDialog({
  incident,
  open,
  onOpenChange,
  onAcknowledge,
  onResolve,
  isAcknowledging = false,
  isResolving = false,
}: IncidentDetailDialogProps) {
  if (!incident) return null

  const stateConfig = STATE_CONFIG[incident.state]
  const StateIcon = stateConfig.icon
  const canAcknowledge =
    incident.state === 'triggered' || incident.state === 'escalated'
  const canResolve =
    incident.state === 'triggered' ||
    incident.state === 'escalated' ||
    incident.state === 'acknowledged'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Incident Details
          </DialogTitle>
          <DialogDescription>
            {incident.policy_name || incident.policy_id}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4 py-4">
            {/* Status Overview */}
            <Card>
              <CardContent className="py-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Status</p>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={cn(
                          'gap-1',
                          stateConfig.bgColor,
                          stateConfig.color
                        )}
                      >
                        <StateIcon className="h-3 w-3" />
                        {stateConfig.label}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      Current Level
                    </p>
                    <p className="font-medium">
                      {incident.current_level} / {incident.max_level}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      Escalations
                    </p>
                    <p className="font-medium">{incident.escalation_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Created</p>
                    <p className="text-sm">{formatDate(incident.created_at)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Acknowledgment/Resolution Info */}
            {(incident.acknowledged_by || incident.resolved_by) && (
              <Card>
                <CardContent className="py-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {incident.acknowledged_by && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">
                          Acknowledged By
                        </p>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">
                            {incident.acknowledged_by}
                          </span>
                        </div>
                        {incident.acknowledged_at && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDate(incident.acknowledged_at)}
                          </p>
                        )}
                      </div>
                    )}
                    {incident.resolved_by && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">
                          Resolved By
                        </p>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">
                            {incident.resolved_by}
                          </span>
                        </div>
                        {incident.resolved_at && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDate(incident.resolved_at)}
                          </p>
                        )}
                        {incident.resolution_note && (
                          <p className="text-sm mt-2 p-2 bg-muted rounded">
                            {incident.resolution_note}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Event Timeline */}
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Event Timeline
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                {!incident.events || incident.events.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No events recorded
                  </p>
                ) : (
                  <div className="relative">
                    <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-muted" />
                    <div className="space-y-4">
                      {incident.events.map((event, index) => {
                        const EventIcon = EVENT_ICONS[event.event_type] || Bell
                        return (
                          <div key={event.id || index} className="relative pl-8">
                            <div
                              className={cn(
                                'absolute left-0 w-6 h-6 rounded-full flex items-center justify-center',
                                event.event_type === 'resolved'
                                  ? 'bg-green-100'
                                  : event.event_type === 'acknowledged'
                                  ? 'bg-blue-100'
                                  : event.event_type === 'escalated'
                                  ? 'bg-orange-100'
                                  : 'bg-muted'
                              )}
                            >
                              <EventIcon
                                className={cn(
                                  'h-3 w-3',
                                  event.event_type === 'resolved'
                                    ? 'text-green-600'
                                    : event.event_type === 'acknowledged'
                                    ? 'text-blue-600'
                                    : event.event_type === 'escalated'
                                    ? 'text-orange-600'
                                    : 'text-muted-foreground'
                                )}
                              />
                            </div>
                            <div className="pb-2">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-sm capitalize">
                                  {event.event_type.replace('_', ' ')}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(event.created_at)}
                                </span>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {event.message}
                              </p>
                              {event.user_id && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  By: {event.user_id}
                                </p>
                              )}
                              {event.level && (
                                <Badge variant="outline" className="mt-1 text-xs">
                                  Level {event.level}
                                </Badge>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Metadata */}
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm">Details</CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Incident ID:</span>
                  </div>
                  <div className="font-mono text-xs">
                    {incident.id.slice(0, 8)}...
                  </div>
                  <div>
                    <span className="text-muted-foreground">Policy ID:</span>
                  </div>
                  <div className="font-mono text-xs">
                    {incident.policy_id.slice(0, 8)}...
                  </div>
                  <div>
                    <span className="text-muted-foreground">
                      Notification ID:
                    </span>
                  </div>
                  <div className="font-mono text-xs">
                    {incident.notification_id.slice(0, 8)}...
                  </div>
                  <div>
                    <span className="text-muted-foreground">Last Updated:</span>
                  </div>
                  <div>{formatDate(incident.updated_at)}</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>

        <Separator />

        <DialogFooter className="pt-4">
          <div className="flex gap-2 w-full justify-between">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            <div className="flex gap-2">
              {canAcknowledge && onAcknowledge && (
                <Button
                  variant="outline"
                  onClick={() => onAcknowledge(incident.id)}
                  disabled={isAcknowledging}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  {isAcknowledging ? 'Acknowledging...' : 'Acknowledge'}
                </Button>
              )}
              {canResolve && onResolve && (
                <Button
                  onClick={() => onResolve(incident.id)}
                  disabled={isResolving}
                >
                  <Shield className="h-4 w-4 mr-2" />
                  {isResolving ? 'Resolving...' : 'Resolve'}
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default IncidentDetailDialog
