/**
 * StorageTieringTab - Main tab component for storage tiering management.
 *
 * Features:
 * - Storage Tiers: CRUD for hot/warm/cold/archive tiers
 * - Tier Policies: CRUD for age/access/size/scheduled/composite/custom policies
 * - Configurations: Global tiering settings
 * - Migration History: View past migrations
 */

import { useState, useCallback, useEffect } from 'react'
import { useSafeIntlayer as useIntlayer } from '@/hooks/useSafeIntlayer'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  Plus,
  Edit,
  Trash2,
  Loader2,
  Database,
  GitBranch,
  Settings,
  History,
  Layers,
  ArrowDown,
  ArrowUp,
  HardDrive,
  Flame,
  Thermometer,
  Snowflake,
  Archive,
  Search,
  RefreshCw,
  Play,
  Zap,
  CheckCircle,
  AlertCircle,
} from 'lucide-react'
import { TierSelector } from './TierSelector'
import { TierPolicyBuilder } from './TierPolicyBuilder'
import { CompositePolicyBuilder } from './CompositePolicyBuilder'
import {
  listStorageTiers,
  createStorageTier,
  updateStorageTier,
  deleteStorageTier,
  listTierPolicies,
  createTierPolicy,
  updateTierPolicy,
  deleteTierPolicy,
  getTierPolicyTree,
  listTieringConfigs,
  createTieringConfig,
  updateTieringConfig,
  deleteTieringConfig,
  listMigrationHistory,
  getTieringStatistics,
  getTieringStatus,
  executePolicy,
  processAllPolicies,
  getTierTypeLabel,
  getPolicyTypeLabel,
  getPolicyConfigSummary,
  getMigrationStatusLabel,
  formatBytes,
  type StorageTier,
  type StorageTierCreate,
  type StorageTierUpdate,
  type TierPolicy,
  type TierPolicyCreate,
  type TierPolicyUpdate,
  type TierPolicyWithChildren,
  type TieringConfig,
  type TieringConfigCreate,
  type TieringConfigUpdate,
  type MigrationHistory,
  type TieringStatistics,
  type TieringStatusResponse,
  type TierType,
  type TierPolicyType,
  type MigrationStatus,
} from '@/api/modules/tiering'

interface StorageTieringTabProps {
  className?: string
}

const TIER_TYPE_ICONS: Record<TierType, React.ReactNode> = {
  hot: <Flame className="h-4 w-4 text-red-500" />,
  warm: <Thermometer className="h-4 w-4 text-orange-500" />,
  cold: <Snowflake className="h-4 w-4 text-blue-500" />,
  archive: <Archive className="h-4 w-4 text-slate-500" />,
}

const MIGRATION_STATUS_COLORS: Record<MigrationStatus, string> = {
  pending: 'bg-yellow-500',
  in_progress: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
}

