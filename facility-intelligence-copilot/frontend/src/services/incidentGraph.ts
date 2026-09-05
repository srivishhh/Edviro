import { API_BASE_URL } from './api';

export type NodeType =
  | 'ASSET'
  | 'COMPONENT'
  | 'SENSOR'
  | 'ANOMALY'
  | 'INCIDENT'
  | 'ROOT_CAUSE'
  | 'IMPACT'
  | 'ACTION';

export type ConfidenceLevel =
  | 'CONFIRMED'
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'SUSPECTED'
  | 'OBSERVED';

export interface NodeTelemetry {
  metric: string;
  current_value: float_string;
  expected_range: string;
  unit?: string;
  baseline?: number | string;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL';
}

type float_string = string | number;

export interface IncidentGraphNode {
  id: string;
  type: NodeType;
  label: string;
  category: string;
  status: 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'NEUTRAL';
  confidence?: string;
  confidence_level: ConfidenceLevel;
  telemetry?: NodeTelemetry;
  details: Record<string, any>;
}

export interface IncidentGraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  confidence?: string;
  label?: string;
}

export interface SimilarHistoricalIncident {
  memory_id: string;
  incident_number: string;
  incident_type: string;
  asset_code: string;
  similarity_pct: number;
  root_cause: string;
  corrective_action: string;
  timestamp: string;
}

export interface IncidentGraphSummary {
  incident_id: string | number;
  incident_name: string;
  alert_type: string;
  asset_id: number;
  asset_name: string;
  asset_code: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  confidence: string;
  confidence_level: ConfidenceLevel;
  affected_components_count: number;
  possible_causes_count: number;
  energy_impact: string;
  status: string;
  detected_at?: string;
}

export interface IncidentGraphResponse {
  summary: IncidentGraphSummary;
  nodes: IncidentGraphNode[];
  edges: IncidentGraphEdge[];
  historical_matches: SimilarHistoricalIncident[];
}

export const FALLBACK_INCIDENT_SUMMARIES: IncidentGraphSummary[] = [
  {
    incident_id: 101,
    incident_name: 'Supply Air Velocity Drop & Thermal Restriction',
    alert_type: 'AIRFLOW_RESTRICTION',
    asset_id: 7,
    asset_name: 'LBNL RTU Rooftop Unit #7 (AHU-09)',
    asset_code: 'AHU-09',
    severity: 'WARNING',
    confidence: '88% Confirmed',
    confidence_level: 'HIGH',
    affected_components_count: 3,
    possible_causes_count: 3,
    energy_impact: 'Elevated (+4.2 kW motor surge)',
    status: 'OPEN',
    detected_at: '2026-09-01T12:15:00Z',
  },
  {
    incident_id: 104,
    incident_name: 'Severe Condenser Heat Rejection Resistance',
    alert_type: 'CONDENSER_FOULING',
    asset_id: 7,
    asset_name: 'LBNL RTU Rooftop Unit #7 (AHU-09)',
    asset_code: 'AHU-09',
    severity: 'CRITICAL',
    confidence: '86% Confirmed',
    confidence_level: 'HIGH',
    affected_components_count: 3,
    possible_causes_count: 3,
    energy_impact: 'Critical Surge (+132.1 kW high back-pressure)',
    status: 'OPEN',
    detected_at: '2026-09-01T12:15:00Z',
  },
  {
    incident_id: 102,
    incident_name: 'Continuous Full-Duty Electrical Energy Surge',
    alert_type: 'HIGH_ENERGY',
    asset_id: 1,
    asset_name: 'Auditorium Ventilation Unit (AHU-01)',
    asset_code: 'HVAC-001',
    severity: 'WARNING',
    confidence: '82% Confirmed',
    confidence_level: 'HIGH',
    affected_components_count: 2,
    possible_causes_count: 2,
    energy_impact: 'Excessive (+6.8 kW peak demand)',
    status: 'OPEN',
    detected_at: '2026-09-01T11:45:00Z',
  },
  {
    incident_id: 103,
    incident_name: 'Supply Air Temperature Anomaly',
    alert_type: 'HIGH_TEMPERATURE',
    asset_id: 7,
    asset_name: 'LBNL RTU Rooftop Unit #7 (AHU-09)',
    asset_code: 'AHU-09',
    severity: 'WARNING',
    confidence: '80% Confirmed',
    confidence_level: 'HIGH',
    affected_components_count: 2,
    possible_causes_count: 2,
    energy_impact: 'Moderate (+2.1 kW thermal overrun)',
    status: 'OPEN',
    detected_at: '2026-09-01T12:15:00Z',
  },
  {
    incident_id: 105,
    incident_name: 'Telemetry Signal Loss & Transducer Anomaly',
    alert_type: 'SENSOR_FAILURE',
    asset_id: 7,
    asset_name: 'LBNL RTU Rooftop Unit #7 (AHU-09)',
    asset_code: 'AHU-09',
    severity: 'CRITICAL',
    confidence: '95% Confirmed',
    confidence_level: 'CONFIRMED',
    affected_components_count: 1,
    possible_causes_count: 2,
    energy_impact: 'Uncalibrated / Blind Cycling (+1.8 kW)',
    status: 'OPEN',
    detected_at: '2026-09-01T12:15:00Z',
  },
];

