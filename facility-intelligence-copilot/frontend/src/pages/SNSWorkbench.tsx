import { useEffect, useState } from 'react';
import {
  Activity,
  Boxes,
  CheckCircle2,
  Copy,
  Cpu,
  Flame,
  Layers,
  Loader2,
  Radio,
  Send,
  Server,
  ShieldCheck,
  Sparkles,
  Workflow,
  Wrench,
  XCircle,
  Zap,
} from 'lucide-react';
import { testSNSWebhook, sendSNSEvent, type SNSTestResponse } from '../services/sns';
import { getAlerts } from '../services/alerts';
import { getAssetTelemetry } from '../services/telemetry';

const ORCHESTRATION_FLOW = [
  { step: '01', name: 'Incident Trigger', agent: 'Telemetry Stream', icon: Activity },
  { step: '02', name: 'Telemetry Detective', agent: 'Z-Score & Drift Analysis', icon: Cpu },
  { step: '03', name: 'Digital Twin Analyst', agent: 'Graph Dependency Traversal', icon: Boxes },
  { step: '04', name: 'Sensor Health', agent: 'Thermistor & Transducer Check', icon: Sparkles },
  { step: '05', name: 'Impact & Severity', agent: 'Comfort & Energy Penalty', icon: Zap },
  { step: '06', name: 'Evidence Fusion', agent: 'Multi-Modal Synergy', icon: Layers },
  { step: '07', name: 'Root Cause', agent: 'Causal Fault Isolation', icon: Flame },
  { step: '08', name: 'Validation Agent', agent: 'Physical Verification Gate', icon: ShieldCheck },
  { step: '09', name: 'Action Dispatch', agent: 'SNS Webhook Gateway', icon: Wrench },
];

