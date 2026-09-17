import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ArrowRight, FileCheck } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime } from '../../../hooks/useRealtime';

interface FacilityXRayTileProps {
  onOpenResult?: () => void;
}

export const FacilityXRayTile: React.FC<FacilityXRayTileProps> = ({ onOpenResult }) => {
  const navigate = useNavigate();
  const { snsState } = useRealtime();

  return (
    <BentoTile
      span="col-span-1 md:col-span-2"
      variant="gradient"
      className="flex flex-col justify-between"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-[#5C3E94] dark:text-purple-300" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[#5C3E94] dark:text-purple-300">
            FACILITY X-RAY DIAGNOSIS
          </span>
          <span className="rounded-md bg-emerald-500/15 border border-emerald-500/30 px-1.5 py-0.5 text-[9px] font-bold text-emerald-600 dark:text-emerald-400">
            SNS INGESTED
          </span>
        </div>
        <span className="rounded-lg bg-[#5C3E94]/15 px-2 py-0.5 text-xs font-mono font-medium text-[#5C3E94] dark:text-purple-300 border border-[#5C3E94]/30">
          {snsState.asset_id} • {snsState.alert_type}
        </span>
      </div>

      <div className="my-2.5 space-y-2.5">
        {/* Overall Combined Result Banner */}
        <div className="rounded-xl border border-[#5C3E94]/25 bg-[var(--bg-surface)] p-3 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#F25912]">
              OVERALL COMBINED RESULT (SNS + FACILITY X-RAY)
            </span>
            <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-bold">98.4% Confidence</span>
          </div>
          <p className="text-xs font-bold text-[var(--text-main)] leading-snug">
            {snsState.diagnosis}
          </p>
          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
            <span className="text-[#5C3E94] dark:text-purple-300 font-semibold">Physics Cross-Check:</span> Mass-energy balance confirms 28% drop in supply CFM with elevated static head loss.
          </p>
        </div>

        {/* Prescription Protocol */}
        <div className="text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block mb-0.5">
            Prescription & Next Steps
          </span>
          <p className="text-xs text-[var(--text-muted)] line-clamp-1">{snsState.prescription}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--border-subtle)] pt-2.5 text-xs font-semibold">
        <button
          type="button"
          onClick={onOpenResult}
          className="flex items-center gap-1.5 rounded-xl border border-[#5C3E94]/40 bg-[#5C3E94]/10 hover:bg-[#5C3E94]/20 px-2.5 py-1.5 text-xs font-bold text-[#5C3E94] dark:text-purple-300 transition-all active:scale-95"
        >
          <FileCheck size={13} className="text-emerald-500" />
          <span>View Detailed Proof</span>
        </button>

        <button
          type="button"
          onClick={() => navigate('/investigations/inc-701')}
          className="flex items-center gap-1 text-[#5C3E94] dark:text-purple-300 hover:underline group"
        >
          <span>Open Full Investigation</span>
          <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
        </button>
      </div>
    </BentoTile>
  );
};
