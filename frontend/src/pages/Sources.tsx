import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Database,
  Plus,
  Trash2,
  Play,
  FileText,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  listSources,
  deleteSource,
  runValidation,
  type Source,
} from '@/api/client'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useConfirm } from '@/components/ConfirmDialog'

export default function Sources() {
  const { t } = useTranslation()
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()
  const { confirm, ConfirmDialog } = useConfirm()

  const loadSources = useCallback(async () => {
    try {
      setLoading(true)
      const response = await listSources()
      setSources(response.data)
    } catch {
      toast({
        title: t('common.error'),
        description: t('sources.loadError'),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [toast, t])

  useEffect(() => {
    loadSources()
  }, [loadSources])

  async function handleDelete(id: string) {
    const confirmed = await confirm({
      title: t('sources.deleteSource'),
      description: t('sources.confirmDelete'),
      confirmText: t('common.delete'),
      variant: 'destructive',
    })
    if (!confirmed) return

    try {
      await deleteSource(id)
      setSources((prev) => prev.filter((s) => s.id !== id))
      toast({
        title: t('common.success'),
        description: t('sources.deleteSuccess'),
      })
    } catch {
      toast({
        title: t('common.error'),
        description: t('sources.deleteFailed'),
        variant: 'destructive',
      })
    }
  }

  async function handleValidate(id: string) {
    try {
      toast({
        title: t('sources.validationStarted'),
        description: t('sources.runningValidation'),
      })
      const result = await runValidation(id, {})
      setSources((prev) =>
        prev.map((s) =>
          s.id === id
            ? { ...s, latest_validation_status: result.status }
            : s
        )
      )
      toast({
        title: result.passed ? t('sources.validationPassed') : t('sources.validationFailed'),
        description: t('sources.foundIssues', { count: result.total_issues }),
        variant: result.passed ? 'default' : 'destructive',
      })
    } catch {
      toast({
        title: t('common.error'),
        description: t('sources.validationError'),
        variant: 'destructive',
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('nav.sources')}</h1>
          <p className="text-muted-foreground">
            {t('sources.subtitle')}
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {t('sources.addSource')}
        </Button>
      </div>

      {/* Sources List */}
      {sources.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Database className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">{t('sources.noSourcesYet')}</h3>
            <p className="text-muted-foreground text-center mb-4">
              {t('sources.noSourcesDesc')}
            </p>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t('sources.addFirstSource')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {sources.map((source) => (
            <Card key={source.id}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Database className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <Link
                        to={`/sources/${source.id}`}
                        className="font-semibold hover:text-primary transition-colors"
                      >
                        {source.name}
                      </Link>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Badge variant="outline">{source.type}</Badge>
                        <span>•</span>
                        <span>
                          {t('sources.lastValidated')}: {formatDate(source.last_validated_at)}
                        </span>
                      </div>
                      {source.description && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {source.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {source.latest_validation_status && (
                      <Badge
                        variant={
                          source.latest_validation_status === 'success' || source.latest_validation_status === 'passed'
                            ? 'success'
                            : source.latest_validation_status === 'failed'
                            ? 'destructive'
                            : source.latest_validation_status === 'warning'
                            ? 'warning'
                            : 'secondary'
                        }
                      >
                        {t(`validation.${source.latest_validation_status}`)}
                      </Badge>
                    )}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleValidate(source.id)}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      {t('sources.validate')}
                    </Button>

                    <Button variant="ghost" size="icon" asChild>
                      <Link to={`/sources/${source.id}`}>
                        <FileText className="h-4 w-4" />
                      </Link>
                    </Button>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(source.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ConfirmDialog />
    </div>
  )
}
