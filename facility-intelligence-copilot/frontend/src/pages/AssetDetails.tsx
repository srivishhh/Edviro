import { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, SlidersHorizontal } from 'lucide-react';
import { getAsset } from '../services/assets';
import { getAssetTelemetry } from '../services/telemetry';
import type { Asset, TelemetryPoint } from '../types';
import { HealthBadge } from '../components/ui/SeverityBadge';
import { StatusIndicator } from '../components/ui/StatusIndicator';
import { LoadingState, ErrorState } from '../components/ui/States';

export default function AssetDetails() {
  const { assetId } = useParams();
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
    const interval = setInterval(load, 2500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [assetId]);

  const latestReading = useMemo(() => telemetry[telemetry.length - 1], [telemetry]);

  if (loading) {
    return <LoadingState message="Loading asset telemetry stream..." />;
  }

  if (error || !asset) {
    return (
      <div className="space-y-4">
        <Link to="/assets" className="inline-flex items-center gap-2 text-xs font-semibold text-zinc-500 hover:text-zinc-900">
          <ArrowLeft size={14} /> Back to Assets
        </Link>
        <ErrorState message={error || 'Asset not found.'} />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="space-y-4">
        <Link to="/assets" className="inline-flex items-center gap-2 text-xs font-semibold text-zinc-500 hover:text-zinc-900 transition-colors">
          <ArrowLeft size={14} /> Back to Asset Registry
        </Link>

        <div className="saas-card p-6 md:p-8 space-y-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-zinc-900 bg-zinc-100 px-2.5 py-1 rounded-md border border-zinc-200">
                {asset.asset_code}
              </span>
              <span className="text-xs uppercase font-bold text-zinc-400 font-mono">{asset.asset_type}</span>
            </div>
            <h1 className="text-3xl font-extrabold text-zinc-950 editorial-title tracking-tight">{asset.name}</h1>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to={`/what-if?assetId=${asset.asset_code}`}
              className="px-3.5 py-1.5 rounded-full bg-zinc-950 hover:bg-zinc-800 text-white text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-colors shadow-2xs"
            >
              <SlidersHorizontal size={13} />
              <span>Simulate</span>
            </Link>
            <HealthBadge score={asset.health_score} />
            <StatusIndicator status={asset.status} />
          </div>
        </div>
      </div>

      {/* Live Metric Cards */}
      {latestReading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 font-mono">
          <div className="saas-card p-5 space-y-1">
            <span className="text-[10px] text-zinc-400 uppercase font-bold block">Discharge Pressure</span>
            <p className="text-2xl font-extrabold text-zinc-900">{latestReading.pressure.toFixed(1)} bar</p>
          </div>
          <div className="saas-card p-5 space-y-1">
            <span className="text-[10px] text-zinc-400 uppercase font-bold block">Supply Temperature</span>
            <p className="text-2xl font-extrabold text-zinc-900">{latestReading.temperature.toFixed(1)}°C</p>
          </div>
          <div className="saas-card p-5 space-y-1">
            <span className="text-[10px] text-zinc-400 uppercase font-bold block">Power Demand</span>
            <p className="text-2xl font-extrabold text-amber-700">{latestReading.energy_kw.toFixed(1)} kW</p>
          </div>
          <div className="saas-card p-5 space-y-1">
            <span className="text-[10px] text-zinc-400 uppercase font-bold block">Airflow Volumetric Flow</span>
            <p className="text-2xl font-extrabold text-zinc-900">{latestReading.airflow.toFixed(1)}%</p>
          </div>
        </div>
      )}
    </div>
  );
}
