# ParcelPilot AI Support Agent -- Product Note

## 1. Core Trust & Reliability Architecture
In enterprise B2B logistics, automated responses involving monetary calculations (cancellation fees, failed-pickup credits) and operational guarantees (support SLAs) carry real financial and legal liability. A confidently wrong AI response is an unacceptable risk.

ParcelPilot achieves enterprise reliability through five design principles:
1. **Deterministic Calculation Guardrails:** The LLM is structurally prevented from performing calculations in prose. Every fee, credit, and SLA check is delegated to deterministic Python domain engines.
2. **Data-Driven Source Authority Hierarchy:** Overrides (such as signed customer contracts) supersede standard SOPs and policy. Deprecated documents are strictly filtered out for current requests, and historical tickets are treated solely as unverified context.
3. **Multi-Tenant Data Isolation:** Dual-layer access control combines application repository filtering with PostgreSQL Row-Level Security (`parcelpilot.user_role`, `parcelpilot.account_id`).
4. **Two-Phase Action Confirmation:** No state change (escalation, ticket status change, follow-up task) can occur in a single prompt. Actions must be drafted (`confirmed=false`), reviewed by the user, and explicitly executed (`confirmed=true`) with an audit log trail.
5. **Calibrated Confidence & Controlled Escalation:** Ambiguity, missing records, or unverified fault data result in controlled escalation with clear explanatory reasons rather than speculative hallucination.

---

## 2. Proactive Issue Detection
To shift support operations from reactive firefighting to proactive incident management, ParcelPilot provides an internal insights endpoint (`GET /internal/insights`, restricted to `support_agent` and `manager` roles) powered by three deterministic computations:

- **Ticket-Volume Anomaly Detection (`app/proactive/anomaly_detection.py`):** Calculates rolling z-scores on ticket counts per product area against a 14-day baseline, automatically surfacing statistically significant spikes (e.g. bulk-upload complaints).
- **SLA Breach Prediction (`app/proactive/sla_predictor.py`):** Evaluates open tickets against contract-specific SLA targets (`app/domain/sla.py`), identifying tickets within 15 minutes of breach before a breach actually occurs.
- **Cross-Account Correlation (`app/proactive/cross_account_correlator.py`):** Correlates matching known issue patterns (e.g. KI-208, KI-211) across multiple independent accounts, detecting platform-wide incidents early.

---

## 3. The Key Success Metric: Escalation Precision
We judge the agent's product usefulness through **Escalation Precision**:
$$\text{Escalation Precision} = \frac{\text{Genuinely Necessary Escalations}}{\text{Total Escalations Created}}$$

This metric directly balances the two primary failure modes:
1. **Under-escalation (Over-confidence):** The agent fabricates or guesses answers when data is missing or ambiguous.
2. **Over-escalation (Excessive caution):** The agent escalates routine inquiries despite having unambiguous contract and policy evidence.

Tracking escalation precision alongside First Contact Resolution (FCR) provides a clear, quantitative measure of system trustworthiness.

---

## 4. Intentional Limitations & Scope Decisions
- **Free-Tier Infrastructure:** Built entirely on open-source and free-tier infrastructure (FastAPI, PostgreSQL, pgvector, SentenceTransformers, Groq/NVIDIA NIM) without paid OpenAI APIs or external vector databases.
- **Mock Authentication:** Implemented via standard bearer tokens mapped to simulated customer and agent sessions (`app/auth/mock_auth.py`), allowing thorough access control testing without third-party auth dependencies.
- **Turn-Based Chat:** Focused on deterministic correctness, tool execution transparency, and latency optimization (<300ms retrieval) over streaming token generation.

---

## 6. Stage 2 Knowledge Administration & Document Governance
In Stage 2, ParcelPilot implements a production-grade Knowledge Administration workflow that balances corpus evolution with governance:

1. **Governance Principle: Upload != Instant Policy Authority:**
   - Unverified RAG corpus expansion is a major vector for hallucination and policy breach.
   - Uploaded PDF documents must move through validation, text extraction, chunking, and embedding into `PENDING_REVIEW` state.
   - Only explicit manager review and activation allows a document to influence policy calculations or LLM answers.
2. **Strict Role Separation:**
   - **Customers:** Cannot upload or access admin interfaces. Customers retrieve only active global customer-visible documents and their own active account agreement.
   - **Support Agents:** Read active internal documents according to policy; cannot upload, activate, deprecate, or supersede documents.
   - **Managers:** Full control over upload, metadata validation, preview, activation, rejection, deprecation, supersession, and audit logs.
3. **Assessment Pack Baseline:**
   - The supplied assessment pack (`01_Support_Policy_v3_CURRENT.pdf`, etc.) remains the seeded baseline corpus.
   - Uploaded documents extend this baseline in a versioned, auditable manner.
