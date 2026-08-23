import os
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.agent.llm_client import _provider_order
from app.api import actions, admin_documents, chat, insights, records
from app.config import settings


def _parse_cors_origins() -> list[str]:
    """
    Parse the comma-separated CORS_ORIGINS setting into a deduplicated list.
    Strips whitespace and ignores empty tokens.
    """
    raw = settings.cors_origins or ""
    seen: set[str] = set()
    origins: list[str] = []
    for part in raw.split(","):
        origin = part.strip().rstrip("/")
        if origin and origin not in seen:
            seen.add(origin)
            origins.append(origin)
    return origins


def _redact_db_url(url: str) -> str:
    """Return the database URL with the password replaced by ***."""
    try:
        parsed = urlsplit(url)
        if parsed.password:
            safe = parsed._replace(
                netloc=parsed.netloc.replace(
                    f":{parsed.password}@", ":***@"
                )
            )
            return safe.geturl()
    except Exception:
        pass
    return "<redacted>"


@asynccontextmanager
async def lifespan(app: FastAPI):
    cors = _parse_cors_origins()
    print("=== ParcelPilot runtime configuration ===")
    print("ENVIRONMENT:", settings.environment)
    print("DATABASE_URL:", _redact_db_url(settings.database_url))
    print("CORS_ORIGINS:", cors)
    print("PRIMARY_PROVIDER:", settings.llm_primary_provider)
    print("FALLBACK_PROVIDER:", settings.llm_fallback_provider)
    print("GROQ_MODEL:", repr(settings.groq_model))
    print("PROVIDER_ORDER:", _provider_order())
    print("GROQ_KEY_CONFIGURED:", bool(settings.groq_api_key))
    print("PROCESS_GROQ_MODEL:", repr(os.environ.get("GROQ_MODEL")))
    print("========================================")
    yield


app = FastAPI(
    title="ParcelPilot AI Support Agent",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_origins = _parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(chat.router)
app.include_router(actions.router)
app.include_router(insights.router)
app.include_router(records.router)
app.include_router(admin_documents.router)


@app.get("/health")
def health():
    """Lightweight liveness check — no DB, no LLM, no side-effects."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "provider": settings.llm_primary_provider,
        "model": settings.groq_model,
    }


@app.get("/ready")
def ready():
    """
    Readiness check — verifies the database connection is reachable.
    Returns 200 when Neon is accessible, 503 otherwise.
    Suitable for Render health checks.
    """
    from app.db.session import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unreachable"},
        )