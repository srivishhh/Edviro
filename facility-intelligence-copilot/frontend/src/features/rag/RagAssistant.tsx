import React, { useState } from 'react';
import { Bot, Send, X, FileText } from 'lucide-react';
import { useTheme } from '../../app/ThemeProvider';

interface SourceCitation {
  doc_id: string;
  incident_id: string;
  asset_id: string;
  document_type: string;
  severity: string;
  timestamp: string;
  title: string;
  fault_type: string;
}

interface Message {
  sender: 'user' | 'assistant';
  text: string;
  sources?: SourceCitation[];
  grounded?: boolean;
  timestamp: string;
}

interface RagAssistantProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RagAssistant: React.FC<RagAssistantProps> = ({ isOpen, onClose }) => {
  const { theme } = useTheme();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      text: "Hello, I am the GSENSE Facility Memory Copilot. Ask me about historical incidents, past diagnostic investigations, technician resolution outcomes, or asset anomaly trends.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const quickQueries = [
    "What happened to AHU-007?",
    "Have we seen this airflow problem before?",
    "What was the previous resolution for AHU-003?",
    "Which chiller had high evaporator approach temp?",
  ];

  const handleSend = async (customQuery?: string) => {
    const q = customQuery || query;
    if (!q.trim() || loading) return;

    const userMsg: Message = {
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMsg: Message = {
          sender: 'assistant',
          text: data.answer,
          sources: data.sources,
          grounded: data.grounded,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'assistant',
            text: "Error communicating with Facility Memory service.",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: "NO MATCHING FACILITY RECORD FOUND or service unavailable.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="flex h-[600px] w-full max-w-2xl flex-col rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] shadow-2xl overflow-hidden transition-colors">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-6 py-4 bg-[var(--bg-surface)]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-1.5 shadow-sm">
              <img
                src="/logo.png"
                alt="Logo"
                className={`h-full w-full object-contain ${
                  theme === 'dark' ? 'invert brightness-125' : 'brightness-90'
                }`}
              />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[var(--text-main)]">Facility Memory & RAG Copilot</h2>
              <p className="text-[11px] text-[var(--text-muted)]">Grounded historical reasoning across all facility telemetry & reports</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl p-1.5 text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-main)]"
          >
            <X size={18} />
          </button>
        </div>

        {/* Message Stream */}
        <div className="flex-1 space-y-4 overflow-y-auto p-6 text-xs" data-lenis-prevent>
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl p-4 leading-relaxed ${
                  m.sender === 'user'
                    ? 'bg-[#5C3E94] text-white rounded-br-sm'
                    : 'bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-main)] rounded-bl-sm shadow-sm'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.text}</div>

                {/* Source Citations */}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-3 border-t border-[var(--border-subtle)] pt-2.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#F25912]">
                      Grounded Citations ({m.sources.length})
                    </span>
                    <div className="mt-1.5 space-y-1.5">
                      {m.sources.map((src) => (
                        <div
                          key={src.doc_id}
                          className="flex items-center justify-between rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] px-2.5 py-1.5 text-[11px]"
                        >
                          <div className="flex items-center gap-2">
                            <FileText size={12} className="text-[#F25912]" />
                            <span className="font-semibold text-[var(--text-main)]">{src.asset_id}</span>
                            <span className="font-mono text-[var(--text-muted)]">({src.incident_id})</span>
                          </div>
                          <span className="rounded-lg bg-[#5C3E94]/15 px-1.5 py-0.5 text-[10px] font-mono text-[#5C3E94] dark:text-purple-300 font-medium border border-[#5C3E94]/30">
                            {src.document_type}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <span className="mt-1 px-1 text-[10px] text-[var(--text-muted)]">{m.timestamp}</span>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 rounded-xl bg-[var(--bg-surface)] p-3 text-[var(--text-muted)] border border-[var(--border-subtle)]">
              <Bot size={16} className="animate-spin text-[#F25912]" />
              <span>Querying historical facility intelligence graph...</span>
            </div>
          )}
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap gap-1.5 border-t border-[var(--border-subtle)] px-6 py-2.5 bg-[var(--bg-surface)]">
          {quickQueries.map((qText, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSend(qText)}
              className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-2.5 py-1 text-[11px] text-[var(--text-muted)] transition-colors hover:border-[#F25912] hover:text-[#F25912]"
            >
              {qText}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="border-t border-[var(--border-subtle)] p-4 bg-[var(--bg-surface)]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask Facility Memory (e.g. What happened to AHU-007?)..."
              className="flex-1 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-2.5 text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] focus:border-[#F25912] focus:outline-none"
            />
            <button
              type="submit"
              disabled={!query.trim() || loading}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#F25912] text-white shadow-sm transition-all hover:bg-orange-600 active:scale-95 disabled:opacity-40"
            >
              <Send size={15} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
