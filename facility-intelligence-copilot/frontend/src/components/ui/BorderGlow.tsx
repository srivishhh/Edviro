import React, { useRef, useCallback, useEffect, type ReactNode, type CSSProperties } from 'react';
import './BorderGlow.css';
import { useTheme } from '../../app/ThemeProvider';

function parseHSL(hslStr: string) {
  const match = hslStr.match(/([\d.]+)\s*([\d.]+)%?\s*([\d.]+)%?/);
  if (!match) return { h: 40, s: 80, l: 80 };
  return { h: parseFloat(match[1]), s: parseFloat(match[2]), l: parseFloat(match[3]) };
}

function buildGlowVars(glowColor: string, intensity: number) {
  const { h, s, l } = parseHSL(glowColor);
  const base = `${h}deg ${s}% ${l}%`;
  const opacities = [100, 60, 50, 40, 30, 20, 10];
  const keys = ['', '-60', '-50', '-40', '-30', '-20', '-10'];
  const vars: Record<string, string> = {};
  for (let i = 0; i < opacities.length; i++) {
    vars[`--glow-color${keys[i]}`] = `hsl(${base} / ${Math.min(opacities[i] * intensity, 100)}%)`;
  }
  return vars;
}

const GRADIENT_POSITIONS = ['80% 55%', '69% 34%', '8% 6%', '41% 38%', '86% 85%', '82% 18%', '51% 4%'];
const GRADIENT_KEYS = ['--gradient-one', '--gradient-two', '--gradient-three', '--gradient-four', '--gradient-five', '--gradient-six', '--gradient-seven'];
const COLOR_MAP = [0, 1, 2, 0, 1, 2, 1];

function buildGradientVars(colors: string[]) {
  const vars: Record<string, string> = {};
  for (let i = 0; i < 7; i++) {
    const c = colors[Math.min(COLOR_MAP[i], colors.length - 1)];
    vars[GRADIENT_KEYS[i]] = `radial-gradient(at ${GRADIENT_POSITIONS[i]}, ${c} 0px, transparent 50%)`;
  }
  vars['--gradient-base'] = `linear-gradient(${colors[0]} 0 100%)`;
  return vars;
}

function isLightColor(color: string) {
  if (color.startsWith('var(')) return false;
  const value = color.trim().replace('#', '');
  if (!/^[\da-f]{3}([\da-f]{3})?$/i.test(value)) return false;
  const hex = value.length === 3 ? value.split('').map(char => char + char).join('') : value;
  const red = parseInt(hex.slice(0, 2), 16);
  const green = parseInt(hex.slice(2, 4), 16);
  const blue = parseInt(hex.slice(4, 6), 16);
  return red * 0.2126 + green * 0.7152 + blue * 0.0722 > 180;
}

export interface BorderGlowProps {
  children: ReactNode;
  className?: string;
  edgeSensitivity?: number;
  glowColor?: string;
  backgroundColor?: string;
  borderRadius?: number;
  glowRadius?: number;
  glowIntensity?: number;
  coneSpread?: number;
  animated?: boolean;
  colors?: string[];
  fillOpacity?: number;
  onClick?: () => void;
  style?: CSSProperties;
}

export const BorderGlow: React.FC<BorderGlowProps> = ({
  children,
  className = '',
  edgeSensitivity = 25,
  glowColor,
  backgroundColor = 'var(--bg-card-default)',
  borderRadius = 24,
  glowRadius = 32,
  glowIntensity = 1.0,
  coneSpread = 25,
  colors,
  fillOpacity = 0.3,
  onClick,
  style,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const rectRef = useRef<{ left: number; top: number; width: number; height: number } | null>(null);
  const rafRef = useRef<number | null>(null);
  const latestPos = useRef<{ x: number; y: number } | null>(null);
  const { theme } = useTheme();

  // Adaptive glow and gradient colors according to Theme if not explicitly passed
  const effectiveGlowColor = glowColor || (theme === 'dark' ? '0 0 95' : '255 80 40');
  const effectiveColors = colors || (theme === 'dark'
    ? ['#ffffff', '#e2e8f0', '#94a3b8']
    : ['#1e1b4b', '#3b0764', '#5C3E94']);

  const updateGlow = useCallback(() => {
    if (!cardRef.current || !latestPos.current || !rectRef.current) return;
    const card = cardRef.current;
    const rect = rectRef.current;
    const x = latestPos.current.x - rect.left;
    const y = latestPos.current.y - rect.top;

    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const dx = x - cx;
    const dy = y - cy;

    let kx = Infinity;
    let ky = Infinity;
    if (dx !== 0) kx = cx / Math.abs(dx);
    if (dy !== 0) ky = cy / Math.abs(dy);
    const edge = Math.min(Math.max(1 / Math.min(kx, ky), 0), 1);

    let degrees = 0;
    if (dx !== 0 || dy !== 0) {
      degrees = Math.atan2(dy, dx) * (180 / Math.PI) + 90;
      if (degrees < 0) degrees += 360;
    }

    card.style.setProperty('--edge-proximity', (edge * 100).toFixed(1));
    card.style.setProperty('--cursor-angle', `${degrees.toFixed(1)}deg`);
    rafRef.current = null;
  }, []);

  const handlePointerEnter = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (cardRef.current) {
      rectRef.current = cardRef.current.getBoundingClientRect();
    }
    latestPos.current = { x: e.clientX, y: e.clientY };
    if (!rafRef.current) {
      rafRef.current = requestAnimationFrame(updateGlow);
    }
  }, [updateGlow]);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    latestPos.current = { x: e.clientX, y: e.clientY };
    if (!rafRef.current) {
      rafRef.current = requestAnimationFrame(updateGlow);
    }
  }, [updateGlow]);

  const handlePointerLeave = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    latestPos.current = null;
    rectRef.current = null;
    if (cardRef.current) {
      cardRef.current.style.setProperty('--edge-proximity', '0');
    }
  }, []);

  useEffect(() => {
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, []);

  const glowVars = buildGlowVars(effectiveGlowColor, glowIntensity);
  const lightSurface = theme === 'light' || isLightColor(backgroundColor);

  return (
    <div
      ref={cardRef}
      onPointerEnter={handlePointerEnter}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      onClick={onClick}
      className={`border-glow-card ${lightSurface ? 'border-glow-card--light' : ''} ${className}`}
      style={{
        '--card-bg': backgroundColor,
        '--edge-sensitivity': edgeSensitivity,
        '--border-radius': `${borderRadius}px`,
        '--glow-padding': `${glowRadius}px`,
        '--cone-spread': coneSpread,
        '--fill-opacity': fillOpacity,
        ...glowVars,
        ...buildGradientVars(effectiveColors),
        ...style,
      } as React.CSSProperties}
    >
      <span className="edge-light" />
      <div className="border-glow-inner">
        {children}
      </div>
    </div>
  );
};

export default BorderGlow;
