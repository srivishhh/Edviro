import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Boxes,
  Brain,
  CheckCircle2,
  ChevronDown,
  Compass,
  ExternalLink,
  Gauge,
  Info,
  Network,
  RotateCcw,
  Wind,
  Zap,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import {
  fetchIncidentRelationshipGraph,
  fetchIncidentSummaries,
  type IncidentGraphNode,
  type IncidentGraphResponse,
  type IncidentGraphSummary,
  type NodeType,
  type SimilarHistoricalIncident,
} from '../services/incidentGraph';
import { LoadingState } from '../components/ui/States';
import { AhuSchematicView } from '../components/incident-graph/AhuSchematicView';
import { CausalExplanationPanel } from '../components/incident-graph/CausalExplanationPanel';

// Layout tier definitions for directed causal DAG
const TIER_COLUMNS: Record<NodeType, number> = {
  ASSET: 0,
  SENSOR: 0,
  INCIDENT: 0,
  ANOMALY: 1,
  COMPONENT: 2,
  ROOT_CAUSE: 3,
  IMPACT: 4,
  ACTION: 5,
};

const TIER_HEADERS = [
  { tier: 0, label: 'OBSERVATIONS', sub: 'Asset & Sensor Telemetry' },
  { tier: 1, label: 'ANOMALIES', sub: 'Detected Deviations' },
  { tier: 2, label: 'AFFECTED COMPONENTS', sub: 'Physical Subsystems' },
  { tier: 3, label: 'POSSIBLE CAUSES', sub: 'Causal Hypotheses' },
  { tier: 4, label: 'OPERATIONAL IMPACT', sub: 'Energy & Zone Comfort' },
  { tier: 5, label: 'RECOMMENDED ACTIONS', sub: 'Corrective Remediation' },
];

