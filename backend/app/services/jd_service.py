from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import resolve_role_profile
from app.models.job import JobDescription
from app.resume_parser.parser import parse_job_description


def create_job_description(db: Session, title: str, raw_text: str) -> JobDescription:
    parsed = parse_job_description(raw_text, title)
    jd = JobDescription(
        title=parsed["title"],
        raw_text=parsed["raw_text"],
        must_have_skills=parsed["must_have_skills"],
        nice_to_have_skills=parsed["nice_to_have_skills"],
        responsibilities=parsed["responsibilities"],
        soft_skills=parsed["soft_skills"],
        min_years_experience=parsed["min_years_experience"],
        domain=parsed["domain"],
        location=parsed["location"],
        remote_policy=parsed["remote_policy"],
        salary_min=parsed["salary_min"],
        salary_max=parsed["salary_max"],
        notice_period_days=parsed["notice_period_days"],
        role_weight_profile=resolve_role_profile(title),
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


def get_job_description(db: Session, jd_id: int) -> JobDescription | None:
    return db.query(JobDescription).filter(JobDescription.id == jd_id).first()


def list_job_descriptions(db: Session) -> list[JobDescription]:
    return db.query(JobDescription).order_by(JobDescription.created_at.desc()).all()


def jd_to_dict(jd: JobDescription) -> dict:
    """Plain-dict view used internally by the ranking engine (which is kept
    DB-agnostic and only ever sees dicts, never ORM objects)."""
    return {
        "id": jd.id,
        "title": jd.title,
        "raw_text": jd.raw_text,
        "must_have_skills": jd.must_have_skills or [],
        "nice_to_have_skills": jd.nice_to_have_skills or [],
        "min_years_experience": jd.min_years_experience or 0,
        "location": jd.location,
        "remote_policy": jd.remote_policy,
        "salary_min": jd.salary_min,
        "salary_max": jd.salary_max,
        "notice_period_days": jd.notice_period_days,
    }
