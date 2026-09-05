import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Activity,
  CheckCircle2,
  Flame,
  Info,
  Layers,
  Lightbulb,
  Loader2,
  Play,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Wind,
  Zap,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { getAssets } from '../services/assets';
import {
  getWhatIfPresets,
  simulateWhatIf,
  type WhatIfParameterChanges,
  type WhatIfPreset,
  type WhatIfSimulateResponse,
} from '../services/whatif';
import type { Asset } from '../types';

export default function WhatIf() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialAssetId = searchParams.get('assetId') || 'HVAC-007';

  // Assets and Presets state
  const [assets, setAssets] = useState<Asset[]>([]);
  const [presets, setPresets] = useState<WhatIfPreset[]>([]);
  const [selectedAssetId, setSelectedAssetId] = useState<string>(initialAssetId);
  const [activePresetId, setActivePresetId] = useState<string | null>(null);

  // Proposed parameters (interactive controls)
  const [proposedTemp, setProposedTemp] = useState<number>(24.0);
  const [proposedPress, setProposedPress] = useState<number>(3.8);
  const [proposedFlow, setProposedFlow] = useState<number>(95.0);
  const [proposedEnergy, setProposedEnergy] = useState<number | null>(null);
  const [autoCalculateEnergy, setAutoCalculateEnergy] = useState<boolean>(true);

  // Simulation execution state
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<WhatIfSimulateResponse | null>(null);
  const [simulationError, setSimulationError] = useState<string | null>(null);

  // Secondary scenario for Side-by-Side Comparison Mode
  const [comparisonMode, setComparisonMode] = useState<boolean>(false);
  const [scenarioBResult, setScenarioBResult] = useState<WhatIfSimulateResponse | null>(null);
  const [scenarioBFlow, setScenarioBFlow] = useState<number>(105.0);
  const [simulatingB, setSimulatingB] = useState<boolean>(false);

  // Load available assets and scenario presets on mount
  useEffect(() => {
    let isActive = true;

    async function initData() {
      try {
        const [assetList, presetList] = await Promise.all([
          getAssets().catch(() => []),
          getWhatIfPresets().catch(() => []),
        ]);

        if (isActive) {
          if (assetList.length > 0) setAssets(assetList);
          if (presetList.length > 0) setPresets(presetList);
        }
      } catch {
        // Fallback gracefully
      }
    }

    void initData();
    return () => {
      isActive = false;
    };
  }, []);

  // Sync with URL query parameter
  useEffect(() => {
    const paramId = searchParams.get('assetId');
    if (paramId && paramId !== selectedAssetId) {
      setSelectedAssetId(paramId);
    }
  }, [searchParams]);

  // Execute simulation when asset or manual "Run Simulation" is triggered
  const handleRunSimulation = async (
    targetAsset: string = selectedAssetId,
    customChanges?: WhatIfParameterChanges,
    presetId?: string
  ) => {
    setSimulating(true);
    setSimulationError(null);

    const changes: WhatIfParameterChanges = customChanges || {
      temperature: proposedTemp,
      pressure: proposedPress,
      airflow: proposedFlow,
      ...(autoCalculateEnergy ? {} : { energy_kw: proposedEnergy ?? undefined }),
    };

    try {
      const res = await simulateWhatIf({
        asset_id: targetAsset,
        changes,
        scenario_preset: presetId || activePresetId || undefined,
      });
      setSimulationResult(res);
    } catch (err) {
      setSimulationError(err instanceof Error ? err.message : 'Simulation run failed.');
    } finally {
      setSimulating(false);
    }
  };

  // Run initial simulation for selected asset on change
  useEffect(() => {
    void handleRunSimulation(selectedAssetId);
  }, [selectedAssetId]);

  // Handle Preset selection
  const handleSelectPreset = (preset: WhatIfPreset) => {
    setActivePresetId(preset.id);

    if (preset.changes.temperature !== undefined) setProposedTemp(preset.changes.temperature);
    if (preset.changes.pressure !== undefined) setProposedPress(preset.changes.pressure);
    if (preset.changes.airflow !== undefined) setProposedFlow(preset.changes.airflow);

    if (preset.changes.energy_kw !== undefined) {
      setProposedEnergy(preset.changes.energy_kw);
      setAutoCalculateEnergy(false);
    } else {
      setAutoCalculateEnergy(true);
      setProposedEnergy(null);
    }

    void handleRunSimulation(selectedAssetId, preset.changes, preset.id);
  };

  // Reset to live current asset values
  const handleReset = () => {
    setActivePresetId(null);
    setAutoCalculateEnergy(true);
    setProposedEnergy(null);

    if (simulationResult) {
      setProposedTemp(simulationResult.current.temperature);
      setProposedPress(simulationResult.current.pressure);
      setProposedFlow(simulationResult.current.airflow);
      void handleRunSimulation(selectedAssetId, {
        temperature: simulationResult.current.temperature,
        pressure: simulationResult.current.pressure,
        airflow: simulationResult.current.airflow,
      });
    }
  };

  // Handle run for Comparison Mode (Scenario B)
  const handleRunScenarioB = async () => {
    setSimulatingB(true);
    try {
      const res = await simulateWhatIf({
        asset_id: selectedAssetId,
        changes: {
          airflow: scenarioBFlow,
          temperature: Math.max(20.0, proposedTemp - 1.5),
        },
        scenario_preset: 'Scenario B (High Flow Target)',
      });
      setScenarioBResult(res);
    } catch (err) {
      // Ignore
    } finally {
      setSimulatingB(false);
    }
  };

  // Format Recharts data comparing Current vs Predicted
  const chartData = useMemo(() => {
    if (!simulationResult) return [];

    const curr = simulationResult.current;
    const pred = simulationResult.predicted;

    return [
      {
        metric: 'Energy (kW)',
        Current: curr.energy_kw,
        Predicted: pred.energy_kw,
        unit: 'kW',
      },
      {
        metric: 'Health (%)',
        Current: curr.health,
        Predicted: pred.health,
        unit: '%',
      },
      {
        metric: 'Risk (%)',
        Current: curr.risk,
        Predicted: pred.risk,
        unit: '%',
      },
    ];
  }, [simulationResult]);

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'LOW':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'MODERATE':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'HIGH':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      default:
        return 'bg-zinc-100 text-zinc-700 border-zinc-200';
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* 1. Header Banner & Decision Support Sandbox Notice */}
      <div className="saas-card p-6 md:p-8 space-y-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-zinc-500">
            <SlidersHorizontal size={16} />
            <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Decision-Support Modeling</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-950 editorial-title tracking-tight">
            What-If Simulator
          </h1>
          <p className="text-zinc-600 text-xs sm:text-sm max-w-2xl leading-relaxed">
            Simulate hypothetical operational changes, airflow adjustments, and setpoint modifications before applying them to the physical facility. Completely isolated and safe.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="px-3.5 py-2 rounded-2xl bg-emerald-50/80 border border-emerald-200 text-emerald-900 text-xs flex items-center gap-2">
            <ShieldCheck size={15} className="text-emerald-600 shrink-0" />
            <div>
              <span className="font-bold block text-[11px] leading-tight">Zero-Risk Sandbox</span>
              <span className="text-[10px] text-emerald-700 block leading-tight">Live telemetry & BMS untouched</span>
            </div>
          </div>

          <button
            onClick={() => setComparisonMode(!comparisonMode)}
            className={`px-4 py-2.5 rounded-full text-xs font-semibold cursor-pointer transition-all flex items-center gap-1.5 border ${
              comparisonMode
                ? 'bg-zinc-950 text-white border-zinc-950 shadow-sm'
                : 'bg-white text-zinc-700 border-zinc-200 hover:bg-zinc-50'
            }`}
          >
            <Layers size={13} />
            <span>{comparisonMode ? 'Single Mode' : 'Scenario Compare'}</span>
          </button>
        </div>
      </div>

      {/* 2. Asset Selector & Scenario Presets */}
      <div className="saas-card p-6 md:p-8 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
          <div className="space-y-1">
            <span className="text-[10px] uppercase tracking-wider font-mono text-zinc-400 font-bold">Scope</span>
            <h2 className="text-base font-bold text-zinc-900">Target Asset & Operating Presets</h2>
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-zinc-600">Select Equipment:</label>
            <select
              value={selectedAssetId}
              onChange={(e) => {
                const val = e.target.value;
                setSelectedAssetId(val);
                setSearchParams({ assetId: val });
              }}
              className="bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 text-xs font-semibold text-zinc-900 focus:outline-none focus:border-zinc-500 cursor-pointer shadow-2xs"
            >
              {assets.length > 0 ? (
                assets.map((a) => (
                  <option key={a.id} value={a.asset_code}>
                    {a.asset_code} &mdash; {a.name}
                  </option>
                ))
              ) : (
                <>
                  <option value="HVAC-007">HVAC-007 (Floor 2 AHU / LBNL RTU Unit)</option>
                  <option value="HVAC-001">HVAC-001 (Ground Floor East Auditorium)</option>
                  <option value="HVAC-002">HVAC-002 (Ground Floor West)</option>
                  <option value="HVAC-003">HVAC-003 (Floor 1 East)</option>
                  <option value="CHILLER-001">CHILLER-001 (Primary Chiller)</option>
                  <option value="CHILLER-002">CHILLER-002 (Secondary Chiller)</option>
                  <option value="HEATPUMP-001">HEATPUMP-001 (Main Heat Pump)</option>
                </>
              )}
            </select>
          </div>
        </div>

        {/* Preset Selector Chips */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-zinc-700 block">Scenario Presets:</span>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {presets.map((preset) => {
              const isSelected = activePresetId === preset.id;
              return (
                <button
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset)}
                  className={`text-left p-3 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-2 ${
                    isSelected
                      ? 'bg-zinc-900 text-white border-zinc-900 shadow-sm'
                      : 'bg-zinc-50/70 border-zinc-200/80 text-zinc-800 hover:border-zinc-300 hover:bg-zinc-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold leading-tight">{preset.name}</span>
                    <Sparkles size={13} className={isSelected ? 'text-amber-300' : 'text-zinc-400'} />
                  </div>
                  <p className={`text-[11px] leading-relaxed line-clamp-2 ${isSelected ? 'text-zinc-300' : 'text-zinc-500'}`}>
                    {preset.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. Interactive Parameters Workbench */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Controls Column (Left, 5 cols) */}
        <div className="lg:col-span-5 saas-card p-6 md:p-8 space-y-6 flex flex-col justify-between">
          <div className="space-y-5">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="flex items-center gap-2">
                <SlidersHorizontal size={16} className="text-zinc-700" />
                <h3 className="text-sm font-bold text-zinc-900">Virtual Operating Sliders</h3>
              </div>
              <button
                onClick={handleReset}
                className="flex items-center gap-1 text-[11px] text-zinc-500 hover:text-zinc-900 font-semibold cursor-pointer transition-colors"
                title="Reset to current live telemetry"
              >
                <RotateCcw size={12} />
                <span>Reset Baseline</span>
              </button>
            </div>

            {/* Slider 1: Temperature */}
            <div className="space-y-2 bg-zinc-50 p-3.5 rounded-2xl border border-zinc-200/70">
              <div className="flex items-center justify-between text-xs">
                <label className="font-semibold text-zinc-800 flex items-center gap-1.5">
                  <Flame size={14} className="text-amber-600" />
                  <span>Supply Temperature</span>
                </label>
                <div className="flex items-center gap-1 font-mono text-xs">
                  <span className="text-zinc-400 text-[10px]">Current: {simulationResult?.current.temperature ?? '--'}°C</span>
                  <span className="font-bold text-zinc-900 bg-white px-2 py-0.5 rounded-md border border-zinc-200">
                    {proposedTemp.toFixed(1)} °C
                  </span>
                </div>
              </div>
              <input
                type="range"
                min="16.0"
                max="36.0"
                step="0.2"
                value={proposedTemp}
                onChange={(e) => {
                  setProposedTemp(parseFloat(e.target.value));
                  setActivePresetId(null);
                }}
                className="w-full accent-zinc-900 cursor-pointer h-1.5 bg-zinc-200 rounded-lg appearance-none"
              />
              <div className="flex justify-between text-[10px] text-zinc-400 font-mono">
                <span>16.0°C (Chilled)</span>
                <span className="text-emerald-700 font-semibold">22–26°C (Target)</span>
                <span>36.0°C (Thermal Stress)</span>
              </div>
            </div>

            {/* Slider 2: Airflow */}
            <div className="space-y-2 bg-zinc-50 p-3.5 rounded-2xl border border-zinc-200/70">
              <div className="flex items-center justify-between text-xs">
                <label className="font-semibold text-zinc-800 flex items-center gap-1.5">
                  <Wind size={14} className="text-sky-600" />
                  <span>Airflow Velocity / Rate</span>
                </label>
                <div className="flex items-center gap-1 font-mono text-xs">
                  <span className="text-zinc-400 text-[10px]">Current: {simulationResult?.current.airflow ?? '--'}%</span>
                  <span className="font-bold text-zinc-900 bg-white px-2 py-0.5 rounded-md border border-zinc-200">
                    {proposedFlow.toFixed(0)} %
                  </span>
                </div>
              </div>
              <input
                type="range"
                min="35.0"
                max="125.0"
                step="1.0"
                value={proposedFlow}
                onChange={(e) => {
                  setProposedFlow(parseFloat(e.target.value));
                  setActivePresetId(null);
                }}
                className="w-full accent-zinc-900 cursor-pointer h-1.5 bg-zinc-200 rounded-lg appearance-none"
              />
              <div className="flex justify-between text-[10px] text-zinc-400 font-mono">
                <span className="text-rose-600">35% (Restricted)</span>
                <span className="text-emerald-700 font-semibold">90–100% (Design)</span>
                <span>125% (Overdrive)</span>
              </div>
            </div>

            {/* Slider 3: Pressure */}
            <div className="space-y-2 bg-zinc-50 p-3.5 rounded-2xl border border-zinc-200/70">
              <div className="flex items-center justify-between text-xs">
                <label className="font-semibold text-zinc-800 flex items-center gap-1.5">
                  <Activity size={14} className="text-indigo-600" />
                  <span>Discharge Pressure</span>
                </label>
                <div className="flex items-center gap-1 font-mono text-xs">
                  <span className="text-zinc-400 text-[10px]">Current: {simulationResult?.current.pressure ?? '--'} bar</span>
                  <span className="font-bold text-zinc-900 bg-white px-2 py-0.5 rounded-md border border-zinc-200">
                    {proposedPress.toFixed(1)} bar
                  </span>
                </div>
              </div>
              <input
                type="range"
                min="2.0"
                max="35.0"
                step="0.2"
                value={proposedPress}
                onChange={(e) => {
                  setProposedPress(parseFloat(e.target.value));
                  setActivePresetId(null);
                }}
                className="w-full accent-zinc-900 cursor-pointer h-1.5 bg-zinc-200 rounded-lg appearance-none"
              />
              <div className="flex justify-between text-[10px] text-zinc-400 font-mono">
                <span>2.0 bar</span>
                <span className="text-emerald-700 font-semibold">3.0–4.5 bar (Nominal)</span>
                <span className="text-rose-600">35.0 bar (RTU Peak)</span>
              </div>
            </div>

            {/* Parameter 4: Energy (kW) with auto-coupling */}
            <div className="space-y-2 bg-zinc-50 p-3.5 rounded-2xl border border-zinc-200/70 text-xs">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-zinc-800 flex items-center gap-1.5">
                  <Zap size={14} className="text-amber-500" />
                  <span>Electrical Demand</span>
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="autoEnergy"
                    checked={autoCalculateEnergy}
                    onChange={(e) => setAutoCalculateEnergy(e.target.checked)}
                    className="rounded accent-zinc-900 cursor-pointer"
                  />
                  <label htmlFor="autoEnergy" className="text-[11px] text-zinc-600 cursor-pointer">
                    Auto-Model Coupled Work
                  </label>
                </div>
              </div>

              {!autoCalculateEnergy && (
                <div className="pt-2">
                  <input
                    type="number"
                    min="1.0"
                    max="200.0"
                    step="0.5"
                    value={proposedEnergy ?? 10.0}
                    onChange={(e) => {
                      setProposedEnergy(parseFloat(e.target.value) || 0);
                      setActivePresetId(null);
                    }}
                    className="w-full bg-white border border-zinc-200 rounded-xl px-3 py-1.5 text-xs font-mono text-zinc-900"
                    placeholder="Explicit power (kW)..."
                  />
                </div>
              )}
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={() => handleRunSimulation()}
              disabled={simulating}
              className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-full bg-zinc-950 hover:bg-zinc-800 text-white font-semibold text-xs transition-all cursor-pointer shadow-md disabled:opacity-50"
            >
              {simulating ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              <span>{simulating ? 'Calculating Physics Model...' : 'Run What-If Simulation'}</span>
            </button>
          </div>
        </div>

        {/* Results & Comparison Column (Right, 7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {simulationError ? (
            <div className="p-6 rounded-3xl bg-rose-50 border border-rose-200 text-rose-900 space-y-2">
              <div className="flex items-center gap-2 font-bold text-sm">
                <ShieldAlert size={16} /> Simulation Error
              </div>
              <p className="text-xs text-rose-700">{simulationError}</p>
            </div>
          ) : simulationResult ? (
            <>
              {/* Impact Metrics Badges */}
              <div className="grid gap-3 sm:grid-cols-3">
                {/* Energy Impact Card */}
                <div className="p-4 rounded-3xl bg-white border border-zinc-200/90 shadow-2xs space-y-1">
                  <div className="flex items-center justify-between text-zinc-500 text-[11px] font-medium">
                    <span>Energy Demand</span>
                    <Zap size={14} className="text-amber-500" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold text-zinc-950 font-mono tracking-tight">
                      {simulationResult.predicted.energy_kw.toFixed(1)} kW
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] font-semibold">
                    {simulationResult.impact.energy_change_percent <= 0 ? (
                      <span className="text-emerald-700 flex items-center gap-0.5">
                        <TrendingDown size={13} /> {simulationResult.impact.energy_change_percent.toFixed(1)}% (
                        {simulationResult.impact.energy_change_kw.toFixed(1)} kW)
                      </span>
                    ) : (
                      <span className="text-rose-700 flex items-center gap-0.5">
                        <TrendingUp size={13} /> +{simulationResult.impact.energy_change_percent.toFixed(1)}% (+
                        {simulationResult.impact.energy_change_kw.toFixed(1)} kW)
                      </span>
                    )}
                  </div>
                </div>

                {/* Health Impact Card */}
                <div className="p-4 rounded-3xl bg-white border border-zinc-200/90 shadow-2xs space-y-1">
                  <div className="flex items-center justify-between text-zinc-500 text-[11px] font-medium">
                    <span>Predicted Health</span>
                    <ShieldCheck size={14} className="text-emerald-600" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold text-zinc-950 font-mono tracking-tight">
                      {simulationResult.predicted.health.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] font-semibold">
                    {simulationResult.impact.health_change >= 0 ? (
                      <span className="text-emerald-700 flex items-center gap-0.5">
                        <TrendingUp size={13} /> +{simulationResult.impact.health_change.toFixed(0)} points gain
                      </span>
                    ) : (
                      <span className="text-rose-700 flex items-center gap-0.5">
                        <TrendingDown size={13} /> {simulationResult.impact.health_change.toFixed(0)} points decline
                      </span>
                    )}
                  </div>
                </div>

                {/* Operational Risk Card */}
                <div className="p-4 rounded-3xl bg-white border border-zinc-200/90 shadow-2xs space-y-1">
                  <div className="flex items-center justify-between text-zinc-500 text-[11px] font-medium">
                    <span>Operational Risk</span>
                    <span className={`px-2 py-0.5 rounded-full border text-[9px] font-bold ${getRiskBadgeColor(simulationResult.predicted.risk_level)}`}>
                      {simulationResult.predicted.risk_level}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold text-zinc-950 font-mono tracking-tight">
                      {simulationResult.predicted.risk.toFixed(0)} / 100
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] font-semibold">
                    {simulationResult.impact.risk_change <= 0 ? (
                      <span className="text-emerald-700 flex items-center gap-0.5">
                        <TrendingDown size={13} /> {simulationResult.impact.risk_change.toFixed(0)} pts reduced risk
                      </span>
                    ) : (
                      <span className="text-rose-700 flex items-center gap-0.5">
                        <TrendingUp size={13} /> +{simulationResult.impact.risk_change.toFixed(0)} pts increased risk
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Parameter Comparison Matrix */}
              <div className="saas-card p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
                  <span className="text-xs font-bold text-zinc-900">Current vs. Predicted Parameters</span>
                  <span className="text-[10px] font-mono text-zinc-500">{simulationResult.asset_id} &bull; Model Matrix</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-zinc-200/70 text-[10px] uppercase font-mono text-zinc-400">
                        <th className="pb-2 font-bold">Metric Parameter</th>
                        <th className="pb-2 font-bold">Current Live</th>
                        <th className="pb-2 font-bold">Simulated Predicted</th>
                        <th className="pb-2 font-bold">Delta (&Delta;)</th>
                        <th className="pb-2 font-bold">Impact Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100 font-mono text-[11px]">
                      <tr>
                        <td className="py-2.5 font-sans font-medium text-zinc-800">Supply Temperature</td>
                        <td className="py-2.5 text-zinc-500">{simulationResult.current.temperature.toFixed(1)} °C</td>
                        <td className="py-2.5 font-bold text-zinc-900">{simulationResult.predicted.temperature.toFixed(1)} °C</td>
                        <td className="py-2.5">
                          {(simulationResult.predicted.temperature - simulationResult.current.temperature) >= 0 ? '+' : ''}
                          {(simulationResult.predicted.temperature - simulationResult.current.temperature).toFixed(1)} °C
                        </td>
                        <td className="py-2.5 font-sans">
                          {simulationResult.predicted.temperature <= 26.0 ? (
                            <span className="text-emerald-700 font-medium">Optimal</span>
                          ) : (
                            <span className="text-amber-700 font-medium">Elevated</span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <td className="py-2.5 font-sans font-medium text-zinc-800">Discharge Pressure</td>
                        <td className="py-2.5 text-zinc-500">{simulationResult.current.pressure.toFixed(1)} bar</td>
                        <td className="py-2.5 font-bold text-zinc-900">{simulationResult.predicted.pressure.toFixed(1)} bar</td>
                        <td className="py-2.5">
                          {(simulationResult.predicted.pressure - simulationResult.current.pressure) >= 0 ? '+' : ''}
                          {(simulationResult.predicted.pressure - simulationResult.current.pressure).toFixed(1)} bar
                        </td>
                        <td className="py-2.5 font-sans">
                          {simulationResult.predicted.pressure <= 4.5 ? (
                            <span className="text-emerald-700 font-medium">Normal</span>
                          ) : (
                            <span className="text-amber-700 font-medium">Head Strain</span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <td className="py-2.5 font-sans font-medium text-zinc-800">Airflow Rate</td>
                        <td className="py-2.5 text-zinc-500">{simulationResult.current.airflow.toFixed(0)} %</td>
                        <td className="py-2.5 font-bold text-zinc-900">{simulationResult.predicted.airflow.toFixed(0)} %</td>
                        <td className="py-2.5">
                          {(simulationResult.predicted.airflow - simulationResult.current.airflow) >= 0 ? '+' : ''}
                          {(simulationResult.predicted.airflow - simulationResult.current.airflow).toFixed(0)} %
                        </td>
                        <td className="py-2.5 font-sans">
                          {simulationResult.predicted.airflow >= 88.0 ? (
                            <span className="text-emerald-700 font-medium">Adequate</span>
                          ) : (
                            <span className="text-rose-700 font-medium">Restricted</span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <td className="py-2.5 font-sans font-medium text-zinc-800">Power Demand</td>
                        <td className="py-2.5 text-zinc-500">{simulationResult.current.energy_kw.toFixed(1)} kW</td>
                        <td className="py-2.5 font-bold text-zinc-900">{simulationResult.predicted.energy_kw.toFixed(1)} kW</td>
                        <td className="py-2.5">
                          {simulationResult.impact.energy_change_kw >= 0 ? '+' : ''}
                          {simulationResult.impact.energy_change_kw.toFixed(1)} kW
                        </td>
                        <td className="py-2.5 font-sans">
                          {simulationResult.impact.energy_change_percent <= 0 ? (
                            <span className="text-emerald-700 font-medium">Lower Demand</span>
                          ) : (
                            <span className="text-rose-700 font-medium">High Penalty</span>
                          )}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Visualized Comparison Chart */}
              <div className="saas-card p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
                  <span className="text-xs font-bold text-zinc-900">Current vs. Predicted Comparison</span>
                  <div className="flex items-center gap-3 text-[10px] font-mono">
                    <span className="flex items-center gap-1 text-zinc-400">
                      <span className="w-2.5 h-2.5 rounded bg-zinc-300 inline-block" /> Current
                    </span>
                    <span className="flex items-center gap-1 text-zinc-900 font-bold">
                      <span className="w-2.5 h-2.5 rounded bg-zinc-950 inline-block" /> Predicted
                    </span>
                  </div>
                </div>

                <div className="h-44 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f1f4" />
                      <XAxis dataKey="metric" tick={{ fontSize: 10, fill: '#71717a' }} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: '#71717a' }} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#18181b',
                          borderColor: '#27272a',
                          borderRadius: '1rem',
                          color: '#fff',
                          fontSize: '11px',
                        }}
                      />
                      <Bar dataKey="Current" fill="#d4d4d8" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Predicted" fill="#18181b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Engineering Causality Narrative & Recommendations */}
              <div className="grid gap-4 sm:grid-cols-2">
                {/* Physical Explanation */}
                <div className="saas-card p-5 space-y-2.5 bg-zinc-50/70 border border-zinc-200">
                  <div className="flex items-center gap-2 text-zinc-900 font-bold text-xs">
                    <Info size={14} className="text-zinc-600" />
                    <span>Causal Explanation</span>
                  </div>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    {simulationResult.explanation}
                  </p>
                </div>

                {/* Recommendations */}
                <div className="saas-card p-5 space-y-2.5 bg-zinc-50/70 border border-zinc-200">
                  <div className="flex items-center gap-2 text-zinc-900 font-bold text-xs">
                    <Lightbulb size={14} className="text-amber-500" />
                    <span>Engineering Recommendations</span>
                  </div>
                  <ul className="text-xs text-zinc-600 space-y-1.5 list-none">
                    {simulationResult.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <CheckCircle2 size={13} className="text-emerald-600 shrink-0 mt-0.5" />
                        <span className="leading-snug">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 rounded-3xl bg-zinc-50 border border-dashed border-zinc-200 text-center flex flex-col items-center justify-center space-y-2">
              <SlidersHorizontal size={28} className="text-zinc-300" />
              <p className="text-xs text-zinc-500">Loading asset simulation model...</p>
            </div>
          )}
        </div>
      </div>

      {/* 4. Optional Scenario Comparison Mode (Side-by-Side: Current vs Scenario A vs Scenario B) */}
      {comparisonMode && simulationResult && (
        <div className="saas-card p-6 md:p-8 space-y-6 border-zinc-900/10">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-400 font-mono">Multi-Scenario Evaluation</span>
              <h2 className="text-base font-bold text-zinc-900">Side-by-Side Scenario Benchmarking</h2>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-zinc-100 text-zinc-700 text-xs font-mono font-semibold">
              Current vs. Scenario A vs. Scenario B
            </span>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {/* Column 1: Current Live */}
            <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200 space-y-3 text-xs">
              <span className="font-bold text-zinc-600 block text-xs uppercase font-mono">Baseline (Current)</span>
              <div className="space-y-1 font-mono text-[11px] text-zinc-700">
                <p>Airflow: {simulationResult.current.airflow}%</p>
                <p>Power: {simulationResult.current.energy_kw.toFixed(1)} kW</p>
                <p>Health: {simulationResult.current.health.toFixed(0)}%</p>
                <p>Risk: {simulationResult.current.risk.toFixed(0)} ({simulationResult.current.risk_level})</p>
              </div>
            </div>

            {/* Column 2: Scenario A */}
            <div className="p-4 rounded-2xl bg-white border-2 border-zinc-900 shadow-sm space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-zinc-950 block text-xs uppercase font-mono">Scenario A (Current Sliders)</span>
                <span className="text-[10px] text-emerald-700 font-bold">Active</span>
              </div>
              <div className="space-y-1 font-mono text-[11px] text-zinc-800">
                <p>Airflow: {simulationResult.predicted.airflow}%</p>
                <p>Power: {simulationResult.predicted.energy_kw.toFixed(1)} kW ({simulationResult.impact.energy_change_percent.toFixed(1)}%)</p>
                <p>Health: {simulationResult.predicted.health.toFixed(0)}%</p>
                <p>Risk: {simulationResult.predicted.risk.toFixed(0)} ({simulationResult.predicted.risk_level})</p>
              </div>
            </div>

            {/* Column 3: Scenario B */}
            <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200 space-y-3 text-xs flex flex-col justify-between">
              <div className="space-y-2">
                <span className="font-bold text-zinc-700 block text-xs uppercase font-mono">Scenario B (Alternative)</span>
                <div className="space-y-1">
                  <label className="text-[10px] text-zinc-500">Airflow target: {scenarioBFlow}%</label>
                  <input
                    type="range"
                    min="60"
                    max="120"
                    step="5"
                    value={scenarioBFlow}
                    onChange={(e) => setScenarioBFlow(parseFloat(e.target.value))}
                    className="w-full accent-zinc-900 h-1 bg-zinc-200 rounded"
                  />
                </div>

                {scenarioBResult ? (
                  <div className="space-y-1 font-mono text-[11px] text-zinc-800 pt-1">
                    <p>Power: {scenarioBResult.predicted.energy_kw.toFixed(1)} kW ({scenarioBResult.impact.energy_change_percent.toFixed(1)}%)</p>
                    <p>Health: {scenarioBResult.predicted.health.toFixed(0)}%</p>
                    <p>Risk: {scenarioBResult.predicted.risk.toFixed(0)} ({scenarioBResult.predicted.risk_level})</p>
                  </div>
                ) : (
                  <p className="text-[10px] text-zinc-400">Click below to compute Scenario B.</p>
                )}
              </div>

              <button
                onClick={handleRunScenarioB}
                disabled={simulatingB}
                className="w-full py-1.5 rounded-xl bg-zinc-800 text-white text-[11px] font-semibold cursor-pointer hover:bg-zinc-700 transition-colors"
              >
                {simulatingB ? 'Computing...' : 'Simulate Scenario B'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
