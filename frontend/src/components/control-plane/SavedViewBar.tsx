import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'

import {
  createSavedView,
  listSavedViews,
  type SavedView,
} from '@/api/modules/control-plane'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'

interface SavedViewBarProps {
  scope: string
  currentFilters: Record<string, unknown>
  onApply: (filters: Record<string, unknown>) => void
}

export function SavedViewBar({ scope, currentFilters, onApply }: SavedViewBarProps) {
  const { toast } = useToast()
  const [views, setViews] = useState<SavedView[]>([])
  const [selectedViewId, setSelectedViewId] = useState<string>('custom')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const loadViews = async () => {
    try {
      const response = await listSavedViews(scope)
      setViews(response.data)
    } catch {
      // Silent: saved views are optional control-plane sugar.
    }
  }

  useEffect(() => {
    void loadViews()
  }, [scope])

  const handleApply = (viewId: string) => {
    setSelectedViewId(viewId)
    if (viewId === 'custom') {
      return
    }
    const view = views.find((item) => item.id === viewId)
    if (view) {
      onApply(view.filters)
    }
  }

  const handleSave = async () => {
    if (!name.trim()) return
    try {
      setIsSaving(true)
      await createSavedView({
        scope,
        name: name.trim(),
        description: description.trim() || undefined,
        filters: currentFilters,
      })
      setDialogOpen(false)
      setName('')
      setDescription('')
      await loadViews()
      toast({ title: 'Saved view created' })
    } catch {
      toast({ title: 'Failed to save view', variant: 'destructive' })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <Select value={selectedViewId} onValueChange={handleApply}>
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Saved views" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="custom">Custom view</SelectItem>
            {views.map((view) => (
              <SelectItem key={view.id} value={view.id}>
                {view.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={() => setDialogOpen(true)}>
          <Save className="mr-2 h-4 w-4" />
          Save View
        </Button>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save current view</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor={`saved-view-name-${scope}`}>Name</Label>
              <Input
                id={`saved-view-name-${scope}`}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Production sources"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`saved-view-description-${scope}`}>Description</Label>
              <Input
                id={`saved-view-description-${scope}`}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Optional notes"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving || !name.trim()}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
