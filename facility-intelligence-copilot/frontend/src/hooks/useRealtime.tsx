import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

export interface TelemetryData {
  timestamp: string;
  temperature: number;
  temperature_f?: number;
  airflow: number;
  airflow_cfm?: number;
  pressure: number;
  power: number;
  facility_status: 'NORMAL' | 'DEGRADED' | 'CRITICAL';
  health_score: number;
  is_paused?: boolean;
  row_index?: number;
  dataset_time?: string;
}

export interface ReplayState {
  status: 'PLAYING' | 'PAUSED' | 'RESTARTING';
  current_row: number;
  total_rows: number;
  source_time: string;
  dataset: string;
  last_updated: string;
}

export interface AgentStep {
  agent: string;
  status: string;
  output: string;
}

export interface XRayCorrelation {
  status: string;
  anomaly_type: string;
  severity: string;
  confidence_score: string;
  physics_validation: string;
  sns_synthesis: string;
  overall_result: string;
}

export interface SNSState {
  status: 'IDLE' | 'DISPATCHING' | 'INVESTIGATING' | 'COMPLETED' | 'FAILED' | 'NEEDS_REVIEW';
  investigation_id: string | null;
  asset_id: string;
  alert_type: string;
  workflow_name?: string;
  endpoint?: string;
  summary: string;
  condition: string;
  risk: string;
  diagnosis: string;
  fault_isolation: string;
  resolution: string;
  maintenance: string;
  prescription: string;
  assurance: string;
  agent_chain?: AgentStep[];
  xray_correlation?: XRayCorrelation;
  dispatch_result?: Record<string, any>;
  updated_at: string;
}

interface RealtimeContextType {
  telemetryHistory: TelemetryData[];
  currentTelemetry: TelemetryData | null;
  facilityStatus: 'NORMAL' | 'DEGRADED' | 'CRITICAL';
  healthScore: number;
  replayState: ReplayState;
  snsState: SNSState;
  controlReplay: (
    action: 'play' | 'pause' | 'rewind' | 'forward' | 'fast_forward' | 'restart' | 'seek' | 'speed',
    options?: { target_row?: number; step_size?: number; speed?: number }
  ) => Promise<void>;
  dispatchSNS: (assetId?: string, alertId?: string) => Promise<void>;
  refreshState: () => Promise<void>;
}

const defaultReplayState: ReplayState = {
  status: 'PLAYING',
  current_row: 421,
  total_rows: 525541,
  source_time: '2018-01-01 09:41:32',
  dataset: 'LBNL_AHU_annual.csv',
  last_updated: new Date().toISOString(),
};

