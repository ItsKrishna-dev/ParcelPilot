import React from 'react';
import { AlertTriangle, Clock, ShieldAlert } from 'lucide-react';
import { SLARiskEntry } from '../../types/api';
import { Badge } from '../shared/Badge';
import { Card } from '../shared/Card';

interface SLARiskTableProps {
  entries: SLARiskEntry[];
}

export const SLARiskTable: React.FC<SLARiskTableProps> = ({ entries }) => {
  if (!entries || entries.length === 0) {
    return (
      <Card className="text-center p-6 text-slate-400 text-xs">
        No active tickets currently approaching or breaching SLA limits.
      </Card>
    );
  }

  return (
    <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden shadow-glass-md">
      <div className="p-4 bg-dark-900 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Clock className="w-4 h-4 text-amber-400" />
          SLA Breach Predictor &amp; At-Risk Tickets ({entries.length})
        </h3>
        <span className="text-[11px] font-mono text-slate-400">Real-time DB Monitor</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-dark-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
              <th className="py-3 px-4">Ticket ID</th>
              <th className="py-3 px-4">Account ID</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">Target (Mins)</th>
              <th className="py-3 px-4">Elapsed</th>
              <th className="py-3 px-4">Time to Breach</th>
              <th className="py-3 px-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
            {entries.map((item) => (
              <tr key={item.ticket_id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-100">{item.ticket_id}</td>
                <td className="py-3 px-4 text-slate-400">{item.account_id}</td>
                <td className="py-3 px-4 font-sans">
                  <Badge variant={item.severity === 'P1' ? 'red' : 'amber'} size="sm">
                    {item.severity}
                  </Badge>
                </td>
                <td className="py-3 px-4 text-slate-300">{item.target_minutes} m</td>
                <td className="py-3 px-4 text-slate-400">{Math.round(item.elapsed_minutes)} m</td>
                <td className="py-3 px-4 font-bold">
                  {item.breached ? (
                    <span className="text-red-400 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Breached ({Math.abs(Math.round(item.minutes_to_breach))}m ago)
                    </span>
                  ) : (
                    <span className="text-amber-400">
                      {Math.round(item.minutes_to_breach)}m remaining
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 font-sans">
                  {item.breached ? (
                    <Badge variant="red">BREACHED</Badge>
                  ) : (
                    <Badge variant="amber">AT RISK</Badge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
