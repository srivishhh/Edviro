import React, { useState } from 'react';
import { Header } from '../../components/Header';
import { BentoGrid } from '../../components/BentoGrid';
import { HeroTile } from './tiles/HeroTile';
import { LiveFacilityTile } from './tiles/LiveFacilityTile';
import { LiveTelemetryTile } from './tiles/LiveTelemetryTile';
import { ReplayPlayerTile } from './tiles/ReplayPlayerTile';
import { FacilityHealthTile } from './tiles/FacilityHealthTile';
import { ActiveAlertTile } from './tiles/ActiveAlertTile';
import { AIInvestigationTile } from './tiles/AIInvestigationTile';
import { FacilityXRayTile } from './tiles/FacilityXRayTile';
import { TechnicianTile } from './tiles/TechnicianTile';
import { RagAssistantTile } from './tiles/RagAssistantTile';
import { RagAssistant } from '../rag/RagAssistant';
import { SNSResultModal } from './SNSResultModal';
import { AceternityGradientBg } from '../../components/ui/AceternityGradientBg';

const CommandCenter: React.FC = () => {
  const [isRagOpen, setIsRagOpen] = useState(false);
  const [isSNSModalOpen, setIsSNSModalOpen] = useState(false);
  const [snsModalTab, setSnsModalTab] = useState<'combined' | 'sns' | 'xray'>('combined');

  const handleOpenSNSResult = (tab: 'combined' | 'sns' | 'xray' = 'combined') => {
    setSnsModalTab(tab);
    setIsSNSModalOpen(true);
  };

  return (
    <div className="relative min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] selection:bg-[#F25912] selection:text-white transition-colors duration-200">
      <AceternityGradientBg />
      <Header />

      <main className="relative z-10 mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <BentoGrid>
          {/* Row 1: Left Hero Identity (2 cols), Live Facility State (1 col), Facility Health (1 col) */}
          <HeroTile />
          <LiveFacilityTile />
          <FacilityHealthTile />

          {/* Row 2: Live Telemetry Graph (2 cols), Replay Controls (1 col), Active Alert (1 col) */}
          <LiveTelemetryTile />
          <ReplayPlayerTile />
          <ActiveAlertTile />

          {/* Row 3: AI Investigation (1 col), Facility X-Ray Diagnosis (2 cols), RAG Assistant (1 col) */}
          <AIInvestigationTile onOpenResult={() => handleOpenSNSResult('sns')} />
          <FacilityXRayTile onOpenResult={() => handleOpenSNSResult('combined')} />
          <RagAssistantTile onOpen={() => setIsRagOpen(true)} />

          {/* Row 4: Technician Performance & Wallet Overview (spanning 4 cols) */}
          <div className="col-span-1 md:col-span-2 lg:col-span-4">
            <TechnicianTile />
          </div>
        </BentoGrid>
      </main>

      <RagAssistant isOpen={isRagOpen} onClose={() => setIsRagOpen(false)} />
      <SNSResultModal
        isOpen={isSNSModalOpen}
        onClose={() => setIsSNSModalOpen(false)}
        initialTab={snsModalTab}
      />
    </div>
  );
};

export default CommandCenter;
