import { NavLink } from 'react-router-dom';
import {
  AlertCircle,
  Boxes,
  Brain,
  Building2,
  ChevronDown,
  Gauge,
  LayoutDashboard,
  Network,
  SlidersHorizontal,
  Sparkles,
  Workflow,
} from 'lucide-react';
import type { SystemStatus } from '../../types';
import { StatusIndicator } from '../ui/StatusIndicator';

interface SidebarProps {
  status: SystemStatus | null;
  alertCount?: number;
}

const NAV_ITEMS = [
  { label: 'Overview', to: '/', icon: LayoutDashboard },
  { label: 'Assets', to: '/assets', icon: Building2 },
  { label: 'Digital Twin', to: '/digital-twin', icon: Boxes },
  { label: 'Alerts', to: '/alerts', icon: AlertCircle, hasBadge: true },
  { label: 'Incident Graph', to: '/incident-graph', icon: Network },
  { label: 'Facility X-Ray', to: '/x-ray', icon: Gauge },
  { label: 'Facility Memory', to: '/facility-memory', icon: Brain },
  { label: 'AI Workbench', to: '/sns-workbench', icon: Workflow },
  { label: 'What-If Simulator', to: '/what-if', icon: SlidersHorizontal },
];

export function Sidebar({ status, alertCount = 2 }: SidebarProps) {
  const isApiOnline = status?.backend === 'healthy';
  const isTwinLive = true;
  const isXRayReady = status?.xray === 'ready' || true;

  return (
    <aside className="w-64 shrink-0 flex flex-col justify-between h-screen sticky top-0 border-r border-zinc-200/90 bg-[#fdfdfd] p-5 select-none z-30">
      <div className="space-y-6">
        {/* Brand Logo Header */}
        <div className="flex items-center gap-3 px-2 pt-1">
          <div className="w-8 h-8 rounded-xl bg-zinc-950 flex items-center justify-center text-white shadow-sm shrink-0">
            <Sparkles size={16} strokeWidth={2} />
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-tight text-zinc-950 uppercase leading-none">
              GSENSE
            </h1>
            <p className="text-[11px] font-medium text-zinc-500 mt-0.5 tracking-tight">
              Facility Intelligence
            </p>
          </div>
        </div>

        {/* Facility Scope Selector */}
        <div className="p-2.5 rounded-xl border border-zinc-200/80 bg-zinc-50/80 flex items-center justify-between text-xs">
          <div className="space-y-0.5">
            <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-400 block">Facility Scope</span>
            <span className="font-semibold text-zinc-800 block">LBNL RTU Dataset</span>
            <span className="text-[10px] text-zinc-500 font-mono">Live Telemetry &bull; Active</span>
          </div>
          <ChevronDown size={14} className="text-zinc-400" />
        </div>

        {/* Navigation Menu */}
        <nav className="space-y-1">
          <p className="px-3 text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-2">
            Intelligence
          </p>
          {NAV_ITEMS.map(({ label, to, icon: Icon, hasBadge }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-zinc-900 text-white shadow-sm font-semibold'
                    : 'text-zinc-600 hover:text-zinc-950 hover:bg-zinc-100/80'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon size={15} strokeWidth={1.75} />
                <span>{label}</span>
              </div>
              {hasBadge && alertCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-900 font-mono text-[10px] font-bold">
                  {alertCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Bottom Sidebar: System Health Breakdown */}
      <div className="rounded-2xl border border-zinc-200 bg-white p-3.5 space-y-2.5 shadow-sm">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-400">Node Status</span>
          <span className="text-[10px] font-mono font-bold text-zinc-600">v2.4.0</span>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-500 font-mono text-[11px]">API Engine</span>
            <StatusIndicator status={isApiOnline ? 'HEALTHY' : 'OFFLINE'} />
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-500 font-mono text-[11px]">Digital Twin</span>
            <StatusIndicator status={isTwinLive ? 'HEALTHY' : 'DEGRADED'} />
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-500 font-mono text-[11px]">X-Ray Agents</span>
            <StatusIndicator status={isXRayReady ? 'HEALTHY' : 'BUSY'} />
          </div>
        </div>
      </div>
    </aside>
  );
}
