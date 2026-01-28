import { useState, useEffect, useMemo } from 'react'
import { useIntlayer } from '@/providers'
import { Link } from 'react-router-dom'
import {
  Plus,
  Trash2,
  Link2,
  ArrowUp,
  ArrowDown,
  ArrowLeftRight,
  Copy,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  getTerms,
  getTermRelationships,
  createRelationship,
  deleteRelationship,
  type GlossaryTerm,
  type TermRelationship,
} from '@/api/modules/glossary'

type RelationshipType = 'synonym' | 'related' | 'parent' | 'child'

interface RelationshipManagerProps {
  termId: string
  termName: string
  onRelationshipChange?: () => void
}

const RELATIONSHIP_ICONS: Record<RelationshipType, typeof Link2> = {
  synonym: Copy,
  related: ArrowLeftRight,
  parent: ArrowUp,
  child: ArrowDown,
}

const RELATIONSHIP_COLORS: Record<RelationshipType, string> = {
  synonym: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  related: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  parent: 'bg-green-500/10 text-green-500 border-green-500/20',
  child: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
}

export function RelationshipManager({
  termId,
  termName,
  onRelationshipChange,
}: RelationshipManagerProps) {
  const glossary = useIntlayer('glossary')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [relationships, setRelationships] = useState<TermRelationship[]>([])
  const [allTerms, setAllTerms] = useState<GlossaryTerm[]>([])
  const [loading, setLoading] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  // Form state
  const [selectedType, setSelectedType] = useState<RelationshipType>('related')
  const [selectedTermId, setSelectedTermId] = useState<string>('')

  // Load relationships and all terms
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      try {
        const [rels, terms] = await Promise.all([
          getTermRelationships(termId),
          getTerms(),
        ])
        setRelationships(rels)
        setAllTerms(terms)
      } catch {
        toast({
          title: str(common.error),
          description: str(glossary.loadError),
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [termId, toast, common, glossary])

  // Group relationships by type
  const groupedRelationships = useMemo(() => {
    const groups: Record<RelationshipType, TermRelationship[]> = {
      synonym: [],
      related: [],
      parent: [],
      child: [],
    }
    relationships.forEach((r) => {
      if (groups[r.relationship_type]) {
        groups[r.relationship_type].push(r)
      }
    })
    return groups
  }, [relationships])

  // Filter out terms that already have a relationship or are the current term
  const availableTerms = useMemo(() => {
    const existingTargetIds = new Set(relationships.map((r) => r.target_term_id))
    return allTerms.filter(
      (t) => t.id !== termId && !existingTargetIds.has(t.id)
    )
  }, [allTerms, relationships, termId])

  const handleAddRelationship = async () => {
    if (!selectedTermId || !selectedType) return

    setLoading(true)
    try {
      const newRel = await createRelationship({
        source_term_id: termId,
        target_term_id: selectedTermId,
        relationship_type: selectedType,
      })
      setRelationships((prev) => [...prev, newRel])
      setDialogOpen(false)
      setSelectedTermId('')
      setSelectedType('related')
      toast({
        title: str(common.success),
        description: str(glossary.relationshipManagement.createSuccess),
      })
      onRelationshipChange?.()
    } catch (err) {
      const message = err instanceof Error ? err.message : ''
      if (message.includes('already exists')) {
        toast({
          title: str(common.error),
          description: str(glossary.relationshipManagement.duplicateError),
          variant: 'destructive',
        })
      } else if (message.includes('itself')) {
        toast({
          title: str(common.error),
          description: str(glossary.relationshipManagement.selfReferenceError),
          variant: 'destructive',
        })
      } else {
        toast({
          title: str(common.error),
          description: str(glossary.relationshipManagement.createError),
          variant: 'destructive',
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteRelationship = async (relId: string) => {
    setLoading(true)
    try {
      await deleteRelationship(relId)
      setRelationships((prev) => prev.filter((r) => r.id !== relId))
      toast({
        title: str(common.success),
        description: str(glossary.relationshipManagement.deleteSuccess),
      })
      onRelationshipChange?.()
    } catch {
      toast({
        title: str(common.error),
        description: str(glossary.relationshipManagement.deleteError),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const getRelationshipLabel = (type: RelationshipType) => {
    switch (type) {
      case 'synonym':
        return glossary.relationshipTypes.synonym
      case 'related':
        return glossary.relationshipTypes.related
      case 'parent':
        return glossary.relationshipTypes.parent
      case 'child':
        return glossary.relationshipTypes.child
    }
  }

  const renderRelationshipGroup = (
    type: RelationshipType,
    rels: TermRelationship[]
  ) => {
    const Icon = RELATIONSHIP_ICONS[type]
    const colorClass = RELATIONSHIP_COLORS[type]

    const getGroupTitle = () => {
      switch (type) {
        case 'synonym':
          return glossary.synonyms
        case 'related':
          return glossary.relatedTerms
        case 'parent':
          return glossary.relationshipManagement.parentTerms
        case 'child':
          return glossary.relationshipManagement.childTerms
      }
    }

    return (
      <Card key={type}>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Icon className="h-4 w-4" />
            {getGroupTitle()}
            <Badge variant="secondary" className="ml-auto">
              {rels.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {rels.length === 0 ? (
            <p className="text-sm text-muted-foreground">-</p>
          ) : (
            <div className="space-y-2">
              {rels.map((rel) => (
                <div
                  key={rel.id}
                  className="flex items-center justify-between p-2 rounded-lg border hover:bg-accent/50 transition-colors"
                >
                  <Link
                    to={`/glossary/${rel.target_term.id}`}
                    className="flex items-center gap-2 flex-1 min-w-0"
                  >
                    <Badge variant="outline" className={colorClass}>
                      {getRelationshipLabel(type)}
                    </Badge>
                    <span className="font-medium truncate">
                      {rel.target_term.name}
                    </span>
                  </Link>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={(e) => {
                      e.preventDefault()
                      handleDeleteRelationship(rel.id)
                    }}
                    disabled={loading}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with Add button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Link2 className="h-5 w-5" />
          {glossary.relationshipManagement.title}
        </h3>
        <Button onClick={() => setDialogOpen(true)} size="sm">
          <Plus className="mr-2 h-4 w-4" />
          {glossary.relationshipManagement.addRelationship}
        </Button>
      </div>

      {/* Relationship groups */}
      <div className="grid gap-4 md:grid-cols-2">
        {renderRelationshipGroup('parent', groupedRelationships.parent)}
        {renderRelationshipGroup('child', groupedRelationships.child)}
        {renderRelationshipGroup('synonym', groupedRelationships.synonym)}
        {renderRelationshipGroup('related', groupedRelationships.related)}
      </div>

      {/* Add Relationship Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {glossary.relationshipManagement.addRelationship}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>{glossary.relationshipManagement.selectRelationType}</Label>
              <Select
                value={selectedType}
                onValueChange={(v) => setSelectedType(v as RelationshipType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="parent">
                    <div className="flex items-center gap-2">
                      <ArrowUp className="h-4 w-4" />
                      {glossary.relationshipTypes.parent}
                    </div>
                  </SelectItem>
                  <SelectItem value="child">
                    <div className="flex items-center gap-2">
                      <ArrowDown className="h-4 w-4" />
                      {glossary.relationshipTypes.child}
                    </div>
                  </SelectItem>
                  <SelectItem value="synonym">
                    <div className="flex items-center gap-2">
                      <Copy className="h-4 w-4" />
                      {glossary.relationshipTypes.synonym}
                    </div>
                  </SelectItem>
                  <SelectItem value="related">
                    <div className="flex items-center gap-2">
                      <ArrowLeftRight className="h-4 w-4" />
                      {glossary.relationshipTypes.related}
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>{glossary.relationshipManagement.selectTargetTerm}</Label>
              <Select value={selectedTermId} onValueChange={setSelectedTermId}>
                <SelectTrigger>
                  <SelectValue placeholder={str(glossary.selectTerm)} />
                </SelectTrigger>
                <SelectContent>
                  {availableTerms.length === 0 ? (
                    <div className="p-2 text-sm text-muted-foreground text-center">
                      {glossary.noTerms}
                    </div>
                  ) : (
                    availableTerms.map((term) => (
                      <SelectItem key={term.id} value={term.id}>
                        {term.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Preview */}
            {selectedTermId && (
              <div className="p-3 rounded-lg bg-muted/50 text-sm">
                <span className="font-medium">{termName}</span>
                <span className="mx-2">→</span>
                <Badge variant="outline" className={RELATIONSHIP_COLORS[selectedType]}>
                  {getRelationshipLabel(selectedType)}
                </Badge>
                <span className="mx-2">→</span>
                <span className="font-medium">
                  {availableTerms.find((t) => t.id === selectedTermId)?.name}
                </span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button
              onClick={handleAddRelationship}
              disabled={!selectedTermId || loading}
            >
              {loading ? common.saving : common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
