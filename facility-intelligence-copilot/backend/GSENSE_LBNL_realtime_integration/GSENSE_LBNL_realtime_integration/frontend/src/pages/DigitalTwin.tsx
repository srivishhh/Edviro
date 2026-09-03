import { useEffect, useMemo, useState } from 'react';
import { Building2, ChevronRight, Activity, Gauge, Thermometer, Power, Wind } from 'lucide-react';
import { getTwinAssets } from '../services/twin';
import type { TwinAsset } from '../types/twin';

function DigitalTwin() {
  const [assets, setAssets] = useState<TwinAsset[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const data = await getTwinAssets();
        if (isMounted) {
          setAssets(data);
          setSelectedId((current) => current ?? data[0]?.asset_id ?? null);
          setError('');
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unable to load digital twin state.');
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

  const selectedAsset = useMemo(
    () => assets.find((asset) => asset.asset_id === selectedId) ?? assets[0] ?? null,
    [assets, selectedId],
  );

  if (loading) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Loading digital twin...</div>;
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-8 text-red-200">
        <p className="font-semibold">Unable to load digital twin state.</p>
        <p className="mt-2 text-sm text-red-100/80">Check that the FastAPI backend is running.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
        <div className="flex items-center gap-3 text-cyan-300">
          <Building2 size={18} />
          <p className="text-sm uppercase tracking-[0.2em]">BUILDING A</p>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {[
            { title: 'Floor 1', items: assets.filter((asset) => asset.asset_id === 1) },
            { title: 'Floor 2', items: assets.filter((asset) => asset.asset_id === 7 || asset.asset_id === 9) },
            { title: 'Floor 3', items: assets.filter((asset) => asset.asset_id === 8) },
          ].map((floor) => (
            <div key={floor.title} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-300">{floor.title}</p>
              <div className="space-y-2">
                {floor.items.length === 0 ? (
                  <p className="text-sm text-slate-500">No assets</p>
                ) : (
                  floor.items.map((asset) => (
                    <button
                      key={asset.asset_id}
                      type="button"
                      onClick={() => setSelectedId(asset.asset_id)}
                      className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition ${
                        selectedAsset?.asset_id === asset.asset_id
                          ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-100'
                          : 'border-slate-700 bg-slate-900 text-slate-200 hover:border-slate-600'
                      }`}
                    >
                      <span>{`HVAC-${asset.asset_id}`}</span>
                      <ChevronRight size={14} />
                    </button>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedAsset ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Digital Twin</p>
              <h3 className="mt-2 text-3xl font-semibold text-slate-100">HVAC-{selectedAsset.asset_id}</h3>
            </div>
            <span className="rounded-full border border-slate-700 px-3 py-1 text-xs uppercase tracking-wide text-slate-200">
              {selectedAsset.status}
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              { label: 'Health', value: `${selectedAsset.health_score}`, icon: Activity },
              { label: 'Temperature', value: `${selectedAsset.current_state.temperature.toFixed(1)}°C`, icon: Thermometer },
              { label: 'Energy', value: `${selectedAsset.current_state.energy_kw.toFixed(1)} kW`, icon: Power },
              { label: 'Pressure', value: `${selectedAsset.current_state.pressure.toFixed(1)} bar`, icon: Gauge },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-xs uppercase tracking-wide">{label}</span>
                  <Icon size={16} className="text-cyan-300" />
                </div>
                <p className="mt-4 text-2xl font-semibold text-slate-100">{value}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="mb-3 flex items-center gap-2 text-cyan-300">
                <Wind size={16} />
                <span className="text-sm uppercase tracking-wide">Airflow</span>
              </div>
              <p className="text-2xl font-semibold text-slate-100">{selectedAsset.current_state.airflow.toFixed(0)}%</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="mb-3 flex items-center gap-2 text-cyan-300">
                <Gauge size={16} />
                <span className="text-sm uppercase tracking-wide">Last Updated</span>
              </div>
              <p className="text-base font-medium text-slate-100">{new Date(selectedAsset.last_updated).toLocaleString()}</p>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <h4 className="text-lg font-semibold text-slate-100">RELATIONSHIPS</h4>
            <div className="mt-4 space-y-3">
              {selectedAsset.relationships.map((relationship) => (
                <div key={`${relationship.type}-${relationship.target}`} className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200">
                  <span className="min-w-28 text-xs uppercase tracking-wide text-slate-400">{relationship.type}</span>
                  <ChevronRight size={14} className="text-slate-500" />
                  <span>{relationship.target}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default DigitalTwin;
