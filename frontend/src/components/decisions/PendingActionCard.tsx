import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, X, AlertTriangle } from 'lucide-react';
import { Button } from '../shared/Button';
import { Badge } from '../shared/Badge';
import { Card } from '../shared/Card';
import { confirmPendingAction } from '../../api/actions';

interface PendingActionCardProps {
  pendingActionId: string;
  actionType: string;
  payload: Record<string, any>;
  sessionId: string;
  onSuccess?: (actionId: string, result: any) => void;
}

export const PendingActionCard: React.FC<PendingActionCardProps> = ({
  pendingActionId,
  actionType,
  payload,
  sessionId,
  onSuccess,
}) => {
  const [isConfirming, setIsConfirming] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executedAt, setExecutedAt] = useState<string | null>(null);

  if (isDismissed) return null;

  const handleConfirm = async () => {
    setIsConfirming(true);
    setError(null);

    try {
      const res = await confirmPendingAction(
        pendingActionId,
        actionType,
        payload,
        sessionId
      );

      if (res.status === 'OK') {
        setIsConfirmed(true);
        setExecutedAt(res.executed_at || new Date().toISOString());
        if (onSuccess) {
          onSuccess(pendingActionId, res);
        }
      } else {
        setError(res.reason || res.message || 'Confirmation failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute confirmed action');
    } finally {
      setIsConfirming(false);
    }
  };

  return (
    <Card className="border-l-4 border-l-amber-500 bg-amber-950/20 border-amber-500/30 my-4 shadow-glass-md">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Action Confirmation Required
              <Badge variant="amber" size="sm">
                Draft Phase
              </Badge>
            </h4>
            <span className="text-xs text-slate-400">
              State-changing action requires explicit confirmation
            </span>
          </div>
        </div>

        {!isConfirmed && (
          <button
            onClick={() => setIsDismissed(true)}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800/60"
            title="Dismiss draft"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="bg-dark-950/80 p-3.5 rounded-lg border border-slate-800 mb-4 text-xs font-mono">
        <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-2 mb-2">
          <span>Action Type: <strong className="text-brand-cyan">{actionType}</strong></span>
          <span>Pending ID: <strong className="text-slate-300">{pendingActionId}</strong></span>
        </div>
        <pre className="text-slate-300 overflow-x-auto text-[11px] leading-relaxed">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </div>

      {error && (
        <div className="mb-3 p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isConfirmed ? (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
            <CheckCircle2 className="w-4 h-4" />
            <span>Action executed successfully and recorded in audit log</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {executedAt}
          </span>
        </div>
      ) : (
        <div className="flex items-center justify-end gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsDismissed(true)}
            disabled={isConfirming}
          >
            Dismiss Draft
          </Button>
          <Button
            variant="emerald"
            size="sm"
            onClick={handleConfirm}
            isLoading={isConfirming}
          >
            Confirm &amp; Execute Action
          </Button>
        </div>
      )}
    </Card>
  );
};
