import { useEffect, useState, useMemo, useCallback } from 'react'
import { useIntlayer } from '@/providers'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import { useGlossaryStore } from '@/stores/glossaryStore'
import type { GlossaryCategory } from '@/api/modules/glossary'

interface CategoryFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  category?: GlossaryCategory | null
  defaultParentId?: string
  onSuccess?: () => void
}

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
  defaultParentId,
  onSuccess,
}: CategoryFormDialogProps) {
  const glossary = useIntlayer('glossary')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const { categories, createCategory, updateCategory } = useGlossaryStore()

  const [loading, setLoading] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [parentId, setParentId] = useState<string>('')

  const isEditing = !!category

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      if (category) {
        setName(category.name)
        setDescription(category.description || '')
        setParentId(category.parent_id || '')
      } else {
        setName('')
        setDescription('')
        setParentId(defaultParentId || '')
      }
    }
  }, [open, category, defaultParentId])

  // Get available parents (exclude self and descendants to prevent circular reference)
  const availableParents = useMemo(() => {
    if (!category) return categories

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

    const excludeIds = new Set([category.id, ...getDescendantIds(category.id)])
    return categories.filter((c) => !excludeIds.has(c.id))
  }, [categories, category])

  // Build path string for category display
  const getCategoryPath = useCallback(
    (cat: GlossaryCategory): string => {
      const path: string[] = []
      let currentId: string | undefined = cat.parent_id
      while (currentId) {
        const parent = categories.find((c) => c.id === currentId)
        if (parent) {
          path.unshift(parent.name)
          currentId = parent.parent_id
        } else {
          break
        }
      }
      return path.length > 0 ? `${path.join(' > ')} > ${cat.name}` : cat.name
    },
    [categories]
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    setLoading(true)
    try {
      if (isEditing && category) {
        await updateCategory(category.id, {
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
      onOpenChange(false)
      onSuccess?.()
    } catch {
      toast({
        title: str(common.error),
        description: str(
          isEditing
            ? glossary.categoryManagement.updateError
            : glossary.categoryManagement.createError
        ),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isEditing
              ? glossary.categoryManagement.editCategory
              : glossary.categoryManagement.addCategory}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="categoryName">
              {glossary.categoryManagement.categoryName}
            </Label>
            <Input
              id="categoryName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Financial Metrics"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="categoryDesc">{glossary.definition}</Label>
            <Textarea
              id="categoryDesc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description for this category..."
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
                <SelectValue placeholder={str(glossary.categoryManagement.noParent)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">
                  {glossary.categoryManagement.noParent}
                </SelectItem>
                {availableParents.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id}>
                    {getCategoryPath(cat)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {glossary.hierarchy.rootLevel}:{' '}
              {parentId
                ? getCategoryPath(
                    availableParents.find((c) => c.id === parentId) || {
                      id: '',
                      name: '',
                      created_at: '',
                      updated_at: '',
                    }
                  )
                : str(glossary.categoryManagement.noParent)}
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              {common.cancel}
            </Button>
            <Button type="submit" disabled={!name.trim() || loading}>
              {loading ? common.saving : common.save}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
