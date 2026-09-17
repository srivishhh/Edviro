import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, Wallet, ShoppingBag, History } from 'lucide-react';
import { Header } from '../../components/Header';
import { GlassCard } from '../../components/GlassCard';

interface CreditInfo {
  available_credits: number;
  total_earned: number;
  total_redeemed: number;
}

interface Transaction {
  transaction_id: string;
  amount: number;
  reason: string;
  timestamp: string;
  status: string;
}

const TechnicianProfile: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>({ name: 'Alex Mercer', role: 'Senior Facility Technician', streak: 7, level: 'Master Specialist' });
  const [creditInfo, setCreditInfo] = useState<CreditInfo>({ available_credits: 2480, total_earned: 2680, total_redeemed: 200 });
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/technicians/me')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setProfile(data))
      .catch(() => {});

    fetch('http://127.0.0.1:8000/api/v1/technicians/me/credits')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setCreditInfo(data))
      .catch(() => {});

    fetch('http://127.0.0.1:8000/api/v1/technicians/me/transactions')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setTransactions(data))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] transition-colors">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Profile Banner */}
        <GlassCard className="p-6 mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#5C3E94] text-xl font-bold text-white shadow-md">
              AM
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-[var(--text-main)]">{profile.name}</h1>
                <span className="rounded-lg bg-[#5C3E94]/15 px-2.5 py-0.5 text-xs font-semibold text-[#5C3E94] dark:text-purple-300 border border-[#5C3E94]/30">
                  {profile.level}
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)]">{profile.role} • Active Streak: {profile.streak} Days 🔥</p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => navigate('/rewards')}
            className="flex items-center gap-2 rounded-xl bg-[#F25912] px-5 py-2.5 font-bold text-white shadow-lg shadow-orange-950/20 transition-all hover:bg-orange-600 active:scale-95"
          >
            <ShoppingBag size={18} />
            <span>Open Reward Store</span>
          </button>
        </GlassCard>

        {/* Wallet Overview Cards */}
        <div className="grid gap-4 md:grid-cols-3 mb-6">
          <GlassCard className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold uppercase text-[var(--text-muted)]">AVAILABLE CREDITS</span>
              <p className="text-3xl font-extrabold text-[#F25912] mt-1 font-mono">{creditInfo.available_credits.toLocaleString()}</p>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">Ready for redemption</p>
            </div>
            <Wallet size={32} className="text-[#F25912]/30" />
          </GlassCard>

          <GlassCard className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold uppercase text-[var(--text-muted)]">LIFETIME EARNED</span>
              <p className="text-3xl font-extrabold text-emerald-500 mt-1 font-mono">{creditInfo.total_earned.toLocaleString()}</p>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">Verified resolutions</p>
            </div>
            <Award size={32} className="text-emerald-500/30" />
          </GlassCard>

          <GlassCard className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold uppercase text-[var(--text-muted)]">REDEEMED</span>
              <p className="text-3xl font-extrabold text-[var(--text-main)] mt-1 font-mono">{creditInfo.total_redeemed.toLocaleString()}</p>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">Claimed gift perks</p>
            </div>
            <ShoppingBag size={32} className="text-[#5C3E94]/30" />
          </GlassCard>
        </div>

        {/* Immutable Transaction Ledger */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <History size={18} className="text-[#5C3E94] dark:text-purple-300" />
            <h2 className="text-base font-bold text-[var(--text-main)]">Immutable Credit Ledger</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[var(--border-subtle)] text-[var(--text-muted)]">
                <tr>
                  <th className="pb-3 font-semibold">Transaction ID</th>
                  <th className="pb-3 font-semibold">Reason / Description</th>
                  <th className="pb-3 font-semibold">Timestamp</th>
                  <th className="pb-3 font-semibold">Amount</th>
                  <th className="pb-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-main)]">
                {transactions.map((tx) => (
                  <tr key={tx.transaction_id} className="hover:bg-[var(--bg-card-hover)]">
                    <td className="py-3 font-mono text-[var(--text-muted)]">{tx.transaction_id}</td>
                    <td className="py-3 font-medium">{tx.reason}</td>
                    <td className="py-3 text-[var(--text-muted)]">{new Date(tx.timestamp).toLocaleString()}</td>
                    <td className="py-3 font-bold">
                      <span className={tx.amount >= 0 ? 'text-emerald-500' : 'text-[#F25912]'}>
                        {tx.amount >= 0 ? `+${tx.amount}` : tx.amount} CREDITS
                      </span>
                    </td>
                    <td className="py-3">
                      <span className="rounded-lg bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold text-emerald-500 border border-emerald-500/30">
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </main>
    </div>
  );
};

export default TechnicianProfile;
