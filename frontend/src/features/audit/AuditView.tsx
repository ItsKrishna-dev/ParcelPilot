import React from 'react';
import { FileText, Shield, Info } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { Card } from '../../components/shared/Card';
import { EmptyState } from '../../components/shared/EmptyState';

interface AuditViewProps {
  session: MockSession;
}

export const AuditView: React.FC<AuditViewProps> = ({ session }) => {
  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <FileText className="w-5 h-5 text-brand-blue" />
          Manager Governance &amp; Audit Log
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Auditable record of all tool trace executions, action confirmations, and SLA overrides.
        </p>
      </div>

      <EmptyState
        icon={Shield}
        title="Audit API Not Exposed in Stage 1"
        description="Audit API is not exposed in this Stage 1 dashboard. Action execution details are recorded directly in PostgreSQL transaction tables during confirmation."
      />

      <Card className="border border-slate-800 bg-dark-900/60 p-4 text-xs text-slate-300">
        <div className="flex items-center gap-2 font-semibold text-slate-200 mb-2">
          <Info className="w-4 h-4 text-brand-blue" />
          <span>Stage 1 Backend Audit Record Architecture</span>
        </div>
        <p className="leading-relaxed text-slate-400">
          When support agents or managers confirm a pending action (such as creating an escalation or overriding an SLA), the backend `action_engine` writes an `Escalation` record into PostgreSQL under the user's role context (`{session.sessionId}`).
        </p>
      </Card>
    </div>
  );
};
