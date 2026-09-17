import React, { useState, useMemo } from 'react';
import { Gauge, Activity } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime, type TelemetryData } from '../../../hooks/useRealtime';
import { useTheme } from '../../../app/ThemeProvider';
import {
  LiveLineChart,
  LiveLine,
  LiveXAxis,
  LiveYAxis,
  type LiveLinePoint,
} from '../../../components/charts';

type MetricType = 'TEMPERATURE' | 'AIRFLOW' | 'PRESSURE' | 'POWER';

export const LiveTelemetryTile: React.FC = () => {
  const { telemetryHistory, currentTelemetry, replayState } = useRealtime();
  const { theme } = useTheme();
  const [activeMetric, setActiveMetric] = useState<MetricType>('AIRFLOW');

  const metricConfig = {
    TEMPERATURE: { key: 'temperature', label: 'Temperature', unit: '°C', color: '#F25912', yMin: 18, yMax: 32 },
    AIRFLOW: {
      key: 'airflow',
      label: 'Airflow',
      unit: '%',
      color: theme === 'dark' ? '#a78bfa' : '#5C3E94',
      yMin: 40,
      yMax: 100,
    },
    PRESSURE: { key: 'pressure', label: 'Static Pressure', unit: 'in.wg', color: '#06b6d4', yMin: 2.5, yMax: 5.0 },
    POWER: { key: 'power', label: 'Energy Load', unit: 'kW', color: '#10b981', yMin: 5, yMax: 20 },
  };

  const currentConfig = metricConfig[activeMetric];

  // Map LBNL telemetry data into streaming time-series points
  const chartData: LiveLinePoint[] = useMemo(() => {
    const nowSec = Math.floor(Date.now() / 1000);
    if (!telemetryHistory || telemetryHistory.length === 0) {
      const defaultVal =
        activeMetric === 'TEMPERATURE'
          ? 23.5
          : activeMetric === 'AIRFLOW'
          ? 78.5
          : activeMetric === 'PRESSURE'
          ? 3.8
          : 11.2;
      return Array.from({ length: 15 }, (_, i) => ({
        time: nowSec - (15 - i) * 2,
        value: defaultVal + Math.sin(i * 0.8) * 0.4,
      }));
    }

    const count = telemetryHistory.length;
    return telemetryHistory.map((item, idx) => {
      const timeOffset = (count - 1 - idx) * 2;
      const rawVal = Number(item[currentConfig.key as keyof TelemetryData]);
      const value = isNaN(rawVal) ? 0 : rawVal;
      return {
        time: nowSec - timeOffset,
        value,
      };
    });
  }, [telemetryHistory, activeMetric, currentConfig.key]);

  // Current value for real-time smooth interpolation
  const currentValue = useMemo(() => {
    if (currentTelemetry && currentTelemetry[currentConfig.key as keyof TelemetryData] !== undefined) {
      const raw = Number(currentTelemetry[currentConfig.key as keyof TelemetryData]);
      if (!isNaN(raw)) return raw;
    }
    if (chartData.length > 0) {
      return chartData[chartData.length - 1].value;
    }
    return 0;
  }, [currentTelemetry, currentConfig.key, chartData]);

  return (
    <BentoTile span="col-span-1 md:col-span-2" variant="translucent" className="flex flex-col justify-between">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#5C3E94]/15 border border-[#5C3E94]/30 text-[#5C3E94] dark:text-purple-300">
            <Gauge size={15} />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                LIVE TELEMETRY STREAM
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-[#5C3E94]/15 px-2 py-0.5 text-[10px] text-[#5C3E94] dark:text-purple-300 font-mono font-semibold border border-[#5C3E94]/30">
                <Activity size={10} className="animate-pulse" />
                AHU-007 • LBNL
              </span>
            </div>
            <span className="text-[10px] text-[var(--text-dim)] font-mono">
              Dataset Row: #{replayState.current_row.toLocaleString()} • Time: {replayState.source_time}
            </span>
          </div>
        </div>

        {/* Metric Selector Tabs */}
        <div className="flex items-center gap-1 rounded-xl bg-[var(--bg-surface)] p-1 border border-[var(--border-subtle)] shadow-xs">
          {(['TEMPERATURE', 'AIRFLOW', 'PRESSURE', 'POWER'] as MetricType[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setActiveMetric(m)}
              className={`rounded-lg px-2.5 py-1 text-[11px] font-bold tracking-tight transition-all duration-200 cursor-pointer ${
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

      {/* Primary Telemetry Value Display */}
      <div className="my-2 flex items-baseline gap-2">
        <span className="text-3xl sm:text-4xl font-black tracking-tight text-[var(--text-main)] font-mono">
          {typeof currentValue === 'number' ? currentValue.toFixed(1) : currentValue}
        </span>
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
          {currentConfig.unit}
        </span>
        <span className="ml-2 text-xs font-semibold text-[var(--text-dim)]">
          ({currentConfig.label})
        </span>
      </div>

      {/* Bklit / Shadcn Live Line Chart */}
      <div className="w-full relative h-[180px] mt-1 rounded-xl overflow-hidden bg-[var(--bg-surface)]/40 border border-[var(--border-subtle)] p-1">
        <LiveLineChart
          data={chartData}
          value={currentValue}
          dataKey="value"
          window={30}
          numXTicks={5}
          lerpSpeed={0.12}
          paused={replayState.status === 'PAUSED'}
          margin={{ top: 16, right: 24, bottom: 24, left: 42 }}
          style={{ height: 172 }}
          className="w-full"
        >
          <LiveLine
            dataKey="value"
            stroke={currentConfig.color}
            strokeWidth={2.5}
            fill={true}
            pulse={true}
            dotSize={4.5}
            badge={true}
            formatValue={(v) => `${v.toFixed(1)} ${currentConfig.unit}`}
          />
          <LiveXAxis
            numTicks={5}
            formatTime={(t) => {
              const d = new Date(t);
              return `${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
            }}
          />
          <LiveYAxis minGap={28} formatValue={(v) => v.toFixed(1)} />
        </LiveLineChart>
      </div>
    </BentoTile>
  );
};
