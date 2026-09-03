import { Bell, Radio, Search, ShieldCheck } from 'lucide-react';
import type { SystemStatus } from '../../types';

interface TopBarProps {
  status?: SystemStatus | null;
  alertCount?: number;
}

export function TopBar({ alertCount = 0 }: TopBarProps) {
  return (
    <header className="h-16 border-b border-zinc-200/90 bg-[#fdfdfd]/80 backdrop-blur-md sticky top-0 z-20 px-8 flex items-center justify-between">
      {/* Search Bar */}
      <div className="flex items-center gap-3 w-80">
        <div className="relative w-full">
          <Search className="absolute left-3 top-2.5 text-zinc-400" size={14} />
          <input
            type="text"
            placeholder="Search assets, telemetry, anomalies..."
            className="w-full bg-zinc-100/80 border border-zinc-200 rounded-full pl-9 pr-4 py-1.5 text-xs text-zinc-800 placeholder-zinc-400 focus:outline-none focus:border-zinc-400 focus:bg-white transition-all font-sans"
          />
        </div>
      </div>

      {/* Right Header Status Badges */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-800 text-xs font-mono">
          <Radio size={12} className="animate-pulse text-emerald-600" />
          <span className="font-semibold">LBNL Replay Active</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-100 border border-zinc-200 text-zinc-700 text-xs font-mono font-medium">
          <ShieldCheck size={13} className="text-zinc-900" />
          <span>7 Agents Ready</span>
        </div>

        {/* Notifications Icon with Badge */}
        <div className="relative p-2 rounded-xl bg-zinc-100 hover:bg-zinc-200 transition-colors text-zinc-700 cursor-pointer">
          <Bell size={16} />
          {alertCount > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          )}
        </div>
      </div>
    </header>
  );
}
