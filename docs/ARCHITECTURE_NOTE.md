# ParcelPilot AI Support Agent -- Architecture Note

## 1. Purpose and scope

ParcelPilot is an AI support and policy-verification system built for the CalQuity AI Engineer assessment. It assists customers and authorised ParcelPilot support/operations staff with shipment cancellations, service credits, support SLAs, order/ticket investigation, known product issues, and escalation preparation.

The system is intentionally designed as a **controlled decision-support agent**, not an unrestricted autonomous agent. The LLM handles natural-language understanding, planning, tool selection, and answer composition. It does not become the authority for fees, credits, SLA deadlines, permissions, or state-changing actions.

The supplied assessment pack is the baseline information source:

- Six PDF documents covering current/deprecated policies, SOPs, product operations, and customer agreements.
- `ParcelPilot_Assessment_Data.xlsx` containing accounts, orders, tickets, and the dataset snapshot time.

The architecture supports future controlled expansion, but uploaded or newly added documents must not automatically become authoritative without validation, classification, and approval.

## 2. High-level architecture

```text
+---------------------------+
| React + TypeScript UI     |
| Customer / Agent / Manager|
+-------------+-------------+
              |
              | Authorization: Bearer <mock session>
              v
+---------------------------+
| FastAPI API layer         |
| validation / auth / CORS  |
+-------------+-------------+
              |
              v
+---------------------------+
| Conversation Router       |
| greeting / help / support |
+------+------+-------------+
       |      |
       |      +------------------------------+
       |                                     |
       v                                     v
+-------------+                    +----------------------+
| Local safe  |                    | Agent Orchestrator    |
| response    |                    | bounded tool loop    |
+-------------+                    +---+--------+---------+
                                      |        |         |
                                      v        v         v
                              +-----------+ +--------+ +-----------+
                              | doc_search| | lookup | | action    |
                              | retrieval | | data + | | engine    |
                              |           | | calc   | | confirm   |
                              +-----+-----+ +---+----+ +-----+-----+
                                    |           |            |
                                    +-----------+------------+
                                                |
                                                v
                              +-------------------------------+
                              | PostgreSQL + pgvector         |
                              | accounts, orders, tickets    |
                              | documents, chunks            |
                              | authority rules, contracts   |
                              | actions, audit log           |
                              +-------------------------------+
                                                ^
                                                |
                              +-------------------------------+
                              | PDF/XLSX ingestion pipeline   |
                              | extraction / chunking / embed |
                              +-------------------------------+

LLM: Groq primary -> NVIDIA NIM fallback
Embeddings: local sentence-transformers, cached/stored
```

## 3. Request lifecycle

A normal support request follows this lifecycle:

```text
HTTP request
  -> authenticate mock session
  -> validate message
  -> classify conversational intent
  -> route obvious greeting/help locally, or continue
  -> identify required calculation and document types
  -> ask LLM for a tool call
  -> validate tool arguments with Pydantic
  -> inject session scope into tool execution
  -> execute retrieval / structured lookup / deterministic calculation
  -> append compact tool result to model context
  -> repeat within bounded iteration limit
  -> validate final answer state
  -> answer, request verification, escalate, or prepare action confirmation
```

The orchestration loop is bounded by a configurable maximum number of tool iterations. A budget exhaustion is represented as `workflow_incomplete`, not silently presented as a verified answer.

## 4. Conversational routing

Not every input is a support request. The system contains a pre-agent intent router (`agent/intent_router.py`) that prevents trivial conversation from consuming retrieval and LLM resources.

The router uses a layered approach:

1. **Deterministic fast path** for unambiguous, low-risk inputs (`hello`, `thanks`, `good morning`) matched by anchored patterns, not a giant keyword list.
2. **Domain-content override** -- regex/entity detection for order IDs (`ORD-\\d+`), ticket IDs (`TKT-\\d+`), account IDs, known-issue IDs (`KI-\\d+`), and cancellation/credit/SLA/action vocabulary. Any domain signal forces routing to the full agent regardless of a leading greeting (`Hello, can I cancel ORD-1001?` -> full agent).
3. **Conservative default** -- ambiguous or unrecognized messages route to the full agent rather than silently receiving a canned response. Uncertainty resolves toward doing real work, never guessing that the message is small talk.

A local conversational response has:

```json
{
  "answer_state": "conversational",
  "confidence": null,
  "escalated": false,
  "tool_trace": [],
  "evidence": [],
  "workflow_complete": true
}
```

This prevents a harmless `hello` from being labelled `Needs Verification` or `Escalation Required`, while preserving the full workflow for meaningful requests.

## 5. Agent and tool design

### 5.1 Document retrieval tool

`doc_search` searches current policies, SOPs, product operations documentation, and account-specific agreements.

Its safety and performance controls include:

- Exclude deprecated documents by default.
- Apply account scope to agreement documents.
- Route document types according to intent:
  - cancellation -> SOP + agreement
  - service credit -> SOP + agreement
  - SLA -> support policy + agreement
  - product status/webhook/bulk upload -> product operations
