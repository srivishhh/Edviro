import {
  Boxes,
  Cpu,
  Flame,
  Layers,
  Radio,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';

interface InvestigationTimelineProps {
  investigationStatus?: string;
}

const AGENTS = [
  { id: 'agent-1', name: 'Telemetry Detective', role: 'Anomaly & Trend Isolator', icon: Cpu, status: 'DONE' },
  { id: 'agent-2', name: 'Digital Twin Analyst', role: 'Dependency Graph Tracer', icon: Boxes, status: 'DONE' },
  { id: 'agent-3', name: 'Sensor Health Validator', role: 'Sensor Drift Detector', icon: Sparkles, status: 'DONE' },
  { id: 'agent-4', name: 'Impact & Severity Assessor', role: 'Comfort & Energy Penalty', icon: Zap, status: 'DONE' },
  { id: 'agent-5', name: 'Cross-Sensor Evidence Fusion', role: 'Multi-Modal Corroboration', icon: Layers, status: 'DONE' },
  { id: 'agent-6', name: 'Root Cause Investigator', role: 'Causal Fault Tree Fused', icon: Flame, status: 'DONE' },
  { id: 'agent-7', name: 'Validation Agent', role: 'Physical Verification Gate', icon: ShieldCheck, status: 'DONE' },
];

export function InvestigationTimeline({ investigationStatus = 'COMPLETED' }: InvestigationTimelineProps) {
  return (
    <div className="saas-card p-6 md:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-zinc-500">
            <Radio size={14} className="text-emerald-500 animate-pulse" />
            <span className="text-[10px] uppercase font-bold tracking-[0.2em]">Multi-Agent Causal Reasoning</span>
          </div>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
            Specialized AI Agent Swarm Execution
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-zinc-400 font-semibold uppercase">Status:</span>
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-mono font-bold">
            {investigationStatus}
          </span>
        </div>
      </div>

      {/* Grid of 7 Specialized Agents */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7">
        {AGENTS.map((ag, idx) => {
          const Icon = ag.icon;
          return (
            <div
              key={ag.id}
              className="p-3.5 rounded-2xl bg-zinc-50 border border-zinc-200/80 flex flex-col justify-between space-y-3 relative group hover:border-zinc-400 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-zinc-400">0{idx + 1}</span>
                <div className="w-6 h-6 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-zinc-700 shadow-2xs">
                  <Icon size={12} strokeWidth={2} />
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-zinc-900 leading-tight">{ag.name}</h4>
                <p className="text-[10px] text-zinc-500 font-mono mt-0.5 leading-snug">{ag.role}</p>
              </div>

              <div className="pt-2 border-t border-zinc-100 flex items-center justify-between text-[10px] font-mono text-emerald-700 font-bold">
                <span>Verified</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
