import { Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { DemoBanner } from './components/DemoBanner'
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

// Import i18n configuration
import './i18n'

function App() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
      <DemoBanner />
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
          <Route path="schedules" element={<Schedules />} />
          <Route path="notifications" element={<Notifications />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
