import { useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { Activity, AlertTriangle, Building2, Gauge, LayoutDashboard, ShieldCheck } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Assets from './pages/Assets'
import AssetDetails from './pages/AssetDetails'
import DigitalTwin from './pages/DigitalTwin'
import Alerts from './pages/Alerts'
import XRay from './pages/XRay'
import { apiGet } from './services/api'

interface SystemStatus {
  backend: string
  database: string
  kafka: string
  xray: string
  simulator: string
}

const navigation = [
  { label: 'Dashboard', to: '/', icon: LayoutDashboard },
  { label: 'Assets', to: '/assets', icon: Building2 },
  { label: 'Digital Twin', to: '/digital-twin', icon: Activity },
  { label: 'Alerts', to: '/alerts', icon: AlertTriangle },
  { label: 'Facility Memory', to: '/facility-memory', icon: ShieldCheck },
  { label: 'X-Ray', to: '/x-ray', icon: Gauge },
]

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)

  useEffect(() => {
    let isMounted = true
    const checkStatus = async () => {
      try {
        const data = await apiGet<SystemStatus>('/api/v1/system/status')
        if (isMounted) {
          setStatus(data)
        }
      } catch {
        if (isMounted) {
          setStatus({
            backend: 'offline',
            database: 'unavailable',
            kafka: 'unavailable',
            xray: 'offline',
            simulator: 'offline',
          })
        }
      }
    }
    void checkStatus()
    const interval = window.setInterval(checkStatus, 15000)
    return () => {
      isMounted = false
      window.clearInterval(interval)
    }
  }, [])

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <div className="mx-auto max-w-7xl px-4 py-6 md:px-6">
          <header className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-slate-950/40">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <p className="text-sm uppercase tracking-[0.22em] text-cyan-400">Facility Intelligence Copilot</p>
                  <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/80 px-2.5 py-0.5 text-xs text-slate-300">
                    <span className="flex items-center gap-1 font-mono">
                      API <span className={status?.backend === 'healthy' ? 'text-emerald-400' : 'text-red-400'}>●</span>
                    </span>
                    <span className="text-slate-600">|</span>
                    <span className="flex items-center gap-1 font-mono">
                      Postgres <span className={status?.database === 'healthy' ? 'text-emerald-400' : 'text-slate-500'}>{status?.database === 'healthy' ? '●' : '○'}</span>
                    </span>
                    <span className="text-slate-600">|</span>
                    <span className="flex items-center gap-1 font-mono">
                      Kafka <span className={status?.kafka === 'healthy' ? 'text-emerald-400' : 'text-slate-500'}>{status?.kafka === 'healthy' ? '●' : '○'}</span>
                    </span>
                    <span className="text-slate-600">|</span>
                    <span className="flex items-center gap-1 font-mono">
                      Twin <span className="text-emerald-400">●</span>
                    </span>
                    <span className="text-slate-600">|</span>
                    <span className="flex items-center gap-1 font-mono">
                      X-Ray <span className={status?.xray === 'ready' ? 'text-cyan-400' : 'text-slate-500'}>●</span>
                    </span>
                  </div>
                </div>
                <h1 className="mt-2 text-3xl font-bold text-slate-100">Operations Intelligence</h1>
              </div>

              <nav className="flex flex-wrap gap-2">
                {navigation.map(({ label, to, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }: { isActive: boolean }) =>
                      `inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm transition ${isActive
                        ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-200'
                        : 'border-slate-700 bg-slate-950/60 text-slate-300 hover:border-slate-600 hover:text-slate-100'
                      }`
                    }
                  >
                    <Icon size={16} />
                    {label}
                  </NavLink>
                ))}
              </nav>
            </div>
          </header>


          <main className="space-y-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/assets" element={<Assets />} />
              <Route path="/assets/:assetId" element={<AssetDetails />} />
              <Route path="/digital-twin" element={<DigitalTwin />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/facility-memory" element={<div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Facility Memory placeholder — to be implemented later.</div>} />
              <Route path="/x-ray" element={<XRay />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App
