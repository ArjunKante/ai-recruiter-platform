from __future__ import annotations

from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audit import AuditLog
from app.schemas import CandidateOut
from app.services.candidate_service import get_candidate, ingest_resume_file, list_candidates_for_jd
from app.services.jd_service import get_job_description

settings = get_settings()
ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")


async def handle_upload_resumes(
    db: Session, job_description_id: int, files: List[UploadFile], actor_email: str | None
) -> List[CandidateOut]:
    jd = get_job_description(db, job_description_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found -- upload a JD before resumes")

    created = []
    errors = []
    for f in files:
        if not f.filename.lower().endswith(ALLOWED_EXTENSIONS):
            errors.append(f"{f.filename}: unsupported file type")
            continue
        content = await f.read()
        if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            errors.append(f"{f.filename}: exceeds {settings.MAX_UPLOAD_MB}MB limit")
            continue
        try:
            candidate = ingest_resume_file(db, job_description_id, f.filename, content)
            created.append(candidate)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{f.filename}: failed to parse ({e})")

    if not created and errors:
        raise HTTPException(status_code=400, detail={"message": "No resumes could be parsed", "errors": errors})

    db.add(AuditLog(
        actor_email=actor_email,
        action="RESUMES_UPLOADED",
        target_type="job_description",
        target_id=job_description_id,
        metadata_json={"uploaded": len(created), "errors": errors},
    ))
    db.commit()
    return created


def handle_list_candidates(db: Session, job_description_id: int) -> List[CandidateOut]:
    return list_candidates_for_jd(db, job_description_id)


def handle_get_candidate(db: Session, candidate_id: int) -> CandidateOut:
    candidate = get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
