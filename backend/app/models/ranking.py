from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


class RankingResult(Base):
    """The persisted output of one ranking_engine run for a single
    (candidate, job_description) pair. Storing the full breakdown -- not
    just the final number -- is what makes every rank explainable and
    reproducible (XAI requirement).
    """

    __tablename__ = "ranking_results"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True, nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), index=True, nullable=False)

    # --- six core component scores, each 0-100 ---
    semantic_skill_match = Column(Float, default=0)
    career_intelligence = Column(Float, default=0)
    behavior_score = Column(Float, default=0)
    context_alignment = Column(Float, default=0)
    resume_quality = Column(Float, default=0)
    trust_score = Column(Float, default=0)

    overall_score = Column(Float, default=0, index=True)
    confidence_score = Column(Float, default=0)
    confidence_band = Column(String, default="Medium")  # High | Medium | Low

    risk_level = Column(String, default="Medium")  # Low | Medium | High
    risk_reasons = Column(JSON, default=list)

    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)

    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    reasoning_text = Column(Text, nullable=True)
    recommendation = Column(String, nullable=True)
    counterfactual_text = Column(Text, nullable=True)

    weight_profile_used = Column(String, default="default")
    weights_applied = Column(JSON, default=dict)  # snapshot of weights at scoring time
    is_duplicate_of_candidate_id = Column(Integer, nullable=True)

    rank_position = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
