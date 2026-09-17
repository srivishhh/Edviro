import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Activity, AlertTriangle, ShieldCheck } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Header } from '../../components/Header';
import { GlassCard } from '../../components/GlassCard';
import { useTheme } from '../../app/ThemeProvider';

export const AssetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [telemetry, setTelemetry] = useState<any[]>([]);

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/v1/assets/${id || 7}/telemetry?limit=20`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => data && Array.isArray(data) && setTelemetry(data))
      .catch(() => {});
  }, [id]);

  const assetName = id === '7' ? 'Air Handling Unit 007' : `Asset Node ${id}`;
  const assetCode = id === '7' ? 'AHU-007' : `NODE-00${id}`;

  const chartData = telemetry.length > 0 ? telemetry : [
    { timestamp: '12:00', airflow: 72, temperature: 28.9, power: 10.8 },
    { timestamp: '12:05', airflow: 70, temperature: 29.4, power: 11.2 },
    { timestamp: '12:10', airflow: 68, temperature: 29.7, power: 11.8 },
    { timestamp: '12:15', airflow: 64, temperature: 30.1, power: 12.3 },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] transition-colors">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={() => navigate('/assets')}
          className="mb-4 flex items-center gap-2 text-xs font-semibold text-[#5C3E94] dark:text-purple-300 hover:underline"
        >
          <ArrowLeft size={14} />
          <span>Back to Assets Inventory</span>
        </button>

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-extrabold text-[var(--text-main)] tracking-tight">{assetName}</h1>
              <span className="rounded-xl bg-[#5C3E94]/15 px-2.5 py-1 text-xs font-mono text-[#5C3E94] dark:text-purple-300 font-semibold border border-[#5C3E94]/30">
                {assetCode}
              </span>
            </div>
            <p className="mt-1 text-sm text-[var(--text-muted)]">Digital Twin telemetry, health history, and active diagnostics.</p>
          </div>

          <button
            type="button"
            onClick={() => navigate('/investigations/inc-701')}
            className="flex items-center gap-2 rounded-xl border border-[#F25912]/40 bg-[#F25912]/15 px-4 py-2.5 text-xs font-bold text-[#F25912] transition-colors hover:bg-[#F25912]/25 active:scale-95"
          >
            <AlertTriangle size={15} />
            <span>View Active Investigation</span>
          </button>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Chart Section */}
          <GlassCard className="lg:col-span-2 p-6">
            <h3 className="text-base font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
              <Activity size={18} className="text-[#5C3E94] dark:text-purple-300" />
              <span>Real-Time Telemetry Curve (Airflow % & CFM)</span>
            </h3>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorAirflow" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#5C3E94" stopOpacity={theme === 'dark' ? 0.4 : 0.2} />
                      <stop offset="95%" stopColor="#5C3E94" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="timestamp" stroke={theme === 'dark' ? '#94a3b8' : '#7f7c8d'} fontSize={11} />
                  <YAxis stroke={theme === 'dark' ? '#94a3b8' : '#7f7c8d'} fontSize={11} domain={['dataMin - 5', 'dataMax + 5']} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme === 'dark' ? '#211832' : '#ffffff',
                      borderColor: theme === 'dark' ? 'rgba(92, 62, 148, 0.4)' : 'rgba(92, 62, 148, 0.2)',
                      color: theme === 'dark' ? '#f8fafc' : '#181126',
                      borderRadius: '12px',
                    }}
                  />
                  <Area type="monotone" dataKey="airflow" stroke="#5C3E94" strokeWidth={2.5} fill="url(#colorAirflow)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </GlassCard>

          {/* Node Metadata & Twin State */}
          <GlassCard className="p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-base font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                <ShieldCheck size={18} className="text-emerald-500" />
                <span>Digital Twin Topology</span>
              </h3>

              <div className="space-y-3 text-xs">
                <div className="flex justify-between border-b border-[var(--border-subtle)] pb-2">
                  <span className="text-[var(--text-muted)]">Node Status</span>
                  <span className="font-semibold text-[#F25912] uppercase">Warning / Degraded</span>
                </div>
                <div className="flex justify-between border-b border-[var(--border-subtle)] pb-2">
                  <span className="text-[var(--text-muted)]">Facility Zone</span>
                  <span className="font-semibold text-[var(--text-main)]">Building 74 • Floor 2</span>
                </div>
                <div className="flex justify-between border-b border-[var(--border-subtle)] pb-2">
                  <span className="text-[var(--text-muted)]">Active Fault</span>
                  <span className="font-semibold text-[#F25912]">Airflow Restriction</span>
                </div>
                <div className="flex justify-between border-b border-[var(--border-subtle)] pb-2">
                  <span className="text-[var(--text-muted)]">Dataset Benchmark</span>
                  <span className="font-semibold text-[var(--text-main)] font-mono">LBNL AHU_annual.csv</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-[var(--border-subtle)]">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[var(--text-muted)]">Assigned Tech</span>
                <span className="font-semibold text-[#5C3E94] dark:text-purple-300">Alex Mercer</span>
              </div>
            </div>
          </GlassCard>
        </div>
      </main>
    </div>
  );
};

export default AssetDetail;
