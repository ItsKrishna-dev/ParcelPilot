import React from 'react';
import { Bot, AlertTriangle, ShieldCheck, Clock, ShieldAlert, FileText, CheckCircle2, Lock } from 'lucide-react';
import { ChatMessage } from '../../types/ui';
import { Badge } from '../shared/Badge';
import { Card } from '../shared/Card';
import { formatMs } from '../../lib/utils';
import { deriveTrustState } from '../../lib/trustState';
import { CancellationCard } from '../decisions/CancellationCard';
import { ServiceCreditCard } from '../decisions/ServiceCreditCard';
import { SLACard } from '../decisions/SLACard';
import { KnownIssueCard } from '../decisions/KnownIssueCard';
import { PendingActionCard } from '../decisions/PendingActionCard';
import { ToolTraceDrawer } from '../traces/ToolTraceDrawer';

interface MessageCardProps {
  message: ChatMessage;
  sessionId: string;
}

export const MessageCard: React.FC<MessageCardProps> = ({
  message,
  sessionId,
}) => {
  const isUser = message.sender === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end my-3">
        <div className="flex items-start gap-2.5 max-w-2xl">
          <div className="bg-brand-blue/20 text-slate-100 border border-brand-blue/30 rounded-2xl rounded-tr-none px-4 py-3 text-sm shadow-sm">
            <p className="whitespace-pre-wrap leading-relaxed">{message.text}</p>
            <span className="text-[10px] text-brand-blue/70 block text-right mt-1 font-mono">
              {message.timestamp}
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-brand-blue text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-glow-blue">
            U
          </div>
        </div>
      </div>
    );
  }

  const response = message.response;
  if (!response) return null;

  const trustState = deriveTrustState(response, message.text);
  const totalToolLatency = (response.tool_trace || []).reduce(
    (acc, t) => acc + (t.latency_ms || 0),
    0
  );

  // Extract decision payload data from tool_trace
  let cancellationData: any = null;
  let serviceCreditData: any = null;
  let slaData: any = null;
  let pendingActionData: any = null;
  let authoritySource: string | undefined = undefined;

  for (const trace of response.tool_trace || []) {
    const outputData = trace.output?.data;

    if (trace.tool_name === 'lookup_structured') {
      const entity = trace.input?.entity;
      if (entity === 'cancellation_calc' && outputData) {
        cancellationData = outputData;
      } else if (entity === 'service_credit_calc' && outputData) {
        serviceCreditData = outputData;
      } else if (entity === 'sla_calc' && outputData) {
        slaData = outputData;
      }
      if (trace.output?.authority_source) {
        authoritySource = trace.output.authority_source;
      }
    }

    if (trace.output?.pending_action_id) {
      pendingActionData = {
        pendingActionId: trace.output.pending_action_id,
        actionType: trace.input?.action_type || 'action',
        payload: trace.input?.payload || {},
      };
    }
  }

  // Detect KI-211 or webhook delay pattern
  const isKI211 =
    message.text.includes('KI-211') ||
    message.text.toLowerCase().includes('booked after') ||
    response.answer.includes('KI-211') ||
    response.answer.toLowerCase().includes('webhook delay') ||
    (response.evidence &&
      response.evidence.some((e) => e.text.includes('KI-211')));

  const isVerifiedWorkflow =
    trustState.answerState === 'verified' && trustState.workflowComplete;

  return (
    <div className="flex justify-start my-4">
      <div className="flex items-start gap-3 max-w-3xl w-full">
        <div className="w-8 h-8 rounded-full bg-dark-800 text-brand-blue border border-brand-blue/30 flex items-center justify-center text-xs font-bold shrink-0 shadow-glow-blue mt-1">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0">
          <Card className="bg-dark-900/90 border-slate-800 shadow-glass-md">
            {/* Header Semantic Trust Bar */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5 mb-3">
              <div className="flex flex-wrap items-center gap-1.5 text-xs">
                {trustState.answerState === 'conversational' ? (
                  <Badge variant="blue" className="flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-brand-blue" />
                    Conversational
                  </Badge>
                ) : (
                  <>
                    {/* Answer State Badge */}
                    {trustState.answerState === 'verified' && (
                      <Badge variant="emerald" className="flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        {isKI211 ? 'Verified Explanation' : 'Verified Decision'}
                      </Badge>
                    )}

                    {trustState.answerState === 'needs_verification' && (
                      <Badge variant="amber" className="flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Needs Verification
                      </Badge>
                    )}

                    {trustState.answerState === 'workflow_incomplete' && (
                      <Badge variant="red" className="flex items-center gap-1">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        Workflow Incomplete
                      </Badge>
                    )}

                    {trustState.answerState === 'access_denied' && (
                      <Badge variant="slate" className="flex items-center gap-1">
                        <Lock className="w-3.5 h-3.5" />
                        Access Restricted
                      </Badge>
                    )}

                    {trustState.answerState === 'provider_unavailable' && (
                      <Badge variant="red" className="flex items-center gap-1">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        Provider Unavailable
                      </Badge>
                    )}

                    {/* Confidence Badge */}
                    <Badge
                      variant={
                        trustState.confidence >= 0.8
                          ? 'emerald'
                          : trustState.confidence >= 0.5
                          ? 'amber'
                          : 'red'
                      }
                      className="font-mono"
                    >
                      Confidence {Math.round(trustState.confidence * 100)}%
                    </Badge>

                    {/* Severity Badge */}
                    {trustState.operationalSeverity !== 'info' && (
                      <Badge
                        variant={
                          trustState.operationalSeverity === 'critical' ||
                          trustState.operationalSeverity === 'high'
                            ? 'red'
                            : 'amber'
                        }
                      >
                        {trustState.operationalSeverity.toUpperCase()} Severity
                      </Badge>
                    )}

                    {/* Verification / Escalation Badge */}
                    {trustState.verification === 'recommended' && (
                      <Badge variant="amber">Verification Recommended</Badge>
                    )}

                    {trustState.escalationRequired ? (
                      <Badge variant="red" className="flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Escalation Required
                      </Badge>
                    ) : (
                      <Badge variant="emerald" className="hidden sm:inline-flex">
                        Escalation Not Required
                      </Badge>
                    )}

                    {/* Authority Source */}
                    {authoritySource && (
                      <Badge
                        variant={
                          authoritySource.toLowerCase().includes('agreement')
                            ? 'violet'
                            : 'blue'
                        }
                      >
                        {authoritySource}
                      </Badge>
                    )}
                  </>
                )}
              </div>

              <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                {totalToolLatency > 0 && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {formatMs(totalToolLatency)}
                  </span>
                )}
                <span>{message.timestamp}</span>
              </div>
            </div>

            {/* Main Response Text */}
            <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap font-sans mb-3">
              {response.answer}
            </div>

            {/* Access Denied Warning Banner */}
            {trustState.answerState === 'access_denied' && (
              <div className="my-3 p-3 rounded-xl bg-slate-800/80 border border-slate-700 text-xs text-slate-300 flex items-center gap-2">
                <Lock className="w-4 h-4 text-slate-400 shrink-0" />
                <span>
                  Tenant isolation enforced: requested order, ticket, or contract data belongs to another account.
                </span>
              </div>
            )}

            {/* Incomplete Workflow Evidence Preview Banner */}
            {trustState.answerState === 'workflow_incomplete' && (
              <div className="my-3 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 space-y-1">
                <div className="flex items-center gap-2 font-semibold text-red-200">
                  <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
                  <span>Evidence Discovered — Not Yet Confirmed as Final Answer</span>
                </div>
                <p className="text-[11px] text-red-300/90 leading-normal">
                  The workflow ended before final answer completion (tool-call budget reached). Discovered evidence is provided below for human agent review.
                </p>
              </div>
            )}

            {/* Verified Decision Cards (ONLY rendered when workflow is verified & complete) */}
            {isVerifiedWorkflow && (
              <>
                {cancellationData && (
                  <CancellationCard
                    data={cancellationData}
                    authoritySource={authoritySource}
                  />
                )}

                {serviceCreditData && (
                  <ServiceCreditCard
                    data={serviceCreditData}
                    authoritySource={authoritySource}
                  />
                )}

                {slaData && (
                  <SLACard data={slaData} authoritySource={authoritySource} />
                )}

                {isKI211 && (
                  <KnownIssueCard
                    issueId="KI-211"
                    title="SwiftShip pickup webhook delay"
                    status="Verified Known Issue"
                    guidance="Product Operations Guide documents that SwiftShip pickup-confirmation webhooks can arrive up to 20 minutes late. Verify carrier status or wait through the 20-minute delay window before concluding that pickup did not occur."
                    sourceDoc="04_Product_Operations_Guide_and_Known_Issues.pdf"
                  />
                )}

                {pendingActionData && (
                  <PendingActionCard
                    pendingActionId={pendingActionData.pendingActionId}
                    actionType={pendingActionData.actionType}
                    payload={pendingActionData.payload}
                    sessionId={sessionId}
                  />
                )}
              </>
            )}

            {/* Tool Trace & Evidence Drawer */}
            {trustState.answerState !== 'access_denied' && trustState.answerState !== 'conversational' && (
              <ToolTraceDrawer
                toolTrace={response.tool_trace || []}
                evidence={response.evidence || []}
              />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
