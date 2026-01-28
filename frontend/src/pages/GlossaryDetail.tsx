import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import {
  BookOpen,
  ArrowLeft,
  Edit,
  History,
  MessageSquare,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useGlossaryStore } from '@/stores/glossaryStore'
import { getTermHistory, type TermHistory } from '@/api/modules/glossary'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { Comments } from '@/components/collaboration/Comments'
import { TermFormDialog, RelationshipManager } from '@/components/glossary'

export default function GlossaryDetail() {
  const { id } = useParams<{ id: string }>()
  const glossary = useSafeIntlayer('glossary')
  const common = useSafeIntlayer('common')
  const {
    selectedTerm,
    loading,
    fetchTerm,
    fetchCategories,
    clearSelectedTerm,
    categories,
  } = useGlossaryStore()
  const { toast } = useToast()

  const [history, setHistory] = useState<TermHistory[]>([])
  const [, setLoadingExtra] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)

  const loadData = async () => {
    if (!id) return
    try {
      await Promise.all([fetchTerm(id), fetchCategories()])

      setLoadingExtra(true)
      const historyData = await getTermHistory(id)
      setHistory(historyData)
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load term details',
        variant: 'destructive',
      })
    } finally {
      setLoadingExtra(false)
    }
  }

  useEffect(() => {
    loadData()

    return () => {
      clearSelectedTerm()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'approved':
        return 'success'
      case 'deprecated':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'approved':
        return glossary.status.approved
      case 'deprecated':
        return glossary.status.deprecated
      default:
        return glossary.status.draft
    }
  }

  if (loading || !selectedTerm) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to="/glossary"
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        {common.back}
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-lg bg-primary/10 flex items-center justify-center">
            <BookOpen className="h-7 w-7 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">{selectedTerm.name}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={getStatusBadgeVariant(selectedTerm.status)}>
                {getStatusLabel(selectedTerm.status)}
              </Badge>
              {selectedTerm.category && (
                <Badge variant="outline">{selectedTerm.category.name}</Badge>
              )}
            </div>
          </div>
        </div>

        <Button variant="outline" onClick={() => setEditDialogOpen(true)}>
          <Edit className="mr-2 h-4 w-4" />
          {common.edit}
        </Button>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">{glossary.tabs.overview}</TabsTrigger>
          <TabsTrigger value="relationships">{glossary.tabs.relationships}</TabsTrigger>
          <TabsTrigger value="history">{glossary.tabs.history}</TabsTrigger>
          <TabsTrigger value="comments">{glossary.tabs.comments}</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{glossary.definition}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{selectedTerm.definition}</p>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{glossary.category}</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{selectedTerm.category?.name || glossary.noCategory}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">{glossary.owner}</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{selectedTerm.owner_id || '-'}</p>
              </CardContent>
            </Card>
          </div>

        </TabsContent>

        {/* Relationships Tab */}
        <TabsContent value="relationships" className="space-y-4">
          <RelationshipManager
            termId={id!}
            termName={selectedTerm.name}
            onRelationshipChange={() => fetchTerm(id!)}
          />
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                {glossary.history}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  {glossary.noHistory}
                </p>
              ) : (
                <div className="space-y-3">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start gap-4 p-3 rounded-lg border"
                    >
                      <div className="flex-1">
                        <p className="font-medium">
                          {item.field_name} updated
                        </p>
                        <div className="text-sm text-muted-foreground mt-1">
                          <span>{glossary.changedFrom}: {item.old_value || '-'}</span>
                          <span className="mx-2">→</span>
                          <span>{glossary.changedTo}: {item.new_value || '-'}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {glossary.changedBy}: {item.changed_by} · {formatDate(item.changed_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Comments Tab */}
        <TabsContent value="comments">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                {glossary.tabs.comments}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Comments resourceType="term" resourceId={id!} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Term Dialog */}
      <TermFormDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        termId={id}
        categories={categories}
        onSuccess={() => {
          loadData()
          setEditDialogOpen(false)
        }}
      />
    </div>
  )
}
