from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.resume_parser.extractor import extract_text
from app.resume_parser.parser import parse_resume


def ingest_resume_file(db: Session, job_description_id: int, filename: str, file_bytes: bytes) -> Candidate:
    raw_text = extract_text(filename, file_bytes)
    parsed = parse_resume(raw_text, filename)

    candidate = Candidate(
        job_description_id=job_description_id,
        name=parsed["name"],
        email=parsed["email"],
        phone=parsed["phone"],
        location=parsed["location"],
        github_url=parsed["github_url"],
        raw_resume_text=parsed["raw_resume_text"],
        source_filename=parsed["source_filename"],
        experience=parsed["experience"],
        education=parsed["education"],
        skills=parsed["skills"],
        certifications=parsed["certifications"],
        total_years_experience=parsed["total_years_experience"],
        notice_period_days=parsed["notice_period_days"],
        desired_salary=parsed["desired_salary"],
        open_to_remote=parsed["open_to_remote"],
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def list_candidates_for_jd(db: Session, job_description_id: int) -> List[Candidate]:
    return db.query(Candidate).filter(Candidate.job_description_id == job_description_id).all()


def get_candidate(db: Session, candidate_id: int) -> Candidate | None:
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()


def candidate_to_dict(c: Candidate) -> dict:
    """Plain-dict view used by the ranking engine (DB-agnostic)."""
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "location": c.location,
        "github_url": c.github_url,
        "raw_resume_text": c.raw_resume_text,
        "experience": c.experience or [],
        "education": c.education or [],
        "skills": c.skills or [],
        "certifications": c.certifications or [],
        "total_years_experience": c.total_years_experience or 0,
        "notice_period_days": c.notice_period_days,
        "desired_salary": c.desired_salary,
        "open_to_remote": c.open_to_remote,
    }
