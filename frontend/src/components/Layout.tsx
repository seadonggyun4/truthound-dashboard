import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import {
  LayoutDashboard,
  Database,
  Moon,
  Sun,
  Menu,
  GitCompare,
  Clock,
  Bell,
  Network,
  AlertTriangle,
  Shield,
  BellRing,
  AlertCircle,
  FileText,
  Puzzle,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Loader2,
  HardDrive,
  BarChart3,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useTheme } from '@/components/theme-provider'
import { LanguageSelector } from '@/components/common'
import { getSession, type SessionContext } from '@/api/modules/control-plane'
import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import logoImg from '@/assets/logo.png'
import { request } from '@/api/core'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

// Navigation throttle delay (ms) - must wait this long between navigations
const NAV_THROTTLE_MS = 800

type NavKey =
  | 'dashboard'
  | 'sources'
  | 'drift'
  | 'lineage'
  | 'anomaly'
  | 'privacy'
  | 'alerts'
  | 'schedules'
  | 'notifications'
  | 'notificationsAdvanced'
  | 'reports'
  | 'plugins'
  | 'storageTiering'
  | 'observability'

interface NavItem {
  key: NavKey
  href: string
  icon: typeof LayoutDashboard
  section?: 'data' | 'quality' | 'ml' | 'system'
  showBadge?: boolean
}