export default function IncidentGraph() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialIncidentId = searchParams.get('incident_id') || searchParams.get('alert_id') || '101';

  const [incidentList, setIncidentList] = useState<IncidentGraphSummary[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>(initialIncidentId);
  const [graphData, setGraphData] = useState<IncidentGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [incidentPathMode, setIncidentPathMode] = useState<boolean>(false);

  // Interactive Canvas Transforms (Pan & Zoom)
  const [scale, setScale] = useState<number>(0.78);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 20, y: 20 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLDivElement>(null);

  // Selected memory modal
  const [selectedMemory, setSelectedMemory] = useState<SimilarHistoricalIncident | null>(null);

  // 1. Fetch available incidents list
  useEffect(() => {
    let isActive = true;
    void (async () => {
      try {
        const summaries = await fetchIncidentSummaries();
        if (isActive) {
          setIncidentList(summaries);
          if (
            !searchParams.get('incident_id') &&
            !searchParams.get('alert_id') &&
            summaries.length > 0
          ) {
            setSelectedIncidentId(String(summaries[0].incident_id));
          }
        }
      } catch {
        // Fallback handled in service
      }
    })();
    return () => {
      isActive = false;
    };
  }, []);

  // 2. Fetch full relationship graph on incident change
  useEffect(() => {
    let isActive = true;
    setLoading(true);
    void (async () => {
      try {
        const data = await fetchIncidentRelationshipGraph(selectedIncidentId);
        if (isActive) {
          setGraphData(data);
          // Default select the primary cause or first anomaly node for instant inspection
          const defaultNode =
            data.nodes.find((n) => n.id === 'cause_primary') ||
            data.nodes.find((n) => n.type === 'ANOMALY') ||
            data.nodes[0];
          if (defaultNode) {
            setSelectedNodeId(defaultNode.id);
          }
        }
      } catch {
        // Handled in service
      } finally {
        if (isActive) setLoading(false);
      }
    })();
    return () => {
      isActive = false;
    };
  }, [selectedIncidentId]);

  const handleIncidentSelect = (id: string) => {
    setSelectedIncidentId(id);
    setSearchParams({ incident_id: id });
    setPan({ x: 20, y: 20 });
    setScale(0.78);
  };

  // Node position calculation for directed causal DAG layout
  const { nodePositions, columnWidths, canvasWidth, canvasHeight } = useMemo(() => {
    if (!graphData) {
      return { nodePositions: {}, columnWidths: [], canvasWidth: 2100, canvasHeight: 850 };
    }

    const tierGroups: Record<number, IncidentGraphNode[]> = {
      0: [],
      1: [],
      2: [],
      3: [],
      4: [],
      5: [],
    };

    graphData.nodes.forEach((node) => {
      const tier = TIER_COLUMNS[node.type] ?? 0;
      tierGroups[tier].push(node);
    });

    // Asset node placed at top of tier 0, followed by sensors
    tierGroups[0].sort((a, b) => (a.type === 'ASSET' ? -1 : b.type === 'ASSET' ? 1 : 0));

    const positions: Record<string, { x: number; y: number; width: number; height: number }> = {};
    // Generous column pitch and node dimensions for complete readability & no overlap
    const colXOffsets = [50, 380, 710, 1040, 1370, 1700];
    const nodeWidth = 270;
    const nodeHeight = 104;
    const startY = 120;
    const gapY = 32;

    let maxBottom = 820;

    Object.entries(tierGroups).forEach(([tierStr, nodes]) => {
      const tier = parseInt(tierStr, 10);
      const colX = colXOffsets[tier] || 50 + tier * 330;

      nodes.forEach((node, idx) => {
        const y = startY + idx * (nodeHeight + gapY);
        positions[node.id] = {
          x: colX,
          y,
          width: nodeWidth,
          height: nodeHeight,
        };
        if (y + nodeHeight + 80 > maxBottom) {
          maxBottom = y + nodeHeight + 80;
        }
      });
    });

    return {
      nodePositions: positions,
      columnWidths: colXOffsets,
      canvasWidth: 2050,
      canvasHeight: Math.max(840, maxBottom),
    };
  }, [graphData]);

  // Connected nodes & edges calculation for highlighting
  const { connectedNodeIds, activeEdgeIds } = useMemo(() => {
    if (!selectedNodeId || !graphData) {
      return { connectedNodeIds: new Set<string>(), activeEdgeIds: new Set<string>() };
    }
    const connectedNodes = new Set<string>([selectedNodeId]);
    const activeEdges = new Set<string>();

    graphData.edges.forEach((edge) => {
      if (edge.source === selectedNodeId) {
        connectedNodes.add(edge.target);
        activeEdges.add(edge.id);
      }
      if (edge.target === selectedNodeId) {
        connectedNodes.add(edge.source);
        activeEdges.add(edge.id);
      }
    });

    return { connectedNodeIds: connectedNodes, activeEdgeIds: activeEdges };
  }, [selectedNodeId, graphData]);

  // Pan and drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // only left click
    setIsPanning(true);
    setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setPan({ x: e.clientX - startPan.x, y: e.clientY - startPan.y });
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleZoomIn = () => setScale((s) => Math.min(1.8, s + 0.15));
  const handleZoomOut = () => setScale((s) => Math.max(0.45, s - 0.15));
  const handleResetView = () => {
    setScale(0.78);
    setPan({ x: 20, y: 20 });
    setSelectedNodeId(null);
  };

  const selectedNode = graphData?.nodes.find((n) => n.id === selectedNodeId) || null;

  if (loading && !graphData) {
    return <LoadingState message="Synthesizing AI Incident Relationship Graph..." />;
  }

  const summary = graphData?.summary;

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. TOP HEADER BANNER (Light Theme Editorial SaaS Card) */}
      <div className="saas-card p-6 md:p-8 space-y-4 bg-white border border-zinc-200/90 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2 text-zinc-500">
            <Network size={16} className="text-cyan-600" />
            <span className="text-[10px] uppercase tracking-[0.2em] font-mono font-bold text-zinc-600">
              Autonomous Causal Dependency Network
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-zinc-950 editorial-title">
            Incident Relationship & Facility Graph
          </h1>
          <p className="text-zinc-600 text-xs sm:text-sm leading-relaxed">
            Unified physical facility schematic and multi-tier causal graph. Identifies where an anomaly is physically located, which component is affected, what sensor detected it, why it is occurring, and its operational impact.
          </p>
        </div>

        {/* Incident Selector Dropdown */}
        <div className="bg-zinc-50/80 border border-zinc-200/90 p-3 rounded-2xl flex flex-col gap-1.5 min-w-[320px] shadow-2xs">
          <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-zinc-500">
            Selected Incident
          </span>
          <div className="relative">
            <select
              value={selectedIncidentId}
              onChange={(e) => handleIncidentSelect(e.target.value)}
              className="w-full appearance-none bg-white border border-zinc-300 hover:border-cyan-600 text-zinc-950 text-xs font-semibold py-2 px-3 pr-8 rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500/30 cursor-pointer transition-all shadow-xs"
            >
              {incidentList.map((inc) => (
                <option key={inc.incident_id} value={inc.incident_id}>
                  #{inc.incident_id} — {inc.incident_name} ({inc.severity})
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-2.5 text-zinc-400 pointer-events-none" />
          </div>
          <span className="text-[10px] text-zinc-500 font-mono">
            {summary ? `Asset: ${summary.asset_code} • ${summary.confidence}` : 'Loading active alerts...'}
          </span>
        </div>
      </div>

      {/* 2. INCIDENT SUMMARY HUD BAR */}
      {summary && (
        <div className="p-4 md:p-5 rounded-2xl bg-white border border-zinc-200/90 text-zinc-800 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
            <div>
              <span className="text-[10px] text-zinc-500 block uppercase font-bold tracking-wider">Incident</span>
              <span className="font-extrabold text-zinc-950 text-sm">{summary.incident_name}</span>
            </div>
            <div className="h-8 w-px bg-zinc-200/80 hidden sm:block" />
            <div>
              <span className="text-[10px] text-zinc-500 block uppercase font-bold tracking-wider">Severity</span>
              <span
                className={`px-2.5 py-0.5 rounded-full font-bold text-[11px] inline-block ${
                  summary.severity === 'CRITICAL'
                    ? 'bg-rose-50 text-rose-800 border border-rose-200'
                    : summary.severity === 'WARNING'
                    ? 'bg-amber-50 text-amber-800 border border-amber-200'
                    : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                }`}
              >
                {summary.severity}
              </span>
            </div>
            <div className="h-8 w-px bg-zinc-200/80 hidden sm:block" />
            <div>
              <span className="text-[10px] text-zinc-500 block uppercase font-bold tracking-wider">Asset Target</span>
              <span className="font-bold text-cyan-700 font-mono">{summary.asset_code}</span>
            </div>
            <div className="h-8 w-px bg-zinc-200/80 hidden md:block" />
            <div>
              <span className="text-[10px] text-zinc-500 block uppercase font-bold tracking-wider">Confidence</span>
              <span className="font-bold text-emerald-700 font-mono">{summary.confidence}</span>
            </div>
            <div className="h-8 w-px bg-zinc-200/80 hidden md:block" />
            <div>
              <span className="text-[10px] text-zinc-500 block uppercase font-bold tracking-wider">Affected Subsystems</span>
              <span className="font-bold text-zinc-950">{summary.affected_components_count} Components</span>
            </div>
            <div className="h-8 w-px bg-zinc-200/80 hidden lg:block" />
            <div>
              <span className="text-[10px] text-zinc-500 block uppercase font-bold tracking-wider">Energy Impact</span>
              <span className="font-bold text-amber-700 font-mono">{summary.energy_impact}</span>
            </div>
          </div>

          {/* Cross-Feature Links */}
          <div className="flex items-center gap-2.5 shrink-0">
            <Link
              to={`/x-ray?asset_id=${summary.asset_id}&alert_id=${summary.incident_id}`}
              className="px-3.5 py-2 rounded-xl bg-cyan-50 hover:bg-cyan-100 border border-cyan-300 text-cyan-950 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
              title="Open deterministic multi-agent root cause diagnosis"
            >
              <Gauge size={13} className="text-cyan-700" />
              <span>Investigate with X-Ray</span>
              <ExternalLink size={11} className="opacity-60" />
            </Link>

            <Link
              to={`/digital-twin`}
              className="px-3.5 py-2 rounded-xl bg-zinc-100 hover:bg-zinc-200 border border-zinc-200 text-zinc-800 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
              title="Inspect 3D/Topological Digital Twin state"
            >
              <Boxes size={13} className="text-zinc-600" />
              <span>View in Digital Twin</span>
              <ExternalLink size={11} className="opacity-60" />
            </Link>
          </div>
        </div>
      )}

      {/* 3. BALANCED SPLIT: PHYSICAL FACILITY / AHU VIEW (LEFT) & CAUSAL FLOW GRAPH (RIGHT) */}
      <div className="grid gap-6 grid-cols-1 xl:grid-cols-2">
        {/* COLUMN 1: PHYSICAL FACILITY / AHU COMPONENT VIEW */}
        <div className="min-h-[640px] flex flex-col">
          <AhuSchematicView
            summary={summary}
            nodes={graphData?.nodes || []}
            edges={graphData?.edges || []}
            selectedNodeId={selectedNodeId}
            onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
            incidentPathMode={incidentPathMode}
            onToggleIncidentPathMode={() => setIncidentPathMode((m) => !m)}
            onResetView={handleResetView}
          />
        </div>

        {/* COLUMN 2: CAUSAL FLOW GRAPH CANVAS */}
        <div className="rounded-3xl bg-white border border-zinc-200/90 shadow-sm relative overflow-hidden flex flex-col min-h-[640px]">
          {/* Controls Overlay Header */}
          <div className="p-3.5 bg-zinc-50/90 border-b border-zinc-200/80 flex items-center justify-between z-20 backdrop-blur-xs flex-wrap gap-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-zinc-950 font-mono font-bold flex items-center gap-1.5 text-[11px]">
                <span className="w-2 h-2 rounded-full bg-cyan-600 animate-pulse" />
                Causal Flow
              </span>
              <span className="text-zinc-300 font-mono">•</span>
              <span className="text-[11px] text-zinc-500 font-mono hidden sm:inline">
                {graphData ? `${graphData.nodes.length} Nodes • ${graphData.edges.length} Links` : ''}
              </span>
            </div>

            {/* Filter Buttons & Canvas Controls */}
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-zinc-100 border border-zinc-200/80 rounded-xl p-0.5 text-[11px] font-mono text-zinc-600">
                {['ALL', 'SENSOR', 'COMPONENT', 'ROOT_CAUSE'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setFilterType(type)}
                    className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                      filterType === type
                        ? 'bg-zinc-900 text-white font-semibold shadow-xs'
                        : 'text-zinc-600 hover:text-zinc-950 hover:bg-zinc-200/60'
                    }`}
                  >
                    {type.replace('_', ' ')}
                  </button>
                ))}
              </div>

              <div className="flex items-center bg-zinc-100 border border-zinc-200/80 rounded-xl p-0.5 text-zinc-700">
                <button
                  onClick={handleZoomIn}
                  className="p-1.5 hover:bg-white hover:text-zinc-950 rounded-lg transition-colors cursor-pointer"
                  title="Zoom In"
                >
                  <ZoomIn size={14} />
                </button>
                <button
                  onClick={handleZoomOut}
                  className="p-1.5 hover:bg-white hover:text-zinc-950 rounded-lg transition-colors cursor-pointer"
                  title="Zoom Out"
                >
                  <ZoomOut size={14} />
                </button>
                <button
                  onClick={handleResetView}
                  className="p-1.5 hover:bg-white hover:text-cyan-700 rounded-lg transition-colors cursor-pointer text-cyan-600"
                  title="Reset Pan & Zoom"
                >
                  <RotateCcw size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* Interactive Pan & Zoom Canvas Area (Light Theme Grid) */}
          <div
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className={`flex-1 relative overflow-hidden select-none cursor-${
              isPanning ? 'grabbing' : 'grab'
            } bg-[#f8fafc] bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:24px_24px]`}
          >
            <div
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                transformOrigin: '0 0',
                transition: isPanning ? 'none' : 'transform 0.15s ease-out',
                width: `${canvasWidth}px`,
                height: `${canvasHeight}px`,
              }}
              className="relative"
            >
              {/* TIER COLUMN GUIDES & HEADERS */}
              <div className="absolute inset-0 pointer-events-none">
                {TIER_HEADERS.map((th, idx) => {
                  const x = columnWidths[idx] || 50 + idx * 330;
                  return (
                    <div
                      key={th.tier}
                      style={{ left: `${x}px`, width: '270px' }}
                      className="absolute top-4 border-t-2 border-cyan-600/40 pt-2"
                    >
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-600" />
                        <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-cyan-800">
                          {th.label}
                        </span>
                      </div>
                      <span className="text-[9.5px] text-zinc-500 block font-mono mt-0.5">
                        {th.sub}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* SVG CONNECTION EDGES */}
              <svg
                className="absolute inset-0 pointer-events-none"
                width={canvasWidth}
                height={canvasHeight}
              >
                <defs>
                  {/* Default arrow marker - Neutral Slate */}
                  <marker
                    id="arrow-default"
                    viewBox="0 0 10 10"
                    refX="9"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#94a3b8" />
                  </marker>
                  {/* Active highlighted arrow marker - Cyan */}
                  <marker
                    id="arrow-active"
                    viewBox="0 0 10 10"
                    refX="9"
                    refY="5"
                    markerWidth="7"
                    markerHeight="7"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#0891b2" />
                  </marker>
                </defs>

                {graphData?.edges.map((edge) => {
                  const srcPos = nodePositions[edge.source];
                  const tgtPos = nodePositions[edge.target];
                  if (!srcPos || !tgtPos) return null;

                  const isEdgeActive = activeEdgeIds.has(edge.id);
                  const isFiltered =
                    filterType !== 'ALL' &&
                    selectedNode &&
                    !connectedNodeIds.has(edge.source) &&
                    !connectedNodeIds.has(edge.target);

                  const x1 = srcPos.x + srcPos.width;
                  const y1 = srcPos.y + srcPos.height / 2;
                  const x2 = tgtPos.x;
                  const y2 = tgtPos.y + tgtPos.height / 2;

                  const dx = Math.abs(x2 - x1) * 0.52;
                  const pathData = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;

                  // Center coordinates for relationship label
                  const midX = (x1 + x2) / 2;
                  const midY = (y1 + y2) / 2;
                  const labelText = edge.label || edge.relationship.replace('_', ' ');
                  const badgeWidth = Math.max(70, labelText.length * 6.5 + 16);

                  return (
                    <g key={edge.id} className={isFiltered ? 'opacity-20' : 'opacity-100'}>
                      {/* Glow stroke for active edge */}
                      {isEdgeActive && (
                        <path
                          d={pathData}
                          fill="none"
                          stroke="#06b6d4"
                          strokeWidth="6"
                          opacity="0.25"
                        />
                      )}
                      {/* Main connecting Bezier curve */}
                      <path
                        d={pathData}
                        fill="none"
                        stroke={isEdgeActive ? '#0891b2' : '#cbd5e1'}
                        strokeWidth={isEdgeActive ? 2.5 : 1.75}
                        strokeDasharray={edge.relationship === 'depends_on' ? '4 3' : undefined}
                        markerEnd={isEdgeActive ? 'url(#arrow-active)' : 'url(#arrow-default)'}
                        className="transition-all duration-200"
                      />
                      {/* Clean white pill label for maximum readability */}
                      {labelText && (
                        <g>
                          <rect
                            x={midX - badgeWidth / 2}
                            y={midY - 9}
                            width={badgeWidth}
                            height={18}
                            rx={9}
                            fill="#ffffff"
                            stroke={isEdgeActive ? '#0891b2' : '#e2e8f0'}
                            strokeWidth={isEdgeActive ? 1.5 : 1}
                            className="shadow-2xs"
                          />
                          <text
                            x={midX}
                            y={midY + 3.5}
                            fill={isEdgeActive ? '#0e7490' : '#475569'}
                            fontSize="9"
                            fontWeight="600"
                            fontFamily="monospace"
                            textAnchor="middle"
                            className="select-none pointer-events-none"
                          >
                            {labelText}
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}
              </svg>

              {/* HIGH-CONTRAST LIGHT THEME INTERACTIVE NODES */}
              {graphData?.nodes.map((node) => {
                const pos = nodePositions[node.id];
                if (!pos) return null;

                const isSelected = selectedNodeId === node.id;
                const isConnected = connectedNodeIds.has(node.id);
                const isDimmed =
                  (selectedNodeId && !isSelected && !isConnected) ||
                  (filterType !== 'ALL' && node.type !== filterType && !isConnected);

                // High-contrast, clean light aesthetic tailored per Node Type
                let nodeBg = 'bg-white border-zinc-200 hover:border-zinc-300';
                let typeColor = 'text-zinc-600';
                let badgeStyle = 'bg-zinc-100 text-zinc-800 border-zinc-200';
                let icon = <Info size={13} className="text-zinc-500" />;

                if (node.type === 'ASSET') {
                  nodeBg = 'bg-slate-50/80 border-slate-300 hover:border-slate-400';
                  typeColor = 'text-slate-700 font-bold';
                  badgeStyle = 'bg-slate-100 text-slate-800 border-slate-200 font-bold';
                  icon = <Boxes size={13} className="text-slate-700" />;
                } else if (node.type === 'SENSOR') {
                  nodeBg = 'bg-sky-50/70 border-sky-200 hover:border-sky-300';
                  typeColor = 'text-sky-800 font-bold';
                  badgeStyle = 'bg-sky-100 text-sky-900 border-sky-200 font-bold';
                  icon = <Activity size={13} className="text-sky-600" />;
                } else if (node.type === 'ANOMALY') {
                  nodeBg = 'bg-amber-50/80 border-amber-300 hover:border-amber-400';
                  typeColor = 'text-amber-900 font-bold';
                  badgeStyle = 'bg-amber-100 text-amber-950 border-amber-300 font-bold';
                  icon = <AlertTriangle size={13} className="text-amber-600" />;
                } else if (node.type === 'COMPONENT') {
                  nodeBg = 'bg-teal-50/70 border-teal-200 hover:border-teal-300';
                  typeColor = 'text-teal-800 font-bold';
                  badgeStyle = 'bg-teal-100 text-teal-900 border-teal-200 font-bold';
                  icon = <Wind size={13} className="text-teal-600" />;
                } else if (node.type === 'ROOT_CAUSE') {
                  nodeBg = 'bg-rose-50/70 border-rose-200 hover:border-rose-300';
                  typeColor = 'text-rose-900 font-bold';
                  badgeStyle = 'bg-rose-100 text-rose-950 border-rose-200 font-bold';
                  icon = <AlertCircle size={13} className="text-rose-600" />;
                } else if (node.type === 'IMPACT') {
                  nodeBg = 'bg-purple-50/70 border-purple-200 hover:border-purple-300';
                  typeColor = 'text-purple-900 font-bold';
                  badgeStyle = 'bg-purple-100 text-purple-950 border-purple-200 font-bold';
                  icon = <Zap size={13} className="text-purple-600" />;
                } else if (node.type === 'ACTION') {
                  nodeBg = 'bg-emerald-50/70 border-emerald-200 hover:border-emerald-300';
                  typeColor = 'text-emerald-900 font-bold';
                  badgeStyle = 'bg-emerald-100 text-emerald-950 border-emerald-200 font-bold';
                  icon = <CheckCircle2 size={13} className="text-emerald-600" />;
                }

                return (
                  <div
                    key={node.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedNodeId(node.id);
                    }}
                    style={{
                      left: `${pos.x}px`,
                      top: `${pos.y}px`,
                      width: `${pos.width}px`,
                      height: `${pos.height}px`,
                    }}
                    className={`absolute p-3 rounded-2xl cursor-pointer transition-all duration-200 flex flex-col justify-between select-none shadow-xs border ${
                      isSelected
                        ? 'bg-white border-2 border-cyan-600 shadow-[0_4px_20px_rgba(8,145,178,0.22)] ring-4 ring-cyan-500/15 z-20'
                        : isConnected
                        ? 'bg-white border-2 border-cyan-500/80 shadow-sm z-10'
                        : `${nodeBg}`
                    } ${isDimmed ? 'opacity-35 grayscale-[15%]' : 'opacity-100'}`}
                  >
                    {/* Node Header Pill & Type */}
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {icon}
                        <span className={`text-[10px] uppercase font-mono tracking-wider truncate ${typeColor}`}>
                          {node.type}
                        </span>
                      </div>
                      <span
                        className={`text-[9px] font-mono px-2 py-0.5 rounded-full border shadow-2xs ${badgeStyle}`}
                      >
                        {node.confidence || node.status}
                      </span>
                    </div>

                    {/* Node Title - High Contrast, Wrapped */}
                    <div
                      className="font-bold text-[13px] text-zinc-950 leading-snug break-words"
                      title={node.label}
                    >
                      {node.label}
                    </div>

                    {/* Live Telemetry or Subsystem Descriptor */}
                    <div className="flex items-center justify-between text-[10px] font-mono text-zinc-600 border-t border-zinc-200/80 pt-1.5">
                      {node.telemetry ? (
                        <>
                          <span className="text-zinc-500 truncate">{node.telemetry.metric}:</span>
                          <span
                            className={`font-bold px-1.5 py-0.2 rounded ${
                              node.telemetry.status === 'CRITICAL'
                                ? 'text-rose-700 bg-rose-50 border border-rose-200'
                                : 'text-emerald-700 bg-emerald-50 border border-emerald-200'
                            }`}
                          >
                            {node.telemetry.current_value} {node.telemetry.unit}
                          </span>
                        </>
                      ) : (
                        <span className="text-zinc-500 truncate font-medium">
                          {node.category || 'Facility Node'}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* 4. LOWER WORKSPACE: NODE INSPECTOR, EXPLANATION PANEL & FACILITY MEMORY */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        {/* COL 1: LIVE NODE INSPECTOR */}
        <div className="lg:col-span-1 rounded-3xl bg-white border border-zinc-200 shadow-sm p-6 space-y-5 text-zinc-900">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase font-mono font-bold text-cyan-700">
                Node Inspector
              </span>
              <h3 className="text-base font-extrabold text-zinc-950 editorial-title">
                {selectedNode ? selectedNode.label : 'Select a Node or Component'}
              </h3>
            </div>
            {selectedNode && (
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase border ${
                  selectedNode.status === 'CRITICAL'
                    ? 'bg-rose-50 text-rose-800 border-rose-200'
                    : selectedNode.status === 'WARNING'
                    ? 'bg-amber-50 text-amber-800 border-amber-200'
                    : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                }`}
              >
                {selectedNode.status}
              </span>
            )}
          </div>

          {selectedNode ? (
            <div className="space-y-4 text-xs">
              {/* Node Metadata Key-Values */}
              <div className="space-y-2 font-mono">
                <div className="flex items-center justify-between py-1.5 border-b border-zinc-100">
                  <span className="text-zinc-500">Classification:</span>
                  <span className="font-bold text-zinc-950">{selectedNode.type}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-zinc-100">
                  <span className="text-zinc-500">Confidence:</span>
                  <span className="font-bold text-cyan-700">
                    {selectedNode.confidence || 'Observed Ground Truth'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-zinc-100">
                  <span className="text-zinc-500">Category:</span>
                  <span className="text-zinc-800 font-semibold">{selectedNode.category}</span>
                </div>
              </div>

              {/* Telemetry Box if Sensor or Component */}
              {selectedNode.telemetry && (
                <div className="p-3.5 rounded-2xl bg-zinc-50/90 border border-zinc-200 space-y-2 font-mono">
                  <div className="flex items-center gap-1.5 text-zinc-500 text-[10px] uppercase font-bold">
                    <Activity size={12} className="text-cyan-600" />
                    <span>Live Telemetry Verification</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="bg-white p-2 rounded-xl border border-zinc-200/80 shadow-2xs">
                      <span className="text-[10px] text-zinc-400 block">Current Reading</span>
                      <span className="text-sm font-extrabold text-zinc-950">
                        {selectedNode.telemetry.current_value} {selectedNode.telemetry.unit}
                      </span>
                    </div>
                    <div className="bg-white p-2 rounded-xl border border-zinc-200/80 shadow-2xs">
                      <span className="text-[10px] text-zinc-400 block">Baseline Target</span>
                      <span className="text-sm font-bold text-zinc-600">
                        {selectedNode.telemetry.baseline || '—'} {selectedNode.telemetry.unit}
                      </span>
                    </div>
                  </div>
                  <div className="text-[11px] text-zinc-600 pt-1 text-center">
                    Expected Operating Range:{' '}
                    <span className="font-bold text-zinc-900">
                      {selectedNode.telemetry.expected_range}
                    </span>
                  </div>
                </div>
              )}

              {/* Details Breakdown */}
              {selectedNode.details && Object.keys(selectedNode.details).length > 0 && (
                <div className="space-y-2 pt-1">
                  <span className="text-[10px] uppercase font-mono font-bold text-zinc-500 block">
                    Subsystem Details
                  </span>
                  <div className="space-y-1.5 text-[11px]">
                    {Object.entries(selectedNode.details).map(([key, val]) => (
                      <div
                        key={key}
                        className="p-2.5 rounded-xl bg-zinc-50/80 border border-zinc-200/70 space-y-0.5"
                      >
                        <span className="text-zinc-500 uppercase font-mono text-[9px] block font-semibold">
                          {key.replace('_', ' ')}
                        </span>
                        <span className="font-medium text-zinc-800">
                          {Array.isArray(val) ? val.join(', ') : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cross-link Actions */}
              <div className="pt-3 border-t border-zinc-100 space-y-2">
                <Link
                  to="/digital-twin"
                  className="w-full py-2.5 px-3 rounded-xl bg-zinc-950 hover:bg-zinc-800 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition-colors shadow-2xs"
                >
                  <Boxes size={13} />
                  <span>View in Digital Twin</span>
                </Link>

                {summary && (
                  <Link
                    to={`/x-ray?asset_id=${summary.asset_id}&alert_id=${summary.incident_id}`}
                    className="w-full py-2.5 px-3 rounded-xl bg-zinc-100 hover:bg-zinc-200 border border-zinc-200 text-zinc-800 text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
                  >
                    <Gauge size={13} />
                    <span>Investigate in Facility X-Ray</span>
                  </Link>
                )}
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-zinc-400 text-xs space-y-2">
              <Compass size={24} className="mx-auto text-zinc-300" />
              <p>Click any component in the AHU view or node in the causal flow to inspect live telemetry, physical dependencies, and causal mechanisms.</p>
            </div>
          )}
        </div>

        {/* COLS 2 & 3: DYNAMIC INCIDENT EXPLANATION & FACILITY MEMORY */}
        <div className="lg:col-span-2 space-y-6">
          {/* WHAT IS HAPPENING? (EXPLANATION PANEL) */}
          <CausalExplanationPanel
            summary={summary}
            nodes={graphData?.nodes || []}
            edges={graphData?.edges || []}
            selectedNodeId={selectedNodeId}
            onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
          />

          {/* SIMILAR HISTORICAL INCIDENTS (Facility Memory Connection) */}
          <div className="p-6 rounded-3xl bg-white border border-zinc-200 shadow-sm space-y-4 text-zinc-900">
            <div className="flex items-center gap-2">
              <Brain size={16} className="text-cyan-600" />
              <div>
                <span className="text-[10px] uppercase font-mono font-bold text-zinc-500 block">
                  Facility Memory
                </span>
                <h3 className="text-sm font-extrabold text-zinc-950">Similar Historical Incidents</h3>
              </div>
            </div>

            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Vector-matched historical incident records and verified maintenance resolutions from facility institutional memory:
            </p>

            <div className="space-y-2.5">
              {graphData?.historical_matches.map((match) => (
                <div
                  key={match.memory_id}
                  onClick={() => setSelectedMemory(match)}
                  className="p-3 rounded-2xl bg-zinc-50 hover:bg-cyan-50/60 border border-zinc-200 hover:border-cyan-300 transition-all cursor-pointer space-y-1.5 shadow-2xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold text-zinc-950">
                      Incident {match.incident_number}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800 border border-cyan-200 text-[10px] font-mono font-bold">
                      {match.similarity_pct}% Similarity
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-zinc-800">{match.incident_type}</div>
                  <div className="text-[10px] text-zinc-500 font-mono">
                    {match.asset_code} • {match.timestamp}
                  </div>
                </div>
              ))}
            </div>

            <Link
              to="/facility-memory"
              className="w-full py-2 px-3 rounded-xl bg-zinc-50 hover:bg-zinc-100 border border-zinc-200 text-zinc-700 text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors"
            >
              <span>Explore Full Facility Memory Archive</span>
              <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      </div>

      {/* HISTORICAL INCIDENT RESOLUTION MODAL */}
      {selectedMemory && (
        <div className="fixed inset-0 z-50 bg-zinc-950/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-3xl p-6 shadow-2xl border border-zinc-200 space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="space-y-0.5">
                <span className="text-[10px] uppercase font-mono font-bold text-cyan-600">
                  Facility Memory Historical Record
                </span>
                <h3 className="text-base font-bold text-zinc-950">
                  {selectedMemory.incident_type} ({selectedMemory.incident_number})
                </h3>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-cyan-100 text-cyan-900 border border-cyan-200 text-xs font-mono font-bold">
                {selectedMemory.similarity_pct}% Match
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-zinc-500 font-mono text-[10px] uppercase block font-bold">
                  Asset & Timestamp
                </span>
                <span className="font-semibold text-zinc-800">
                  {selectedMemory.asset_code} • {selectedMemory.timestamp}
                </span>
              </div>

              <div>
                <span className="text-zinc-500 font-mono text-[10px] uppercase block font-bold">
                  Verified Root Cause
                </span>
                <p className="text-zinc-800 bg-zinc-50 p-2.5 rounded-xl border border-zinc-200/80 leading-relaxed font-medium">
                  {selectedMemory.root_cause}
                </p>
              </div>

              <div>
                <span className="text-zinc-500 font-mono text-[10px] uppercase block font-bold">
                  Corrective Maintenance Resolution
                </span>
                <p className="text-emerald-950 bg-emerald-50/80 p-2.5 rounded-xl border border-emerald-200 leading-relaxed font-medium">
                  {selectedMemory.corrective_action}
                </p>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedMemory(null)}
                className="px-4 py-2 rounded-xl bg-zinc-950 text-white text-xs font-semibold hover:bg-zinc-800 cursor-pointer transition-colors"
              >
                Close Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
