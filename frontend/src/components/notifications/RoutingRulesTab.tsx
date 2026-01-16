/**
 * Routing Rules Tab Component
 * Displays and manages notification routing rules
 */

import { useState, useEffect } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  Plus,
  MoreHorizontal,
  Edit,
  Trash2,
  ArrowUpDown,
  Loader2,
} from 'lucide-react'
import type { RoutingRule, NotificationChannel } from '@/api/client'
import {
  listRoutingRules,
  createRoutingRule,
  updateRoutingRule,
  deleteRoutingRule,
  listNotificationChannels,
} from '@/api/client'

interface RoutingRulesTabProps {
  className?: string
}

export function RoutingRulesTab({ className }: RoutingRulesTabProps) {
  const content = useIntlayer('notificationsAdvanced')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [rules, setRules] = useState<RoutingRule[]>([])
  const [channels, setChannels] = useState<NotificationChannel[]>([])
  const [loading, setLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<RoutingRule | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [ruleToDelete, setRuleToDelete] = useState<RoutingRule | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formPriority, setFormPriority] = useState(0)
  const [formStopOnMatch, setFormStopOnMatch] = useState(false)
  const [formIsActive, setFormIsActive] = useState(true)
  const [formRuleConfig, setFormRuleConfig] = useState('{}')
  const [formActions, setFormActions] = useState<string[]>([])
  const [formSaving, setFormSaving] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [rulesRes, channelsRes] = await Promise.all([
        listRoutingRules(),
        listNotificationChannels(),
      ])
      setRules(rulesRes.items || [])
      setChannels(channelsRes.data || [])
    } catch {
      toast({
        title: str(content.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const openCreateDialog = () => {
    setEditingRule(null)
    setFormName('')
    setFormPriority(0)
    setFormStopOnMatch(false)
    setFormIsActive(true)
    setFormRuleConfig('{"type": "always", "params": {}}')
    setFormActions([])
    setIsDialogOpen(true)
  }

  const openEditDialog = (rule: RoutingRule) => {
    setEditingRule(rule)
    setFormName(rule.name)
    setFormPriority(rule.priority)
    setFormStopOnMatch(rule.stop_on_match)
    setFormIsActive(rule.is_active)
    setFormRuleConfig(JSON.stringify(rule.rule_config, null, 2))
    setFormActions(rule.actions)
    setIsDialogOpen(true)
  }

  const handleSave = async () => {
    setFormSaving(true)
    try {
      const ruleConfig = JSON.parse(formRuleConfig)
      const data = {
        name: formName,
        priority: formPriority,
        stop_on_match: formStopOnMatch,
        is_active: formIsActive,
        rule_config: ruleConfig,
        actions: formActions,
      }

      if (editingRule) {
        await updateRoutingRule(editingRule.id, data)
        toast({ title: str(content.success.configUpdated) })
      } else {
        await createRoutingRule(data)
        toast({ title: str(content.success.configCreated) })
      }

      setIsDialogOpen(false)
      loadData()
    } catch (e) {
      toast({
        title: editingRule
          ? str(content.errors.updateFailed)
          : str(content.errors.createFailed),
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setFormSaving(false)
    }
  }

  const confirmDelete = (rule: RoutingRule) => {
    setRuleToDelete(rule)
    setDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!ruleToDelete) return

    try {
      await deleteRoutingRule(ruleToDelete.id)
      toast({ title: str(content.success.configDeleted) })
      setDeleteDialogOpen(false)
      setRuleToDelete(null)
      loadData()
    } catch {
      toast({
        title: str(content.errors.deleteFailed),
        variant: 'destructive',
      })
    }
  }

  const toggleActive = async (rule: RoutingRule) => {
    try {
      await updateRoutingRule(rule.id, { is_active: !rule.is_active })
      setRules((prev) =>
        prev.map((r) => (r.id === rule.id ? { ...r, is_active: !r.is_active } : r))
      )
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  const getChannelName = (channelId: string) => {
    const channel = channels.find((c) => c.id === channelId)
    return channel?.name || channelId.slice(0, 8)
  }

  const getRuleTypeLabel = (config: Record<string, unknown>): string => {
    const type = config.type as string
    const labels: Record<string, string> = {
      severity: 'Severity',
      issue_count: 'Issue Count',
      pass_rate: 'Pass Rate',
      time_window: 'Time Window',
      tag: 'Tag',
      data_asset: 'Data Asset',
      metadata: 'Metadata',
      status: 'Status',
      error: 'Error',
      always: 'Always',
      never: 'Never',
      all_of: 'All Of',
      any_of: 'Any Of',
      not: 'Not',
    }
    return labels[type] || type
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{content.routing.title}</h3>
          <p className="text-sm text-muted-foreground">{content.routing.subtitle}</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-2" />
          {content.routing.addRule}
        </Button>
      </div>

      {rules.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          {content.routing.noRules}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{content.common.name}</TableHead>
              <TableHead className="w-[100px]">
                <div className="flex items-center gap-1">
                  {content.routing.priority}
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </TableHead>
              <TableHead>Type</TableHead>
              <TableHead>{content.routing.actions}</TableHead>
              <TableHead className="w-[100px]">{content.routing.stopOnMatch}</TableHead>
              <TableHead className="w-[80px]">{content.common.active}</TableHead>
              <TableHead className="w-[60px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rules
              .sort((a, b) => b.priority - a.priority)
              .map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell className="font-medium">{rule.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{rule.priority}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">{getRuleTypeLabel(rule.rule_config)}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {rule.actions.slice(0, 3).map((channelId) => (
                        <Badge key={channelId} variant="outline" className="text-xs">
                          {getChannelName(channelId)}
                        </Badge>
                      ))}
                      {rule.actions.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{rule.actions.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {rule.stop_on_match ? (
                      <Badge variant="default">Yes</Badge>
                    ) : (
                      <Badge variant="outline">No</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={rule.is_active}
                      onCheckedChange={() => toggleActive(rule)}
                    />
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEditDialog(rule)}>
                          <Edit className="h-4 w-4 mr-2" />
                          {common.edit}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => confirmDelete(rule)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          {common.delete}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingRule ? content.routing.editRule : content.routing.addRule}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{content.common.name}</Label>
                <Input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="Rule name"
                />
              </div>
              <div className="space-y-2">
                <Label>{content.routing.priority}</Label>
                <Input
                  type="number"
                  value={formPriority}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormPriority(parseInt(e.target.value) || 0)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>{content.routing.ruleConfig}</Label>
              <Textarea
                value={formRuleConfig}
                onChange={(e) => setFormRuleConfig(e.target.value)}
                className="font-mono text-sm"
                rows={6}
              />
            </div>

            <div className="space-y-2">
              <Label>{content.routing.actions}</Label>
              <div className="flex flex-wrap gap-2">
                {channels.map((channel) => (
                  <Badge
                    key={channel.id}
                    variant={formActions.includes(channel.id) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => {
                      setFormActions((prev) =>
                        prev.includes(channel.id)
                          ? prev.filter((id) => id !== channel.id)
                          : [...prev, channel.id]
                      )
                    }}
                  >
                    {channel.name}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  checked={formStopOnMatch}
                  onCheckedChange={setFormStopOnMatch}
                />
                <Label>{content.routing.stopOnMatch}</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={formIsActive} onCheckedChange={setFormIsActive} />
                <Label>{content.common.active}</Label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button onClick={handleSave} disabled={formSaving || !formName}>
              {formSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{common.delete}</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to delete "{ruleToDelete?.name}"?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              {common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