const navigation: NavItem[] = [
  // Data Management
  { key: 'dashboard', href: '/', icon: LayoutDashboard, section: 'data' },
  { key: 'sources', href: '/sources', icon: Database, section: 'data' },
  // Data Quality
  { key: 'drift', href: '/drift', icon: GitCompare, section: 'quality' },
  { key: 'privacy', href: '/privacy', icon: Shield, section: 'quality' },
  { key: 'lineage', href: '/lineage', icon: Network, section: 'quality' },
  // ML & Monitoring
  { key: 'anomaly', href: '/anomaly', icon: AlertTriangle, section: 'ml' },
  // System
  { key: 'alerts', href: '/alerts', icon: AlertCircle, section: 'system', showBadge: true },
  { key: 'schedules', href: '/schedules', icon: Clock, section: 'system' },
  { key: 'notifications', href: '/notifications', icon: Bell, section: 'system' },
  { key: 'notificationsAdvanced', href: '/notifications/advanced', icon: BellRing, section: 'system' },
  { key: 'reports', href: '/reports', icon: FileText, section: 'system' },
  { key: 'plugins', href: '/plugins', icon: Puzzle, section: 'system' },
  { key: 'storageTiering', href: '/storage-tiering', icon: HardDrive, section: 'system' },
  { key: 'observability', href: '/observability', icon: BarChart3, section: 'system' },
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const nav = useSafeIntlayer('nav')
  const { theme, setTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebar-collapsed')
    return saved === 'true'
  })
  const [alertCount, setAlertCount] = useState(0)
  const [localIP, setLocalIP] = useState<string>('')
  const [sessionContext, setSessionContext] = useState<SessionContext | null>(null)

  // Navigation loading state
  const [isNavigating, setIsNavigating] = useState(false)
  const lastNavTime = useRef(0)
  const navTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const sidebarWidth = sidebarCollapsed ? 64 : 220

  const toggleSidebarCollapsed = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev
      localStorage.setItem('sidebar-collapsed', String(next))
      return next
    })
  }, [])

  // Collapsible section states
  const [dataOpen, setDataOpen] = useState(true)
  const [qualityOpen, setQualityOpen] = useState(true)
  const [mlOpen, setMlOpen] = useState(true)
  const [systemOpen, setSystemOpen] = useState(true)

  const isRouteActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    // /validations/* routes should highlight Data Sources (sources)
    if (path === '/sources' && location.pathname.startsWith('/validations')) {
      return true
    }
    if (location.pathname === path) return true
    if (location.pathname.startsWith(`${path}/`)) {
      // Don't match parent if a more specific nav item exists for this path
      const hasMoreSpecific = navigation.some(
        (item) => item.href !== path && item.href.startsWith(`${path}/`) && location.pathname.startsWith(item.href)
      )
      return !hasMoreSpecific
    }
    return false
  }

  // Throttled navigation handler
  const handleNavClick = useCallback((e: React.MouseEvent, href: string) => {
    e.preventDefault()

    const now = Date.now()

    // Skip if already navigating or within throttle window
    if (isNavigating || now - lastNavTime.current < NAV_THROTTLE_MS) {
      return
    }

    // Skip if already on this page
    if (isRouteActive(href)) {
      setSidebarOpen(false)
      return
    }

    lastNavTime.current = now
    setIsNavigating(true)
    setSidebarOpen(false)

    // Navigate immediately
    navigate(href)
  }, [isNavigating, navigate, isRouteActive])

  // Clear loading state after navigation completes + minimum display time
  useEffect(() => {
    // Keep loading overlay visible for at least 500ms after navigation
    const timer = setTimeout(() => {
      setIsNavigating(false)
    }, 500)

    return () => clearTimeout(timer)
  }, [location.pathname])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (navTimeoutRef.current) {
        clearTimeout(navTimeoutRef.current)
      }
    }
  }, [])

  // Get hostname and port from browser
  useEffect(() => {
    const host = window.location.hostname
    const port = window.location.port
    setLocalIP(port ? `${host}:${port}` : host)
  }, [])

  // Fetch alert count for badge
  useEffect(() => {
    const fetchAlertCount = async () => {
      try {
        const response = await request<{ count?: number }>('/alerts/count', { params: { status: 'open' } })
        setAlertCount(response.count || 0)
      } catch {
        // Silently fail - badge just won't show
      }
    }

    fetchAlertCount()
    // Refresh every 60 seconds
    const interval = setInterval(fetchAlertCount, 60000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const bootstrapSession = async () => {
      try {
        const session = await getSession()
        setSessionContext(session)
      } catch {
        // Keep the dashboard usable even if the control-plane bootstrap fails.
      }
    }
    void bootstrapSession()
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'fixed left-0 top-0 bottom-0 z-50 transform bg-card/70 backdrop-blur-xl border-r border-[--glass-border] transition-all duration-200 lg:translate-x-0 flex flex-col h-screen',
          sidebarCollapsed ? 'w-16' : 'w-[220px]',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className={cn(
          'flex h-16 items-center gap-2 border-b border-[--glass-border] flex-shrink-0',
          sidebarCollapsed ? 'justify-center px-2' : 'px-6'
        )}>
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <img src={logoImg} alt="Truthound" className="h-6 w-6" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-lg">Truthound</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className={cn(
          'flex-1 overflow-y-auto space-y-2 min-h-0',
          sidebarCollapsed ? 'p-2' : 'p-4'
        )}>
          {/* Data Management Section */}
          {sidebarCollapsed ? (
            <div className="space-y-1">
              <div className="h-px bg-border my-2" />
              {navigation.filter(item => item.section === 'data').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <Tooltip key={item.key}>
                    <TooltipTrigger asChild>
                      <a
                        href={item.href}
                        onClick={(e) => handleNavClick(e, item.href)}
                        className={cn(
                          'flex items-center justify-center rounded-lg p-2.5 transition-colors relative',
                          isActive
                            ? 'bg-primary/15 text-primary'
                            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                          isNavigating && 'pointer-events-none opacity-50'
                        )}
                      >
                        <item.icon className="h-4 w-4" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="right">{nav[item.key]}</TooltipContent>
                  </Tooltip>
                )
              })}
            </div>
          ) : (
          <Collapsible open={dataOpen} onOpenChange={setDataOpen}>
            <CollapsibleTrigger className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {dataOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              <span>Data Management</span>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 mt-1">
              {navigation.filter(item => item.section === 'data').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <a
                    key={item.key}
                    href={item.href}
                    onClick={(e) => handleNavClick(e, item.href)}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ml-6',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                      isNavigating && 'pointer-events-none opacity-50'
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    <span className="flex-1">{nav[item.key]}</span>
                  </a>
                )
              })}
            </CollapsibleContent>
          </Collapsible>
          )}

          {/* Data Quality Section */}
          {sidebarCollapsed ? (
            <div className="space-y-1">
              <div className="h-px bg-border my-2" />
              {navigation.filter(item => item.section === 'quality').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <Tooltip key={item.key}>
                    <TooltipTrigger asChild>
                      <a
                        href={item.href}
                        onClick={(e) => handleNavClick(e, item.href)}
                        className={cn(
                          'flex items-center justify-center rounded-lg p-2.5 transition-colors',
                          isActive
                            ? 'bg-primary/15 text-primary'
                            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                          isNavigating && 'pointer-events-none opacity-50'
                        )}
                      >
                        <item.icon className="h-4 w-4" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="right">{nav[item.key]}</TooltipContent>
                  </Tooltip>
                )
              })}
            </div>
          ) : (
          <Collapsible open={qualityOpen} onOpenChange={setQualityOpen}>
            <CollapsibleTrigger className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {qualityOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              <span>Data Quality</span>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 mt-1">
              {navigation.filter(item => item.section === 'quality').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <a
                    key={item.key}
                    href={item.href}
                    onClick={(e) => handleNavClick(e, item.href)}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ml-6',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                      isNavigating && 'pointer-events-none opacity-50'
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    <span className="flex-1">{nav[item.key]}</span>
                  </a>
                )
              })}
            </CollapsibleContent>
          </Collapsible>
          )}

          {/* ML & Monitoring Section */}
          {sidebarCollapsed ? (
            <div className="space-y-1">
              <div className="h-px bg-border my-2" />
              {navigation.filter(item => item.section === 'ml').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <Tooltip key={item.key}>
                    <TooltipTrigger asChild>
                      <a
                        href={item.href}
                        onClick={(e) => handleNavClick(e, item.href)}
                        className={cn(
                          'flex items-center justify-center rounded-lg p-2.5 transition-colors',
                          isActive
                            ? 'bg-primary/15 text-primary'
                            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                          isNavigating && 'pointer-events-none opacity-50'
                        )}
                      >
                        <item.icon className="h-4 w-4" />
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="right">{nav[item.key]}</TooltipContent>
                  </Tooltip>
                )
              })}
            </div>
          ) : (
          <Collapsible open={mlOpen} onOpenChange={setMlOpen}>
            <CollapsibleTrigger className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {mlOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              <span>ML & Monitoring</span>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 mt-1">
              {navigation.filter(item => item.section === 'ml').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <a
                    key={item.key}
                    href={item.href}
                    onClick={(e) => handleNavClick(e, item.href)}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ml-6',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                      isNavigating && 'pointer-events-none opacity-50'
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    <span className="flex-1">{nav[item.key]}</span>
                  </a>
                )
              })}
            </CollapsibleContent>
          </Collapsible>
          )}

          {/* System Section */}
          {sidebarCollapsed ? (
            <div className="space-y-1">
              <div className="h-px bg-border my-2" />
              {navigation.filter(item => item.section === 'system').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <Tooltip key={item.key}>
                    <TooltipTrigger asChild>
                      <a
                        href={item.href}
                        onClick={(e) => handleNavClick(e, item.href)}
                        className={cn(
                          'flex items-center justify-center rounded-lg p-2.5 transition-colors relative',
                          isActive
                            ? 'bg-primary/15 text-primary'
                            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                          isNavigating && 'pointer-events-none opacity-50'
                        )}
                      >
                        <item.icon className="h-4 w-4" />
                        {item.showBadge && alertCount > 0 && (
                          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive" />
                        )}
                      </a>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <span>{nav[item.key]}</span>
                      {item.showBadge && alertCount > 0 && (
                        <Badge variant="destructive" className="ml-2 h-5 min-w-[20px] px-1.5 text-xs">
                          {alertCount > 99 ? '99+' : alertCount}
                        </Badge>
                      )}
                    </TooltipContent>
                  </Tooltip>
                )
              })}
            </div>
          ) : (
          <Collapsible open={systemOpen} onOpenChange={setSystemOpen}>
            <CollapsibleTrigger className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {systemOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              <span>System</span>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 mt-1">
              {navigation.filter(item => item.section === 'system').map((item) => {
                const isActive = isRouteActive(item.href)
                return (
                  <a
                    key={item.key}
                    href={item.href}
                    onClick={(e) => handleNavClick(e, item.href)}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ml-6',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                      isNavigating && 'pointer-events-none opacity-50'
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    <span className="flex-1">{nav[item.key]}</span>
                    {item.showBadge && alertCount > 0 && (
                      <Badge
                        variant="destructive"
                        className="h-5 min-w-[20px] px-1.5 text-xs"
                      >
                        {alertCount > 99 ? '99+' : alertCount}
                      </Badge>
                    )}
                  </a>
                )
              })}
            </CollapsibleContent>
          </Collapsible>
          )}
        </nav>

        {/* Collapse toggle */}
        <div className="border-t border-[--glass-border] p-2 flex-shrink-0 hidden lg:block">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleSidebarCollapsed}
                className={cn('w-full', sidebarCollapsed ? 'justify-center px-0' : 'justify-start')}
              >
                {sidebarCollapsed ? (
                  <PanelLeftOpen className="h-4 w-4" />
                ) : (
                  <>
                    <PanelLeftClose className="h-4 w-4 mr-2" />
                    <span className="text-xs text-muted-foreground">Collapse</span>
                  </>
                )}
              </Button>
            </TooltipTrigger>
            {sidebarCollapsed && <TooltipContent side="right">Expand sidebar</TooltipContent>}
          </Tooltip>
        </div>
      </aside>
      </TooltipProvider>

      {/* Main content */}
      <div
        className="transition-all duration-200"
        style={{ paddingLeft: `var(--sidebar-width, 0px)` }}
      >
        <style>{`@media (min-width: 1024px) { :root { --sidebar-width: ${sidebarWidth}px; } }`}</style>
        {/* Top bar */}
        <header
          className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-[--glass-border] bg-background/70 backdrop-blur-xl shadow-sm shadow-black/5 px-6"
        >
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          {localIP && (
            <div className="hidden lg:flex items-center gap-2 text-xs text-muted-foreground font-mono">
              <span className="px-2 py-1 rounded-md bg-muted/50">
                {localIP}
              </span>
            </div>
          )}
          {sessionContext && (
            <div className="hidden lg:flex items-center gap-2">
              <Badge variant="outline">{sessionContext.workspace.name}</Badge>
              <Badge variant="secondary">{sessionContext.user.display_name}</Badge>
            </div>
          )}
          <div className="flex-1" />
          <div className="flex items-center gap-1">
            <LanguageSelector iconOnly />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title="Toggle theme"
            >
              {theme === 'dark' ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>

        {/* Navigation loading overlay */}
        {isNavigating && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">Loading...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
