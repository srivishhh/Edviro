import React from 'react';
import { HeartPulse } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime } from '../../../hooks/useRealtime';

export const FacilityHealthTile: React.FC = () => {
  const { healthScore, facilityStatus } = useRealtime();

  return (
    <BentoTile span="col-span-1" variant="translucent" className="flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <HeartPulse size={16} className="text-[#F25912]" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">FACILITY HEALTH</span>
        </div>
        <span className="text-xs text-[var(--text-muted)] font-mono font-medium">TWIN INDEX</span>
      </div>

      <div className="my-3 flex items-center justify-between">
        <div>
          <div className="text-4xl font-extrabold tracking-tight text-[var(--text-main)] font-mono">{healthScore}%</div>
          <p className="mt-1 text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
            Status: <span className={facilityStatus === 'NORMAL' ? 'text-emerald-500 font-bold' : 'text-[#F25912] font-bold'}>{facilityStatus}</span>
          </p>
        </div>

        {/* Health Radial Meter */}
        <div className="relative flex h-16 w-16 items-center justify-center rounded-full border border-[var(--border-subtle)] bg-[var(--bg-surface)] shadow-inner">
          <svg className="h-full w-full -rotate-90 p-1" viewBox="0 0 36 36">
            <path
              className="text-[var(--border-subtle)]"
              strokeWidth="3.5"
              stroke="currentColor"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className={healthScore > 80 ? 'text-emerald-500' : 'text-[#F25912]'}
              strokeDasharray={`${healthScore}, 100`}
              strokeWidth="3.5"
              strokeLinecap="round"
              stroke="currentColor"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
        </div>
      </div>

      <div className="text-[11px] text-[var(--text-muted)] border-t border-[var(--border-subtle)] pt-2 font-mono">
        Digital Twin model verified
      </div>
    </BentoTile>
  );
};
