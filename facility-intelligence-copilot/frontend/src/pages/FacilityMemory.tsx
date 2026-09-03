import { useState, type FormEvent } from 'react';
import {
  Bot,
  Brain,
  Clock,
  Plus,
  Search,
  Sparkles,
  User,
} from 'lucide-react';

interface MemoryItem {
  id: string;
  assetCode: string;
  assetName: string;
  incidentType: string;
  timestamp: string;
  symptoms: string[];
  rootCause: string;
  correctiveAction: string;
  sopReference: string;
  technician: string;
  verificationMethod: string;
}

const INITIAL_MEMORIES: MemoryItem[] = [
  {
    id: 'MEM-2026-104',
    assetCode: 'HVAC-007',
    assetName: 'LBNL RTU Rooftop Unit #7',
    incidentType: 'Condenser Coil Fin Fouling',
    timestamp: '2026-09-01 12:15',
    symptoms: [
      'Compressor discharge head pressure elevated to 31.5 bar (456.6 psi)',
      'Electrical power surged to 140.6 kW under high back-pressure',
      'Exterior heat exchanger fin obstruction from pollen/particulate buildup',
    ],
    rootCause:
      'Severe particulate and pollen accumulation on exterior condenser coil fins inhibiting ambient heat rejection.',
    correctiveAction:
      'Washed condenser coils with non-acidic foaming chemical coil cleaner and verified fan motor current draw.',
    sopReference: 'SOP-RTU-COND-01 (Condenser Rejection & Coil Maintenance)',
    technician: 'Senior HVAC Tech (LBNL Plant Operations)',
    verificationMethod:
      'Post-wash discharge pressure normalized to 14.2 bar; power draw decreased to 8.2 kW baseline.',
  },
  {
    id: 'MEM-2026-089',
    assetCode: 'HVAC-007',
    assetName: 'LBNL RTU Rooftop Unit #7',
    incidentType: 'Intake Filter Particulate Restriction',
    timestamp: '2026-08-14 14:20',
    symptoms: [
      'Airflow velocity dropped to 64% design rating',
      'Plenum chamber supply temp rose to 30.1°C',
      'Fan motor power draw elevated +4.2 kW above baseline',
    ],
    rootCause:
      'Physical particulate loading on intake MERV-13 air filter cartridge creating 36% aerodynamic drag.',
    correctiveAction:
      'Replaced primary MERV-13 intake filter cartridge and zero-calibrated static differential transducer.',
    sopReference: 'SOP-HVAC-FLT-02 (Level 2 Filtration Service)',
    technician: 'Lead Facility Operations Specialist',
    verificationMethod:
      'Measured static pressure dropped from 2.8 in.w.g to 0.45 in.w.g; airflow restored to 98%.',
  },
  {
    id: 'MEM-2026-074',
    assetCode: 'CHILLER-001',
    assetName: 'Primary Water Chiller',
    incidentType: 'Expansion Valve Stepper Sticking',
    timestamp: '2026-07-29 11:05',
    symptoms: [
      'Low evaporator suction superheat fluctuation (2.1°C to 11.4°C)',
      'Chilled water delta-T degraded by 1.8°C',
    ],
    rootCause:
      'Electronic expansion valve (EEV) stepper actuator mechanical friction under thermal cycling.',
    correctiveAction:
      'Exercised and re-indexed EEV stepper motor; applied dielectric lubricant to actuator spindle.',
    sopReference: 'SOP-CHL-VALV-04 (Electronic Expansion Calibration)',
    technician: 'Senior Refrigeration Specialist',
    verificationMethod:
      'Superheat stabilized at 5.5°C +/- 0.3°C across 4-hour full capacity load run.',
  },
];