- Return compact metadata: document ID, filename, status, date, page, score, and truncated text.
- Deduplicate overlapping chunks.
- Cache retrieval structures and avoid re-embedding the full corpus on each request.
- Preserve provenance so the UI can explain which source influenced the response.

### 5.2 Structured lookup and deterministic calculation tool

`lookup_structured` handles accounts, orders, tickets, and deterministic calculations.

The calculation entities are:

- `cancellation_calc`
- `service_credit_calc`
- `sla_calc`

The LLM must not calculate business outcomes itself. The tool layer loads the relevant records, retrieves structured contract overrides, resolves authority, and calls deterministic domain functions.

Examples:

```text
ORD-1001 -> cancellation_calc -> ALLOWED_NO_FEE -> INR 0
ORD-2001 -> cancellation_calc -> ALLOWED_WITH_FEE -> INR 250
ORD-2002 -> service_credit_calc -> ELIGIBLE -> INR 300
```

The tool rejects unsupported filters instead of silently ignoring them. This prevents a customer query such as `account_name=LumenWorks` from being silently converted into a query over the current session's records.

### 5.3 State-changing action tool

`action_engine` supports mocked actions such as:

- Create escalation.
- Update ticket status.
- Create follow-up task.

Actions follow a two-phase process:

```text
prepare draft
  -> return pending_action_id
  -> user explicitly confirms
  -> verify exact pending action, actor, scope, expiry, and single-use status
  -> execute once
  -> write audit log
```

The first call with `confirmed=false` does not mutate business state. Replayed pending IDs are rejected to provide idempotency during retries or double-clicks.

## 6. Deterministic domain logic

### Cancellation

The cancellation engine handles:

- DRAFT: no fee.
- BOOKED before pickup: default 30-minute free window, then INR 250 unless contract overrides.
- PICKED_UP: cannot cancel; use return-to-origin.
- DELIVERED: cannot cancel.
- Missing timestamps or unknown statuses: verification required.

### Service credits

The service-credit engine handles:

- Delay relative to the scheduled pickup-window end.
- Carrier-fault and customer-fault conditions.
- Default lower-of-INR-500-or-10%-of-fee rule.
- Contract-specific threshold, fixed amount, and cap overrides.
- Manager approval above the configured INR threshold.
- Missing fault/timing information as `NEEDS_VERIFICATION`.

For a still-BOOKED order with no actual pickup timestamp, the fixed dataset snapshot is used as the reference time when the order record establishes that pickup has not occurred. This correctly evaluates `ORD-2002` as 4.5 hours late at the assessment snapshot.

### SLA

SLA calculation selects contract targets when structured contract rules contain them; otherwise it falls back to the current Support Policy by plan and severity. The current assessment implementation uses simplified minute conversions for business-hour/day targets, documented as a limitation.

## 7. Contract rules and source authority

Agreement clauses are extracted into `contract_rules` rather than encoded as account-ID conditionals.

Supported rule types include:

- `cancellation_fee_waived`
- `cancellation_free_window_minutes`
- `cancellation_fee_inr`
- `service_credit_delay_threshold_hours`
- `service_credit_fixed_amount_inr`
- `service_credit_monthly_cap_inr`
- `sla_p1_minutes`
- `sla_p2_minutes`
- `sla_p3_minutes`

Every extracted rule retains:

- account ID
- source document ID
- clause type
- rule key
- value
- source text
- effective date

The source precedence model is:

```text
signed customer agreement
  > current Cancellation & Service Credit SOP
  > current Support Policy
  > current Product Operations Guide
  > deprecated documents for explicit history only
  > historical ticket resolutions as unverified context
```

This explains why:

- Northstar's signed agreement waives the late cancellation fee.
- LumenWorks receives a fixed INR 300 credit after its four-hour threshold.
- Beacon Retail falls back to the standard SOP.
- Axis Labs falls back to the standard Enterprise policy.
- TKT-450 and TKT-451 cannot override current policy or contract truth.

## 8. Document ingestion

The ingestion pipeline reads the original PDFs directly:

```text
PDF
  -> page text extraction
  -> normalization
  -> overlapping chunks
  -> local embedding generation
  -> documents/doc_chunks persistence
  -> optional contract-rule extraction
```

The workbook pipeline reads:

```text
README -> snapshot time and notes
accounts -> accounts table
orders -> orders table
tickets -> tickets table
```

Account reloads use upsert behavior so contract documents are not broken by deleting referenced account rows. Dependent workbook records are replaced in foreign-key-safe order.

## 9. Retrieval performance

The first implementation re-embedded every document chunk for every request, causing several-second retrieval latency. The optimized implementation avoids that pattern.

Performance controls:

- Build/cache BM25 structures.
- Load local embedding model once when semantic retrieval is enabled.
- Embed only the query, not the complete corpus, during a request.
- Reuse stored vectors for future pgvector SQL similarity search.
- Limit top-k results.
- Deduplicate chunks.
- Truncate long excerpts.
- Route to the narrowest relevant document types.
- Keep structured calculations independent from retrieval.

