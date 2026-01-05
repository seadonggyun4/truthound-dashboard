import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Sources from './pages/Sources'
import SourceDetail from './pages/SourceDetail'
import Rules from './pages/Rules'
import Validations from './pages/Validations'
import History from './pages/History'
import Profile from './pages/Profile'
import Drift from './pages/Drift'
import Schedules from './pages/Schedules'

function App() {
  return (
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
      </Route>
    </Routes>
  )
}

export default App
