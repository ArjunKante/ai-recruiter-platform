from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.database import Base


class Candidate(Base):
    """A parsed candidate resume, scoped to one upload batch (job_description_id
    is nullable because the same candidate record can theoretically be
    re-ranked against a different JD; ranking results live in their own
    table keyed by (candidate_id, job_description_id)).
    """

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    job_description_id = Column(Integer, index=True, nullable=True)

    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    github_url = Column(String, nullable=True)

    raw_resume_text = Column(Text, nullable=False)
    source_filename = Column(String, nullable=True)

    # Structured extraction (lists of dicts) produced by resume_parser
    experience = Column(JSON, default=list)   # [{company, title, start, end, bullets:[...]}]
    education = Column(JSON, default=list)    # [{school, degree, year}]
    skills = Column(JSON, default=list)       # normalized flat skill list
    certifications = Column(JSON, default=list)

    total_years_experience = Column(Integer, default=0)
    notice_period_days = Column(Integer, nullable=True)
    desired_salary = Column(Integer, nullable=True)
    open_to_remote = Column(String, nullable=True)  # remote | hybrid | onsite | unknown

    created_at = Column(DateTime, default=dt.datetime.utcnow)
