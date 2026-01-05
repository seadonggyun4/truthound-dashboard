import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Database,
  Plus,
  MoreVertical,
  Trash2,
  Play,
  FileText,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadSources()
  }, [])

  async function loadSources() {
    try {
      setLoading(true)
      const response = await listSources()
      setSources(response.data)
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to load sources',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this source?')) return

    try {
      await deleteSource(id)
      setSources((prev) => prev.filter((s) => s.id !== id))
      toast({
        title: 'Success',
        description: 'Source deleted successfully',
      })
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to delete source',
        variant: 'destructive',
      })
    }
  }

  async function handleValidate(id: string) {
    try {
      toast({
        title: 'Validation Started',
        description: 'Running validation...',
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
        title: result.passed ? 'Validation Passed' : 'Validation Failed',
        description: `Found ${result.total_issues} issues`,
        variant: result.passed ? 'default' : 'destructive',
      })
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to run validation',
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
          <h1 className="text-3xl font-bold">Data Sources</h1>
          <p className="text-muted-foreground">
            Manage your data sources and validations
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Source
        </Button>
      </div>

      {/* Sources List */}
      {sources.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Database className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No sources yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Add your first data source to start monitoring data quality
            </p>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Your First Source
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
                          Last validated: {formatDate(source.last_validated_at)}
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

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleValidate(source.id)}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      Validate
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
    </div>
  )
}