export default function SNSWorkbench() {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<SNSTestResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Live Canonical Payload State
  const [canonicalPayload, setCanonicalPayload] = useState({
    investigation_id: 'INV-LBNL-LIVE',
    facility_id: 'FAC-001',
    facility_name: 'LBNL RTU Dataset',
    asset_id: 'HVAC-007',
    asset_name: 'LBNL RTU Rooftop Unit #7',
    metric: 'discharge_pressure',
    current_value: 31.5,
    unit: 'bar',
    timestamp: new Date().toISOString(),
  });

  // Custom Event Simulation State (Manual Diagnostic Tool)
  const [customAssetId, setCustomAssetId] = useState('HVAC-007');
  const [customMetric, setCustomMetric] = useState('pressure');
  const [customValue, setCustomValue] = useState(31.5);
  const [customUnit, setCustomUnit] = useState('bar');
  const [sendingCustom, setSendingCustom] = useState(false);
  const [customResponse, setCustomResponse] = useState<SNSTestResponse | null>(null);

  useEffect(() => {
    let isActive = true;
    const loadLiveContext = async () => {
      try {
        const [alerts, telemetry] = await Promise.all([
          getAlerts().catch(() => []),
          getAssetTelemetry(7, { limit: 1 }).catch(() => []),
        ]);

        if (isActive) {
          const openAlert = alerts.find((a) => a.status === 'OPEN') || alerts[0];
          const latestPoint = telemetry[telemetry.length - 1];

          setCanonicalPayload({
            investigation_id: openAlert ? `INV-${openAlert.id}` : 'INV-LBNL-LIVE',
            facility_id: 'FAC-001',
            facility_name: 'LBNL RTU Dataset',
            asset_id: 'HVAC-007',
            asset_name: 'LBNL RTU Rooftop Unit #7',
            metric: latestPoint && latestPoint.pressure > 16 ? 'discharge_pressure' : 'temperature',
            current_value: latestPoint ? Number((latestPoint.pressure > 16 ? latestPoint.pressure : latestPoint.temperature).toFixed(1)) : 31.5,
            unit: latestPoint && latestPoint.pressure > 16 ? 'bar' : 'C',
            timestamp: latestPoint ? latestPoint.timestamp : new Date().toISOString(),
          });
        }
      } catch {
        // Fallback gracefully
      }
    };

    void loadLiveContext();
    const interval = setInterval(loadLiveContext, 3000);
    return () => {
      isActive = false;
      clearInterval(interval);
    };
  }, []);

  const handleTestWebhook = async () => {
    setTesting(true);
    setTestError(null);
    try {
      const res = await testSNSWebhook();
      setTestResult(res);
    } catch (err) {
      setTestError(err instanceof Error ? err.message : 'Webhook trigger connection failed.');
    } finally {
      setTesting(false);
    }
  };

  const handleSendCustomEvent = async () => {
    setSendingCustom(true);
    try {
      const res = await sendSNSEvent({
        investigation_id: `INV-SIM-${Math.floor(Math.random() * 8999 + 1000)}`,
        facility_id: 'FAC-001',
        facility_name: 'LBNL RTU Dataset',
        asset_id: customAssetId,
        asset_name: customAssetId === 'HVAC-007' ? 'LBNL RTU Rooftop Unit #7' : 'Facility Equipment',
        metric: customMetric,
        current_value: customValue,
        unit: customUnit,
        timestamp: new Date().toISOString(),
      });
      setCustomResponse(res);
    } catch (err) {
      alert(`Event dispatch failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSendingCustom(false);
    }
  };

  const handleCopyPayload = () => {
    void navigator.clipboard.writeText(JSON.stringify(canonicalPayload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="saas-card p-6 md:p-8 space-y-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-zinc-500">
            <Workflow size={16} />
            <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Autonomous Multi-Agent Orchestration</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-950 editorial-title tracking-tight">
            AI Workbench
          </h1>
          <p className="text-zinc-600 text-xs sm:text-sm max-w-2xl leading-relaxed">
            Multi-agent orchestration bridge interfacing GSENSE with SNS Workbench autonomous trigger webhooks and bidirectional investigation callbacks.
          </p>
        </div>

        <button
          onClick={handleTestWebhook}
          disabled={testing}
          className="flex items-center gap-2 px-6 py-3 rounded-full bg-zinc-950 text-white font-semibold hover:bg-zinc-800 transition-all text-xs cursor-pointer shadow-sm disabled:opacity-50 shrink-0"
        >
          {testing ? <Loader2 size={13} className="animate-spin" /> : <Radio size={13} />}
          <span>Test SNS Webhook Dispatch</span>
        </button>
      </div>

      {/* 1. 9-STEP MULTI-AGENT ORCHESTRATION PIPELINE TOPOLOGY */}
      <div className="saas-card p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
          <div className="space-y-0.5">
            <span className="text-[10px] uppercase tracking-wider font-mono text-zinc-400 font-bold">Agent Flow</span>
            <h2 className="text-base font-bold text-zinc-900">Multi-Agent Investigation Architecture</h2>
          </div>
          <span className="px-2.5 py-0.5 rounded-full bg-zinc-100 text-zinc-600 font-mono text-xs font-semibold">
            9 Autonomous Stages
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-9">
          {ORCHESTRATION_FLOW.map(({ step, name, agent, icon: Icon }) => (
            <div
              key={step}
              className="p-3 rounded-2xl bg-zinc-50 border border-zinc-200/80 flex flex-col justify-between space-y-3 relative group hover:border-zinc-400 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-zinc-400">{step}</span>
                <div className="w-6 h-6 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-zinc-700 shadow-2xs">
                  <Icon size={12} strokeWidth={2} />
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold text-zinc-900 leading-tight">{name}</h3>
                <p className="text-[10px] text-zinc-500 font-mono mt-0.5 leading-snug">{agent}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2. CANONICAL WEBHOOK PAYLOAD INSPECTOR & SNS TEST OUTPUT */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Live Canonical Webhook Schema */}
        <div className="saas-card p-6 md:p-8 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="flex items-center gap-2">
                <Server size={16} className="text-zinc-700" />
                <h3 className="text-sm font-bold text-zinc-900">Live Canonical Webhook Payload</h3>
              </div>

              <button
                onClick={handleCopyPayload}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-100 hover:bg-zinc-200 text-zinc-700 text-xs font-mono font-semibold transition-colors cursor-pointer"
              >
                {copied ? <CheckCircle2 size={12} className="text-emerald-600" /> : <Copy size={12} />}
                <span>{copied ? 'Copied' : 'Copy JSON'}</span>
              </button>
            </div>

            <p className="text-xs text-zinc-500">
              Live payload generated from current active LBNL RTU telemetry and alert state dispatched to SNS Workbench:
            </p>
          </div>

          <pre className="p-4 rounded-2xl bg-zinc-950 text-zinc-100 font-mono text-xs overflow-x-auto leading-relaxed border border-zinc-800 shadow-inner">
            <code>{JSON.stringify(canonicalPayload, null, 2)}</code>
          </pre>
        </div>

        {/* Right: Live Webhook Response Console */}
        <div className="saas-card p-6 md:p-8 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="flex items-center gap-2">
                <Radio size={16} className="text-zinc-700" />
                <h3 className="text-sm font-bold text-zinc-900">SNS Webhook Response Stream</h3>
              </div>

              <span className="text-[10px] font-mono text-zinc-400">
                {testResult ? 'HTTP 200 OK' : 'Ready'}
              </span>
            </div>

            <p className="text-xs text-zinc-500">
              Inbound and outbound callback confirmation messages returned by the FastAPI integration bridge:
            </p>
          </div>

          {testResult ? (
            <div className="p-4 rounded-2xl bg-emerald-50/50 border border-emerald-200 text-xs space-y-2 font-mono text-emerald-950">
              <div className="flex items-center justify-between">
                <span className="font-bold flex items-center gap-1.5 text-emerald-800">
                  <CheckCircle2 size={14} /> Webhook Dispatched Successfully
                </span>
                <span className="text-[10px] text-emerald-700">HTTP {testResult.sns_status_code}</span>
              </div>
              <p className="text-zinc-700">{testResult.detail || `Status: ${testResult.status}`}</p>
              {testResult.investigation_id && (
                <p className="text-[11px] text-zinc-500">Investigation ID: {testResult.investigation_id}</p>
              )}
            </div>
          ) : testError ? (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs space-y-1 font-mono text-rose-900">
              <span className="font-bold flex items-center gap-1.5">
                <XCircle size={14} /> Webhook Error
              </span>
              <p className="text-rose-700">{testError}</p>
            </div>
          ) : (
            <div className="p-8 rounded-2xl bg-zinc-50 border border-dashed border-zinc-200 text-center space-y-2 flex flex-col items-center justify-center">
              <Radio size={24} className="text-zinc-300 animate-pulse" />
              <p className="text-xs text-zinc-500">Click &ldquo;Test SNS Webhook Dispatch&rdquo; to execute live trigger.</p>
            </div>
          )}
        </div>
      </div>

      {/* 3. OUTBOUND TELEMETRY EVENT SIMULATOR (MANUAL TESTING TOOL) */}
      <div className="saas-card p-6 md:p-8 space-y-6">
        <div className="border-b border-zinc-100 pb-3 space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-zinc-100 text-zinc-700 text-[10px] font-mono font-semibold">
            <span>MANUAL DIAGNOSTIC TOOL</span>
          </div>
          <h2 className="text-base font-bold text-zinc-900">Outbound Telemetry Event Simulator</h2>
          <p className="text-xs text-zinc-500">
            Transmit manual custom telemetry payloads into the multi-agent pipeline (separate from the automated LBNL real-time replay stream).
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-zinc-700">Target Asset</label>
            <select
              value={customAssetId}
              onChange={(e) => setCustomAssetId(e.target.value)}
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 text-xs text-zinc-800 focus:outline-none focus:border-zinc-400"
            >
              <option value="HVAC-007">HVAC-007 (LBNL RTU Unit)</option>
              <option value="HVAC-001">HVAC-001 (Auditorium AHU)</option>
              <option value="CHILLER-001">CHILLER-001 (Primary Chiller)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-zinc-700">Telemetry Metric</label>
            <select
              value={customMetric}
              onChange={(e) => {
                const metric = e.target.value;
                setCustomMetric(metric);
                if (metric === 'temperature') setCustomUnit('C');
                if (metric === 'pressure') setCustomUnit('bar');
                if (metric === 'airflow') setCustomUnit('%');
                if (metric === 'power') setCustomUnit('kW');
              }}
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 text-xs text-zinc-800 focus:outline-none focus:border-zinc-400"
            >
              <option value="pressure">Refrigerant Pressure (bar)</option>
              <option value="power">Electrical Power (kW)</option>
              <option value="temperature">Supply Temperature (°C)</option>
              <option value="airflow">Airflow Velocity (%)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-zinc-700">Metric Value</label>
            <input
              type="number"
              value={customValue}
              onChange={(e) => setCustomValue(parseFloat(e.target.value) || 0)}
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 text-xs text-zinc-800 font-mono focus:outline-none focus:border-zinc-400"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleSendCustomEvent}
              disabled={sendingCustom}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
            >
              {sendingCustom ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
              <span>Emit Event</span>
            </button>
          </div>
        </div>

        {customResponse && (
          <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200 text-xs font-mono space-y-1">
            <span className="font-bold text-zinc-800">Dispatch Response:</span>
            <p className="text-zinc-600">{customResponse.detail || `Status: ${customResponse.status} (HTTP ${customResponse.sns_status_code})`}</p>
          </div>
        )}
      </div>
    </div>
  );
}
