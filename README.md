# ParcelPilot AI Support Agent

AI support system for ParcelPilot (B2B logistics platform) built for the CalQuity AI Engineer
assessment. Supports both a **customer-facing** chatbot and an **internal support/operations**
chatbot, backed by a document + structured-data agent with explicit source-authority resolution,
Postgres Row-Level Security, and a two-phase confirm-before-act workflow for state-changing tools.

See `docs/ARCHITECTURE_NOTE.md` and `docs/PRODUCT_NOTE.md` for design rationale.

## Stack (free-tier only, no paid APIs)
- **Backend:** FastAPI + SQLAlchemy + Postgres (pgvector extension)
- **LLM:** NVIDIA NIM (primary) with automatic Groq fallback -- both free-tier, OpenAI-compatible APIs
- **Embeddings:** local `sentence-transformers/all-MiniLM-L6-v2` (no external API call)
- **Frontend:** a single static HTML/JS chat page (no build step) served by FastAPI, showing the
  active tool per turn and a confidence badge
- **Access control:** enforced in the repository layer AND via native Postgres Row-Level Security

## Project Layout
```
backend/app/
  main.py                 FastAPI app entrypoint
  config.py               env/config, dataset snapshot time
  auth/                   mock authentication (customer / support_agent / manager)
  db/                     SQLAlchemy models, RLS policies, source-authority rules, repository layer
  ingestion/              PDF/XLSX loaders, chunker, local embedder
  retrieval/              hybrid search + source-authority resolver
  domain/                 deterministic calculation functions (fees, credits, SLA)
  agent/                  orchestrator, tool registry, Pydantic tool schemas, LLM adapter
  agent/tools/            the 3 required tools
  proactive/              anomaly detection, SLA breach prediction, cross-account correlation
  api/                    chat / actions / insights routes
backend/tests/            pytest suite (source authority, edge cases, access control, actions)
frontend/                 static chat UI
docs/                     architecture note, product note
```

## Setup

### 1. Start Postgres (with pgvector)
```bash
docker compose up -d db
```

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in NVIDIA_NIM_API_KEY / GROQ_API_KEY
python -m app.db.init_db          # creates tables, seeds accounts/orders/tickets, seeds authority rules
python -m app.ingestion.load_workbook --path ../data_pack/ParcelPilot_Assessment_Data.xlsx
python -m app.ingestion.pdf_loader --dir ../data_pack   # chunk + embed the 6 supplied PDFs
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
Just open `frontend/index.html` in a browser (it talks to `http://localhost:8000`), or:
```bash
cd frontend && python -m http.server 5173
```

### 4. Run tests
```bash
cd backend && pytest -v
```

## Mock Users (for testing access control)
| user_id | role | account_id | Use for |
|---|---|---|---|
| cust-northstar | customer | ACCT-001 | Northstar customer-facing session |
| cust-lumenworks | customer | ACCT-002 | LumenWorks customer-facing session |
| agent-rohit | support_agent | null | Internal agent, cross-account read, cannot approve >INR1000 credit |
| manager-priya | manager | null | Internal manager, can confirm high-value credits/escalations |

## Notes on Determinism
All "current time" logic reads `DATASET_SNAPSHOT_TIME` from config -- never the real wall clock --
so answers are reproducible against the fixed dataset snapshot (2026-08-16 11:00 IST) stated in the
workbook README, regardless of when you run the app.
