import { useState, useMemo, useCallback } from 'react'
import { useIntlayer } from '@/providers'
import {
  Plus,
  Edit,
  Trash2,
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  MoreHorizontal,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'
import { useConfirm } from '@/components/ConfirmDialog'
import { str } from '@/lib/intlayer-utils'
import { useGlossaryStore } from '@/stores/glossaryStore'
import type { GlossaryCategory, GlossaryTerm } from '@/api/modules/glossary'

interface CategoryTreeNode extends GlossaryCategory {
  children: CategoryTreeNode[]
  termCount: number
  level: number
}

interface CategoryManagerProps {
  terms: GlossaryTerm[]
  onCategoryChange?: () => void
}

export function CategoryManager({ terms, onCategoryChange }: CategoryManagerProps) {
  const glossary = useIntlayer('glossary')
  const common = useIntlayer('common')
  const { toast } = useToast()
  const { confirm, ConfirmDialog } = useConfirm()

  const { categories, createCategory, updateCategory, deleteCategory } =
    useGlossaryStore()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<GlossaryCategory | null>(
    null
  )
  const [loading, setLoading] = useState(false)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  // Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [parentId, setParentId] = useState<string>('')

  // Build tree structure
  const categoryTree = useMemo(() => {
    const termCountMap = new Map<string, number>()
    terms.forEach((t) => {
      if (t.category_id) {
        termCountMap.set(t.category_id, (termCountMap.get(t.category_id) || 0) + 1)
      }
    })

    const buildTree = (
      parentId: string | null,
      level: number
    ): CategoryTreeNode[] => {
      return categories
        .filter((c) => (c.parent_id || null) === parentId)
        .map((c) => ({
          ...c,
          level,
          termCount: termCountMap.get(c.id) || 0,
          children: buildTree(c.id, level + 1),
        }))
        .sort((a, b) => a.name.localeCompare(b.name))
    }

    return buildTree(null, 0)
  }, [categories, terms])

  // Get flattened list for parent selection (excluding self and descendants)
  const getAvailableParents = useCallback(
    (excludeId?: string) => {
      const getDescendantIds = (nodeId: string): Set<string> => {
        const descendants = new Set<string>()
        const addDescendants = (id: string) => {
          categories
            .filter((c) => c.parent_id === id)
            .forEach((c) => {
              descendants.add(c.id)
              addDescendants(c.id)
            })
        }
        addDescendants(nodeId)
        return descendants
      }

      const excludeIds = excludeId
        ? new Set([excludeId, ...getDescendantIds(excludeId)])
        : new Set<string>()

      return categories.filter((c) => !excludeIds.has(c.id))
    },
    [categories]
  )

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const expandAll = () => {
    setExpandedIds(new Set(categories.map((c) => c.id)))
  }

  const collapseAll = () => {
    setExpandedIds(new Set())
  }

  const openCreateDialog = (parentCategory?: GlossaryCategory) => {
    setEditingCategory(null)
    setName('')
    setDescription('')
    setParentId(parentCategory?.id || '')
    setDialogOpen(true)
  }

  const openEditDialog = (category: GlossaryCategory) => {
    setEditingCategory(category)
    setName(category.name)
    setDescription(category.description || '')
    setParentId(category.parent_id || '')
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    if (!name.trim()) return

    setLoading(true)
    try {
      if (editingCategory) {
        await updateCategory(editingCategory.id, {
          name: name.trim(),
          description: description.trim() || undefined,
          parent_id: parentId || undefined,
        })
        toast({
          title: str(common.success),
          description: str(glossary.categoryManagement.updateSuccess),
        })
      } else {
        await createCategory({
          name: name.trim(),
          description: description.trim() || undefined,
          parent_id: parentId || undefined,
        })
        toast({
          title: str(common.success),
          description: str(glossary.categoryManagement.createSuccess),
        })
      }
      setDialogOpen(false)
      onCategoryChange?.()
    } catch {
      toast({
        title: str(common.error),
        description: str(
          editingCategory
            ? glossary.categoryManagement.updateError
            : glossary.categoryManagement.createError
        ),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (category: GlossaryCategory) => {
    const confirmed = await confirm({
      title: str(glossary.categoryManagement.deleteCategory),
      description: str(glossary.categoryManagement.confirmDeleteCategory),
      confirmText: str(common.delete),
      variant: 'destructive',
    })

    if (!confirmed) return

    setLoading(true)
    try {
      await deleteCategory(category.id)
      toast({
        title: str(common.success),
        description: str(glossary.categoryManagement.deleteSuccess),
      })
      onCategoryChange?.()
    } catch {
      toast({
        title: str(common.error),
        description: str(glossary.categoryManagement.deleteError),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const renderTreeNode = (node: CategoryTreeNode) => {
    const isExpanded = expandedIds.has(node.id)
    const hasChildren = node.children.length > 0

    return (
      <div key={node.id}>
        <div
          className="flex items-center gap-2 p-2 rounded-lg hover:bg-accent/50 transition-colors group"
          style={{ paddingLeft: `${node.level * 24 + 8}px` }}
        >
          {/* Expand/collapse button */}
          <button
            className="h-6 w-6 flex items-center justify-center rounded hover:bg-accent disabled:opacity-0"
            onClick={() => toggleExpand(node.id)}
            disabled={!hasChildren}
          >
            {hasChildren &&
              (isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              ))}
          </button>

          {/* Folder icon */}
          {isExpanded && hasChildren ? (
            <FolderOpen className="h-4 w-4 text-primary" />
          ) : (
            <Folder className="h-4 w-4 text-muted-foreground" />
          )}

          {/* Name */}
          <span className="font-medium flex-1">{node.name}</span>

          {/* Term count */}
          {node.termCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {node.termCount} {str(glossary.categoryManagement.termCount)}
            </Badge>
          )}

          {/* Children count */}
          {hasChildren && (
            <Badge variant="outline" className="text-xs">
              {node.children.length} {str(glossary.categoryManagement.subcategories)}
            </Badge>
          )}

          {/* Actions dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => openCreateDialog(node)}>
                <Plus className="mr-2 h-4 w-4" />
                {glossary.categoryManagement.addCategory}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => openEditDialog(node)}>
                <Edit className="mr-2 h-4 w-4" />
                {glossary.categoryManagement.editCategory}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => handleDelete(node)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {glossary.categoryManagement.deleteCategory}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Children */}
        {isExpanded && hasChildren && (
          <div>{node.children.map(renderTreeNode)}</div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">
            {glossary.categoryManagement.title}
          </h3>
          <p className="text-sm text-muted-foreground">
            {glossary.categoryManagement.subtitle}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {categories.length > 0 && (
            <>
              <Button variant="ghost" size="sm" onClick={expandAll}>
                {glossary.categoryManagement.expand}
              </Button>
              <Button variant="ghost" size="sm" onClick={collapseAll}>
                {glossary.categoryManagement.collapse}
              </Button>
            </>
          )}
          <Button onClick={() => openCreateDialog()} size="sm">
            <Plus className="mr-2 h-4 w-4" />
            {glossary.categoryManagement.addCategory}
          </Button>
        </div>
      </div>

      {/* Category tree */}
      {categoryTree.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Folder className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {glossary.categoryManagement.noCategories}
            </h3>
            <p className="text-muted-foreground text-center mb-4">
              {glossary.categoryManagement.noCategoriesDesc}
            </p>
            <Button onClick={() => openCreateDialog()}>
              <Plus className="mr-2 h-4 w-4" />
              {glossary.categoryManagement.addCategory}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-2">
            {categoryTree.map(renderTreeNode)}
          </CardContent>
        </Card>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingCategory
                ? glossary.categoryManagement.editCategory
                : glossary.categoryManagement.addCategory}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">
                {glossary.categoryManagement.categoryName}
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Financial Metrics"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">{glossary.definition}</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description..."
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>{glossary.categoryManagement.parentCategory}</Label>
              <Select
                value={parentId || 'none'}
                onValueChange={(v) => setParentId(v === 'none' ? '' : v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">
                    {glossary.categoryManagement.noParent}
                  </SelectItem>
                  {getAvailableParents(editingCategory?.id).map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button onClick={handleSubmit} disabled={!name.trim() || loading}>
              {loading ? common.saving : common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog />
    </div>
  )
}
