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
import Glossary from './pages/Glossary'
import GlossaryDetail from './pages/GlossaryDetail'
import Catalog from './pages/Catalog'
import CatalogDetail from './pages/CatalogDetail'
import Activity from './pages/Activity'
import Maintenance from './pages/Maintenance'
import VersionHistory from './pages/VersionHistory'
import Lineage from './pages/Lineage'
import Anomaly from './pages/Anomaly'
import Privacy from './pages/Privacy'
import DriftMonitoring from './pages/DriftMonitoring'
import NotificationsAdvanced from './pages/NotificationsAdvanced'
import ModelMonitoring from './pages/ModelMonitoring'
import Alerts from './pages/Alerts'
import TriggerMonitoring from './pages/TriggerMonitoring'
import SchemaEvolution from './pages/SchemaEvolution'
import ProfileComparison from './pages/ProfileComparison'
import RuleSuggestions from './pages/RuleSuggestions'
import Plugins from './pages/Plugins'
import Reports from './pages/Reports'
import QualityReporter from './pages/QualityReporter'
import StorageTiering from './pages/StorageTiering'
import SchemaWatcher from './pages/SchemaWatcher'
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
          <Route path="sources/:id/versions" element={<VersionHistory />} />
          <Route path="validations/:id" element={<Validations />} />
          <Route path="drift" element={<Drift />} />
          <Route path="lineage" element={<Lineage />} />
          <Route path="schedules" element={<Schedules />} />
          <Route path="notifications" element={<Notifications />} />
          {/* Phase 5: Business Glossary & Data Catalog */}
          <Route path="glossary" element={<Glossary />} />
          <Route path="glossary/:id" element={<GlossaryDetail />} />
          <Route path="catalog" element={<Catalog />} />
          <Route path="catalog/:id" element={<CatalogDetail />} />
          <Route path="activity" element={<Activity />} />
          {/* Phase 4: Maintenance */}
          <Route path="maintenance" element={<Maintenance />} />
          {/* Phase 10: Advanced ML & Data Quality */}
          <Route path="anomaly" element={<Anomaly />} />
          <Route path="privacy" element={<Privacy />} />
          <Route path="drift-monitoring" element={<DriftMonitoring />} />
          <Route path="notifications/advanced" element={<NotificationsAdvanced />} />
          <Route path="model-monitoring" element={<ModelMonitoring />} />
          {/* Unified Alerts */}
          <Route path="alerts" element={<Alerts />} />
          {/* Trigger Monitoring */}
          <Route path="triggers" element={<TriggerMonitoring />} />
          {/* Schema Evolution */}
          <Route path="schema-evolution" element={<SchemaEvolution />} />
          {/* Profile Comparison */}
          <Route path="profile-comparison" element={<ProfileComparison />} />
          {/* Rule Suggestions */}
          <Route path="rule-suggestions" element={<RuleSuggestions />} />
          {/* Phase 9: Plugin System */}
          <Route path="plugins" element={<Plugins />} />
          {/* Reports & History */}
          <Route path="reports" element={<Reports />} />
          {/* Quality Reporter */}
          <Route path="quality-reporter" element={<QualityReporter />} />
          {/* Storage Tiering (truthound 1.2.10+) */}
          <Route path="storage-tiering" element={<StorageTiering />} />
          {/* Schema Watcher (truthound 1.2.10+) */}
          <Route path="schema-watcher" element={<SchemaWatcher />} />
          {/* Observability (truthound store observability) */}
          <Route path="observability" element={<Observability />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
