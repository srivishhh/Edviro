import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, ArrowRight } from 'lucide-react';
import { useTheme } from '../../app/ThemeProvider';

export const AdminLogin: React.FC = () => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [passcode, setPasscode] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('gsense-role', 'admin');
    navigate('/admin');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-primary)] px-4 text-[var(--text-main)] transition-colors">
      <div className="w-full max-w-md rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-8 shadow-2xl">
        <div className="text-center mb-6">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-2.5 shadow-md">
            <img
              src="/logo.png"
              alt="GSENSE Logo"
              className={`h-full w-full object-contain ${
                theme === 'dark' ? 'invert brightness-125' : 'brightness-90'
              }`}
            />
          </div>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-[var(--text-main)]">Admin Console Access</h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">Management authentication & governance boundary</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-[var(--text-main)] font-semibold mb-1">Admin Security PIN</label>
            <input
              type="password"
              required
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              placeholder="Enter admin passcode (e.g. 123456)"
              className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-3.5 py-2.5 text-[var(--text-main)] focus:border-[#5C3E94] focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#5C3E94] px-4 py-3 font-bold text-white shadow-lg shadow-purple-950/20 transition-all hover:bg-[#412B6B] active:scale-95"
          >
            <Shield size={16} />
            <span>Authenticate Admin</span>
            <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default AdminLogin;
