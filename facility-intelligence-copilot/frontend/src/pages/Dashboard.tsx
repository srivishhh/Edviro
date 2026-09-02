import { AlertTriangle, Building2, Gauge, HeartPulse, Zap } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { getAssets } from '../services/assets';
import type { Asset } from '../types/asset';

function Dashboard() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      try {
        const data = await getAssets();
        if (isActive) {
          setAssets(data);
          setError('');
        }
      } catch (err) {
        if (isActive) {
          setError(err instanceof Error ? err.message : 'Unable to load facility data.');
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      isActive = false;
    };
  }, []);

  const summary = useMemo(() => {
    const total = assets.length;
    const healthy = assets.filter((asset) => asset.status?.toLowerCase() === 'healthy').length;
    const warning = assets.filter((asset) => asset.status?.toLowerCase() === 'warning').length;
    const critical = assets.filter((asset) => asset.status?.toLowerCase() === 'critical').length;
    const avgHealth = total > 0 ? Math.round(assets.reduce((sum, asset) => sum + (asset.health_score ?? 0), 0) / total) : 0;

    return { total, healthy, warning, critical, avgHealth };
  }, [assets]);

  if (loading) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Loading facility overview...</div>;
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-8 text-red-200">
        <p className="font-semibold">Unable to load facility data.</p>
        <p className="mt-2 text-sm text-red-100/80">Check that the FastAPI backend is running.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        {[
          { label: 'Total Assets', value: summary.total, icon: Building2, accent: 'text-cyan-300' },
          { label: 'Healthy', value: summary.healthy, icon: HeartPulse, accent: 'text-emerald-300' },
          { label: 'Warning', value: summary.warning, icon: AlertTriangle, accent: 'text-amber-300' },
          { label: 'Critical', value: summary.critical, icon: Zap, accent: 'text-red-300' },
        ].map(({ label, value, icon: Icon, accent }) => (
          <div key={label} className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">{label}</p>
              <Icon className={accent} size={18} />
            </div>
            <p className="mt-4 text-3xl font-semibold text-slate-100">{value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-100">Recent Assets</h2>
            <span className="rounded-full border border-slate-700 px-2 py-1 text-xs text-slate-300">Live inventory</span>
          </div>

          {assets.length === 0 ? (
            <p className="text-slate-400">No facility assets found.</p>
          ) : (
            <div className="space-y-3">
              {assets.slice(0, 6).map((asset) => (
                <div key={asset.id} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                  <div>
                    <p className="font-medium text-slate-100">{asset.name}</p>
                    <p className="text-xs text-slate-400">{asset.asset_code} • {asset.asset_type}</p>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-300">
                    <span className="rounded-full bg-slate-800 px-2 py-1 text-xs uppercase tracking-wide text-slate-200">
                      {asset.status}
                    </span>
                    <span className="flex items-center gap-1">
                      <Gauge size={14} />
                      {asset.health_score}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="text-xl font-semibold text-slate-100">Asset Health</h2>
          <div className="mt-6 space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between text-sm text-slate-300">
                <span>Average health</span>
                <span>{summary.avgHealth}%</span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                  style={{ width: `${Math.min(summary.avgHealth, 100)}%` }}
                />
              </div>
            </div>

            <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/10 p-3">
              <p className="text-sm text-cyan-200">Current energy load</p>
              <p className="mt-2 text-2xl font-semibold text-slate-100">
                {assets.length > 0 ? `${Math.round(assets.reduce((sum, asset) => sum + (asset.health_score ?? 0), 0) / assets.length)}%` : '0%'}
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
