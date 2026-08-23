import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  hoverEffect = false,
}) => {
  return (
    <div
      className={cn(
        'glass-panel rounded-xl p-5 border border-slate-800/80 shadow-glass-sm',
        hoverEffect && 'glass-panel-hover cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  );
};
