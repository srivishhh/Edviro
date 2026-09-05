import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Boxes,
  Layers,
  Network,
  SlidersHorizontal,
} from 'lucide-react';
import { getTwinAssets } from '../services/twin';
import { HealthBadge } from '../components/ui/SeverityBadge';
import { LoadingState } from '../components/ui/States';

interface TopologyNode {
  id: string;
  name: string;
  type: 'BUILDING' | 'FLOOR' | 'HVAC' | 'CHILLER' | 'HEAT_PUMP' | 'SENSOR' | 'ZONE';
  health: number;
  status: 'HEALTHY' | 'WARNING' | 'CRITICAL';
  level: string;
  connectedTo: string[];
  metrics?: {
    temp?: number;
    power?: number;
    flow?: number;
    pressure?: number;
  };
}

const INITIAL_TOPOLOGY_NODES: TopologyNode[] = [
  {
    id: 'FAC-001',
    name: 'LBNL Facility Digital Twin',
    type: 'BUILDING',
    health: 91,
    status: 'HEALTHY',
    level: 'Campus Root',
    connectedTo: ['FL-01', 'FL-02', 'FL-03'],
  },
  {
    id: 'FL-01',
    name: 'Floor 1 — Auditorium & Labs',
    type: 'FLOOR',
    health: 98,
    status: 'HEALTHY',
    level: 'Level 1',
    connectedTo: ['HVAC-001', 'ZONE-101'],
  },
  {
    id: 'FL-02',
    name: 'Floor 2 — Mechanical & Zone Deck',
    type: 'FLOOR',
    health: 72,
    status: 'WARNING',
    level: 'Level 2',
    connectedTo: ['HVAC-007', 'SENSOR-T02', 'ZONE-204'],
  },
  {
    id: 'FL-03',
    name: 'Floor 3 — Library & Server Room',
    type: 'FLOOR',
    health: 95,
    status: 'HEALTHY',
    level: 'Level 3',
    connectedTo: ['HVAC-003', 'ZONE-301'],
  },
  {
    id: 'HVAC-007',
    name: 'LBNL RTU Rooftop Unit #7',
    type: 'HVAC',
    health: 68,
    status: 'WARNING',
    level: 'Mechanical Deck (L2)',
    connectedTo: ['CHILLER-001', 'SENSOR-T02', 'ZONE-204'],
    metrics: { temp: 16.1, power: 140.6, flow: 97.6, pressure: 31.5 },
  },
  {
    id: 'HVAC-001',
    name: 'Auditorium Ventilation Unit',
    type: 'HVAC',
    health: 97,
    status: 'HEALTHY',
    level: 'Mechanical Deck (L1)',
    connectedTo: ['CHILLER-001', 'ZONE-101'],
    metrics: { temp: 21.5, power: 4.8, flow: 96, pressure: 3.8 },
  },
  {
    id: 'CHILLER-001',
    name: 'Primary Water Chiller',
    type: 'CHILLER',
    health: 94,
    status: 'HEALTHY',
    level: 'Basement Central Plant',
    connectedTo: ['HP-001', 'HVAC-007', 'HVAC-001'],
    metrics: { temp: 7.2, power: 34.5, flow: 98, pressure: 6.2 },
  },
  {
    id: 'HP-001',
    name: 'Geothermal Heat Pump',
    type: 'HEAT_PUMP',
    health: 96,
    status: 'HEALTHY',
    level: 'Basement Central Plant',
    connectedTo: ['CHILLER-001'],
    metrics: { temp: 18.0, power: 18.2, flow: 92, pressure: 4.5 },
  },
  {
    id: 'SENSOR-T02',
    name: 'LBNL RTU Refrigerant & Head Transducer',
    type: 'SENSOR',
    health: 99,
    status: 'HEALTHY',
    level: 'RTU Circuit 1',
    connectedTo: ['HVAC-007'],
    metrics: { temp: 41.3, power: 0.1, flow: 97.6, pressure: 31.5 },
  },
  {
    id: 'ZONE-204',
    name: 'Conditioned Zone Block 204–210',
    type: 'ZONE',
    health: 82,
    status: 'WARNING',
    level: 'Floor 2 East Wing',
    connectedTo: ['HVAC-007'],
  },
];

