import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../app/ThemeProvider';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`
        relative flex h-9 w-9 items-center justify-center rounded-xl
        border transition-all duration-300 active:scale-95
        ${
          theme === 'dark'
            ? 'border-purple-500/30 bg-[#2a1f40]/80 text-amber-300 hover:border-purple-400/50 hover:bg-[#382855] hover:text-amber-200 shadow-inner'
            : 'border-purple-200 bg-white/90 text-purple-900 hover:border-purple-400 hover:bg-purple-50 hover:text-purple-950 shadow-sm'
        }
      `}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      <span className="sr-only">Toggle theme</span>
      {theme === 'dark' ? (
        <Sun size={17} className="transition-transform duration-300 rotate-0 hover:rotate-45 text-amber-300" />
      ) : (
        <Moon size={17} className="transition-transform duration-300 -rotate-12 hover:rotate-0 text-purple-900" />
      )}
    </button>
  );
};
