import React from 'react';
import { Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Badge } from '../shared/Badge';
import { Card } from '../shared/Card';

interface SLACardProps {
  data: {
    target_minutes: number;
    elapsed_minutes: number;
    breached: boolean;
    minutes_to_breach?: number;
    contract_sources?: string[];
  };
  authoritySource?: string;
}

export const SLACard: React.FC<SLACardProps> = ({ data, authoritySource }) => {
  const isBreached = data.breached;
  const minutesLeft = data.minutes_to_breach ?? data.target_minutes - data.elapsed_minutes;
  const isApproaching = !isBreached && minutesLeft > 0 && minutesLeft <= 30;

  return (
    <Card className="border-l-4 border-l-brand-violet bg-dark-900/90 my-3">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              SLA Response Target Evaluation
            </h4>
            <span className="text-xs text-slate-400">
              Deterministic SLA calculation
            </span>
          </div>
        </div>

        {isBreached ? (
          <Badge variant="red">SLA Breached</Badge>
        ) : isApproaching ? (
          <Badge variant="amber">Breach Warning (&lt;30m)</Badge>
        ) : (
          <Badge variant="emerald">Within Target</Badge>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 p-3 bg-dark-950/60 rounded-lg border border-slate-800/80 mb-3 text-xs">
        <div>
          <span className="text-slate-500 block mb-0.5">Target Response</span>
          <span className="font-mono text-sm font-semibold text-slate-200">
            {data.target_minutes} mins
          </span>
        </div>

        <div>
          <span className="text-slate-500 block mb-0.5">Elapsed Time</span>
          <span className="font-mono text-sm font-semibold text-slate-300">
            {Math.round(data.elapsed_minutes)} mins
          </span>
        </div>

        <div>
          <span className="text-slate-500 block mb-0.5">Time Remaining</span>
          <span
            className={`font-mono text-sm font-semibold ${
              isBreached
                ? 'text-red-400'
                : isApproaching
                ? 'text-amber-400'
                : 'text-emerald-400'
            }`}
          >
            {isBreached
              ? `${Math.abs(Math.round(minutesLeft))}m overdue`
              : `${Math.round(minutesLeft)}m remaining`}
          </span>
        </div>
      </div>

      {authoritySource && (
        <div className="text-[11px] text-slate-400 flex items-center gap-1.5 pt-1">
          <span className="text-slate-500">Source:</span>
          <Badge variant="violet" size="sm">
            {authoritySource}
          </Badge>
        </div>
      )}
    </Card>
  );
};
