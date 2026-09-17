import React, { useRef, useState } from 'react';
import { Play, Pause, RotateCcw, FastForward, PlaySquare } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useRealtime } from '../../../hooks/useRealtime';

export const ReplayPlayerTile: React.FC = () => {
  const { replayState, controlReplay } = useRealtime();
  const progressBarRef = useRef<HTMLDivElement>(null);
  const [hoverRow, setHoverRow] = useState<number | null>(null);
  const [hoverPos, setHoverPos] = useState<number>(0);
  const [selectedSpeed, setSelectedSpeed] = useState<number>(1);

  const percentProgress = Math.round((replayState.current_row / replayState.total_rows) * 100 * 10) / 10;

  const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const ratio = clickX / rect.width;
    const targetRow = Math.max(1, Math.round(ratio * replayState.total_rows));
    controlReplay('seek', { target_row: targetRow });
  };

  const handleProgressBarMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const hoverX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const ratio = hoverX / rect.width;
    setHoverPos(hoverX);
    setHoverRow(Math.max(1, Math.round(ratio * replayState.total_rows)));
  };

  const handleSpeedChange = (speed: number) => {
    setSelectedSpeed(speed);
    controlReplay('speed', { speed });
  };

  const anomalyPresets = [
    { label: 'Baseline (0k)', row: 5000, color: 'text-emerald-500' },
    { label: 'Belt Slip (25k)', row: 25000, color: 'text-[#F25912]' },
    { label: 'Coil Sat (80k)', row: 80000, color: 'text-red-500' },
    { label: 'Surge (180k)', row: 180000, color: 'text-amber-500' },
    { label: 'Leak (320k)', row: 320000, color: 'text-purple-500' },
  ];

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
              ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
              : 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30'
          }`}
        >
          {replayState.status}
        </span>
      </div>

      <div className="my-2 space-y-2">
        <div className="flex items-baseline justify-between text-xs font-mono text-[var(--text-main)]">
          <span className="font-semibold text-[var(--text-muted)]">ROW CURSOR</span>
          <span className="text-[#F25912] font-bold">
            {replayState.current_row.toLocaleString()} / {replayState.total_rows.toLocaleString()}
          </span>
        </div>

        {/* Interactive Scrubbable Progress Track */}
        <div
          ref={progressBarRef}
          onClick={handleProgressBarClick}
          onMouseMove={handleProgressBarMouseMove}
          onMouseLeave={() => setHoverRow(null)}
          className="group/track relative h-4 w-full cursor-pointer rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center p-0.5 transition-all hover:border-[#F25912]/60 hover:bg-[var(--bg-card)]"
          title="Click or drag to seek to any point in the 525,541 LBNL dataset"
        >
          {/* Active progress fill */}
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#5C3E94] to-[#F25912] transition-all duration-150"
            style={{ width: `${Math.max(1.5, percentProgress)}%` }}
          />

          {/* Scrubber Knob */}
          <div
            className="absolute top-1/2 -translate-y-1/2 h-3.5 w-3.5 rounded-full bg-white border-2 border-[#F25912] shadow-md transition-all group-hover/track:scale-125"
            style={{ left: `calc(${Math.max(1, Math.min(98, percentProgress))}% - 7px)` }}
          />

          {/* Hover Scrub Tooltip */}
          {hoverRow !== null && (
            <div
              className="pointer-events-none absolute -top-8 -translate-x-1/2 rounded-md bg-[#181126] dark:bg-black/90 px-2 py-0.5 text-[10px] font-mono text-white shadow-lg border border-white/10 z-20 whitespace-nowrap"
              style={{ left: `${hoverPos}px` }}
            >
              Seek: Row {hoverRow.toLocaleString()} ({Math.round((hoverRow / replayState.total_rows) * 100)}%)
            </div>
          )}
        </div>

        <div className="flex justify-between text-[11px] font-mono text-[var(--text-muted)]">
          <span>TIME: {replayState.source_time}</span>
          <span className="font-semibold text-[var(--text-main)]">{percentProgress}%</span>
        </div>

        {/* Anomaly Quick-Seek Jumps */}
        <div className="flex flex-wrap items-center gap-1 pt-0.5">
          {anomalyPresets.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                controlReplay('seek', { target_row: preset.row });
              }}
              className={`rounded-md bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[#5C3E94] px-1.5 py-0.5 text-[9px] font-mono font-bold transition-all active:scale-95 ${preset.color}`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Control Buttons + Speed Selector */}
      <div className="flex flex-wrap items-center justify-between gap-1.5 pt-2 border-t border-[var(--border-subtle)]">
        {/* Playback Controls */}
        <div className="flex items-center gap-1.5">
          {/* Restart */}
          <button
            type="button"
            onClick={() => controlReplay('restart')}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] transition-all hover:border-[#5C3E94] hover:text-[#5C3E94] active:scale-95"
            title="Restart Replay Cursor (Row 1)"
          >
            <RotateCcw size={13} />
          </button>

          {/* Rewind 500 rows */}
          <button
            type="button"
            onClick={() => controlReplay('rewind', { step_size: 500 })}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] transition-all hover:border-[#5C3E94] hover:text-[#5C3E94] active:scale-95"
            title="Rewind 500 Rows"
          >
            <FastForward size={13} className="rotate-180" />
          </button>

          {/* Play / Pause Toggle */}
          {replayState.status === 'PLAYING' ? (
            <button
              type="button"
              onClick={() => controlReplay('pause')}
              className="flex h-7 w-10 items-center justify-center rounded-lg border border-amber-500/40 bg-amber-500/15 text-amber-600 dark:text-amber-400 font-semibold transition-all hover:bg-amber-500/25 active:scale-95"
              title="Pause Replay"
            >
              <Pause size={14} />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => controlReplay('play')}
              className="flex h-7 w-10 items-center justify-center rounded-lg border border-emerald-500/40 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-semibold transition-all hover:bg-emerald-500/25 active:scale-95"
              title="Play Replay"
            >
              <Play size={14} />
            </button>
          )}

          {/* Fast Forward 500 rows */}
          <button
            type="button"
            onClick={() => controlReplay('forward', { step_size: 500 })}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] transition-all hover:border-[#5C3E94] hover:text-[#5C3E94] active:scale-95"
            title="Fast Forward 500 Rows"
          >
            <FastForward size={13} />
          </button>
        </div>

        {/* Speed Selector */}
        <div className="flex items-center gap-0.5 rounded-lg bg-[var(--bg-surface)] p-0.5 border border-[var(--border-subtle)]">
          {[1, 2, 5, 10].map((spd) => (
            <button
              key={spd}
              type="button"
              onClick={() => handleSpeedChange(spd)}
              className={`rounded px-1.5 py-0.5 text-[9px] font-mono font-bold transition-all ${
                selectedSpeed === spd
                  ? 'bg-[#F25912] text-white shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>
    </BentoTile>
  );
};
