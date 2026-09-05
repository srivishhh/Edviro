import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  ArrowUpRight,
  Clock,
  Network,
  Sparkles,
} from 'lucide-react';
import { getAlerts, updateAlertStatus } from '../services/alerts';
import type { Alert } from '../types';
import { SeverityBadge } from '../components/ui/SeverityBadge';
import { LoadingState, EmptyState } from '../components/ui/States';
import { useToast } from '../context/ToastContext';

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const { showToast } = useToast();

  const loadAlerts = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const data = await getAlerts();
      if (data && data.length > 0) {
        setAlerts(data);
      }
    } catch {
      // Fallback
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    void loadAlerts(false);
    const interval = setInterval(() => void loadAlerts(true), 2500);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const handleStatusChange = async (alertId: number, newStatus: string) => {
    try {
      await updateAlertStatus(alertId, newStatus);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: newStatus } : a))
      );
      showToast('success', 'Incident Status Updated', `Alert #${alertId} marked as ${newStatus}.`);
    } catch {
      showToast('error', 'Update Failed', 'Could not update alert status.');
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    const matchesSev = severityFilter === 'ALL' || a.severity.toUpperCase() === severityFilter;
    const matchesStat = statusFilter === 'ALL' || a.status.toUpperCase() === statusFilter;
    return matchesSev && matchesStat;
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="saas-card p-6 md:p-8 space-y-3 bg-white">
        <div className="flex items-center gap-2 text-zinc-500">
          <AlertCircle size={16} />
          <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Incident Stream</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-950 editorial-title tracking-tight">
          Facility Alerts & Anomaly Feed
        </h1>
        <p className="text-zinc-600 text-xs sm:text-sm max-w-2xl leading-relaxed">
          Chronological event feed of real-time thermodynamic, physical airflow, and electrical anomalies detected across monitored facility infrastructure.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="saas-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Severity Filter Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-zinc-400 text-xs font-mono">Severity:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'WARNING', 'INFO'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                severityFilter === sev
                  ? 'bg-zinc-900 text-white font-semibold'
                  : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Status Filter Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-zinc-400 text-xs font-mono">Status:</span>
          {['ALL', 'OPEN', 'ACKNOWLEDGED', 'RESOLVED'].map((stat) => (
            <button
              key={stat}
              onClick={() => setStatusFilter(stat)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                statusFilter === stat
                  ? 'bg-zinc-900 text-white font-semibold'
                  : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              {stat}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Feed List */}
      <div className="space-y-4">
        {loading ? (
          <LoadingState message="Fetching live incident alert feed..." />
        ) : filteredAlerts.length === 0 ? (
          <EmptyState message="No incident alerts matching selected criteria." />
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className="saas-card p-6 space-y-4 bg-white hover:border-zinc-300 transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-xs font-bold text-zinc-900 bg-zinc-100 px-2 py-0.5 rounded border border-zinc-200">
                    HVAC-{String(alert.asset_id).padStart(3, '0')}
                  </span>
                  <SeverityBadge severity={alert.severity} />
                  <span className="text-zinc-400">&bull;</span>
                  <span className="text-xs font-mono text-zinc-500">
                    Anomaly Score: {(alert.anomaly_score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="flex items-center gap-2 font-mono text-[11px] text-zinc-400">
                  <Clock size={12} />
                  <span>{alert.detected_at}</span>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold text-zinc-900 tracking-tight">
                  {alert.alert_type.replace(/_/g, ' ')}
                </h3>
                <p className="text-xs text-zinc-600 mt-1 leading-relaxed">{alert.message}</p>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                {/* State selector */}
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-zinc-400 font-mono">Status:</span>
                  <select
                    value={alert.status}
                    onChange={(e) => void handleStatusChange(alert.id, e.target.value)}
                    className="bg-zinc-50 border border-zinc-200 rounded-lg px-2.5 py-1 text-xs text-zinc-800 font-mono focus:outline-none focus:border-zinc-400 cursor-pointer"
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="DISMISSED">DISMISSED</option>
                  </select>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <Link
                    to={`/incident-graph?incident_id=${alert.id}`}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-cyan-50 hover:bg-cyan-100 border border-cyan-300 text-cyan-950 text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Network size={12} className="text-cyan-700" />
                    <span>Relationship Graph</span>
                  </Link>

                  <Link
                    to={`/x-ray?asset_id=${alert.asset_id}&alert_id=${alert.id}`}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Sparkles size={12} />
                    <span>Causal X-Ray</span>
                    <ArrowUpRight size={12} />
                  </Link>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