export function StorageTieringTab({ className }: StorageTieringTabProps) {
  const rawContent = useIntlayer('tiering')
  const rawCommon = useIntlayer('common')
  const { toast } = useToast()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const content = rawContent as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const common = rawCommon as any

  // Tab state
  const [activeTab, setActiveTab] = useState('tiers')

  // Data state
  const [tiers, setTiers] = useState<StorageTier[]>([])
  const [policies, setPolicies] = useState<TierPolicy[]>([])
  const [configs, setConfigs] = useState<TieringConfig[]>([])
  const [migrations, setMigrations] = useState<MigrationHistory[]>([])
  const [stats, setStats] = useState<TieringStatistics | null>(null)
  const [status, setStatus] = useState<TieringStatusResponse | null>(null)

  // Loading state
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Search state
  const [tierSearch, setTierSearch] = useState('')
  const [policySearch, setPolicySearch] = useState('')

  // Dialog state - Tiers
  const [tierDialogOpen, setTierDialogOpen] = useState(false)
  const [editingTier, setEditingTier] = useState<StorageTier | null>(null)
  const [deleteTierDialogOpen, setDeleteTierDialogOpen] = useState(false)
  const [tierToDelete, setTierToDelete] = useState<StorageTier | null>(null)

  // Dialog state - Policies
  const [policyDialogOpen, setPolicyDialogOpen] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<TierPolicy | null>(null)
  const [deletePolicyDialogOpen, setDeletePolicyDialogOpen] = useState(false)
  const [policyToDelete, setPolicyToDelete] = useState<TierPolicy | null>(null)
  const [compositePolicyTree, setCompositePolicyTree] = useState<TierPolicyWithChildren | null>(null)
  const [compositeDialogOpen, setCompositeDialogOpen] = useState(false)

  // Dialog state - Configs
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<TieringConfig | null>(null)
  const [deleteConfigDialogOpen, setDeleteConfigDialogOpen] = useState(false)
  const [configToDelete, setConfigToDelete] = useState<TieringConfig | null>(null)

  // Tier form state
  const [tierFormName, setTierFormName] = useState('')
  const [tierFormType, setTierFormType] = useState<TierType>('hot')
  const [tierFormStoreType, setTierFormStoreType] = useState('file')
  const [tierFormPriority, setTierFormPriority] = useState(1)
  const [tierFormCostPerGb, setTierFormCostPerGb] = useState<number | null>(null)
  const [tierFormRetrievalTimeMs, setTierFormRetrievalTimeMs] = useState<number | null>(null)
  const [tierFormIsActive, setTierFormIsActive] = useState(true)

  // Config form state
  const [configFormName, setConfigFormName] = useState('')
  const [configFormDescription, setConfigFormDescription] = useState('')
  const [configFormDefaultTierId, setConfigFormDefaultTierId] = useState<string | null>(null)
  const [configFormEnablePromotion, setConfigFormEnablePromotion] = useState(false)
  const [configFormPromotionThreshold, setConfigFormPromotionThreshold] = useState(10)
  const [configFormCheckIntervalHours, setConfigFormCheckIntervalHours] = useState(24)
  const [configFormBatchSize, setConfigFormBatchSize] = useState(100)
  const [configFormEnableParallel, setConfigFormEnableParallel] = useState(false)
  const [configFormMaxParallel, setConfigFormMaxParallel] = useState(4)
  const [configFormIsActive, setConfigFormIsActive] = useState(true)

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [tiersRes, policiesRes, configsRes, migrationsRes, statsRes, statusRes] = await Promise.all([
        listStorageTiers(),
        listTierPolicies(),
        listTieringConfigs(),
        listMigrationHistory({ limit: 50 }),
        getTieringStatistics(),
        getTieringStatus(),
      ])
      setTiers(tiersRes.items || [])
      setPolicies(policiesRes.items || [])
      setConfigs(configsRes.items || [])
      setMigrations(migrationsRes.items || [])
      setStats(statsRes)
      setStatus(statusRes)
    } catch {
      toast({
        title: str(content.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [toast, content.errors.loadFailed])

  useEffect(() => {
    loadData()
  }, [loadData])

  // ============================================================================
  // Tier CRUD
  // ============================================================================

  const openCreateTierDialog = () => {
    setEditingTier(null)
    setTierFormName('')
    setTierFormType('hot')
    setTierFormStoreType('file')
    setTierFormPriority(1)
    setTierFormCostPerGb(null)
    setTierFormRetrievalTimeMs(null)
    setTierFormIsActive(true)
    setTierDialogOpen(true)
  }

  const openEditTierDialog = (tier: StorageTier) => {
    setEditingTier(tier)
    setTierFormName(tier.name)
    setTierFormType(tier.tier_type)
    setTierFormStoreType(tier.store_type)
    setTierFormPriority(tier.priority)
    setTierFormCostPerGb(tier.cost_per_gb)
    setTierFormRetrievalTimeMs(tier.retrieval_time_ms)
    setTierFormIsActive(tier.is_active)
    setTierDialogOpen(true)
  }

  const handleSaveTier = async () => {
    setActionLoading(true)
    try {
      const data: StorageTierCreate | StorageTierUpdate = {
        name: tierFormName,
        tier_type: tierFormType,
        store_type: tierFormStoreType,
        priority: tierFormPriority,
        cost_per_gb: tierFormCostPerGb ?? undefined,
        retrieval_time_ms: tierFormRetrievalTimeMs ?? undefined,
        is_active: tierFormIsActive,
      }

      if (editingTier) {
        await updateStorageTier(editingTier.id, data)
        toast({ title: str(content.messages.tierUpdated) })
      } else {
        await createStorageTier(data as StorageTierCreate)
        toast({ title: str(content.messages.tierCreated) })
      }

      setTierDialogOpen(false)
      loadData()
    } catch {
      toast({
        title: editingTier ? str(content.errors.updateFailed) : str(content.errors.createFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeleteTier = async () => {
    if (!tierToDelete) return

    setActionLoading(true)
    try {
      await deleteStorageTier(tierToDelete.id)
      toast({ title: str(content.messages.tierDeleted) })
      setDeleteTierDialogOpen(false)
      setTierToDelete(null)
      loadData()
    } catch {
      toast({
        title: str(content.errors.deleteFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const toggleTierActive = async (tier: StorageTier) => {
    try {
      await updateStorageTier(tier.id, { is_active: !tier.is_active })
      setTiers((prev) =>
        prev.map((t) => (t.id === tier.id ? { ...t, is_active: !t.is_active } : t))
      )
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  // ============================================================================
  // Policy CRUD
  // ============================================================================

  const openCreatePolicyDialog = () => {
    setEditingPolicy(null)
    setPolicyDialogOpen(true)
  }

  const openEditPolicyDialog = (policy: TierPolicy) => {
    setEditingPolicy(policy)
    setPolicyDialogOpen(true)
  }

  const handleSavePolicy = async (data: TierPolicyCreate | TierPolicyUpdate) => {
    setActionLoading(true)
    try {
      if (editingPolicy) {
        await updateTierPolicy(editingPolicy.id, data)
        toast({ title: str(content.messages.policyUpdated) })
      } else {
        await createTierPolicy(data as TierPolicyCreate)
        toast({ title: str(content.messages.policyCreated) })
      }

      setPolicyDialogOpen(false)
      loadData()
    } catch {
      toast({
        title: editingPolicy ? str(content.errors.updateFailed) : str(content.errors.createFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeletePolicy = async () => {
    if (!policyToDelete) return

    setActionLoading(true)
    try {
      await deleteTierPolicy(policyToDelete.id)
      toast({ title: str(content.messages.policyDeleted) })
      setDeletePolicyDialogOpen(false)
      setPolicyToDelete(null)
      loadData()
    } catch {
      toast({
        title: str(content.errors.deleteFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const togglePolicyActive = async (policy: TierPolicy) => {
    try {
      await updateTierPolicy(policy.id, { is_active: !policy.is_active })
      setPolicies((prev) =>
        prev.map((p) => (p.id === policy.id ? { ...p, is_active: !p.is_active } : p))
      )
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  const openCompositeTreeDialog = async (policy: TierPolicy) => {
    if (policy.policy_type !== 'composite') return

    setActionLoading(true)
    try {
      const tree = await getTierPolicyTree(policy.id)
      setCompositePolicyTree(tree)
      setCompositeDialogOpen(true)
    } catch {
      toast({
        title: str(content.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleAddChildPolicy = async (parentId: string, childId: string) => {
    try {
      await updateTierPolicy(childId, { parent_id: parentId })
      // Reload tree
      const tree = await getTierPolicyTree(parentId)
      setCompositePolicyTree(tree)
      loadData()
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  const handleRemoveChildPolicy = async (childId: string) => {
    try {
      await updateTierPolicy(childId, { parent_id: undefined })
      // Reload tree if we have one open
      if (compositePolicyTree) {
        const tree = await getTierPolicyTree(compositePolicyTree.id)
        setCompositePolicyTree(tree)
      }
      loadData()
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  // ============================================================================
  // Policy Execution
  // ============================================================================

  const handleExecutePolicy = async (policy: TierPolicy, dryRun: boolean = false) => {
    setActionLoading(true)
    try {
      const result = await executePolicy(policy.id, { dry_run: dryRun })

      if (result.items_migrated > 0 || result.items_failed > 0) {
        toast({
          title: dryRun ? content.messages.dryRunComplete : content.messages.policyExecuted,
          description: `Scanned: ${result.items_scanned}, Migrated: ${result.items_migrated}, Failed: ${result.items_failed}`,
        })
      } else {
        toast({
          title: content.messages.noItemsToMigrate,
        })
      }

      // Reload data to show new migrations
      if (!dryRun) {
        loadData()
      }
    } catch {
      toast({
        title: str(content.errors.executionFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleProcessAllPolicies = async () => {
    setActionLoading(true)
    try {
      const result = await processAllPolicies()

      toast({
        title: content.messages.allPoliciesProcessed,
        description: `Policies: ${result.policies_executed}, Migrated: ${result.total_items_migrated}, Failed: ${result.total_items_failed}`,
      })

      loadData()
    } catch {
      toast({
        title: str(content.errors.executionFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  // ============================================================================
  // Config CRUD
  // ============================================================================

  const openCreateConfigDialog = () => {
    setEditingConfig(null)
    setConfigFormName('')
    setConfigFormDescription('')
    setConfigFormDefaultTierId(null)
    setConfigFormEnablePromotion(false)
    setConfigFormPromotionThreshold(10)
    setConfigFormCheckIntervalHours(24)
    setConfigFormBatchSize(100)
    setConfigFormEnableParallel(false)
    setConfigFormMaxParallel(4)
    setConfigFormIsActive(true)
    setConfigDialogOpen(true)
  }

  const openEditConfigDialog = (config: TieringConfig) => {
    setEditingConfig(config)
    setConfigFormName(config.name)
    setConfigFormDescription(config.description || '')
    setConfigFormDefaultTierId(config.default_tier_id)
    setConfigFormEnablePromotion(config.enable_promotion)
    setConfigFormPromotionThreshold(config.promotion_threshold)
    setConfigFormCheckIntervalHours(config.check_interval_hours)
    setConfigFormBatchSize(config.batch_size)
    setConfigFormEnableParallel(config.enable_parallel_migration)
    setConfigFormMaxParallel(config.max_parallel_migrations)
    setConfigFormIsActive(config.is_active)
    setConfigDialogOpen(true)
  }

  const handleSaveConfig = async () => {
    setActionLoading(true)
    try {
      const data: TieringConfigCreate | TieringConfigUpdate = {
        name: configFormName,
        description: configFormDescription || undefined,
        default_tier_id: configFormDefaultTierId ?? undefined,
        enable_promotion: configFormEnablePromotion,
        promotion_threshold: configFormPromotionThreshold,
        check_interval_hours: configFormCheckIntervalHours,
        batch_size: configFormBatchSize,
        enable_parallel_migration: configFormEnableParallel,
        max_parallel_migrations: configFormMaxParallel,
        is_active: configFormIsActive,
      }

      if (editingConfig) {
        await updateTieringConfig(editingConfig.id, data)
        toast({ title: str(content.messages.configUpdated) })
      } else {
        await createTieringConfig(data as TieringConfigCreate)
        toast({ title: str(content.messages.configCreated) })
      }

      setConfigDialogOpen(false)
      loadData()
    } catch {
      toast({
        title: editingConfig ? str(content.errors.updateFailed) : str(content.errors.createFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeleteConfig = async () => {
    if (!configToDelete) return

    setActionLoading(true)
    try {
      await deleteTieringConfig(configToDelete.id)
      toast({ title: str(content.messages.configDeleted) })
      setDeleteConfigDialogOpen(false)
      setConfigToDelete(null)
      loadData()
    } catch {
      toast({
        title: str(content.errors.deleteFailed),
        variant: 'destructive',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const toggleConfigActive = async (config: TieringConfig) => {
    try {
      await updateTieringConfig(config.id, { is_active: !config.is_active })
      setConfigs((prev) =>
        prev.map((c) => (c.id === config.id ? { ...c, is_active: !c.is_active } : c))
      )
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  // ============================================================================
  // Filtered lists
  // ============================================================================

  const filteredTiers = tiers.filter((tier) =>
    tier.name.toLowerCase().includes(tierSearch.toLowerCase())
  )

  const filteredPolicies = policies.filter((policy) =>
    policy.name.toLowerCase().includes(policySearch.toLowerCase())
  )

  // ============================================================================
  // Loading state
  // ============================================================================

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className={className}>
      {/* Status Banner */}
      {status && (
        <Card className={`mb-6 ${status.truthound_available ? 'border-green-500/50' : 'border-yellow-500/50'}`}>
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  {status.truthound_available ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                  )}
                  <span className="font-medium">
                    {status.truthound_available
                      ? content.status.truthoundConnected
                      : content.status.truthoundFallback}
                  </span>
                </div>
                <Badge variant={status.tiering_enabled ? 'default' : 'secondary'}>
                  {status.tiering_enabled ? content.status.tieringEnabled : content.status.tieringDisabled}
                </Badge>
                {status.active_config_name && (
                  <span className="text-sm text-muted-foreground">
                    Config: {status.active_config_name}
                  </span>
                )}
                <span className="text-sm text-muted-foreground">
                  {content.status.migrationsLast24h}: {status.migrations_last_24h}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleProcessAllPolicies}
                disabled={actionLoading || !status.tiering_enabled}
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4 mr-2" />
                )}
                {content.actions.processAllPolicies}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Database className="h-4 w-4" />
                {content.stats.totalTiers}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_tiers}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active_tiers} {str(content.stats.activeTiers).toLowerCase()}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                {content.stats.totalPolicies}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_policies}</div>
              <p className="text-xs text-muted-foreground">
                {stats.composite_policies} {str(content.stats.compositePolicies).toLowerCase()}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <History className="h-4 w-4" />
                {content.stats.totalMigrations}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_migrations}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-500">{stats.successful_migrations} {str(content.stats.successfulMigrations).toLowerCase()}</span>
                {' / '}
                <span className="text-red-500">{stats.failed_migrations} {str(content.stats.failedMigrations).toLowerCase()}</span>
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <HardDrive className="h-4 w-4" />
                {content.stats.totalBytesMigrated}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatBytes(stats.total_bytes_migrated)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between mb-4">
          <TabsList>
            <TabsTrigger value="tiers" className="gap-2">
              <Database className="h-4 w-4" />
              {content.tabs.tiers}
            </TabsTrigger>
            <TabsTrigger value="policies" className="gap-2">
              <GitBranch className="h-4 w-4" />
              {content.tabs.policies}
            </TabsTrigger>
            <TabsTrigger value="configs" className="gap-2">
              <Settings className="h-4 w-4" />
              {content.tabs.configs}
            </TabsTrigger>
            <TabsTrigger value="migrations" className="gap-2">
              <History className="h-4 w-4" />
              {content.tabs.migrations}
            </TabsTrigger>
          </TabsList>
          <Button variant="outline" onClick={loadData} size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            {common.refresh}
          </Button>
        </div>

        {/* Storage Tiers Tab */}
        <TabsContent value="tiers">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="relative w-64">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={str(content.placeholders.searchTiers)}
                  value={tierSearch}
                  onChange={(e) => setTierSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
              <Button onClick={openCreateTierDialog}>
                <Plus className="h-4 w-4 mr-2" />
                {content.actions.createTier}
              </Button>
            </div>

            {filteredTiers.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
                {content.empty.noTiers}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{content.form.name}</TableHead>
                    <TableHead>{content.form.tierType}</TableHead>
                    <TableHead>{content.form.storeType}</TableHead>
                    <TableHead>{content.form.priority}</TableHead>
                    <TableHead>{content.form.costPerGb}</TableHead>
                    <TableHead>{content.form.retrievalTimeMs}</TableHead>
                    <TableHead className="w-[80px]">{content.form.isActive}</TableHead>
                    <TableHead className="w-[100px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTiers.map((tier) => (
                    <TableRow key={tier.id}>
                      <TableCell className="font-medium">{tier.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="gap-1">
                          {TIER_TYPE_ICONS[tier.tier_type]}
                          {getTierTypeLabel(tier.tier_type)}
                        </Badge>
                      </TableCell>
                      <TableCell>{tier.store_type}</TableCell>
                      <TableCell>{tier.priority}</TableCell>
                      <TableCell>
                        {tier.cost_per_gb !== null ? `$${tier.cost_per_gb}` : '-'}
                      </TableCell>
                      <TableCell>
                        {tier.retrieval_time_ms !== null ? `${tier.retrieval_time_ms}ms` : '-'}
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={tier.is_active}
                          onCheckedChange={() => toggleTierActive(tier)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => openEditTierDialog(tier)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setTierToDelete(tier)
                              setDeleteTierDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </TabsContent>

        {/* Tier Policies Tab */}
        <TabsContent value="policies">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="relative w-64">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={str(content.placeholders.searchPolicies)}
                  value={policySearch}
                  onChange={(e) => setPolicySearch(e.target.value)}
                  className="pl-8"
                />
              </div>
              <Button onClick={openCreatePolicyDialog}>
                <Plus className="h-4 w-4 mr-2" />
                {content.actions.createPolicy}
              </Button>
            </div>

            {filteredPolicies.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
                {content.empty.noPolicies}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{content.form.name}</TableHead>
                    <TableHead>{content.form.policyType}</TableHead>
                    <TableHead>{content.form.fromTier} → {content.form.toTier}</TableHead>
                    <TableHead>{content.form.direction}</TableHead>
                    <TableHead>Config</TableHead>
                    <TableHead className="w-[80px]">{content.form.isActive}</TableHead>
                    <TableHead className="w-[120px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPolicies.map((policy) => (
                    <TableRow key={policy.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          {policy.parent_id && (
                            <span className="text-xs text-muted-foreground">└─</span>
                          )}
                          {policy.name}
                          {policy.policy_type === 'composite' && (
                            <Badge variant="secondary" className="text-xs">
                              <Layers className="h-3 w-3 mr-1" />
                              {policy.child_count} children
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{getPolicyTypeLabel(policy.policy_type)}</Badge>
                      </TableCell>
                      <TableCell>
                        {policy.from_tier_name || 'N/A'} → {policy.to_tier_name || 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={policy.direction === 'demote' ? 'secondary' : 'default'}
                          className="gap-1"
                        >
                          {policy.direction === 'demote' ? (
                            <ArrowDown className="h-3 w-3" />
                          ) : (
                            <ArrowUp className="h-3 w-3" />
                          )}
                          {policy.direction === 'demote'
                            ? content.migrationDirection.demote
                            : content.migrationDirection.promote}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {getPolicyConfigSummary(policy.policy_type, policy.config)}
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={policy.is_active}
                          onCheckedChange={() => togglePolicyActive(policy)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleExecutePolicy(policy, true)}
                            disabled={!policy.is_active || actionLoading}
                            title={str(content.actions.dryRun)}
                          >
                            <Search className="h-4 w-4 text-blue-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleExecutePolicy(policy, false)}
                            disabled={!policy.is_active || actionLoading}
                            title={str(content.actions.executePolicy)}
                          >
                            <Play className="h-4 w-4 text-green-500" />
                          </Button>
                          {policy.policy_type === 'composite' && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openCompositeTreeDialog(policy)}
                              title={str(content.actions.viewTree)}
                            >
                              <Layers className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => openEditPolicyDialog(policy)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setPolicyToDelete(policy)
                              setDeletePolicyDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </TabsContent>

        {/* Configurations Tab */}
        <TabsContent value="configs">
          <div className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={openCreateConfigDialog}>
                <Plus className="h-4 w-4 mr-2" />
                {content.actions.createConfig}
              </Button>
            </div>

            {configs.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
                {content.empty.noConfigs}
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {configs.map((config) => (
                  <Card key={config.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">{config.name}</CardTitle>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={config.is_active}
                            onCheckedChange={() => toggleConfigActive(config)}
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => openEditConfigDialog(config)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setConfigToDelete(config)
                              setDeleteConfigDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                      {config.description && (
                        <CardDescription>{config.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">{content.form.defaultTier}: </span>
                          <span>{config.default_tier_name || 'None'}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{content.form.checkIntervalHours}: </span>
                          <span>{config.check_interval_hours}h</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{content.form.batchSize}: </span>
                          <span>{config.batch_size}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{content.form.enablePromotion}: </span>
                          <Badge variant={config.enable_promotion ? 'default' : 'secondary'}>
                            {config.enable_promotion ? 'Yes' : 'No'}
                          </Badge>
                        </div>
                        {config.enable_parallel_migration && (
                          <div>
                            <span className="text-muted-foreground">{content.form.maxParallelMigrations}: </span>
                            <span>{config.max_parallel_migrations}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Migration History Tab */}
        <TabsContent value="migrations">
          {migrations.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
              {content.empty.noMigrations}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item ID</TableHead>
                  <TableHead>Policy</TableHead>
                  <TableHead>{content.form.fromTier} → {content.form.toTier}</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Started At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {migrations.map((migration) => (
                  <TableRow key={migration.id}>
                    <TableCell className="font-mono text-xs">
                      {migration.item_id.slice(0, 12)}...
                    </TableCell>
                    <TableCell>{migration.policy_name || 'N/A'}</TableCell>
                    <TableCell>
                      {migration.from_tier_name || 'N/A'} → {migration.to_tier_name || 'N/A'}
                    </TableCell>
                    <TableCell>{formatBytes(migration.size_bytes)}</TableCell>
                    <TableCell>
                      <Badge className={MIGRATION_STATUS_COLORS[migration.status]}>
                        {getMigrationStatusLabel(migration.status)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {migration.duration_ms !== null ? `${migration.duration_ms}ms` : '-'}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {new Date(migration.started_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>
      </Tabs>

      {/* Tier Dialog */}
      <Dialog open={tierDialogOpen} onOpenChange={setTierDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingTier ? content.actions.editTier : content.actions.createTier}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{content.form.name}</Label>
                <Input
                  value={tierFormName}
                  onChange={(e) => setTierFormName(e.target.value)}
                  placeholder="Tier name"
                />
              </div>
              <div className="space-y-2">
                <Label>{content.form.tierType}</Label>
                <Select value={tierFormType} onValueChange={(v: TierType) => setTierFormType(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hot">
                      <div className="flex items-center gap-2">{TIER_TYPE_ICONS.hot} Hot</div>
                    </SelectItem>
                    <SelectItem value="warm">
                      <div className="flex items-center gap-2">{TIER_TYPE_ICONS.warm} Warm</div>
                    </SelectItem>
                    <SelectItem value="cold">
                      <div className="flex items-center gap-2">{TIER_TYPE_ICONS.cold} Cold</div>
                    </SelectItem>
                    <SelectItem value="archive">
                      <div className="flex items-center gap-2">{TIER_TYPE_ICONS.archive} Archive</div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{content.form.storeType}</Label>
                <Input
                  value={tierFormStoreType}
                  onChange={(e) => setTierFormStoreType(e.target.value)}
                  placeholder="file, s3, gcs, azure..."
                />
              </div>
              <div className="space-y-2">
                <Label>{content.form.priority}</Label>
                <Input
                  type="number"
                  value={tierFormPriority}
                  onChange={(e) => setTierFormPriority(parseInt(e.target.value) || 1)}
                  min={1}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{content.form.costPerGb}</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={tierFormCostPerGb ?? ''}
                  onChange={(e) =>
                    setTierFormCostPerGb(e.target.value ? parseFloat(e.target.value) : null)
                  }
                  placeholder="Optional"
                />
              </div>
              <div className="space-y-2">
                <Label>{content.form.retrievalTimeMs}</Label>
                <Input
                  type="number"
                  value={tierFormRetrievalTimeMs ?? ''}
                  onChange={(e) =>
                    setTierFormRetrievalTimeMs(e.target.value ? parseInt(e.target.value) : null)
                  }
                  placeholder="Optional"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Switch checked={tierFormIsActive} onCheckedChange={setTierFormIsActive} />
              <Label>{content.form.isActive}</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setTierDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button onClick={handleSaveTier} disabled={actionLoading || !tierFormName}>
              {actionLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Policy Dialog */}
      <TierPolicyBuilder
        open={policyDialogOpen}
        onOpenChange={setPolicyDialogOpen}
        tiers={tiers}
        policy={editingPolicy}
        onSave={handleSavePolicy}
        loading={actionLoading}
      />

      {/* Composite Policy Tree Dialog */}
      <Dialog open={compositeDialogOpen} onOpenChange={setCompositeDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {compositePolicyTree?.name} - {content.composite.childPolicies}
            </DialogTitle>
            <DialogDescription>
              {content.policyTypeDescriptions.composite}
            </DialogDescription>
          </DialogHeader>

          {compositePolicyTree && (
            <CompositePolicyBuilder
              policy={compositePolicyTree}
              allPolicies={policies}
              onAddChild={handleAddChildPolicy}
              onRemoveChild={handleRemoveChildPolicy}
              loading={actionLoading}
            />
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setCompositeDialogOpen(false)}>
              {common.close}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Config Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>
              {editingConfig ? content.actions.editConfig : content.actions.createConfig}
            </DialogTitle>
          </DialogHeader>

          <ScrollArea className="max-h-[60vh] pr-4">
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{content.form.name}</Label>
                <Input
                  value={configFormName}
                  onChange={(e) => setConfigFormName(e.target.value)}
                  placeholder="Configuration name"
                />
              </div>

              <div className="space-y-2">
                <Label>{content.form.description}</Label>
                <Textarea
                  value={configFormDescription}
                  onChange={(e) => setConfigFormDescription(e.target.value)}
                  placeholder="Optional description"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label>{content.form.defaultTier}</Label>
                <TierSelector
                  tiers={tiers}
                  value={configFormDefaultTierId ?? ''}
                  onChange={(v) => setConfigFormDefaultTierId(v || null)}
                  placeholder={str(content.placeholders.selectTier)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{content.form.checkIntervalHours}</Label>
                  <Input
                    type="number"
                    value={configFormCheckIntervalHours}
                    onChange={(e) => setConfigFormCheckIntervalHours(parseInt(e.target.value) || 24)}
                    min={1}
                  />
                </div>
                <div className="space-y-2">
                  <Label>{content.form.batchSize}</Label>
                  <Input
                    type="number"
                    value={configFormBatchSize}
                    onChange={(e) => setConfigFormBatchSize(parseInt(e.target.value) || 100)}
                    min={1}
                  />
                </div>
              </div>

              <div className="space-y-4 border-t pt-4">
                <div className="flex items-center justify-between">
                  <Label>{content.form.enablePromotion}</Label>
                  <Switch
                    checked={configFormEnablePromotion}
                    onCheckedChange={setConfigFormEnablePromotion}
                  />
                </div>

                {configFormEnablePromotion && (
                  <div className="space-y-2 pl-4">
                    <Label>{content.form.promotionThreshold}</Label>
                    <Input
                      type="number"
                      value={configFormPromotionThreshold}
                      onChange={(e) => setConfigFormPromotionThreshold(parseInt(e.target.value) || 10)}
                      min={1}
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of accesses required to trigger promotion
                    </p>
                  </div>
                )}
              </div>

              <div className="space-y-4 border-t pt-4">
                <div className="flex items-center justify-between">
                  <Label>{content.form.enableParallelMigration}</Label>
                  <Switch
                    checked={configFormEnableParallel}
                    onCheckedChange={setConfigFormEnableParallel}
                  />
                </div>

                {configFormEnableParallel && (
                  <div className="space-y-2 pl-4">
                    <Label>{content.form.maxParallelMigrations}</Label>
                    <Input
                      type="number"
                      value={configFormMaxParallel}
                      onChange={(e) => setConfigFormMaxParallel(parseInt(e.target.value) || 4)}
                      min={1}
                      max={16}
                    />
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 border-t pt-4">
                <Switch checked={configFormIsActive} onCheckedChange={setConfigFormIsActive} />
                <Label>{content.form.isActive}</Label>
              </div>
            </div>
          </ScrollArea>

          <DialogFooter>
            <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button onClick={handleSaveConfig} disabled={actionLoading || !configFormName}>
              {actionLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Tier Confirmation */}
      <Dialog open={deleteTierDialogOpen} onOpenChange={setDeleteTierDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{content.actions.deleteTier}</DialogTitle>
          </DialogHeader>
          <p>{content.messages.confirmDeleteTier}</p>
          <p className="font-medium">{tierToDelete?.name}</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTierDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button variant="destructive" onClick={handleDeleteTier} disabled={actionLoading}>
              {actionLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Policy Confirmation */}
      <Dialog open={deletePolicyDialogOpen} onOpenChange={setDeletePolicyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{content.actions.deletePolicy}</DialogTitle>
          </DialogHeader>
          <p>{content.messages.confirmDeletePolicy}</p>
          <p className="font-medium">{policyToDelete?.name}</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletePolicyDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button variant="destructive" onClick={handleDeletePolicy} disabled={actionLoading}>
              {actionLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Config Confirmation */}
      <Dialog open={deleteConfigDialogOpen} onOpenChange={setDeleteConfigDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{content.actions.deleteConfig}</DialogTitle>
          </DialogHeader>
          <p>{content.messages.confirmDeleteConfig}</p>
          <p className="font-medium">{configToDelete?.name}</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfigDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfig} disabled={actionLoading}>
              {actionLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
