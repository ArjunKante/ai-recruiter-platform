"""
Application entry point. Run with:
  uvicorn app.main:app --reload --port 8000

All scoring logic lives in the backend. The frontend (React/TS) only renders
API responses -- it never calculates scores.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes.api import router

settings = get_settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_INDEX_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (idempotent -- safe to run against an
    existing DB; production would use Alembic migrations instead)."""
    init_db()
    yield


app = FastAPI(
    title="AI Recruiter Platform API",
    description=(
        "Production-quality AI recruiting platform that ranks candidates "
        "like an experienced recruiter. All scoring logic lives here in the "
        "backend -- the frontend only renders API responses."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1024)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────

app.include_router(router, prefix="/api")


@app.get("/", tags=["Health"])
def root():
    return {
        "name": settings.APP_NAME,
        "status": "ok",
        "version": "1.0.0",
        "docs": "/docs",
        "environment": settings.ENV,
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
