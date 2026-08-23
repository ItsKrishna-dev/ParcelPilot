import React, { useEffect, useState } from 'react';
import {
  FileText,
  Upload,
  RefreshCw,
  AlertCircle,
  Filter,
  Search,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Eye,
} from 'lucide-react';
import { MockSession } from '../../types/auth';
import { AdminDocument } from '../../types/admin';
import { fetchAdminDocuments } from '../../api/admin';
import { Card } from '../../components/shared/Card';
import { Badge } from '../../components/shared/Badge';
import { Button } from '../../components/shared/Button';
import { LoadingSkeleton } from '../../components/shared/LoadingSkeleton';
import { EmptyState } from '../../components/shared/EmptyState';
import { UploadModal } from './UploadModal';
import { ReviewDrawer } from './ReviewDrawer';
import { formatDate } from '../../lib/utils';

interface KnowledgeAdminViewProps {
  session: MockSession;
}

export const KnowledgeAdminView: React.FC<KnowledgeAdminViewProps> = ({
  session,
}) => {
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedReviewDoc, setSelectedReviewDoc] = useState<AdminDocument | null>(
    null
  );

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAdminDocuments(session.sessionId);
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [session.sessionId]);

  const filteredDocs = documents.filter((doc) => {
    const term = search.toLowerCase();
    const matchesSearch =
      doc.title.toLowerCase().includes(term) ||
      doc.filename.toLowerCase().includes(term) ||
      doc.doc_id.toLowerCase().includes(term) ||
      (doc.account_id && doc.account_id.toLowerCase().includes(term));

    const matchesStatus =
      statusFilter === 'all' || doc.status === statusFilter;

    const matchesType = typeFilter === 'all' || doc.doc_type === typeFilter;

    return matchesSearch && matchesStatus && matchesType;
  });

  const pendingCount = documents.filter((d) => d.status === 'PENDING_REVIEW').length;
  const activeCount = documents.filter((d) => d.status === 'ACTIVE' || d.status === 'CURRENT').length;
  const failedCount = documents.filter((d) => d.status === 'FAILED').length;
  const deprecatedCount = documents.filter((d) => d.status === 'DEPRECATED' || d.status === 'SUPERSEDED').length;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
      case 'CURRENT':
        return <Badge variant="emerald">ACTIVE</Badge>;
      case 'PENDING_REVIEW':
        return <Badge variant="amber">PENDING REVIEW</Badge>;
      case 'PROCESSING':
        return <Badge variant="blue">PROCESSING</Badge>;
      case 'FAILED':
        return <Badge variant="red">FAILED</Badge>;
      case 'REJECTED':
        return <Badge variant="red">REJECTED</Badge>;
      case 'DEPRECATED':
      case 'SUPERSEDED':
        return <Badge variant="slate">{status}</Badge>;
      default:
        return <Badge variant="slate">{status}</Badge>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-brand-blue" />
            Knowledge Administration
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Governed document ingestion. Uploaded documents require review before they influence agent responses.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={isLoading}
            className="glass-panel px-3 py-2 rounded-xl border border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsUploadOpen(true)}
          >
            <Upload className="w-4 h-4" />
            Upload Document
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <Card className="border-l-4 border-l-amber-500 bg-amber-950/20">
          <span className="text-slate-400 block mb-1">Pending Review</span>
          <span className="text-2xl font-bold font-mono text-amber-400">
            {pendingCount}
          </span>
        </Card>

        <Card className="border-l-4 border-l-emerald-500 bg-emerald-950/20">
          <span className="text-slate-400 block mb-1">Active Corpus</span>
          <span className="text-2xl font-bold font-mono text-emerald-400">
            {activeCount}
          </span>
        </Card>

        <Card className="border-l-4 border-l-red-500 bg-red-950/20">
          <span className="text-slate-400 block mb-1">Ingestion Failures</span>
          <span className="text-2xl font-bold font-mono text-red-400">
            {failedCount}
          </span>
        </Card>

        <Card className="border-l-4 border-l-slate-500 bg-slate-900/60">
          <span className="text-slate-400 block mb-1">Deprecated / Superseded</span>
          <span className="text-2xl font-bold font-mono text-slate-300">
            {deprecatedCount}
          </span>
        </Card>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 glass-panel p-3 rounded-xl border border-slate-800">
        <div className="flex-1 min-w-[200px] flex items-center gap-2 bg-dark-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by title, filename, doc ID, or account..."
            className="bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none w-full"
          />
        </div>

        <div className="flex items-center gap-2 text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-dark-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="ACTIVE">Active</option>
            <option value="CURRENT">Current (Baseline)</option>
            <option value="FAILED">Failed</option>
            <option value="DEPRECATED">Deprecated</option>
            <option value="SUPERSEDED">Superseded</option>
            <option value="REJECTED">Rejected</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-dark-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none"
          >
            <option value="all">All Document Types</option>
            <option value="support_policy">Support Policy</option>
            <option value="sop">SOP</option>
            <option value="product_ops">Product Operations</option>
            <option value="agreement">Signed Agreement</option>
            <option value="internal_note">Internal Note</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Document Table */}
      {isLoading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-16 w-full" />
          <LoadingSkeleton className="h-16 w-full" />
          <LoadingSkeleton className="h-16 w-full" />
        </div>
      ) : filteredDocs.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No Documents Found"
          description="No knowledge documents match your filter criteria."
        />
      ) : (
        <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden shadow-glass-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-dark-900 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Doc ID / Title</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Scope / Account</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Effective</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {filteredDocs.map((d) => (
                  <tr key={d.doc_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100 font-sans line-clamp-1">
                        {d.title || d.filename}
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {d.doc_id} • {d.filename}
                      </span>
                    </td>

                    <td className="py-3 px-4 font-sans font-medium uppercase text-brand-cyan text-[11px]">
                      {d.doc_type}
                    </td>

                    <td className="py-3 px-4 font-sans">
                      <div className="flex flex-col">
                        <span className="text-slate-300 text-xs">
                          {d.account_id || 'Global Policy'}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {d.visibility}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4 font-sans">{getStatusBadge(d.status)}</td>

                    <td className="py-3 px-4 text-slate-400">
                      {d.effective_date ? formatDate(d.effective_date) : 'Immediate'}
                    </td>

                    <td className="py-3 px-4 text-slate-400 font-sans">
                      <div className="text-[11px]">{d.uploaded_by || 'system'}</div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        {formatDate(d.uploaded_at)}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-right font-sans">
                      <Button
                        variant={d.status === 'PENDING_REVIEW' ? 'emerald' : 'secondary'}
                        size="sm"
                        onClick={() => setSelectedReviewDoc(d)}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        {d.status === 'PENDING_REVIEW' ? 'Review & Process' : 'Inspect'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        sessionId={session.sessionId}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={loadData}
      />

      {/* Review Drawer */}
      <ReviewDrawer
        doc={selectedReviewDoc}
        allDocs={documents}
        sessionId={session.sessionId}
        onClose={() => setSelectedReviewDoc(null)}
        onSuccess={loadData}
      />
    </div>
  );
};
