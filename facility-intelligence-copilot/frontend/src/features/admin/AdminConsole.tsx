import React, { useEffect, useState } from 'react';
import {
  Plus,
  ToggleLeft,
  ToggleRight,
  CheckCircle2,
  Bell,
  Award,
  FileText,
} from 'lucide-react';
import { Header } from '../../components/Header';
import { GlassCard } from '../../components/GlassCard';
import { AceternityGradientBg } from '../../components/ui/AceternityGradientBg';
import { useTheme } from '../../app/ThemeProvider';

interface Reward {
  id: string;
  name: string;
  description: string;
  cost: number;
  inventory: number;
  active: boolean;
  category: string;
}

interface ResolutionReport {
  report_id: string;
  incident_id: string;
  asset_id: string;
  technician_id: string;
  technician_name?: string;
  observed_problem: string;
  action_performed: string;
  root_cause_observed: string;
  parts_inspected?: string;
  resolution_status: string;
  review_status: string;
  submitted_at: string;
  suggested_credits: number;
  awarded_credits?: number;
  admin_notes?: string;
  evidence?: string;
}

interface AdminNotification {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export const AdminConsole: React.FC = () => {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<'reports' | 'rewards' | 'notifications'>('reports');
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [reports, setReports] = useState<ResolutionReport[]>([]);
  const [notifications, setNotifications] = useState<AdminNotification[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);

  // Approval modal state
  const [selectedReport, setSelectedReport] = useState<ResolutionReport | null>(null);
  const [approvalCredits, setApprovalCredits] = useState<number>(150);
  const [adminNotes, setAdminNotes] = useState<string>('Verified on-time resolution');
  const [isProcessing, setIsProcessing] = useState(false);

  // New reward form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [cost, setCost] = useState(500);
  const [inventory, setInventory] = useState(10);
  const [category, setCategory] = useState('Perks');

  const fetchAdminData = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/admin/rewards');
      if (res.ok) setRewards(await res.json());

      const repRes = await fetch('http://127.0.0.1:8000/api/v1/admin/reports');
      if (repRes.ok) setReports(await repRes.json());

      const notifRes = await fetch('http://127.0.0.1:8000/api/v1/admin/notifications');
      if (notifRes.ok) setNotifications(await notifRes.json());
    } catch {
      // Backend fallback
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleApproveReport = async (incidentId: string) => {
    setIsProcessing(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/admin/reports/${incidentId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved_credits: Number(approvalCredits),
          credits: Number(approvalCredits),
          admin_notes: adminNotes,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        alert(data.message || `Report Approved! +${approvalCredits} credits transferred to technician.`);
        setSelectedReport(null);
        await fetchAdminData();
      } else {
        const err = await res.json();
        alert(`Approval Error: ${err.detail || 'Could not approve report.'}`);
      }
    } catch {
      alert('Error connecting to backend server.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleActive = async (id: string, current: boolean) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/admin/rewards/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !current }),
      });
      if (res.ok) fetchAdminData();
    } catch {
      // Network error
    }
  };

