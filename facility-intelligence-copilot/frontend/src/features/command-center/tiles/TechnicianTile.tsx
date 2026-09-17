import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, ArrowRight, Wallet } from 'lucide-react';
import { BentoTile } from '../../../components/BentoTile';

interface TechProfile {
  name: string;
  role: string;
  credits: number;
  completed: number;
  streak: number;
  level: string;
}

export const TechnicianTile: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<TechProfile>({
    name: 'Alex Mercer',
    role: 'Senior Facility Technician',
    credits: 2480,
    completed: 24,
    streak: 7,
    level: 'Master Specialist',
  });

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/technicians/me')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setProfile(data))
      .catch(() => {});
  }, []);

  return (
    <BentoTile
      span="col-span-1"
      variant="hero"
      onClick={() => navigate('/profile')}
      className="flex flex-col justify-between"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Award size={16} className="text-[#5C3E94] dark:text-purple-300" />
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            TECHNICIAN WORKSPACE
          </span>
        </div>
        <span className="rounded-lg bg-[#F25912]/15 px-2 py-0.5 text-[10px] font-bold text-[#F25912] border border-[#F25912]/30">
          STREAK: {profile.streak}🔥
        </span>
      </div>

      <div className="my-3">
        <div className="flex items-baseline justify-between">
          <div>
            <p className="text-xs text-[var(--text-muted)]">{profile.name}</p>
            <p className="text-2xl font-extrabold text-[var(--text-main)] font-mono">{profile.credits.toLocaleString()}</p>
          </div>
          <span className="text-xs font-semibold text-[#5C3E94] dark:text-purple-300 uppercase tracking-wider">CREDITS</span>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2 rounded-2xl bg-[var(--bg-surface)] p-3 text-xs border border-[var(--border-subtle)]">
          <div>
            <span className="text-[var(--text-muted)]">Resolutions</span>
            <p className="font-semibold text-[var(--text-main)]">{profile.completed} Verified</p>
          </div>
          <div>
            <span className="text-[var(--text-muted)]">Rank Tier</span>
            <p className="font-semibold text-[#5C3E94] dark:text-purple-300">{profile.level}</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-2 text-xs text-[#5C3E94] dark:text-purple-300 font-semibold group">
        <div className="flex items-center gap-1.5">
          <Wallet size={13} />
          <span>Wallet, Ledger & Rewards</span>
        </div>
        <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
      </div>
    </BentoTile>
  );
};
