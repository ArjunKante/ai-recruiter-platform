"""
All API routes assembled in one router module. Each route delegates
immediately to a controller so routes stay thin (just HTTP plumbing) and
every business decision lives in controllers / services / engines.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.controllers.auth_controller import handle_login, handle_register
from app.controllers.candidate_controller import (
    handle_get_candidate,
    handle_list_candidates,
    handle_upload_resumes,
)
from app.controllers.chat_controller import handle_chat
from app.controllers.export_controller import handle_export
from app.controllers.jd_controller import handle_create_jd, handle_get_jd, handle_list_jds
from app.controllers.ranking_controller import (
    handle_compare,
    handle_get_rankings,
    handle_run_ranking,
)
from app.database import get_db
from app.models.audit import AuditLog, PromptLog
from app.models.user import User
from app.ranking_engine.dynamic_weights import get_weight_profile
from app.schemas import (
    AuditLogOut,
    CandidateOut,
    ChatRequest,
    ChatResponse,
    CompareRequest,
    ExportRequest,
    JobDescriptionCreate,
    JobDescriptionOut,
    PromptLogOut,
    RankingResultOut,
    TokenOut,
    UserCreate,
    UserLogin,
)
from app.utils.security import get_current_user, get_current_user_optional, require_admin

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenOut, tags=["Auth"])
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user. The first account is automatically promoted to admin."""
    return handle_register(db, payload)


@router.post("/auth/login", response_model=TokenOut, tags=["Auth"])
def login(payload: UserLogin, db: Session = Depends(get_db)):
    return handle_login(db, payload)


@router.get("/auth/me", tags=["Auth"])
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "role": current_user.role}

# ─────────────────────────────────────────────────────────────────────────────
# Job Descriptions
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/jobs", response_model=JobDescriptionOut, tags=["Job Descriptions"])
def create_jd(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    return handle_create_jd(db, payload, actor_email=user.email if user else None)


@router.get("/jobs", response_model=List[JobDescriptionOut], tags=["Job Descriptions"])
def list_jds(db: Session = Depends(get_db)):
    return handle_list_jds(db)


@router.get("/jobs/{jd_id}", response_model=JobDescriptionOut, tags=["Job Descriptions"])
def get_jd(jd_id: int, db: Session = Depends(get_db)):
    return handle_get_jd(db, jd_id)


@router.get("/jobs/{jd_id}/weights", tags=["Job Descriptions"])
def get_weights(jd_id: int, db: Session = Depends(get_db)):
    """Return the active dynamic weight profile for a JD (surfaced in the
    dashboard so recruiters always see what's driving each score)."""
    jd = handle_get_jd(db, jd_id)
    return get_weight_profile(jd.title)

# ─────────────────────────────────────────────────────────────────────────────
# Candidates / Resumes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/jobs/{jd_id}/candidates", response_model=List[CandidateOut], tags=["Candidates"])
async def upload_resumes(
    jd_id: int,
    files: List[UploadFile] = File(..., description="PDF, DOCX or TXT resume files (batch upload supported)"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Batch-upload one or more resume files. Files are parsed immediately on
    upload; structured fields are persisted so ranking runs don't re-parse."""
    return await handle_upload_resumes(db, jd_id, files, actor_email=user.email if user else None)


@router.get("/jobs/{jd_id}/candidates", response_model=List[CandidateOut], tags=["Candidates"])
def list_candidates(jd_id: int, db: Session = Depends(get_db)):
    return handle_list_candidates(db, jd_id)


@router.get("/candidates/{candidate_id}", response_model=CandidateOut, tags=["Candidates"])
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    return handle_get_candidate(db, candidate_id)

# ─────────────────────────────────────────────────────────────────────────────
# Ranking Engine
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/jobs/{jd_id}/rank", response_model=List[RankingResultOut], tags=["Ranking"])
def run_ranking(
    jd_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Trigger a full ranking run: parse, embed, score all six dimensions,
    call the LLM for recruiter reasoning, persist results. Returns ranked list."""
    return handle_run_ranking(db, jd_id, actor_email=user.email if user else None)


@router.get("/jobs/{jd_id}/rank", response_model=List[RankingResultOut], tags=["Ranking"])
def get_rankings(jd_id: int, db: Session = Depends(get_db)):
    """Retrieve the most recent ranking results for a JD without re-running."""
    return handle_get_rankings(db, jd_id)


@router.post("/compare", response_model=List[RankingResultOut], tags=["Ranking"])
def compare_candidates(payload: CompareRequest, db: Session = Depends(get_db)):
    """Module 15: side-by-side comparison of 2-4 candidates."""
    return handle_compare(db, payload)

# ─────────────────────────────────────────────────────────────────────────────
# AI Chat Search  (Module 16)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Natural-language recruiter chat. Routes the question through the LLM
    with the ranked candidate pool as grounding context."""
    return handle_chat(db, payload)

# ─────────────────────────────────────────────────────────────────────────────
# Downloads  (Module Downloads)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/export", tags=["Export"])
def export_shortlist(payload: ExportRequest, db: Session = Depends(get_db)):
    """Download the shortlist as CSV, Excel, or PDF."""
    data, content_type, filename = handle_export(db, payload)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# ─────────────────────────────────────────────────────────────────────────────
# Admin  (Bonus: audit logs, prompt logs)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/admin/audit-logs", response_model=List[AuditLogOut], tags=["Admin"])
def audit_logs(
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return rows


@router.get("/admin/prompt-logs", response_model=List[PromptLogOut], tags=["Admin"])
def prompt_logs(
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    rows = db.query(PromptLog).order_by(PromptLog.created_at.desc()).limit(limit).all()
    return rows


@router.get("/admin/stats", tags=["Admin"])
def admin_stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from app.models.candidate import Candidate
    from app.models.job import JobDescription
    from app.models.ranking import RankingResult
    from app.models.user import User as UserModel

    return {
        "total_users": db.query(UserModel).count(),
        "total_jobs": db.query(JobDescription).count(),
        "total_candidates": db.query(Candidate).count(),
        "total_ranking_runs": db.query(AuditLog).filter(AuditLog.action == "RANKING_RUN").count(),
        "total_llm_calls": db.query(PromptLog).count(),
    }
