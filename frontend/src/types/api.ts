export interface ToolTraceEntry {
  tool_name: string;
  input: Record<string, any>;
  output: Record<string, any>;
  latency_ms: number;
}

export interface EvidenceItem {
  doc_id: string;
  filename: string;
  status: string;
  effective_date?: string | null;
  page?: number | null;
  text: string;
  score?: number;
}

import { AnswerState, VerificationState, OperationalSeverity } from './trust';

export interface ChatResponse {
  answer: string;
  confidence: number | null;
  escalated: boolean;
  tool_trace: ToolTraceEntry[];
  evidence: EvidenceItem[];

  answer_state?: AnswerState;
  workflow_complete?: boolean;
  verification?: VerificationState;
  operational_severity?: OperationalSeverity;
  escalation_required?: boolean;

  intent_category?: string;
  intent_confidence?: number;
  intent_method?: string;
}

export interface ActionEngineOutput {
  status: string;
  message?: string;
  pending_action_id?: string;
  executed_at?: string;
  reason?: string;
}

export interface AnomalySignal {
  product_area: string;
  rolling_count: number;
  baseline_avg: number;
  z_score: number;
  is_spike: boolean;
}

export interface SLARiskEntry {
  ticket_id: string;
  account_id: string;
  severity: string;
  target_minutes: number;
  elapsed_minutes: number;
  minutes_to_breach: number;
  breached: boolean;
}

export interface CorrelationSignal {
  issue_id: string;
  title: string;
  affected_accounts: string[];
  ticket_count: number;
  guidance: string;
}

export interface InsightsResponse {
  ticket_volume_anomalies: AnomalySignal[];
  sla_risk: SLARiskEntry[];
  cross_account_correlations: CorrelationSignal[];
  as_of: string;
}

export interface OrderRecord {
  order_id: string;
  account_id: string;
  carrier: string;
  status: string;
  booked_at?: string | null;
  pickup_window_start?: string | null;
  pickup_window_end?: string | null;
  pickup_actual_at?: string | null;
  shipment_fee_inr: number;
  carrier_fault?: boolean | null;
  customer_fault?: boolean | null;
  cancellation_requested_at?: string | null;
  notes?: string | null;
}

export interface TicketRecord {
  ticket_id: string;
  account_id: string;
  order_id?: string | null;
  subject: string;
  status: string;
  severity?: string | null;
  created_at: string;
  updated_at?: string | null;
  historical_resolution?: string | null;
}

export interface AccountRecord {
  account_id: string;
  company_name: string;
  plan: string;
  status: string;
  cancellation_fee_waived?: boolean;
  sla_p1_minutes?: number;
  sla_p2_minutes?: number;
  sla_p3_minutes?: number;
  contract_credit_cap_inr?: number;
}
