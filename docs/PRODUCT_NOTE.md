# ParcelPilot AI Support Agent -- Product Note

## 1. Product vision

ParcelPilot is a trustworthy support and operations assistant for a B2B logistics platform. It is designed to help customers receive fast answers about their own shipments and help authorised support teams investigate issues across accounts, tickets, policies, contracts, and operational data.

The product is not positioned as a generic chatbot. Its differentiator is controlled decision support: it combines natural-language interaction with source-aware retrieval, contract-aware deterministic calculations, tenant-scoped data access, explicit uncertainty, and confirmation before any state-changing action.

The assistant is useful because it reduces the manual effort of searching multiple systems while avoiding the most damaging support failure: confidently giving a numerically or contractually wrong answer.

## 2. Users and jobs to be done

### Customer

A customer wants to:

- Understand whether a shipment can be cancelled.
- Know whether a cancellation fee applies.
- Check service-credit eligibility.
- Understand a delayed or inconsistent shipment status.
- Ask about plan capabilities and support response expectations.
- Receive an answer scoped only to their own account.

### Support agent

An internal support agent wants to:

- Investigate an order or ticket quickly.
- See the applicable account contract.
- Apply the correct current policy or SOP.
- Identify known product issues before escalating a suspected defect.
- Check SLA risk.
- Prepare an escalation or follow-up action without accidentally executing it.

### Manager / operations lead

A manager wants to:

- Review proactive issue signals.
- See tickets approaching or exceeding SLA.
- Identify issues affecting multiple customers.
- Review escalation activity and audit evidence.
- Govern future policy and knowledge-base changes.

## 3. Core product capabilities

### Grounded customer and operations chat

The React dashboard provides role-aware chat experiences for customer, support-agent, and manager sessions. Each response can expose its tool trace, evidence, confidence, and answer state without forcing every user to read raw technical details.

The initial interface is local and conversational. Obvious greetings and general-help requests do not consume an LLM or retrieval request. Meaningful domain requests still reach the full support workflow, including messages that begin with a greeting such as “Hello, can I cancel ORD-1001?”

### Contract-aware decisions

The system does not apply one global policy to every customer. It checks whether a signed agreement exists and applies contract-specific clauses when relevant.

Examples from the supplied data pack:

- Northstar can cancel a BOOKED shipment before pickup without a fee, even after the default 30-minute window.
- LumenWorks receives a fixed INR 300 failed-pickup credit when the delay is more than four hours and fault conditions are satisfied.
- Beacon Retail and Axis Labs have no supplied custom agreement, so standard current policy/SOP rules apply.

### Deterministic calculations

Fees, service-credit amounts, elapsed delays, eligibility, and SLA outcomes are calculated by deterministic domain functions. The LLM explains the result but does not perform the business arithmetic.

This gives a reviewer a direct, testable answer to the question: “Where did this amount come from?”

### Trust and provenance

Each result can show:

- Source document.
- Current/deprecated status.
- Page number.
- Authority source.
- Contract override indicator.
- Calculation result.
- Verification requirement.
- Escalation requirement.
- Workflow completion state.

A completed verified answer is kept visually distinct from evidence discovered during an incomplete workflow.

### Action safety

The agent can prepare escalations, ticket updates, and follow-up tasks, but an action is not executed simply because the LLM suggested it.

The product uses:

```text
prepare draft
  -> show exact action to user
  -> explicit confirmation
  -> execute once
  -> write audit log
```

This avoids accidental mutations and duplicate actions caused by retries or double-clicks.

## 4. Additional client problem selected: proactive issue detection

The assessment asks what broader problem ParcelPilot should solve beyond reactive chat. We selected **proactive issue detection**.

A reactive support bot waits for a customer to ask a question. An operations team also needs to know what is becoming urgent before every affected customer opens a ticket.

The system adds internal proactive signals for:

### Ticket-volume anomalies

Tickets are grouped into product areas and compared against recent baseline activity using a statistical spike detector. This can surface a sudden concentration of bulk-upload, status, security, or outage complaints.

### SLA risk

Open tickets are evaluated against the same contract-aware SLA logic used by the chatbot. This avoids a dashboard showing a different SLA deadline from the support assistant.

### Cross-account correlations

Known-issue matches are compared across accounts. If the same issue appears for multiple customers during a short window, the system can surface it as a possible product-wide incident rather than leaving agents to discover the pattern manually.

### Why this approach

The proactive layer intentionally uses deterministic/statistical logic instead of asking an LLM to invent an operational narrative. This makes alerts easier to explain, test, schedule, and trust.

## 5. Trust model and product behavior

The product treats reliability as a workflow property, not merely a model-quality property.

### Source precedence

```text
signed account agreement
  > current cancellation/service-credit SOP
  > current support policy
  > current product operations guide
  > deprecated documents for historical requests only
  > historical ticket resolutions as unverified context
```

### Uncertainty behavior

The system should answer directly when authoritative evidence and required structured data are available. It should ask for verification or recommend escalation when:

- A required timestamp is missing.
- Fault attribution is unknown.
- Sources conflict without a resolvable precedence.
- An account/order/ticket cannot be found.
- A provider or tool fails.
- The workflow budget is exhausted.

The desired product behavior is not “always answer.” It is “answer when justified, and make uncertainty visible when not.”

### Privacy behavior

Customers are restricted to their own account in the data/tool layer. A customer prompt cannot be used to retrieve another customer's orders, tickets, or agreement. Internal support roles receive broader access according to the mock role model.

### Conversation behavior

