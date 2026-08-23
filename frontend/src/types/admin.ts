export interface AdminDocument {
  doc_id: string;
  filename: string;
  original_filename: string;
  title: string;
  doc_type: 'support_policy' | 'sop' | 'product_ops' | 'agreement' | 'internal_note';
  status:
    | 'DRAFT'
    | 'PROCESSING'
    | 'PENDING_REVIEW'
    | 'ACTIVE'
    | 'CURRENT'
    | 'REJECTED'
    | 'SUPERSEDED'
    | 'DEPRECATED'
    | 'FAILED';
  visibility: 'customer_visible' | 'internal_only';
  effective_date?: string | null;
  expires_at?: string | null;
  account_id?: string | null;
  authority_rank?: number | null;
  supersedes_doc_id?: string | null;
  superseded_by_doc_id?: string | null;
  checksum_sha256?: string | null;
  uploaded_by?: string | null;
  uploaded_at?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  activated_by?: string | null;
  activated_at?: string | null;
  ingestion_error?: string | null;
  is_user_uploaded: boolean;
  source_origin: string;
  chunk_count: number;
  rule_count: number;
}

export interface DocumentPreview {
  doc_id: string;
  title: string;
  filename: string;
  doc_type: string;
  status: string;
  page_count: number;
  chunk_count: number;
  preview_text: string;
  chunks_snippet: Array<{ page?: number; text: string }>;
  extracted_contract_rules: Array<{
    rule_key: string;
    clause_type: string;
    value_number?: number | null;
    value_boolean?: boolean | null;
    value_text?: string | null;
    source_text: string;
  }>;
}

export interface AuditLogEntry {
  log_id: number;
  actor_user_id: string;
  actor_role: string;
  action_type: string;
  target_account_id?: string | null;
  payload?: Record<string, any> | null;
  result: string;
  created_at: string;
}
