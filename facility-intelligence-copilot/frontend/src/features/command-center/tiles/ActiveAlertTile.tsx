import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowRight } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';

import { useRealtime } from '../../../hooks/useRealtime';

export const ActiveAlertTile: React.FC = () => {
  const navigate = useNavigate();
  const { snsState, facilityStatus } = useRealtime();

  const isNominal = snsState.alert_type === 'NOMINAL_OPERATION' || facilityStatus === 'NORMAL';
  const alertTitle = isNominal ? 'SYSTEM NOMINAL' : snsState.alert_type.replace(/_/g, ' ');
  const severityBadge = isNominal ? 'NOMINAL' : 'HIGH';

  return (
    <BentoTile
      span="col-span-1"
      variant="alert"
      onClick={() => navigate('/investigations/inc-701')}
      className="flex flex-col justify-between"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle size={16} className={isNominal ? 'text-emerald-500' : 'text-[#F25912]'} />
          <span className={`text-xs font-semibold uppercase tracking-wider ${isNominal ? 'text-emerald-600 dark:text-emerald-400' : 'text-[#F25912]'}`}>
            {isNominal ? 'FACILITY STATUS' : 'ACTIVE INCIDENT'}
          </span>
        </div>
        <span className={`rounded-lg px-2 py-0.5 text-[10px] font-bold ${
          isNominal
            ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
            : 'bg-[#F25912]/20 text-[#F25912] border border-[#F25912]/40'
        }`}>
          {severityBadge}
        </span>
      </div>

      <div className="my-3">
        <h3 className="text-base font-bold text-[var(--text-main)] truncate">{alertTitle}</h3>
        <p className="mt-1 text-xs text-[var(--text-muted)] font-mono">ASSET: AHU-007 • LBNL DATASET</p>
        <p className="mt-2 text-xs text-[var(--text-muted)] line-clamp-2">
          {snsState.diagnosis || 'All AHU-007 parameters operate within optimal ASHRAE 90.1 baselines.'}
        </p>
      </div>

      <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-2 text-xs text-[#F25912] font-semibold group">
        <span>View Incident Details</span>
        <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
      </div>
    </BentoTile>
  );
};
