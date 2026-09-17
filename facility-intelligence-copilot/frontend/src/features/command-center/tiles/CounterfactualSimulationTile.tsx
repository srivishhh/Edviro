import React, { useState, useEffect } from 'react';
import { GlassCard } from '../../../components/GlassCard';
import {
  counterfactualService,
} from '../../../services/counterfactualService';
import type {
  ActiveIncidentResponse,
  CounterfactualCandidate,
} from '../../../services/counterfactualService';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldCheck,
  Sparkles,
  RefreshCw,
} from 'lucide-react';

interface Props {
  onOpenDetails?: (candidate: CounterfactualCandidate) => void;
}

export const CounterfactualSimulationTile: React.FC<Props> = () => {
  const [data, setData] = useState<ActiveIncidentResponse | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CounterfactualCandidate | null>(null);
  const [isActuating, setIsActuating] = useState(false);
  const [actuationSuccess, setActuationSuccess] = useState(false);

  const fetchIncidentData = async () => {
    try {
      const res = await counterfactualService.getActiveIncident();
      setData(res);
      if (res.counterfactual_solution?.winning_candidate) {
        setSelectedCandidate(res.counterfactual_solution.winning_candidate);
      } else if (res.counterfactual_solution?.all_candidates?.length > 0) {
        setSelectedCandidate(res.counterfactual_solution.all_candidates[0]);
      }
    } catch (e) {
      console.error('Error fetching counterfactual incident:', e);
    }
  };

  useEffect(() => {
    fetchIncidentData();
    const interval = setInterval(fetchIncidentData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleActuate = async (cand: CounterfactualCandidate) => {
    if (cand.status !== 'VALIDATED') return;
    setIsActuating(true);
    try {
      await counterfactualService.applyActuation({
        candidate_id: cand.candidate_id,
        interventions: cand.proposed_interventions,
        asset_id: data?.asset_id || 'AHU-007',
        notes: `Technician approved: ${cand.title}`,
      });
      setActuationSuccess(true);
      setTimeout(() => {
        setActuationSuccess(false);
        fetchIncidentData();
      }, 3000);
    } catch (e) {
      console.error('Failed to actuate:', e);
    } finally {
      setIsActuating(false);
    }
  };

  const solution = data?.counterfactual_solution;
  const candidates = solution?.all_candidates || [];

  return (
    <GlassCard className="col-span-1 md:col-span-2 lg:col-span-4 p-6 relative overflow-hidden bg-black/40 border border-white/10 rounded-2xl">
      {/* Background ambient lighting */}
      <div className="absolute -right-20 -top-20 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -left-20 -bottom-20 w-80 h-80 bg-[#F25912]/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-white tracking-wide">
                GSENSE 3.0 Counterfactual Intelligence & Virtual Twin
              </h2>
              <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/30">
                Active ML Simulation
              </span>
            </div>
            <p className="text-xs text-white/50">
              Deterministic constraint validation & predictive thermodynamic state evaluation for AHU-007
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-white/5 rounded-lg border border-white/10 font-mono text-white/80">
            <span>Root Cause:</span>
            <span className="text-[#F25912] font-semibold uppercase">
              {data?.fault_diagnosis?.replace(/_/g, ' ') || 'NOMINAL'}
            </span>
            <span className="text-white/40">({((data?.fault_probability || 0.95) * 100).toFixed(0)}%)</span>
          </div>

          <button
            onClick={() => fetchIncidentData()}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors border border-white/10"
            title="Refresh Evaluation"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Candidate Decision Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {candidates.map((cand) => {
          const isValidated = cand.status === 'VALIDATED';
          const isSelected = selectedCandidate?.candidate_id === cand.candidate_id;

          return (
            <div
              key={cand.candidate_id}
              onClick={() => setSelectedCandidate(cand)}
              className={`cursor-pointer rounded-xl p-4 transition-all duration-200 border relative flex flex-col justify-between ${
                isValidated
                  ? isSelected
                    ? 'bg-emerald-950/30 border-emerald-500/60 shadow-lg shadow-emerald-500/10'
                    : 'bg-emerald-950/10 border-emerald-500/20 hover:border-emerald-500/40'
                  : isSelected
                  ? 'bg-rose-950/30 border-rose-500/60 shadow-lg shadow-rose-500/10'
                  : 'bg-rose-950/10 border-rose-500/20 hover:border-rose-500/40 opacity-75 hover:opacity-100'
              }`}
            >
              {/* Status Badge */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-1.5">
                  {isValidated ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      <CheckCircle2 className="h-3 w-3" />
                      VALIDATED SOLUTION
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide bg-rose-500/20 text-rose-300 border border-rose-500/40">
                      <XCircle className="h-3 w-3" />
                      REJECTED CANDIDATE
                    </span>
                  )}
                </div>

                <span className="text-[11px] font-mono text-white/50">
                  Fit: {(cand.score * 100).toFixed(0)}%
                </span>
              </div>

              {/* Title & Description */}
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-white/90 mb-1 leading-snug">
                  {cand.title}
                </h3>
                <p className="text-xs text-white/60 line-clamp-2">
                  {cand.validation_summary || cand.title}
                </p>
              </div>

              {/* Key Delta Metrics */}
              <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-black/40 border border-white/5 text-center mb-4">
                <div>
                  <span className="text-[9px] text-white/40 block font-mono">ENERGY SAVED</span>
                  <span className={`text-xs font-mono font-bold ${isValidated ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {cand.energy_saved_pct > 0 ? `+${cand.energy_saved_pct}%` : `${cand.energy_saved_pct}%`}
                  </span>
                </div>
                <div>
                  <span className="text-[9px] text-white/40 block font-mono">ZONE TEMP</span>
                  <span className="text-xs font-mono font-bold text-sky-400">
                    {cand.predicted_state.zone_temp ? `${cand.predicted_state.zone_temp.toFixed(1)}°C` : '22.8°C'}
                  </span>
                </div>
                <div>
                  <span className="text-[9px] text-white/40 block font-mono">STATIC SP</span>
                  <span className="text-xs font-mono font-bold text-amber-400">
                    {cand.predicted_state.sa_sp ? `${cand.predicted_state.sa_sp.toFixed(2)}"` : '1.5"'}
                  </span>
                </div>
              </div>

              {/* Interventions pills */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                {Object.entries(cand.proposed_interventions).map(([k, v]) => (
                  <span
                    key={k}
                    className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/5 border border-white/10 text-white/70"
                  >
                    {k.toUpperCase()}: <strong className="text-white">{v}%</strong>
                  </span>
                ))}
              </div>

              {/* Action / Violations footer */}
              {isValidated ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleActuate(cand);
                  }}
                  disabled={isActuating || actuationSuccess}
                  className={`w-full py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                    actuationSuccess
                      ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                      : 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-md shadow-emerald-950/40 active:scale-[0.98]'
                  }`}
                >
                  {actuationSuccess ? (
                    <>
                      <CheckCircle2 className="h-4 w-4" />
                      Actuated to Digital Twin!
                    </>
                  ) : isActuating ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Applying Actuation...
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="h-4 w-4" />
                      Approve & Actuate Interventions
                    </>
                  )}
                </button>
              ) : (
                <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-300 flex items-start gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-rose-400" />
                  <span className="line-clamp-2">
                    {cand.violations?.[0]?.description || 'Failed deterministic safety checks.'}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
};
