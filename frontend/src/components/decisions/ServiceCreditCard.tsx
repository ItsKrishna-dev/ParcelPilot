import React from 'react';
import { DollarSign, CheckCircle2, AlertCircle, UserCheck } from 'lucide-react';
import { Badge } from '../shared/Badge';
import { Card } from '../shared/Card';

interface ServiceCreditCardProps {
  data: {
    decision: string;
    credit_inr: number;
    requires_manager_approval?: boolean;
    reason: string;
    contract_sources?: string[];
  };
  authoritySource?: string;
}

export const ServiceCreditCard: React.FC<ServiceCreditCardProps> = ({
  data,
  authoritySource,
}) => {
  const isEligible = data.decision === 'ELIGIBLE';
  const isAgreementOverride = authoritySource?.toLowerCase().includes('agreement');

  return (
    <Card className="border-l-4 border-l-emerald-500 bg-dark-900/90 my-3">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              Failed-Pickup Service Credit Evaluation
            </h4>
            <span className="text-xs text-slate-400">
              Deterministic domain calculation
            </span>
          </div>
        </div>

        {isEligible ? (
          <Badge variant="emerald">Eligible for Credit</Badge>
        ) : data.decision === 'NEEDS_VERIFICATION' ? (
          <Badge variant="amber">Needs Fault Verification</Badge>
        ) : (
          <Badge variant="red">Not Eligible</Badge>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 p-3 bg-dark-950/60 rounded-lg border border-slate-800/80 mb-3 text-xs">
        <div>
          <span className="text-slate-500 block mb-0.5">Credit Amount</span>
          <span className="font-mono text-sm font-bold text-emerald-400">
            ₹{data.credit_inr.toLocaleString('en-IN')}
          </span>
        </div>

        <div>
          <span className="text-slate-500 block mb-0.5">Manager Approval</span>
          <span className="text-slate-300 font-medium">
            {data.requires_manager_approval ? (
              <span className="text-amber-400 flex items-center gap-1 font-semibold">
                <UserCheck className="w-3.5 h-3.5" /> Required (&gt;₹1,000)
              </span>
            ) : (
              <span className="text-slate-400">Not Required</span>
            )}
          </span>
        </div>

        <div>
          <span className="text-slate-500 block mb-0.5">Authority Source</span>
          <div className="flex items-center gap-1">
            <span className="text-slate-300 font-medium truncate">
              {authoritySource || 'Standard Credit SOP'}
            </span>
            {isAgreementOverride && (
              <Badge variant="violet" size="sm" className="px-1 text-[9px]">
                Agreement
              </Badge>
            )}
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded border border-slate-800/50 leading-relaxed">
        {data.reason}
      </p>
    </Card>
  );
};