export default function FacilityMemory() {
  const [memories, setMemories] = useState<MemoryItem[]>(INITIAL_MEMORIES);
  const [search, setSearch] = useState('');
  const [selectedMemory, setSelectedMemory] = useState<MemoryItem>(INITIAL_MEMORIES[0]);

  // Copilot Chat State
  const [copilotPrompt, setCopilotPrompt] = useState('');
  const [copilotResponses, setCopilotResponses] = useState<
    Array<{ role: 'user' | 'assistant'; text: string; citations?: string[] }>
  >([
    {
      role: 'assistant',
      text: 'Hello, I am the GSENSE Facility Memory Copilot. I have indexed all historical incident logs, causal X-Ray resolutions, and maintenance SOPs. How can I assist you with institutional facility knowledge today?',
    },
  ]);
  const [isAsking, setIsAsking] = useState(false);

  // New Log Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newLog, setNewLog] = useState({
    assetCode: 'HVAC-007',
    incidentType: '',
    whatHappened: '',
    rootCause: '',
    fixApplied: '',
    sopRef: '',
    techName: '',
  });

  const handleAskCopilot = (e: FormEvent) => {
    e.preventDefault();
    if (!copilotPrompt.trim() || isAsking) return;

    const userQ = copilotPrompt.trim();
    setCopilotPrompt('');
    setCopilotResponses((prev) => [...prev, { role: 'user', text: userQ }]);
    setIsAsking(true);

    setTimeout(() => {
      let reply = '';
      let citations: string[] = [];

      if (userQ.toLowerCase().includes('condenser') || userQ.toLowerCase().includes('fouling') || userQ.toLowerCase().includes('pressure')) {
        reply =
          'According to LBNL institutional record MEM-2026-104, Rooftop Unit HVAC-007 experienced severe condenser coil fin fouling causing discharge head pressure to spike to 31.5 bar and electrical power demand to surge to 140.6 kW. Recommended SOP: Wash exterior condenser coils with non-acidic chemical coil cleaner, inspect condenser fans, and verify liquid line subcooling.';
        citations = ['MEM-2026-104', 'SOP-RTU-COND-01', 'LBNL-AFDD-REF'];
      } else if (userQ.toLowerCase().includes('hvac-007') || userQ.toLowerCase().includes('filter') || userQ.toLowerCase().includes('airflow')) {
        reply =
          'According to institutional record MEM-2026-089 (August 14, 2026), HVAC-007 experienced an identical pattern: intake MERV-13 particulate loading caused 48% airflow restriction and 30.1°C plenum overheating. Recommended SOP: replace primary MERV-13 filter and re-zero the static differential pressure transducer.';
        citations = ['MEM-2026-089', 'SOP-HVAC-FLT-02'];
      } else if (userQ.toLowerCase().includes('chiller') || userQ.toLowerCase().includes('valve')) {
        reply =
          'Historical record MEM-2026-074 indicates CHILLER-002 had expansion valve stepper motor sticking under high ambient heat loads. Technician re-indexed the actuator positioning mechanism.';
        citations = ['MEM-2026-074'];
      } else {
        reply = `Cross-referencing institutional records for "${userQ}"... Most incidents in this category correlate with periodic condenser coil fouling or differential pressure calibration drift.`;
        citations = ['SOP-GEN-MAINT-01'];
      }

      setCopilotResponses((prev) => [
        ...prev,
        { role: 'assistant', text: reply, citations },
      ]);
      setIsAsking(false);
    }, 500);
  };

  const handleAddLog = (e: FormEvent) => {
    e.preventDefault();
    if (!newLog.incidentType || !newLog.whatHappened) return;

    const entry: MemoryItem = {
      id: `MEM-2026-0${Math.floor(Math.random() * 900 + 100)}`,
      assetCode: newLog.assetCode,
      assetName: newLog.assetCode.startsWith('HVAC') ? `Air Handling Unit (${newLog.assetCode})` : 'Chiller Subsystem',
      incidentType: newLog.incidentType,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 16),
      symptoms: [newLog.whatHappened],
      rootCause: newLog.rootCause || 'Identified via technician investigation',
      correctiveAction: newLog.fixApplied || 'Standard preventative servicing',
      sopReference: newLog.sopRef || 'SOP-GEN-MAINT',
      technician: newLog.techName || 'Duty Technician',
      verificationMethod: 'Sensor telemetry verified within nominal bounds post-service.',
    };

    setMemories([entry, ...memories]);
    setSelectedMemory(entry);
    setShowAddModal(false);
    setNewLog({
      assetCode: 'HVAC-007',
      incidentType: '',
      whatHappened: '',
      rootCause: '',
      fixApplied: '',
      sopRef: '',
      techName: '',
    });
  };

  const filtered = memories.filter(
    (m) =>
      m.assetCode.toLowerCase().includes(search.toLowerCase()) ||
      m.incidentType.toLowerCase().includes(search.toLowerCase()) ||
      m.rootCause.toLowerCase().includes(search.toLowerCase()) ||
      m.technician.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="saas-card p-6 md:p-8 space-y-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-zinc-500">
            <Brain size={16} />
            <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Institutional Knowledge Engine</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-950 editorial-title tracking-tight">
            Facility Memory
          </h1>
          <p className="text-zinc-600 text-xs sm:text-sm max-w-2xl leading-relaxed">
            Institutional knowledge repository storing past root causes, corrective SOPs, technician notes, and causal AI learnings to eliminate repeat diagnostic effort.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-zinc-950 text-white font-semibold hover:bg-zinc-800 transition-all text-xs cursor-pointer shadow-sm shrink-0"
        >
          <Plus size={13} />
          <span>Log Corrective Action</span>
        </button>
      </div>

      {/* Main Two-Column Split: Copilot Q&A vs Archive & Inspector */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Historical Record Explorer + Record Inspector */}
        <div className="lg:col-span-2 space-y-6">
          {/* Search bar */}
          <div className="saas-card p-4 flex items-center gap-3">
            <Search size={14} className="text-zinc-400" />
            <input
              type="text"
              placeholder="Search past root causes, SOPs, asset codes, or technicians..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-transparent text-xs text-zinc-800 placeholder-zinc-400 focus:outline-none font-sans"
            />
          </div>

          {/* Records Table / Cards */}
          <div className="space-y-3">
            {filtered.map((item) => {
              const isSelected = selectedMemory.id === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedMemory(item)}
                  className={`saas-card p-5 cursor-pointer transition-all space-y-3 ${
                    isSelected
                      ? 'border-zinc-900 ring-2 ring-zinc-900/10 shadow-md bg-white'
                      : 'hover:border-zinc-300 bg-zinc-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-zinc-900 bg-zinc-100 px-2 py-0.5 rounded border border-zinc-200">
                          {item.id}
                        </span>
                        <span className="font-mono text-xs text-zinc-600 font-semibold">{item.assetCode}</span>
                        <span className="text-zinc-400">&bull;</span>
                        <span className="text-xs text-zinc-500">{item.assetName}</span>
                      </div>
                      <h3 className="text-sm font-bold text-zinc-900">{item.incidentType}</h3>
                    </div>

                    <div className="flex items-center gap-1.5 text-zinc-400 font-mono text-[11px] shrink-0">
                      <Clock size={12} />
                      <span>{item.timestamp}</span>
                    </div>
                  </div>

                  <p className="text-xs text-zinc-600 line-clamp-2 leading-relaxed">
                    <strong className="text-zinc-800">Root Cause:</strong> {item.rootCause}
                  </p>

                  <div className="flex items-center justify-between text-[11px] font-mono text-zinc-500 pt-2 border-t border-zinc-100">
                    <span>SOP: {item.sopReference.split(' ')[0]}</span>
                    <span>Logged by: {item.technician}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Selected Memory Inspector */}
          {selectedMemory && (
            <div className="saas-card p-6 md:p-8 space-y-6 bg-white border-zinc-900/40">
              <div className="flex items-start justify-between border-b border-zinc-100 pb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-zinc-900 text-white font-mono text-xs font-bold">
                      {selectedMemory.id}
                    </span>
                    <span className="text-xs font-mono font-bold text-zinc-700">{selectedMemory.assetCode}</span>
                  </div>
                  <h2 className="text-lg font-bold text-zinc-900">{selectedMemory.incidentType}</h2>
                </div>

                <div className="text-right text-xs font-mono text-zinc-400 space-y-0.5">
                  <p>Resolved: {selectedMemory.timestamp}</p>
                  <p className="text-zinc-700 font-semibold">{selectedMemory.technician}</p>
                </div>
              </div>

              {/* Observed Symptoms */}
              <div className="space-y-2">
                <h4 className="text-[10px] uppercase font-mono font-bold tracking-wider text-zinc-400">
                  Observed Physical Symptoms
                </h4>
                <div className="space-y-1.5">
                  {selectedMemory.symptoms.map((s, i) => (
                    <div key={i} className="p-2.5 rounded-xl bg-zinc-50 border border-zinc-200/80 text-xs text-zinc-700 font-mono">
                      &bull; {s}
                    </div>
                  ))}
                </div>
              </div>

              {/* Root Cause & Fix */}
              <div className="grid gap-4 sm:grid-cols-2 text-xs">
                <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200/80 space-y-1.5">
                  <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-zinc-400 block">
                    Institutional Root Cause
                  </span>
                  <p className="text-zinc-800 leading-relaxed font-medium">{selectedMemory.rootCause}</p>
                </div>

                <div className="p-4 rounded-2xl bg-emerald-50/50 border border-emerald-200/80 space-y-1.5">
                  <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-emerald-800 block">
                    Corrective SOP Action Executed
                  </span>
                  <p className="text-emerald-950 leading-relaxed font-medium">{selectedMemory.correctiveAction}</p>
                </div>
              </div>

              {/* SOP & Verification */}
              <div className="space-y-2 pt-2 border-t border-zinc-100 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-zinc-500">Standard Operating Procedure:</span>
                  <span className="font-mono font-bold text-zinc-900">{selectedMemory.sopReference}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-zinc-500">Telemetry Verification:</span>
                  <span className="text-zinc-700 font-medium">{selectedMemory.verificationMethod}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right 1 Col: Institutional Memory AI Assistant */}
        <div className="lg:col-span-1 space-y-6">
          <div className="saas-card p-6 space-y-4 bg-white flex flex-col justify-between h-[640px] sticky top-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
                <div className="flex items-center gap-2 text-zinc-900">
                  <Bot size={18} strokeWidth={2} />
                  <h3 className="text-sm font-bold">Facility Memory Copilot</h3>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                  RAG INDEXED
                </span>
              </div>

              {/* Chat Thread */}
              <div className="space-y-3 overflow-y-auto max-h-[460px] pr-1 text-xs">
                {copilotResponses.map((msg, i) => (
                  <div
                    key={i}
                    className={`p-3.5 rounded-2xl space-y-2 ${
                      msg.role === 'user'
                        ? 'bg-zinc-900 text-white ml-6'
                        : 'bg-zinc-50 border border-zinc-200/80 text-zinc-800 mr-2'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-mono text-[10px] text-zinc-400">
                      {msg.role === 'user' ? <User size={11} /> : <Sparkles size={11} />}
                      <span>{msg.role === 'user' ? 'Operator' : 'Memory Agent'}</span>
                    </div>
                    <p className="leading-relaxed">{msg.text}</p>
                    {msg.citations && (
                      <div className="flex items-center gap-1 flex-wrap pt-1">
                        {msg.citations.map((c) => (
                          <span
                            key={c}
                            className="px-2 py-0.5 rounded-md bg-white text-zinc-900 border border-zinc-200 font-mono text-[9px] font-bold"
                          >
                            Ref: {c}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {isAsking && (
                  <div className="p-3 rounded-2xl bg-zinc-50 border border-zinc-200 text-xs font-mono text-zinc-400 animate-pulse">
                    Querying institutional memory graph...
                  </div>
                )}
              </div>
            </div>

            {/* Prompt Input Box */}
            <form onSubmit={handleAskCopilot} className="pt-3 border-t border-zinc-100 space-y-2">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Ask memory: 'How was HVAC-007 fixed previously?'"
                  value={copilotPrompt}
                  onChange={(e) => setCopilotPrompt(e.target.value)}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 placeholder-zinc-400 focus:outline-none focus:border-zinc-900 font-sans"
                />
              </div>
              <button
                type="submit"
                disabled={isAsking || !copilotPrompt.trim()}
                className="w-full py-2 rounded-xl bg-zinc-950 text-white text-xs font-semibold hover:bg-zinc-800 transition-colors disabled:opacity-50 cursor-pointer"
              >
                Query Facility Memory
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Log Corrective Action Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 md:p-8 space-y-5 shadow-2xl border border-zinc-200">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <h3 className="text-base font-bold text-zinc-900">Record Corrective Action to Facility Memory</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-zinc-400 hover:text-zinc-600 cursor-pointer text-xs"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleAddLog} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-700">Target Asset</label>
                  <select
                    value={newLog.assetCode}
                    onChange={(e) => setNewLog({ ...newLog, assetCode: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-2 font-mono"
                  >
                    <option value="HVAC-007">HVAC-007 (AHU Floor 2)</option>
                    <option value="HVAC-001">HVAC-001 (Auditorium AHU)</option>
                    <option value="CHILLER-001">CHILLER-001 (Primary Chiller)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-zinc-700">Incident Category</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Filter Particulate Loading"
                    value={newLog.incidentType}
                    onChange={(e) => setNewLog({ ...newLog, incidentType: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-2 font-sans"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-zinc-700">Observed Telemetry Symptoms</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Airflow dropped to 64%, supply temp rose to 30.1°C"
                  value={newLog.whatHappened}
                  onChange={(e) => setNewLog({ ...newLog, whatHappened: e.target.value })}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-2 font-sans"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-zinc-700">Root Cause Identified</label>
                <input
                  type="text"
                  placeholder="e.g. MERV-13 air filter clogged with fine particulates"
                  value={newLog.rootCause}
                  onChange={(e) => setNewLog({ ...newLog, rootCause: e.target.value })}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-2 font-sans"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-zinc-700">Corrective Action Taken</label>
                <input
                  type="text"
                  placeholder="e.g. Swapped filter cartridge and re-zeroed sensor"
                  value={newLog.fixApplied}
                  onChange={(e) => setNewLog({ ...newLog, fixApplied: e.target.value })}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-2 font-sans"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-700">SOP Reference Code</label>
                  <input
                    type="text"
                    placeholder="e.g. SOP-HVAC-FLT-02"
                    value={newLog.sopRef}
                    onChange={(e) => setNewLog({ ...newLog, sopRef: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-2 font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-zinc-700">Technician Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Lead Facility Specialist"
                    value={newLog.techName}
                    onChange={(e) => setNewLog({ ...newLog, techName: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-2 font-sans"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-zinc-950 text-white font-semibold hover:bg-zinc-800 transition-colors cursor-pointer mt-2"
              >
                Save to Institutional Memory
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
