import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Wrench, ArrowRight, Lock, Sparkles, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth, type UserRole } from '../../app/AuthContext';
import { useTheme } from '../../app/ThemeProvider';
import { AceternityGradientBg } from '../../components/ui/AceternityGradientBg';
import { ThemeToggle } from '../../components/ThemeToggle';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { theme } = useTheme();
  const [selectedRole, setSelectedRole] = useState<UserRole>('technician');
  const [passcode, setPasscode] = useState('123456');
  const [loading, setLoading] = useState(false);

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      login(selectedRole, selectedRole === 'admin' ? 'Operations Admin' : 'Alex Mercer');
      setLoading(false);
      if (selectedRole === 'admin') {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
    }, 400);
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center p-4 selection:bg-[#F25912] selection:text-white overflow-hidden">
      <AceternityGradientBg />

      {/* Top Header Floating Controls */}
      <div className="absolute top-6 right-6 z-20 flex items-center gap-3">
        <ThemeToggle />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-lg rounded-3xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-8 sm:p-10 backdrop-blur-2xl shadow-[var(--card-shadow)]"
      >
        {/* Brand Header & Emblem */}
        <div className="text-center">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 10 }}
            transition={{ type: 'spring', stiffness: 300, damping: 15 }}
            className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-3 shadow-lg"
          >
            <img
              src="/logo.png"
              alt="GSENSE Logo"
              className={`h-full w-full object-contain ${
                theme === 'dark' ? 'invert brightness-125' : 'brightness-90'
              }`}
            />
          </motion.div>

          <div className="mt-4 flex items-center justify-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-[var(--text-main)]">GSENSE</h1>
            <span className="rounded-md bg-[#F25912]/15 px-2 py-0.5 text-[11px] font-bold text-[#F25912] border border-[#F25912]/30">
              V2.0
            </span>
          </div>

          <p className="mt-1 text-xs text-[var(--text-muted)] font-medium">
            Autonomous Facility Intelligence & Operations Workspace
          </p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleLoginSubmit} className="mt-8 space-y-6">
          {/* Role Selection */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">
              Select Operating Domain
            </label>

            <div className="grid grid-cols-2 gap-3">
              {/* Technician Role Card */}
              <button
                type="button"
                onClick={() => setSelectedRole('technician')}
                className={`relative flex flex-col items-start gap-2 rounded-2xl border p-4 text-left transition-all ${
                  selectedRole === 'technician'
                    ? 'border-[#5C3E94] bg-[#5C3E94]/15 shadow-md shadow-purple-950/10 ring-1 ring-[#5C3E94]'
                    : 'border-[var(--border-subtle)] bg-[var(--bg-surface)]/60 hover:border-[#5C3E94]/50'
                }`}
              >
                {selectedRole === 'technician' && (
                  <span className="absolute top-3 right-3 text-[#5C3E94] dark:text-purple-300">
                    <CheckCircle2 size={16} />
                  </span>
                )}
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#5C3E94] text-white">
                  <Wrench size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[var(--text-main)]">Technician</h3>
                  <p className="text-[11px] text-[var(--text-muted)] mt-0.5">Command Center & Rewards</p>
                </div>
              </button>

              {/* Administrator Role Card */}
              <button
                type="button"
                onClick={() => setSelectedRole('admin')}
                className={`relative flex flex-col items-start gap-2 rounded-2xl border p-4 text-left transition-all ${
                  selectedRole === 'admin'
                    ? 'border-[#F25912] bg-[#F25912]/15 shadow-md shadow-orange-950/10 ring-1 ring-[#F25912]'
                    : 'border-[var(--border-subtle)] bg-[var(--bg-surface)]/60 hover:border-[#F25912]/50'
                }`}
              >
                {selectedRole === 'admin' && (
                  <span className="absolute top-3 right-3 text-[#F25912]">
                    <CheckCircle2 size={16} />
                  </span>
                )}
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#F25912] text-white">
                  <Shield size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[var(--text-main)]">Administrator</h3>
                  <p className="text-[11px] text-[var(--text-muted)] mt-0.5">Governance & Approvals</p>
                </div>
              </button>
            </div>
          </div>

          {/* Passcode Input */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
              Access Token / Security PIN
            </label>
            <div className="relative">
              <input
                type="password"
                required
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                placeholder="Enter 6-digit access code"
                className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-4 py-3 pl-10 text-xs font-mono text-[var(--text-main)] placeholder-[var(--text-muted)] focus:border-[#5C3E94] focus:outline-none focus:ring-1 focus:ring-[#5C3E94]"
              />
              <Lock size={15} className="absolute left-3.5 top-3.5 text-[var(--text-muted)]" />
            </div>
            <p className="mt-1.5 text-[11px] text-[var(--text-muted)]">
              Demo code: <span className="font-mono text-[#F25912]">123456</span>
            </p>
          </div>

          {/* Submit Button */}
          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className={`flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 px-5 font-bold text-white shadow-xl transition-all ${
              selectedRole === 'admin'
                ? 'bg-[#F25912] hover:bg-orange-600 shadow-orange-950/30'
                : 'bg-[#5C3E94] hover:bg-[#412B6B] shadow-purple-950/30'
            }`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="animate-spin" />
                <span>Authenticating Node...</span>
              </div>
            ) : (
              <>
                <span>Enter as {selectedRole === 'admin' ? 'Administrator' : 'Technician'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </motion.button>
        </form>

        {/* Footer Disclaimer */}
        <div className="mt-8 pt-4 border-t border-[var(--border-subtle)] text-center text-[11px] text-[var(--text-muted)] font-medium">
          Protected by GSENSE Multi-Agent Security Protocol • ISO 27001 Facility Certified
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
