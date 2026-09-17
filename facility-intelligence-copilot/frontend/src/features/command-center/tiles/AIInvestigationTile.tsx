import React, { useState } from 'react';
import { Bot, Send, Loader2, CheckCircle2, Zap } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime } from '../../../hooks/useRealtime';

interface AIInvestigationTileProps {
  onOpenResult?: () => void;
}

export const AIInvestigationTile: React.FC<AIInvestigationTileProps> = ({ onOpenResult }) => {
  const { snsState, dispatchSNS } = useRealtime();
  const [localAnalyzing, setLocalAnalyzing] = useState(false);
  const [agentStep, setAgentStep] = useState(0);

  const steps = [
    'Triager Agent: Validating Telemetry',
    'Metric Analyst: Correlating Flow Drop',
    'Root Cause: Isolating VFD Transmission',
    'Prescriptive: Remediation Generated',
  ];

  const handleTriggerDispatch = async (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setLocalAnalyzing(true);
    setAgentStep(0);

    const stepInterval = setInterval(() => {
      setAgentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 400);

    try {
      await dispatchSNS('AHU-007', '101');
    } finally {
      setTimeout(() => {
        clearInterval(stepInterval);
        setLocalAnalyzing(false);
      }, 1600);
    }
  };

  const isRunning = localAnalyzing || snsState.status === 'DISPATCHING';

  return (
    <BentoTile span="col-span-1" variant="translucent" className="flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot size={16} className="text-[#5C3E94] dark:text-purple-300" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">SNS WORKBENCH</span>
        </div>
        <span
          className={`rounded-lg px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
            isRunning
              ? 'bg-[#F25912]/20 text-[#F25912] border border-[#F25912]/40 animate-pulse'
              : 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
          }`}
        >
          {isRunning ? 'EXECUTING' : 'COMPLETED'}
        </span>
      </div>

      <div className="my-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Zap size={13} className="text-[#F25912]" />
            <span className="text-sm font-bold text-[var(--text-main)]">10 Autonomous Agents</span>
          </div>
          <span className="rounded-md bg-[#5C3E94]/15 px-2 py-0.5 text-[10px] font-mono text-[#5C3E94] dark:text-purple-300 font-semibold border border-[#5C3E94]/30">
            {snsState.asset_id}
          </span>
        </div>

        {isRunning ? (
          <div className="mt-2.5 rounded-xl bg-[var(--bg-surface)] p-2.5 border border-[var(--border-subtle)] text-[11px] space-y-1">
            <div className="flex items-center gap-2 text-[#F25912] font-semibold">
              <Loader2 size={12} className="animate-spin" />
              <span>{steps[agentStep]}</span>
            </div>
            <div className="h-1 w-full bg-[var(--bg-primary)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#F25912] transition-all duration-300"
                style={{ width: `${((agentStep + 1) / steps.length) * 100}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="mt-2 text-xs text-[var(--text-muted)] leading-relaxed">
            <p className="line-clamp-2">
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">✓ Multi-Agent Graph Verified:</span> {snsState.diagnosis}
            </p>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--border-subtle)] pt-2.5">
        {/* Result Button to show what SNS workbench has done */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onOpenResult?.();
          }}
          className="flex items-center gap-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/15 hover:bg-emerald-500/25 px-2.5 py-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-300 shadow-sm transition-all active:scale-95"
          title="View SNS Workbench Multi-Agent Result"
        >
          <CheckCircle2 size={13} className="text-emerald-500" />
          <span>Result</span>
        </button>

        {/* Trigger Dispatch */}
        <button
          type="button"
          onClick={handleTriggerDispatch}
          disabled={isRunning}
          className="flex items-center gap-1.5 rounded-xl border border-[#5C3E94] bg-[#5C3E94] px-3 py-1.5 text-xs font-bold text-white shadow-sm transition-all hover:bg-[#412B6B] active:scale-95 disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 size={13} className="animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Send size={13} />
              <span>Run SNS Agent</span>
            </>
          )}
        </button>
      </div>
    </BentoTile>
  );
};
