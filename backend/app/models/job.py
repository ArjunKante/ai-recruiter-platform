from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from app.database import Base


class JobDescription(Base):
    """A parsed job description. `must_have_skills` / `nice_to_have_skills`
    are stored as JSON arrays produced by the resume_parser's JD extractor
    so the ranking engine never has to re-parse free text at scoring time.
    """

    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)

    must_have_skills = Column(JSON, default=list)
    nice_to_have_skills = Column(JSON, default=list)
    responsibilities = Column(JSON, default=list)
    soft_skills = Column(JSON, default=list)

    min_years_experience = Column(Integer, default=0)
    domain = Column(String, nullable=True)
    location = Column(String, nullable=True)
    remote_policy = Column(String, nullable=True)  # remote | hybrid | onsite
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    notice_period_days = Column(Integer, nullable=True)

    role_weight_profile = Column(String, default="default")

    created_at = Column(DateTime, default=dt.datetime.utcnow)
