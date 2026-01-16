import { Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { LoadingFallback } from './components/LoadingFallback'
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

function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
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
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
