# ParcelPilot AI Support Agent -- Architecture Note

## 1. Agent Design & State Machine
The agent implements a lightweight, hand-rolled state machine (`app/agent/orchestrator.py`):
`plan -> tool_call -> observe -> calculation_guard -> confidence_check -> respond | escalate | confirm`.

Heavyweight agent frameworks were deliberately avoided to maintain full auditability and unit-testability of all state transitions. Every decision path, error state, and confidence calculation is transparent and testable without framework magic.

The LLM is invoked through an OpenAI-compatible adapter (`app/agent/llm_client.py`) with Groq (`openai/gpt-oss-20b`) as the primary provider and NVIDIA NIM as an automatic fallback. Free-tier token and rate constraints are managed via concise prompt engineering, bounded 429 retry backoff, and compact tool responses.

## 2. Deterministic Calculation Enforcement
To guarantee financial and policy correctness, the LLM is **never allowed to perform business arithmetic or policy evaluations in prose**.

- **Detection (`app/domain/calculation_requirements.py`):** Automatically detects if an inquiry concerns cancellation eligibility/fees (`cancellation_calc`), failed-pickup service credits (`service_credit_calc`), or SLA response/breach targets (`sla_calc`).
- **Orchestrator Guardrail (`app/agent/orchestrator.py`):** If the LLM attempts to finalize a response before calling the detected calculation tool, the orchestrator intercepts the turn, re-prompts the model with an explicit directive, and ensures the calculation result drives the final output.
- **Pure Python Domain Engines (`app/domain/`):** Pure deterministic arithmetic and edge case logic for:
  - `cancellation.py`: Free DRAFT, 30m BOOKED free window vs INR 250 fee, agreement waivers, PICKED_UP return-to-origin workflows, DELIVERED restrictions.
  - `service_credit.py`: 2h (or agreement-specified 4h) delay thresholds, carrier fault verification, fixed/capped amounts, manager approval thresholds (>INR 1,000). Handles `pickup_actual_at is None` for still-BOOKED shipments using the fixed logical snapshot time.
  - `sla.py`: Target lookup across Enterprise/Growth/Standard tiers and custom agreement overrides, elapsed calculation against ticket creation.

## 3. High-Performance Retrieval Architecture
Retrieval latency was optimized from ~6 seconds down to **under 300ms** through five design improvements:
1. **Query-Only Embedding:** Rather than re-encoding the entire document corpus on every query, `SentenceTransformer` runs once as a thread-safe singleton, encoding solely the query vector (~10ms).
2. **Database Vector Similarity:** Chunks are pre-embedded at ingestion time and stored in `doc_chunks.embedding` (`pgvector`). Semantic matching runs via cosine distance.
3. **BM25 Hybrid Fusion:** In-memory BM25 Okapi scores are combined with semantic similarity using weighted rank fusion (`0.5 * bm25_norm + 0.5 * cosine_sim`).
4. **Document-Type Routing & Truncation:** Document types (`support_policy`, `sop`, `product_ops`, `agreement`) are filtered per tool call, and chunk text is truncated to `RETRIEVAL_MAX_CHUNK_CHARS` (1800) to minimize prompt token overhead.
5. **Deduplication:** Overlapping chunks sharing identical document ID, page, and text prefixes are deduplicated before returning.

## 4. ContractRule Data-Driven Overrides
To eliminate hardcoded account IDs in business logic:
- `ContractRule` records are stored in PostgreSQL (`app/db/models.py`) and extracted deterministically from agreement PDFs (`app/ingestion/contract_rules.py`).
- Supported rule types:
  - `cancellation_fee_waived`, `cancellation_free_window_minutes`, `cancellation_fee_inr`
  - `service_credit_delay_threshold_hours`, `service_credit_fixed_amount_inr`, `service_credit_monthly_cap_inr`
  - `sla_p1_minutes`, `sla_p2_minutes`, `sla_p3_minutes`
- `resolve_contract_overrides()` (`app/domain/contract_rules.py`) converts database rows into typed overrides, ensuring domain logic remains completely account-agnostic.

## 5. Source Reliability and Authority Precedence
Precedence rules are encoded as relational data in `source_authority_rules` (`app/db/models.py`, resolved by `app/retrieval/source_authority.py`):
1. **Signed Customer Agreement** (Highest authority for account)
2. **Current Cancellation & Service Credit SOP**
3. **Current Support Policy**
4. **Product Operations Guide & Known Issues**
5. **Deprecated Documents** (Excluded by default; marked with explicit warning if historical policy requested)
6. **Historical Ticket Resolutions** (Treated as unverified context, never as policy authority)

## 6. Access Control & Row-Level Security (RLS)
Access control is enforced in two independent layers:
1. **Application Repository Layer (`app/db/repository.py`):** Every query filters by `session.account_id` when `role == "customer"`.
2. **PostgreSQL Native RLS (`app/db/rls_policies.sql`):** Uses transaction-local session settings `parcelpilot.user_role` and `parcelpilot.account_id` via `set_config(..., true)`. Even if an application bug omitted a where clause, the database engine enforces tenant isolation.

