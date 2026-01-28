/**
 * TierPolicyBuilder - Build and configure tier migration policies.
 */

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { ArrowRight, Layers, Save } from 'lucide-react'
import { TierSelector } from './TierSelector'
import { PolicyConfigForm } from './PolicyConfigForm'
import {
  getPolicyTypeLabel,
  type StorageTier,
  type TierPolicy,
  type TierPolicyType,
  type TierPolicyCreate,
  type MigrationDirection,
  type PolicyConfig,
} from '@/api/modules/tiering'

interface TierPolicyBuilderProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  tiers: StorageTier[]
  parentPolicies?: TierPolicy[]
  policy?: TierPolicy | null
  onSave: (data: TierPolicyCreate) => Promise<void>
  loading?: boolean
}

const POLICY_TYPES: TierPolicyType[] = [
  'age_based',
  'access_based',
  'size_based',
  'scheduled',
  'composite',
  'custom',
]

const DEFAULT_CONFIGS: Record<TierPolicyType, PolicyConfig> = {
  age_based: { after_days: 7 },
  access_based: { inactive_days: 30, access_window_days: 7 },
  size_based: { min_size_mb: 100 },
  scheduled: { min_age_days: 0 },
  composite: { require_all: true, child_policy_ids: [] },
  custom: { predicate_expression: '', description: '' },
}

export function TierPolicyBuilder({
  open,
  onOpenChange,
  tiers,
  parentPolicies = [],
  policy,
  onSave,
  loading = false,
}: TierPolicyBuilderProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [policyType, setPolicyType] = useState<TierPolicyType>('age_based')
  const [fromTierId, setFromTierId] = useState<string>('')
  const [toTierId, setToTierId] = useState<string>('')
  const [direction, setDirection] = useState<MigrationDirection>('demote')
  const [config, setConfig] = useState<PolicyConfig>(DEFAULT_CONFIGS.age_based)
  const [isActive, setIsActive] = useState(true)
  const [priority, setPriority] = useState(0)
  const [parentId, setParentId] = useState<string | null>(null)

  const isEdit = !!policy

  // Reset form when opening or policy changes
  useEffect(() => {
    if (open) {
      if (policy) {
        setName(policy.name)
        setDescription(policy.description || '')
        setPolicyType(policy.policy_type)
        setFromTierId(policy.from_tier_id)
        setToTierId(policy.to_tier_id)
        setDirection(policy.direction)
        setConfig(policy.config)
        setIsActive(policy.is_active)
        setPriority(policy.priority)
        setParentId(policy.parent_id)
      } else {
        setName('')
        setDescription('')
        setPolicyType('age_based')
        setFromTierId(tiers[0]?.id || '')
        setToTierId(tiers[1]?.id || '')
        setDirection('demote')
        setConfig(DEFAULT_CONFIGS.age_based)
        setIsActive(true)
        setPriority(0)
        setParentId(null)
      }
    }
  }, [open, policy, tiers])

  // Update config when policy type changes
  const handlePolicyTypeChange = (type: TierPolicyType) => {
    setPolicyType(type)
    setConfig(DEFAULT_CONFIGS[type])
  }

  const handleSubmit = async () => {
    const data: TierPolicyCreate = {
      name,
      description: description || undefined,
      policy_type: policyType,
      from_tier_id: fromTierId,
      to_tier_id: toTierId,
      direction,
      config,
      is_active: isActive,
      priority,
      parent_id: parentId || undefined,
    }
    await onSave(data)
  }

  const isValid =
    name.trim() !== '' &&
    fromTierId !== '' &&
    toTierId !== '' &&
    fromTierId !== toTierId

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            {isEdit ? 'Edit Tier Policy' : 'Create Tier Policy'}
          </DialogTitle>
          <DialogDescription>
            Define a migration policy to automatically move data between storage tiers.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="basic" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="tiers">Tiers</TabsTrigger>
            <TabsTrigger value="config">Configuration</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="name">Policy Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Move old data to warm tier"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this policy does..."
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="policy_type">Policy Type *</Label>
              <Select value={policyType} onValueChange={handlePolicyTypeChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {POLICY_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      <div className="flex items-center gap-2">
                        <span>{getPolicyTypeLabel(type)}</span>
                        {type === 'composite' && (
                          <Badge variant="secondary" className="text-xs">
                            AND/OR
                          </Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Active</Label>
                <p className="text-xs text-muted-foreground">
                  Enable this policy for automatic migrations
                </p>
              </div>
              <Switch checked={isActive} onCheckedChange={setIsActive} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="priority">Priority</Label>
                <Input
                  id="priority"
                  type="number"
                  min={0}
                  max={1000}
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value) || 0)}
                />
                <p className="text-xs text-muted-foreground">
                  Lower values run first
                </p>
              </div>
              {parentPolicies.length > 0 && (
                <div className="space-y-2">
                  <Label>Parent Policy</Label>
                  <Select
                    value={parentId || ''}
                    onValueChange={(v) => setParentId(v || null)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="None (root policy)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None (root policy)</SelectItem>
                      {parentPolicies.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="tiers" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Source Tier *</Label>
              <TierSelector
                tiers={tiers}
                value={fromTierId}
                onChange={setFromTierId}
                placeholder="Select source tier"
                excludeId={toTierId}
              />
            </div>

            <div className="flex items-center justify-center py-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <ArrowRight className="h-5 w-5" />
                <Badge variant={direction === 'demote' ? 'destructive' : 'default'}>
                  {direction === 'demote' ? 'Demote' : 'Promote'}
                </Badge>
                <ArrowRight className="h-5 w-5" />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Destination Tier *</Label>
              <TierSelector
                tiers={tiers}
                value={toTierId}
                onChange={setToTierId}
                placeholder="Select destination tier"
                excludeId={fromTierId}
              />
            </div>

            <div className="space-y-2">
              <Label>Migration Direction</Label>
              <Select
                value={direction}
                onValueChange={(v) => setDirection(v as MigrationDirection)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="demote">
                    <div>
                      <div>Demote</div>
                      <div className="text-xs text-muted-foreground">
                        Move to cheaper/slower tier
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="promote">
                    <div>
                      <div>Promote</div>
                      <div className="text-xs text-muted-foreground">
                        Move to faster/more expensive tier
                      </div>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </TabsContent>

          <TabsContent value="config" className="space-y-4 mt-4">
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium mb-4 flex items-center gap-2">
                {getPolicyTypeLabel(policyType)} Configuration
                {policyType === 'composite' && (
                  <Badge variant="outline">AND/OR Logic</Badge>
                )}
              </h4>
              <PolicyConfigForm
                policyType={policyType}
                config={config}
                onChange={setConfig}
              />
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-6">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || loading}>
            <Save className="h-4 w-4 mr-2" />
            {loading ? 'Saving...' : isEdit ? 'Update Policy' : 'Create Policy'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
