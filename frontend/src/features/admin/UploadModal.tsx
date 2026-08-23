import React, { useState } from 'react';
import { Upload, X, AlertTriangle, FileText, CheckCircle2, ShieldAlert } from 'lucide-react';
import { uploadAdminDocument } from '../../api/admin';
import { Button } from '../../components/shared/Button';
import { Badge } from '../../components/shared/Badge';

interface UploadModalProps {
  isOpen: boolean;
  sessionId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  sessionId,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [docType, setDocType] = useState<string>('support_policy');
  const [visibility, setVisibility] = useState<string>('internal_only');
  const [accountId, setAccountId] = useState<string>('ACCT-001');
  const [effectiveDate, setEffectiveDate] = useState<string>('');
  const [expiresAt, setExpiresAt] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Only PDF files (.pdf) are permitted.');
        setFile(null);
        return;
      }
      if (selected.size > 10 * 1024 * 1024) {
        setError('File size exceeds 10MB limit.');
        setFile(null);
        return;
      }
      setError(null);
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.pdf$/i, ''));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF document to upload.');
      return;
    }

    if (docType === 'agreement' && !accountId) {
      setError('Agreement documents require selecting a valid customer Account ID.');
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title || file.name);
    formData.append('doc_type', docType);
    formData.append('visibility', visibility);
    if (docType === 'agreement' && accountId) {
      formData.append('account_id', accountId);
    }
    if (effectiveDate) {
      formData.append('effective_date', new Date(effectiveDate).toISOString());
    }
    if (expiresAt) {
      formData.append('expires_at', new Date(expiresAt).toISOString());
    }

    try {
      await uploadAdminDocument(sessionId, formData);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-dark-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-panel max-w-lg w-full rounded-2xl border border-slate-700/80 shadow-2xl p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-1">
          <div className="p-2 rounded-xl bg-brand-blue/15 text-brand-blue border border-brand-blue/30">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">
              Upload Knowledge Document
            </h3>
            <span className="text-xs text-slate-400">
              Governed manager ingestion workflow
            </span>
          </div>
        </div>

        {/* Warning Banner */}
        <div className="my-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 flex items-start gap-2.5 leading-relaxed">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong className="block font-semibold text-amber-200">
              Upload != Instant Policy Authority
            </strong>
            Uploaded documents enter <strong>PENDING_REVIEW</strong> state and require explicit manager review &amp; activation before influencing policy or agent answers.
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* File Picker */}
          <div>
            <label className="block font-semibold text-slate-300 mb-1">
              Select PDF File (Max 10MB) *
            </label>
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="w-full bg-dark-900 border border-slate-700/80 rounded-xl p-2.5 text-slate-300 text-xs file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-blue file:text-white hover:file:bg-blue-600 cursor-pointer"
            />
          </div>

          {/* Document Title */}
          <div>
            <label className="block font-semibold text-slate-300 mb-1">
              Document Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Northstar Logistics 2026 Enterprise Agreement Amendment"
              className="w-full bg-dark-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-blue"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Document Type */}
            <div>
              <label className="block font-semibold text-slate-300 mb-1">
                Document Type *
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full bg-dark-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-blue"
              >
                <option value="support_policy">Support Policy</option>
                <option value="sop">SOP (Standard Operating Procedure)</option>
                <option value="product_ops">Product Operations Guide</option>
                <option value="agreement">Signed Customer Agreement</option>
                <option value="internal_note">Internal Operations Note</option>
              </select>
            </div>

            {/* Visibility */}
            <div>
              <label className="block font-semibold text-slate-300 mb-1">
                Visibility *
              </label>
              <select
                value={visibility}
                onChange={(e) => setVisibility(e.target.value)}
                className="w-full bg-dark-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-blue"
              >
                <option value="internal_only">Internal Only</option>
                <option value="customer_visible" disabled={docType === 'internal_note'}>
                  Customer Visible
                </option>
              </select>
            </div>
          </div>

          {/* Account Selector (Required for agreement) */}
          {docType === 'agreement' && (
            <div>
              <label className="block font-semibold text-amber-400 mb-1">
                Target Customer Account *
              </label>
              <select
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="w-full bg-dark-900 border border-amber-500/40 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
              >
                <option value="ACCT-001">ACCT-001 (Northstar Logistics)</option>
                <option value="ACCT-002">ACCT-002 (LumenWorks)</option>
                <option value="ACCT-003">ACCT-003 (Beacon Retail)</option>
                <option value="ACCT-004">ACCT-004 (Axis Labs)</option>
              </select>
            </div>
          )}

          {/* Effective & Expiry Dates */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-300 mb-1">
                Effective Date
              </label>
              <input
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                className="w-full bg-dark-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-300 mb-1">
                Expiration Date (Optional)
              </label>
              <input
                type="date"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                className="w-full bg-dark-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="ghost" size="sm" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={!file}
              isLoading={isUploading}
            >
              Upload &amp; Process Document
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
