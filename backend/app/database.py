"""
SQLAlchemy engine + session management.

Uses DATABASE_URL from config. Works unmodified against SQLite (zero-config
local/demo use) or PostgreSQL (production) -- only the connection string
changes, the ORM models and queries are identical.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. For a hackathon/demo this replaces a migration
    tool; for production swap this for Alembic migrations."""
    from app.models import candidate, job, ranking, user, audit  # noqa: F401

    Base.metadata.create_all(bind=engine)
