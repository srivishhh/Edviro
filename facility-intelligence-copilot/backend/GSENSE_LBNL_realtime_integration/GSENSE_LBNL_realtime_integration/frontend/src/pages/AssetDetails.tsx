import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, Gauge, HeartPulse, Power, Thermometer, Wind } from 'lucide-react';
import { getAsset } from '../services/assets';
import { getAssetTelemetry } from '../services/telemetry';
import type { Asset } from '../types/asset';
import type { TelemetryPoint } from '../types/telemetry';

function AssetDetails() {
  const { assetId } = useParams();
  const navigate = useNavigate();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!assetId) {
      setError('Asset identifier is missing.');
      setLoading(false);
      return;
    }

    let isMounted = true;

    const load = async () => {
      try {
        const [assetData, telemetryData] = await Promise.all([
          getAsset(Number(assetId)),
          getAssetTelemetry(Number(assetId), { limit: 20 }),
        ]);

        if (isMounted) {
          setAsset(assetData);
          setTelemetry(telemetryData);
          setError('');
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unable to load asset details.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    void load();
    const interval = window.setInterval(() => { void load(); }, 2000);
    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [assetId]);

  const latestReading = useMemo(() => telemetry[telemetry.length - 1], [telemetry]);

  if (loading) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Loading asset details...</div>;
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-8 text-red-200">
        <p className="font-semibold">Unable to load asset details.</p>
        <p className="mt-2 text-sm text-red-100/80">Check that the FastAPI backend is running.</p>
      </div>
    );
  }

  if (!asset) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Asset not found.</div>;
  }

  const metricCards = [
    { label: 'Status', value: asset.status, icon: Activity, tone: 'text-cyan-300' },
    { label: 'Health', value: `${asset.health_score}`, icon: HeartPulse, tone: 'text-emerald-300' },
    { label: 'Temperature', value: latestReading ? `${latestReading.temperature.toFixed(1)}°C` : '—', icon: Thermometer, tone: 'text-amber-300' },
    { label: 'Energy', value: latestReading ? `${latestReading.energy_kw.toFixed(1)} kW` : '—', icon: Power, tone: 'text-violet-300' },
    { label: 'Pressure', value: latestReading ? `${latestReading.pressure.toFixed(1)} bar` : '—', icon: Gauge, tone: 'text-pink-300' },
    { label: 'Airflow', value: latestReading ? `${latestReading.airflow.toFixed(0)}%` : '—', icon: Wind, tone: 'text-sky-300' },
  ];

  const chartSeries = telemetry.map((point) => ({
    ...point,
    label: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }));

  return (
    <div className="space-y-6">
      <header className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">{asset.asset_code}</p>
            <h2 className="mt-2 text-3xl font-semibold text-slate-100">{asset.name}</h2>
          </div>
          <button
            type="button"
            onClick={() => navigate('/x-ray')}
            className="inline-flex items-center justify-center rounded-full border border-cyan-500/60 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-200 transition hover:border-cyan-400 hover:bg-cyan-500/20"
          >
            [ RUN FACILITY X-RAY ]
          </button>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        {metricCards.map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs uppercase tracking-wide">{label}</span>
              <Icon className={tone} size={16} />
            </div>
            <p className="mt-4 text-xl font-semibold text-slate-100">{value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <h3 className="mb-4 text-lg font-semibold text-slate-100">Temperature</h3>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartSeries}>
                  <defs>
                    <linearGradient id="temperature-fill" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#fbbf24" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fill: '#cbd5e1', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#cbd5e1', fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="temperature" stroke="#fbbf24" fill="url(#temperature-fill)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <h3 className="mb-4 text-lg font-semibold text-slate-100">Energy & Airflow</h3>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartSeries}>
                  <defs>
                    <linearGradient id="energy-fill" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1} />
                    </linearGradient>
                    <linearGradient id="airflow-fill" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fill: '#cbd5e1', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#cbd5e1', fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="energy_kw" stroke="#8b5cf6" fill="url(#energy-fill)" strokeWidth={2} />
                  <Area type="monotone" dataKey="airflow" stroke="#38bdf8" fill="url(#airflow-fill)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <aside className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <h3 className="text-lg font-semibold text-slate-100">Asset Metadata</h3>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <div className="flex justify-between"><span>Last Updated</span><span>{latestReading ? new Date(latestReading.timestamp).toLocaleString() : '—'}</span></div>
              <div className="flex justify-between"><span>Building</span><span>{asset.building_id ?? '—'}</span></div>
              <div className="flex justify-between"><span>Floor</span><span>{asset.floor_id ?? '—'}</span></div>
              <div className="flex justify-between"><span>Type</span><span>{asset.asset_type}</span></div>
            </div>
            {asset.status?.toLowerCase() === 'warning' || asset.status?.toLowerCase() === 'critical' ? (
              <button
                type="button"
                onClick={() => navigate('/x-ray')}
                className="mt-4 inline-flex w-full items-center justify-center rounded-xl border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-sm font-medium text-amber-200 transition hover:border-amber-400 hover:bg-amber-500/20"
              >
                [Investigate with X-Ray]
              </button>
            ) : null}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <h3 className="text-lg font-semibold text-slate-100">Relationships</h3>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3"><span className="text-slate-400">SERVES</span><p className="mt-1 text-slate-100">Floor {asset.floor_id ?? '—'}</p></div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3"><span className="text-slate-400">DEPENDS ON</span><p className="mt-1 text-slate-100">CHILLER-002</p></div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3"><span className="text-slate-400">MONITORED BY</span><p className="mt-1 text-slate-100">TEMP-007, ENERGY-007, PRESSURE-007, AIRFLOW-007</p></div>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}

export default AssetDetails;
