from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.database import Base


class AuditLog(Base):
    """Append-only log of meaningful platform actions, surfaced on the
    admin dashboard. Cheap to write, valuable for trust/compliance."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_email = Column(String, nullable=True)
    action = Column(String, nullable=False)        # e.g. "JD_CREATED", "RANKING_RUN"
    target_type = Column(String, nullable=True)    # e.g. "job_description", "candidate"
    target_id = Column(Integer, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class PromptLog(Base):
    """Every prompt sent to the LLM and the raw response, for explainability
    and debugging. This is what backs the 'prompt logging' bonus feature."""

    __tablename__ = "prompt_logs"

    id = Column(Integer, primary_key=True, index=True)
    purpose = Column(String, nullable=False)  # e.g. "recruiter_reasoning", "chat_search"
    candidate_id = Column(Integer, nullable=True)
    job_description_id = Column(Integer, nullable=True)
    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    model = Column(String, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
