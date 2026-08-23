# ParcelPilot — Deployment Guide

> **Architecture:** Browser → Vercel (React frontend) → Render (FastAPI backend) → Neon PostgreSQL

The Neon database is **already hosted**. This guide covers connecting to it and deploying the frontend and backend services. No database provisioning is needed.

---

## Table of Contents

1. [Local Development Workflow](#1-local-development-workflow)
2. [Existing Neon Database](#2-existing-neon-database)
3. [Database Initialization & Ingestion](#3-database-initialization--ingestion)
4. [Render Backend Deployment](#4-render-backend-deployment)
5. [Vercel Frontend Deployment](#5-vercel-frontend-deployment)
6. [CORS Finalization](#6-cors-finalization)
7. [Security Notes](#7-security-notes)

---

## 1. Local Development Workflow

### Prerequisites

- Python 3.11+
- Node.js 18+ / npm
- (Optional) Docker — only needed for local PostgreSQL instead of Neon

### 1a. Start local PostgreSQL (Docker, optional)

If you want a local database instead of pointing to Neon:

```bash
docker compose up -d db
```

Set `DATABASE_URL` in `.env` to the Docker URL:

```env
DATABASE_URL=postgresql+psycopg2://parcelpilot:parcelpilot@localhost:5433/parcelpilot
```

Port `5433` is the host-side mapping; `5432` is used inside Docker.

### 1b. Configure environment variables

```bash
cp .env.example .env
# Edit .env: fill in your API keys and DATABASE_URL
cp frontend/.env.example frontend/.env
# frontend/.env already contains VITE_API_BASE_URL=http://127.0.0.1:8000
```

Never commit `.env` files — they are gitignored.

### 1c. Initialize the backend (Terminal 1)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run once to set up schema, RLS, and seed data:
python -m app.db.init_db

# Load structured data from the Excel workbook:
python -m app.ingestion.load_workbook --path ../data_pack/ParcelPilot_Assessment_Data.xlsx

# Parse and embed PDFs into the vector store:
python -m app.ingestion.pdf_loader --dir ../data_pack

# Start the backend:
uvicorn app.main:app --reload --port 8000
```

### 1d. Start the frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### 1e. Local health checks

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
```

Both should return HTTP 200.

---

## 2. Existing Neon Database

The Neon database is already provisioned and populated. You do **not** need to create, reset, or migrate it.

### Connecting to Neon

Set `DATABASE_URL` in your `.env` (locally) or in the Render dashboard (production):

```env
DATABASE_URL=postgresql://USER:PASSWORD@NEON_HOST/neondb?sslmode=require&channel_binding=require
```

> **Important:** Keep the `sslmode=require&channel_binding=require` parameters — they are required by Neon.

### Verify the connection without printing secrets

```bash
cd backend
source .venv/bin/activate
python - <<'PY'
from urllib.parse import urlsplit
from app.config import settings

parsed = urlsplit(settings.database_url)
print("Database host:", parsed.hostname)
print("Database port:", parsed.port or 5432)
print("Database name:", parsed.path.lstrip("/"))
print("Using Neon:", "neon.tech" in (parsed.hostname or ""))
PY
```

### Do not reset the Neon database

Do **not** run `DROP TABLE`, `TRUNCATE`, or `DELETE` against production.  
`init_db.py` is idempotent — it skips seeding if accounts already exist.

---

## 3. Database Initialization & Ingestion

> **When to run:** Run these commands **once** against a fresh database (local Docker or a new Neon instance).  
> They are **not** run automatically on every Render restart.

```bash
# From backend/ with .venv activated and DATABASE_URL pointing to Neon or local:

python -m app.db.init_db

python -m app.ingestion.load_workbook \
  --path ../data_pack/ParcelPilot_Assessment_Data.xlsx

python -m app.ingestion.pdf_loader \
  --dir ../data_pack
```

Both `load_workbook` and `pdf_loader` are **idempotent** — re-running them does not create duplicate metadata rows. However, avoid regenerating embeddings unnecessarily on an already-populated database.

### Safe ways to run against Neon on Render

- **Option A (recommended):** Run locally against Neon before deployment:  
  Set `DATABASE_URL` in your local `.env` to the Neon URL and run the commands above.

- **Option B:** Use the Render Shell (dashboard → your service → Shell):  
  ```bash
  python -m app.db.init_db
  python -m app.ingestion.pdf_loader --dir ../data_pack
  ```
  Only use this for one-off manual runs, not in the start command.

**Do not place ingestion commands in the Render start command** — embeddings take time and should not block service startup.

---

## 4. Render Backend Deployment

### Repository settings

| Setting | Value |
|---|---|
| Repository | Your GitHub repo (e.g. `your-org/ParcelPilot`) |
| Branch | `main` |
| Root Directory | `backend` |
| Runtime | Python |

### Build & start commands

| Setting | Value |
|---|---|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

> **Do not use `--reload`** in the start command. It is for development only.

### Required environment variables (set in Render dashboard)

| Variable | Description |
|---|---|
| `DATABASE_URL` | Your Neon connection string (with SSL params) |
| `GROQ_API_KEY` | Your Groq API key |
| `APP_SECRET_KEY` | Random secret for session signing (e.g. `openssl rand -hex 32`) |
| `CORS_ORIGINS` | Comma-separated frontend origins (see [CORS section](#6-cors-finalization)) |
| `ENVIRONMENT` | Set to `production` |

### Optional environment variables

| Variable | Default | Description |
|---|---|---|
| `NVIDIA_NIM_API_KEY` | _(empty)_ | NVIDIA NIM fallback provider key |
| `GROQ_MODEL` | `openai/gpt-oss-20b` | Groq model name |
| `GROQ_MAX_TOKENS` | `768` | Max tokens per Groq response |
| `LLM_PRIMARY_PROVIDER` | `groq` | Primary LLM provider |
| `LLM_FALLBACK_PROVIDER` | `nvidia` | Fallback LLM provider |
| `DB_POOL_SIZE` | `3` | SQLAlchemy pool size |
| `DB_MAX_OVERFLOW` | `2` | Pool max overflow |

### Verify deployment

```bash
# After deployment:
curl -i https://YOUR-RENDER-SERVICE.onrender.com/health
curl -i https://YOUR-RENDER-SERVICE.onrender.com/ready
```

Both should return HTTP 200.

### Logs

Render dashboard → your service → Logs tab.  
The startup log shows `DATABASE_URL: postgresql://USER:***@HOST/...` (password is redacted).

### Safe restart

Render dashboard → your service → Manual Deploy → Deploy latest commit.  
A restart does **not** run `init_db` or ingestion — only the `startCommand` runs.

---

## 5. Vercel Frontend Deployment

### Settings

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |
| Node Version | 18 (or 20) |

`frontend/vercel.json` is pre-configured with SPA rewrites so client-side routes (e.g. deep links) work correctly.

### Required environment variable

Set this in the Vercel dashboard under **Settings → Environment Variables**:

| Variable | Scope | Value |
|---|---|---|
| `VITE_API_BASE_URL` | Production | `https://YOUR-RENDER-SERVICE.onrender.com` |
| `VITE_API_BASE_URL` | Preview | `https://YOUR-RENDER-SERVICE.onrender.com` (or a staging backend) |

> **Important:** `VITE_API_BASE_URL` is a **public** build-time variable — it is embedded in the JavaScript bundle. Never set it to a secret value or backend credential.

### After changing environment variables

Vercel environment variable changes do **not** take effect until you **redeploy**:  
Vercel dashboard → Deployments → Redeploy.

### SPA routing

`frontend/vercel.json` contains:
```json
{
  "rewrites": [{ "source": "/((?!assets/).*)", "destination": "/index.html" }]
}
```
This ensures deep links work correctly (all non-asset paths render `index.html`).

### Local production build test

```bash
cd frontend
npm run build     # Must succeed with exit code 0
npm run preview   # Serves dist/ locally for smoke testing
```

---

## 6. CORS Finalization

After Vercel assigns your production URL (e.g. `https://parcelpilot-abc.vercel.app`):

1. Go to Render dashboard → your backend service → Environment.
2. Update `CORS_ORIGINS`:
   ```
   https://parcelpilot-abc.vercel.app,http://localhost:5173,http://127.0.0.1:5173
   ```
3. Save and trigger a redeploy (or Render will restart automatically).
4. Test:
   ```bash
   curl -i -X OPTIONS \
     https://YOUR-RENDER-SERVICE.onrender.com/health \
     -H "Origin: https://parcelpilot-abc.vercel.app" \
     -H "Access-Control-Request-Method: GET"
   ```
   The response should include `Access-Control-Allow-Origin: https://parcelpilot-abc.vercel.app`.

> **Never** use `CORS_ORIGINS=*` in production.

---

## 7. Security Notes

- **Secrets:** `DATABASE_URL`, `GROQ_API_KEY`, `APP_SECRET_KEY`, and `NVIDIA_NIM_API_KEY` must only be set in Render environment variables — never committed to the repository.
- **Frontend bundle:** `VITE_API_BASE_URL` is the only variable embedded in the Vercel bundle. It is the backend's public HTTPS URL — not a secret.
- **Database URL in logs:** The startup log redacts the password: `postgresql://USER:***@HOST/...`.
- **CORS:** In production, only exact configured origins are allowed — no wildcard.
- **RLS:** PostgreSQL Row-Level Security is applied via `init_db.py` and enforced at the database level. Render deployment does not change RLS behavior.
- **Auth:** The API uses `Authorization: Bearer <session_id>` header-based mock auth. Token validation is handled server-side and is not weakened by deployment changes.
