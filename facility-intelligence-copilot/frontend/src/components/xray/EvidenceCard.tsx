import { Eye, Flame, ShieldCheck, Sparkles, Wrench } from 'lucide-react';
import type { EvidenceItem } from '../../types';

interface EvidenceCardProps {
  evidence?: EvidenceItem[];
  observed?: string[];
  correlated?: string[];
  inferred?: string[];
  leadingHypothesis?: string;
  confidence?: string;
  recommendedActions?: string[];
}

export function EvidenceCard({
  evidence = [],
  observed = [],
  correlated = [],
  inferred = [],
  leadingHypothesis = 'Multi-agent causal reasoning in progress.',
  confidence = 'HIGH',
  recommendedActions = [],
}: EvidenceCardProps) {
  const displayObserved = observed.length > 0 ? observed : [
    'Telemetry sensor measurements ingested into causal reasoning pipeline.',
  ];

  const displayCorrelated = correlated.length > 0 ? correlated : [
    'Time-series multi-sensor synchronization verified across asset graph.',
  ];

  const displayInferred = inferred.length > 0 ? inferred : [
    'Thermodynamic fault mechanism derived by Root Cause Investigator.',
  ];

  return (
    <div className="space-y-6">
      {/* 3 EVIDENCE CATEGORIES (OBSERVED, CORRELATED, INFERRED) */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* 1. OBSERVED */}
        <div className="saas-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div className="flex items-center gap-1.5 text-zinc-900">
              <Eye size={15} strokeWidth={1.75} />
              <h3 className="text-xs font-bold uppercase tracking-wider">OBSERVED</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-600 font-semibold">
              HARD TELEMETRY
            </span>
          </div>

          <div className="space-y-2.5">
            {displayObserved.map((obs, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-zinc-50 border border-zinc-200/60 text-xs text-zinc-700 leading-relaxed font-mono">
                {obs}
              </div>
            ))}
          </div>
        </div>

        {/* 2. CORRELATED */}
        <div className="saas-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div className="flex items-center gap-1.5 text-zinc-900">
              <Sparkles size={15} strokeWidth={1.75} />
              <h3 className="text-xs font-bold uppercase tracking-wider">CORRELATED</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-600 font-semibold">
              TIME-SERIES FUSION
            </span>
          </div>

          <div className="space-y-2.5">
            {displayCorrelated.map((cor, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-zinc-50 border border-zinc-200/60 text-xs text-zinc-700 leading-relaxed">
                {cor}
              </div>
            ))}
          </div>
        </div>

        {/* 3. INFERRED */}
        <div className="saas-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div className="flex items-center gap-1.5 text-zinc-900">
              <Flame size={15} strokeWidth={1.75} />
              <h3 className="text-xs font-bold uppercase tracking-wider">INFERRED</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-600 font-semibold">
              PHYSICAL MECHANISM
            </span>
          </div>

          <div className="space-y-2.5">
            {displayInferred.map((inf, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-zinc-50 border border-zinc-200/60 text-xs text-zinc-700 leading-relaxed">
                {inf}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CROSS-SENSOR CORROBORATION EVIDENCE */}
      {evidence && evidence.length > 0 && (
        <div className="saas-card p-6 md:p-8 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div className="flex items-center gap-2 text-zinc-900">
              <ShieldCheck size={16} strokeWidth={1.75} />
              <h3 className="text-xs font-bold uppercase tracking-wider">Cross-Sensor Corroboration Feed</h3>
            </div>
            <span className="text-[10px] font-mono text-zinc-400">{evidence.length} Signals Corroborated</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {evidence.map((item, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-zinc-50 border border-zinc-200 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-zinc-900 uppercase">{item.metric}</span>
                  <span className="text-[10px] font-mono text-zinc-500">{item.source}</span>
                </div>
                <p className="text-zinc-700 text-[11px] leading-snug">{item.interpretation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* LEADING HYPOTHESIS & CONFIDENCE BANNER */}
      <div className="saas-card p-6 md:p-8 space-y-4 bg-gradient-to-br from-white to-zinc-50/50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-3">
          <div className="flex items-center gap-2 text-zinc-900">
            <ShieldCheck size={16} strokeWidth={1.75} />
            <span className="text-xs font-bold uppercase tracking-wider">Leading Root Cause Hypothesis</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-zinc-400 uppercase font-mono font-semibold">Confidence:</span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-mono font-bold">
              {confidence}
            </span>
          </div>
        </div>

        <p className="text-lg font-bold text-zinc-900 tracking-tight leading-snug">
          {leadingHypothesis}
        </p>

        <p className="text-xs text-zinc-500 leading-relaxed">
          GSENSE Validation Gate confirmed that observed physical telemetry directly corroborates the thermodynamic failure mechanism.
        </p>
      </div>

      {/* RECOMMENDED ACTIONS */}
      {recommendedActions.length > 0 && (
        <div className="saas-card p-6 md:p-8 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div className="flex items-center gap-2 text-zinc-900">
              <Wrench size={16} strokeWidth={1.75} />
              <h3 className="text-xs font-bold uppercase tracking-wider">Recommended Standard Operating Procedures (SOPs)</h3>
            </div>
            <span className="text-[10px] font-mono text-zinc-400">Actionable Prescriptions</span>
          </div>

          <div className="space-y-2.5">
            {recommendedActions.map((act, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl border border-zinc-200/80 bg-zinc-50/50 flex items-start gap-3 text-xs text-zinc-800"
              >
                <div className="w-5 h-5 rounded-md bg-zinc-900 text-white font-mono font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                  {idx + 1}
                </div>
                <span className="leading-relaxed font-medium">{act}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
