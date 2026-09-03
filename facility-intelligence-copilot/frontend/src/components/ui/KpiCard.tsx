import type { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: LucideIcon;
}

export function KpiCard({ label, value, change, icon: Icon }: KpiCardProps) {
  return (
    <div className="saas-card p-5 space-y-3 bg-white">
      <div className="flex items-center justify-between text-zinc-500">
        <span className="text-xs font-medium text-zinc-600 tracking-tight">{label}</span>
        <div className="w-8 h-8 rounded-xl bg-zinc-50 border border-zinc-200/60 flex items-center justify-center text-zinc-700">
          <Icon size={15} strokeWidth={1.75} />
        </div>
      </div>

      <div className="space-y-1">
        <p className="text-2xl font-extrabold text-zinc-950 font-mono tracking-tight">{value}</p>
        {change && (
          <p className="text-[11px] text-zinc-500 font-mono">
            {change}
          </p>
        )}
      </div>
    </div>
  );
}
