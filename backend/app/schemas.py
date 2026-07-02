"""
Pydantic schemas: the contract between the frontend and the API.

Kept in one module deliberately -- the project is hackathon-scoped, and a
single source of truth for every request/response shape is easier to audit
than a schema fragmented across a dozen tiny files.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Job description
# ---------------------------------------------------------------------------
class JobDescriptionCreate(BaseModel):
    title: str
    raw_text: str


class JobDescriptionOut(BaseModel):
    id: int
    title: str
    raw_text: str
    must_have_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    responsibilities: List[str] = []
    soft_skills: List[str] = []
    min_years_experience: int = 0
    domain: Optional[str] = None
    location: Optional[str] = None
    remote_policy: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    notice_period_days: Optional[int] = None
    role_weight_profile: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Candidate
# ---------------------------------------------------------------------------
class CandidateOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    location: Optional[str] = None
    github_url: Optional[str] = None
    source_filename: Optional[str] = None
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    skills: List[str] = []
    certifications: List[Dict[str, Any]] = []
    total_years_experience: int = 0
    notice_period_days: Optional[int] = None
    desired_salary: Optional[int] = None
    open_to_remote: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------
class ScoreBreakdown(BaseModel):
    semantic_skill_match: float
    career_intelligence: float
    behavior_score: float
    context_alignment: float
    resume_quality: float
    trust_score: float
    overall_score: float


class RankingResultOut(BaseModel):
    id: int
    candidate_id: int
    job_description_id: int
    candidate_name: str
    candidate_title: Optional[str] = None
    candidate_company: Optional[str] = None
    rank_position: Optional[int] = None

    scores: ScoreBreakdown
    confidence_score: float
    confidence_band: str
    risk_level: str
    risk_reasons: List[str] = []

    matched_skills: List[str] = []
    missing_skills: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    reasoning_text: Optional[str] = None
    recommendation: Optional[str] = None
    counterfactual_text: Optional[str] = None

    weight_profile_used: str
    weights_applied: Dict[str, float] = {}
    is_duplicate_of_candidate_id: Optional[int] = None

    class Config:
        from_attributes = True


class RankingRunRequest(BaseModel):
    job_description_id: int
    top_n: Optional[int] = None


class RankingRunStatus(BaseModel):
    job_description_id: int
    total_candidates: int
    processed: int
    status: str  # "running" | "complete" | "error"


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
class CompareRequest(BaseModel):
    job_description_id: int
    candidate_ids: List[int] = Field(min_length=2, max_length=4)


# ---------------------------------------------------------------------------
# Chat / NL search
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    job_description_id: int
    message: str
    history: List[Dict[str, str]] = []  # [{role, content}]


class ChatResponse(BaseModel):
    reply: str
    referenced_candidate_ids: List[int] = []


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
class ExportRequest(BaseModel):
    job_description_id: int
    format: str = Field(pattern="^(csv|xlsx|pdf)$")
    candidate_ids: Optional[List[int]] = None  # None = export full shortlist


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
class AuditLogOut(BaseModel):
    id: int
    actor_email: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    metadata_json: Dict[str, Any] = {}
    created_at: dt.datetime

    class Config:
        from_attributes = True


class PromptLogOut(BaseModel):
    id: int
    purpose: str
    candidate_id: Optional[int] = None
    job_description_id: Optional[int] = None
    prompt_text: str
    response_text: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: dt.datetime

    class Config:
        from_attributes = True
