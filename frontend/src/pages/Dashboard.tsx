import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { listSources, type Source } from '@/api/client'
import { formatDate, getStatusColor } from '@/lib/utils'

export default function Dashboard() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    loadSources()
  }, [])

  async function loadSources() {
    try {
      setLoading(true)
      const response = await listSources({ limit: 10 })
      setSources(response.data)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  // Calculate stats
  const totalSources = sources.length
  const passedSources = sources.filter(
    (s) => s.latest_validation_status === 'success'
  ).length
  const failedSources = sources.filter(
    (s) => s.latest_validation_status === 'failed'
  ).length
  const pendingSources = sources.filter(
    (s) => !s.latest_validation_status || s.latest_validation_status === 'pending'
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
        <p className="text-muted-foreground">Failed to load dashboard data</p>
        <Button onClick={loadSources}>Retry</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Data quality overview and monitoring
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sources</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalSources}</div>
            <p className="text-xs text-muted-foreground">
              Configured data sources
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Passed</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {passedSources}
            </div>
            <p className="text-xs text-muted-foreground">
              Validation passed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {failedSources}
            </div>
            <p className="text-xs text-muted-foreground">
              Validation failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {pendingSources}
            </div>
            <p className="text-xs text-muted-foreground">
              Not yet validated
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Sources */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Recent Sources</CardTitle>
            <p className="text-sm text-muted-foreground">
              Your configured data sources
            </p>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link to="/sources">
              View All
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {sources.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Database className="h-12 w-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground mb-4">
                No data sources configured yet
              </p>
              <Button asChild>
                <Link to="/sources">Add Your First Source</Link>
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
                        {source.type} • Last validated:{' '}
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
                            : source.latest_validation_status === 'failed'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {source.latest_validation_status}
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
    </div>
  )
}
