/**
 * Drift monitor form component.
 *
 * Form for creating and editing drift monitors.
 */

import { useCallback, useEffect, useState, useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Eye, ArrowLeft, CheckCircle2, AlertTriangle, Info } from 'lucide-react'
import { getSourceSchema, learnSchema, type Schema } from '@/api/modules/schemas'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DriftPreviewResults } from './DriftPreviewResults'
import type { DriftPreviewData } from './types'
import type { Source } from '@/api/modules/sources'

const API_BASE = '/api/v1'

async function previewDrift(data: {
  baseline_source_id: string
  current_source_id: string
  method: string
  threshold: number
}): Promise<DriftPreviewData> {
  const response = await fetch(`${API_BASE}/drift/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Preview failed' }))
    throw new Error(error.detail || 'Preview failed')
  }
  // API returns preview data directly, not wrapped in { data: ... }
  return response.json()
}

interface DriftMonitorFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: DriftMonitorFormData) => Promise<void>
  sources: Source[]
  initialData?: Partial<DriftMonitorFormData>
  isEditing?: boolean
}

const SCHEDULE_PRESETS = [
  { label: 'Every Hour', value: '0 * * * *' },
  { label: 'Every 6 Hours', value: '0 */6 * * *' },
  { label: 'Daily (midnight)', value: '0 0 * * *' },
  { label: 'Weekly (Sunday)', value: '0 0 * * 0' },
]

import { DriftMethodSelector } from './DriftMethodSelector'
import type { DriftMethod } from '@/api/modules/drift'

export interface DriftMonitorFormData {
  name: string
  baseline_source_id: string
  current_source_id: string
  cron_expression: string
  method: string
  threshold: number
  alert_on_drift: boolean
  alert_threshold_critical: number
  alert_threshold_high: number
}

type FormStep = 'configure' | 'preview'

export function DriftMonitorForm({
  open,
  onOpenChange,
  onSubmit,
  sources,
  initialData,
  isEditing = false,
}: DriftMonitorFormProps) {
  const t = useIntlayer('driftMonitor')
  const common = useIntlayer('common')

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [activeTab, setActiveTab] = useState('basic')
  const [formData, setFormData] = useState<DriftMonitorFormData>({
    name: '',
    baseline_source_id: '',
    current_source_id: '',
    cron_expression: '0 0 * * *',
    method: 'auto',
    threshold: 0.05,
    alert_on_drift: true,
    alert_threshold_critical: 0.3,
    alert_threshold_high: 0.2,
  })

  // Preview step state
  const [step, setStep] = useState<FormStep>('configure')
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [previewResult, setPreviewResult] = useState<DriftPreviewData | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)

  // Schema compatibility check state
  const [baselineSchema, setBaselineSchema] = useState<Schema | null>(null)
  const [currentSchema, setCurrentSchema] = useState<Schema | null>(null)
  const [isLoadingSchema, setIsLoadingSchema] = useState(false)

  useEffect(() => {
    if (initialData) {
      setFormData((prev) => ({ ...prev, ...initialData }))
    }
  }, [initialData])

  // Fetch schema when baseline source changes
  useEffect(() => {
    if (!formData.baseline_source_id) {
      setBaselineSchema(null)
      return
    }

    const fetchSchema = async () => {
      setIsLoadingSchema(true)
      try {
        let schema = await getSourceSchema(formData.baseline_source_id)
        if (!schema) {
          // Learn schema if not exists
          schema = await learnSchema(formData.baseline_source_id)
        }
        setBaselineSchema(schema)
      } catch {
        setBaselineSchema(null)
      } finally {
        setIsLoadingSchema(false)
      }
    }
    fetchSchema()
  }, [formData.baseline_source_id])

  // Fetch schema when current source changes
  useEffect(() => {
    if (!formData.current_source_id) {
      setCurrentSchema(null)
      return
    }

    const fetchSchema = async () => {
      setIsLoadingSchema(true)
      try {
        let schema = await getSourceSchema(formData.current_source_id)
        if (!schema) {
          // Learn schema if not exists
          schema = await learnSchema(formData.current_source_id)
        }
        setCurrentSchema(schema)
      } catch {
        setCurrentSchema(null)
      } finally {
        setIsLoadingSchema(false)
      }
    }
    fetchSchema()
  }, [formData.current_source_id])

  // Schema compatibility check
  const schemaCompatibility = useMemo(() => {
    if (!baselineSchema || !currentSchema) {
      return null
    }

    const baselineColumns = new Set(baselineSchema.columns || [])
    const currentColumns = new Set(currentSchema.columns || [])

    const matchingColumns = [...baselineColumns].filter(col => currentColumns.has(col))
    const onlyInBaseline = [...baselineColumns].filter(col => !currentColumns.has(col))
    const onlyInCurrent = [...currentColumns].filter(col => !baselineColumns.has(col))

    const totalUniqueColumns = new Set([...baselineColumns, ...currentColumns]).size
    const matchPercentage = totalUniqueColumns > 0
      ? Math.round((matchingColumns.length / totalUniqueColumns) * 100)
      : 0

    return {
      matchingColumns,
      onlyInBaseline,
      onlyInCurrent,
      matchPercentage,
      isCompatible: matchingColumns.length > 0,
      isFullMatch: onlyInBaseline.length === 0 && onlyInCurrent.length === 0,
    }
  }, [baselineSchema, currentSchema])

  // Reset step when dialog closes
  useEffect(() => {
    if (!open) {
      setStep('configure')
      setPreviewResult(null)
      setPreviewError(null)
    }
  }, [open])

  const handleRunPreview = useCallback(async () => {
    setIsPreviewing(true)
    setPreviewError(null)
    setPreviewResult(null)

    try {
      const result = await previewDrift({
        baseline_source_id: formData.baseline_source_id,
        current_source_id: formData.current_source_id,
        method: formData.method,
        threshold: formData.threshold,
      })
      setPreviewResult(result)
      setStep('preview')
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : 'Preview failed')
    } finally {
      setIsPreviewing(false)
    }
  }, [formData])

  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true)
    try {
      await onSubmit(formData)
      onOpenChange(false)
    } finally {
      setIsSubmitting(false)
    }
  }, [formData, onSubmit, onOpenChange])

  const handleBack = useCallback(() => {
    setStep('configure')
    setPreviewResult(null)
  }, [])

  const isValid =
    formData.name.trim() !== '' &&
    formData.baseline_source_id !== '' &&
    formData.current_source_id !== '' &&
    formData.baseline_source_id !== formData.current_source_id

  const canPreview =
    formData.baseline_source_id !== '' &&
    formData.current_source_id !== '' &&
    formData.baseline_source_id !== formData.current_source_id

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={step === 'preview' ? 'max-w-4xl max-h-[90vh] overflow-y-auto' : 'max-w-lg'}>
        <DialogHeader>
          <DialogTitle>
            {step === 'preview'
              ? (t.preview?.previewResults ?? 'Preview Results')
              : (isEditing ? t.monitor.editMonitor : t.monitor.createMonitor)}
          </DialogTitle>
          <DialogDescription>
            {step === 'preview'
              ? (t.preview?.reviewBeforeCreate ?? 'Review drift results before creating the monitor')
              : 'Configure automatic drift detection between data sources'}
          </DialogDescription>
        </DialogHeader>

        {/* Preview Results Step */}
        {step === 'preview' && previewResult && (
          <>
            <DriftPreviewResults data={previewResult} />
            <DialogFooter>
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                {t.preview?.backToConfig ?? 'Back to Configuration'}
              </Button>
              <Button onClick={handleSubmit} disabled={!isValid || isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <CheckCircle2 className="mr-2 h-4 w-4" />
                {isEditing ? common.save : common.create}
              </Button>
            </DialogFooter>
          </>
        )}

        {/* Configuration Step */}
        {step === 'configure' && (
          <>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="py-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="basic">{t.tabs?.basic ?? 'Basic'}</TabsTrigger>
            <TabsTrigger value="alerts">{t.tabs?.alerts ?? 'Alerts'}</TabsTrigger>
          </TabsList>

          {/* Basic Configuration Tab */}
          <TabsContent value="basic" className="space-y-4 mt-4">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">{t.monitor.name}</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="Daily Sales Drift Check"
              />
            </div>

            {/* Baseline Source */}
            <div className="space-y-2">
              <Label>{t.monitor.baselineSource}</Label>
              <Select
                value={formData.baseline_source_id}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, baseline_source_id: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select baseline source" />
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

            {/* Current Source */}
            <div className="space-y-2">
              <Label>{t.monitor.currentSource}</Label>
              <Select
                value={formData.current_source_id}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, current_source_id: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select current source" />
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

            {/* Schema Compatibility Warning */}
            {isLoadingSchema && formData.baseline_source_id && formData.current_source_id && (
              <Alert>
                <Loader2 className="h-4 w-4 animate-spin" />
                <AlertDescription>Checking schema compatibility...</AlertDescription>
              </Alert>
            )}

            {!isLoadingSchema && schemaCompatibility && !schemaCompatibility.isCompatible && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Schema mismatch:</strong> No matching columns between sources.
                  <br />
                  <span className="text-xs">
                    Baseline: {baselineSchema?.columns?.join(', ') || 'N/A'}
                    <br />
                    Current: {currentSchema?.columns?.join(', ') || 'N/A'}
                  </span>
                </AlertDescription>
              </Alert>
            )}

            {!isLoadingSchema && schemaCompatibility && schemaCompatibility.isCompatible && !schemaCompatibility.isFullMatch && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Partial schema match ({schemaCompatibility.matchPercentage}%)</strong>
                  <br />
                  <span className="text-xs text-muted-foreground">
                    {schemaCompatibility.matchingColumns.length} matching columns: {schemaCompatibility.matchingColumns.join(', ')}
                    {schemaCompatibility.onlyInBaseline.length > 0 && (
                      <>
                        <br />
                        Only in baseline: {schemaCompatibility.onlyInBaseline.join(', ')}
                      </>
                    )}
                    {schemaCompatibility.onlyInCurrent.length > 0 && (
                      <>
                        <br />
                        Only in current: {schemaCompatibility.onlyInCurrent.join(', ')}
                      </>
                    )}
                  </span>
                </AlertDescription>
              </Alert>
            )}

            {!isLoadingSchema && schemaCompatibility?.isFullMatch && (
              <Alert className="border-green-500/50 bg-green-500/10">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <AlertDescription className="text-green-600 dark:text-green-400">
                  Schemas fully match ({schemaCompatibility.matchingColumns.length} columns)
                </AlertDescription>
              </Alert>
            )}

            {/* Schedule */}
            <div className="space-y-2">
              <Label>{t.monitor.schedule}</Label>
              <Select
                value={formData.cron_expression}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, cron_expression: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SCHEDULE_PRESETS.map((preset) => (
                    <SelectItem key={preset.value} value={preset.value}>
                      {preset.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Method - Using reusable DriftMethodSelector */}
            <div className="space-y-2">
              <Label>{t.monitor.method}</Label>
              <DriftMethodSelector
                value={formData.method as DriftMethod}
                onChange={(method) => setFormData((prev) => ({ ...prev, method }))}
                variant="compact"
                showThresholdHints
              />
            </div>

            {/* Threshold */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{t.monitor.threshold}</Label>
                <span className="text-sm text-muted-foreground">
                  {(formData.threshold * 100).toFixed(0)}%
                </span>
              </div>
              <Slider
                value={[formData.threshold]}
                onValueChange={([value]) => setFormData((prev) => ({ ...prev, threshold: value }))}
                min={0.01}
                max={0.5}
                step={0.01}
              />
            </div>
          </TabsContent>

          {/* Alerts Configuration Tab */}
          <TabsContent value="alerts" className="space-y-4 mt-4">
            {/* Alert on Drift */}
            <div className="flex items-center justify-between">
              <Label htmlFor="alert-on-drift">{t.monitor.alertOnDrift}</Label>
              <Switch
                id="alert-on-drift"
                checked={formData.alert_on_drift}
                onCheckedChange={(checked) =>
                  setFormData((prev) => ({ ...prev, alert_on_drift: checked }))
                }
              />
            </div>

            {/* Alert Thresholds */}
            {formData.alert_on_drift && (
              <div className="space-y-4 rounded-lg border p-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-red-500">{t.monitor.criticalThreshold}</Label>
                    <span className="text-sm text-muted-foreground">
                      {(formData.alert_threshold_critical * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    value={[formData.alert_threshold_critical]}
                    onValueChange={([value]) =>
                      setFormData((prev) => ({ ...prev, alert_threshold_critical: value }))
                    }
                    min={0.1}
                    max={1}
                    step={0.05}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-orange-500">{t.monitor.highThreshold}</Label>
                    <span className="text-sm text-muted-foreground">
                      {(formData.alert_threshold_high * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    value={[formData.alert_threshold_high]}
                    onValueChange={([value]) =>
                      setFormData((prev) => ({ ...prev, alert_threshold_high: value }))
                    }
                    min={0.05}
                    max={0.5}
                    step={0.05}
                  />
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

          {/* Preview Error */}
          {previewError && (
            <div className="rounded-lg border border-destructive bg-destructive/10 p-3">
              <p className="text-sm text-destructive flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                {previewError}
              </p>
            </div>
          )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {common.cancel}
          </Button>
          {!isEditing && (
            <Button
              variant="secondary"
              onClick={handleRunPreview}
              disabled={!canPreview || isPreviewing}
            >
              {isPreviewing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Eye className="mr-2 h-4 w-4" />
              {t.preview?.runPreview ?? 'Preview'}
            </Button>
          )}
          <Button onClick={handleSubmit} disabled={!isValid || isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEditing ? common.save : common.create}
          </Button>
        </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
