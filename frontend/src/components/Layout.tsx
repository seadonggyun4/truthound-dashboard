import { Outlet, Link, useLocation } from 'react-router-dom'
import { useIntlayer } from '@/providers'
import {
  LayoutDashboard,
  Database,
  Moon,
  Sun,
  Menu,
  GitCompare,
  Clock,
  Bell,
  BookOpen,
  FolderOpen,
  Activity,
  Settings,
  Network,
  AlertTriangle,
  Shield,
  Radio,
  Cpu,
  BellRing,
  AlertCircle,
  FileText,
  Puzzle,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useTheme } from '@/components/theme-provider'
import { LanguageSelector } from '@/components/common'
import { useState, useEffect } from 'react'
import logoImg from '@/assets/logo.png'
import { apiClient } from '@/api/client'

type NavKey = 'dashboard' | 'sources' | 'catalog' | 'glossary' | 'drift' | 'lineage' | 'schedules' | 'activity' | 'notifications' | 'maintenance' | 'anomaly' | 'privacy' | 'driftMonitoring' | 'modelMonitoring' | 'notificationsAdvanced' | 'alerts' | 'reports' | 'plugins'

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
  { key: 'catalog', href: '/catalog', icon: FolderOpen, section: 'data' },
  { key: 'glossary', href: '/glossary', icon: BookOpen, section: 'data' },
  // Data Quality
  { key: 'drift', href: '/drift', icon: GitCompare, section: 'quality' },
  { key: 'driftMonitoring', href: '/drift-monitoring', icon: Radio, section: 'quality' },
  { key: 'privacy', href: '/privacy', icon: Shield, section: 'quality' },
  { key: 'lineage', href: '/lineage', icon: Network, section: 'quality' },
  // ML & Monitoring
  { key: 'anomaly', href: '/anomaly', icon: AlertTriangle, section: 'ml' },
  { key: 'modelMonitoring', href: '/model-monitoring', icon: Cpu, section: 'ml' },
  // System
  { key: 'alerts', href: '/alerts', icon: AlertCircle, section: 'system', showBadge: true },
  { key: 'schedules', href: '/schedules', icon: Clock, section: 'system' },
  { key: 'activity', href: '/activity', icon: Activity, section: 'system' },
  { key: 'notifications', href: '/notifications', icon: Bell, section: 'system' },
  { key: 'notificationsAdvanced', href: '/notifications/advanced', icon: BellRing, section: 'system' },
  { key: 'reports', href: '/reports', icon: FileText, section: 'system' },
  { key: 'plugins', href: '/plugins', icon: Puzzle, section: 'system' },
  { key: 'maintenance', href: '/maintenance', icon: Settings, section: 'system' },
]

const sectionLabels = {
  data: 'Data Management',
  quality: 'Data Quality',
  ml: 'ML & Monitoring',
  system: 'System',
}

export default function Layout() {
  const location = useLocation()
  const nav = useIntlayer('nav')
  const { theme, setTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [alertCount, setAlertCount] = useState(0)
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set())

  const toggleSection = (section: string) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev)
      if (next.has(section)) {
        next.delete(section)
      } else {
        next.add(section)
      }
      return next
    })
  }

  const groupedNav = navigation.reduce((acc, item) => {
    const section = item.section || 'other'
    if (!acc[section]) acc[section] = []
    acc[section].push(item)
    return acc
  }, {} as Record<string, NavItem[]>)

  // Fetch alert count for badge
  useEffect(() => {
    const fetchAlertCount = async () => {
      try {
        const response = await apiClient.get('/alerts/count?status=open') as { data: { data?: { count?: number } } }
        setAlertCount(response.data.data?.count || 0)
      } catch {
        // Silently fail - badge just won't show
      }
    }

    fetchAlertCount()
    // Refresh every 60 seconds
    const interval = setInterval(fetchAlertCount, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 bottom-0 z-50 w-48 transform bg-card border-r transition-transform duration-200 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <img src={logoImg} alt="Truthound" className="h-6 w-6" />
          </div>
          <span className="font-semibold text-lg">Truthound</span>
        </div>

        {/* Navigation with ScrollArea */}
        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="space-y-2">
            {Object.entries(groupedNav).map(([section, items]) => {
              const isCollapsed = collapsedSections.has(section)
              return (
                <div key={section} className="space-y-1">
                  <button
                    onClick={() => toggleSection(section)}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs font-semibold text-muted-foreground hover:bg-accent transition-colors"
                  >
                    {isCollapsed ? (
                      <ChevronRight className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                    <span>{sectionLabels[section as keyof typeof sectionLabels]}</span>
                  </button>
                  {!isCollapsed && (
                    <div className="space-y-0.5 pl-1">
                      {items.map((item) => {
                        const isActive =
                          item.href === '/'
                            ? location.pathname === '/'
                            : location.pathname.startsWith(item.href)
                        return (
                          <Link
                            key={item.key}
                            to={item.href}
                            onClick={() => setSidebarOpen(false)}
                            className={cn(
                              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                              isActive
                                ? 'bg-primary/10 text-primary'
                                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                            )}
                          >
                            <item.icon className="h-4 w-4" />
                            <span className="flex-1 text-xs">{nav[item.key]}</span>
                            {item.showBadge && alertCount > 0 && (
                              <Badge
                                variant="destructive"
                                className="h-5 min-w-[20px] px-1.5 text-xs"
                              >
                                {alertCount > 99 ? '99+' : alertCount}
                              </Badge>
                            )}
                          </Link>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </nav>
        </ScrollArea>

      </aside>

      {/* Main content */}
      <div className="lg:pl-48">
        {/* Top bar */}
        <header
          className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6"
        >
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
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
      </div>
    </div>
  )
}
