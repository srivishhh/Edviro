import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowRight } from 'lucide-react';
import { Header } from '../../components/Header';
import { GlassCard } from '../../components/GlassCard';

const INVESTIGATIONS_LIST = [
  {
    id: 'inc-701',
    assetId: 'AHU-007',
    alertType: 'AIRFLOW_RESTRICTION',
    severity: 'HIGH',
    status: 'COMPLETED',
    diagnosis: 'VFD belt slippage or inlet guide vane mechanical obstruction on supply fan.',
    timestamp: '2026-09-15T09:41:32Z',
  },
  {
    id: 'inc-609',
    assetId: 'AHU-003',
    alertType: 'FILTER_PRESSURE_HIGH',
    severity: 'MEDIUM',
    status: 'RESOLVED',
    diagnosis: 'Filter bank particulate saturation exceeding 350 Pa limit.',
    timestamp: '2026-09-12T10:15:00Z',
  },
];

const Investigations: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] transition-colors">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-main)]">AI Investigations & Incidents</h1>
            <p className="text-sm text-[var(--text-muted)]">SNS Multi-Agent diagnostic executions and technician task dispatch.</p>
          </div>
        </div>

        <div className="space-y-4">
          {INVESTIGATIONS_LIST.map((item) => (
            <GlassCard
              key={item.id}
              onClick={() => navigate(`/investigations/${item.id}`)}
              className="p-5 flex flex-wrap items-center justify-between gap-4"
            >
              <div className="flex items-start gap-4">
                <div className="rounded-xl border border-[#F25912]/30 bg-[#F25912]/10 p-3 text-[#F25912]">
                  <AlertTriangle size={20} />
                </div>

                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-[var(--text-main)] text-base">{item.alertType}</span>
                    <span className="rounded-lg bg-[#5C3E94]/15 px-2 py-0.5 text-xs font-mono text-[#5C3E94] dark:text-purple-300 font-semibold border border-[#5C3E94]/30">
                      {item.assetId}
                    </span>
                    <span
                      className={`rounded-lg px-2 py-0.5 text-[10px] font-bold ${
                        item.severity === 'HIGH' ? 'bg-[#F25912]/20 text-[#F25912]' : 'bg-amber-500/20 text-amber-500'
                      }`}
                    >
                      {item.severity}
                    </span>
                  </div>

                  <p className="text-xs text-[var(--text-muted)] max-w-2xl">{item.diagnosis}</p>
                  <p className="text-[11px] text-[var(--text-muted)] font-mono mt-2">
                    ID: {item.id} • {new Date(item.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <span
                  className={`rounded-xl px-3 py-1 text-xs font-bold ${
                    item.status === 'RESOLVED'
                      ? 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/30'
                      : 'bg-[#5C3E94]/15 text-[#5C3E94] dark:text-purple-300 border border-[#5C3E94]/30'
                  }`}
                >
                  {item.status}
                </span>

                <div className="flex items-center gap-1 text-xs text-[#5C3E94] dark:text-purple-300 font-semibold">
                  <span>Open Report</span>
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

export default Investigations;
