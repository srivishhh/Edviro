import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Gauge } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime } from '../../../hooks/useRealtime';
import { useTheme } from '../../../app/ThemeProvider';

type MetricType = 'TEMPERATURE' | 'AIRFLOW' | 'PRESSURE' | 'POWER';

export const LiveTelemetryTile: React.FC = () => {
  const { telemetryHistory, currentTelemetry } = useRealtime();
  const { theme } = useTheme();
  const [activeMetric, setActiveMetric] = useState<MetricType>('AIRFLOW');

  const metricConfig = {
    TEMPERATURE: { key: 'temperature', label: 'Temperature', unit: '°C', color: '#F25912' },
    AIRFLOW: { key: 'airflow', label: 'Airflow', unit: '%', color: '#5C3E94' },
    PRESSURE: { key: 'pressure', label: 'Static Pressure', unit: 'in.wg', color: '#8b5cf6' },
    POWER: { key: 'power', label: 'Energy Load', unit: 'kW', color: '#10b981' },
  };

  const currentConfig = metricConfig[activeMetric];

  const chartData = telemetryHistory.length > 0 ? telemetryHistory : [
    { timestamp: '09:40', temperature: 23.5, airflow: 78.5, pressure: 3.8, power: 11.2 },
    { timestamp: '09:41', temperature: 23.8, airflow: 77.0, pressure: 3.85, power: 11.4 },
    { timestamp: '09:42', temperature: 24.1, airflow: 75.2, pressure: 3.9, power: 11.6 },
    { timestamp: '09:43', temperature: 24.5, airflow: 72.0, pressure: 3.95, power: 11.9 },
  ];

  const currentValue = currentTelemetry
    ? currentTelemetry[currentConfig.key as keyof typeof currentTelemetry]
    : chartData[chartData.length - 1][currentConfig.key as keyof typeof chartData[0]];

  return (
    <BentoTile span="col-span-1 md:col-span-2" variant="translucent" className="flex flex-col justify-between">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Gauge size={16} className="text-[#5C3E94] dark:text-purple-300" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">LIVE TELEMETRY STREAM</span>
          <span className="rounded-lg bg-[#5C3E94]/15 px-2 py-0.5 text-[11px] text-[#5C3E94] dark:text-purple-300 font-mono font-medium border border-[#5C3E94]/30">
            AHU-007 • LBNL
          </span>
        </div>

        {/* Metric Selector Buttons */}
        <div className="flex items-center gap-1 rounded-xl bg-[var(--bg-surface)] p-1 border border-[var(--border-subtle)]">
          {(['TEMPERATURE', 'AIRFLOW', 'PRESSURE', 'POWER'] as MetricType[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setActiveMetric(m)}
              className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold tracking-tight transition-all ${
                activeMetric === m
                  ? 'bg-[#5C3E94] text-white shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-primary)]/50'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Primary Value Readout */}
      <div className="my-2 flex items-baseline gap-2">
        <span className="text-3xl font-extrabold tracking-tight text-[var(--text-main)] font-mono">{currentValue}</span>
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">{currentConfig.unit}</span>
      </div>

      {/* Chart */}
      <div className="h-32 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id={`color-${activeMetric}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={currentConfig.color} stopOpacity={theme === 'dark' ? 0.4 : 0.25} />
                <stop offset="95%" stopColor={currentConfig.color} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="timestamp" stroke={theme === 'dark' ? '#94a3b8' : '#7f7c8d'} fontSize={10} tickLine={false} />
            <YAxis stroke={theme === 'dark' ? '#94a3b8' : '#7f7c8d'} fontSize={10} tickLine={false} domain={['dataMin - 2', 'dataMax + 2']} />
            <Tooltip
              contentStyle={{
                backgroundColor: theme === 'dark' ? '#211832' : '#ffffff',
                borderColor: theme === 'dark' ? 'rgba(92, 62, 148, 0.4)' : 'rgba(92, 62, 148, 0.2)',
                color: theme === 'dark' ? '#f8fafc' : '#181126',
                borderRadius: '12px',
                fontSize: '12px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
              }}
            />
            <Area
              type="monotone"
              dataKey={currentConfig.key}
              stroke={currentConfig.color}
              strokeWidth={2.5}
              fillOpacity={1}
              fill={`url(#color-${activeMetric})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </BentoTile>
  );
};
