import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Shield, User, LogOut, FileEdit, Brain } from 'lucide-react';
import { motion } from 'framer-motion';
import { ThemeToggle } from './ThemeToggle';
import { QuickReportModal } from './QuickReportModal';
import { useRealtime } from '../hooks/useRealtime';
import { useTheme } from '../app/ThemeProvider';
import { useAuth } from '../app/AuthContext';

interface HeaderProps {
  onOpenRag?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenRag }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { facilityStatus } = useRealtime();
  const { theme } = useTheme();
  const { user, logout } = useAuth();
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isTechnician = user?.role === 'technician' || !user;
  const isAdmin = user?.role === 'admin';

  const technicianNavItems = [
    { label: 'Command Center', path: '/dashboard' },
    { label: 'Assets', path: '/assets' },
    { label: 'Investigations', path: '/investigations' },
    { label: 'Rewards Store', path: '/rewards' },
  ];

  const adminNavItems = [
    { label: 'Admin Governance', path: '/admin' },
    { label: 'Live Telemetry', path: '/dashboard' },
  ];

  const navItems = isAdmin ? adminNavItems : technicianNavItems;

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-[var(--border-subtle)] bg-[var(--bg-primary)]/80 backdrop-blur-2xl transition-colors duration-200">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          {/* Brand Left */}
          <div className="flex items-center gap-6">
            <Link to={isAdmin ? '/admin' : '/dashboard'} className="group flex items-center gap-3">
              <motion.div
                whileHover={{ rotate: 90 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-1.5 shadow-sm"
              >
                <img
                  src="/logo.png"
                  alt="GSENSE Logo"
                  className={`h-full w-full object-contain ${
                    theme === 'dark' ? 'invert brightness-125' : 'brightness-90'
                  }`}
                />
              </motion.div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="text-base font-black tracking-tight text-[var(--text-main)]">GSENSE</span>
                  <span
                    className={`rounded-md px-1.5 py-0.2 text-[10px] font-bold ${
                      isAdmin
                        ? 'bg-[#F25912]/15 text-[#F25912] border border-[#F25912]/30'
                        : 'bg-[#5C3E94]/15 text-[#5C3E94] dark:text-purple-300 border border-[#5C3E94]/30'
                    }`}
                  >
                    {isAdmin ? 'ADMIN' : 'COPILOT'}
                  </span>
                </div>
                <span className="text-[11px] text-[var(--text-muted)] font-medium">Facility Intelligence</span>
              </div>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const active = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`rounded-xl px-3.5 py-1.5 text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
                      active
                        ? isAdmin
                          ? 'bg-[#F25912] text-white shadow-sm'
                          : 'bg-[#5C3E94] text-white shadow-sm'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface)]'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Status & Actions Right */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Live Status Pill */}
            <div className="flex items-center gap-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-1.5 text-xs">
              <span className="relative flex h-2 w-2">
                <span
                  className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                    facilityStatus === 'CRITICAL'
                      ? 'bg-red-400'
                      : facilityStatus === 'DEGRADED'
                      ? 'bg-amber-400'
                      : 'bg-emerald-400'
                  }`}
                />
                <span
                  className={`relative inline-flex h-2 w-2 rounded-full ${
                    facilityStatus === 'CRITICAL'
                      ? 'bg-red-500'
                      : facilityStatus === 'DEGRADED'
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                  }`}
                />
              </span>
              <span className="font-mono text-[11px] font-medium tracking-tight text-[var(--text-main)]">
                LIVE • {facilityStatus}
              </span>
            </div>

            {/* Quick Report Submission Button (Near Theme Toggle) */}
            <button
              type="button"
              onClick={() => setIsReportModalOpen(true)}
              className="flex items-center gap-1.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-[var(--text-main)] transition-all hover:border-[#5C3E94] hover:bg-[#5C3E94]/10 active:scale-95 cursor-pointer shadow-xs"
              title="Write Report / Observation for Admin"
            >
              <FileEdit size={14} className="text-[#5C3E94] dark:text-purple-300" />
              <span className="hidden sm:inline">Write Report</span>
            </button>

            <ThemeToggle />

            {/* Circular Facility Memory RAG Modal Button */}
            {onOpenRag && (
              <button
                type="button"
                onClick={onOpenRag}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-purple-500/40 bg-purple-500/15 text-purple-300 transition-all hover:bg-purple-500/30 hover:scale-105 active:scale-95 cursor-pointer shadow-sm shadow-purple-500/20"
                title="Open Facility Memory Modal"
              >
                <Brain size={16} />
              </button>
            )}

            {/* Profile / Role Identity Link */}
            {isTechnician ? (
              <Link
                to="/profile"
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] transition-all hover:border-[#5C3E94] hover:text-[#5C3E94] active:scale-95 cursor-pointer"
                title="Technician Wallet & Profile"
              >
                <User size={16} />
              </Link>
            ) : (
              <Link
                to="/admin"
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] transition-all hover:border-[#F25912] hover:text-[#F25912] active:scale-95 cursor-pointer"
                title="Admin Console"
              >
                <Shield size={16} />
              </Link>
            )}

            {/* Explicit Logout Button */}
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-2.5 py-1.5 text-xs font-semibold text-[var(--text-muted)] transition-all hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-400 active:scale-95 cursor-pointer"
              title="Log out from current domain"
            >
              <LogOut size={14} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Quick Report Modal */}
      <QuickReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
      />
    </>
  );
};
