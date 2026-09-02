import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowRight, Gauge } from 'lucide-react';
import { getAssets } from '../services/assets';
import type { Asset } from '../types/asset';

function Assets() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const data = await getAssets();
        if (isMounted) {
          setAssets(data);
          setError('');
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unable to load facility data.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Loading facility assets...</div>;
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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-slate-100">FACILITY ASSETS</h2>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs uppercase tracking-wide text-slate-300">
          {assets.length} assets
        </span>
      </div>

      {assets.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">No assets available.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {assets.map((asset) => (
            <Link
              key={asset.id}
              to={`/assets/${asset.id}`}
              className="group rounded-2xl border border-slate-800 bg-slate-900 p-5 transition hover:border-cyan-500/50 hover:bg-slate-800"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-lg font-semibold text-slate-100">{asset.asset_code}</p>
                  <p className="mt-1 text-sm text-slate-400">{asset.name}</p>
                </div>
                <ArrowRight className="text-slate-500 transition group-hover:text-cyan-300" size={18} />
              </div>

              <div className="mt-5 flex items-center justify-between text-sm">
                <span className="rounded-full border border-slate-700 px-2 py-1 text-xs uppercase tracking-wide text-slate-200">
                  {asset.status}
                </span>
                <span className="flex items-center gap-1 text-slate-300">
                  <Gauge size={14} />
                  {asset.health_score}
                </span>
              </div>

              <div className="mt-5 flex items-center gap-2 text-xs text-slate-400">
                <Activity size={12} />
                <span>{asset.asset_type}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default Assets;