## 7. State-Changing Action Workflow
State-changing actions (`create_escalation`, `update_ticket_status`, `create_follow_up_task`) follow a structural **two-phase commit**:
- `confirmed=false`: Creates a draft and returns a TTL-bound `pending_action_id` without executing or modifying core entities.
- `confirmed=true`: Executes only when the user explicitly confirms with the exact `pending_action_id`. Consumes the action once (idempotency guard) and records the event in `audit_log`.

## 8. Error Handling & API Contract
The API guarantees that expected agent failures (provider rate limits, missing records, invalid tool arguments, access denials) **never produce HTTP 500 crashes**:
- Every response conforms to `ChatResponse`:
  ```json
  {
    "answer": "string",
    "confidence": 0.95,
    "escalated": false,
    "tool_trace": [],
    "evidence": []
  }
  ```
- All tool latencies (`latency_ms`) are recorded in the trace.
## 9. Stage 2 Knowledge Administration & Document Governance
Stage 2 introduces a secure, manager-governed document ingestion workflow (`app/api/admin_documents.py`, `app/ingestion/doc_processor.py`):

1. **Upload Lifecycle & State Machine:**
   `Manager Upload PDF -> Validation -> PROCESSING -> Text extraction, chunking, embedding -> Proposed metadata -> PENDING_REVIEW -> Manager Review -> ACTIVATE / REJECT / DEPRECATE / SUPERSEDE -> Only ACTIVE documents influence answers`
2. **Document State Machine:**
   `DRAFT`, `PROCESSING`, `PENDING_REVIEW`, `ACTIVE`, `REJECTED`, `SUPERSEDED`, `DEPRECATED`, `FAILED`.
   - Only `ACTIVE` (or seeded `CURRENT`) documents are queried in `hybrid_search` for normal user queries.
   - `PENDING_REVIEW`, `PROCESSING`, `DRAFT`, `REJECTED`, `SUPERSEDED`, and `FAILED` documents are strictly excluded from retrieval.
   - `DEPRECATED` documents are excluded unless `allow_deprecated=True` is explicitly specified for historical inquiries.
3. **File Security & Local Storage:**
   - Saved to `backend/storage/documents/doc_<uuid>.pdf` (excluded from git).
   - Validation: PDF header magic bytes (`%PDF-`), 10MB max size, sanitized filenames (preventing path traversal).
   - Checksum: SHA-256 hash calculated upon upload; duplicate active uploads are rejected.
   - Content handling: PDF text extracted via `pypdf`, chunked, embedded locally. Content treated as untrusted text (never executed).
4. **Contract Rule Extraction for Agreement Uploads:**
   - Uploaded customer agreements (`document_type == "agreement"`) run structured contract rule extraction (`app/ingestion/contract_rules.py`) upon activation, dynamically inserting `ContractRule` records into PostgreSQL without modifying Python code.
5. **Auditing & Governance:**
   - Every lifecycle event (`document_uploaded`, `document_ingestion_started`, `document_ingestion_succeeded`, `document_ingestion_failed`, `document_activated`, `document_rejected`, `document_deprecated`, `document_superseded`, `document_reprocessed`) records an entry in `audit_log`.

## 10. Conversational Pre-Agent Intent Router
To prevent simple conversational statements (e.g. "hello", "thanks") from routing through the expensive LLM RAG/tool-calling workflow and producing false escalations, a hybrid intent routing layer is integrated before the orchestrator's `run_turn()` call:

1. **Pre-Agent Intent Router flow:**
   - **Normalization:** Cleans text by lowercasing and stripping punctuation.
   - **Deterministic Fast Path:** Inspects high-precision greeting, acknowledgement, and help patterns. Obvious greetings bypass the RAG agent instantly (0ms latency, zero token consumption).
   - **Domain-Content Safety Override:** Checks for order/ticket/account/KI IDs or domain keywords (SLA, cancellation, credit, stuck, status, etc.). Any matching signal immediately forces routing to the main RAG agent.
   - **Semantic Fallback:** Ambiguous short inputs run semantic comparison against prototype embeddings (greeting, acknowledgement, help) using the cached local `SentenceTransformer` model.
   - **Conservative Thresholding:** Requires a similarity score of `>= 0.65` and a score margin of `>= 0.08` over the second-best category. If criteria are unmet, defaults to `UNKNOWN` (routed to the main agent).
2. **conversational Response Contract:**
   - Bypassed conversational messages return a response structure with `answer_state="conversational"`, `confidence=null`, `workflow_complete=true`, and empty `tool_trace` and `evidence`.
   - General help queries return role-aware capability responses (customized for Customer, Support Agent, and Manager roles).
3. **Frontend Trust-State Synchronization:**
   - When `answer_state === "conversational"`, the UI displays a `Conversational` badge, renders the answer text, and suppresses all policy confidence values, severity tags, escalation warning headers, decision cards, evidence lists, and tool traces.