  const handleCreateReward = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/admin/rewards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description, cost, inventory, category, active: true }),
      });
      if (res.ok) {
        setShowAddModal(false);
        setName('');
        setDescription('');
        fetchAdminData();
      }
    } catch {
      // Network error
    }
  };

  const pendingCount = reports.filter(
    (r) => r.review_status === 'PENDING' || r.review_status === 'UNDER_REVIEW'
  ).length;

  return (
    <div className="relative min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] selection:bg-[#F25912] selection:text-white transition-colors duration-200">
      <AceternityGradientBg />
      <Header />

      <main className="relative z-10 mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Admin Header Banner */}
        <GlassCard className="p-6 mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-2.5 shadow-md">
              <img
                src="/logo.png"
                alt="GSENSE Logo"
                className={`h-full w-full object-contain ${
                  theme === 'dark' ? 'invert brightness-125' : 'brightness-90'
                }`}
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black text-[var(--text-main)] tracking-tight">Admin Governance Console</h1>
                <span className="rounded-lg bg-[#F25912]/15 px-2.5 py-0.5 text-xs font-bold text-[#F25912] border border-[#F25912]/30">
                  OPERATIONS ROOT
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Technician report authorization, credit transfers, and reward store management.
              </p>
            </div>
          </div>

          {/* Quick Tab Switcher */}
          <div className="flex items-center gap-1 rounded-2xl bg-[var(--bg-surface)] p-1.5 border border-[var(--border-subtle)] shadow-inner">
            <button
              type="button"
              onClick={() => setActiveTab('reports')}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all ${
                activeTab === 'reports'
                  ? 'bg-[#F25912] text-white shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              <FileText size={15} />
              <span>Pending Reviews ({pendingCount})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('rewards')}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all ${
                activeTab === 'rewards'
                  ? 'bg-[#5C3E94] text-white shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              <Award size={15} />
              <span>Reward Catalog</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('notifications')}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all ${
                activeTab === 'notifications'
                  ? 'bg-[#5C3E94] text-white shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              <Bell size={15} />
              <span>Audit Log ({notifications.length})</span>
            </button>
          </div>
        </GlassCard>

        {/* Tab 1: Resolution Reports Review */}
        {activeTab === 'reports' && (
          <div className="space-y-4">
            {reports.map((report) => {
              const isPending = report.review_status === 'PENDING' || report.review_status === 'UNDER_REVIEW';
              return (
                <GlassCard key={report.report_id} className="p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-base font-bold text-[var(--text-main)]">INCIDENT: {report.incident_id}</span>
                        <span className="rounded-lg bg-[#5C3E94]/15 px-2.5 py-0.5 text-xs font-mono text-[#5C3E94] dark:text-purple-300 font-semibold border border-[#5C3E94]/30">
                          {report.asset_id}
                        </span>
                        <span
                          className={`rounded-lg px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                            report.review_status === 'APPROVED'
                              ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                              : 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {report.review_status}
                        </span>
                      </div>

                      <p className="text-xs text-[var(--text-muted)]">
                        Submitted by <strong className="text-[var(--text-main)]">{report.technician_name || report.technician_id}</strong> on{' '}
                        {new Date(report.submitted_at).toLocaleString()}
                      </p>
                    </div>

                    {isPending ? (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedReport(report);
                          setApprovalCredits(report.suggested_credits || 150);
                        }}
                        className="flex items-center gap-1.5 rounded-xl bg-[#F25912] px-4 py-2 text-xs font-bold text-white shadow-md shadow-orange-950/20 transition-all hover:bg-orange-600 active:scale-95"
                      >
                        <CheckCircle2 size={15} />
                        <span>Review & Authorize (+{report.suggested_credits || 150} Credits)</span>
                      </button>
                    ) : (
                      <div className="flex items-center gap-1.5 rounded-xl bg-emerald-500/15 px-3 py-1.5 text-xs font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 size={15} />
                        <span>Awarded +{report.awarded_credits} Credits</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 rounded-2xl bg-[var(--bg-surface)] p-4 text-xs border border-[var(--border-subtle)]">
                    <div>
                      <span className="font-semibold text-[var(--text-muted)]">Observed Problem</span>
                      <p className="text-[var(--text-main)] mt-1 font-medium">{report.observed_problem}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-[var(--text-muted)]">Action Performed</span>
                      <p className="text-[var(--text-main)] mt-1 font-medium">{report.action_performed}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-[var(--text-muted)]">Identified Root Cause</span>
                      <p className="text-[var(--text-main)] mt-1 font-medium">{report.root_cause_observed}</p>
                    </div>
                  </div>
                </GlassCard>
              );
            })}
          </div>
        )}

        {/* Tab 2: Reward Store Management */}
        {activeTab === 'rewards' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-lg font-bold text-[var(--text-main)]">Reward Catalog Governance</h2>
              <button
                type="button"
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 rounded-xl bg-[#5C3E94] px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-[#412B6B] active:scale-95 transition-all"
              >
                <Plus size={15} />
                <span>Add New Reward</span>
              </button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {rewards.map((reward) => (
                <GlassCard key={reward.id} className="p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="rounded-lg bg-[#5C3E94]/15 px-2.5 py-0.5 text-xs font-mono text-[#5C3E94] dark:text-purple-300 font-semibold border border-[#5C3E94]/30">
                        {reward.category}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleToggleActive(reward.id, reward.active)}
                        className="text-xs"
                      >
                        {reward.active ? (
                          <ToggleRight size={26} className="text-emerald-500" />
                        ) : (
                          <ToggleLeft size={26} className="text-[var(--text-muted)]" />
                        )}
                      </button>
                    </div>

                    <h3 className="text-base font-bold text-[var(--text-main)]">{reward.name}</h3>
                    <p className="text-xs text-[var(--text-muted)] mt-1">{reward.description}</p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs">
                    <span className="font-extrabold text-[#F25912] font-mono">{reward.cost} Credits</span>
                    <span className="text-[var(--text-muted)]">Stock: {reward.inventory}</span>
                  </div>
                </GlassCard>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Notifications / Audit Log */}
        {activeTab === 'notifications' && (
          <GlassCard className="p-6">
            <h2 className="text-lg font-bold text-[var(--text-main)] mb-4">Real-Time Operational Audit Trail</h2>
            <div className="space-y-3">
              {notifications.map((n) => (
                <div
                  key={n.id}
                  className="flex items-center justify-between rounded-xl bg-[var(--bg-surface)] p-3.5 text-xs border border-[var(--border-subtle)]"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#5C3E94]/20 text-[#5C3E94] dark:text-purple-300">
                      <Bell size={15} />
                    </div>
                    <div>
                      <h4 className="font-bold text-[var(--text-main)]">{n.title}</h4>
                      <p className="text-[var(--text-muted)]">{n.message}</p>
                    </div>
                  </div>
                  <span className="font-mono text-[11px] text-[var(--text-muted)]">{new Date(n.timestamp).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Approval Modal */}
        {selectedReport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-3xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-6 shadow-2xl">
              <h3 className="text-lg font-bold text-[var(--text-main)] mb-2">Authorize Resolution Report</h3>
              <p className="text-xs text-[var(--text-muted)] mb-4">
                Validate technician resolution on <strong className="text-[var(--text-main)]">{selectedReport.asset_id}</strong> ({selectedReport.incident_id}).
              </p>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Award Credits to Technician</label>
                  <input
                    type="number"
                    value={approvalCredits}
                    onChange={(e) => setApprovalCredits(Number(e.target.value))}
                    className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-main)] font-mono focus:border-[#F25912] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Admin Audit Notes</label>
                  <input
                    type="text"
                    value={adminNotes}
                    onChange={(e) => setAdminNotes(e.target.value)}
                    className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-main)] focus:border-[#F25912] focus:outline-none"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedReport(null)}
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-[var(--text-muted)] hover:bg-[var(--bg-primary)]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => handleApproveReport(selectedReport.incident_id)}
                  className="rounded-xl bg-[#F25912] px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-orange-600 active:scale-95 disabled:opacity-50"
                >
                  {isProcessing ? 'Authorizing...' : `Confirm & Transfer ${approvalCredits} Credits`}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add Reward Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
            <form onSubmit={handleCreateReward} className="w-full max-w-md rounded-3xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-6 shadow-2xl">
              <h3 className="text-lg font-bold text-[var(--text-main)] mb-4">Add New Reward Item</h3>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Item Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Starbucks Gift Card"
                    className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-main)] focus:border-[#5C3E94] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Description</label>
                  <input
                    type="text"
                    required
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="e.g. $25 coffee voucher"
                    className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-main)] focus:border-[#5C3E94] focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[var(--text-muted)] font-semibold mb-1">Credit Cost</label>
                    <input
                      type="number"
                      required
                      value={cost}
                      onChange={(e) => setCost(Number(e.target.value))}
                      className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-main)] font-mono focus:border-[#5C3E94] focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-[var(--text-muted)] font-semibold mb-1">Inventory</label>
                    <input
                      type="number"
                      required
                      value={inventory}
                      onChange={(e) => setInventory(Number(e.target.value))}
                      className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-main)] font-mono focus:border-[#5C3E94] focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-main)] focus:border-[#5C3E94] focus:outline-none"
                  >
                    <option value="Perks">Perks</option>
                    <option value="Tools">Tools</option>
                    <option value="Vouchers">Vouchers</option>
                    <option value="Gear">Gear</option>
                  </select>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-[var(--text-muted)] hover:bg-[var(--bg-primary)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-[#5C3E94] px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-[#412B6B] active:scale-95"
                >
                  Create Reward
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminConsole;
