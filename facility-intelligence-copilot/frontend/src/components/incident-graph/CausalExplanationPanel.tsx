import {
  Activity,
  AlertCircle,
  ArrowRight,
  Brain,
  CheckCircle2,
  Compass,
  Layers,
  Zap,
} from 'lucide-react';
import type {
  IncidentGraphEdge,
  IncidentGraphNode,
  IncidentGraphSummary,
} from '../../services/incidentGraph';

interface CausalExplanationPanelProps {
  summary: IncidentGraphSummary | undefined;
  nodes: IncidentGraphNode[];
  edges: IncidentGraphEdge[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
}

export function CausalExplanationPanel({
  summary,
  nodes,
  selectedNodeId,
  onSelectNode,
}: CausalExplanationPanelProps) {
  // Extract key causal actors from project graph nodes
  const sensorNode =
    nodes.find((n) => n.type === 'SENSOR' && n.status !== 'HEALTHY') ||
    nodes.find((n) => n.type === 'SENSOR');

  const anomalyNode =
    nodes.find((n) => n.type === 'ANOMALY' && n.status !== 'HEALTHY') ||
    nodes.find((n) => n.type === 'ANOMALY');

  const componentNode =
    nodes.find((n) => n.type === 'COMPONENT' && n.status !== 'HEALTHY') ||
    nodes.find((n) => n.type === 'COMPONENT');

  const rootCauseNode =
    nodes.find((n) => n.id === 'cause_primary') ||
    nodes.find((n) => n.type === 'ROOT_CAUSE');

  const impactNode =
    nodes.find((n) => n.id === 'impact_energy') ||
    nodes.find((n) => n.id === 'impact_comfort') ||
    nodes.find((n) => n.type === 'IMPACT');

  const actionNode =
    nodes.find((n) => n.type === 'ACTION');

  // Dynamic explanation narrative calculations
  const detectedValue = sensorNode?.telemetry?.current_value || 'abnormal';
  const unit = sensorNode?.telemetry?.unit || '';
  const baseline = sensorNode?.telemetry?.baseline;

  let deviationText = `${detectedValue} ${unit}`;
  if (baseline !== undefined) {
    const numVal = typeof detectedValue === 'string' ? parseFloat(detectedValue) : Number(detectedValue);
    const numBase = typeof baseline === 'string' ? parseFloat(baseline) : Number(baseline);
    if (!isNaN(numVal) && !isNaN(numBase)) {
      const diff = Math.abs(numVal - numBase).toFixed(1);
      const direction = numVal > numBase ? 'increase above' : 'drop below';
      deviationText = `${diff} ${unit} ${direction} baseline of ${baseline} ${unit}`;
    } else {
      deviationText = `${detectedValue} ${unit} (baseline: ${baseline} ${unit})`;
    }
  }

  return (
    <div className="rounded-3xl bg-white border border-zinc-200/90 shadow-sm p-6 space-y-5 text-zinc-900">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-cyan-50 border border-cyan-200 flex items-center justify-center text-cyan-700 shadow-2xs">
            <Compass size={16} />
          </div>
          <div>
            <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-cyan-800 block">
              INCIDENT SYNTHESIS & EXPLANATION
            </span>
            <h3 className="text-base font-extrabold text-zinc-950 editorial-title">
              WHAT IS HAPPENING?
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-mono font-bold text-zinc-400">Diagnosis Confidence:</span>
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-mono font-bold">
            {summary?.confidence || '88% Confirmed'}
          </span>
        </div>
      </div>

      {/* Narrative Synthesis Box */}
      <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200/80 space-y-2.5 text-xs text-zinc-700 leading-relaxed font-sans">
        <p>
          The{' '}
          <button
            onClick={() => sensorNode && onSelectNode(sensorNode.id)}
            className="font-bold text-cyan-800 hover:underline cursor-pointer inline-flex items-center gap-0.5"
            title="Click to select sensor"
          >
            {sensorNode?.label || 'Telemetry Sensor'}
          </button>{' '}
          detected a {sensorNode?.telemetry?.metric?.toLowerCase() || 'telemetry'} reading of{' '}
          <span className="font-bold text-zinc-950">{deviationText}</span>.
        </p>

        <p>
          The anomaly is physically localized in the{' '}
          <button
            onClick={() => componentNode && onSelectNode(componentNode.id)}
            className="font-bold text-teal-800 hover:underline cursor-pointer"
            title="Click to select component"
          >
            {componentNode?.label || 'subsystem component'}
          </button>
          . Multi-agent causal inference traces the primary probable cause to{' '}
          <button
            onClick={() => rootCauseNode && onSelectNode(rootCauseNode.id)}
            className="font-bold text-rose-800 hover:underline cursor-pointer"
            title="Click to select root cause"
          >
            {rootCauseNode?.label || 'Root Cause Hypothesis'}
          </button>
          , creating{' '}
          <button
            onClick={() => impactNode && onSelectNode(impactNode.id)}
            className="font-bold text-purple-800 hover:underline cursor-pointer"
            title="Click to select impact"
          >
            {impactNode?.label || 'Operational Impact'}
          </button>
          .
        </p>

        {actionNode && (
          <p className="pt-1 text-emerald-950 font-medium">
            Recommended Action:{' '}
            <button
              onClick={() => onSelectNode(actionNode.id)}
              className="font-bold hover:underline cursor-pointer text-emerald-900 inline-flex items-center gap-1"
              title="Click to select action"
            >
              <CheckCircle2 size={13} className="text-emerald-600" />
              {actionNode.label}
            </button>
            .
          </p>
        )}
      </div>

      {/* Interactive Causal Chain Breadcrumbs */}
      <div className="space-y-2">
        <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-zinc-400 block">
          Current Causal Pathway (Click any step to synchronize view):
        </span>

        <div className="flex items-center gap-1.5 flex-wrap text-[11px] font-mono">
          {sensorNode && (
            <button
              onClick={() => onSelectNode(sensorNode.id)}
              className={`px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                selectedNodeId === sensorNode.id
                  ? 'bg-cyan-600 text-white border-cyan-700 shadow-xs font-bold'
                  : 'bg-sky-50 hover:bg-sky-100 text-sky-900 border-sky-200'
              }`}
            >
              <Activity size={12} className="text-sky-600" />
              <span>{sensorNode.label}</span>
            </button>
          )}

          <ArrowRight size={13} className="text-zinc-300 shrink-0" />

          {anomalyNode && (
            <button
              onClick={() => onSelectNode(anomalyNode.id)}
              className={`px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                selectedNodeId === anomalyNode.id
                  ? 'bg-cyan-600 text-white border-cyan-700 shadow-xs font-bold'
                  : 'bg-amber-50 hover:bg-amber-100 text-amber-900 border-amber-200'
              }`}
            >
              <AlertCircle size={12} className="text-amber-600" />
              <span>{anomalyNode.label}</span>
            </button>
          )}

          <ArrowRight size={13} className="text-zinc-300 shrink-0" />

          {componentNode && (
            <button
              onClick={() => onSelectNode(componentNode.id)}
              className={`px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                selectedNodeId === componentNode.id
                  ? 'bg-cyan-600 text-white border-cyan-700 shadow-xs font-bold'
                  : 'bg-teal-50 hover:bg-teal-100 text-teal-900 border-teal-200'
              }`}
            >
              <Layers size={12} className="text-teal-600" />
              <span>{componentNode.label}</span>
            </button>
          )}

          <ArrowRight size={13} className="text-zinc-300 shrink-0" />

          {rootCauseNode && (
            <button
              onClick={() => onSelectNode(rootCauseNode.id)}
              className={`px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                selectedNodeId === rootCauseNode.id
                  ? 'bg-cyan-600 text-white border-cyan-700 shadow-xs font-bold'
                  : 'bg-rose-50 hover:bg-rose-100 text-rose-900 border-rose-200'
              }`}
            >
              <Brain size={12} className="text-rose-600" />
              <span>{rootCauseNode.label}</span>
            </button>
          )}

          <ArrowRight size={13} className="text-zinc-300 shrink-0" />

          {impactNode && (
            <button
              onClick={() => onSelectNode(impactNode.id)}
              className={`px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                selectedNodeId === impactNode.id
                  ? 'bg-cyan-600 text-white border-cyan-700 shadow-xs font-bold'
                  : 'bg-purple-50 hover:bg-purple-100 text-purple-900 border-purple-200'
              }`}
            >
              <Zap size={12} className="text-purple-600" />
              <span>{impactNode.label}</span>
            </button>
          )}

          {actionNode && (
            <>
              <ArrowRight size={13} className="text-zinc-300 shrink-0" />
              <button
                onClick={() => onSelectNode(actionNode.id)}
                className={`px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                  selectedNodeId === actionNode.id
                    ? 'bg-cyan-600 text-white border-cyan-700 shadow-xs font-bold'
                    : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border-emerald-200'
                }`}
              >
                <CheckCircle2 size={12} className="text-emerald-600" />
                <span>{actionNode.label}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
