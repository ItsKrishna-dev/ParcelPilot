import React from 'react';
import { cn } from '../../lib/utils';

export type BadgeVariant =
  | 'emerald'
  | 'amber'
  | 'red'
  | 'blue'
  | 'cyan'
  | 'violet'
  | 'slate';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  size?: 'sm' | 'md';
}

const variantStyles: Record<BadgeVariant, string> = {
  emerald: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  amber: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  red: 'bg-red-500/15 text-red-400 border-red-500/30',
  blue: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  cyan: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  violet: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  slate: 'bg-slate-500/15 text-slate-300 border-slate-500/30',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'slate',
  className,
  size = 'sm',
}) => {
  return (
    <span
      className={cn(
        'inline-flex items-center font-medium border rounded-full backdrop-blur-sm tracking-wide',
        size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
};
