import React from 'react';
import { useTheme } from '../../app/ThemeProvider';

export const AceternityGradientBg: React.FC = () => {
  const { theme } = useTheme();

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* Top Left Deep Purple Glow */}
      <div
        className={`absolute -top-40 -left-40 h-[500px] w-[500px] rounded-full blur-[140px] transition-all duration-700 ${
          theme === 'dark'
            ? 'bg-[#5C3E94]/25 opacity-70'
            : 'bg-[#5C3E94]/5 opacity-30'
        }`}
      />

      {/* Top Right Orange Energy Accent Glow */}
      <div
        className={`absolute top-0 right-0 h-[450px] w-[450px] rounded-full blur-[160px] transition-all duration-700 ${
          theme === 'dark'
            ? 'bg-[#F25912]/15 opacity-60'
            : 'bg-[#F25912]/5 opacity-20'
        }`}
      />

      {/* Center Ambient Mesh */}
      <div
        className={`absolute top-1/3 left-1/2 -translate-x-1/2 h-[600px] w-[800px] rounded-full blur-[180px] transition-all duration-700 ${
          theme === 'dark'
            ? 'bg-[#412B6B]/20 opacity-80'
            : 'bg-white opacity-40'
        }`}
      />

      {/* Bottom Purple Ambient Pool */}
      <div
        className={`absolute -bottom-40 -right-20 h-[550px] w-[550px] rounded-full blur-[150px] transition-all duration-700 ${
          theme === 'dark'
            ? 'bg-[#5C3E94]/20 opacity-60'
            : 'bg-[#5C3E94]/5 opacity-20'
        }`}
      />

      {/* Subtle Fine Grid Texture */}
      <div
        className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]"
        style={{
          backgroundImage: `radial-gradient(rgba(242, 89, 18, 0.6) 1px, transparent 1px)`,
          backgroundSize: '32px 32px',
        }}
      />
    </div>
  );
};
