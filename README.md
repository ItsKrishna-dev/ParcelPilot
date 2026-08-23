# ParcelPilot AI Support Agent

AI support system for ParcelPilot (a B2B logistics platform) . The system supports both a **customer-facing** chatbot and an **internal support/operations** chatbot, backed by a document + structured-data agent with explicit source-authority resolution, PostgreSQL Row-Level Security, deterministic calculation guardrails, and a two-phase confirm-before-act workflow for state-changing tools.

See `docs/ARCHITECTURE_NOTE.md` and `docs/PRODUCT_NOTE.md` for in-depth design rationale and product trade-offs.

---

## Technology Stack (Free Tier / Local Only)

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (pgvector extension)
- **Primary LLM Provider:** Groq (`openai/gpt-oss-20b` -- fast, low token footprint under 8k TPM limits)
- **Fallback LLM Provider:** NVIDIA NIM (`nvidia/llama-3.1-nemotron-70b-instruct`)
- **Embeddings & Search:** Local `sentence-transformers/all-MiniLM-L6-v2` with pgvector cosine distance + in-memory BM25 hybrid ranking (<300ms retrieval, query-only encoding)
- **Frontend (Stage 1 Console):** React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons + Recharts (Trust Operations Console)
- **Access Control:** Transaction-local PostgreSQL Row-Level Security (`parcelpilot.user_role`, `parcelpilot.account_id`) + repository layer application-level scoping
- **Deterministic Domain Logic:** Pure Python calculation engines for cancellation fees, failed-pickup service credits, and SLA breach checks (`app/domain/`)

---

## Project Layout

```text
ParcelPilot/
├── .env.example                # Environment variables template
├── docker-compose.yml          # Postgres + pgvector container definition
├── data_pack/                  # Supplied PDFs and assessment Excel workbook
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI application entrypoint & lifespan
│   │   ├── config.py           # Central configuration & absolute .env resolution
│   │   ├── auth/               # Mock authentication & role dependency injection
│   │   ├── db/                 # Models, RLS SQL, repository chokepoint
│   │   ├── domain/             # Deterministic calculation engines & requirement detector
│   │   ├── retrieval/          # Fast hybrid search & source-authority resolver
│   │   ├── ingestion/          # PDF parser, workbook loader, contract rule extractor
│   │   ├── agent/              # Orchestrator, LLM provider client, schemas, tool registry
│   │   ├── proactive/          # Anomaly detection, SLA predictor, cross-account correlator
│   │   └── api/                # Chat, actions, insights, and records endpoints
│   └── tests/                  # Pytest test suite (79 passing unit & integration tests)
├── frontend/                   # React + TypeScript B2B Operations Console
│   ├── src/
│   │   ├── api/                # Client, chat, actions, insights, records API helpers
│   │   ├── components/         # Layout, chat cards, decision cards, traces, evidence, insights
│   │   ├── features/           # Audit view (Stage 1 empty state)
│   │   ├── lib/                # Tailwind merging & formatting utilities
│   │   └── types/              # Auth mock sessions and API response TypeScript interfaces
│   ├── .env.example            # VITE_API_BASE_URL=http://127.0.0.1:8000
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
└── docs/                       # ARCHITECTURE_NOTE.md & PRODUCT_NOTE.md
```

---

## Local Setup & Two-Terminal Workflow

### 1. Start PostgreSQL (with pgvector) via Docker

```bash
docker compose up -d db
```

*Port Mapping Note:* Use port `5433` when connecting locally (`DATABASE_URL=postgresql+psycopg2://parcelpilot:parcelpilot@localhost:5433/parcelpilot`).

### 2. Configure Backend & Frontend Environment

Copy backend and frontend `.env.example` templates:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Ensure `frontend/.env` contains:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Initialize Backend & Run Server (Terminal 1)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Initialize database, load workbook, parse PDFs
python -m app.db.init_db
python -m app.ingestion.load_workbook --path ../data_pack/ParcelPilot_Assessment_Data.xlsx
python -m app.ingestion.pdf_loader --dir ../data_pack

# Start FastAPI backend on port 8000
uvicorn app.main:app --reload --port 8000
```

### 4. Start React + TypeScript Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173`.

> **Note on Knowledge Admin:** In Stage 1, the Knowledge Admin navigation link is displayed in disabled/coming-soon mode as **"Knowledge Admin — Stage 2"** for manager roles. Document upload, review, activation, and ingestion management are scheduled for Stage 2.

---

## Running Automated Tests

Run the complete test suite (70 tests across domain calculations, fast retrieval, access control, 2-phase action confirmation, rate limiting, and all golden assessment test cases):

```bash
cd backend
python -m compileall app
pytest -v
```

---

## Mock Roles & Test Users

The API supports `Authorization: Bearer <session_id>` header for simulated role-based sessions:

| Session ID | Role | Account ID | Context |
|---|---|---|---|
| `cust-northstar` | `customer` | `ACCT-001` | Northstar customer session (signed agreement overrides cancellation fee to INR 0) |
| `cust-lumenworks` | `customer` | `ACCT-002` | LumenWorks customer session (Growth plan, 4h service credit threshold, fixed INR 300) |
| `cust-beacon` | `customer` | `ACCT-003` | Beacon Retail customer session (Standard plan, standard SOP applies) |
| `agent-rohit` | `support_agent` | `None` | Internal operations agent (cross-account read, draft escalations) |
| `manager-priya` | `manager` | `None` | Internal manager (cross-account read, high-value credit & escalation approval) |

---

## Assessment Rules & Guarantees

1. **Dataset Snapshot Time:** All business calculations (cancellation windows, elapsed pickup delay, SLA targets) use the fixed snapshot timestamp `2026-08-16 11:00 Asia/Kolkata` from configuration (`DATASET_SNAPSHOT_TIME`), never wall-clock time.
2. **Deterministic Calculation Guard:** If a user inquiry asks about cancellation eligibility, cancellation fee, failed-pickup service credit, or SLA response targets, the agent state machine enforces execution of `cancellation_calc`, `service_credit_calc`, or `sla_calc` before generating a final answer.
3. **Source Authority Hierarchy:** Signed Customer Agreement > Current Cancellation/Credit SOP > Current Support Policy > Product Ops Guide > Deprecated Documents (explicit history only) > Historical Ticket Resolutions (labeled unverified context).
4. **Data Isolation:** Customer sessions are prevented from viewing or querying cross-account orders, tickets, or agreements via both application repository checks and PostgreSQL Row-Level Security.
5. **Two-Phase Action Confirmation:** State-changing actions (`create_escalation`, `update_ticket_status`, `create_follow_up_task`) return a draft and pending action ID on `confirmed=false`. Execution only occurs on explicit confirmation with `confirmed=true` and is recorded in `audit_log`.

---

## Troubleshooting

- **Port Conflict on 5432:** If local Postgres or another service is already on port 5432, Docker maps Postgres to host port `5433`. Ensure `DATABASE_URL` in `.env` uses port `5433`.
- **Groq Rate Limit (TPM 8000):** Default model is set to `openai/gpt-oss-20b` with max 1024 tokens. If rate limits are reached, the system performs bounded backoff before falling back to NVIDIA NIM or returning a controlled escalation without crashing.
