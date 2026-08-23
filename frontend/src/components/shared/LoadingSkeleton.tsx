import React from 'react';
import { cn } from '../../lib/utils';

interface SkeletonProps {
  className?: string;
}

export const LoadingSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div
      className={cn(
        'animate-pulse bg-slate-800/60 rounded-md border border-slate-700/30',
        className
      )}
    />
  );
};
