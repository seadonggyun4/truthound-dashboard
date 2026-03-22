import { Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { LoadingFallback } from './components/LoadingFallback'
import { GlobalConfirmDialog } from './components/ConfirmDialog'
import Dashboard from './pages/Dashboard'
import Sources from './pages/Sources'
import SourceDetail from './pages/SourceDetail'
import Rules from './pages/Rules'
import Validations from './pages/Validations'
import History from './pages/History'
import Profile from './pages/Profile'
import Drift from './pages/Drift'
import Schedules from './pages/Schedules'
import Notifications from './pages/Notifications'
import Lineage from './pages/Lineage'
import Anomaly from './pages/Anomaly'
import Privacy from './pages/Privacy'
import NotificationsAdvanced from './pages/NotificationsAdvanced'
import Alerts from './pages/Alerts'
import TriggerMonitoring from './pages/TriggerMonitoring'
import SchemaEvolution from './pages/SchemaEvolution'
import ProfileComparison from './pages/ProfileComparison'
import RuleSuggestions from './pages/RuleSuggestions'
import Plugins from './pages/Plugins'
import Reports from './pages/Reports'
import StorageTiering from './pages/StorageTiering'
import Observability from './pages/Observability'

function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <GlobalConfirmDialog />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="sources" element={<Sources />} />
          <Route path="sources/:id" element={<SourceDetail />} />
          <Route path="sources/:id/rules" element={<Rules />} />
          <Route path="sources/:id/history" element={<History />} />
          <Route path="sources/:id/profile" element={<Profile />} />
          <Route path="validations/:id" element={<Validations />} />
          <Route path="drift" element={<Drift />} />
          <Route path="lineage" element={<Lineage />} />
          <Route path="schedules" element={<Schedules />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="anomaly" element={<Anomaly />} />
          <Route path="privacy" element={<Privacy />} />
          <Route path="notifications/advanced" element={<NotificationsAdvanced />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="triggers" element={<TriggerMonitoring />} />
          <Route path="schema-evolution" element={<SchemaEvolution />} />
          <Route path="profile-comparison" element={<ProfileComparison />} />
          <Route path="rule-suggestions" element={<RuleSuggestions />} />
          <Route path="plugins" element={<Plugins />} />
          <Route path="reports" element={<Reports />} />
          <Route path="storage-tiering" element={<StorageTiering />} />
          <Route path="observability" element={<Observability />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
