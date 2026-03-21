import { useCallback, useState } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { useApi, useMutation } from '@/hooks/use-api'
import {
  disablePlugin,
  enablePlugin,
  getMarketplaceStats,
  installPlugin,
  listPlugins,
  uninstallPlugin,
  type Plugin,
  type PluginStatus,
  type PluginType,
} from '@/api/modules/plugins'
import { str } from '@/lib/intlayer-utils'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { toast } from '@/hooks/use-toast'
import {
  AlertTriangle,
  CheckCircle,
  Download,
  Eye,
  FileText,
  MoreVertical,
  Package,
  Power,
  PowerOff,
  RefreshCw,
  Search,
  Settings,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Star,
  Trash2,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  PluginDetailDialog,
} from '@/components/plugins'

export function Plugins() {
  const t = useSafeIntlayer('plugins')
  const [activeTab, setActiveTab] = useState('marketplace')
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<PluginType | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<PluginStatus | 'all'>('all')
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null)
  const [showInstallDialog, setShowInstallDialog] = useState(false)
  const [showUninstallDialog, setShowUninstallDialog] = useState(false)
  const [showPluginDetail, setShowPluginDetail] = useState(false)

  const { data: plugins, loading: loadingPlugins, refetch: refetchPlugins } = useApi(
    () =>
      listPlugins({
        type: typeFilter !== 'all' ? typeFilter : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchQuery || undefined,
        limit: 50,
      }),
    [typeFilter, statusFilter, searchQuery]
  )

  const { data: stats } = useApi(getMarketplaceStats, [])

  const { mutate: doInstall, loading: installing } = useMutation(
    (pluginId: string) => installPlugin(pluginId)
  )
  const { mutate: doUninstall, loading: uninstalling } = useMutation(
    (pluginId: string) => uninstallPlugin(pluginId)
  )
  const { mutate: doEnable } = useMutation(
    (pluginId: string) => enablePlugin(pluginId)
  )
  const { mutate: doDisable } = useMutation(
    (pluginId: string) => disablePlugin(pluginId)
  )

  const handleViewPlugin = useCallback((plugin: Plugin) => {
    setSelectedPlugin(plugin)
    setShowPluginDetail(true)
  }, [])

  const handleInstall = async () => {
    if (!selectedPlugin) return
    try {
      await doInstall(selectedPlugin.id)
      toast({ title: str(t.messages.installSuccess) })
      setShowInstallDialog(false)
      setSelectedPlugin(null)
      refetchPlugins()
    } catch {
      toast({ title: str(t.messages.installFailed), variant: 'destructive' })
    }
  }

  const handleUninstall = async () => {
    if (!selectedPlugin) return
    try {
      await doUninstall(selectedPlugin.id)
      toast({ title: str(t.messages.uninstallSuccess) })
      setShowUninstallDialog(false)
      setSelectedPlugin(null)
      refetchPlugins()
    } catch {
      toast({ title: str(t.messages.uninstallFailed), variant: 'destructive' })
    }
  }

  const handleTogglePlugin = async (plugin: Plugin) => {
    try {
      if (plugin.is_enabled) {
        await doDisable(plugin.id)
        toast({ title: str(t.messages.disableSuccess) })
      } else {
        await doEnable(plugin.id)
        toast({ title: str(t.messages.enableSuccess) })
      }
      refetchPlugins()
    } catch {
      toast({ title: 'Operation failed', variant: 'destructive' })
    }
  }

  const getStatusBadge = (status: PluginStatus) => {
    const variants: Record<PluginStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }> = {
      available: { variant: 'outline', icon: <Package className="w-3 h-3" /> },
      installed: { variant: 'secondary', icon: <Download className="w-3 h-3" /> },
      enabled: { variant: 'default', icon: <CheckCircle className="w-3 h-3" /> },
      disabled: { variant: 'secondary', icon: <PowerOff className="w-3 h-3" /> },
      update_available: { variant: 'outline', icon: <RefreshCw className="w-3 h-3" /> },
      error: { variant: 'destructive', icon: <AlertTriangle className="w-3 h-3" /> },
    }
    const { variant, icon } = variants[status] || variants.available
    return (
      <Badge variant={variant} className="gap-1">
        {icon}
        {str(t.status[status === 'update_available' ? 'updateAvailable' : status])}
      </Badge>
    )
  }

  const getSecurityBadge = (level: string) => {
    const icons: Record<string, React.ReactNode> = {
      trusted: <ShieldCheck className="w-3 h-3 text-green-500" />,
      verified: <Shield className="w-3 h-3 text-blue-500" />,
      unverified: <ShieldAlert className="w-3 h-3 text-yellow-500" />,
      sandboxed: <Shield className="w-3 h-3 text-gray-500" />,
    }
    return (
      <Badge variant="outline" className="gap-1">
        {icons[level]}
        {str(t.security[level as keyof typeof t.security])}
      </Badge>
    )
  }

  const getTypeBadge = (type: PluginType) => {
    const icons: Record<PluginType, React.ReactNode> = {
      validator: <CheckCircle className="w-3 h-3" />,
      reporter: <FileText className="w-3 h-3" />,
      connector: <Package className="w-3 h-3" />,
      transformer: <Settings className="w-3 h-3" />,
    }
    return (
      <Badge variant="secondary" className="gap-1">
        {icons[type]}
        {str(t.types[type])}
      </Badge>
    )
  }

  const renderPluginCard = (plugin: Plugin) => (
    <Card
      key={plugin.id}
      className="flex flex-col cursor-pointer hover:border-primary/50 transition-colors"
      onClick={() => handleViewPlugin(plugin)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {plugin.icon_url ? (
              <img src={plugin.icon_url} alt="" className="w-10 h-10 rounded" />
            ) : (
              <div className="w-10 h-10 rounded bg-muted flex items-center justify-center">
                <Package className="w-5 h-5 text-muted-foreground" />
              </div>
            )}
            <div>
              <CardTitle className="text-base">{plugin.display_name}</CardTitle>
              <CardDescription className="text-xs">
                {str(t.card.by)} {plugin.author?.name || 'Unknown'} · v{plugin.version}
              </CardDescription>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(event) => event.stopPropagation()}>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={(event) => { event.stopPropagation(); handleViewPlugin(plugin) }}>
                <Eye className="w-4 h-4 mr-2" />
                {str(t.actions.viewDetails)}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {plugin.status === 'available' && (
                <DropdownMenuItem onClick={(event) => { event.stopPropagation(); setSelectedPlugin(plugin); setShowInstallDialog(true) }}>
                  <Download className="w-4 h-4 mr-2" />
                  {str(t.actions.install)}
                </DropdownMenuItem>
              )}
              {(plugin.status === 'installed' || plugin.status === 'enabled' || plugin.status === 'disabled') && (
                <>
                  <DropdownMenuItem onClick={(event) => { event.stopPropagation(); void handleTogglePlugin(plugin) }}>
                    {plugin.is_enabled ? (
                      <>
                        <PowerOff className="w-4 h-4 mr-2" />
                        {str(t.actions.disable)}
                      </>
                    ) : (
                      <>
                        <Power className="w-4 h-4 mr-2" />
                        {str(t.actions.enable)}
                      </>
                    )}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-destructive"
                    onClick={(event) => { event.stopPropagation(); setSelectedPlugin(plugin); setShowUninstallDialog(true) }}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {str(t.actions.uninstall)}
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-2">
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          {plugin.description}
        </p>
        <div className="flex flex-wrap gap-1">
          {getTypeBadge(plugin.type)}
          {getStatusBadge(plugin.status)}
          {getSecurityBadge(plugin.security_level)}
        </div>
      </CardContent>
      <CardFooter className="pt-2 border-t text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <Download className="w-3 h-3" />
            {plugin.install_count}
          </span>
          {plugin.rating && (
            <span className="flex items-center gap-1">
              <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
              {plugin.rating.toFixed(1)}
            </span>
          )}
          {plugin.validators_count > 0 && (
            <span>{plugin.validators_count} validators</span>
          )}
          {plugin.reporters_count > 0 && (
            <span>{plugin.reporters_count} reporters</span>
          )}
        </div>
      </CardFooter>
    </Card>
  )

  const installedPlugins = plugins?.data.filter((plugin) => plugin.status !== 'available') ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t.title}</h1>
          <p className="text-muted-foreground">{t.description}</p>
        </div>
        <Button onClick={() => refetchPlugins()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{stats.total_plugins}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.totalPlugins)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{stats.total_validators}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.totalValidators)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{stats.total_reporters}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.totalReporters)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{installedPlugins.length}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.installedPlugins)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{plugins?.data.filter((plugin) => plugin.is_enabled).length || 0}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.enabledPlugins)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="marketplace">{t.tabs.marketplace}</TabsTrigger>
          <TabsTrigger value="installed">{t.tabs.installed}</TabsTrigger>
        </TabsList>

        <TabsContent value="marketplace" className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder={str(t.search.placeholder)}
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={typeFilter} onValueChange={(value) => setTypeFilter(value as PluginType | 'all')}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={str(t.search.filterByType)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="validator">{str(t.types.validator)}</SelectItem>
                <SelectItem value="reporter">{str(t.types.reporter)}</SelectItem>
                <SelectItem value="connector">{str(t.types.connector)}</SelectItem>
                <SelectItem value="transformer">{str(t.types.transformer)}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as PluginStatus | 'all')}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={str(t.search.filterByStatus)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="available">{str(t.status.available)}</SelectItem>
                <SelectItem value="installed">{str(t.status.installed)}</SelectItem>
                <SelectItem value="enabled">{str(t.status.enabled)}</SelectItem>
                <SelectItem value="disabled">{str(t.status.disabled)}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {loadingPlugins ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : plugins?.data.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">{str(t.messages.noPlugins)}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {plugins?.data.map(renderPluginCard)}
            </div>
          )}
        </TabsContent>

        <TabsContent value="installed" className="space-y-4">
          {loadingPlugins ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : installedPlugins.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">{str(t.messages.noPlugins)}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {installedPlugins.map(renderPluginCard)}
            </div>
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={showInstallDialog} onOpenChange={setShowInstallDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.actions.install)} {selectedPlugin?.display_name}</DialogTitle>
            <DialogDescription>
              {selectedPlugin?.security_level === 'unverified' && (
                <div className="flex items-center gap-2 text-yellow-600 mt-2">
                  <AlertTriangle className="w-4 h-4" />
                  {str(t.securityWarnings.unverifiedPlugin)}
                </div>
              )}
              {selectedPlugin?.permissions && selectedPlugin.permissions.length > 0 && (
                <div className="mt-4">
                  <p className="font-medium">{str(t.securityWarnings.permissionsRequired)}</p>
                  <ul className="list-disc list-inside mt-2">
                    {selectedPlugin.permissions.map((permission) => (
                      <li key={permission}>{str(t.permissions[permission as keyof typeof t.permissions] || permission)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInstallDialog(false)}>
              {str(t.actions.cancel)}
            </Button>
            <Button onClick={handleInstall} disabled={installing}>
              {installing ? 'Installing...' : str(t.actions.install)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showUninstallDialog} onOpenChange={setShowUninstallDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.actions.uninstall)} {selectedPlugin?.display_name}</DialogTitle>
            <DialogDescription>{str(t.messages.confirmUninstall)}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUninstallDialog(false)}>
              {str(t.actions.cancel)}
            </Button>
            <Button variant="destructive" onClick={handleUninstall} disabled={uninstalling}>
              {uninstalling ? 'Uninstalling...' : str(t.actions.uninstall)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <PluginDetailDialog
        open={showPluginDetail}
        onOpenChange={setShowPluginDetail}
        plugin={selectedPlugin}
        onSuccess={() => {
          refetchPlugins()
          setShowPluginDetail(false)
        }}
      />
    </div>
  )
}

export default Plugins
