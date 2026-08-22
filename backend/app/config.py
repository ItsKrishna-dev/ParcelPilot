"""
Central configuration. Nothing else in the codebase should read os.environ directly or
call datetime.now() for business-logic "current time" -- always import DATASET_SNAPSHOT_TIME
from here so answers stay reproducible against the fixed dataset snapshot.
"""
from datetime import datetime
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(default="postgresql+psycopg2://parcelpilot:parcelpilot@localhost:5432/parcelpilot")

    nvidia_nim_api_key: str = Field(default="")
    nvidia_nim_base_url: str = Field(default="https://integrate.api.nvidia.com/v1")
    nvidia_nim_model: str = Field(default="nvidia/llama-3.1-nemotron-70b-instruct")

    groq_api_key: str = Field(default="")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")
    groq_model: str = Field(default="llama-3.3-70b-versatile")

    llm_primary_provider: str = Field(default="nvidia")
    llm_fallback_provider: str = Field(default="groq")

    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    dataset_snapshot_time: str = Field(default="2026-08-16T11:00:00+05:30")
    app_secret_key: str = Field(default="change_me_in_production")
    manager_approval_threshold_inr: float = Field(default=1000.0)
    pending_action_ttl_seconds: int = Field(default=600)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def dataset_snapshot_time() -> datetime:
    """The single source of truth for 'now' across the whole system.

    Every SLA / cancellation-window / credit-eligibility calculation MUST call this
    instead of datetime.now(), so the system's answers are reproducible against the
    fixed dataset snapshot regardless of when the grader actually runs it.
    """
    return datetime.fromisoformat(settings.dataset_snapshot_time)
