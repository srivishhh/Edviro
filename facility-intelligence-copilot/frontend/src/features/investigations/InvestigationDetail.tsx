import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Send, Award, ShieldCheck, Clock } from 'lucide-react';
import { Header } from '../../components/Header';
import { GlassCard } from '../../components/GlassCard';

export const InvestigationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const incidentId = id || 'inc-701';

  // Form State
  const [observedProblem, setObservedProblem] = useState('');
  const [actionPerformed, setActionPerformed] = useState('');
  const [rootCauseObserved, setRootCauseObserved] = useState('');
  const [partsInspected, setPartsInspected] = useState('Supply Fan, VFD Belt, Inflow Damper');
  const [resolutionStatus, setResolutionStatus] = useState('RESOLVED');
  const [additionalNotes, setAdditionalNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedReport, setSubmittedReport] = useState<any>(null);

  const fetchReport = () => {
    fetch(`http://127.0.0.1:8000/api/v1/incidents/${incidentId}/resolution-report`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.submitted) {
          setSubmittedReport(data.report);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchReport();
  }, [incidentId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!observedProblem || !actionPerformed || !rootCauseObserved) {
      alert('Please complete all required fields in the resolution report.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/incidents/${incidentId}/resolution-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incidentId,
          asset_id: 'AHU-007',
          observed_problem: observedProblem,
          action_performed: actionPerformed,
          root_cause_observed: rootCauseObserved,
          parts_inspected: partsInspected,
          resolution_status: resolutionStatus,
          additional_notes: additionalNotes,
          evidence: 'Airflow differential telemetry & physical inspection verified',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        alert(data.message || 'Report submitted! Awaiting Admin Review.');
        setSubmittedReport(data.report);
      } else {
        const err = await res.json();
        alert(`Submission Error: ${err.detail}`);
      }
    } catch {
      alert('Failed to connect to backend server.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] transition-colors">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={() => navigate('/investigations')}
          className="mb-4 flex items-center gap-2 text-xs font-semibold text-[#F25912] hover:underline"
        >
          <ArrowLeft size={14} />
          <span>Back to Incidents</span>
        </button>

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-extrabold text-[var(--text-main)] tracking-tight">AIRFLOW RESTRICTION</h1>
              <span className="rounded-xl bg-[#5C3E94] px-2.5 py-1 text-xs font-mono font-bold text-white shadow-sm">
                AHU-007
              </span>
              <span className="rounded-xl bg-[#F25912]/20 border border-[#F25912]/40 px-2.5 py-1 text-xs font-bold text-[#F25912]">
                HIGH SEVERITY
              </span>
            </div>
            <p className="mt-1 text-sm text-[var(--text-muted)]">INCIDENT ID: {incidentId} • Executed via Real SNS Workbench Pipeline</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* SNS Diagnosis Details */}
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-[var(--text-main)] flex items-center gap-2">
              <ShieldCheck size={18} className="text-[#F25912]" />
              <span>SNS Multi-Agent Analysis & Diagnostics</span>
            </h2>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-semibold text-[var(--text-muted)] uppercase tracking-wide">CONDITION</span>
                <p className="text-[var(--text-main)] mt-0.5">Airflow Restriction detected via pressure differential telemetry across supply fan plenum.</p>
              </div>

              <div>
                <span className="font-semibold text-[var(--text-muted)] uppercase tracking-wide">RISK ASSESSMENT</span>
                <p className="text-[var(--text-main)] mt-0.5">Cooling performance degradation, zone temperature overshoot, and potential fan coil freeze-up.</p>
              </div>

              <div>
                <span className="font-semibold text-[#5C3E94] dark:text-purple-300 uppercase tracking-wide">DIAGNOSIS</span>
                <p className="text-[var(--text-main)] font-medium mt-0.5">VFD belt slippage or inlet guide vane mechanical obstruction on supply fan.</p>
              </div>

              <div>
                <span className="font-semibold text-[var(--text-muted)] uppercase tracking-wide">RECOMMENDED RESOLUTION</span>
                <p className="text-[var(--text-main)] mt-0.5">Inspect supply fan belt tension and align VFD pulley; inspect damper actuators.</p>
              </div>

              <div>
                <span className="font-semibold text-[var(--text-muted)] uppercase tracking-wide">PRESCRIPTION</span>
                <p className="text-[var(--text-main)] mt-0.5">Clear obstruction, tension VFD drive belt to 12mm deflection, recalibrate airflow sensor.</p>
              </div>

              <div>
                <span className="font-semibold text-[var(--text-muted)] uppercase tracking-wide">ASSURANCE</span>
                <p className="text-[var(--text-main)] mt-0.5">Baseline airflow expected to return to &gt;95% within 30 minutes of mechanical repair.</p>
              </div>
            </div>
          </GlassCard>

          {/* Technician Resolution Form or Submitted Review State */}
          <GlassCard className="p-6">
            <h2 className="text-base font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
              <Award size={18} className="text-[#F25912]" />
              <span>Technician Resolution Report</span>
            </h2>

            {submittedReport ? (
              <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 text-xs space-y-3 shadow-inner">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[var(--text-main)] font-bold text-sm">
                    {submittedReport.review_status === 'APPROVED' ? (
                      <>
                        <CheckCircle2 size={18} className="text-emerald-500" />
                        <span className="text-emerald-500">Resolution Verified & Awarded</span>
                      </>
                    ) : (
                      <>
                        <Clock size={18} className="text-amber-500 animate-pulse" />
                        <span className="text-amber-500">Awaiting Admin Review</span>
                      </>
                    )}
                  </div>
                  {submittedReport.review_status === 'APPROVED' ? (
                    <span className="rounded-xl bg-emerald-500/15 px-2.5 py-1 text-emerald-500 font-bold border border-emerald-500/30">
                      +{submittedReport.awarded_credits} CREDITS
                    </span>
                  ) : (
                    <span className="rounded-xl bg-amber-500/15 px-2.5 py-1 text-amber-500 font-bold border border-amber-500/30">
                      {submittedReport.suggested_credits} Credits Pending
                    </span>
                  )}
                </div>

                <div className="border-t border-[var(--border-subtle)] pt-3 space-y-2">
                  <p><span className="text-[var(--text-muted)]">Observed Problem:</span> <span className="text-[var(--text-main)]">{submittedReport.observed_problem}</span></p>
                  <p><span className="text-[var(--text-muted)]">Action Performed:</span> <span className="text-[var(--text-main)]">{submittedReport.action_performed}</span></p>
                  <p><span className="text-[var(--text-muted)]">Observed Root Cause:</span> <span className="text-[var(--text-main)]">{submittedReport.root_cause_observed}</span></p>
                  <p><span className="text-[var(--text-muted)]">Resolution Status:</span> <strong className="text-emerald-500">{submittedReport.resolution_status}</strong></p>
                  {submittedReport.admin_notes && (
                    <p><span className="text-[var(--text-muted)]">Admin Notes:</span> <span className="text-[#5C3E94] dark:text-purple-300 font-medium">{submittedReport.admin_notes}</span></p>
                  )}
                </div>

                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => navigate('/profile')}
                    className="w-full rounded-xl bg-[#5C3E94] px-4 py-2.5 font-bold text-white text-center hover:bg-[#412B6B] active:scale-95 transition-all shadow-sm"
                  >
                    View Credits Wallet & Ledger
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-3 text-xs">
                <div>
                  <label className="block text-[var(--text-main)] font-semibold mb-1">Observed Problem *</label>
                  <input
                    type="text"
                    required
                    value={observedProblem}
                    onChange={(e) => setObservedProblem(e.target.value)}
                    placeholder="e.g., Supply fan drive belt loose, airflow CFM down 28%"
                    className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2 text-[var(--text-main)] focus:border-[#F25912] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[var(--text-main)] font-semibold mb-1">Action Performed *</label>
                  <textarea
                    required
                    rows={2}
                    value={actionPerformed}
                    onChange={(e) => setActionPerformed(e.target.value)}
                    placeholder="e.g., Re-tensioned supply fan VFD drive belt to 12mm deflection, lubricated bearings"
                    className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2 text-[var(--text-main)] focus:border-[#F25912] focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[var(--text-main)] font-semibold mb-1">Root Cause Observed *</label>
                    <input
                      type="text"
                      required
                      value={rootCauseObserved}
                      onChange={(e) => setRootCauseObserved(e.target.value)}
                      placeholder="e.g., VFD belt slippage due to normal wear"
                      className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2 text-[var(--text-main)] focus:border-[#F25912] focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-[var(--text-main)] font-semibold mb-1">Parts Inspected</label>
                    <input
                      type="text"
                      value={partsInspected}
                      onChange={(e) => setPartsInspected(e.target.value)}
                      className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2 text-[var(--text-main)] focus:border-[#F25912] focus:outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[var(--text-main)] font-semibold mb-1">Resolution Status</label>
                    <select
                      value={resolutionStatus}
                      onChange={(e) => setResolutionStatus(e.target.value)}
                      className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2 text-[var(--text-main)] focus:border-[#F25912] focus:outline-none"
                    >
                      <option value="RESOLVED">RESOLVED</option>
                      <option value="PARTIALLY_RESOLVED">PARTIALLY RESOLVED</option>
                      <option value="NOT_RESOLVED">NOT RESOLVED</option>
                      <option value="ESCALATE">ESCALATE</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[var(--text-main)] font-semibold mb-1">Additional Notes</label>
                    <input
                      type="text"
                      value={additionalNotes}
                      onChange={(e) => setAdditionalNotes(e.target.value)}
                      placeholder="Optional notes"
                      className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3.5 py-2 text-[var(--text-main)] focus:border-[#F25912] focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-[#F25912] px-4 py-3 font-bold text-white shadow-lg shadow-orange-950/20 transition-all hover:bg-orange-600 active:scale-95 disabled:opacity-50"
                >
                  <Send size={15} />
                  <span>{isSubmitting ? 'Submitting to Admin...' : 'Submit Resolution Report for Admin Review'}</span>
                </button>
              </form>
            )}
          </GlassCard>
        </div>
      </main>
    </div>
  );
};

export default InvestigationDetail;
