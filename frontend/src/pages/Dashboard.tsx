import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { useThrottledFetch } from '@/hooks/useThrottledFetch'
import {
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  BellRing,
  FileText,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { listSources, type SourceListResponse } from '@/api/modules/sources'
import { getOverview, type OverviewResponse } from '@/api/modules/control-plane'
import { formatDate } from '@/lib/utils'
import { AnimatedNumber } from '@/components/AnimatedNumber'
import { GlassCard } from '@/components/GlassCard'

export default function Dashboard() {
  const nav = useSafeIntlayer('nav')
  const dashboard = useSafeIntlayer('dashboard')
  const common = useSafeIntlayer('common')
  const validation = useSafeIntlayer('validation')

  // Throttled fetch with 500ms throttle and 30s cache
  const {
    data: sourcesResponse,
    isLoading: loading,
    error,
    refetch: loadSources,
  } = useThrottledFetch<SourceListResponse>(
    'dashboard-sources',
    () => listSources({ limit: 10 }),
    { throttleMs: 500, cacheTtlMs: 30000 }
  )

  const { data: overviewResponse } = useThrottledFetch<OverviewResponse>(
    'dashboard-overview',
    getOverview,
    { throttleMs: 500, cacheTtlMs: 30000 }
  )

  const sources = sourcesResponse?.data ?? []
  const activeIncidents = overviewResponse?.incidents.active ?? 0
  const totalArtifacts = overviewResponse?.artifacts.total ?? 0
  const quickViews = overviewResponse?.saved_views ?? []
  const incidentBacklog = overviewResponse?.incident_backlog ?? []
  const assigneeWorkload = overviewResponse?.assignee_workload ?? []
  const artifactTypes = overviewResponse?.artifact_types ?? []
  const sourcesByOwner = overviewResponse?.sources_by_owner ?? []
  const sourcesByTeam = overviewResponse?.sources_by_team ?? []
  const sourcesByDomain = overviewResponse?.sources_by_domain ?? []
  const ownershipFreshness = overviewResponse?.artifact_freshness_by_ownership ?? []

  // Create a helper to get validation status labels
  const getValidationLabel = useMemo(() => {
    return (status: string | null | undefined) => {
      if (!status) return null
      switch (status) {
        case 'passed': return validation.passed
        case 'success': return validation.success
        case 'failed': return validation.failed
        case 'error': return validation.error
        case 'pending': return validation.pending
        case 'warning': return validation.warning
        default: return status
      }
    }
  }, [validation])

  // Calculate stats
  // Backend validation status values: 'success' | 'failed' | 'error' | 'pending' | 'running' | null
  const totalSources = sources.length
  const passedSources = sources.filter(
    (s) => s.latest_validation_status === 'success'
  ).length
  const failedSources = sources.filter(
    (s) => s.latest_validation_status === 'failed' || s.latest_validation_status === 'error'
  ).length
  const pendingSources = sources.filter(
    (s) => !s.latest_validation_status || s.latest_validation_status === 'pending' || s.latest_validation_status === 'running'
  ).length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <XCircle className="h-12 w-12 text-destructive" />
        <p className="text-muted-foreground">{dashboard.loadError}</p>
        <Button onClick={() => loadSources(true)}>{common.retry}</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{nav.dashboard}</h1>
        <p className="text-muted-foreground">
          {dashboard.subtitle}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <GlassCard
          className="bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border-primary/20"
          glowColor="#fd9e4b"
        >
          <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-primary/10 blur-2xl" />
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-xl bg-primary/20 flex items-center justify-center">
                <Database className="h-7 w-7 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">{dashboard.totalSources}</p>
                <p className="text-3xl font-bold">
                  <AnimatedNumber value={totalSources} duration={1200} />
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {dashboard.configuredSources}
                </p>
              </div>
            </div>
          </CardContent>
        </GlassCard>

        <GlassCard
          className="bg-gradient-to-br from-green-500/10 via-green-500/5 to-transparent border-green-500/20"
          glowColor="#22c55e"
        >
          <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-green-500/10 blur-2xl" />
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-xl bg-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-7 w-7 text-green-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">{dashboard.passed}</p>
                <p className="text-3xl font-bold text-green-500">
                  <AnimatedNumber value={passedSources} duration={1200} />
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {dashboard.validationPassed}
                </p>
              </div>
            </div>
          </CardContent>
        </GlassCard>

        <GlassCard
          className="bg-gradient-to-br from-red-500/10 via-red-500/5 to-transparent border-red-500/20"
          glowColor="#ef4444"
        >
          <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-red-500/10 blur-2xl" />
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-xl bg-red-500/20 flex items-center justify-center">
                <XCircle className="h-7 w-7 text-red-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">{dashboard.failed}</p>
                <p className="text-3xl font-bold text-red-500">
                  <AnimatedNumber value={failedSources} duration={1200} />
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {dashboard.validationFailed}
                </p>
              </div>
            </div>
          </CardContent>
        </GlassCard>

        <GlassCard
          className="bg-gradient-to-br from-yellow-500/10 via-yellow-500/5 to-transparent border-yellow-500/20"
          glowColor="#eab308"
        >
          <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-yellow-500/10 blur-2xl" />
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-xl bg-yellow-500/20 flex items-center justify-center">
                <AlertTriangle className="h-7 w-7 text-yellow-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">{dashboard.pending}</p>
                <p className="text-3xl font-bold text-yellow-500">
                  <AnimatedNumber value={pendingSources} duration={1200} />
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {dashboard.notValidated}
                </p>
              </div>
            </div>
          </CardContent>
        </GlassCard>

        <GlassCard
          className="bg-gradient-to-br from-orange-500/10 via-orange-500/5 to-transparent border-orange-500/20"
          glowColor="#f97316"
        >
          <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-orange-500/10 blur-2xl" />
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-xl bg-orange-500/20 flex items-center justify-center">
                <BellRing className="h-7 w-7 text-orange-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Incidents</p>
                <p className="text-3xl font-bold text-orange-500">
                  <AnimatedNumber value={activeIncidents} duration={1200} />
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Escalations awaiting action
                </p>
              </div>
            </div>
          </CardContent>
        </GlassCard>

        <GlassCard
          className="bg-gradient-to-br from-sky-500/10 via-sky-500/5 to-transparent border-sky-500/20"
          glowColor="#0ea5e9"
        >
          <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-sky-500/10 blur-2xl" />
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-xl bg-sky-500/20 flex items-center justify-center">
                <FileText className="h-7 w-7 text-sky-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Artifacts</p>
                <p className="text-3xl font-bold text-sky-500">
                  <AnimatedNumber value={totalArtifacts} duration={1200} />
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Reports and Data Docs history
                </p>
              </div>
            </div>
          </CardContent>
        </GlassCard>
      </div>

      {/* Recent Sources */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{dashboard.recentSources}</CardTitle>
            <p className="text-sm text-muted-foreground">
              {dashboard.recentSourcesDesc}
            </p>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link to="/sources">
              {dashboard.viewAll}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {sources.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Database className="h-12 w-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground mb-4">
                {dashboard.noSources}
              </p>
              <Button asChild>
                <Link to="/sources">{dashboard.addFirstSource}</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {sources.slice(0, 5).map((source) => (
                <Link
                  key={source.id}
                  to={`/sources/${source.id}`}
                  className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Database className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{source.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {source.type} • {dashboard.lastValidated}:{' '}
                        {formatDate(source.last_validated_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {source.latest_validation_status && (
                      <Badge
                        variant={
                          source.latest_validation_status === 'success'
                            ? 'success'
                            : source.latest_validation_status === 'failed' || source.latest_validation_status === 'error'
                            ? 'destructive'
                            : source.latest_validation_status === 'pending' || source.latest_validation_status === 'running'
                            ? 'warning'
                            : 'secondary'
                        }
                      >
                        {getValidationLabel(source.latest_validation_status)}
                      </Badge>
                    )}
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quick Views</CardTitle>
          <p className="text-sm text-muted-foreground">
            Saved operational filters from Sources and Reports.
          </p>
        </CardHeader>
        <CardContent>
          {quickViews.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Save a filtered view to pin it on the dashboard.
            </p>
          ) : (
            <div className="space-y-3">
              {quickViews.map((view) => {
                const href =
                  view.scope === 'artifacts'
                    ? '/reports'
                    : view.scope === 'alerts'
                      ? '/alerts'
                    : view.scope === 'history'
                      ? '/sources'
                      : '/sources'
                return (
                  <Link
                    key={view.id}
                    to={href}
                    className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent transition-colors"
                  >
                    <div>
                      <p className="font-medium">{view.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {view.scope}
                        {view.owner_name ? ` • ${view.owner_name}` : ''}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Queue Backlog</CardTitle>
            <p className="text-sm text-muted-foreground">
              Active queue load and current assignee workload.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {incidentBacklog.length === 0 ? (
              <p className="text-sm text-muted-foreground">No active incident queues.</p>
            ) : (
              <div className="space-y-3">
                {incidentBacklog.map((item) => (
                  <div key={item.queue_id} className="flex items-center justify-between rounded-lg border p-3">
                    <span className="font-medium">{item.queue_name}</span>
                    <Badge variant="outline">{item.count}</Badge>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-3">Assignee Workload</p>
              {assigneeWorkload.length === 0 ? (
                <p className="text-sm text-muted-foreground">No assignees are carrying active incidents.</p>
              ) : (
                <div className="space-y-3">
                  {assigneeWorkload.map((item) => (
                    <div key={item.user_id ?? item.user_name} className="flex items-center justify-between rounded-lg border p-3">
                      <span className="font-medium">{item.user_name}</span>
                      <Badge variant="secondary">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Artifact Freshness</CardTitle>
            <p className="text-sm text-muted-foreground">
              Type split plus freshness for reports and Data Docs.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border p-3">
                <p className="text-sm text-muted-foreground">Fresh 24h</p>
                <p className="text-2xl font-bold">{overviewResponse?.artifacts.fresh_24h ?? 0}</p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-sm text-muted-foreground">Stale 7d+</p>
                <p className="text-2xl font-bold">{overviewResponse?.artifacts.stale ?? 0}</p>
              </div>
            </div>

            {artifactTypes.length === 0 ? (
              <p className="text-sm text-muted-foreground">No artifacts generated yet.</p>
            ) : (
              <div className="space-y-3">
                {artifactTypes.map((item) => (
                  <div key={item.artifact_type} className="flex items-center justify-between rounded-lg border p-3">
                    <span className="font-medium">
                      {item.artifact_type === 'datadocs' ? 'Data Docs' : 'Report'}
                    </span>
                    <Badge variant="outline">{item.count}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Ownership Coverage</CardTitle>
            <p className="text-sm text-muted-foreground">
              Owner slices and sources still marked as unowned.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border p-3">
              <p className="text-sm text-muted-foreground">Unowned Sources</p>
              <p className="text-2xl font-bold">{overviewResponse?.sources.unowned ?? 0}</p>
            </div>
            {sourcesByOwner.length === 0 ? (
              <p className="text-sm text-muted-foreground">No ownership assignments yet.</p>
            ) : (
              <div className="space-y-3">
                {sourcesByOwner.slice(0, 5).map((item) => (
                  <div key={item.id ?? item.name} className="flex items-center justify-between rounded-lg border p-3">
                    <span className="font-medium">{item.name}</span>
                    <Badge variant="outline">{item.count}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Team And Domain Slices</CardTitle>
            <p className="text-sm text-muted-foreground">
              Fleet distribution by team and domain without changing the existing dashboard layout.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-3">By Team</p>
              {sourcesByTeam.length === 0 ? (
                <p className="text-sm text-muted-foreground">No teams assigned.</p>
              ) : (
                <div className="space-y-2">
                  {sourcesByTeam.slice(0, 4).map((item) => (
                    <div key={item.id ?? item.name} className="flex items-center justify-between rounded-lg border p-3">
                      <span className="font-medium">{item.name}</span>
                      <Badge variant="secondary">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-3">By Domain</p>
              {sourcesByDomain.length === 0 ? (
                <p className="text-sm text-muted-foreground">No domains assigned.</p>
              ) : (
                <div className="space-y-2">
                  {sourcesByDomain.slice(0, 4).map((item) => (
                    <div key={item.id ?? item.name} className="flex items-center justify-between rounded-lg border p-3">
                      <span className="font-medium">{item.name}</span>
                      <Badge variant="outline">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Artifact Freshness By Ownership</CardTitle>
            <p className="text-sm text-muted-foreground">
              Fresh and stale artifacts grouped by owner, team, or domain.
            </p>
          </CardHeader>
          <CardContent>
            {ownershipFreshness.length === 0 ? (
              <p className="text-sm text-muted-foreground">No ownership-linked artifacts yet.</p>
            ) : (
              <div className="space-y-3">
                {ownershipFreshness.slice(0, 6).map((item) => (
                  <div
                    key={`${item.ownership_type}:${item.ownership_id ?? item.ownership_name}`}
                    className="rounded-lg border p-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{item.ownership_name}</span>
                      <Badge variant="outline">{item.ownership_type}</Badge>
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Fresh 24h: {item.fresh_24h}</span>
                      <span>Stale: {item.stale}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