export default function DigitalTwin() {
  const [nodes, setNodes] = useState<TopologyNode[]>(INITIAL_TOPOLOGY_NODES);
  const [loading, setLoading] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string>('HVAC-007');
  const [filterType, setFilterType] = useState<string>('ALL');

  useEffect(() => {
    let isActive = true;

    const loadTwin = async (silent = false) => {
      try {
        const twinAssets = await getTwinAssets();
        if (isActive && twinAssets && twinAssets.length > 0) {
          setNodes((prevNodes) =>
            prevNodes.map((node) => {
              if (node.id === 'HVAC-007') {
                const asset7 = twinAssets.find((a) => a.asset_id === 7);
                if (asset7 && asset7.current_state) {
                  return {
                    ...node,
                    health: Math.round(asset7.health_score || node.health),
                    status: (asset7.status?.toUpperCase() as any) || node.status,
                    metrics: {
                      temp: asset7.current_state.temperature,
                      power: asset7.current_state.energy_kw,
                      flow: asset7.current_state.airflow,
                      pressure: asset7.current_state.pressure,
                    },
                  };
                }
              }
              return node;
            })
          );
        }
      } catch {
        // Fallback gracefully
      } finally {
        if (isActive && !silent) {
          setLoading(false);
        }
      }
    };

    void loadTwin(false);
    const interval = setInterval(() => void loadTwin(true), 3000);

    return () => {
      isActive = false;
      clearInterval(interval);
    };
  }, []);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[4];

  if (loading) {
    return <LoadingState message="Constructing Digital Twin Graph Topology..." />;
  }

  const filteredNodes = nodes.filter(
    (n) => filterType === 'ALL' || n.type === filterType
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="saas-card p-6 md:p-8 space-y-3 bg-white">
        <div className="flex items-center gap-2 text-zinc-500">
          <Boxes size={16} />
          <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Thermodynamic Spatial Graph</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-950 editorial-title tracking-tight">
          Digital Twin Topology
        </h1>
        <p className="text-zinc-600 text-xs sm:text-sm max-w-2xl leading-relaxed">
          Interactive dependency network connecting building zones, HVAC equipment, central chillers, and telemetry sensor nodes with live cross-stream validation.
        </p>
      </div>

      {/* Filter Category Pills */}
      <div className="flex items-center gap-2 flex-wrap">
        {['ALL', 'BUILDING', 'FLOOR', 'HVAC', 'CHILLER', 'HEAT_PUMP', 'SENSOR', 'ZONE'].map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
              filterType === type
                ? 'bg-zinc-900 text-white font-semibold'
                : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
            }`}
          >
            {type.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Main Split Layout: Left Node Grid / Right Live Inspector */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Interactive Topology Nodes */}
        <div className="lg:col-span-2 grid gap-4 sm:grid-cols-2">
          {filteredNodes.map((node) => {
            const isSelected = selectedNode.id === node.id;
            return (
              <div
                key={node.id}
                onClick={() => setSelectedNodeId(node.id)}
                className={`saas-card p-5 cursor-pointer transition-all space-y-3 ${
                  isSelected
                    ? 'border-zinc-900 ring-2 ring-zinc-900/10 shadow-md bg-white'
                    : 'hover:border-zinc-300 bg-zinc-50/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-zinc-900 bg-zinc-100 px-2 py-0.5 rounded border border-zinc-200">
                        {node.id}
                      </span>
                      <span className="text-[10px] uppercase font-bold text-zinc-400">{node.type}</span>
                    </div>
                    <h3 className="text-sm font-bold text-zinc-900">{node.name}</h3>
                  </div>

                  <HealthBadge score={node.health} />
                </div>

                <div className="text-xs text-zinc-500 font-mono">{node.level}</div>

                {node.metrics && (
                  <div className="grid grid-cols-3 gap-2 pt-2 border-t border-zinc-100 text-center font-mono">
                    <div className="bg-zinc-50 rounded-lg p-1.5 border border-zinc-100">
                      <span className="text-[10px] text-zinc-400 block">Temp</span>
                      <span className="text-xs font-bold text-zinc-800">{node.metrics.temp}°C</span>
                    </div>
                    <div className="bg-zinc-50 rounded-lg p-1.5 border border-zinc-100">
                      <span className="text-[10px] text-zinc-400 block">Power</span>
                      <span className="text-xs font-bold text-zinc-800">{node.metrics.power}kW</span>
                    </div>
                    <div className="bg-zinc-50 rounded-lg p-1.5 border border-zinc-100">
                      <span className="text-[10px] text-zinc-400 block">Flow</span>
                      <span className="text-xs font-bold text-zinc-800">{node.metrics.flow}%</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Right: Live Selected Node Graph Inspector */}
        <div className="lg:col-span-1 space-y-6">
          <div className="saas-card p-6 space-y-5 bg-white sticky top-6">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-4">
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-mono font-bold text-zinc-400">Node Inspector</span>
                <h3 className="text-lg font-bold text-zinc-900">{selectedNode.name}</h3>
              </div>
              <HealthBadge score={selectedNode.health} />
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-zinc-100">
                <span className="text-zinc-500 font-mono">Identifier:</span>
                <span className="font-mono font-bold text-zinc-900">{selectedNode.id}</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-zinc-100">
                <span className="text-zinc-500 font-mono">Classification:</span>
                <span className="font-semibold text-zinc-800">{selectedNode.type}</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-zinc-100">
                <span className="text-zinc-500 font-mono">Location Deck:</span>
                <span className="text-zinc-800 font-mono">{selectedNode.level}</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-zinc-100">
                <span className="text-zinc-500 font-mono">Operating Status:</span>
                <span className={`font-mono font-bold ${
                  selectedNode.status === 'HEALTHY' ? 'text-emerald-700' : 'text-amber-700'
                }`}>
                  {selectedNode.status}
                </span>
              </div>
            </div>

            {selectedNode.metrics && (
              <div className="space-y-2 pt-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 block">
                  Live Sensor Stream
                </span>
                <div className="grid grid-cols-2 gap-2 font-mono">
                  <div className="p-2.5 rounded-xl bg-zinc-50 border border-zinc-200">
                    <span className="text-[10px] text-zinc-500 block">Temperature</span>
                    <span className="text-sm font-bold text-zinc-900">{selectedNode.metrics.temp}°C</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-zinc-50 border border-zinc-200">
                    <span className="text-[10px] text-zinc-500 block">Power Demand</span>
                    <span className="text-sm font-bold text-zinc-900">{selectedNode.metrics.power} kW</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-zinc-50 border border-zinc-200">
                    <span className="text-[10px] text-zinc-500 block">Airflow Velocity</span>
                    <span className="text-sm font-bold text-zinc-900">{selectedNode.metrics.flow}%</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-zinc-50 border border-zinc-200">
                    <span className="text-[10px] text-zinc-500 block">Head Pressure</span>
                    <span className="text-sm font-bold text-zinc-900">{selectedNode.metrics.pressure || 3.8} bar</span>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2.5 pt-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 block">
                Topological Dependencies
              </span>
              <div className="space-y-1.5">
                {selectedNode.connectedTo.map((target) => (
                  <div
                    key={target}
                    className="p-2.5 rounded-xl bg-zinc-50 border border-zinc-200/80 flex items-center justify-between text-xs font-mono text-zinc-700"
                  >
                    <div className="flex items-center gap-2">
                      <Layers size={13} className="text-zinc-400" />
                      <span>{target}</span>
                    </div>
                    <ArrowRight size={12} className="text-zinc-400" />
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 space-y-2">
              <Link
                to={`/incident-graph?incident_id=101`}
                className="w-full py-2.5 px-4 rounded-xl bg-cyan-950 hover:bg-cyan-900 border border-cyan-700/80 text-cyan-200 text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-2xs"
              >
                <Network size={14} />
                <span>View Incident Relationships</span>
              </Link>

              <Link
                to={`/what-if?assetId=${selectedNode.id}`}
                className="w-full py-2.5 px-4 rounded-xl bg-zinc-950 hover:bg-zinc-800 text-white text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-2xs"
              >
                <SlidersHorizontal size={14} />
                <span>Simulate Operational Changes</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
