/**
 * RuleSuggestionDialog - Dialog for viewing and applying rule suggestions.
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { RuleSuggestionCard, type SuggestedRule } from './RuleSuggestionCard'
import { Loader2, Sparkles, Search, CheckSquare, Square, Filter } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface RuleSuggestionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceName: string
  suggestions: SuggestedRule[]
  isLoading?: boolean
  onApply: (selectedIds: string[]) => Promise<void>
}

export function RuleSuggestionDialog({
  open,
  onOpenChange,
  sourceName,
  suggestions,
  isLoading = false,
  onApply,
}: RuleSuggestionDialogProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [isApplying, setIsApplying] = useState(false)

  // Reset selection when dialog opens with new suggestions
  useEffect(() => {
    if (open && suggestions.length > 0) {
      // Pre-select high confidence suggestions
      const highConfidence = suggestions
        .filter((s) => s.confidence >= 85)
        .map((s) => s.id)
      setSelectedIds(new Set(highConfidence))
    }
  }, [open, suggestions])

  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const selectAll = () => {
    setSelectedIds(new Set(filteredSuggestions.map((s) => s.id)))
  }

  const deselectAll = () => {
    setSelectedIds(new Set())
  }

  const handleApply = async () => {
    if (selectedIds.size === 0) return
    setIsApplying(true)
    try {
      await onApply(Array.from(selectedIds))
      onOpenChange(false)
    } finally {
      setIsApplying(false)
    }
  }

  // Get unique categories
  const categories = [...new Set(suggestions.map((s) => s.category))]

  // Filter suggestions
  const filteredSuggestions = suggestions.filter((s) => {
    const matchesSearch =
      searchTerm === '' ||
      s.validator_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.column_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.reason.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCategory = categoryFilter === 'all' || s.category === categoryFilter

    return matchesSearch && matchesCategory
  })

  const highConfidenceCount = suggestions.filter((s) => s.confidence >= 85).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Suggested Validation Rules
          </DialogTitle>
          <DialogDescription>
            Based on profile analysis of <strong>{sourceName}</strong>, we suggest the following
            validation rules. Select the rules you want to apply.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Analyzing profile data...</p>
            </div>
          </div>
        ) : suggestions.length === 0 ? (
          <div className="flex-1 flex items-center justify-center py-12">
            <p className="text-muted-foreground">No suggestions available. Run profiling first.</p>
          </div>
        ) : (
          <>
            {/* Stats and Filters */}
            <div className="flex items-center justify-between gap-4 py-2 border-b">
              <div className="flex items-center gap-2">
                <Badge variant="secondary">
                  {suggestions.length} suggestions
                </Badge>
                <Badge variant="outline" className="bg-green-500/10 text-green-500">
                  {highConfidenceCount} high confidence
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={selectAll}
                  className="h-8 px-2"
                >
                  <CheckSquare className="h-4 w-4 mr-1" />
                  All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={deselectAll}
                  className="h-8 px-2"
                >
                  <Square className="h-4 w-4 mr-1" />
                  None
                </Button>
              </div>
            </div>

            {/* Search and Filter */}
            <div className="flex items-center gap-2 py-2">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search suggestions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 h-9"
                />
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[140px] h-9">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Suggestions List */}
            <div className="flex-1 overflow-y-auto space-y-2 py-2 min-h-[200px] max-h-[400px]">
              {filteredSuggestions.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No suggestions match your filters.
                </p>
              ) : (
                filteredSuggestions.map((suggestion) => (
                  <RuleSuggestionCard
                    key={suggestion.id}
                    suggestion={suggestion}
                    selected={selectedIds.has(suggestion.id)}
                    onToggle={toggleSelection}
                  />
                ))
              )}
            </div>
          </>
        )}

        <DialogFooter className="border-t pt-4">
          <div className="flex items-center justify-between w-full">
            <p className="text-sm text-muted-foreground">
              {selectedIds.size} of {suggestions.length} selected
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleApply}
                disabled={selectedIds.size === 0 || isApplying}
              >
                {isApplying ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Applying...
                  </>
                ) : (
                  `Apply ${selectedIds.size} Rules`
                )}
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