Observed repeated retrieval performance for the small assessment corpus reached low-millisecond latency after cache warm-up, while the first call may still include one-time initialization overhead.

## 10. Access control and privacy

The system uses two layers:

### Application layer

`db/repository.py` enforces session-level account scope before data reaches the LLM. Customer sessions can only access their own account. Unsupported filters are rejected.

### PostgreSQL layer

PostgreSQL RLS policies use transaction-local settings:

```text
parcelpilot.user_role
parcelpilot.account_id
```

The names are deliberately namespaced and avoid PostgreSQL reserved identifiers such as `current_role`. The application sets these values with transaction-local `set_config()` calls.

Customer data from another account must never enter:

- tool output
- model context
- evidence response
- frontend response

Internal support-agent and manager sessions have broader access through the existing mock role model. Authentication remains mocked for the assessment and is explicitly documented as a production limitation.

## 11. Confidence and answer states

The system separates:

| Field | Meaning |
|---|---|
| Confidence | Strength of support for the answer |
| Operational severity | Seriousness of the underlying issue |
| Verification | Whether additional confirmation is advisable/required |
| Escalation | Whether a human must intervene |
| Workflow completion | Whether the intended tool workflow completed |
| Answer state | Stable overall response category |

Important answer states include:

- `conversational`
- `verified`
- `needs_verification`
- `workflow_incomplete`
- `access_denied`
- `provider_unavailable`
- `out_of_scope`
- `error`

Decision cards are rendered only when the response is verified and the workflow is complete. If a tool budget is exhausted after evidence was collected, the UI shows evidence as discovered but not confirmed—not as a verified decision.

## 12. LLM provider strategy

Groq is the preferred provider because it offers fast OpenAI-compatible inference and fits the free-tools constraint. The default model is configurable through `.env` and currently uses `openai/gpt-oss-20b` to reduce token pressure.

NVIDIA NIM is supported as an optional fallback through the same adapter interface. Provider aliases such as `nvidia`, `nvidia_nim`, and `nim` normalize to a canonical provider name.

Provider failures are handled explicitly:

- 401: configuration/authentication error.
- 404: invalid/unavailable model.
- 429: bounded rate-limit handling.
- timeout/network failure: provider failure.
- both providers unavailable: controlled escalation response.

API keys are never included in logs or responses.

## 13. Frontend architecture

The React + TypeScript + Vite frontend is organized into:

```text
src/api/          typed API clients
src/components/   reusable UI components
src/features/     feature-level screens and state
src/lib/          trust/error/formatting helpers
src/types/        shared response and state types
```

The dashboard supports customer, support-agent, and manager contexts. It displays:

- Role/session context.
- Chat responses.
- Confidence and answer state.
- Decision cards.
- Evidence and tool trace.
- Loading/error states.
- Proactive insights.
- Confirmation cards for pending actions.

The initial empty chat state and obvious conversational responses do not call the LLM. Suggested support prompts call the real API.

## 14. Major technical trade-offs

| Decision | Benefit | Trade-off |
|---|---|---|
| Groq primary | Fast, free-tier-compatible inference | TPM limits require compact context and bounded output |
| NVIDIA NIM adapter | Optional free/provider fallback | Requires separate credentials and model availability |
| Local embeddings | No paid embedding API | Model startup and local resource usage |
| BM25/cache-first retrieval | Very fast for small corpus | Semantic recall needs SQL-side pgvector at larger scale |
| PostgreSQL + pgvector | Structured storage, vector readiness, RLS | More setup than SQLite |
| Hand-rolled orchestrator | Transparent state machine and easy testing | More orchestration code to maintain |
| Deterministic calculators | Correct, reproducible decisions | Every rule variant must be explicitly modeled |
| ContractRule extraction | No account-ID business logic, auditable provenance | Extraction patterns need review for new agreement formats |
| Mock authentication | Fast assessment implementation | Not production security |
| Two-phase actions | Prevents accidental and duplicate writes | Requires an extra confirmation step |
| Local intent fast path | Saves latency/tokens for obvious conversation | Ambiguous messages need conservative routing |

## 15. Current limitations and next steps

Known limitations:

- Authentication is mocked.
- SLA business-calendar and holiday handling is simplified.
- Agreement extraction is pattern-based for the supplied documents.
- SQL-side pgvector similarity search is the next retrieval-scale improvement.
- Chat is turn-based rather than token-streamed.
- Carrier status is based on the supplied snapshot rather than live integrations.
- The action engine is mocked locally for the assessment.

Next production steps:

1. Replace mock authentication with OIDC/JWT and tenant claims.
2. Add manager-governed document administration with review/activation states.
3. Add SQL-side pgvector retrieval and retrieval evaluation metrics.
4. Add real business calendars and time zones.
5. Integrate carrier webhooks and ticketing systems.
6. Add continuous golden-set evaluation and observability.
7. Add verified human-resolution feedback rather than trusting raw historical tickets.
