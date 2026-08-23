export type AnswerState =
  | 'conversational'
  | 'verified'
  | 'needs_verification'
  | 'workflow_incomplete'
  | 'access_denied'
  | 'out_of_scope'
  | 'provider_unavailable'
  | 'error';

export type OperationalSeverity =
  | 'info'
  | 'low'
  | 'medium'
  | 'high'
  | 'critical'
  | 'unknown';

export type VerificationState =
  | 'not_required'
  | 'recommended'
  | 'required';

export interface TrustState {
  answerState: AnswerState;
  confidence: number;
  operationalSeverity: OperationalSeverity;
  escalationRequired: boolean;
  verification: VerificationState;
  workflowComplete: boolean;
}

export interface UserFacingError {
  title: string;
  message: string;
  code:
    | 'BACKEND_UNAVAILABLE'
    | 'PROVIDER_UNAVAILABLE'
    | 'ACCESS_DENIED'
    | 'VALIDATION_ERROR'
    | 'MALFORMED_RESPONSE'
    | 'TIMEOUT'
    | 'UNKNOWN';
}
