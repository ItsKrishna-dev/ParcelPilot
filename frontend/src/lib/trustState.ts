import { ChatResponse } from '../types/api';
import { TrustState, OperationalSeverity } from '../types/trust';

export function deriveTrustState(
  response: ChatResponse,
  userMessage?: string
): TrustState {
  if (response.answer_state) {
    return {
      answerState: response.answer_state,
      confidence: response.confidence ?? 0,
      operationalSeverity: response.operational_severity ?? 'info',
      escalationRequired: response.escalation_required ?? false,
      verification: response.verification ?? 'not_required',
      workflowComplete: response.workflow_complete ?? true,
    };
  }

  const answer = response.answer || '';
  const confidence = response.confidence ?? 0;
  const escalated = response.escalated ?? false;
  const traces = response.tool_trace || [];
  const evidence = response.evidence || [];

  const lowerAnswer = answer.toLowerCase();
  const lowerUserMsg = (userMessage || '').toLowerCase();

  // Detect Provider Error / Failure
  const isProviderUnavailable =
    lowerAnswer.includes('unable to reach the ai model provider') ||
    lowerAnswer.includes('all ai providers failed') ||
    lowerAnswer.includes('provider unavailable');

  if (isProviderUnavailable) {
    return {
      answerState: 'provider_unavailable',
      confidence: 0,
      operationalSeverity: 'critical',
      escalationRequired: true,
      verification: 'required',
      workflowComplete: false,
    };
  }

  // Detect Access Denied
  const isAccessDenied =
    lowerAnswer.includes('access denied') ||
    lowerAnswer.includes('restricted to account') ||
    traces.some(
      (t) =>
        t.output?.status === 'ACCESS_DENIED' ||
        (t.output?.error && String(t.output.error).includes('Access denied'))
    );

  if (isAccessDenied) {
    return {
      answerState: 'access_denied',
      confidence: 0,
      operationalSeverity: 'medium',
      escalationRequired: false,
      verification: 'not_required',
      workflowComplete: true,
    };
  }

  // Detect Workflow Incomplete (e.g. tool budget exhausted or empty content)
  const isWorkflowIncomplete =
    lowerAnswer.includes('allotted tool-call budget') ||
    lowerAnswer.includes('workflow did not complete') ||
    (confidence <= 0.25 &&
      escalated &&
      (lowerAnswer.includes('tool-call budget') || lowerAnswer.includes('escalating to human agent')));

  if (isWorkflowIncomplete) {
    return {
      answerState: 'workflow_incomplete',
      confidence: Math.min(confidence, 0.25),
      operationalSeverity: 'high',
      escalationRequired: true,
      verification: 'required',
      workflowComplete: false,
    };
  }

  // Detect Needs Verification
  const isNeedsVerification =
    traces.some((t) => t.output?.status === 'NEEDS_VERIFICATION') ||
    lowerAnswer.includes('needs_verification') ||
    lowerAnswer.includes('requires verification') ||
    lowerAnswer.includes('unable to confirm fault') ||
    (confidence <= 0.55 && escalated);

  if (isNeedsVerification) {
    return {
      answerState: 'needs_verification',
      confidence: Math.min(confidence, 0.55),
      operationalSeverity: 'medium',
      escalationRequired: true,
      verification: 'required',
      workflowComplete: true,
    };
  }

  // Detect KI-211 or recommended carrier verification (SwiftShip webhook delay)
  const isKI211 =
    lowerUserMsg.includes('ki-211') ||
    lowerUserMsg.includes('booked after') ||
    lowerUserMsg.includes('driver picked') ||
    answer.includes('KI-211') ||
    lowerAnswer.includes('webhook delay') ||
    evidence.some((e) => e.text.includes('KI-211'));

  if (isKI211) {
    return {
      answerState: 'verified',
      confidence: 0.95,
      operationalSeverity: 'medium',
      escalationRequired: false,
      verification: 'recommended',
      workflowComplete: true,
    };
  }

  // Standard Verified Answer (Fee waivers, service credits, SLA lookup)
  const finalConf = Math.min(Math.max(confidence, 0.85), 0.95);
  let severity: OperationalSeverity = 'info';

  for (const t of traces) {
    if (t.input?.entity === 'sla_calc' && t.output?.data?.breached) {
      severity = 'high';
    } else if (
      t.input?.entity === 'service_credit_calc' &&
      t.output?.data?.credit_amount_inr > 0
    ) {
      severity = 'low';
    }
  }

  return {
    answerState: 'verified',
    confidence: finalConf,
    operationalSeverity: severity,
    escalationRequired: false,
    verification: 'not_required',
    workflowComplete: true,
  };
}
