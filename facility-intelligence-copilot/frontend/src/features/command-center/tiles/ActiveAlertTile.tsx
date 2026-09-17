import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowRight } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';

export const ActiveAlertTile: React.FC = () => {
  const navigate = useNavigate();

  return (
    <BentoTile
      span="col-span-1"
      variant="alert"
      onClick={() => navigate('/investigations/inc-701')}
      className="flex flex-col justify-between"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle size={16} className="text-[#F25912]" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[#F25912]">ACTIVE INCIDENT</span>
        </div>
        <span className="rounded-lg bg-[#F25912]/20 px-2 py-0.5 text-[10px] font-bold text-[#F25912] border border-[#F25912]/40">
          HIGH
        </span>
      </div>

      <div className="my-3">
        <h3 className="text-base font-bold text-[var(--text-main)]">AIRFLOW RESTRICTION</h3>
        <p className="mt-1 text-xs text-[var(--text-muted)] font-mono">ASSET: AHU-007 • SUPPLY FAN</p>
        <p className="mt-2 text-xs text-[var(--text-muted)] line-clamp-2">
          Supply airflow dropped 28% below baseline. VFD drive belt slippage detected.
        </p>
      </div>

      <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-2 text-xs text-[#F25912] font-semibold group">
        <span>View Incident Details</span>
        <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
      </div>
    </BentoTile>
  );
};
