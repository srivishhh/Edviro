import React from 'react';
import { Activity, ShieldCheck, Zap } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';
import { useTheme } from '../../../app/ThemeProvider';

export const HeroTile: React.FC = () => {
  const { theme } = useTheme();

  return (
    <BentoTile span="col-span-1 md:col-span-2 lg:col-span-2" variant="hero" className="flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 mb-3">
            <span className="rounded-lg bg-[#5C3E94]/15 border border-[#5C3E94]/30 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-[#5C3E94] dark:text-purple-300">
              LBNL Facility Data
            </span>
            <span className="text-xs text-[var(--text-muted)] font-mono">BLDG 74 • SINGLE-DUCT AHU</span>
          </div>

          <div className="h-10 w-10 p-1 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] opacity-80 group-hover:opacity-100 transition-opacity">
            <img
              src="/logo.png"
              alt="Logo Emblem"
              className={`h-full w-full object-contain ${
                theme === 'dark' ? 'invert brightness-125' : 'brightness-90'
              }`}
            />
          </div>
        </div>

        <h1 className="text-3xl font-extrabold tracking-tight text-[var(--text-main)] sm:text-4xl">
          GSENSE <span className="font-normal text-[var(--text-muted)]">Intelligence</span>
        </h1>
        
        <p className="mt-2 text-sm text-[var(--text-muted)] max-w-md leading-relaxed font-normal">
          &ldquo;See the facility. Understand the fault. Act with confidence.&rdquo;
        </p>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-3 pt-4 border-t border-[var(--border-subtle)]">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-[var(--text-muted)]">
            <Activity size={13} className="text-[#5C3E94] dark:text-purple-400" />
            <span>FACILITY</span>
          </div>
          <span className="text-xs font-semibold text-[var(--text-main)]">LBNL AHU Live</span>
        </div>

        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-[var(--text-muted)]">
            <ShieldCheck size={13} className="text-emerald-500" />
            <span>TWIN STATE</span>
          </div>
          <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">OPERATIONAL</span>
        </div>

        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-[var(--text-muted)]">
            <Zap size={13} className="text-[#F25912]" />
            <span>SNS COPILOT</span>
          </div>
          <span className="text-xs font-semibold text-[var(--text-main)]">10 AGENTS</span>
        </div>
      </div>
    </BentoTile>
  );
};
