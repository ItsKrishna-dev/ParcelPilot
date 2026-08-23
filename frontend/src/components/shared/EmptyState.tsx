import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'glass-panel rounded-xl p-10 text-center flex flex-col items-center justify-center border border-slate-800',
        className
      )}
    >
      <div className="p-3 bg-dark-800/80 rounded-xl text-slate-400 border border-slate-700/60 mb-4 shadow-inner">
        <Icon className="w-8 h-8 text-brand-blue" />
      </div>
      <h3 className="text-base font-semibold text-slate-200 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm mb-5 leading-relaxed">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
};
