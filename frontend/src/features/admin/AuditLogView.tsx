import React, { useEffect, useState } from 'react';
import { FileText, RefreshCw, AlertCircle, Shield, Search } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { AuditLogEntry } from '../../types/admin';
import { fetchAuditLogs } from '../../api/admin';
import { Badge } from '../../components/shared/Badge';
import { LoadingSkeleton } from '../../components/shared/LoadingSkeleton';
import { EmptyState } from '../../components/shared/EmptyState';
import { formatDate } from '../../lib/utils';

interface AuditLogViewProps {
  session: MockSession;
}

export const AuditLogView: React.FC<AuditLogViewProps> = ({ session }) => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAuditLogs(session.sessionId);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [session.sessionId]);

  const filteredLogs = logs.filter((l) => {
    const term = search.toLowerCase();
    return (
      l.action_type.toLowerCase().includes(term) ||
      l.actor_user_id.toLowerCase().includes(term) ||
      (l.target_account_id && l.target_account_id.toLowerCase().includes(term)) ||
      (l.payload?.doc_id && String(l.payload.doc_id).toLowerCase().includes(term))
    );
  });

  const getActionBadge = (action: string) => {
    if (action.includes('activated') || action.includes('succeeded')) {
      return <Badge variant="emerald">{action}</Badge>;
    }
    if (action.includes('failed') || action.includes('rejected')) {
      return <Badge variant="red">{action}</Badge>;
    }
    if (action.includes('uploaded') || action.includes('started')) {
      return <Badge variant="blue">{action}</Badge>;
    }
    return <Badge variant="slate">{action}</Badge>;
  };

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-blue" />
            Manager Audit Trail &amp; Governance Log
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Auditable trail of document uploads, state transitions, ingestion events, and SLA overrides.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="glass-panel px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Audit Log
        </button>
      </div>

      <div className="flex items-center gap-2 bg-dark-900 border border-slate-800 rounded-xl px-3 py-2 text-xs">
        <Search className="w-4 h-4 text-slate-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search audit trail by actor, doc ID, action, or account..."
          className="bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-16 w-full" />
          <LoadingSkeleton className="h-16 w-full" />
          <LoadingSkeleton className="h-16 w-full" />
        </div>
      ) : filteredLogs.length === 0 ? (
        <EmptyState
          icon={Shield}
          title="No Audit Records Found"
          description="There are no audit events matching your search filter."
        />
      ) : (
        <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden shadow-glass-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-dark-900 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Log ID</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Target Account</th>
                  <th className="py-3 px-4">Result</th>
                  <th className="py-3 px-4">Payload Details</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {filteredLogs.map((l) => (
                  <tr key={l.log_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-400">#{l.log_id}</td>
                    <td className="py-3 px-4">
                      <span className="text-slate-200 font-semibold">{l.actor_user_id}</span>
                      <span className="text-[10px] text-slate-500 block">{l.actor_role}</span>
                    </td>
                    <td className="py-3 px-4 font-sans">{getActionBadge(l.action_type)}</td>
                    <td className="py-3 px-4 text-slate-400">{l.target_account_id || 'Global'}</td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">{l.result}</td>
                    <td className="py-3 px-4 max-w-xs truncate text-[11px] text-slate-400">
                      {JSON.stringify(l.payload || {})}
                    </td>
                    <td className="py-3 px-4 text-slate-400">{formatDate(l.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
