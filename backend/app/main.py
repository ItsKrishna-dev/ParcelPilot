import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.llm_client import _provider_order
from app.api import actions, chat, insights
from app.config import settings


app = FastAPI(
    title="ParcelPilot AI Support Agent",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat.router)
app.include_router(actions.router)
app.include_router(insights.router)


@app.on_event("startup")
def print_runtime_configuration():
    print("=== ParcelPilot runtime configuration ===")
    print("DATABASE_URL:", settings.database_url)
    print("PRIMARY_PROVIDER:", settings.llm_primary_provider)
    print("FALLBACK_PROVIDER:", settings.llm_fallback_provider)
    print("GROQ_MODEL:", repr(settings.groq_model))
    print("PROVIDER_ORDER:", _provider_order())
    print("GROQ_KEY_CONFIGURED:", bool(settings.groq_api_key))
    print("PROCESS_GROQ_MODEL:", repr(os.environ.get("GROQ_MODEL")))
    print("========================================")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": settings.llm_primary_provider,
        "model": settings.groq_model,
    }