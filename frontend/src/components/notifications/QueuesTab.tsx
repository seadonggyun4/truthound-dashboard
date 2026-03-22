import { useCallback, useEffect, useState } from 'react'
import { Inbox, Loader2, Pencil, Plus, Trash2, Users } from 'lucide-react'

import {
  createIncidentQueue,
  deleteIncidentQueue,
  listIncidentQueues,
  type IncidentQueue,
  updateIncidentQueue,
} from '@/api/modules/notifications'
import { listUsers, type User } from '@/api/modules/control-plane'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Switch } from '@/components/ui/switch'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'

interface QueuesTabProps {
  onChanged?: () => void | Promise<void>
}

interface QueueFormState {
  name: string
  description: string
  is_default: boolean
  is_active: boolean
  member_ids: string[]
}

const EMPTY_FORM: QueueFormState = {
  name: '',
  description: '',
  is_default: false,
  is_active: true,
  member_ids: [],
}

export function QueuesTab({ onChanged }: QueuesTabProps) {
  const t = useSafeIntlayer('notificationsAdvanced')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()
  const queueContent = (t as { queues?: Record<string, any> }).queues ?? {}

  const [queues, setQueues] = useState<IncidentQueue[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingQueue, setEditingQueue] = useState<IncidentQueue | null>(null)
  const [form, setForm] = useState<QueueFormState>(EMPTY_FORM)

  const loadData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [queueResponse, userResponse] = await Promise.all([
        listIncidentQueues(),
        listUsers(),
      ])
      setQueues(queueResponse.items)
      setUsers(userResponse)
    } catch {
      toast({
        title: str(common.error),
        description: str(t.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast, common.error, t])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const openCreate = () => {
    setEditingQueue(null)
    setForm(EMPTY_FORM)
    setDialogOpen(true)
  }

  const openEdit = (queue: IncidentQueue) => {
    setEditingQueue(queue)
    setForm({
      name: queue.name,
      description: queue.description ?? '',
      is_default: queue.is_default,
      is_active: queue.is_active,
      member_ids: queue.members.map((member) => member.user_id),
    })
    setDialogOpen(true)
  }

  const toggleMember = (userId: string) => {
    setForm((current) => ({
      ...current,
      member_ids: current.member_ids.includes(userId)
        ? current.member_ids.filter((id) => id !== userId)
        : [...current.member_ids, userId],
    }))
  }

  const handleSave = async () => {
    if (!form.name.trim()) {
      return
    }
    try {
      setIsSaving(true)
      if (editingQueue) {
        await updateIncidentQueue(editingQueue.id, {
          name: form.name.trim(),
          description: form.description.trim() || undefined,
          is_default: form.is_default,
          is_active: form.is_active,
          member_ids: form.member_ids,
        })
      } else {
        await createIncidentQueue({
          name: form.name.trim(),
          description: form.description.trim() || undefined,
          is_default: form.is_default,
          is_active: form.is_active,
          member_ids: form.member_ids,
        })
      }
      setDialogOpen(false)
      setEditingQueue(null)
      setForm(EMPTY_FORM)
      await loadData()
      await onChanged?.()
      toast({
        title: editingQueue ? 'Queue updated' : 'Queue created',
      })
    } catch {
      toast({
        title: str(common.error),
        description: editingQueue ? 'Failed to update queue' : 'Failed to create queue',
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (queue: IncidentQueue) => {
    if (queue.is_default) {
      return
    }
    try {
      await deleteIncidentQueue(queue.id)
      await loadData()
      await onChanged?.()
      toast({ title: 'Queue deleted' })
    } catch {
      toast({
        title: str(common.error),
        description: 'Failed to delete queue',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <Inbox className="h-5 w-5" />
              {str(queueContent.title ?? 'Incident Queues')}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {str(queueContent.subtitle ?? 'Manage routing queues and responders')}
            </p>
          </div>
          <Button onClick={openCreate}>
            <Plus className="mr-2 h-4 w-4" />
            {str(queueContent.create ?? 'Create Queue')}
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : queues.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              {str(queueContent.empty ?? 'No queues configured yet')}
            </div>
          ) : (
            <div className="rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{str(queueContent.columns?.name ?? 'Queue')}</TableHead>
                    <TableHead>{str(queueContent.columns?.members ?? 'Members')}</TableHead>
                    <TableHead>{str(queueContent.columns?.status ?? 'Status')}</TableHead>
                    <TableHead className="text-right">{str(common.actions)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {queues.map((queue) => (
                    <TableRow key={queue.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{queue.name}</span>
                            {queue.is_default && (
                              <Badge variant="secondary">{str(queueContent.badges?.default ?? 'Default')}</Badge>
                            )}
                            {!queue.is_active && (
                              <Badge variant="outline">{str(queueContent.badges?.inactive ?? 'Inactive')}</Badge>
                            )}
                          </div>
                          {queue.description && (
                            <p className="text-xs text-muted-foreground">{queue.description}</p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 text-sm">
                            <Users className="h-4 w-4 text-muted-foreground" />
                            {queue.members.length}
                          </div>
                          {queue.members.length > 0 && (
                            <p className="text-xs text-muted-foreground">
                              {queue.members.slice(0, 3).map((member) => member.user_name).join(', ')}
                              {queue.members.length > 3 ? ` +${queue.members.length - 3}` : ''}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={queue.is_active ? 'outline' : 'secondary'}>
                          {queue.is_active
                            ? str(queueContent.badges?.active ?? 'Active')
                            : str(queueContent.badges?.inactive ?? 'Inactive')}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={() => openEdit(queue)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={queue.is_default}
                            onClick={() => void handleDelete(queue)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingQueue
                ? str(queueContent.edit ?? 'Edit Queue')
                : str(queueContent.create ?? 'Create Queue')}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="queue-name">{str(queueContent.form?.name ?? 'Queue Name')}</Label>
                <Input
                  id="queue-name"
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="Platform Operations"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="queue-description">{str(queueContent.form?.description ?? 'Description')}</Label>
                <Textarea
                  id="queue-description"
                  value={form.description}
                  onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                  rows={3}
                  placeholder="Queue for platform and data reliability incidents"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center justify-between rounded-lg border px-4 py-3">
                <div>
                  <Label>{str(queueContent.form?.defaultQueue ?? 'Default Queue')}</Label>
                  <p className="text-xs text-muted-foreground">
                    {str(queueContent.form?.defaultQueueDescription ?? 'Route newly created incidents here by default')}
                  </p>
                </div>
                <Switch
                  checked={form.is_default}
                  onCheckedChange={(checked) => setForm((current) => ({ ...current, is_default: checked }))}
                />
              </div>

              <div className="flex items-center justify-between rounded-lg border px-4 py-3">
                <div>
                  <Label>{str(queueContent.form?.active ?? 'Active Queue')}</Label>
                  <p className="text-xs text-muted-foreground">
                    {str(queueContent.form?.activeDescription ?? 'Inactive queues remain visible but stop receiving new assignments')}
                  </p>
                </div>
                <Switch
                  checked={form.is_active}
                  onCheckedChange={(checked) => setForm((current) => ({ ...current, is_active: checked }))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>{str(queueContent.form?.members ?? 'Queue Members')}</Label>
              <ScrollArea className="h-52 rounded-lg border">
                <div className="space-y-2 p-4">
                  {users.map((user) => (
                    <label
                      key={user.id}
                      className="flex cursor-pointer items-start gap-3 rounded-md border p-3 hover:bg-muted/40"
                    >
                      <Checkbox
                        checked={form.member_ids.includes(user.id)}
                        onCheckedChange={() => toggleMember(user.id)}
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium">{user.display_name}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              {str(common.cancel)}
            </Button>
            <Button onClick={() => void handleSave()} disabled={isSaving || !form.name.trim()}>
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {str(common.save)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
