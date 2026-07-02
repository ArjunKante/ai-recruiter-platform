from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.schemas import JobDescriptionCreate, JobDescriptionOut
from app.services.jd_service import create_job_description, get_job_description, list_job_descriptions


def handle_create_jd(db: Session, payload: JobDescriptionCreate, actor_email: str | None) -> JobDescriptionOut:
    if len(payload.raw_text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Job description text is too short to parse meaningfully")
    jd = create_job_description(db, payload.title, payload.raw_text)
    db.add(AuditLog(actor_email=actor_email, action="JD_CREATED", target_type="job_description", target_id=jd.id))
    db.commit()
    return jd


def handle_get_jd(db: Session, jd_id: int) -> JobDescriptionOut:
    jd = get_job_description(db, jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


def handle_list_jds(db: Session) -> list[JobDescriptionOut]:
    return list_job_descriptions(db)
