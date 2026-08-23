import React from 'react';
import { Layers, AlertCircle, Wrench, Users } from 'lucide-react';
import { CorrelationSignal, AnomalySignal } from '../../types/api';
import { Card } from '../shared/Card';
import { Badge } from '../shared/Badge';

interface IssueClustersCardProps {
  correlations: CorrelationSignal[];
  anomalies: AnomalySignal[];
}

export const IssueClustersCard: React.FC<IssueClustersCardProps> = ({
  correlations,
  anomalies,
}) => {
  return (
    <div className="space-y-4">
      {/* Cross-Account Correlation Signals */}
      <div>
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-3">
          <Layers className="w-4 h-4 text-brand-cyan" />
          Cross-Account Issue Clusters &amp; Correlator
        </h3>

        {correlations.length === 0 ? (
          <Card className="text-center p-4 text-slate-400 text-xs">
            No cross-account issue clusters detected in the current window.
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {correlations.map((corr) => (
              <Card
                key={corr.issue_id}
                className="border-l-4 border-l-brand-cyan bg-dark-900/90"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-xs font-bold text-brand-cyan">
                      {corr.issue_id}
                    </span>
                    <h4 className="text-xs font-semibold text-slate-200">
                      {corr.title}
                    </h4>
                  </div>
                  <Badge variant="cyan">{corr.ticket_count} Tickets</Badge>
                </div>

                <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-2">
                  <Users className="w-3.5 h-3.5 text-slate-500" />
                  <span>Affected Accounts:</span>
                  <div className="flex items-center gap-1">
                    {corr.affected_accounts.map((acc) => (
                      <span
                        key={acc}
                        className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]"
                      >
                        {acc}
                      </span>
                    ))}
                  </div>
                </div>

                <p className="text-xs text-slate-300 bg-dark-950/60 p-2.5 rounded border border-slate-800/80 leading-relaxed">
                  <Wrench className="w-3.5 h-3.5 inline mr-1 text-brand-cyan" />
                  {corr.guidance}
                </p>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Ticket Volume Spike Anomalies */}
      {anomalies.length > 0 && (
        <div className="pt-2">
          <h4 className="text-xs font-bold text-slate-300 flex items-center gap-2 mb-2">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            Ticket Volume Spike Signals
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {anomalies.map((anom, idx) => (
              <Card
                key={idx}
                className={`border ${
                  anom.is_spike
                    ? 'border-amber-500/40 bg-amber-950/20'
                    : 'border-slate-800 bg-dark-900/60'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-semibold text-xs text-slate-200">
                    {anom.product_area}
                  </span>
                  {anom.is_spike ? (
                    <Badge variant="amber" size="sm">
                      Z-Score: {anom.z_score.toFixed(1)}
                    </Badge>
                  ) : (
                    <Badge variant="slate" size="sm">
                      Normal
                    </Badge>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 font-mono mt-2 flex justify-between">
                  <span>Rolling: {anom.rolling_count}</span>
                  <span>Baseline: {anom.baseline_avg}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
