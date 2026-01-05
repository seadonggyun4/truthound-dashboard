import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
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
import { Label } from '@/components/ui/label'
import {
  listSources,
  listDriftComparisons,
  compareDrift,
  type Source,
  type DriftComparison,
} from '@/api/client'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { GitCompare, Plus, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react'

export default function Drift() {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [sources, setSources] = useState<Source[]>([])
  const [comparisons, setComparisons] = useState<DriftComparison[]>([])
  const [loading, setLoading] = useState(true)
  const [comparing, setComparing] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  // New comparison form
  const [baselineId, setBaselineId] = useState('')
  const [currentId, setCurrentId] = useState('')
  const [method, setMethod] = useState<'auto' | 'ks' | 'psi' | 'chi2' | 'js'>('auto')

  useEffect(() => {
    async function fetchData() {
      try {
        const [sourcesRes, comparisonsRes] = await Promise.all([
          listSources(),
          listDriftComparisons({ limit: 20 }),
        ])
        setSources(sourcesRes.data)
        setComparisons(comparisonsRes.data)
      } catch (err) {
        toast({
          variant: 'destructive',
          title: t('common.error'),
          description: err instanceof Error ? err.message : t('errors.loadFailed'),
        })
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [toast, t])

  const handleCompare = async () => {
    if (!baselineId || !currentId) {
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: t('drift.selectBothSources'),
      })
      return
    }

    if (baselineId === currentId) {
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: t('drift.mustBeDifferent'),
      })
      return
    }

    try {
      setComparing(true)
      const result = await compareDrift({
        baseline_source_id: baselineId,
        current_source_id: currentId,
        method,
      })

      setComparisons((prev) => [result.data, ...prev])
      setDialogOpen(false)
      setBaselineId('')
      setCurrentId('')

      toast({
        title: t('drift.comparisonComplete'),
        description: result.data.has_drift
          ? t('drift.driftDetectedColumns', { count: result.data.drifted_columns })
          : t('drift.noDriftDetected'),
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: t('drift.comparisonFailed'),
        description: err instanceof Error ? err.message : t('errors.generic'),
      })
    } finally {
      setComparing(false)
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
          <h1 className="text-2xl font-bold">{t('drift.title')}</h1>
          <p className="text-muted-foreground">{t('drift.subtitle')}</p>
        </div>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {t('drift.newComparison')}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('drift.compareDatasets')}</DialogTitle>
              <DialogDescription>
                {t('drift.compareDescription')}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{t('drift.baselineSource')}</Label>
                <Select value={baselineId} onValueChange={setBaselineId}>
                  <SelectTrigger>
                    <SelectValue placeholder={t('drift.selectBaseline')} />
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
                <Label>{t('drift.currentSource')}</Label>
                <Select value={currentId} onValueChange={setCurrentId}>
                  <SelectTrigger>
                    <SelectValue placeholder={t('drift.selectCurrent')} />
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
                <Label>{t('drift.detectionMethod')}</Label>
                <Select value={method} onValueChange={(v) => setMethod(v as typeof method)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">{t('drift.methods.auto')}</SelectItem>
                    <SelectItem value="ks">{t('drift.methods.ks')}</SelectItem>
                    <SelectItem value="psi">{t('drift.methods.psi')}</SelectItem>
                    <SelectItem value="chi2">{t('drift.methods.chi2')}</SelectItem>
                    <SelectItem value="js">{t('drift.methods.js')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleCompare} disabled={comparing}>
                {comparing ? t('drift.comparing') : t('drift.compare')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Comparisons List */}
      {comparisons.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <GitCompare className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">{t('drift.noComparisonsYet')}</h3>
            <p className="text-muted-foreground text-center mb-4">
              {t('drift.noComparisonsDesc')}
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              {t('drift.newComparison')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {comparisons.map((c) => (
            <Card key={c.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {c.has_drift ? (
                      <AlertTriangle className="h-5 w-5 text-amber-500" />
                    ) : (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                    <div>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        {getSourceName(c.baseline_source_id)}
                        <ArrowRight className="h-4 w-4" />
                        {getSourceName(c.current_source_id)}
                      </CardTitle>
                      <CardDescription>{formatDate(c.created_at)}</CardDescription>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {c.has_high_drift && (
                      <Badge variant="destructive">{t('drift.highDrift')}</Badge>
                    )}
                    {c.has_drift && !c.has_high_drift && (
                      <Badge variant="warning" className="bg-amber-500 text-white">
                        {t('drift.driftDetected')}
                      </Badge>
                    )}
                    {!c.has_drift && <Badge variant="outline">{t('drift.noDrift')}</Badge>}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">{t('drift.columnsCompared')}</div>
                    <div className="text-xl font-semibold">{c.total_columns || 0}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">{t('drift.driftedColumns')}</div>
                    <div className="text-xl font-semibold text-amber-600">
                      {c.drifted_columns || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">{t('drift.driftPercentage')}</div>
                    <div className="text-xl font-semibold">
                      {c.drift_percentage?.toFixed(1) || 0}%
                    </div>
                  </div>
                </div>

                {c.result?.columns && c.result.columns.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="text-sm font-medium mb-2">{t('drift.columnDetails')}</div>
                    <div className="space-y-2">
                      {c.result.columns
                        .filter((col) => col.drifted)
                        .slice(0, 5)
                        .map((col) => (
                          <div
                            key={col.column}
                            className="flex items-center justify-between p-2 bg-muted/50 rounded"
                          >
                            <div>
                              <span className="font-mono text-sm">{col.column}</span>
                              <span className="text-xs text-muted-foreground ml-2">
                                ({col.dtype})
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{col.method}</Badge>
                              <Badge
                                variant={col.level === 'high' ? 'destructive' : 'secondary'}
                              >
                                {col.level}
                              </Badge>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
