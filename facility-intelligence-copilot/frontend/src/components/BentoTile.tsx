import React, { useRef, useState, type ReactNode } from 'react';
import { motion } from 'framer-motion';

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
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePos, setMousePos] = useState({ x: -200, y: -200 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'alert':
        return 'hover:border-[#F25912]/80 dark:hover:border-[#F25912]';
      case 'hero':
        return 'hover:border-purple-400 dark:hover:border-[#5C3E94]';
      default:
        return 'hover:border-purple-400 dark:hover:border-[#5C3E94]';
    }
  };

  const getVariantInlineStyle = () => {
    switch (variant) {
      case 'hero':
        return { background: 'var(--bg-card-hero)', borderColor: 'var(--border-card)' };
      case 'translucent':
        return { background: 'var(--bg-card-translucent)', borderColor: 'var(--border-card)' };
      case 'gradient':
        return { background: 'var(--bg-card-gradient)', borderColor: 'var(--border-card)' };
      case 'alert':
        return { background: 'var(--bg-card-alert)', borderColor: 'var(--border-card-alert)' };
      default:
        return { background: 'var(--bg-card-default)', borderColor: 'var(--border-card)' };
    }
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 1, 0.5, 1] }}
      whileHover={onClick ? { scale: 1.008 } : undefined}
      whileTap={onClick ? { scale: 0.992 } : undefined}
      style={{
        ...getVariantInlineStyle(),
        boxShadow: 'var(--card-shadow)',
      }}
      className={`
        group relative overflow-hidden rounded-3xl
        border p-5 sm:p-6 text-[var(--text-main)]
        backdrop-blur-xl transition-all duration-300
        ${getVariantStyles()}
        ${onClick ? 'cursor-pointer' : ''}
        ${span} ${className}
      `}
    >
      {/* Dynamic Specular Glare (Glasscn UI style) */}
      <div
        className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: isHovered
            ? `radial-gradient(400px circle at ${mousePos.x}px ${mousePos.y}px, var(--glass-glare), transparent 70%)`
            : undefined,
        }}
      />

      {/* Top Specular Line Accent */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#5C3E94]/30 to-transparent" />

      {/* Card Content */}
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
};
