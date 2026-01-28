/**
 * CompositePolicyBuilder - Visual builder for composite tier policies with AND/OR logic.
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertTriangle,
  GitBranch,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  Layers,
} from 'lucide-react'
import {
  getPolicyTypeLabel,
  getPolicyConfigSummary,
  type TierPolicy,
  type TierPolicyWithChildren,
} from '@/api/modules/tiering'

interface CompositePolicyBuilderProps {
  policy: TierPolicyWithChildren
  allPolicies: TierPolicy[]
  onAddChild: (parentId: string, childId: string) => Promise<void>
  onRemoveChild: (childId: string) => Promise<void>
  loading?: boolean
}

export function CompositePolicyBuilder({
  policy,
  allPolicies,
  onAddChild,
  onRemoveChild,
  loading = false,
}: CompositePolicyBuilderProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ [policy.id]: true })
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [selectedParentId, setSelectedParentId] = useState<string | null>(null)

  const isAndLogic = (policy.config as { require_all?: boolean }).require_all !== false

  // Get available policies that can be added as children
  const getAvailablePolicies = (parentId: string) => {
    const existingChildIds = new Set(
      allPolicies.filter((p) => p.parent_id === parentId).map((p) => p.id)
    )
    return allPolicies.filter(
      (p) =>
        p.id !== policy.id &&
        !existingChildIds.has(p.id) &&
        p.policy_type !== 'composite' &&
        !p.parent_id // Only root policies can be added as children
    )
  }

  const toggleExpand = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const handleOpenAddDialog = (parentId: string) => {
    setSelectedParentId(parentId)
    setAddDialogOpen(true)
  }

  const handleAddChild = async (childId: string) => {
    if (selectedParentId) {
      await onAddChild(selectedParentId, childId)
      setAddDialogOpen(false)
      setSelectedParentId(null)
    }
  }

  const renderPolicyNode = (
    node: TierPolicyWithChildren,
    depth: number = 0
  ): React.ReactNode => {
    const isComposite = node.policy_type === 'composite'
    const hasChildren = node.children && node.children.length > 0
    const isExpanded = expanded[node.id]
    const nodeIsAndLogic = isComposite
      ? (node.config as { require_all?: boolean }).require_all !== false
      : null

    return (
      <div
        key={node.id}
        className={`${depth > 0 ? 'ml-6 border-l-2 border-muted pl-4' : ''}`}
      >
        <div
          className={`flex items-center gap-2 p-2 rounded-md hover:bg-muted/50 ${
            isComposite ? 'bg-muted/30' : ''
          }`}
        >
          {isComposite && hasChildren ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => toggleExpand(node.id)}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          ) : (
            <div className="w-6" />
          )}

          {isComposite ? (
            <Layers className="h-4 w-4 text-primary" />
          ) : (
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          )}

          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">{node.name}</span>
              <Badge variant="outline" className="text-xs">
                {getPolicyTypeLabel(node.policy_type)}
              </Badge>
              {isComposite && (
                <Badge
                  variant={nodeIsAndLogic ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {nodeIsAndLogic ? 'AND' : 'OR'}
                </Badge>
              )}
            </div>
            <div className="text-xs text-muted-foreground">
              {node.from_tier_name} → {node.to_tier_name}
              {!isComposite && (
                <span className="ml-2">
                  ({getPolicyConfigSummary(node.policy_type, node.config)})
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            {!node.is_active && (
              <Badge variant="outline" className="text-xs">
                Inactive
              </Badge>
            )}
            {isComposite && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0"
                onClick={() => handleOpenAddDialog(node.id)}
                disabled={loading}
              >
                <Plus className="h-4 w-4" />
              </Button>
            )}
            {depth > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                onClick={() => onRemoveChild(node.id)}
                disabled={loading}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {isComposite && hasChildren && isExpanded && (
          <div className="mt-1">
            {node.children.map((child) => renderPolicyNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  const availablePolicies = selectedParentId
    ? getAvailablePolicies(selectedParentId)
    : []

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Layers className="h-5 w-5" />
          Composite Policy Structure
          <Badge variant={isAndLogic ? 'default' : 'secondary'} className="ml-2">
            {isAndLogic ? 'AND Logic' : 'OR Logic'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {policy.children.length < 2 && (
          <div className="flex items-center gap-2 p-3 mb-4 bg-amber-500/10 text-amber-700 dark:text-amber-400 rounded-md">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm">
              Composite policies require at least 2 child policies to function.
            </span>
          </div>
        )}

        <div className="space-y-1">{renderPolicyNode(policy)}</div>

        <div className="mt-4 p-3 bg-muted/50 rounded-md text-sm text-muted-foreground">
          <strong>{isAndLogic ? 'AND Logic:' : 'OR Logic:'}</strong>{' '}
          {isAndLogic
            ? 'All child policies must match for migration to occur.'
            : 'Any child policy match triggers migration.'}
        </div>
      </CardContent>

      {/* Add Child Policy Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Child Policy</DialogTitle>
            <DialogDescription>
              Select a policy to add as a child. Only non-composite root policies
              can be added.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {availablePolicies.length === 0 ? (
              <div className="text-center py-4 text-muted-foreground">
                No available policies to add. Create more policies first.
              </div>
            ) : (
              availablePolicies.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between p-3 border rounded-md hover:bg-muted/50 cursor-pointer"
                  onClick={() => handleAddChild(p.id)}
                >
                  <div>
                    <div className="font-medium">{p.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {getPolicyTypeLabel(p.policy_type)} • {p.from_tier_name} →{' '}
                      {p.to_tier_name}
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {getPolicyConfigSummary(p.policy_type, p.config)}
                  </Badge>
                </div>
              ))
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
