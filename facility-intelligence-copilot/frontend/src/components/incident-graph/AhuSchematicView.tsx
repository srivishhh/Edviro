import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  ArrowDown,
  ArrowRight,
  ArrowUp,
  Cpu,
  Eye,
  Layers,
  Maximize2,
  Minimize2,
  RotateCcw,
  Sparkles,
  Thermometer,
  Wind,
  Zap,
} from 'lucide-react';
import type {
  IncidentGraphEdge,
  IncidentGraphNode,
  IncidentGraphSummary,
} from '../../services/incidentGraph';

interface AhuSchematicViewProps {
  summary: IncidentGraphSummary | undefined;
  nodes: IncidentGraphNode[];
  edges: IncidentGraphEdge[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
  incidentPathMode: boolean;
  onToggleIncidentPathMode: () => void;
  onResetView: () => void;
}

export function AhuSchematicView({
  summary,
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
  incidentPathMode,
  onToggleIncidentPathMode,
  onResetView,
}: AhuSchematicViewProps) {
  const [isZoomedFit, setIsZoomedFit] = useState(false);

  // Helper lookup map
  const nodeMap = React.useMemo(() => {
    const map = new Map<string, IncidentGraphNode>();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  // Derive anomalies for the Faults Detected summary bar
  const anomalies = React.useMemo(() => {
    return nodes.filter((n) => n.type === 'ANOMALY');
  }, [nodes]);

  // Determine active incident path nodes (nodes on the causal chain for the active incident)
  const incidentPathNodeIds = React.useMemo(() => {
    const pathIds = new Set<string>();
    // Add all active anomalies, sensors with warnings/critical, and root causes
    nodes.forEach((n) => {
      if (n.status === 'CRITICAL' || n.status === 'WARNING') {
        pathIds.add(n.id);
      }
    });

    // Add immediate connected neighbors from edges
    edges.forEach((e) => {
      if (pathIds.has(e.source) || pathIds.has(e.target)) {
        pathIds.add(e.source);
        pathIds.add(e.target);
      }
    });

    return pathIds;
  }, [nodes, edges]);

  // Bidirectional selection & relationship checking
  const isDirectlySelected = (id: string) => selectedNodeId === id;

  const isRelatedOrConnected = (targetId: string): boolean => {
    if (!selectedNodeId) return false;
    if (selectedNodeId === targetId) return true;

    // Direct edge connection
    const hasDirectEdge = edges.some(
      (e) =>
        (e.source === selectedNodeId && e.target === targetId) ||
        (e.target === selectedNodeId && e.source === targetId)
    );
    if (hasDirectEdge) return true;

    // Multi-hop / Semantic mapping across causal tiers:
    if (
      targetId === 'comp_cooling_coil' &&
      (selectedNodeId === 'anom_high_temp' ||
        selectedNodeId === 'sensor_temp' ||
        selectedNodeId === 'cause_primary')
    ) {
      return true;
    }
    if (
      targetId === 'comp_filter' &&
      (selectedNodeId === 'anom_low_airflow' ||
        selectedNodeId === 'sensor_airflow' ||
        selectedNodeId === 'cause_primary' ||
        selectedNodeId === 'action_replace_filter')
    ) {
      return true;
    }
    if (
      targetId === 'comp_damper' &&
      (selectedNodeId === 'anom_low_airflow' ||
        selectedNodeId === 'cause_secondary' ||
        selectedNodeId === 'action_check_damper')
    ) {
      return true;
    }
    if (
      targetId === 'comp_fan' &&
      (selectedNodeId === 'anom_power_surge' ||
        selectedNodeId === 'sensor_energy' ||
        selectedNodeId === 'impact_energy')
    ) {
      return true;
    }
    if (
      targetId === 'comp_condenser' &&
      (selectedNodeId === 'anom_head_pressure' ||
        selectedNodeId === 'sensor_pressure' ||
        selectedNodeId === 'cause_primary')
    ) {
      return true;
    }
    if (
      targetId === 'sensor_temp' &&
      (selectedNodeId === 'anom_high_temp' || selectedNodeId === 'comp_cooling_coil')
    ) {
      return true;
    }
    if (
      targetId === 'sensor_airflow' &&
      (selectedNodeId === 'anom_low_airflow' ||
        selectedNodeId === 'comp_filter' ||
        selectedNodeId === 'comp_damper')
    ) {
      return true;
    }
    if (
      targetId === 'sensor_energy' &&
      (selectedNodeId === 'anom_power_surge' || selectedNodeId === 'comp_fan')
    ) {
      return true;
    }
    if (
      targetId === 'sensor_pressure' &&
      (selectedNodeId === 'comp_filter' ||
        selectedNodeId === 'comp_condenser' ||
        selectedNodeId === 'anom_head_pressure')
    ) {
      return true;
    }
    if (
      targetId === 'impact_comfort' &&
      (selectedNodeId === 'comp_cooling_coil' ||
        selectedNodeId === 'comp_fan' ||
        selectedNodeId === 'anom_high_temp')
    ) {
      return true;
    }

    return false;
  };

  // Node status lookup
  const getNodeStatus = (id: string): 'CRITICAL' | 'WARNING' | 'HEALTHY' => {
    const n = nodeMap.get(id);
    if (!n) return 'HEALTHY';
    if (n.status === 'CRITICAL') return 'CRITICAL';
    if (n.status === 'WARNING') return 'WARNING';
    return 'HEALTHY';
  };

  // Sensor node references
  const tempSensor = nodeMap.get('sensor_temp');
  const airflowSensor = nodeMap.get('sensor_airflow');
  const energySensor = nodeMap.get('sensor_energy');
  const pressureSensor = nodeMap.get('sensor_pressure');

  // Overall facility risk level badge
  const riskLabel =
    summary?.severity === 'CRITICAL'
      ? 'CRITICAL RISK'
      : summary?.severity === 'WARNING'
      ? 'HIGH RISK'
      : 'NORMAL';

  const riskBadgeStyle =
    summary?.severity === 'CRITICAL'
      ? 'bg-rose-50 text-rose-800 border-rose-200'
      : summary?.severity === 'WARNING'
      ? 'bg-amber-50 text-amber-800 border-amber-200'
      : 'bg-emerald-50 text-emerald-800 border-emerald-200';

  return (
    <div className="rounded-3xl bg-white border border-zinc-200/90 shadow-sm overflow-hidden flex flex-col h-full">
      {/* 1. PHYSICAL VIEW CARD HEADER */}
      <div className="p-4 sm:p-5 bg-zinc-50/85 border-b border-zinc-200/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-cyan-50 border border-cyan-200 flex items-center justify-center text-cyan-700 shadow-2xs">
            <Layers size={17} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-cyan-800">
                FACILITY VIEW
              </span>
              <span className="text-zinc-300">•</span>
              <span className="text-[11px] font-mono font-extrabold text-zinc-950 bg-white px-2 py-0.5 rounded border border-zinc-200 shadow-2xs">
                {summary?.asset_code || 'AHU-09'}
              </span>
              <span className="text-zinc-400 font-mono text-[10px]">
                {summary?.asset_id === 7 ? 'HVAC-007' : `HVAC-00${summary?.asset_id || 1}`}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs font-extrabold text-zinc-950">
                Air Handling Unit (AHU) Physical Schematic
              </span>
              <span
                className={`text-[9.5px] font-mono font-bold px-2 py-0.5 rounded-full border ${riskBadgeStyle}`}
              >
                Status: {riskLabel}
              </span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {/* Incident Path Filter Toggle */}
          <button
            onClick={onToggleIncidentPathMode}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer flex items-center gap-1.5 border ${
              incidentPathMode
                ? 'bg-cyan-600 text-white border-cyan-700 shadow-xs'
                : 'bg-white hover:bg-zinc-100 text-zinc-700 border-zinc-200'
            }`}
            title="When enabled, highlights only components on the incident causal path"
          >
            <Sparkles size={13} className={incidentPathMode ? 'text-cyan-200' : 'text-zinc-500'} />
            <span>{incidentPathMode ? 'Incident Path: Active' : 'Focus Incident Path'}</span>
          </button>

          <button
            onClick={() => setIsZoomedFit((z) => !z)}
            className="p-1.5 rounded-xl bg-white hover:bg-zinc-100 border border-zinc-200 text-zinc-600 hover:text-zinc-950 transition-all cursor-pointer"
            title={isZoomedFit ? 'Reset Scale' : 'Fit to Screen'}
          >
            {isZoomedFit ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>

          <button
            onClick={onResetView}
            className="p-1.5 rounded-xl bg-white hover:bg-zinc-100 border border-zinc-200 text-zinc-600 hover:text-cyan-700 transition-all cursor-pointer"
            title="Reset Component & Graph Selection"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      {/* 2. FAULT SUMMARY BAR */}
      <div className="px-4 sm:px-5 py-2.5 bg-amber-50/50 border-b border-amber-200/60 flex items-center justify-between flex-wrap gap-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase font-bold text-amber-950 flex items-center gap-1.5">
            <AlertCircle size={13} className="text-amber-600" />
            FAULTS DETECTED: {anomalies.length > 0 ? anomalies.length : 1}
          </span>
          <span className="text-zinc-400 font-mono text-[10px] hidden sm:inline">
            (Click fault to focus physical component)
          </span>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {anomalies.map((anom) => {
            const isSelected = selectedNodeId === anom.id;
            const dotColor =
              anom.status === 'CRITICAL' ? 'bg-rose-500 animate-pulse' : 'bg-amber-500';
            return (
              <button
                key={anom.id}
                onClick={() => onSelectNode(anom.id)}
                className={`px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold transition-all cursor-pointer flex items-center gap-1.5 border ${
                  isSelected
                    ? 'bg-amber-600 text-white border-amber-700 shadow-xs ring-2 ring-amber-500/20'
                    : 'bg-white hover:bg-amber-100/70 text-amber-950 border-amber-200/90 shadow-2xs'
                }`}
                title={`Select anomaly: ${anom.label}`}
              >
                <span className={`w-2 h-2 rounded-full ${dotColor}`} />
                <span>{anom.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. MAIN 2D/2.5D TECHNICAL AHU SCHEMATIC CANVAS */}
      <div
        className={`flex-1 p-4 sm:p-6 relative overflow-auto bg-[#f8fafc] select-none flex flex-col justify-center min-h-[500px] transition-transform duration-200 ${
          isZoomedFit ? 'scale-95 origin-top' : 'scale-100'
        }`}
      >
        <div className="max-w-4xl mx-auto w-full space-y-4">
          {/* TOP AIRFLOW SECTION LABELS: OUTSIDE AIR & EXHAUST AIR */}
          <div className="flex items-center justify-between text-[11px] font-mono font-bold text-zinc-700 px-3">
            {/* OUTSIDE AIR INLET */}
            <div className="flex items-center gap-2 bg-sky-50 px-3 py-1.5 rounded-xl border border-sky-200 text-sky-950 shadow-2xs">
              <Wind size={14} className="text-sky-600" />
              <div>
                <span className="uppercase tracking-wider font-extrabold block text-[10px] text-sky-900">
                  OUTSIDE AIR
                </span>
                <span className="text-[9.5px] text-sky-700 font-normal">Fresh Air Intake (32°C Ambient)</span>
              </div>
              <ArrowDown size={13} className="text-sky-600 animate-bounce" />
            </div>

            {/* EXHAUST AIR SPILL */}
            <div className="flex items-center gap-2 bg-zinc-100 px-3 py-1.5 rounded-xl border border-zinc-200 text-zinc-700 shadow-2xs">
              <ArrowUp size={13} className="text-zinc-500" />
              <div>
                <span className="uppercase tracking-wider font-extrabold block text-[10px] text-zinc-800">
                  EXHAUST AIR
                </span>
                <span className="text-[9.5px] text-zinc-500 font-normal">Spill & Relief Louver</span>
              </div>
            </div>
          </div>

          {/* MAIN AHU AIR CASING CHAMBER */}
          <div className="p-4 sm:p-5 rounded-3xl bg-white border-2 border-zinc-300 shadow-sm relative overflow-hidden">
            {/* Ductwork Flow Background Texture & Animated Flow Line */}
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none opacity-40"
              preserveAspectRatio="none"
            >
              <defs>
                <pattern
                  id="ahu-duct-grid"
                  width="20"
                  height="20"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M 20 0 L 0 0 0 20"
                    fill="none"
                    stroke="#e2e8f0"
                    strokeWidth="0.75"
                  />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#ahu-duct-grid)" />
              {/* Animated Airflow Line */}
              <line
                x1="0"
                y1="50%"
                x2="100%"
                y2="50%"
                stroke="#0284c7"
                strokeWidth="2.5"
                strokeDasharray="6 6"
                className="animate-flow"
              />
            </svg>

            {/* Subsystems Grid: Damper -> Filter -> Cooling Coil -> Heating Coil -> Supply Fan */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 relative z-10">
              {/* 1. COMPONENT: INTAKE DAMPER */}
              <SchematicComponentCard
                id="comp_damper"
                name="Intake Damper"
                sectionLabel="MIXING DAMPER"
                tag="DAMPER-01"
                status={getNodeStatus('comp_damper')}
                isSelected={isDirectlySelected('comp_damper')}
                isRelated={isRelatedOrConnected('comp_damper')}
                isPathActive={
                  !incidentPathMode || incidentPathNodeIds.has('comp_damper')
                }
                onClick={() => onSelectNode('comp_damper')}
                icon={<Wind size={16} className="text-teal-600" />}
                sensorTap={
                  airflowSensor ? (
                    <SensorTapBadge
                      id="sensor_airflow"
                      label="AIRFLOW-007"
                      value={`${airflowSensor.telemetry?.current_value || '64.0'}%`}
                      status={airflowSensor.status}
                      isSelected={isDirectlySelected('sensor_airflow')}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectNode('sensor_airflow');
                      }}
                    />
                  ) : null
                }
                desc="Outside air modulating louvers & Belimo actuator"
                schematicSymbol="VANE-MIX"
              />

              {/* 2. COMPONENT: PRIMARY AIR FILTER */}
              <SchematicComponentCard
                id="comp_filter"
                name="Primary Air Filter"
                sectionLabel="FILTRATION"
                tag="FILTER-01 (MERV-13)"
                status={getNodeStatus('comp_filter')}
                isSelected={isDirectlySelected('comp_filter')}
                isRelated={isRelatedOrConnected('comp_filter')}
                isPathActive={
                  !incidentPathMode || incidentPathNodeIds.has('comp_filter')
                }
                onClick={() => onSelectNode('comp_filter')}
                icon={<Layers size={16} className="text-amber-600" />}
                sensorTap={
                  pressureSensor ? (
                    <SensorTapBadge
                      id="sensor_pressure"
                      label="DP-007"
                      value={`${pressureSensor.telemetry?.current_value || '4.3'} bar`}
                      status={pressureSensor.status}
                      isSelected={isDirectlySelected('sensor_pressure')}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectNode('sensor_pressure');
                      }}
                    />
                  ) : null
                }
                desc="Deep-pleat particulate filter cartridge bank"
                schematicSymbol="PLEAT-MESH"
              />

              {/* 3. COMPONENT: COOLING COIL */}
              <SchematicComponentCard
                id="comp_cooling_coil"
                name="Cooling Coil"
                sectionLabel="COOLING BLOCK"
                tag="COIL-COOL-01"
                status={getNodeStatus('comp_cooling_coil')}
                isSelected={isDirectlySelected('comp_cooling_coil')}
                isRelated={isRelatedOrConnected('comp_cooling_coil')}
                isPathActive={
                  !incidentPathMode || incidentPathNodeIds.has('comp_cooling_coil')
                }
                onClick={() => onSelectNode('comp_cooling_coil')}
                icon={<Thermometer size={16} className="text-sky-600" />}
                sensorTap={
                  tempSensor ? (
                    <SensorTapBadge
                      id="sensor_temp"
                      label="TEMP-007"
                      value={`${tempSensor.telemetry?.current_value || '30.1'}°C`}
                      status={tempSensor.status}
                      isSelected={isDirectlySelected('sensor_temp')}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectNode('sensor_temp');
                      }}
                    />
                  ) : null
                }
                desc="Chilled water / DX copper-tube aluminum-fin block"
                schematicSymbol="COIL-FINS"
              />

              {/* 4. COMPONENT: HEATING COIL */}
              <SchematicComponentCard
                id="comp_heating_coil"
                name="Heating Coil"
                sectionLabel="HEATING BLOCK"
                tag="COIL-HEAT-01"
                status={getNodeStatus('comp_heating_coil')}
                isSelected={isDirectlySelected('comp_heating_coil')}
                isRelated={isRelatedOrConnected('comp_heating_coil')}
                isPathActive={
                  !incidentPathMode || incidentPathNodeIds.has('comp_heating_coil')
                }
                onClick={() => onSelectNode('comp_heating_coil')}
                icon={<Activity size={16} className="text-rose-600" />}
                desc="Hot water auxiliary pre-heat coil & 2-way valve"
                schematicSymbol="COIL-HEAT"
              />

              {/* 5. COMPONENT: SUPPLY AIR FAN */}
              <SchematicComponentCard
                id="comp_fan"
                name="Supply Air Fan"
                sectionLabel="PLENUM FAN"
                tag="FAN-01 (15kW VFD)"
                status={getNodeStatus('comp_fan')}
                isSelected={isDirectlySelected('comp_fan')}
                isRelated={isRelatedOrConnected('comp_fan')}
                isPathActive={
                  !incidentPathMode || incidentPathNodeIds.has('comp_fan')
                }
                onClick={() => onSelectNode('comp_fan')}
                icon={<Cpu size={16} className="text-indigo-600" />}
                sensorTap={
                  energySensor ? (
                    <SensorTapBadge
                      id="sensor_energy"
                      label="ENERGY-007"
                      value={`${energySensor.telemetry?.current_value || '12.3'} kW`}
                      status={energySensor.status}
                      isSelected={isDirectlySelected('sensor_energy')}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectNode('sensor_energy');
                      }}
                    />
                  ) : null
                }
                desc="Direct-drive backward plenum centrifugal rotor"
                schematicSymbol="FAN-ROTOR"
              />
            </div>

            {/* CONDENSER / COMPRESSOR SECTION IF PRESENT (e.g. for RTU-07 Circuit 1) */}
            {nodeMap.has('comp_condenser') && (
              <div className="pt-3.5 border-t border-zinc-200 mt-3.5">
                <div className="flex items-center justify-between text-[10px] font-mono font-bold text-zinc-600 mb-2">
                  <span className="uppercase text-rose-900 flex items-center gap-1.5 font-bold">
                    <Zap size={12} className="text-rose-600" />
                    EXTERIOR REFRIGERANT CONDENSER & COMPRESSOR CIRCUIT
                  </span>
                  <span className="text-zinc-400 font-mono text-[9.5px]">
                    Heat Rejection Subsystem (Circuit 1)
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <SchematicComponentCard
                    id="comp_condenser"
                    name="Exterior Condenser Coil & Compressor"
                    sectionLabel="HEAT REJECTION"
                    tag="COND-01 (Circuit 1)"
                    status={getNodeStatus('comp_condenser')}
                    isSelected={isDirectlySelected('comp_condenser')}
                    isRelated={isRelatedOrConnected('comp_condenser')}
                    isPathActive={
                      !incidentPathMode || incidentPathNodeIds.has('comp_condenser')
                    }
                    onClick={() => onSelectNode('comp_condenser')}
                    icon={<Zap size={16} className="text-rose-600" />}
                    sensorTap={
                      pressureSensor ? (
                        <SensorTapBadge
                          id="sensor_pressure"
                          label="HEAD-PRESS-007"
                          value={`${pressureSensor.telemetry?.current_value || '31.5'} bar`}
                          status={pressureSensor.status}
                          isSelected={isDirectlySelected('sensor_pressure')}
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectNode('sensor_pressure');
                          }}
                        />
                      ) : null
                    }
                    desc="Air-cooled micro-channel heat rejection coil & compressor bank"
                    schematicSymbol="COND-COIL"
                  />
                </div>
              </div>
            )}

            {/* AIRFLOW DIRECTION ARROW STEPS */}
            <div className="hidden md:flex items-center justify-between text-zinc-500 px-4 pt-3 font-mono text-[10px] border-t border-zinc-100 mt-3">
              <div className="flex items-center gap-1 text-cyan-800 font-bold">
                <span className="w-2 h-2 rounded-full bg-cyan-600 animate-pulse" />
                <span>Return & Intake Air</span>
                <ArrowRight size={12} className="text-cyan-600" />
              </div>

              <div className="flex items-center gap-1 text-zinc-500">
                <span>Particulate Filtration</span>
                <ArrowRight size={12} className="text-zinc-400" />
              </div>

              <div className="flex items-center gap-1 text-zinc-500">
                <span>Thermal Conditioning</span>
                <ArrowRight size={12} className="text-zinc-400" />
              </div>

              <div className="flex items-center gap-1 text-cyan-800 font-bold">
                <span>Plenum Fan Compression</span>
                <ArrowRight size={12} className="text-cyan-600" />
              </div>
            </div>
          </div>

          {/* BOTTOM SECTION: RETURN AIR & TO ZONE SUPPLY */}
          <div className="flex flex-col sm:flex-row items-center justify-between text-[11px] font-mono gap-3 px-3">
            {/* RETURN AIR FROM ZONE */}
            <div className="flex items-center gap-2.5 bg-zinc-100/90 px-3.5 py-2 rounded-2xl border border-zinc-200 text-zinc-800 shadow-2xs">
              <ArrowUp size={14} className="text-zinc-600" />
              <div>
                <span className="uppercase tracking-wider font-extrabold block text-[10px] text-zinc-900">
                  RETURN AIR
                </span>
                <span className="text-[9.5px] text-zinc-500 font-normal">
                  From Zone 204 Return Air Grilles
                </span>
              </div>
            </div>

            {/* SUPPLY AIR TO ZONE */}
            <div
              onClick={() => onSelectNode('impact_comfort')}
              className={`flex items-center gap-2.5 px-4 py-2 rounded-2xl border cursor-pointer transition-all shadow-2xs ${
                selectedNodeId === 'impact_comfort'
                  ? 'bg-cyan-50 border-cyan-500 text-cyan-950 font-extrabold ring-4 ring-cyan-500/20'
                  : 'bg-white hover:bg-zinc-50 border-zinc-200 text-zinc-800'
              }`}
              title="Conditioned supply air delivery target"
            >
              <div className="w-2.5 h-2.5 rounded-full bg-cyan-600" />
              <div>
                <span className="uppercase tracking-wider font-extrabold block text-[10px] text-cyan-950">
                  SUPPLY AIR → TO ZONE
                </span>
                <span className="text-[9.5px] text-zinc-500 font-normal">
                  Conditioned Zone Block 204–210
                </span>
              </div>
              <ArrowRight size={14} className="text-cyan-700" />
            </div>
          </div>
        </div>
      </div>

      {/* 4. TECHNICAL LEGEND & INTERACTION GUIDANCE */}
      <div className="p-3.5 bg-zinc-50/90 border-t border-zinc-200/80 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-zinc-600">
        <div className="flex items-center gap-3">
          <span className="font-bold text-zinc-800">Fault Markers:</span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            <span className="font-semibold text-rose-900">Critical Fault</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="font-semibold text-amber-900">Warning Anomaly</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="font-semibold text-emerald-900">Normal</span>
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-500 text-[10px]">
          <Eye size={12} className="text-cyan-600" />
          <span>Click any physical component or sensor tap to synchronize with Causal Flow</span>
        </div>
      </div>
    </div>
  );
}

// Sub-component: Technical Schematic Component Card
interface SchematicComponentCardProps {
  id: string;
  name: string;
  sectionLabel: string;
  tag: string;
  status: 'CRITICAL' | 'WARNING' | 'HEALTHY';
  isSelected: boolean;
  isRelated: boolean;
  isPathActive: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  sensorTap?: React.ReactNode;
  desc: string;
  schematicSymbol: string;
}

function SchematicComponentCard({
  name,
  sectionLabel,
  tag,
  status,
  isSelected,
  isRelated,
  isPathActive,
  onClick,
  icon,
  sensorTap,
  desc,
}: SchematicComponentCardProps) {
  let statusBadge = 'bg-emerald-50 text-emerald-800 border-emerald-200';
  let faultMarker = 'bg-emerald-500';

  if (status === 'CRITICAL') {
    statusBadge = 'bg-rose-50 text-rose-800 border-rose-200 font-bold';
    faultMarker = 'bg-rose-500 ring-4 ring-rose-200 animate-pulse';
  } else if (status === 'WARNING') {
    statusBadge = 'bg-amber-50 text-amber-900 border-amber-200 font-bold';
    faultMarker = 'bg-amber-500 ring-4 ring-amber-200';
  }

  return (
    <div
      onClick={onClick}
      className={`p-3.5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between select-none shadow-2xs relative ${
        isSelected
          ? 'bg-white border-2 border-cyan-600 shadow-[0_4px_22px_rgba(8,145,178,0.25)] ring-4 ring-cyan-500/20 z-20'
          : isRelated
          ? 'bg-white border-2 border-cyan-400/90 shadow-xs z-10'
          : 'bg-zinc-50/70 hover:bg-white border-zinc-200 hover:border-zinc-300'
      } ${!isPathActive ? 'opacity-30 grayscale-[25%]' : 'opacity-100'}`}
    >
      {/* Top row: Section label & Fault Marker */}
      <div className="flex items-center justify-between gap-1">
        <span className="text-[9px] font-mono font-bold tracking-wider text-zinc-400 uppercase truncate">
          {sectionLabel}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className={`w-2.5 h-2.5 rounded-full ${faultMarker}`} />
          <span className={`text-[8.5px] font-mono px-1.5 py-0.2 rounded border ${statusBadge}`}>
            {status}
          </span>
        </div>
      </div>

      {/* Component Symbol & Title */}
      <div className="space-y-1 py-2.5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-white border border-zinc-200 flex items-center justify-center shadow-2xs shrink-0">
            {icon}
          </div>
          <div className="min-w-0">
            <div className="text-[9.5px] font-mono text-zinc-400 font-semibold truncate">
              {tag}
            </div>
            <div className="text-xs font-extrabold text-zinc-950 leading-tight truncate" title={name}>
              {name}
            </div>
          </div>
        </div>
        <div className="text-[10px] text-zinc-500 leading-normal line-clamp-1">{desc}</div>
      </div>

      {/* Sensor Tap Attachment if present */}
      {sensorTap && <div className="pt-1.5 border-t border-zinc-100">{sensorTap}</div>}
    </div>
  );
}

// Sub-component: Attached Sensor Tap Badge
interface SensorTapBadgeProps {
  id: string;
  label: string;
  value: string;
  status: string;
  isSelected: boolean;
  onClick: (e: React.MouseEvent) => void;
}

function SensorTapBadge({
  label,
  value,
  status,
  isSelected,
  onClick,
}: SensorTapBadgeProps) {
  const isCritical = status === 'CRITICAL';
  const isWarning = status === 'WARNING';
  const isAlert = isCritical || isWarning;

  return (
    <div
      onClick={onClick}
      className={`p-1.5 rounded-xl border flex items-center justify-between text-[9px] font-mono cursor-pointer transition-all shadow-2xs ${
        isSelected
          ? 'bg-cyan-50 border-cyan-500 text-cyan-950 ring-2 ring-cyan-500/20 font-bold'
          : isAlert
          ? 'bg-amber-50/90 border-amber-200 text-amber-950 font-bold hover:bg-amber-100'
          : 'bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-50'
      }`}
      title={`Telemetry sensor tap: ${label}`}
    >
      <div className="flex items-center gap-1 truncate">
        <Zap size={10} className={isAlert ? 'text-amber-600' : 'text-cyan-600'} />
        <span className="truncate">{label}</span>
      </div>
      <span
        className={`shrink-0 ml-1 font-extrabold ${
          isCritical ? 'text-rose-700' : isWarning ? 'text-amber-800' : 'text-emerald-700'
        }`}
      >
        {value}
      </span>
    </div>
  );
}
