import { useEffect, useState } from 'react';
import { Radio, X } from 'lucide-react';
import type { Asset, TelemetryPoint } from '../../types';
import { getAssetTelemetry } from '../../services/telemetry';
import { HealthBadge } from '../ui/SeverityBadge';
import { LoadingState } from '../ui/States';

interface AssetDrawerProps {
  asset: Asset | null;
  onClose: () => void;
}

export function AssetDrawer({ asset, onClose }: AssetDrawerProps) {
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!asset) return;
    setLoading(true);
    getAssetTelemetry(asset.id, { limit: 10 })
      .then((data) => setTelemetry(data))
      .catch(() => setTelemetry([]))
      .finally(() => setLoading(false));
  }, [asset]);

  if (!asset) return null;

  const latest = telemetry[telemetry.length - 1];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-zinc-950/20 backdrop-blur-xs animate-fadeIn">
      <div className="w-full max-w-md bg-white h-full shadow-2xl p-6 md:p-8 flex flex-col justify-between overflow-y-auto space-y-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between border-b border-zinc-100 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-zinc-900 bg-zinc-100 px-2 py-0.5 rounded border border-zinc-200">
                  {asset.asset_code}
                </span>
                <span className="text-[10px] uppercase font-bold text-zinc-400">{asset.asset_type}</span>
              </div>
              <h2 className="text-xl font-bold text-zinc-900">{asset.name}</h2>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-full hover:bg-zinc-100 text-zinc-400 hover:text-zinc-600 transition-colors cursor-pointer"
            >
              <X size={18} />
            </button>
          </div>

          {/* Health & Status */}
          <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-50 border border-zinc-200 text-xs">
            <span className="font-medium text-zinc-600">Equipment Health Index</span>
            <HealthBadge score={asset.health_score} />
          </div>

          {/* Specs Details */}
          <div className="space-y-3 text-xs">
            <h3 className="font-bold text-zinc-900 uppercase tracking-wider text-[10px]">Specifications</h3>
            <div className="space-y-2 font-mono">
              <div className="flex justify-between py-1 border-b border-zinc-100">
                <span className="text-zinc-500">Asset Type:</span>
                <span className="text-zinc-900">{asset.asset_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-100">
                <span className="text-zinc-500">Operating Status:</span>
                <span className="text-zinc-900 uppercase">{asset.status}</span>
              </div>
            </div>
          </div>

          {/* Live Telemetry Snapshot */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-zinc-900 uppercase tracking-wider text-[10px]">Live Telemetry</h3>
              <span className="text-[10px] font-mono text-zinc-400 flex items-center gap-1">
                <Radio size={10} className="text-emerald-500 animate-pulse" /> Live Stream
              </span>
            </div>

            {loading ? (
              <LoadingState message="Fetching live telemetry..." />
            ) : latest ? (
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-xl bg-zinc-50 border border-zinc-200">
                  <span className="text-[10px] text-zinc-400 block">Temperature</span>
                  <span className="text-base font-bold text-zinc-900">{latest.temperature}°C</span>
                </div>
                <div className="p-3 rounded-xl bg-zinc-50 border border-zinc-200">
                  <span className="text-[10px] text-zinc-400 block">Power Demand</span>
                  <span className="text-base font-bold text-zinc-900">{latest.energy_kw} kW</span>
                </div>
                <div className="p-3 rounded-xl bg-zinc-50 border border-zinc-200">
                  <span className="text-[10px] text-zinc-400 block">Head Pressure</span>
                  <span className="text-base font-bold text-zinc-900">{latest.pressure} bar</span>
                </div>
                <div className="p-3 rounded-xl bg-zinc-50 border border-zinc-200">
                  <span className="text-[10px] text-zinc-400 block">Airflow Flow Rate</span>
                  <span className="text-base font-bold text-zinc-900">{latest.airflow}%</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-zinc-400 font-mono">No telemetry events logged.</p>
            )}
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2.5 rounded-full bg-zinc-950 text-white text-xs font-semibold hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
}
