import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMs(ms: number): string {
  if (ms < 1) return '<1 ms';
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export function formatDate(isoStr?: string | null): string {
  if (!isoStr) return 'N/A';
  try {
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoStr;
  }
}

export function getConfidenceBadgeProps(confidence: number) {
  if (confidence >= 0.9) {
    return {
      label: `Verified (${Math.round(confidence * 100)}%)`,
      variant: 'emerald' as const,
    };
  }
  if (confidence >= 0.55) {
    return {
      label: `Moderate (${Math.round(confidence * 100)}%)`,
      variant: 'amber' as const,
    };
  }
  return {
    label: `Low (${Math.round(confidence * 100)}%)`,
    variant: 'red' as const,
  };
}
