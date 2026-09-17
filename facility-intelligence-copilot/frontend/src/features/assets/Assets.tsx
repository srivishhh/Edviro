import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Gauge, ArrowRight } from 'lucide-react';
import { Header } from '../../components/Header';
import { GlassCard } from '../../components/GlassCard';

const ASSETS_LIST = [
  { id: '1', code: 'HVAC-001', name: 'Primary Air Handler 001', type: 'HVAC', status: 'healthy', health: 94, floor: 'Floor 1' },
  { id: '2', code: 'HVAC-002', name: 'Secondary Air Handler 002', type: 'HVAC', status: 'healthy', health: 91, floor: 'Floor 1' },
  { id: '3', code: 'HVAC-003', name: 'AHU East Wing 003', type: 'HVAC', status: 'warning', health: 76, floor: 'Floor 2' },
  { id: '7', code: 'AHU-007', name: 'Air Handling Unit 007', type: 'HVAC', status: 'critical', health: 68, floor: 'Floor 2' },
  { id: '8', code: 'CHILLER-001', name: 'Centrifugal Chiller 001', type: 'Chiller', status: 'healthy', health: 89, floor: 'Basement' },
  { id: '9', code: 'CHILLER-002', name: 'Centrifugal Chiller 002', type: 'Chiller', status: 'healthy', health: 93, floor: 'Basement' },
];

const Assets: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] transition-colors">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-main)]">Facility Assets Inventory</h1>
            <p className="text-sm text-[var(--text-muted)]">Connected equipment, digital twin node health, and real-time state.</p>
          </div>
          <span className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-1 text-xs font-mono text-[#5C3E94] dark:text-purple-300 font-medium">
            {ASSETS_LIST.length} Total Nodes
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {ASSETS_LIST.map((asset) => (
            <GlassCard
              key={asset.id}
              onClick={() => navigate(`/assets/${asset.id}`)}
              className="p-5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="rounded-lg bg-[#5C3E94]/15 px-2.5 py-0.5 text-xs font-mono text-[#5C3E94] dark:text-purple-300 font-semibold border border-[#5C3E94]/30">
                    {asset.code}
                  </span>
                  <span
                    className={`rounded-lg px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                      asset.status === 'healthy'
                        ? 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/30'
                        : asset.status === 'warning'
                        ? 'bg-amber-500/15 text-amber-500 border border-amber-500/30'
                        : 'bg-[#F25912]/15 text-[#F25912] border border-[#F25912]/30'
                    }`}
                  >
                    {asset.status}
                  </span>
                </div>

                <h3 className="text-base font-bold text-[var(--text-main)]">{asset.name}</h3>
                <p className="text-xs text-[var(--text-muted)] mt-1">{asset.type} • {asset.floor}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-[var(--text-main)]">
                  <Gauge size={14} className="text-[#5C3E94] dark:text-purple-300" />
                  <span className="font-semibold font-mono">{asset.health}% Health</span>
                </div>

                <div className="flex items-center gap-1 text-xs text-[#5C3E94] dark:text-purple-300 font-semibold">
                  <span>View Details</span>
                  <ArrowRight size={14} />
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Assets;
