"""
Central application configuration.

All tunable behaviour (DB connection, secrets, LLM provider, dynamic scoring
weights per role) is defined here and sourced from environment variables so
the same codebase runs unmodified in dev / staging / prod.

IMPORTANT: per the product spec, scoring weights are NEVER hardcoded inside
the ranking engine itself -- they live here as data, are looked up per role,
and are returned to the frontend so recruiters can see exactly how a score
was computed. The frontend only renders these; it never recomputes them.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Core ---
    APP_NAME: str = "AI Recruiter Platform"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # --- Database ---
    # SQLite by default so the project runs with zero external services.
    # Point DATABASE_URL at a real Postgres instance for production, e.g.
    # postgresql+psycopg2://user:password@localhost:5432/ai_recruiter
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./ai_recruiter.db"
    )

    # --- Auth ---
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # --- LLM provider ---
    # Claude is the default reasoning engine. The llm_service module is
    # written behind a provider interface so OPENAI / GEMINI / OLLAMA can be
    # swapped in by implementing the same `BaseLLMClient` contract.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "claude")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- File storage ---
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "10"))

    # --- Vector store ---
    VECTOR_INDEX_DIR: str = os.getenv("VECTOR_INDEX_DIR", "./vector_index")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "512"))

    # --- GitHub enrichment (optional, public API, no token required for
    # low-volume use; set GITHUB_TOKEN to raise the rate limit) ---
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # --- Trust engine ---
    TRUST_HIGH_RISK_THRESHOLD: int = int(os.getenv("TRUST_HIGH_RISK_THRESHOLD", "55"))

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ---------------------------------------------------------------------------
# Dynamic weight engine configuration
# ---------------------------------------------------------------------------
# Each role family maps to a weight profile across the six score components.
# Weights must sum to 100. The ranking engine looks up the closest profile
# for the parsed JD title; "default" is the fallback used when no role
# keyword matches.
ROLE_WEIGHT_PROFILES: Dict[str, Dict[str, int]] = {
    "default": {
        "semantic_skill_match": 30,
        "career_intelligence": 25,
        "behavior_score": 15,
        "context_alignment": 10,
        "resume_quality": 10,
        "trust_score": 10,
    },
    "backend_engineer": {
        "semantic_skill_match": 40,
        "career_intelligence": 25,
        "behavior_score": 15,
        "context_alignment": 10,
        "resume_quality": 5,
        "trust_score": 5,
    },
    "frontend_engineer": {
        "semantic_skill_match": 40,
        "career_intelligence": 22,
        "behavior_score": 18,
        "context_alignment": 10,
        "resume_quality": 5,
        "trust_score": 5,
    },
    "data_engineer": {
        "semantic_skill_match": 38,
        "career_intelligence": 27,
        "behavior_score": 13,
        "context_alignment": 10,
        "resume_quality": 5,
        "trust_score": 7,
    },
    "product_manager": {
        "semantic_skill_match": 20,
        "career_intelligence": 30,
        "behavior_score": 20,
        "context_alignment": 10,
        "resume_quality": 10,
        "trust_score": 10,
    },
    "engineering_manager": {
        "semantic_skill_match": 20,
        "career_intelligence": 32,
        "behavior_score": 23,
        "context_alignment": 10,
        "resume_quality": 5,
        "trust_score": 10,
    },
    "designer": {
        "semantic_skill_match": 30,
        "career_intelligence": 22,
        "behavior_score": 23,
        "context_alignment": 10,
        "resume_quality": 10,
        "trust_score": 5,
    },
    "sales": {
        "semantic_skill_match": 15,
        "career_intelligence": 30,
        "behavior_score": 30,
        "context_alignment": 15,
        "resume_quality": 5,
        "trust_score": 5,
    },
}

# Keywords used to classify a free-text JD title into one of the profiles
# above. First match wins; order matters (more specific roles first).
ROLE_KEYWORD_MAP = [
    ("engineering_manager", ["engineering manager", "eng manager", "head of engineering"]),
    ("product_manager", ["product manager", "product owner", " pm "]),
    ("data_engineer", ["data engineer", "data scientist", "ml engineer", "machine learning"]),
    ("frontend_engineer", ["frontend", "front-end", "front end", "react developer", "ui engineer"]),
    ("backend_engineer", ["backend", "back-end", "back end", "platform engineer", "infrastructure engineer", "api engineer"]),
    ("designer", ["product designer", "ux designer", "ui designer", "visual designer"]),
    ("sales", ["account executive", "sales", "business development"]),
]


def resolve_role_profile(jd_title: str) -> str:
    """Classify a JD title into the closest weight profile key."""
    t = (jd_title or "").lower()
    for profile_key, keywords in ROLE_KEYWORD_MAP:
        if any(kw in t for kw in keywords):
            return profile_key
    return "default"
