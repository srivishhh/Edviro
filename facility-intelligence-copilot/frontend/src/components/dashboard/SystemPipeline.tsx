import {
  Activity,
  ArrowRight,
  Boxes,
  Cpu,
  Flame,
  Radio,
  ShieldCheck,
  Wrench,
} from 'lucide-react';

const PIPELINE_NODES = [
  { step: '01', title: 'Data Ingestion', desc: 'LBNL Replay / Kafka', icon: Radio },
  { step: '02', title: 'Twin Update', desc: 'Spatial Dependency Graph', icon: Boxes },
  { step: '03', title: 'Anomaly Gate', desc: 'Z-Score & Thermodynamic Check', icon: Cpu },
  { step: '04', title: 'Incident Alert', desc: 'Threshold Trigger', icon: Activity },
  { step: '05', title: 'Causal X-Ray', desc: '7-Agent Multi-Modal AI', icon: Flame },
  { step: '06', title: 'Verification', desc: 'Physical Validation Gate', icon: ShieldCheck },
  { step: '07', title: 'Action SOP', desc: 'SNS Workbench Callback', icon: Wrench },
];

export function SystemPipeline() {
  return (
    <div className="saas-card p-6 md:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-100 pb-4">
        <div>
          <span className="text-[10px] uppercase font-bold tracking-[0.2em] text-zinc-400 block mb-1">
            End-to-End Pipeline
          </span>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight">Facility Intelligence Architecture</h3>
        </div>
        <span className="px-3 py-1 rounded-full bg-zinc-100 text-zinc-700 text-xs font-mono font-medium self-start sm:self-auto">
          Synchronous Multi-Stage Pipeline
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-7">
        {PIPELINE_NODES.map((node, idx) => {
          const Icon = node.icon;
          return (
            <div
              key={node.step}
              className="p-3.5 rounded-2xl bg-zinc-50/60 border border-zinc-200/80 flex flex-col justify-between space-y-3 relative group hover:border-zinc-400 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-zinc-400">{node.step}</span>
                <div className="w-6 h-6 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-zinc-700 shadow-2xs">
                  <Icon size={12} strokeWidth={2} />
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-zinc-900 leading-tight">{node.title}</h4>
                <p className="text-[10px] text-zinc-500 font-mono mt-0.5 leading-snug">{node.desc}</p>
              </div>

              {idx < PIPELINE_NODES.length - 1 && (
                <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-zinc-300">
                  <ArrowRight size={10} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
