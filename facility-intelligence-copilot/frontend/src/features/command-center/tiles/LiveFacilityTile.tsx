import React from 'react';
import { Building2, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime } from '../../../hooks/useRealtime';

export const LiveFacilityTile: React.FC = () => {
  const { facilityStatus, currentTelemetry } = useRealtime();

  const getStatusColor = () => {
    if (facilityStatus === 'CRITICAL') return 'text-red-500 bg-red-500/10 border-red-500/30';
    if (facilityStatus === 'DEGRADED') return 'text-amber-500 bg-amber-500/10 border-amber-500/30';
    return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30';
  };

  return (
    <BentoTile span="col-span-1" variant="gradient" className="flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Building2 size={16} className="text-[#5C3E94] dark:text-purple-300" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">FACILITY STATE</span>
        </div>
        <span className="text-xs text-[var(--text-muted)] font-mono font-medium">AHU-007</span>
      </div>

      <div className="my-3">
        <div className={`inline-flex items-center gap-2 rounded-xl border px-3.5 py-1.5 font-semibold text-base ${getStatusColor()}`}>
          {facilityStatus === 'NORMAL' ? <CheckCircle2 size={17} /> : <AlertTriangle size={17} />}
          <span>{facilityStatus}</span>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-[var(--text-muted)]">
          <div>
            <span>Active Assets</span>
            <p className="text-sm font-semibold text-[var(--text-main)]">6 Monitored</p>
          </div>
          <div>
            <span>Active Alerts</span>
            <p className="text-sm font-semibold text-[#F25912]">1 Diagnostic</p>
          </div>
        </div>
      </div>

      <div className="text-[11px] font-mono text-[var(--text-muted)] border-t border-[var(--border-subtle)] pt-2">
        Sync: {currentTelemetry?.timestamp ? new Date(currentTelemetry.timestamp).toLocaleTimeString() : 'LIVE STREAM'}
      </div>
    </BentoTile>
  );
};
