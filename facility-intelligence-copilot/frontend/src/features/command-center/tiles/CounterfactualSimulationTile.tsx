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
  AlertTriangle,
  ShieldCheck,
  Sparkles,
  RefreshCw,
  Cpu,
  Check,
  Flame,
  Wind,
  Gauge,
  Zap,
} from 'lucide-react';

interface Props {
  onOpenDetails?: (candidate: CounterfactualCandidate) => void;
}

export const CounterfactualSimulationTile: React.FC<Props> = () => {
  const [data, setData] = useState<ActiveIncidentResponse | null>(null);
  const [isActuating, setIsActuating] = useState(false);
  const [actuationSuccess, setActuationSuccess] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  const fetchIncidentData = async () => {
    setIsSimulating(true);
    try {
      const res = await counterfactualService.getActiveIncident();
      setData(res);
    } catch (e) {
      console.error('Error fetching counterfactual incident:', e);
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    fetchIncidentData();
    const interval = setInterval(fetchIncidentData, 10000);
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
      }, 3500);
    } catch (e) {
      console.error('Failed to actuate:', e);
    } finally {
      setIsActuating(false);
    }
  };

  const solution = data?.counterfactual_solution;
  const candidates = solution?.all_candidates || [];
  const winningCandidate = solution?.winning_candidate;
  const hasValidatedIntervention = Boolean(winningCandidate && winningCandidate.status === 'VALIDATED');

  return (
    <div id="counterfactual-tile" className="col-span-1 md:col-span-2 lg:col-span-4">
      <GlassCard className="w-full p-6 relative overflow-hidden bg-black/40 border border-white/10 rounded-2xl">
        {/* Ambient lighting */}
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
                  SNS → Digital Twin → Validated Action
                </span>
              </div>
              <p className="text-xs text-white/50">
                Deterministic validation & predictive state simulation for {data?.asset_name || 'AHU-007'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <button
              onClick={() => fetchIncidentData()}
              disabled={isSimulating}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 transition-colors border border-emerald-500/30 font-semibold active:scale-95"
              title="Trigger SNS candidate generation and virtual Twin simulation"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isSimulating ? 'animate-spin' : ''}`} />
              <span>{isSimulating ? 'Simulating...' : 'Run Simulation'}</span>
            </button>
          </div>
        </div>

        {/* 1. ACTIVE ISSUE SECTION */}
        <div className="mb-5 p-3.5 rounded-xl bg-gradient-to-r from-red-950/20 via-orange-950/20 to-black/30 border border-red-500/20 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 font-bold">
              <Flame className="h-4 w-4" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider font-mono text-red-400 block font-bold">
                Active HVAC Anomaly Detected
              </span>
              <span className="text-sm font-semibold text-white">
                {data?.fault_diagnosis ? data.fault_diagnosis.replace(/_/g, ' ').toUpperCase() : 'NOMINAL BASELINE'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="text-right">
              <span className="text-[10px] text-white/40 block">HEALTH SCORE</span>
              <span className={`font-bold text-sm ${data?.health_score && data.health_score > 75 ? 'text-emerald-400' : 'text-orange-400'}`}>
                {data?.health_score || 94}%
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-white/40 block">FACILITY STATUS</span>
              <span className="font-bold text-sm text-white/90">
                {data?.facility_status || 'NOMINAL'}
              </span>
            </div>
          </div>
        </div>

        {/* 2. SIMULATION MATRIX TABLE */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-sky-400" />
              <h3 className="text-xs font-semibold text-white/90 tracking-wide uppercase">
                Digital Twin Counterfactual Simulation ({candidates.length} Candidate Actions Evaluated)
              </h3>
            </div>
            <span className="text-[11px] text-white/40 font-mono">
              Tested via state_regressors.joblib surrogate
            </span>
          </div>

          <div className="space-y-2">
            {candidates.map((cand) => {
              const isValidated = cand.status === 'VALIDATED';
              const safetyPass = !cand.violations || cand.violations.length === 0;
              const resolutionPass = cand.resolution?.status === 'RESOLVES_ISSUE' || isValidated;

              return (
                <div
                  key={cand.candidate_id}
                  className={`p-3 rounded-xl border transition-all ${
                    isValidated
                      ? 'bg-emerald-950/20 border-emerald-500/40 shadow-sm shadow-emerald-500/5'
                      : 'bg-white/[0.02] border-white/10 opacity-80'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono tracking-wide ${
                        isValidated
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      }`}>
                        {isValidated ? 'VALIDATED' : 'REJECTED'}
                      </span>
                      <h4 className="text-xs font-semibold text-white/90">{cand.title}</h4>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] font-mono">
                      <span className="flex items-center gap-1">
                        <span className="text-white/40">Safety:</span>
                        <strong className={safetyPass ? 'text-emerald-400' : 'text-rose-400'}>
                          {safetyPass ? 'PASS' : 'FAIL'}
                        </strong>
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="text-white/40">Resolution:</span>
                        <strong className={resolutionPass ? 'text-emerald-400' : 'text-rose-400'}>
                          {resolutionPass ? 'RESOLVES' : 'DOES NOT RESOLVE'}
                        </strong>
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-white/60 mb-2">
                    {cand.validation_summary || 'Evaluated against ASHRAE comfort and mechanical constraints.'}
                  </p>

                  <div className="flex flex-wrap items-center gap-2">
                    {Object.entries(cand.proposed_interventions).map(([act, val]) => (
                      <span
                        key={act}
                        className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/5 border border-white/10 text-white/70"
                      >
                        {act.toUpperCase()}: <strong className="text-white">{val}%</strong>
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3. VALIDATED INTERVENTION & TECHNICIAN APPROVAL */}
        {hasValidatedIntervention && winningCandidate ? (
          <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-950/40 via-black/50 to-teal-950/30 border-2 border-emerald-500/50 shadow-lg shadow-emerald-500/10">
            <div className="flex items-center justify-between mb-3 border-b border-emerald-500/20 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block">
                    Recommended Technician Intervention
                  </span>
                  <h3 className="text-sm font-bold text-white">{winningCandidate.title}</h3>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                  PASS ALL CRITERIA
                </span>
              </div>
            </div>

            {/* Predicted Result Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-4">
              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Wind className="h-3 w-3 text-sky-400" /> SUPPLY AIRFLOW
                </span>
                <span className="text-xs font-mono font-bold text-sky-400">
                  {winningCandidate.predicted_state.sa_cfm ? `${winningCandidate.predicted_state.sa_cfm.toFixed(0)} CFM` : '15,200 CFM'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Flame className="h-3 w-3 text-orange-400" /> ZONE TEMP
                </span>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {winningCandidate.predicted_state.zone_temp ? `${winningCandidate.predicted_state.zone_temp.toFixed(1)}°C` : '22.5°C'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Gauge className="h-3 w-3 text-amber-400" /> STATIC SP
                </span>
                <span className="text-xs font-mono font-bold text-amber-400">
                  {winningCandidate.predicted_state.sa_sp ? `${winningCandidate.predicted_state.sa_sp.toFixed(2)}"` : '1.50"'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Zap className="h-3 w-3 text-emerald-400" /> ENERGY SAVINGS
                </span>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {winningCandidate.energy_saved_pct > 0 ? `+${winningCandidate.energy_saved_pct}%` : `${winningCandidate.energy_saved_pct}%`}
                </span>
              </div>
            </div>

            {/* Actuation Button */}
            <button
              onClick={() => handleActuate(winningCandidate)}
              disabled={isActuating || actuationSuccess}
              className={`w-full py-3 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                actuationSuccess
                  ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                  : 'bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-950/60 active:scale-[0.99] cursor-pointer'
              }`}
            >
              {actuationSuccess ? (
                <>
                  <Check className="h-4 w-4 stroke-[3]" />
                  <span>Intervention Actuated to Digital Twin & Control Loop!</span>
                </>
              ) : isActuating ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Applying Validated Actuation...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  <span>Approve & Actuate Interventions</span>
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 text-center">
            <AlertTriangle className="h-6 w-6 text-rose-400 mx-auto mb-2" />
            <h4 className="text-xs font-bold text-rose-300 mb-1 uppercase tracking-wider">
              NO VALIDATED INTERVENTION AVAILABLE
            </h4>
            <p className="text-xs text-white/60 max-w-md mx-auto">
              {solution?.reason || 'No simulated candidate satisfied both the required safety constraints and fault resolution criteria.'}
            </p>
          </div>
        )}
      </GlassCard>
    </div>
  );
};