Simple greetings are not treated as failed support questions. A greeting receives a local conversational response without false confidence, severity, evidence, or escalation labels. Ambiguous messages are handled conservatively; real domain content always reaches the support workflow.

## 6. Current assessment scenarios

The current product can demonstrate these high-value scenarios:

| Scenario | Product result |
|---|---|
| Northstar asks about ORD-1001 cancellation | Contract override, ALLOWED_NO_FEE, INR 0 |
| LumenWorks asks about ORD-2001 cancellation | Standard SOP after contract confirms no waiver, INR 250 fee |
| LumenWorks asks about ORD-2002 credit | 4.5-hour delay exceeds four-hour contract threshold, fixed INR 300 credit |
| SwiftShip remains BOOKED after pickup | KI-211 webhook delay, verify carrier status or wait up to 20 minutes |
| Large Growth CSV fails | KI-208 intermittent failure above approximately 3,000 rows; split upload below that size |
| Customer requests another account's orders | Safe access restriction; no cross-account data returned |
| Agent asks to escalate a ticket | Draft shown first; explicit confirmation required before execution |

## 7. Prioritized future roadmap

### Priority 1: real identity and tenant security

Replace mock sessions with OIDC/JWT authentication, tenant claims, role management, session expiry, and production-grade authorization. This is the most important prerequisite for handling real customer data.

### Priority 2: governed Knowledge Administration

Add a manager-only document workflow:

```text
upload
  -> validate
  -> extract/chunk/embed
  -> pending review
  -> manager activation
  -> active retrieval source
```

A document should never become authoritative merely because a user uploaded it. The workflow should support activation, rejection, deprecation, supersession, provenance, and audit history.

### Priority 3: production retrieval and evaluation

Move semantic retrieval to SQL-side pgvector similarity search at larger corpus sizes, retain keyword retrieval for exact policy terms, and measure:

- recall of authoritative clauses
- deprecated-source exclusion
- agreement precedence accuracy
- evidence sufficiency
- answer/tool consistency

### Priority 4: complete business-calendar SLA logic

Implement time-zone-aware business calendars, weekends, holidays, 24x7 coverage, after-hours exclusions, and account-specific support schedules.

### Priority 5: live operational integrations

Connect carrier status systems, ticketing systems, and event/webhook streams so the assistant can distinguish a stale snapshot from a current operational state.

### Priority 6: human feedback and verified answers

Capture human-reviewed resolutions in a curated verified-answer store. Raw historical tickets should remain untrusted unless a human explicitly validates them.

### Priority 7: streaming and observability

Add streaming progress events, structured logs, traces, provider health metrics, retrieval metrics, token usage, latency budgets, and alerting.

## 8. Intentionally left out of this submission

The following were intentionally excluded or simplified to keep the assessment focused and reliable:

- Real OAuth/JWT authentication; mock authentication is used as permitted by the brief.
- Production carrier integrations; the supplied workbook snapshot is used.
- Full business-calendar and holiday-aware SLA calculation.
- Fully learned ticket-severity classification; the current proactive layer uses conservative heuristics/statistical logic.
- Token-by-token streaming.
- Production distributed job queues and workers.
- Real external ticketing/escalation integrations; the action engine is mocked locally.
- Automatic arbitrary document activation; future knowledge expansion must be manager-governed.
- Hosted deployment in the current development phase; local reproducibility was prioritized first.

These exclusions are deliberate scope decisions rather than hidden gaps. Each is documented with a clear production path.

## 9. Success metrics

### Primary metric: human-validated resolution rate

```text
Correctly resolved eligible requests without unnecessary escalation
---------------------------------------------------------------
All eligible requests reviewed by humans
```

This measures whether the product is useful without rewarding unsafe guessing. It captures:

- Correct answers.
- Appropriate use of deterministic tools.
- Appropriate escalation.
- Avoidance of unnecessary human work.

### Safety guardrail metrics

The following should be treated as hard guardrails:

- Cross-account data leakage: 0.
- State-changing actions without confirmation: 0.
- Current-answer use of deprecated policy: 0.
- Unsupported fee/credit/SLA calculations: 0.
- Unlogged successful state-changing actions: 0.

### Supporting operational metrics

- Median time to grounded answer.
- P95 answer latency.
- Retrieval latency.
- Tool-call correctness.
- Evidence sufficiency rate.
- Escalation precision.
- Provider failure rate.
- Rate-limit frequency.
- SLA-risk detection precision.

## 10. Demo narrative

The five-minute demonstration should follow a compact story:

1. Start with the problem: support agents manually search policies, agreements, product docs, tickets, and operational data.
2. Show the architecture and emphasize that the LLM orchestrates but deterministic tools decide.
3. Demonstrate Northstar ORD-1001 and the signed-agreement override.
4. Demonstrate LumenWorks ORD-2002 and the contract-specific INR 300 credit.
5. Demonstrate KI-211 and evidence-aware product troubleshooting.
6. Demonstrate account isolation or the confirmation-before-action flow.
7. Show the proactive issue-detection view.
8. Close with the trust principle: the system answers when evidence supports it and escalates when it does not.

## 11. Product conclusion

ParcelPilot is intentionally more than a chat surface. It is a controlled support decision layer combining:

```text
natural-language interaction
+ source-aware retrieval
+ contract-aware policy resolution
+ deterministic calculations
+ account-scoped data access
+ uncertainty and escalation handling
+ confirmation-protected actions
+ proactive operational signals
```

The product's long-term value is not just faster text generation. It is reducing support effort while making policy decisions more explainable, reproducible, and safe to act on.
