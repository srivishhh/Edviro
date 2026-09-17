import React from 'react';
import { Sparkles, MessageSquare, ArrowRight } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';

interface RagAssistantTileProps {
  onOpen: () => void;
}

export const RagAssistantTile: React.FC<RagAssistantTileProps> = ({ onOpen }) => {
  return (
    <BentoTile
      span="col-span-1"
      variant="translucent"
      onClick={onOpen}
      className="flex flex-col justify-between"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-[#F25912]" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">FACILITY MEMORY</span>
        </div>
        <span className="rounded-lg bg-[#5C3E94]/15 px-2 py-0.5 text-[10px] font-mono font-medium text-[#5C3E94] dark:text-purple-300 border border-[#5C3E94]/30">
          RAG ACTIVE
        </span>
      </div>

      <div className="my-3">
        <h3 className="text-base font-bold text-[var(--text-main)]">Facility Memory Copilot</h3>
        <p className="mt-1 text-xs text-[var(--text-muted)] leading-relaxed">
          Ask questions about historical anomalies, verified technician fixes, and LBNL baseline benchmarks.
        </p>
      </div>

      <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-2 text-xs text-[#F25912] font-semibold group">
        <div className="flex items-center gap-1.5">
          <MessageSquare size={13} />
          <span>Launch Chatbot</span>
        </div>
        <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
      </div>
    </BentoTile>
  );
};
