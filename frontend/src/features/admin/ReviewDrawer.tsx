import React, { useEffect, useState } from 'react';
import {
  X,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Award,
  RefreshCw,
  Info,
  Clock,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { AdminDocument, DocumentPreview } from '../../types/admin';
import { fetchDocumentPreview, reviewAdminDocument } from '../../api/admin';
import { Button } from '../../components/shared/Button';
import { Badge } from '../../components/shared/Badge';
import { Card } from '../../components/shared/Card';

interface ReviewDrawerProps {
  doc: AdminDocument | null;
  allDocs: AdminDocument[];
  sessionId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const ReviewDrawer: React.FC<ReviewDrawerProps> = ({
  doc,
  allDocs,
  sessionId,
  onClose,
  onSuccess,
}) => {
  const [preview, setPreview] = useState<DocumentPreview | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [confirmAction, setConfirmAction] = useState<
    'activate' | 'reject' | 'deprecate' | 'supersede' | 'reprocess' | null
  >(null);
  const [reason, setReason] = useState('');
  const [targetSupersedesId, setTargetSupersedesId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (doc) {
      setIsLoadingPreview(true);
      setError(null);
      fetchDocumentPreview(sessionId, doc.doc_id)
        .then(setPreview)
        .catch((err) => setError(err.message))
        .finally(() => setIsLoadingPreview(false));
    } else {
      setPreview(null);
    }
  }, [doc, sessionId]);

  if (!doc) return null;

  const handleExecuteAction = async () => {
    if (!confirmAction) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await reviewAdminDocument(
        sessionId,
        doc.doc_id,
        confirmAction,
        reason,
        targetSupersedesId || undefined
      );
      setConfirmAction(null);
      setReason('');
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'State transition failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeOtherDocs = allDocs.filter(
    (d) => d.doc_id !== doc.doc_id && (d.status === 'ACTIVE' || d.status === 'CURRENT')
  );

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-dark-950/70 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-2xl bg-dark-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-slide-left">
        {/* Header */}
        <div className="p-4 sm:p-6 border-b border-slate-800 flex items-center justify-between bg-dark-950/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-brand-cyan font-bold">
                {doc.doc_id}
              </span>
              <Badge
                variant={
                  doc.status === 'ACTIVE' || doc.status === 'CURRENT'
                    ? 'emerald'
                    : doc.status === 'PENDING_REVIEW'
                    ? 'amber'
                    : doc.status === 'DEPRECATED' || doc.status === 'SUPERSEDED'
                    ? 'slate'
                    : 'red'
                }
              >
                {doc.status}
              </Badge>
            </div>
            <h2 className="text-base font-bold text-slate-100 line-clamp-1">
              {doc.title || doc.filename}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 text-xs">
          {error && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4 bg-dark-950/80 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-500 block mb-0.5">Document Type</span>
              <span className="font-semibold text-slate-200 uppercase">
                {doc.doc_type}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block mb-0.5">Visibility</span>
              <Badge variant={doc.visibility === 'customer_visible' ? 'blue' : 'slate'} size="sm">
                {doc.visibility}
              </Badge>
            </div>

            <div>
              <span className="text-slate-500 block mb-0.5">Account Scope</span>
              <span className="font-mono text-slate-200">
                {doc.account_id || 'Global Policy'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block mb-0.5">Effective Date</span>
              <span className="text-slate-300">
                {doc.effective_date ? new Date(doc.effective_date).toLocaleDateString() : 'Immediate'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block mb-0.5">Uploaded By</span>
              <span className="text-slate-300 font-mono">
                {doc.uploaded_by || 'system'}
              </span>
            </div>

            <div>
              <span className="text-slate-500 block mb-0.5">SHA-256 Checksum</span>
              <span className="font-mono text-[10px] text-slate-400 truncate block max-w-[120px]">
                {doc.checksum_sha256 ? `${doc.checksum_sha256.slice(0, 12)}...` : 'N/A'}
              </span>
            </div>
          </div>

          {/* Extracted Contract Rules Preview */}
          {doc.doc_type === 'agreement' && preview?.extracted_contract_rules && (
            <div>
              <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5 mb-2">
                <Award className="w-4 h-4 text-violet-400" />
                Extracted Agreement Clauses ({preview.extracted_contract_rules.length})
              </h4>
              <div className="space-y-2">
                {preview.extracted_contract_rules.map((rule, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-violet-950/20 border border-violet-500/30 rounded-lg text-xs"
                  >
                    <div className="flex items-center justify-between text-violet-300 font-mono font-semibold mb-1">
                      <span>{rule.rule_key}</span>
                      <span className="text-[10px] text-slate-400">
                        {rule.clause_type}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300 bg-dark-950/60 p-2 rounded border border-slate-800 font-mono">
                      "{rule.source_text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Safe Text Content Preview */}
          <div>
            <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5 mb-2">
              <FileText className="w-4 h-4 text-brand-blue" />
              Document Text Preview ({preview?.chunk_count || 0} Chunks)
            </h4>

            {isLoadingPreview ? (
              <div className="p-4 text-center text-slate-500">
                Loading safe document preview...
              </div>
            ) : (
              <pre className="p-4 bg-dark-950/90 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed">
                {preview?.preview_text || 'No text extracted.'}
              </pre>
            )}
          </div>

          {/* Confirmation Dialog Overlay inside Drawer */}
          {confirmAction && (
            <Card className="border-l-4 border-l-brand-blue bg-dark-950 p-4 border border-brand-blue/30 space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-slate-100">
                <ShieldCheck className="w-5 h-5 text-brand-blue" />
                <span>Confirm Action: <strong className="uppercase">{confirmAction}</strong></span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {confirmAction === 'activate' &&
                  'Activating this document will make its clauses and content eligible for live LLM retrieval and policy calculations.'}
                {confirmAction === 'reject' &&
                  'Rejecting will exclude this document from retrieval permanently.'}
                {confirmAction === 'deprecate' &&
                  'Deprecating will remove this document from normal current-policy answers. It will only be retrieved for explicit historical queries.'}
                {confirmAction === 'supersede' &&
                  'Superseding will replace an existing active policy document with this one.'}
              </p>

              {(confirmAction === 'activate' || confirmAction === 'supersede') && activeOtherDocs.length > 0 && (
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">
                    Optionally Supersede Existing Document:
                  </label>
                  <select
                    value={targetSupersedesId}
                    onChange={(e) => setTargetSupersedesId(e.target.value)}
                    className="w-full bg-dark-900 border border-slate-700/80 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="">None (Keep both active)</option>
                    {activeOtherDocs.map((d) => (
                      <option key={d.doc_id} value={d.doc_id}>
                        Supersede {d.doc_id} ({d.title})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">
                  Manager Review Reason / Audit Note:
                </label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Approved 2026 contract terms per legal signoff"
                  className="w-full bg-dark-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmAction(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant={confirmAction === 'reject' ? 'danger' : 'emerald'}
                  size="sm"
                  onClick={handleExecuteAction}
                  isLoading={isSubmitting}
                >
                  Confirm &amp; Execute {confirmAction.toUpperCase()}
                </Button>
              </div>
            </Card>
          )}
        </div>

        {/* Action Footer */}
        {!confirmAction && (
          <div className="p-4 border-t border-slate-800 bg-dark-950/90 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {doc.status === 'FAILED' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setConfirmAction('reprocess')}
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Reprocess Ingestion
                </Button>
              )}

              {(doc.status === 'ACTIVE' || doc.status === 'CURRENT') && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setConfirmAction('deprecate')}
                >
                  Deprecate
                </Button>
              )}
            </div>

            <div className="flex items-center gap-2">
              {doc.status === 'PENDING_REVIEW' && (
                <>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => setConfirmAction('reject')}
                  >
                    Reject
                  </Button>
                  <Button
                    variant="emerald"
                    size="sm"
                    onClick={() => setConfirmAction('activate')}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Activate Document
                  </Button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
