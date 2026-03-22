import { render, screen } from '@testing-library/react'
import { MemoryRouter, Outlet } from 'react-router-dom'
import { vi } from 'vitest'
import App from '@/App'

function makePage(name: string) {
  return function MockPage() {
    return <div data-testid={`page-${name}`}>{name}</div>
  }
}

vi.mock('@/components/Layout', () => ({
  default: () => (
    <div data-testid="layout">
      <Outlet />
    </div>
  ),
}))

vi.mock('@/components/LoadingFallback', () => ({
  LoadingFallback: () => <div data-testid="loading-fallback">loading</div>,
}))

vi.mock('@/components/ConfirmDialog', () => ({
  GlobalConfirmDialog: () => <div data-testid="global-confirm-dialog" />,
}))

vi.mock('@/pages/Dashboard', () => ({ default: makePage('dashboard') }))
vi.mock('@/pages/Sources', () => ({ default: makePage('sources') }))
vi.mock('@/pages/SourceDetail', () => ({ default: makePage('source-detail') }))
vi.mock('@/pages/Rules', () => ({ default: makePage('rules') }))
vi.mock('@/pages/Validations', () => ({ default: makePage('validations') }))
vi.mock('@/pages/History', () => ({ default: makePage('history') }))
vi.mock('@/pages/Profile', () => ({ default: makePage('profile') }))
vi.mock('@/pages/Drift', () => ({ default: makePage('drift') }))
vi.mock('@/pages/Schedules', () => ({ default: makePage('schedules') }))
vi.mock('@/pages/Notifications', () => ({ default: makePage('notifications') }))
vi.mock('@/pages/Lineage', () => ({ default: makePage('lineage') }))
vi.mock('@/pages/Anomaly', () => ({ default: makePage('anomaly') }))
vi.mock('@/pages/Privacy', () => ({ default: makePage('privacy') }))
vi.mock('@/pages/NotificationsAdvanced', () => ({ default: makePage('notifications-advanced') }))
vi.mock('@/pages/Alerts', () => ({ default: makePage('alerts') }))
vi.mock('@/pages/TriggerMonitoring', () => ({ default: makePage('triggers') }))
vi.mock('@/pages/SchemaEvolution', () => ({ default: makePage('schema-evolution') }))
vi.mock('@/pages/ProfileComparison', () => ({ default: makePage('profile-comparison') }))
vi.mock('@/pages/RuleSuggestions', () => ({ default: makePage('rule-suggestions') }))
vi.mock('@/pages/Plugins', () => ({ default: makePage('plugins') }))
vi.mock('@/pages/Reports', () => ({ default: makePage('reports') }))
vi.mock('@/pages/StorageTiering', () => ({ default: makePage('storage-tiering') }))
vi.mock('@/pages/Observability', () => ({ default: makePage('observability') }))

function renderRoute(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <App />
    </MemoryRouter>
  )
}

describe('App route smoke coverage', () => {
  it('renders the dashboard route', () => {
    renderRoute('/')

    expect(screen.getByTestId('page-dashboard')).toBeInTheDocument()
  })

  it('renders the artifact-backed reports route', () => {
    renderRoute('/reports')

    expect(screen.getByTestId('page-reports')).toBeInTheDocument()
  })

  it('renders the alerts workbench route', () => {
    renderRoute('/alerts')

    expect(screen.getByTestId('page-alerts')).toBeInTheDocument()
  })

  it('renders the history route for a source', () => {
    renderRoute('/sources/source-1/history')

    expect(screen.getByTestId('page-history')).toBeInTheDocument()
  })

  it('does not register the removed version history route', () => {
    renderRoute('/sources/source-1/versions')

    expect(screen.queryByTestId('page-history')).not.toBeInTheDocument()
    expect(screen.queryByTestId('page-source-detail')).not.toBeInTheDocument()
  })
})
