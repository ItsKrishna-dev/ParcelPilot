import React, { useEffect, useState } from 'react';
import { Ticket, RefreshCw, AlertCircle, Search, Filter } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { TicketRecord } from '../../types/api';
import { fetchTickets } from '../../api/records';
import { Badge } from '../shared/Badge';
import { LoadingSkeleton } from '../shared/LoadingSkeleton';
import { EmptyState } from '../shared/EmptyState';
import { formatDate } from '../../lib/utils';

interface TicketsViewProps {
  session: MockSession;
}

export const TicketsView: React.FC<TicketsViewProps> = ({ session }) => {
  const [tickets, setTickets] = useState<TicketRecord[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchTickets(session.sessionId);
      setTickets(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load support tickets.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [session.sessionId]);

  const filteredTickets = tickets.filter((t) => {
    const matchesSearch =
      t.ticket_id.toLowerCase().includes(search.toLowerCase()) ||
      t.subject.toLowerCase().includes(search.toLowerCase()) ||
      (t.order_id && t.order_id.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === 'all' || t.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const getSeverityBadge = (severity?: string | null) => {
    switch (severity) {
      case 'P1':
        return <Badge variant="red">P1 Critical</Badge>;
      case 'P2':
        return <Badge variant="amber">P2 High</Badge>;
      case 'P3':
        return <Badge variant="blue">P3 Normal</Badge>;
      default:
        return <Badge variant="slate">{severity || 'P3'}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <Badge variant="red">OPEN</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="amber">IN PROGRESS</Badge>;
      case 'RESOLVED':
        return <Badge variant="emerald">RESOLVED</Badge>;
      default:
        return <Badge variant="slate">{status}</Badge>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Ticket className="w-5 h-5 text-brand-blue" />
            Support Ticket Queue
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {session.role === 'customer'
              ? `Tickets submitted under ${session.accountName || session.accountId}`
              : 'Support Operations Queue — Cross-Account Ticket Overview'}
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="glass-panel px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Queue
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 glass-panel p-3 rounded-xl border border-slate-800">
        <div className="flex-1 min-w-[200px] flex items-center gap-2 bg-dark-900 border border-slate-700/80 rounded-lg px-3 py-1.5">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ticket ID, order ID, or subject..."
            className="bg-transparent text-xs text-slate-200 placeholder-slate-500 focus:outline-none w-full"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-dark-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
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
        </div>
      ) : filteredTickets.length === 0 ? (
        <EmptyState
          icon={Ticket}
          title="No Tickets Found"
          description="No tickets match your search or filter parameters."
        />
      ) : (
        <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden shadow-glass-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-dark-900 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Ticket ID</th>
                  <th className="py-3 px-4">Account</th>
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4">Subject</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {filteredTickets.map((t) => (
                  <tr key={t.ticket_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-100">{t.ticket_id}</td>
                    <td className="py-3 px-4 text-slate-400">{t.account_id}</td>
                    <td className="py-3 px-4 text-brand-cyan">{t.order_id || 'N/A'}</td>
                    <td className="py-3 px-4 font-sans font-medium text-slate-200 max-w-xs truncate">
                      {t.subject}
                    </td>
                    <td className="py-3 px-4 font-sans">{getSeverityBadge(t.severity)}</td>
                    <td className="py-3 px-4 font-sans">{getStatusBadge(t.status)}</td>
                    <td className="py-3 px-4 text-slate-400">{formatDate(t.created_at)}</td>
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
