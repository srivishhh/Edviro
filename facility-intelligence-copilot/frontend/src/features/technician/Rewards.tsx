import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ShoppingBag } from 'lucide-react';
import { Header } from '../../components/Header';
import { GlassCard } from '../../components/GlassCard';

interface Reward {
  id: string;
  name: string;
  description: string;
  cost: number;
  inventory: number;
  active: boolean;
  category: string;
}

export const Rewards: React.FC = () => {
  const navigate = useNavigate();
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [availableCredits, setAvailableCredits] = useState<number>(2480);
  const [redeemingId, setRedeemingId] = useState<string | null>(null);

  const fetchCatalog = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/rewards');
      if (res.ok) {
        const data = await res.json();
        setRewards(data);
      }
      const creditRes = await fetch('http://127.0.0.1:8000/api/v1/technicians/me/credits');
      if (creditRes.ok) {
        const creditData = await creditRes.json();
        setAvailableCredits(creditData.available_credits);
      }
    } catch {
      // Backend fallback catalog
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  const handleRedeem = async (reward: Reward) => {
    if (availableCredits < reward.cost) {
      alert('Insufficient credits balance.');
      return;
    }

    setRedeemingId(reward.id);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/redemptions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reward_id: reward.id }),
      });

      if (res.ok) {
        const result = await res.json();
        alert(result.message);
        setAvailableCredits(result.new_balance);
        fetchCatalog();
      } else {
        const err = await res.json();
        alert(`Redemption Failed: ${err.detail}`);
      }
    } catch {
      alert('Error connecting to backend server.');
    } finally {
      setRedeemingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] transition-colors">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={() => navigate('/profile')}
          className="mb-4 flex items-center gap-2 text-xs font-semibold text-[#5C3E94] dark:text-purple-300 hover:underline"
        >
          <ArrowLeft size={14} />
          <span>Back to Profile Wallet</span>
        </button>

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-[var(--text-main)] tracking-tight">Technician Reward Store</h1>
            <p className="text-sm text-[var(--text-muted)]">Redeem earned performance credits for verified perks and tools.</p>
          </div>

          <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-4 py-2.5 text-right shadow-sm">
            <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">AVAILABLE BALANCE</span>
            <p className="text-xl font-extrabold text-[#F25912] font-mono">{availableCredits.toLocaleString()} Credits</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {rewards.map((item) => (
            <GlassCard key={item.id} className="p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="rounded-lg bg-[#5C3E94]/15 px-2.5 py-0.5 text-[11px] font-mono text-[#5C3E94] dark:text-purple-300 font-semibold border border-[#5C3E94]/30">
                    {item.category}
                  </span>
                  <span className="text-xs text-[var(--text-muted)]">Stock: {item.inventory}</span>
                </div>

                <h3 className="text-base font-bold text-[var(--text-main)]">{item.name}</h3>
                <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">{item.description}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
                <span className="text-base font-extrabold text-[#F25912] font-mono">{item.cost} Credits</span>

                <button
                  type="button"
                  onClick={() => handleRedeem(item)}
                  disabled={redeemingId === item.id || availableCredits < item.cost || item.inventory <= 0}
                  className="flex items-center gap-1.5 rounded-xl bg-[#5C3E94] px-3.5 py-2 text-xs font-bold text-white shadow-sm transition-all hover:bg-[#412B6B] active:scale-95 disabled:opacity-40"
                >
                  <ShoppingBag size={14} />
                  <span>{redeemingId === item.id ? 'Claiming...' : 'Redeem Perk'}</span>
                </button>
              </div>
            </GlassCard>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Rewards;
