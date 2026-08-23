import { ChatResponse, ToolTraceEntry, EvidenceItem } from './api';

export type CustomerNavView = 'chat' | 'orders' | 'tickets' | 'coverage';

export type SupportAgentNavView =
  | 'chat'
  | 'tickets'
  | 'sla_risk'
  | 'issue_clusters'
  | 'escalations';

export type ManagerNavView =
  | SupportAgentNavView
  | 'audit'
  | 'knowledge_admin';

export type ActiveNavView = CustomerNavView | ManagerNavView;

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  timestamp: string;
  text: string;
  response?: ChatResponse;
  isLoading?: boolean;
}
