from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings


# Conservative pool settings for Render free-tier / Neon serverless.
# Neon's pooler limits concurrent connections; a small pool avoids exhaustion.
# Override via env vars DB_POOL_SIZE / DB_MAX_OVERFLOW / DB_POOL_TIMEOUT / DB_POOL_RECYCLE.
import os

_pool_size = int(os.environ.get("DB_POOL_SIZE", "3"))
_max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "2"))
_pool_timeout = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
_pool_recycle = int(os.environ.get("DB_POOL_RECYCLE", "300"))

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=_pool_size,
    max_overflow=_max_overflow,
    pool_timeout=_pool_timeout,
    pool_recycle=_pool_recycle,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
