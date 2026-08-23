import React, { useEffect, useState } from 'react';
import { Shield, Award, Clock, DollarSign, CheckCircle2, AlertCircle } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { AccountRecord } from '../../types/api';
import { fetchAccountDetails } from '../../api/records';
import { Card } from '../shared/Card';
import { Badge } from '../shared/Badge';
import { LoadingSkeleton } from '../shared/LoadingSkeleton';

interface AccountCoverageViewProps {
  session: MockSession;
}

export const AccountCoverageView: React.FC<AccountCoverageViewProps> = ({
  session,
}) => {
  const [account, setAccount] = useState<AccountRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchAccountDetails(session.sessionId);
        setAccount(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load account coverage.');
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [session.sessionId]);

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Shield className="w-5 h-5 text-brand-violet" />
          Account Coverage &amp; Support Entitlements
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Active contract rules and SLA targets governing account{' '}
          <strong className="text-slate-200">{session.accountId || 'General'}</strong>
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          <LoadingSkeleton className="h-32 w-full" />
          <LoadingSkeleton className="h-48 w-full" />
        </div>
      ) : account ? (
        <div className="space-y-6">
          <Card className="border-l-4 border-l-brand-violet bg-dark-900/90">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div>
                <span className="text-xs font-mono text-violet-400 uppercase tracking-wider block mb-1">
                  Enterprise Support Tier
                </span>
                <h3 className="text-lg font-bold text-slate-100">
                  {account.company_name}
                </h3>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="violet" size="md">
                  {account.plan} Plan
                </Badge>
                <Badge variant="emerald" size="md">
                  {account.status}
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-dark-950/80 rounded-xl border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block mb-1">Cancellation Fee Terms</span>
                <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                  {account.cancellation_fee_waived ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Waived for BOOKED
                    </span>
                  ) : (
                    <span className="text-slate-300">Standard SOP (INR 250)</span>
                  )}
                </div>
              </div>

              <div>
                <span className="text-slate-500 block mb-1">Credit Cap Limit</span>
                <span className="font-mono text-sm font-bold text-emerald-400">
                  ₹{account.contract_credit_cap_inr?.toLocaleString('en-IN') || '5,000'} / mo
                </span>
              </div>

              <div>
                <span className="text-slate-500 block mb-1">SLA P1 Target</span>
                <span className="font-mono text-sm font-bold text-brand-cyan">
                  {account.sla_p1_minutes || 15} minutes
                </span>
              </div>
            </div>
          </Card>

          {/* SLA Target Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="border border-slate-800 bg-dark-900/80">
              <div className="flex items-center gap-2 text-red-400 text-xs font-semibold mb-2">
                <Clock className="w-4 h-4" /> P1 Critical Target
              </div>
              <p className="text-2xl font-mono font-bold text-slate-100">
                {account.sla_p1_minutes || 15} mins
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                24x7 immediate response for system outage or emergency.
              </p>
            </Card>

            <Card className="border border-slate-800 bg-dark-900/80">
              <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold mb-2">
                <Clock className="w-4 h-4" /> P2 High Target
              </div>
              <p className="text-2xl font-mono font-bold text-slate-100">
                {account.sla_p2_minutes || 60} mins
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                Business hours response for major operational impact.
              </p>
            </Card>

            <Card className="border border-slate-800 bg-dark-900/80">
              <div className="flex items-center gap-2 text-brand-blue text-xs font-semibold mb-2">
                <Clock className="w-4 h-4" /> P3 Standard Target
              </div>
              <p className="text-2xl font-mono font-bold text-slate-100">
                {account.sla_p3_minutes || 480} mins
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                General inquiry and standard support requests.
              </p>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
};
