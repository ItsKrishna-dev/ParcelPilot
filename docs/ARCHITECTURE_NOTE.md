# ParcelPilot AI Support Agent -- Architecture Note

## Agent Design
A hand-rolled state machine (`app/agent/orchestrator.py`): plan -> tool_call -> observe ->
confidence_check -> respond | escalate | confirm. We deliberately avoided a heavyweight agent
framework so every transition is auditable and unit-testable in isolation -- a reviewer can
read one file top-to-bottom and see exactly how a decision was reached. The LLM is called
through an OpenAI-compatible tool-calling interface (`app/agent/llm_client.py`) with NVIDIA NIM
as the primary provider and Groq as an automatic fallback, so a rate-limit or outage on one
free-tier provider does not take the agent down.

## Tool Design
Three required tools, each with a Pydantic-validated input/output contract
(`app/agent/schemas.py`) so a malformed model-generated call cannot silently produce a wrong
number:
1. **doc_search** -- hybrid BM25 + pgvector retrieval over the 6 supplied documents, filtered
   to `status='CURRENT'` unless the caller explicitly requests historical policy.
2. **lookup_structured** -- scoped SQL + deterministic calculation functions
   (`app/domain/cancellation.py`, `service_credit.py`, `sla.py`). Access scoping is enforced
   inside this tool via `app/db/repository.py`, never left to prompt instructions.
3. **action_engine** -- two-phase (`confirmed=false` drafts only; `confirmed=true` + the exact
   `pending_action_id` executes) with TTL-bound, single-use pending actions and an audit-log
   write on execution.

## Document and Structured-Data Handling
Documents are parsed from the original PDFs at ingestion time (`app/ingestion/pdf_loader.py`),
not pre-converted to Markdown, so the pipeline still works if the grader substitutes a
differently formatted PDF. Structured data (accounts/orders/tickets) loads directly from the
supplied workbook (`app/ingestion/load_workbook.py`). All "current time" logic reads a single
injected `DATASET_SNAPSHOT_TIME` constant (`app/config.py`) -- never the real wall clock --
so calculations stay reproducible against the fixed 2026-08-16 11:00 IST snapshot.

## Source Reliability and Conflict Handling
Authority precedence (signed agreement > current SOP > current support policy > current
product docs > deprecated docs > historical tickets) is encoded as **data** in a
`source_authority_rules` table (`app/db/models.py`, resolved by
`app/retrieval/source_authority.py`), not as if/else branches in Python or as prompt text
alone. This makes precedence auditable, unit-testable (`tests/test_source_authority.py`), and
updatable by a policy admin without a code deploy. Deprecated documents are hard-filtered out
of retrieval by default. Historical ticket `historical_resolution` text is always rendered
with an "unverified historical note" label and is never used to compute a fee/credit/SLA
number -- confirmed by `TKT-450`/`TKT-451` in the sample data, both of which contain guidance
that contradicts the current contract/product truth.

## Access Control
Enforced in two independent layers: (1) `app/db/repository.py` filters every query by the
caller's `account_id` for `role=customer`; (2) native Postgres Row-Level Security policies
(`app/db/rls_policies.sql`) enforce the same boundary at the database engine, so a bug in layer
(1) cannot leak cross-account data. Internal roles (`support_agent`, `manager`) get broader
read access, but manager-only actions (e.g. confirming a service credit above
`MANAGER_APPROVAL_THRESHOLD_INR`) are gated the same way.

## Major Technical Trade-offs
- **Hand-rolled orchestrator vs. LangChain/LangGraph:** chose auditability and test coverage
  over framework convenience, at the cost of some boilerplate (tool dispatch, message
  formatting) we'd otherwise get for free.
- **Local embeddings vs. hosted embedding API:** `sentence-transformers` runs locally, so
  retrieval has zero external dependency and zero per-request cost, at the cost of slightly
  lower embedding quality than a large hosted model.
- **Postgres RLS as a second enforcement layer:** adds setup complexity (session variables,
  policy SQL) for a meaningful reliability guarantee -- multi-tenant leakage is blocked even if
  the application-layer filter has a bug.
- **Simple whitespace chunker vs. sentence-aware NLP chunking:** the source documents are 1-2
  pages each, so a naive sliding window chunker is sufficient and avoids an extra NLP
  dependency; this would need revisiting for longer documents.
- **Statistical anomaly detection (z-score/EWMA) vs. an LLM-generated "insights" summary:** the
  proactive dashboard is a scheduled batch computation, not an LLM call -- cheaper,
  deterministic, and easier to trust than a model narrating "what looks unusual."
