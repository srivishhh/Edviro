import React, { type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { BorderGlow } from './ui/BorderGlow';
import { useTheme } from '../app/ThemeProvider';

export type BentoVariant = 'hero' | 'translucent' | 'gradient' | 'alert' | 'default';

interface BentoTileProps {
  children: ReactNode;
  span?: string; // e.g. "col-span-1 md:col-span-2"
  className?: string;
  variant?: BentoVariant;
  onClick?: () => void;
}

export const BentoTile: React.FC<BentoTileProps> = ({
  children,
  span = 'col-span-1',
  className = '',
  variant = 'default',
  onClick,
}) => {
  const { theme } = useTheme();

  const getVariantBg = () => {
    switch (variant) {
      case 'hero':
        return 'var(--bg-card-hero)';
      case 'translucent':
        return 'var(--bg-card-translucent)';
      case 'gradient':
        return 'var(--bg-card-gradient)';
      case 'alert':
        return 'var(--bg-card-alert)';
      default:
        return 'var(--bg-card-default)';
    }
  };

  const getGlowConfig = () => {
    if (variant === 'alert') {
      return {
        glowColor: theme === 'dark' ? '15 95 60' : '15 95 45',
        colors: theme === 'dark'
          ? ['#f97316', '#ef4444', '#f59e0b']
          : ['#c2410c', '#b91c1c', '#ea580c'],
      };
    }
    // Dark mode: soft white/luminous crystalline edge glow
    // Light mode: dark blue + violet edge glow
    return {
      glowColor: theme === 'dark' ? '0 0 95' : '255 80 40',
      colors: theme === 'dark'
        ? ['#ffffff', '#e2e8f0', '#94a3b8']
        : ['#1e1b4b', '#3b0764', '#5C3E94'],
    };
  };

  const glowConfig = getGlowConfig();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 1, 0.5, 1] }}
      whileHover={onClick ? { scale: 1.008 } : undefined}
      whileTap={onClick ? { scale: 0.992 } : undefined}
      className={`relative ${span} ${onClick ? 'cursor-pointer' : ''}`}
      style={{ overflow: 'visible' }}
    >
      <BorderGlow
        glowColor={glowConfig.glowColor}
        colors={glowConfig.colors}
        backgroundColor={getVariantBg()}
        borderRadius={24}
        glowRadius={36}
        glowIntensity={theme === 'dark' ? 1.15 : 1.25}
        edgeSensitivity={25}
        coneSpread={28}
        fillOpacity={theme === 'dark' ? 0.3 : 0.45}
        onClick={onClick}
        className={`w-full h-full p-5 sm:p-6 text-[var(--text-main)] backdrop-blur-xl ${className}`}
      >
        {/* Top Specular Line Accent */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#5C3E94]/30 to-transparent" />

        {/* Bento Content */}
        <div className="relative z-10 w-full h-full flex flex-col justify-between">
          {children}
        </div>
      </BorderGlow>
    </motion.div>
  );
};
