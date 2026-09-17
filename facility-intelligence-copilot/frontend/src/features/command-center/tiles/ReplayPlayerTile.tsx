import React from 'react';
import { Play, Pause, RotateCcw, FastForward, PlaySquare } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime } from '../../../hooks/useRealtime';

export const ReplayPlayerTile: React.FC = () => {
  const { replayState, controlReplay } = useRealtime();

  const percentProgress = Math.round((replayState.current_row / replayState.total_rows) * 100 * 10) / 10;

  return (
    <BentoTile span="col-span-1" variant="translucent" className="flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <PlaySquare size={16} className="text-[#5C3E94] dark:text-purple-300" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">LBNL REPLAY</span>
        </div>
        <span
          className={`rounded-lg px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
            replayState.status === 'PLAYING'
              ? 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/30'
              : 'bg-amber-500/15 text-amber-500 border border-amber-500/30'
          }`}
        >
          {replayState.status}
        </span>
      </div>

      <div className="my-3">
        <div className="flex items-baseline justify-between text-xs font-mono text-[var(--text-main)]">
          <span>ROW CURSOR</span>
          <span className="text-[#F25912] font-semibold">{replayState.current_row} / {replayState.total_rows}</span>
        </div>

        {/* Progress Bar */}
        <div className="my-2 h-1.5 w-full overflow-hidden rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
          <div
            className="h-full rounded-full bg-[#F25912] transition-all duration-300"
            style={{ width: `${Math.max(1, percentProgress)}%` }}
          />
        </div>

        <div className="flex justify-between text-[11px] font-mono text-[var(--text-muted)]">
          <span>TIME: {replayState.source_time}</span>
          <span>{percentProgress}%</span>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="flex items-center justify-center gap-2 pt-2 border-t border-[var(--border-subtle)]">
        <button
          type="button"
          onClick={() => controlReplay('restart')}
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] transition-all hover:border-[#5C3E94] hover:text-[#5C3E94] active:scale-95"
          title="Restart Replay Cursor"
        >
          <RotateCcw size={14} />
        </button>

        <button
          type="button"
          onClick={() => controlReplay('rewind')}
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] transition-all hover:border-[#5C3E94] hover:text-[#5C3E94] active:scale-95"
          title="Rewind 100 Rows"
        >
          <FastForward size={14} className="rotate-180" />
        </button>

        {replayState.status === 'PLAYING' ? (
          <button
            type="button"
            onClick={() => controlReplay('pause')}
            className="flex h-8 w-12 items-center justify-center rounded-xl border border-amber-500/40 bg-amber-500/15 text-amber-600 dark:text-amber-400 font-semibold transition-all hover:bg-amber-500/25 active:scale-95"
            title="Pause Replay"
          >
            <Pause size={15} />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => controlReplay('play')}
            className="flex h-8 w-12 items-center justify-center rounded-xl border border-emerald-500/40 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-semibold transition-all hover:bg-emerald-500/25 active:scale-95"
            title="Play Replay"
          >
            <Play size={15} />
          </button>
        )}
      </div>
    </BentoTile>
  );
};