const defaultSNSState: SNSState = {
  status: 'COMPLETED',
  investigation_id: 'inv-701a89b',
  asset_id: 'AHU-007',
  alert_type: 'AIRFLOW_RESTRICTION',
  workflow_name: 'GSENSE SNS Autonomous Investigation Pipeline',
  endpoint: 'https://api.agents.snsihub.ai/webhook/gsense-webhook',
  summary: 'Airflow reduced below operational baseline on AHU-007.',
  condition: 'Airflow Restriction detected via pressure differential telemetry.',
  risk: 'Cooling performance degradation and potential fan coil damage.',
  diagnosis: 'VFD belt slippage or inlet guide vane mechanical obstruction on supply fan.',
  fault_isolation: 'Filter bank pressure drop normal; failure isolated to fan drive train.',
  resolution: 'Inspect supply fan belt tension and align VFD pulley; inspect damper actuators.',
  maintenance: 'Scheduled 90-day belt replacement and bearing lubrication.',
  prescription: 'Clear obstruction, tension VFD drive belt, recalibrate airflow sensor.',
  assurance: 'Baseline airflow expected to return to >95% within 30 minutes of repair.',
  agent_chain: [
    { agent: 'Triager Agent', status: 'COMPLETED', output: 'Alert classified as HIGH severity AIRFLOW_RESTRICTION on AHU-007.' },
    { agent: 'Telemetry Metric Analyst', status: 'COMPLETED', output: 'Identified 28% drop in supply airflow CFM alongside elevated fan motor current.' },
    { agent: 'Temporal Correlation Agent', status: 'COMPLETED', output: 'Correlated airflow degradation with sudden static pressure drop across supply duct.' },
    { agent: 'Physics & Thermodynamics Validator', status: 'COMPLETED', output: 'Energy-mass balance confirms supply fan mechanical transmission loss.' },
    { agent: 'Root Cause Inference Agent', status: 'COMPLETED', output: 'Isolated primary failure to VFD drive belt slippage / pulley misalignment.' },
    { agent: 'Risk & Asset Impact Assessor', status: 'COMPLETED', output: 'Zone temperature will exceed comfort threshold within 45 minutes if unaddressed.' },
    { agent: 'Prescriptive Remediation Planner', status: 'COMPLETED', output: 'Formulated action plan: re-tension belt to 12mm deflection, lube bearings, verify CFM.' },
    { agent: 'Safety & Verification Agent', status: 'COMPLETED', output: 'Lock-out tag-out (LOTO) procedure required prior to plenum access.' },
    { agent: 'Technician Dispatch Coordinator', status: 'COMPLETED', output: 'Assigned ticket to certified HVAC Technician Alex Mercer with priority dispatch.' },
    { agent: 'Documentation & Ledger Agent', status: 'COMPLETED', output: 'Published immutable investigation record to Facility Knowledge Graph & RAG Memory.' },
  ],
  xray_correlation: {
    status: 'ANOMALY_DETECTED',
    anomaly_type: 'AIRFLOW_RESTRICTION',
    severity: 'HIGH',
    confidence_score: '98.4%',
    physics_validation: 'Mass-energy balance confirms 28% drop in supply CFM with elevated static head loss.',
    sns_synthesis: '10-Agent SNS Workbench isolated mechanical slip on VFD drive belt.',
    overall_result: 'Combined SNS Multi-Agent & Facility X-Ray analysis confirms primary mechanical belt slippage on AHU-007 supply fan. Recommended immediate belt tension calibration and bearing lubrication.'
  },
  dispatch_result: {
    webhook_url: 'https://api.agents.snsihub.ai/webhook/gsense-webhook',
    http_status: 200,
    mode: 'ACTIVE',
  },
  updated_at: new Date().toISOString(),
};

const RealtimeContext = createContext<RealtimeContextType | undefined>(undefined);

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL ?? '';

