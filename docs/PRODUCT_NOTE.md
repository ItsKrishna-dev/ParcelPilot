# ParcelPilot AI Support Agent -- Product Note

## Additional Client Problem Chosen: Proactive Issue Detection
We built an internal insights endpoint (`app/api/insights.py`, `GET /internal/insights`,
restricted to `support_agent`/`manager` roles) backed by three deterministic, non-LLM
computations:
- **Ticket-volume anomaly detection** (`app/proactive/anomaly_detection.py`): rolling z-score
  on ticket counts per product-area against a 14-day baseline, flagging genuine spikes (e.g. a
  sudden run of bulk-upload complaints) rather than relying on keyword clustering alone.
- **SLA breach prediction** (`app/proactive/sla_predictor.py`): reuses the exact same
  contract-aware `app/domain/sla.py` logic the chatbot uses, so the dashboard and the chatbot
  can never disagree about what a given account's SLA target is.
- **Cross-account correlation** (`app/proactive/cross_account_correlator.py`): flags when the
  same known-issue tag (e.g. KI-208) appears across multiple accounts within a rolling window,
  surfacing a product-wide incident instead of several seemingly unrelated tickets.

We chose this over "Trust and Reliability" as the *additional* problem because the
source-authority engine, RLS access control, and confidence/escalation gate already built for
the minimum requirements substantially address reliability by construction; proactive
detection is a genuinely new capability layered on top.

## What Else We Would Build for ParcelPilot
1. **Real authentication + role management** (replacing mock auth) -- highest priority before
   any production usage, since customer trust depends on this being airtight, not mocked.
2. **A policy-admin UI over `source_authority_rules`** so a non-engineer can update precedence
   or add a new document type without a deploy -- turns our biggest architectural
   differentiator into an actual product surface.
3. **Streaming responses** in the chat UI so users see tool calls resolve incrementally rather
   than waiting for the full turn.
4. **A feedback loop on escalations** -- when a human resolves an escalation the agent created,
   capture the resolution back into a curated "verified answers" table, so future confidence
   scoring can trust it (unlike raw historical tickets, which we explicitly do not trust today).
5. **Multi-turn session memory** for the internal chatbot so an agent can investigate a ticket
   across several follow-up questions without re-stating context each time.

## What We Intentionally Left Out
- Real OAuth/JWT authentication (mocked per the assessment's explicit allowance).
- A production-grade frontend framework (Next.js/React) -- a static HTML/JS page was
  sufficient to satisfy "simple chat interface... shows which tool is being used" without
  adding a build-toolchain dependency.
- Streaming token-by-token responses -- turn-based responses were enough to demonstrate tool
  use and confirmation flow within the assessment's time constraints.
- A learned/ML-based severity classifier for tickets -- `_guess_severity` in
  `sla_predictor.py` uses keyword heuristics; a trained classifier is a natural next step once
  there's enough labeled ticket history.

## One Metric to Judge Product Usefulness
**Escalation precision**: of all escalations the agent creates, what fraction would a human
reviewer agree were genuinely necessary (vs. cases the agent could have answered directly, or
cases where the agent missed an escalation it should have raised)? This single metric captures
both failure modes the assessment brief explicitly worries about -- a confidently wrong direct
answer (should have escalated but didn't) and an unhelpfully over-cautious agent (escalated
when it had enough evidence to answer) -- in one number the team can track release-over-release.
