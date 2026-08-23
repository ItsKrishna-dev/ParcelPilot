"""
Central application configuration.

The .env file is resolved relative to the repository root rather than the current
working directory. This allows commands to work consistently whether they are run
from the project root or from backend/.
"""

from datetime import datetime
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    database_url: str = Field(
        default=(
            "postgresql+psycopg2://parcelpilot:parcelpilot"
            "@localhost:5433/parcelpilot"
        )
    )
    
    # LLM Provider Configuration
    llm_primary_provider: str = Field(default="groq")
    llm_fallback_provider: str = Field(default="nvidia")
    
    # Groq (Primary)
    groq_api_key: str = Field(default="")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")
    groq_model: str = Field(default="openai/gpt-oss-20b")
    groq_max_tokens: int = Field(default=768)
    
    # NVIDIA NIM (Fallback)
    nvidia_nim_api_key: str = Field(default="")
    nvidia_nim_base_url: str = Field(default="https://integrate.api.nvidia.com/v1")
    nvidia_nim_model: str = Field(default="nvidia/llama-3.1-nemotron-70b-instruct")

    # Orchestrator & LLM limits
    llm_max_tool_iterations: int = Field(default=4)
    llm_retry_max_attempts: int = Field(default=1)

    # Retrieval Configuration
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    retrieval_top_k: int = Field(default=3)
    retrieval_max_chunk_chars: int = Field(default=1200)

    # Dataset & Assessment Configuration
    dataset_snapshot_time: str = Field(default="2026-08-16T11:00:00+05:30")
    app_secret_key: str = Field(default="change_me_in_production")
    manager_approval_threshold_inr: float = Field(default=1000.0)
    pending_action_ttl_seconds: int = Field(default=600)

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()


def dataset_snapshot_time() -> datetime:
    """
    Return the fixed assessment snapshot time.

    Never use datetime.now() for cancellation, credit, or SLA calculations.
    Returns naive datetime to match database datetime columns consistently.
    """
    dt = datetime.fromisoformat(settings.dataset_snapshot_time)
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt