import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  listSources,
  listSchedules,
  createSchedule,
  deleteSchedule,
  pauseSchedule,
  resumeSchedule,
  runScheduleNow,
  type Source,
  type Schedule,
} from '@/api/client'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import {
  Clock,
  Plus,
  MoreVertical,
  Play,
  Pause,
  Trash2,
  PlayCircle,
  Calendar,
} from 'lucide-react'

const CRON_PRESETS = [
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every 6 hours', value: '0 */6 * * *' },
  { label: 'Daily at midnight', value: '0 0 * * *' },
  { label: 'Daily at 8 AM', value: '0 8 * * *' },
  { label: 'Every Monday', value: '0 0 * * 1' },
  { label: 'Every month', value: '0 0 1 * *' },
]

export default function Schedules() {
  const { toast } = useToast()
  const [sources, setSources] = useState<Source[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  // Form state
  const [formName, setFormName] = useState('')
  const [formSourceId, setFormSourceId] = useState('')
  const [formCron, setFormCron] = useState('0 0 * * *')
  const [formNotify, setFormNotify] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      const [sourcesRes, schedulesRes] = await Promise.all([
        listSources(),
        listSchedules(),
      ])
      setSources(sourcesRes.data)
      setSchedules(schedulesRes.data)
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to load data',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formName || !formSourceId || !formCron) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Please fill in all required fields',
      })
      return
    }

    try {
      setCreating(true)
      const result = await createSchedule({
        name: formName,
        source_id: formSourceId,
        cron_expression: formCron,
        notify_on_failure: formNotify,
      })

      setSchedules((prev) => [result.data, ...prev])
      setDialogOpen(false)
      setFormName('')
      setFormSourceId('')
      setFormCron('0 0 * * *')

      toast({
        title: 'Schedule created',
        description: `${result.data.name} has been scheduled`,
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to create schedule',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteSchedule(id)
      setSchedules((prev) => prev.filter((s) => s.id !== id))
      toast({ title: 'Schedule deleted' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to delete',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    }
  }

  const handlePause = async (id: string) => {
    try {
      const result = await pauseSchedule(id)
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? result.schedule : s))
      )
      toast({ title: 'Schedule paused' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to pause',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    }
  }

  const handleResume = async (id: string) => {
    try {
      const result = await resumeSchedule(id)
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? result.schedule : s))
      )
      toast({ title: 'Schedule resumed' })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to resume',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    }
  }

  const handleRunNow = async (id: string) => {
    try {
      const result = await runScheduleNow(id)
      toast({
        title: 'Validation triggered',
        description: result.passed ? 'Validation passed' : 'Validation completed',
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to run',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    }
  }

  const getSourceName = (id: string) => {
    const source = sources.find((s) => s.id === id)
    return source?.name || id.slice(0, 8)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Schedules</h1>
          <p className="text-muted-foreground">Manage scheduled validation runs</p>
        </div>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Schedule
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Schedule</DialogTitle>
              <DialogDescription>
                Set up automated validation runs for a data source
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input
                  placeholder="Daily validation"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Source</Label>
                <Select value={formSourceId} onValueChange={setFormSourceId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select source..." />
                  </SelectTrigger>
                  <SelectContent>
                    {sources.map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Schedule</Label>
                <Select value={formCron} onValueChange={setFormCron}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CRON_PRESETS.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Custom cron expression"
                  value={formCron}
                  onChange={(e) => setFormCron(e.target.value)}
                  className="mt-2"
                />
                <p className="text-xs text-muted-foreground">
                  Format: minute hour day month weekday
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="notify"
                  checked={formNotify}
                  onCheckedChange={setFormNotify}
                />
                <Label htmlFor="notify">Notify on failure</Label>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={creating}>
                {creating ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Schedules List */}
      {schedules.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No schedules yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create a schedule to automate validation runs
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Schedule
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {schedules.map((s) => (
            <Card key={s.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Clock
                      className={`h-5 w-5 ${
                        s.is_active ? 'text-green-500' : 'text-muted-foreground'
                      }`}
                    />
                    <div>
                      <CardTitle className="text-lg">{s.name}</CardTitle>
                      <CardDescription>
                        Source: {getSourceName(s.source_id)}
                      </CardDescription>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={s.is_active ? 'default' : 'secondary'}>
                      {s.is_active ? 'Active' : 'Paused'}
                    </Badge>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleRunNow(s.id)}>
                          <PlayCircle className="h-4 w-4 mr-2" />
                          Run Now
                        </DropdownMenuItem>
                        {s.is_active ? (
                          <DropdownMenuItem onClick={() => handlePause(s.id)}>
                            <Pause className="h-4 w-4 mr-2" />
                            Pause
                          </DropdownMenuItem>
                        ) : (
                          <DropdownMenuItem onClick={() => handleResume(s.id)}>
                            <Play className="h-4 w-4 mr-2" />
                            Resume
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => handleDelete(s.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Cron Expression</div>
                    <div className="font-mono">{s.cron_expression}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Last Run</div>
                    <div>{s.last_run_at ? formatDate(s.last_run_at) : 'Never'}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Next Run</div>
                    <div>
                      {s.next_run_at && s.is_active
                        ? formatDate(s.next_run_at)
                        : '-'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
