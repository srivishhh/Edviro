import { useEffect, useState } from 'react';
import { AlertTriangle, Gauge, Search, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getAlerts } from '../services/alerts';
import type { Alert } from '../types/alert';

function Alerts() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        let isActive = true;

        const loadAlerts = async () => {
            try {
                const data = await getAlerts();
                if (isActive) {
                    setAlerts(data);
                    setError('');
                }
            } catch (err) {
                if (isActive) {
                    setError(err instanceof Error ? err.message : 'Failed to load alerts.');
                }
            } finally {
                if (isActive) {
                    setLoading(false);
                }
            }
        };

        void loadAlerts();
        return () => {
            isActive = false;
        };
    }, []);

    if (loading) {
        return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Loading alerts...</div>;
    }

    if (error) {
        return (
            <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-8 text-red-200">
                <p className="font-semibold">Unable to load alerts.</p>
                <p className="mt-2 text-sm text-red-100/80">{error}</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <header className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                <div className="flex items-center gap-3">
                    <AlertTriangle className="text-amber-500" size={24} />
                    <h2 className="text-2xl font-semibold text-slate-100">Facility Alerts</h2>
                </div>
                <p className="mt-2 text-slate-400">Manage and investigate active facility anomalies.</p>
            </header>

            {alerts.length === 0 ? (
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400">
                    <ShieldCheck className="mx-auto mb-3 text-emerald-500" size={32} />
                    <p>No active alerts. Facility is operating normally.</p>
                </div>
            ) : (
                <div className="grid gap-4">
                    {alerts.map((alert) => (
                        <div key={alert.id} className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:flex-row md:items-center md:justify-between">
                            <div className="space-y-2">
                                <div className="flex items-center gap-3">
                                    <span
                                        className={`rounded-full px-2 py-1 text-xs font-semibold tracking-wide ${alert.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                                            alert.severity === 'WARNING' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                                                'bg-slate-700/50 text-slate-300 border border-slate-700'
                                            }`}
                                    >
                                        {alert.severity}
                                    </span>
                                    <span className="text-lg font-semibold text-slate-200">{alert.alert_type.replace(/_/g, ' ')}</span>
                                    <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-400 uppercase">
                                        Asset ID: {alert.asset_id}
                                    </span>
                                </div>
                                <p className="text-slate-300">{alert.message}</p>
                                <div className="flex items-center gap-4 text-xs text-slate-400">
                                    <span className="flex items-center gap-1">
                                        <Gauge size={14} /> Anomaly Score: {alert.anomaly_score.toFixed(2)}
                                    </span>
                                    <span>Detected: {new Date(alert.detected_at).toLocaleString()}</span>
                                    <span>Status: {alert.status}</span>
                                </div>
                            </div>
                            <div className="shrink-0 pt-2 md:pt-0">
                                <Link
                                    to={`/x-ray?asset_id=${alert.asset_id}&alert_id=${alert.id}`}
                                    className="inline-flex items-center gap-2 rounded-xl bg-cyan-700/20 px-4 py-2 font-medium text-cyan-300 transition-colors hover:bg-cyan-600/30 border border-cyan-500/30"
                                >
                                    <Search size={16} />
                                    INVESTIGATE WITH X-RAY
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Alerts;
