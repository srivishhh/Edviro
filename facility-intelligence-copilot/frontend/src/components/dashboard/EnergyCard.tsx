import { Zap } from 'lucide-react';

interface EnergyCardProps {
  wastedKw?: number | string;
  costImpactHour?: string;
  co2PenaltyKg?: string;
}

export function EnergyCard({
  wastedKw = 4.3,
  costImpactHour = '$0.76/hr',
  co2PenaltyKg = '1.6 kg/hr',
}: EnergyCardProps) {
  return (
    <div className="saas-card p-6 md:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-4">
        <div>
          <div className="flex items-center gap-1.5 text-zinc-500 mb-1">
            <Zap size={14} />
            <span className="text-[10px] uppercase font-bold tracking-[0.2em]">Thermodynamic Power Load</span>
          </div>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight">Energy & Efficiency Intelligence</h3>
        </div>
        <span className="text-[11px] px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-mono font-medium">
          HVAC-007 +{wastedKw} kW Overdraw
        </span>
      </div>

      {/* Grid Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 text-xs">
        <div className="p-4 rounded-2xl bg-amber-50/40 border border-amber-200/80 space-y-1">
          <p className="text-amber-800 font-medium">Abnormal Excess Power</p>
          <p className="text-2xl font-extrabold text-amber-700 font-mono">+{wastedKw} kW</p>
          <p className="text-[10px] text-amber-600">Compressor over-torque</p>
        </div>

        <div className="p-4 rounded-2xl bg-zinc-50/60 border border-zinc-200/80 space-y-1">
          <p className="text-zinc-500 font-medium">Hourly Drag Cost</p>
          <p className="text-2xl font-extrabold text-zinc-900 font-mono">{costImpactHour}</p>
          <p className="text-[10px] text-zinc-400">Continuous operation</p>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-50/40 border border-emerald-200/80 space-y-1">
          <p className="text-emerald-800 font-medium">Carbon Footprint Rate</p>
          <p className="text-2xl font-extrabold text-emerald-700 font-mono">{co2PenaltyKg}</p>
          <p className="text-[10px] text-emerald-600">CO2 equivalent rate</p>
        </div>
      </div>
    </div>
  );
}