export async function fetchIncidentSummaries(): Promise<IncidentGraphSummary[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/relationships`, {
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch {
    return FALLBACK_INCIDENT_SUMMARIES;
  }
}

export async function fetchIncidentRelationshipGraph(
  incidentId: string | number
): Promise<IncidentGraphResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/relationships`, {
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch {
    // If backend offline, generate fallback matching the requested incident
    const summary =
      FALLBACK_INCIDENT_SUMMARIES.find((s) => String(s.incident_id) === String(incidentId)) ||
      FALLBACK_INCIDENT_SUMMARIES[0];

    return {
      summary,
      nodes: [
        {
          id: 'asset_7',
          type: 'ASSET',
          label: 'Asset: AHU-09 / HVAC-007',
          category: 'Facility Asset',
          status: 'WARNING',
          confidence: 'Confirmed',
          confidence_level: 'CONFIRMED',
          details: {
            name: 'LBNL RTU Rooftop Unit #7 (AHU-09)',
            location: 'Level 2 Mechanical Deck — East Wing',
            serves: 'Conditioned Zone Block 204–210',
            health_score: 68,
          },
        },
        {
          id: 'sensor_airflow',
          type: 'SENSOR',
          label: 'Airflow Sensor',
          category: 'Telemetry Observation',
          status: 'CRITICAL',
          confidence: 'Observed',
          confidence_level: 'OBSERVED',
          telemetry: {
            metric: 'Airflow Velocity Rating',
            current_value: '64.0',
            expected_range: '85.0–100.0 %',
            unit: '%',
            baseline: 96.0,
            status: 'CRITICAL',
          },
          details: {
            sensor_tag: 'AIRFLOW-007',
            location: 'Intake filter exit cross-section',
          },
        },
        {
          id: 'sensor_temp',
          type: 'SENSOR',
          label: 'Temperature Sensor',
          category: 'Telemetry Observation',
          status: 'CRITICAL',
          confidence: 'Observed',
          confidence_level: 'OBSERVED',
          telemetry: {
            metric: 'Supply Air Temperature',
            current_value: '30.1',
            expected_range: '20.0–26.0 °C',
            unit: '°C',
            baseline: 22.5,
            status: 'CRITICAL',
          },
          details: {
            sensor_tag: 'TEMP-007',
            location: 'Plenum supply discharge chamber',
          },
        },
        {
          id: 'sensor_energy',
          type: 'SENSOR',
          label: 'Power Sub-meter',
          category: 'Telemetry Observation',
          status: 'CRITICAL',
          confidence: 'Observed',
          confidence_level: 'OBSERVED',
          telemetry: {
            metric: 'Electrical Power Demand',
            current_value: '12.3',
            expected_range: '5.0–8.5 kW',
            unit: 'kW',
            baseline: 6.2,
            status: 'CRITICAL',
          },
          details: {
            sensor_tag: 'ENERGY-007',
            location: 'RTU-07 main MCC feeder bucket',
          },
        },
        {
          id: 'anom_low_airflow',
          type: 'ANOMALY',
          label: 'Airflow Restriction Anomaly',
          category: 'Anomaly',
          status: 'CRITICAL',
          confidence: 'Confirmed (64.0% vs 96.0% baseline)',
          confidence_level: 'CONFIRMED',
          details: {
            deviation: '-32% airflow deficit across supply duct',
            reported_by: 'sensor_airflow',
          },
        },
        {
          id: 'anom_high_temp',
          type: 'ANOMALY',
          label: 'Supply Temperature Rise',
          category: 'Anomaly',
          status: 'WARNING',
          confidence: 'Confirmed (30.1°C vs 22.0°C baseline)',
          confidence_level: 'CONFIRMED',
          details: {
            deviation: '+8.1°C thermal departure from comfortable setpoint',
            reported_by: 'sensor_temp',
          },
        },
        {
          id: 'comp_damper',
          type: 'COMPONENT',
          label: 'Intake Damper',
          category: 'Component',
          status: 'WARNING',
          confidence: 'Suspected',
          confidence_level: 'SUSPECTED',
          details: {
            description: 'Modulating motorized outside air intake damper with Belimo electronic actuator.',
            connected_sensors: ['Airflow Sensor (AIRFLOW-007)'],
          },
        },
        {
          id: 'comp_filter',
          type: 'COMPONENT',
          label: 'Primary Air Filter',
          category: 'Component',
          status: 'CRITICAL',
          confidence: 'Confirmed',
          confidence_level: 'CONFIRMED',
          details: {
            description: '24x24x2 MERV-13 deep-pleat high-efficiency particulate air filter bank.',
            connected_sensors: ['Airflow Sensor (AIRFLOW-007)'],
          },
        },
        {
          id: 'comp_cooling_coil',
          type: 'COMPONENT',
          label: 'Cooling Coil',
          category: 'Component',
          status: 'WARNING',
          confidence: 'Confirmed',
          confidence_level: 'CONFIRMED',
          details: {
            description: 'Chilled water / DX copper-tube aluminum-fin heat exchanger coil block.',
            connected_sensors: ['Temperature Sensor (TEMP-007)'],
          },
        },
        {
          id: 'comp_fan',
          type: 'COMPONENT',
          label: 'Supply Air Fan',
          category: 'Component',
          status: 'WARNING',
          confidence: 'Confirmed',
          confidence_level: 'CONFIRMED',
          details: {
            description: 'Direct-drive backward-curved centrifugal plenum fan with 15kW ABB VFD drive.',
            connected_sensors: ['Power Sub-meter (ENERGY-007)'],
          },
        },
        {
          id: 'cause_primary',
          type: 'ROOT_CAUSE',
          label: 'Filter Loading / Clogged Media',
          category: 'Root Cause Hypothesis',
          status: 'CRITICAL',
          confidence: '88% (Primary)',
          confidence_level: 'HIGH',
          details: {
            cause_description: 'Airflow restriction due to clogged filter or restricted damper actuator in HVAC supply duct.',
            hypothesis_tier: 'Primary Causal Factor',
          },
        },
        {
          id: 'cause_secondary',
          type: 'ROOT_CAUSE',
          label: 'Damper Actuator Sticking',
          category: 'Alternative Cause Hypothesis',
          status: 'WARNING',
          confidence: '34% (Secondary)',
          confidence_level: 'MEDIUM',
          details: {
            cause_description: 'Mechanical linkage binding or Belimo actuator calibration drift on intake louvers.',
          },
        },
        {
          id: 'impact_energy',
          type: 'IMPACT',
          label: 'Excess Electrical Power Surge',
          category: 'Operational Impact',
          status: 'CRITICAL',
          confidence: 'Observed (+4.2 kW)',
          confidence_level: 'CONFIRMED',
          details: {
            impact_type: 'Energy & Financial Penalty',
            estimated_cost_per_day: '$38.40 USD excess utility cost',
          },
        },
        {
          id: 'impact_comfort',
          type: 'IMPACT',
          label: 'Zone 204 Thermal Discomfort',
          category: 'Operational Impact',
          status: 'WARNING',
          confidence: 'Observed (+8.1°C)',
          confidence_level: 'CONFIRMED',
          details: {
            impact_type: 'Occupant Thermal Comfort Deviation',
            affected_area: 'Floor 2 Conditioned Zone Block 204–210',
          },
        },
        {
          id: 'action_replace_filter',
          type: 'ACTION',
          label: 'Replace MERV-13 Air Filter',
          category: 'Recommended Action',
          status: 'HEALTHY',
          confidence: 'High Priority',
          confidence_level: 'HIGH',
          details: {
            parts_required: '24x24x2 MERV-13 Pleated Filter Cartridge (Qty 4)',
            sop_ref: 'SOP-HVAC-FLT-02',
          },
        },
        {
          id: 'action_check_damper',
          type: 'ACTION',
          label: 'Inspect Damper Actuator Linkage',
          category: 'Recommended Action',
          status: 'HEALTHY',
          confidence: 'Medium Priority',
          confidence_level: 'MEDIUM',
          details: {
            verification: 'Perform 0-100% stroke test via BMS manual override',
            sop_ref: 'SOP-RTU-DAMP-01',
          },
        },
      ],
      edges: [
        { id: 'e1', source: 'asset_7', target: 'sensor_airflow', relationship: 'monitored_by', label: 'Monitors' },
        { id: 'e2', source: 'asset_7', target: 'sensor_temp', relationship: 'monitored_by', label: 'Monitors' },
        { id: 'e3', source: 'asset_7', target: 'sensor_energy', relationship: 'monitored_by', label: 'Monitors' },
        { id: 'e4', source: 'sensor_airflow', target: 'anom_low_airflow', relationship: 'reports_anomaly', label: 'Reports Anomaly' },
        { id: 'e5', source: 'sensor_temp', target: 'anom_high_temp', relationship: 'reports_anomaly', label: 'Reports Anomaly' },
        { id: 'e6', source: 'sensor_airflow', target: 'comp_filter', relationship: 'measures', label: 'Measures Velocity' },
        { id: 'e7', source: 'comp_damper', target: 'comp_filter', relationship: 'depends_on', label: 'Feeds Air' },
        { id: 'e8', source: 'comp_filter', target: 'comp_cooling_coil', relationship: 'depends_on', label: 'Feeds Plenum' },
        { id: 'e9', source: 'comp_cooling_coil', target: 'comp_fan', relationship: 'depends_on', label: 'Supplies Fan' },
        { id: 'e10', source: 'anom_low_airflow', target: 'comp_filter', relationship: 'associated_with', label: 'Restricts Airflow' },
        { id: 'e11', source: 'anom_high_temp', target: 'comp_cooling_coil', relationship: 'associated_with', label: 'Thermal Rise' },
        { id: 'e12', source: 'comp_filter', target: 'cause_primary', relationship: 'caused_by', label: 'Primary Cause' },
        { id: 'e13', source: 'comp_damper', target: 'cause_secondary', relationship: 'caused_by', label: 'Secondary Cause' },
        { id: 'e14', source: 'cause_primary', target: 'impact_energy', relationship: 'produces', label: 'Produces Surge' },
        { id: 'e15', source: 'cause_primary', target: 'impact_comfort', relationship: 'produces', label: 'Causes Discomfort' },
        { id: 'e16', source: 'impact_energy', target: 'action_replace_filter', relationship: 'requires', label: 'Requires Action' },
        { id: 'e17', source: 'impact_comfort', target: 'action_check_damper', relationship: 'requires', label: 'Requires Check' },
      ],
      historical_matches: [
        {
          memory_id: 'MEM-2026-089',
          incident_number: '#089',
          incident_type: 'Intake Filter Particulate Restriction',
          asset_code: 'HVAC-007',
          similarity_pct: 94,
          root_cause: 'Physical particulate loading on intake MERV-13 air filter cartridge creating 36% aerodynamic drag.',
          corrective_action: 'Replaced primary MERV-13 intake filter cartridge and zero-calibrated static differential transducer.',
          timestamp: '2026-08-14 14:20',
        },
        {
          memory_id: 'MEM-2026-104',
          incident_number: '#104',
          incident_type: 'Condenser Coil Fin Fouling',
          asset_code: 'HVAC-007',
          similarity_pct: 87,
          root_cause: 'Severe particulate and pollen accumulation on exterior condenser coil fins inhibiting ambient heat rejection.',
          corrective_action: 'Washed condenser coils with non-acidic foaming chemical coil cleaner and verified fan motor current draw.',
          timestamp: '2026-09-01 12:15',
        },
        {
          memory_id: 'MEM-2026-074',
          incident_number: '#074',
          incident_type: 'Expansion Valve Stepper Sticking',
          asset_code: 'CHILLER-001',
          similarity_pct: 76,
          root_cause: 'Electronic expansion valve (EEV) stepper actuator mechanical friction under thermal cycling.',
          corrective_action: 'Exercised and re-indexed EEV stepper motor; applied dielectric lubricant to actuator spindle.',
          timestamp: '2026-07-29 11:05',
        },
      ],
    };
  }
}
