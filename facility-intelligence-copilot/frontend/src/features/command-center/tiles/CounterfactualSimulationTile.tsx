import React, { useState, useEffect, useCallback } from 'react';
import { GlassCard } from '../../../components/GlassCard';
import {
  counterfactualService,
} from '../../../services/counterfactualService';
import type {
  ActiveIncidentResponse,
  CounterfactualCandidate,
  InvestigateResponse,
  SNSCandidateAction,
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
  Brain,
  ChevronRight,
  Activity,
  BarChart3,
} from 'lucide-react';

interface Props {
  onOpenDetails?: (candidate: CounterfactualCandidate) => void;
}

type SimulationStage = 'idle' | 'fetching_incident' | 'running_sns' | 'simulating' | 'done';

export const CounterfactualSimulationTile: React.FC<Props> = () => {
  const [incidentData, setIncidentData] = useState<ActiveIncidentResponse | null>(null);
  const [investigateResult, setInvestigateResult] = useState<InvestigateResponse | null>(null);
  const [stage, setStage] = useState<SimulationStage>('idle');
  const [isActuating, setIsActuating] = useState(false);
  const [actuationSuccess, setActuationSuccess] = useState(false);
  const [stageLabel, setStageLabel] = useState('');

  // Auto-fetch incident data on mount and every 15s
  const fetchIncidentData = useCallback(async () => {
    try {
      const res = await counterfactualService.getActiveIncident();
      setIncidentData(res);
    } catch (e) {
      console.error('Error fetching active incident:', e);
    }
  }, []);

  useEffect(() => {
    fetchIncidentData();
    const interval = setInterval(fetchIncidentData, 15000);
    return () => clearInterval(interval);
  }, [fetchIncidentData]);

  // Full pipeline: SNS → Digital Twin → Validated result
  const runFullSimulation = useCallback(async () => {
    if (!incidentData?.has_active_incident || !incidentData?.incident_id) {
      // If no active incident, still run with current data
      return;
    }

    setStage('running_sns');
    setStageLabel('Dispatching to SNS Workbench (3.0 GSense)...');
    setInvestigateResult(null);

    try {
      // Short delay for visual feedback
      await new Promise(r => setTimeout(r, 600));
      setStage('simulating');
      setStageLabel('Running Digital Twin simulations...');

      const result = await counterfactualService.runInvestigation(
        incidentData.incident_id,
        {
          asset_id: incidentData.asset_id,
          detected_fault: incidentData.fault_diagnosis,
          current_telemetry: incidentData.current_telemetry,
        }
      );

      setInvestigateResult(result);
      setStage('done');
      setStageLabel('');
    } catch (e) {
      console.error('Investigation failed:', e);
      setStage('idle');
      setStageLabel('');
    }
  }, [incidentData]);

  const handleActuate = async (cand: CounterfactualCandidate) => {
    if (cand.status !== 'VALIDATED') return;
    setIsActuating(true);
    try {
      await counterfactualService.applyActuation({
        candidate_id: cand.candidate_id,
        interventions: cand.proposed_interventions,
        asset_id: incidentData?.asset_id || 'AHU-007',
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

  // --- Derived state ---
  const isRunning = stage === 'running_sns' || stage === 'simulating';
  const snsCandidates: SNSCandidateAction[] = investigateResult?.sns?.candidate_actions || [];
  const simulations: CounterfactualCandidate[] = investigateResult?.simulations || [];
  const winningCandidate = investigateResult?.validated_intervention;
  const hasValidated = Boolean(winningCandidate && winningCandidate.status === 'VALIDATED');
  const simSummary = investigateResult?.simulation_summary;

  // Fallback: use legacy counterfactual_solution from active incident if no investigate result
  const legacySolution = incidentData?.counterfactual_solution;
  const displayCandidates = simulations.length > 0 ? simulations : (legacySolution?.all_candidates || []);
  const displayWinner = winningCandidate || legacySolution?.winning_candidate;
  const displayHasValidated = Boolean(displayWinner && displayWinner.status === 'VALIDATED');

  return (
    <div id="counterfactual-tile" className="col-span-1 md:col-span-2 lg:col-span-4">
      <GlassCard className="w-full p-6 relative overflow-hidden bg-black/40 border border-white/10 rounded-2xl">
        {/* Ambient lighting */}
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-20 -bottom-20 w-80 h-80 bg-[#F25912]/10 rounded-full blur-3xl pointer-events-none" />

        {/* ── Header ─────────────────────────────────────── */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5 border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-semibold text-white tracking-wide">
                  GSENSE 3.0 Counterfactual Intelligence & Virtual Twin
                </h2>
                <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/30">
                  SNS → Digital Twin → Validated Action
                </span>
              </div>
              <p className="text-xs text-white/50">
                Deterministic validation & predictive state simulation for {incidentData?.asset_name || 'AHU-007'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {isRunning && (
              <span className="flex items-center gap-1.5 text-sky-400 font-mono text-[11px] animate-pulse">
                <Activity className="h-3.5 w-3.5" />
                {stageLabel}
              </span>
            )}
            <button
              onClick={runFullSimulation}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 transition-colors border border-emerald-500/30 font-semibold active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
              title="Run full SNS + Digital Twin pipeline"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRunning ? 'animate-spin' : ''}`} />
              <span>{isRunning ? 'Running...' : 'Run Simulation'}</span>
            </button>
          </div>
        </div>

        {/* ── 1. ACTIVE ANOMALY ───────────────────────────── */}
        <div className="mb-4 p-3.5 rounded-xl bg-gradient-to-r from-red-950/20 via-orange-950/20 to-black/30 border border-red-500/20 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 font-bold">
              <Flame className="h-4 w-4" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider font-mono text-red-400 block font-bold">
                Active HVAC Anomaly Detected
              </span>
              <span className="text-sm font-semibold text-white">
                {incidentData?.fault_diagnosis
                  ? incidentData.fault_diagnosis.replace(/_/g, ' ').toUpperCase()
                  : 'NOMINAL BASELINE'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="text-right">
              <span className="text-[10px] text-white/40 block">HEALTH SCORE</span>
              <span className={`font-bold text-sm ${
                incidentData?.health_score && incidentData.health_score > 75 ? 'text-emerald-400' : 'text-orange-400'
              }`}>
                {incidentData?.health_score || 94}%
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-white/40 block">FACILITY STATUS</span>
              <span className="font-bold text-sm text-white/90">
                {incidentData?.facility_status || 'NOMINAL'}
              </span>
            </div>
            {incidentData?.fault_probability ? (
              <div className="text-right">
                <span className="text-[10px] text-white/40 block">CONFIDENCE</span>
                <span className="font-bold text-sm text-amber-400">
                  {(incidentData.fault_probability * 100).toFixed(0)}%
                </span>
              </div>
            ) : null}
          </div>
        </div>

        {/* ── 2. SNS GENERATED ACTIONS (only shown after investigation) ── */}
        {snsCandidates.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2.5">
              <Brain className="h-4 w-4 text-violet-400" />
              <h3 className="text-xs font-semibold text-white/90 tracking-wide uppercase">
                SNS Workbench — 3.0 GSense Generated{' '}
                <span className="text-violet-400">{snsCandidates.length} Candidate Actions</span>
              </h3>
              <span className="ml-auto text-[10px] font-mono text-white/40">
                {investigateResult?.sns?.workflow_name} · exec: {investigateResult?.sns?.execution_id?.slice(-8)}
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {snsCandidates.map((action, i) => (
                <div
                  key={action.action_id}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-violet-950/30 border border-violet-500/25 text-[11px] font-mono"
                >
                  <span className="text-violet-400/60 font-bold">{i + 1}</span>
                  <ChevronRight className="h-3 w-3 text-violet-400/40" />
                  <span className="text-white/70">{action.target.toUpperCase()}</span>
                  <span className="text-white/40">:</span>
                  <span className="text-white/50">{action.current_value.toFixed(0)}%</span>
                  <span className="text-violet-400">→</span>
                  <strong className="text-white">{action.proposed_value.toFixed(0)}%</strong>
                </div>
              ))}
            </div>

            {snsCandidates.length > 0 && (
              <p className="mt-2 text-[10px] text-white/40 font-mono">
                provenance: LLM_REASONING · each candidate → independent Digital Twin simulation branch
              </p>
            )}
          </div>
        )}

        {/* Pipeline flow arrow (shown during and after simulation) */}
        {(isRunning || investigateResult) && (
          <div className="flex items-center gap-2 mb-4 text-[10px] font-mono text-white/40">
            <span className={`px-2 py-0.5 rounded ${stage === 'running_sns' ? 'bg-violet-500/30 text-violet-300 animate-pulse' : 'bg-violet-500/15 text-violet-400'}`}>
              SNS
            </span>
            <ChevronRight className="h-3 w-3" />
            <span className={`px-2 py-0.5 rounded ${stage === 'simulating' ? 'bg-sky-500/30 text-sky-300 animate-pulse' : 'bg-sky-500/15 text-sky-400'}`}>
              DIGITAL TWIN
            </span>
            <ChevronRight className="h-3 w-3" />
            <span className={`px-2 py-0.5 rounded ${stage === 'done' ? (hasValidated ? 'bg-emerald-500/30 text-emerald-300' : 'bg-rose-500/30 text-rose-300') : 'bg-white/5 text-white/30'}`}>
              {stage === 'done' ? (hasValidated ? 'VALIDATED' : 'NO_VALIDATED_INTERVENTION') : 'RESULT'}
            </span>
            {simSummary && (
              <span className="ml-auto text-white/50">
                {simSummary.total_simulated} simulated · {simSummary.safe} safe · {simSummary.resolves} resolve · {simSummary.validated} validated
              </span>
            )}
          </div>
        )}

        {/* ── 3. COUNTERFACTUAL SIMULATION MATRIX ────────── */}
        {displayCandidates.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-sky-400" />
                <h3 className="text-xs font-semibold text-white/90 tracking-wide uppercase">
                  Digital Twin Counterfactual Simulation ({displayCandidates.length} Branches Evaluated)
                </h3>
              </div>
              <span className="text-[11px] text-white/40 font-mono">
                via state_regressors.joblib surrogate · independent baselines
              </span>
            </div>

            <div className="space-y-2">
              {displayCandidates.map((cand) => {
                const isValidated = cand.status === 'VALIDATED';
                const safetyPass = !cand.violations || cand.violations.length === 0;
                const resolutionPass =
                  cand.resolution?.status === 'RESOLVES_ISSUE' || isValidated;
                const isSNSCandidate = cand.candidate_id.includes('sns_');

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
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono tracking-wide ${
                            isValidated
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {isValidated ? 'VALIDATED' : cand.status}
                        </span>
                        {isSNSCandidate && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-violet-500/15 text-violet-400 border border-violet-500/20">
                            SNS
                          </span>
                        )}
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
                        {cand.energy_saved_pct !== 0 && (
                          <span className="flex items-center gap-1">
                            <Zap className="h-3 w-3 text-emerald-400" />
                            <strong className={cand.energy_saved_pct > 0 ? 'text-emerald-400' : 'text-orange-400'}>
                              {cand.energy_saved_pct > 0 ? '+' : ''}{cand.energy_saved_pct.toFixed(1)}%
                            </strong>
                          </span>
                        )}
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
                          {act.toUpperCase()}:{' '}
                          <strong className="text-white">{Number(val).toFixed(0)}%</strong>
                        </span>
                      ))}
                      {cand.predicted_state?.zone_temp && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/5 border border-white/10 text-white/50">
                          predicted zone: <strong className="text-white/80">{cand.predicted_state.zone_temp.toFixed(1)}°C</strong>
                        </span>
                      )}
                      {cand.predicted_state?.sa_temp && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/5 border border-white/10 text-white/50">
                          SAT: <strong className="text-white/80">{cand.predicted_state.sa_temp.toFixed(1)}°C</strong>
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── 4. VALIDATED INTERVENTION HERO CARD ─────────── */}
        {displayHasValidated && displayWinner ? (
          <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-950/40 via-black/50 to-teal-950/30 border-2 border-emerald-500/50 shadow-lg shadow-emerald-500/10">
            <div className="flex items-center justify-between mb-3 border-b border-emerald-500/20 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block">
                    Recommended Technician Intervention — Digital Twin Validated
                  </span>
                  <h3 className="text-sm font-bold text-white">{displayWinner.title}</h3>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                  PASS ALL CRITERIA
                </span>
                <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
                  score: {displayWinner.score?.toFixed(3)}
                </span>
              </div>
            </div>

            {/* Predicted metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-4">
              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Wind className="h-3 w-3 text-sky-400" /> SUPPLY AIRFLOW
                </span>
                <span className="text-xs font-mono font-bold text-sky-400">
                  {displayWinner.predicted_state?.sa_cfm
                    ? `${displayWinner.predicted_state.sa_cfm.toFixed(0)} CFM`
                    : '—'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Flame className="h-3 w-3 text-orange-400" /> ZONE TEMP
                </span>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {displayWinner.predicted_state?.zone_temp
                    ? `${displayWinner.predicted_state.zone_temp.toFixed(1)}°C`
                    : '—'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Gauge className="h-3 w-3 text-amber-400" /> STATIC SP
                </span>
                <span className="text-xs font-mono font-bold text-amber-400">
                  {displayWinner.predicted_state?.sa_sp
                    ? `${displayWinner.predicted_state.sa_sp.toFixed(2)}"`
                    : '—'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-emerald-500/20 text-center">
                <span className="text-[10px] text-white/40 block font-mono flex items-center justify-center gap-1">
                  <Zap className="h-3 w-3 text-emerald-400" /> ENERGY SAVINGS
                </span>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {displayWinner.energy_saved_pct != null
                    ? `${displayWinner.energy_saved_pct > 0 ? '+' : ''}${displayWinner.energy_saved_pct.toFixed(1)}%`
                    : '—'}
                </span>
              </div>
            </div>

            {/* Resolution evidence */}
            {displayWinner.resolution?.evidence && displayWinner.resolution.evidence.length > 0 && (
              <div className="mb-3 p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/15">
                <div className="flex items-center gap-1.5 mb-1">
                  <BarChart3 className="h-3 w-3 text-emerald-400" />
                  <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider">Resolution Evidence</span>
                </div>
                {displayWinner.resolution.evidence.map((ev, i) => (
                  <p key={i} className="text-[11px] text-white/60 leading-relaxed">{ev}</p>
                ))}
              </div>
            )}

            {/* Actuation Button */}
            <button
              onClick={() => handleActuate(displayWinner)}
              disabled={isActuating || actuationSuccess}
              className={`w-full py-3 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                actuationSuccess
                  ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                  : 'bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-950/60 active:scale-[0.99] cursor-pointer disabled:opacity-60'
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
                  <span>Approve & Actuate Intervention</span>
                </>
              )}
            </button>
          </div>
        ) : investigateResult ? (
          /* NO_VALIDATED_INTERVENTION — show failure reasons */
          <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30">
            <div className="flex items-start gap-3 mb-3">
              <AlertTriangle className="h-6 w-6 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-rose-300 mb-1 uppercase tracking-wider">
                  NO VALIDATED INTERVENTION — ALL {simulations.length} CANDIDATES EVALUATED
                </h4>
                <p className="text-xs text-white/60">
                  {investigateResult.reason || 'No simulated candidate satisfied both the required safety constraints and fault resolution criteria.'}
                </p>
              </div>
            </div>
            {simulations.length > 0 && (
              <div className="mt-3 pt-3 border-t border-rose-500/15">
                <p className="text-[10px] font-mono text-white/40 uppercase tracking-wider mb-1.5">Rejection reasons:</p>
                {simulations.slice(0, 4).map(c => (
                  <p key={c.candidate_id} className="text-[11px] text-white/50 leading-relaxed">
                    <strong className="text-rose-400">{c.candidate_id}</strong>: {c.validation_summary}
                  </p>
                ))}
              </div>
            )}
          </div>
        ) : displayCandidates.length === 0 ? (
          /* Initial state — no simulation run yet */
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 text-center">
            <Sparkles className="h-6 w-6 text-emerald-400/50 mx-auto mb-2" />
            <h4 className="text-xs font-medium text-white/50 mb-1">
              Click &ldquo;Run Simulation&rdquo; to start the GSENSE 3.0 pipeline
            </h4>
            <p className="text-[11px] text-white/30">
              SNS Workbench will generate 6–8 fault-specific candidates, each independently simulated in the Digital Twin.
            </p>
          </div>
        ) : (
          /* Legacy solution available but no investigate result yet */
          legacySolution && !displayHasValidated && (
            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 text-center">
              <AlertTriangle className="h-6 w-6 text-rose-400 mx-auto mb-2" />
              <h4 className="text-xs font-bold text-rose-300 mb-1 uppercase tracking-wider">
                NO VALIDATED INTERVENTION AVAILABLE
              </h4>
              <p className="text-xs text-white/60 max-w-md mx-auto">
                {legacySolution.reason || 'No simulated candidate satisfied both the required safety constraints and fault resolution criteria.'}
              </p>
            </div>
          )
        )}
      </GlassCard>
    </div>
  );
};
