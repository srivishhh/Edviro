import { useEffect, useState } from 'react';
import { Building2, ChevronRight, Filter, Search } from 'lucide-react';
import { getAssets } from '../services/assets';
import type { Asset } from '../types';
import { HealthBadge } from '../components/ui/SeverityBadge';
import { StatusIndicator } from '../components/ui/StatusIndicator';
import { EmptyState, ErrorState, LoadingState } from '../components/ui/States';
import { AssetDrawer } from '../components/assets/AssetDrawer';

export default function Assets() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

  const load = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const data = await getAssets();
      setAssets(data);
      setError('');
    } catch (err) {
      if (!silent) setError(err instanceof Error ? err.message : 'Unable to load facility assets.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    const interval = setInterval(() => void load(true), 4000);
    return () => clearInterval(interval);
  }, []);

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch =
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.asset_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.asset_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'ALL' || asset.asset_type.toUpperCase().includes(selectedType);
    return matchesSearch && matchesType;
  });

  const assetTypes = ['ALL', ...Array.from(new Set(assets.map((a) => a.asset_type.toUpperCase())))];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="saas-card p-6 md:p-8 space-y-3 bg-white">
        <div className="flex items-center gap-2 text-zinc-500">
          <Building2 size={16} />
          <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Equipment Registry</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-950 editorial-title tracking-tight">
          Facility Assets
        </h1>
        <p className="text-zinc-600 text-xs sm:text-sm max-w-2xl leading-relaxed">
          Comprehensive inventory of monitored mechanical, electrical, and thermal infrastructure assets across the facility.
        </p>
      </div>

      {/* Filter and Search Controls */}
      <div className="saas-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 text-zinc-400" size={13} />
          <input
            type="text"
            placeholder="Search code, name, type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-zinc-50 border border-zinc-200 rounded-full pl-8 pr-3 py-1.5 text-xs text-zinc-800 placeholder-zinc-400 focus:outline-none focus:border-zinc-400"
          />
        </div>

        {/* Type Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          <Filter size={13} className="text-zinc-400 shrink-0" />
          {assetTypes.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all shrink-0 cursor-pointer ${
                selectedType === type
                  ? 'bg-zinc-900 text-white font-semibold'
                  : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Assets Table Card */}
      <div className="saas-card overflow-hidden bg-white">
        {loading ? (
          <LoadingState message="Loading facility asset registry..." />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void load()} />
        ) : filteredAssets.length === 0 ? (
          <EmptyState message="No equipment matching query criteria." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-zinc-100 bg-zinc-50/70 text-zinc-400 font-mono uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-6">Asset Code</th>
                  <th className="py-3 px-6">Equipment Name</th>
                  <th className="py-3 px-6">Category</th>
                  <th className="py-3 px-6">Operating Status</th>
                  <th className="py-3 px-6">Health Index</th>
                  <th className="py-3 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {filteredAssets.map((asset) => (
                  <tr
                    key={asset.id}
                    onClick={() => setSelectedAsset(asset)}
                    className="hover:bg-zinc-50/80 transition-colors cursor-pointer group"
                  >
                    <td className="py-4 px-6 font-mono font-bold text-zinc-900">
                      {asset.asset_code}
                    </td>
                    <td className="py-4 px-6 font-semibold text-zinc-800">
                      {asset.name}
                    </td>
                    <td className="py-4 px-6 text-zinc-500 font-mono text-[11px]">
                      {asset.asset_type}
                    </td>
                    <td className="py-4 px-6">
                      <StatusIndicator status={asset.status} />
                    </td>
                    <td className="py-4 px-6">
                      <HealthBadge score={asset.health_score} />
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="inline-flex items-center gap-1 text-zinc-400 group-hover:text-zinc-900 transition-colors font-medium">
                        <span>Inspect</span>
                        <ChevronRight size={13} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Slide-out Drawer */}
      <AssetDrawer asset={selectedAsset} onClose={() => setSelectedAsset(null)} />
    </div>
  );
}
