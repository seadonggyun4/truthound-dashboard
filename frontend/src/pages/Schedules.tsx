import { useState, useEffect, useCallback, useMemo } from 'react'
import { useIntlayer } from '@/providers'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  listValidators,
  getSourceSchema,
  type Source,
  type Schedule,
  type ValidatorDefinition,
  type ValidatorConfig,
  type Schema,
} from '@/api/client'
import { formatDate } from '@/lib/utils'
import { str } from '@/lib/intlayer-utils'
import { useToast } from '@/hooks/use-toast'
import { ValidatorSelector } from '@/components/validators'
import {
  Clock,
  Plus,
  MoreVertical,
  Play,
  Pause,
  Trash2,
  PlayCircle,
  Calendar,
  Sliders,
} from 'lucide-react'

export default function Schedules() {
  const nav = useIntlayer('nav')
  const schedules_t = useIntlayer('schedules')
  const common = useIntlayer('common')
  const errors = useIntlayer('errors')
  const validation = useIntlayer('validation')
  const { toast } = useToast()

  const CRON_PRESETS = useMemo(() => [
    { label: schedules_t.cronPresets.everyHour, value: '0 * * * *' },
    { label: schedules_t.cronPresets.every6Hours, value: '0 */6 * * *' },
    { label: schedules_t.cronPresets.dailyMidnight, value: '0 0 * * *' },
    { label: schedules_t.cronPresets.daily8am, value: '0 8 * * *' },
    { label: schedules_t.cronPresets.everyMonday, value: '0 0 * * 1' },
    { label: schedules_t.cronPresets.everyMonth, value: '0 0 1 * *' },
  ], [schedules_t])
  const [sources, setSources] = useState<Source[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  // Validator configuration state
  const [validators, setValidators] = useState<ValidatorDefinition[]>([])
  const [validatorConfigs, setValidatorConfigs] = useState<ValidatorConfig[]>([])
  const [loadingValidators, setLoadingValidators] = useState(false)
  const [selectedSourceSchema, setSelectedSourceSchema] = useState<Schema | null>(null)
  const [dialogTab, setDialogTab] = useState<string>('basic')

  // Form state
  const [formName, setFormName] = useState('')
  const [formSourceId, setFormSourceId] = useState('')
  const [formCron, setFormCron] = useState('0 0 * * *')
  const [formNotify, setFormNotify] = useState(true)

  const fetchData = useCallback(async () => {
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
        title: str(common.error),
        description: err instanceof Error ? err.message : str(errors.loadFailed),
      })
    } finally {
      setLoading(false)
    }
  }, [toast, common, errors])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Load validators when dialog opens
  const loadValidators = useCallback(async () => {
    if (validators.length > 0) return
    try {
      setLoadingValidators(true)
      const validatorDefs = await listValidators()
      setValidators(validatorDefs)
    } catch {
      toast({
        variant: 'destructive',
        title: str(common.error),
        description: str(errors.loadFailed),
      })
    } finally {
      setLoadingValidators(false)
    }
  }, [validators.length, toast, common, errors])

  // Load schema when source changes
  const loadSourceSchema = useCallback(async (sourceId: string) => {
    if (!sourceId) {
      setSelectedSourceSchema(null)
      return
    }
    try {
      const schema = await getSourceSchema(sourceId)
      setSelectedSourceSchema(schema)
    } catch {
      setSelectedSourceSchema(null)
    }
  }, [])

  const handleCreate = async () => {
    if (!formName || !formSourceId || !formCron) {
      toast({
        variant: 'destructive',
        title: str(common.error),
        description: str(schedules_t.fillRequired),
      })
      return
    }

    try {
      setCreating(true)
      // Build config with validator_configs if any are configured
      const enabledConfigs = validatorConfigs.filter((c) => c.enabled)
      const config = enabledConfigs.length > 0 ? { validator_configs: enabledConfigs } : undefined

      const result = await createSchedule({
        name: formName,
        source_id: formSourceId,
        cron_expression: formCron,
        notify_on_failure: formNotify,
        config,
      })

      setSchedules((prev) => [result.data, ...prev])
      setDialogOpen(false)
      resetForm()

      toast({
        title: str(schedules_t.scheduleCreated),
        description: `${result.data.name} created successfully`,
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: str(schedules_t.createFailed),
        description: err instanceof Error ? err.message : str(errors.generic),
      })
    } finally {
      setCreating(false)
    }
  }

  const resetForm = () => {
    setFormName('')
    setFormSourceId('')
    setFormCron('0 0 * * *')
    setFormNotify(true)
    setValidatorConfigs([])
    setSelectedSourceSchema(null)
    setDialogTab('basic')
  }

  const handleDialogOpen = (open: boolean) => {
    setDialogOpen(open)
    if (open) {
      loadValidators()
    } else {
      resetForm()
    }
  }

  const handleSourceChange = (sourceId: string) => {
    setFormSourceId(sourceId)
    loadSourceSchema(sourceId)
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteSchedule(id)
      setSchedules((prev) => prev.filter((s) => s.id !== id))
      toast({ title: str(schedules_t.deleted) })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: str(schedules_t.deleteFailed),
        description: err instanceof Error ? err.message : str(errors.generic),
      })
    }
  }

  const handlePause = async (id: string) => {
    try {
      const result = await pauseSchedule(id)
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? result.schedule : s))
      )
      toast({ title: str(schedules_t.schedulePaused) })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: str(schedules_t.pauseFailed),
        description: err instanceof Error ? err.message : str(errors.generic),
      })
    }
  }

  const handleResume = async (id: string) => {
    try {
      const result = await resumeSchedule(id)
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? result.schedule : s))
      )
      toast({ title: str(schedules_t.scheduleResumed) })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: str(schedules_t.resumeFailed),
        description: err instanceof Error ? err.message : str(errors.generic),
      })
    }
  }

  const handleRunNow = async (id: string) => {
    try {
      const result = await runScheduleNow(id)
      toast({
        title: str(schedules_t.validationTriggered),
        description: str(result.passed ? validation.passed : validation.failed),
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: str(schedules_t.runFailed),
        description: err instanceof Error ? err.message : str(errors.generic),
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
          <h1 className="text-2xl font-bold">{nav.schedules}</h1>
          <p className="text-muted-foreground">{schedules_t.subtitle}</p>
        </div>

        <Dialog open={dialogOpen} onOpenChange={handleDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {schedules_t.newSchedule}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle>{schedules_t.createSchedule}</DialogTitle>
              <DialogDescription>
                {schedules_t.createScheduleDesc}
              </DialogDescription>
            </DialogHeader>

            <Tabs value={dialogTab} onValueChange={setDialogTab} className="flex-1 overflow-hidden flex flex-col">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="basic">
                  <Clock className="h-4 w-4 mr-2" />
                  Basic Settings
                </TabsTrigger>
                <TabsTrigger value="validators" disabled={!formSourceId}>
                  <Sliders className="h-4 w-4 mr-2" />
                  Validators
                  {validatorConfigs.filter((c) => c.enabled).length > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {validatorConfigs.filter((c) => c.enabled).length}
                    </Badge>
                  )}
                </TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4 py-4 overflow-y-auto flex-1">
                <div className="space-y-2">
                  <Label>{common.name}</Label>
                  <Input
                    placeholder={str(schedules_t.cronPresets.dailyMidnight)}
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>{common.source}</Label>
                  <Select value={formSourceId} onValueChange={handleSourceChange}>
                    <SelectTrigger>
                      <SelectValue placeholder={str(schedules_t.selectSource)} />
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
                  <Label>{common.schedule}</Label>
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
                    placeholder={str(schedules_t.customCron)}
                    value={formCron}
                    onChange={(e) => setFormCron(e.target.value)}
                    className="mt-2"
                  />
                  <p className="text-xs text-muted-foreground">
                    {schedules_t.cronFormat}
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="notify"
                    checked={formNotify}
                    onCheckedChange={setFormNotify}
                  />
                  <Label htmlFor="notify">{schedules_t.notifyOnFailure}</Label>
                </div>

                {formSourceId && (
                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground">
                      Select a source first, then configure validators in the "Validators" tab.
                      If no validators are configured, all validators will run by default.
                    </p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="validators" className="py-4 overflow-y-auto flex-1">
                {loadingValidators ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                  </div>
                ) : (
                  <ValidatorSelector
                    validators={validators}
                    configs={validatorConfigs}
                    onChange={setValidatorConfigs}
                    columns={selectedSourceSchema?.columns || []}
                  />
                )}
              </TabsContent>
            </Tabs>

            <DialogFooter className="pt-4 border-t">
              <Button variant="outline" onClick={() => handleDialogOpen(false)}>
                {common.cancel}
              </Button>
              <Button onClick={handleCreate} disabled={creating}>
                {creating ? schedules_t.creating : common.create}
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
            <h3 className="text-lg font-medium mb-2">{schedules_t.noSchedulesYet}</h3>
            <p className="text-muted-foreground text-center mb-4">
              {schedules_t.noSchedulesDesc}
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              {schedules_t.newSchedule}
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
                        {common.source}: {getSourceName(s.source_id)}
                      </CardDescription>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={s.is_active ? 'default' : 'secondary'}>
                      {s.is_active ? schedules_t.active : schedules_t.paused}
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
                          {schedules_t.runNow}
                        </DropdownMenuItem>
                        {s.is_active ? (
                          <DropdownMenuItem onClick={() => handlePause(s.id)}>
                            <Pause className="h-4 w-4 mr-2" />
                            {schedules_t.pause}
                          </DropdownMenuItem>
                        ) : (
                          <DropdownMenuItem onClick={() => handleResume(s.id)}>
                            <Play className="h-4 w-4 mr-2" />
                            {schedules_t.resume}
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => handleDelete(s.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          {common.delete}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">{schedules_t.cronExpression}</div>
                    <div className="font-mono">{s.cron_expression}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">{schedules_t.lastRun}</div>
                    <div>{s.last_run_at ? formatDate(s.last_run_at) : common.never}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">{schedules_t.nextRun}</div>
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