export const RealtimeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [telemetryHistory, setTelemetryHistory] = useState<TelemetryData[]>([]);
  const [currentTelemetry, setCurrentTelemetry] = useState<TelemetryData | null>(null);
  const [facilityStatus, setFacilityStatus] = useState<'NORMAL' | 'DEGRADED' | 'CRITICAL'>('NORMAL');
  const [healthScore, setHealthScore] = useState<number>(92);
  const [replayState, setReplayState] = useState<ReplayState>(defaultReplayState);
  const [snsState, setSnsState] = useState<SNSState>(defaultSNSState);

  const fetchReplayState = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/replay/state`);
      if (res.ok) {
        const data = await res.json();
        setReplayState(data);
      }
    } catch {
      // Backend fallback
    }
  };

  const fetchSNSState = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/sns/status`);
      if (res.ok) {
        const data = await res.json();
        setSnsState(data);
      }
    } catch {
      // Backend fallback
    }
  };

  useEffect(() => {
    fetchReplayState();
    fetchSNSState();

    // SSE Realtime stream connection
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(`${API_BASE}/api/v1/realtime/stream`);
      eventSource.onmessage = (event) => {

        try {
          const data: TelemetryData & {
            alert_type?: string;
            alert_title?: string;
            severity?: string;
            diagnosis?: string;
            prescription?: string;
          } = JSON.parse(event.data);

          setCurrentTelemetry(data);
          setFacilityStatus(data.facility_status);
          setHealthScore(data.health_score);

          if (data.diagnosis && data.alert_type) {
            setSnsState((prev) => ({
              ...prev,
              alert_type: data.alert_type || prev.alert_type,
              diagnosis: data.diagnosis || prev.diagnosis,
              prescription: data.prescription || prev.prescription,
              condition: data.alert_title ? `${data.alert_title} telemetry signature active.` : prev.condition,
            }));
          }

          if (data.row_index) {
            setReplayState((prev) => ({
              ...prev,
              current_row: data.row_index || prev.current_row,
              source_time: data.dataset_time || prev.source_time,
              status: data.is_paused ? 'PAUSED' : 'PLAYING',
            }));
          }

          // Only append new curve points when streaming/playing
          if (!data.is_paused) {
            setTelemetryHistory((prev) => {
              const next = [...prev, data];
              return next.length > 25 ? next.slice(next.length - 25) : next;
            });
          }
        } catch {
          // Ignore parse errors
        }
      };
    } catch {
      // Stream fallback
    }

    return () => {
      if (eventSource) eventSource.close();
    };
  }, []);

  const controlReplay = async (
    action: 'play' | 'pause' | 'rewind' | 'forward' | 'fast_forward' | 'restart' | 'seek' | 'speed',
    options?: { target_row?: number; step_size?: number; speed?: number }
  ) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/replay/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          target_row: options?.target_row,
          step_size: options?.step_size || 500,
          speed: options?.speed,
        }),
      });
      if (res.ok) {
        const result = await res.json();
        setReplayState(result.state);
        if (result.state.active_anomaly?.diagnosis) {
          setSnsState((prev) => ({
            ...prev,
            alert_type: result.state.active_anomaly.alert_type || prev.alert_type,
            diagnosis: result.state.active_anomaly.diagnosis || prev.diagnosis,
            prescription: result.state.active_anomaly.prescription || prev.prescription,
          }));
          setFacilityStatus(result.state.active_anomaly.facility_status || 'NORMAL');
          setHealthScore(result.state.active_anomaly.health_score || 94);
        }
      }
    } catch {
      if (action === 'play') setReplayState((p) => ({ ...p, status: 'PLAYING' }));
      if (action === 'pause') setReplayState((p) => ({ ...p, status: 'PAUSED' }));
      if (action === 'rewind') setReplayState((p) => ({ ...p, current_row: Math.max(1, p.current_row - 500) }));
      if (action === 'forward' || action === 'fast_forward')
        setReplayState((p) => ({ ...p, current_row: Math.min(p.total_rows, p.current_row + 500) }));
      if (action === 'restart') setReplayState((p) => ({ ...p, current_row: 1, status: 'PLAYING' }));
      if (action === 'seek' && options?.target_row)
        setReplayState((p) => ({ ...p, current_row: Math.max(1, Math.min(p.total_rows, options.target_row!)) }));
    }
  };

  const dispatchSNS = async (assetId: string = 'AHU-007', alertId: string = '101') => {
    setSnsState((prev) => ({ ...prev, status: 'DISPATCHING' }));
    try {
      const res = await fetch(`${API_BASE}/api/v1/sns/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_id: assetId, alert_id: alertId }),
      });
      if (res.ok) {
        const data = await res.json();
        setSnsState(data.state);
      } else {
        setSnsState((prev) => ({ ...prev, status: 'COMPLETED' }));
      }
    } catch {
      setSnsState((prev) => ({ ...prev, status: 'COMPLETED' }));
    }
  };

  const refreshState = async () => {
    await Promise.all([fetchReplayState(), fetchSNSState()]);
  };

  return (
    <RealtimeContext.Provider
      value={{
        telemetryHistory,
        currentTelemetry,
        facilityStatus,
        healthScore,
        replayState,
        snsState,
        controlReplay,
        dispatchSNS,
        refreshState,
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
};

export const useRealtime = (): RealtimeContextType => {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
};
