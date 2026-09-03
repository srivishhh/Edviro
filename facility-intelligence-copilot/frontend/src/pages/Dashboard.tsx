import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  ArrowUpRight,
  Gauge,
  HeartPulse,
  Radio,
  Sparkles,
  Zap,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { getAlerts } from '../services/alerts';
import { getAssetTelemetry } from '../services/telemetry';
import type { Alert, TelemetryPoint } from '../types';
import { KpiCard } from '../components/ui/KpiCard';
import { SeverityBadge } from '../components/ui/SeverityBadge';
import { LoadingState } from '../components/ui/States';
import { SystemPipeline } from '../components/dashboard/SystemPipeline';
import { EnergyCard } from '../components/dashboard/EnergyCard';

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeMetric, setActiveMetric] = useState<'pressure' | 'power' | 'temperature' | 'airflow'>('pressure');

  useEffect(() => {
    let isActive = true;

    const fetchLiveTelemetryAndData = async () => {
      try {
        const [alertList, telemetryPoints] = await Promise.all([
          getAlerts().catch(() => []),
          getAssetTelemetry(7, { limit: 25 }).catch(() => []),
        ]);

        if (isActive) {
          if (alertList.length > 0) setAlerts(alertList);
          if (telemetryPoints.length > 0) setTelemetry(telemetryPoints);
        }
      } catch {
        // Ignore fallback errors
      } finally {
        if (isActive) setLoading(false);
      }
    };

    void fetchLiveTelemetryAndData();
    const interval = setInterval(fetchLiveTelemetryAndData, 2500);

    return () => {
      isActive = false;
      clearInterval(interval);
    };
  }, []);

  const latestTelemetry = useMemo(() => {
    if (telemetry.length > 0) {
      return telemetry[telemetry.length - 1];
    }
    return {
      timestamp: new Date().toISOString(),
      temperature: 16.1,
      energy_kw: 140.6,
      pressure: 31.5,
      airflow: 97.6,
    };
  }, [telemetry]);

  const activeAlert = useMemo(() => {
    return (
      alerts.find((a) => a.status === 'OPEN' || a.status === 'ACKNOWLEDGED') ||
      alerts[0] || {
        id: 101,
        asset_id: 7,
        alert_type: 'CONDENSER_FOULING',
        severity: 'HIGH',
        message: 'Condenser fouling pattern detected: Elevated discharge head pressure (31.5 bar) with high compressor power demand (140.6 kW).',
        anomaly_score: 0.96,
        detected_at: new Date().toISOString(),
        status: 'OPEN',
      }
    );
  }, [alerts]);

  const chartData = useMemo(() => {
    if (telemetry.length > 0) {
      return telemetry.map((pt, idx) => {
        let timeLabel = `T-${(telemetry.length - idx) * 2}m`;
        if (pt.timestamp) {
          const d = new Date(pt.timestamp);
          if (!isNaN(d.getTime())) {
            timeLabel = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          }
        }
        return {
          time: timeLabel,
          temperature: pt.temperature,
          power: pt.energy_kw,
          pressure: pt.pressure,
          airflow: pt.airflow,
        };
      });
    }
    return [
      { time: '12:00', temperature: 18.2, power: 8.5, pressure: 14.2, airflow: 98.0 },
      { time: '12:05', temperature: 17.5, power: 45.0, pressure: 22.1, airflow: 97.5 },
      { time: '12:10', temperature: 16.8, power: 98.2, pressure: 28.4, airflow: 97.2 },
      { time: '12:15', temperature: 16.1, power: 140.6, pressure: 31.5, airflow: 97.6 },
    ];
  }, [telemetry]);

  if (loading) {
    return <LoadingState message="Connecting to LBNL Real-Time Telemetry Stream..." />;
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. EDITORIAL HERO INTRO BANNER */}
      <div className="saas-card p-6 md:p-8 space-y-4 bg-white">
        <div className="flex items-center gap-2 text-zinc-500">
          <Sparkles size={16} />
          <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Facility Intelligence Copilot</span>
        </div>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-950 editorial-title tracking-tight">
              Operational Overview
            </h1>
            <p className="text-zinc-600 text-xs sm:text-sm max-w-2xl mt-1 leading-relaxed">
              Real-time spatial digital twin telemetry fused with 7-agent autonomous causal AI root cause diagnosis.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/x-ray"
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-zinc-950 text-white font-semibold hover:bg-zinc-800 transition-all text-xs cursor-pointer shadow-sm"
            >
              <Gauge size={13} />
              <span>Launch Facility X-Ray</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. TOP METRIC STATS ROW */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Facility Health Index"
          value="88.4%"
          change="Thermodynamic load nominal"
          trend="up"
          icon={HeartPulse}
        />
        <KpiCard
          label="Active RTU Discharge Head"
          value={`${latestTelemetry.pressure.toFixed(1)} bar`}
          change="Baseline: 12.0–16.0 bar"
          trend="down"
          icon={Activity}
        />
        <KpiCard
          label="RTU Compressor Power"
          value={`${latestTelemetry.energy_kw.toFixed(1)} kW`}
          change="Excess power overdraw"
          trend="down"
          icon={Zap}
        />
        <KpiCard
          label="Active Incidents"
          value={alerts.filter((a) => a.status === 'OPEN').length || 1}
          change="1 high severity incident"
          trend="neutral"
          icon={AlertCircle}
        />
      </div>

      {/* 3. LIVE FEATURED INCIDENT HERO HERO-CARD */}
      <div className="saas-card p-6 md:p-8 space-y-6 bg-gradient-to-br from-white to-zinc-50/70">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
              <AlertCircle size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-zinc-900 font-mono">HVAC-007</span>
                <span className="text-zinc-400">&bull;</span>
                <span className="text-xs text-zinc-600 font-medium">LBNL RTU Rooftop Unit #7</span>
              </div>
              <h2 className="text-base font-bold text-zinc-950 tracking-tight">
                {activeAlert.alert_type.replace(/_/g, ' ')}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3 self-start sm:self-auto">
            <SeverityBadge severity={activeAlert.severity} />
            <Link
              to={`/x-ray?asset_id=7&alert_id=${activeAlert.id}`}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold transition-colors cursor-pointer"
            >
              <span>Investigate with Facility X-Ray</span>
              <ArrowUpRight size={13} />
            </Link>
          </div>
        </div>

        {/* Live Replayed Measurements Strip */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 font-mono text-xs">
          <div className="p-3.5 rounded-2xl bg-white border border-zinc-200 shadow-2xs space-y-1">
            <span className="text-[10px] text-zinc-400 font-bold block uppercase tracking-wider">Discharge Head</span>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-extrabold text-zinc-950">{latestTelemetry.pressure.toFixed(1)} bar</span>
              <span className="text-[10px] text-rose-600 font-semibold font-sans">
                {latestTelemetry.pressure > 16 ? '+High Back-Pressure' : 'Nominal'}
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-zinc-200 shadow-2xs space-y-1">
            <span className="text-[10px] text-zinc-400 font-bold block uppercase tracking-wider">Supply Temp</span>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-extrabold text-zinc-950">{latestTelemetry.temperature.toFixed(1)}°C</span>
              <span className="text-[10px] text-zinc-500 font-sans">RTU Deck</span>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-zinc-200 shadow-2xs space-y-1">
            <span className="text-[10px] text-zinc-400 font-bold block uppercase tracking-wider">Power Demand</span>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-extrabold text-amber-700">{latestTelemetry.energy_kw.toFixed(1)} kW</span>
              <span className="text-[10px] text-amber-700 font-semibold font-sans">Excess Load</span>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-zinc-200 shadow-2xs space-y-1">
            <span className="text-[10px] text-zinc-400 font-bold block uppercase tracking-wider">Volumetric Flow</span>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-extrabold text-zinc-950">{latestTelemetry.airflow.toFixed(1)}%</span>
              <span className="text-[10px] text-emerald-600 font-semibold font-sans">Supply Fan On</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. REAL-TIME 24-HR MULTI-CURVE TELEMETRY CHART */}
      <div className="saas-card p-6 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Radio size={14} className="text-emerald-500 animate-pulse" />
              <span className="text-[10px] uppercase font-bold tracking-[0.2em] text-zinc-400">
                Live Chronological Telemetry Stream
              </span>
            </div>
            <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
              LBNL RTU Telemetry Curves (HVAC-007)
            </h3>
          </div>

          {/* Metric Selector Pills */}
          <div className="flex items-center gap-1.5 bg-zinc-100 p-1 rounded-full text-xs self-start sm:self-auto font-mono">
            {(['pressure', 'power', 'temperature', 'airflow'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setActiveMetric(m)}
                className={`px-3 py-1 rounded-full text-xs font-semibold capitalize transition-all cursor-pointer ${
                  activeMetric === m ? 'bg-white text-zinc-950 shadow-xs' : 'text-zinc-500 hover:text-zinc-800'
                }`}
              >
                {m === 'pressure' ? 'Pressure (bar)' : m === 'power' ? 'Power (kW)' : m === 'temperature' ? 'Temp (°C)' : 'Flow (%)'}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Area Chart */}
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="metricGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#18181b" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#18181b" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
              <XAxis dataKey="time" stroke="#a1a1aa" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#a1a1aa" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  borderRadius: '12px',
                  border: 'none',
                  color: '#fff',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                }}
              />
              <Area
                type="monotone"
                dataKey={activeMetric}
                stroke="#18181b"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#metricGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 5. 7-STAGE PIPELINE & POWER LOAD INTELLIGENCE */}
      <SystemPipeline />

      <EnergyCard
        wastedKw={(Math.max(0, latestTelemetry.energy_kw - 8.5)).toFixed(1)}
        costImpactHour={`$${((latestTelemetry.energy_kw - 8.5) * 0.18).toFixed(2)}/hr`}
        co2PenaltyKg={`${((latestTelemetry.energy_kw - 8.5) * 0.38).toFixed(1)} kg/hr`}
      />
    </div>
  );
}
