import React from 'react';
import { ShieldCheck, AlertTriangle, XCircle, Info } from 'lucide-react';
import { Badge } from '../shared/Badge';
import { Card } from '../shared/Card';

interface CancellationCardProps {
  data: {
    decision: string;
    fee_inr: number;
    reason: string;
    contract_sources?: string[];
  };
  authoritySource?: string;
}

export const CancellationCard: React.FC<CancellationCardProps> = ({
  data,
  authoritySource,
}) => {
  const isWaived = data.decision === 'ALLOWED_NO_FEE';
  const isAllowedWithFee = data.decision === 'ALLOWED_WITH_FEE';
  const isNotAllowed = data.decision.startsWith('NOT_ALLOWED');
  const isAgreementOverride = authoritySource?.toLowerCase().includes('agreement');

  const getDecisionBadge = () => {
    switch (data.decision) {
      case 'ALLOWED_NO_FEE':
        return <Badge variant="emerald">Allowed (No Fee)</Badge>;
      case 'ALLOWED_WITH_FEE':
        return <Badge variant="amber">Allowed (₹{data.fee_inr} Fee)</Badge>;
      case 'NOT_ALLOWED_DELIVERED':
        return <Badge variant="red">Delivered (Cannot Cancel)</Badge>;
      case 'NOT_ALLOWED_USE_RETURN_TO_ORIGIN':
        return <Badge variant="red">Picked Up (Use Return-to-Origin)</Badge>;
      default:
        return <Badge variant="amber">{data.decision}</Badge>;
    }
  };

  return (
    <Card className="border-l-4 border-l-brand-blue bg-dark-900/90 my-3">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-blue-500/10 text-brand-blue border border-blue-500/20">
            {isWaived ? (
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            ) : isAllowedWithFee ? (
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              Shipment Cancellation Evaluation
            </h4>
            <span className="text-xs text-slate-400">
              Deterministic domain calculation
            </span>
          </div>
        </div>
        {getDecisionBadge()}
      </div>

      <div className="grid grid-cols-2 gap-3 p-3 bg-dark-950/60 rounded-lg border border-slate-800/80 mb-3 text-xs">
        <div>
          <span className="text-slate-500 block mb-0.5">Cancellation Fee</span>
          <span className="font-mono text-sm font-semibold text-slate-200">
            ₹{data.fee_inr.toLocaleString('en-IN')}
          </span>
        </div>

        <div>
          <span className="text-slate-500 block mb-0.5">Authority Source</span>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-300 font-medium truncate max-w-[140px]">
              {authoritySource || 'Standard SOP'}
            </span>
            {isAgreementOverride && (
              <Badge variant="violet" size="sm" className="px-1.5 text-[10px]">
                Contract Override
              </Badge>
            )}
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded border border-slate-800/50 leading-relaxed">
        <Info className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
        {data.reason}
      </p>
    </Card>
  );
};
