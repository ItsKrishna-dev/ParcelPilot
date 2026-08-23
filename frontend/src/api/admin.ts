import { fetchApi } from './client';
import { AdminDocument, DocumentPreview, AuditLogEntry } from '../types/admin';

export async function fetchAdminDocuments(
  sessionId: string,
  filters?: {
    doc_status?: string;
    doc_type?: string;
    account_id?: string;
    visibility?: string;
  }
): Promise<AdminDocument[]> {
  const params = new URLSearchParams();
  if (filters?.doc_status) params.append('doc_status', filters.doc_status);
  if (filters?.doc_type) params.append('doc_type', filters.doc_type);
  if (filters?.account_id) params.append('account_id', filters.account_id);
  if (filters?.visibility) params.append('visibility', filters.visibility);

  const query = params.toString() ? `?${params.toString()}` : '';
  const res = await fetchApi<{ documents: AdminDocument[] }>(
    `/admin/documents${query}`,
    {},
    sessionId
  );
  return res.documents || [];
}

export async function uploadAdminDocument(
  sessionId: string,
  formData: FormData
): Promise<{ status: string; message: string; document: AdminDocument }> {
  // Multipart upload — cannot use fetchApi (sets Content-Type: application/json).
  // Re-use the same base URL source as the rest of the app.
  const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  ).replace(/\/+$/, '');

  const response = await fetch(`${API_BASE_URL}/admin/documents/upload`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${sessionId}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let message = `Upload failed with status ${response.status}`;
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      message = errorText || message;
    }
    throw new Error(message);
  }

  return response.json();
}

export async function fetchDocumentDetails(
  sessionId: string,
  docId: string
): Promise<AdminDocument> {
  const res = await fetchApi<{ document: AdminDocument }>(
    `/admin/documents/${docId}`,
    {},
    sessionId
  );
  return res.document;
}

export async function fetchDocumentPreview(
  sessionId: string,
  docId: string
): Promise<DocumentPreview> {
  return fetchApi<DocumentPreview>(
    `/admin/documents/${docId}/preview`,
    {},
    sessionId
  );
}

export async function reviewAdminDocument(
  sessionId: string,
  docId: string,
  action: 'activate' | 'reject' | 'deprecate' | 'supersede' | 'reprocess',
  reason?: string,
  supersedesDocId?: string
): Promise<{ status: string; message: string; document: AdminDocument }> {
  return fetchApi<{ status: string; message: string; document: AdminDocument }>(
    `/admin/documents/${docId}/review`,
    {
      method: 'POST',
      body: JSON.stringify({
        action,
        reason,
        supersedes_doc_id: supersedesDocId,
        confirmed: true,
      }),
    },
    sessionId
  );
}

export async function fetchAuditLogs(
  sessionId: string,
  docId?: string
): Promise<AuditLogEntry[]> {
  const query = docId ? `?doc_id=${encodeURIComponent(docId)}` : '';
  const res = await fetchApi<{ audit_logs: AuditLogEntry[] }>(
    `/admin/audit-log${query}`,
    {},
    sessionId
  );
  return res.audit_logs || [];
}
