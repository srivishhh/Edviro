import { AlertTriangle, CheckCircle2, Gauge, ShieldCheck, Sparkles, TrendingUp, Loader2 } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { createInvestigation, getInvestigation, type InvestigationResult } from '../services/xray';
import type { Asset } from '../types/asset';
import { getAsset } from '../services/assets';

function XRay() {
  const [searchParams] = useSearchParams();
  const assetIdParam = searchParams.get('asset_id');
  const alertIdParam = searchParams.get('alert_id');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [investigation, setInvestigation] = useState<InvestigationResult | null>(null);
  const [assetDetails, setAssetDetails] = useState<Asset | null>(null);

  useEffect(() => {
    let isActive = true;

    const startInvestigation = async () => {
      if (!assetIdParam || !alertIdParam) {
        return; // Nothing to investigate
      }

      setLoading(true);
      setError('');
      try {
        const assetId = parseInt(assetIdParam, 10);
        const alertId = parseInt(alertIdParam, 10);

        if (isActive) {
          try {
            const asset = await getAsset(assetId);
            setAssetDetails(asset);
          } catch (e) {
            // Asset load can gracefully fail if fallback is needed, though shouldn't happen.
          }
        }

        const data = await createInvestigation(assetId, alertId);

        if (isActive) {
          setInvestigation(data);

          if (data.status === 'PENDING') {
            // Poll for result
            const pollInterval = window.setInterval(async () => {
              try {
                const updated = await getInvestigation(data.investigation_id);
                if (isActive) {
                  setInvestigation(updated);
                  if (updated.status !== 'PENDING') {
                    window.clearInterval(pollInterval);
                  }
                }
              } catch (e) {
                // Ignore temporary network errors during polling
              }
            }, 2000);

            return () => window.clearInterval(pollInterval);
          }
        }
      } catch (err) {
        if (isActive) {
          setError(err instanceof Error ? err.message : 'Investigation failed to start.');
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    };

    const cleanup = startInvestigation();
    return () => {
      isActive = false;
      if (cleanup && typeof cleanup.then === 'function') {
        cleanup.then(cleanFn => typeof cleanFn === 'function' && cleanFn());
      }
    };
  }, [assetIdParam, alertIdParam]);

  if (!assetIdParam || !alertIdParam) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-300">
        <p>Please select an alert from the Alerts page to begin an investigation.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-8 text-red-200">
        <p className="font-semibold">Investigation Failed</p>
        <p className="mt-2 text-sm text-red-100/80">{error}</p>
      </div>
    );
  }

  if (loading && !investigation) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900 p-12 text-slate-300 min-h-[400px]">
        <Loader2 className="animate-spin text-cyan-500 mb-4" size={32} />
        <p className="text-lg">Initializing Facility X-Ray...</p>
      </div>
    );
  }

  const isPending = investigation?.status === 'PENDING';

  return (
    <div className="space-y-6">
      <header className="rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/60 to-slate-900 p-6 flex justify-between items-center">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">FACILITY X-RAY</p>
          <h2 className="mt-3 text-3xl font-semibold text-slate-100">Industrial Investigation Console</h2>
        </div>
        <div>
          <span className={`px-4 py-1.5 rounded-full text-xs tracking-wider border font-bold ${isPending ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 animate-pulse' :
              investigation?.status === 'FAILED' ? 'bg-red-500/20 text-red-300 border-red-500/40' :
                'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
            }`}>
            {investigation?.status || 'UNKNOWN'}
          </span>
        </div>
      </header>

      {isPending ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900 p-12 text-cyan-300 min-h-[400px]">
          <Loader2 className="animate-spin mb-4" size={48} />
          <p className="text-xl font-semibold">AI is analyzing telemetry and relationships...</p>
          <p className="mt-2 text-sm text-slate-400">This may take a few moments while we gather evidence.</p>
        </div>
      ) : (
        <>
          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase tracking-[0.2em] text-slate-400">Incident</span>
                <span className={`rounded-full border px-2 py-1 text-xs font-medium ${investigation?.severity === 'CRITICAL' ? 'border-red-500/40 bg-red-500/10 text-red-200' :
                    'border-amber-500/40 bg-amber-500/10 text-amber-200'
                  }`}>
                  {investigation?.severity || 'UNKNOWN'}
                </span>
              </div>

              <div className="mt-5 space-y-4">
                <div>
                  <p className="text-sm text-slate-400">Asset</p>
                  <p className="mt-1 text-2xl font-semibold text-slate-100">{assetDetails?.name || `Asset #${investigation?.asset_id}`}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Incident</p>
                  <p className="mt-1 text-lg text-slate-100">{investigation?.summary || 'Pending summary...'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Confidence</p>
                  <p className="mt-1 text-lg text-emerald-300">{investigation?.confidence || 'N/A'}</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <div className="flex items-center gap-2 text-cyan-300">
                <Sparkles size={18} />
                <p className="text-xs uppercase tracking-[0.2em]">Root cause</p>
              </div>
              <h3 className="mt-4 text-2xl font-semibold text-slate-100">{investigation?.root_cause || 'Analyzing root cause...'}</h3>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <div className="mb-4 flex items-center gap-2 text-emerald-300">
                <ShieldCheck size={18} />
                <h3 className="text-lg font-semibold text-slate-100">WHY WE THINK THIS</h3>
              </div>
              <ul className="space-y-3 text-slate-200">
                {investigation?.evidence?.map((item, index) => (
                  <li key={index} className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                    <CheckCircle2 className="mt-0.5 text-emerald-400" size={16} />
                    <div>
                      <span className="font-semibold">{item.metric}: </span>
                      <span>{item.interpretation}</span>
                      <div className="text-xs text-slate-400 mt-1">Observed: {item.current_value.toFixed(2)} (Baseline: {item.baseline.toFixed(2)})</div>
                    </div>
                  </li>
                ))}
                {!investigation?.evidence?.length && (
                  <li className="text-slate-400 italic">No structured evidence available.</li>
                )}
              </ul>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <div className="mb-4 flex items-center gap-2 text-amber-300">
                <TrendingUp size={18} />
                <h3 className="text-lg font-semibold text-slate-100">RECOMMENDED ACTIONS</h3>
              </div>
              <ol className="space-y-3 text-slate-200">
                {investigation?.recommended_actions?.map((action, index) => (
                  <li key={index} className="flex gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                    <span className="flex h-6 w-6 items-center justify-center shrink-0 rounded-full bg-amber-500/10 text-xs font-semibold text-amber-200">{index + 1}</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ol>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2 mt-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-center gap-2 text-violet-300">
                <AlertTriangle size={16} />
                <span className="text-sm uppercase tracking-[0.2em]">Related Assets Affected</span>
              </div>
              <div className="mt-4 space-y-2 text-sm text-slate-300">
                {investigation?.affected_assets?.length ? (
                  investigation.affected_assets.map(asset => <p key={asset}>{asset}</p>)
                ) : (
                  <p>None isolated</p>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-center gap-2 text-slate-400">
                <Gauge size={16} />
                <span className="text-sm uppercase tracking-[0.2em]">Investigation ID</span>
              </div>
              <div className="mt-4 break-all text-sm font-mono text-slate-500">
                {investigation?.investigation_id}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default XRay;
