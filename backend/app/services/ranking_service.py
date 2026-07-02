"""
The ranking pipeline orchestrator. This is the one place that touches the
DB, the vector store, the rule engines, AND the LLM service -- everything
downstream of here is either pure computation (ranking_engine/*) or pure
persistence (models). Keeping this orchestration in one service makes the
full request -> response flow easy to trace for a single ranking run.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.audit import AuditLog, PromptLog
from app.models.candidate import Candidate
from app.models.ranking import RankingResult
from app.ranking_engine.ranking_engine import (
    compute_full_score,
    counterfactual_rank_estimate,
    detect_duplicate_candidates,
)
from app.services.candidate_service import candidate_to_dict, list_candidates_for_jd
from app.services.jd_service import get_job_description, jd_to_dict
from app.vector_store.faiss_index import CandidateVectorIndex
from app.llm_service.reasoning_service import generate_reasoning
from app.utils.helpers import setup_logger

logger = setup_logger("services.ranking_service")


def run_ranking(db: Session, job_description_id: int, actor_email: str | None = None) -> List[RankingResult]:
    jd = get_job_description(db, job_description_id)
    if jd is None:
        raise ValueError("Job description not found")
    candidates = list_candidates_for_jd(db, job_description_id)
    if not candidates:
        raise ValueError("No candidates uploaded for this job description yet")

    jd_dict = jd_to_dict(jd)
    candidate_dicts = {c.id: candidate_to_dict(c) for c in candidates}

    # --- build one vector index over the whole candidate pool for this JD ---
    index = CandidateVectorIndex()
    ids = list(candidate_dicts.keys())
    texts = [candidate_dicts[cid]["raw_resume_text"] for cid in ids]
    index.build(ids, texts)
    similarity_results = dict(index.query(jd_dict["raw_text"], top_k=len(ids)))

    # clear any previous ranking results for this JD so re-runs don't duplicate rows
    db.query(RankingResult).filter(RankingResult.job_description_id == job_description_id).delete()
    db.commit()

    computed_by_id: Dict[int, Dict[str, Any]] = {}
    ranking_rows: List[RankingResult] = []

    for cid in ids:
        candidate_dict = candidate_dicts[cid]
        doc_similarity = similarity_results.get(cid, 0.5)
        computed = compute_full_score(candidate_dict, jd_dict, doc_similarity)
        computed_by_id[cid] = computed

        reasoning_payload = generate_reasoning(candidate_dict, jd_dict, computed)

        row = RankingResult(
            candidate_id=cid,
            job_description_id=job_description_id,
            semantic_skill_match=computed["scores"]["semantic_skill_match"],
            career_intelligence=computed["scores"]["career_intelligence"],
            behavior_score=computed["scores"]["behavior_score"],
            context_alignment=computed["scores"]["context_alignment"],
            resume_quality=computed["scores"]["resume_quality"],
            trust_score=computed["scores"]["trust_score"],
            overall_score=computed["scores"]["overall_score"],
            confidence_score=computed["confidence_score"],
            confidence_band=computed["confidence_band"],
            risk_level=computed["risk_level"],
            risk_reasons=computed["risk_reasons"],
            matched_skills=computed["matched_skills"],
            missing_skills=computed["missing_skills"],
            strengths=reasoning_payload["strengths"],
            weaknesses=reasoning_payload["weaknesses"],
            reasoning_text=reasoning_payload["reasoning"],
            recommendation=reasoning_payload["recommendation"],
            counterfactual_text=reasoning_payload["counterfactual"],
            weight_profile_used=computed["weight_profile_used"],
            weights_applied=computed["weights_applied"],
        )
        db.add(row)
        ranking_rows.append(row)

        db.add(PromptLog(
            purpose="recruiter_reasoning",
            candidate_id=cid,
            job_description_id=job_description_id,
            prompt_text=reasoning_payload["prompt_text"],
            response_text=reasoning_payload["response_text"],
            model=reasoning_payload["model"],
            latency_ms=reasoning_payload["latency_ms"],
        ))

    db.commit()

    # --- rank, assign positions, detect duplicates ---
    ranking_rows.sort(key=lambda r: r.overall_score, reverse=True)
    for i, row in enumerate(ranking_rows, start=1):
        row.rank_position = i

    sim_matrix = index.pairwise_similarity_matrix()
    duplicates = detect_duplicate_candidates(ids, sim_matrix)
    for row in ranking_rows:
        if row.candidate_id in duplicates:
            row.is_duplicate_of_candidate_id = duplicates[row.candidate_id]

    db.commit()

    db.add(AuditLog(
        actor_email=actor_email,
        action="RANKING_RUN",
        target_type="job_description",
        target_id=job_description_id,
        metadata_json={"candidate_count": len(ids)},
    ))
    db.commit()

    for row in ranking_rows:
        db.refresh(row)
    return ranking_rows


def _display_title_company(candidate: Candidate) -> tuple[str | None, str | None]:
    exp = candidate.experience or []
    if not exp:
        return None, None
    most_recent = exp[0]
    return most_recent.get("title"), most_recent.get("company")


def ranking_result_to_out(db: Session, row: RankingResult) -> Dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.id == row.candidate_id).first()
    title, company = _display_title_company(candidate) if candidate else (None, None)
    return {
        "id": row.id,
        "candidate_id": row.candidate_id,
        "job_description_id": row.job_description_id,
        "candidate_name": candidate.name if candidate else "Unknown",
        "candidate_title": title,
        "candidate_company": company,
        "rank_position": row.rank_position,
        "scores": {
            "semantic_skill_match": row.semantic_skill_match,
            "career_intelligence": row.career_intelligence,
            "behavior_score": row.behavior_score,
            "context_alignment": row.context_alignment,
            "resume_quality": row.resume_quality,
            "trust_score": row.trust_score,
            "overall_score": row.overall_score,
        },
        "confidence_score": row.confidence_score,
        "confidence_band": row.confidence_band,
        "risk_level": row.risk_level,
        "risk_reasons": row.risk_reasons or [],
        "matched_skills": row.matched_skills or [],
        "missing_skills": row.missing_skills or [],
        "strengths": row.strengths or [],
        "weaknesses": row.weaknesses or [],
        "reasoning_text": row.reasoning_text,
        "recommendation": row.recommendation,
        "counterfactual_text": row.counterfactual_text,
        "weight_profile_used": row.weight_profile_used,
        "weights_applied": row.weights_applied or {},
        "is_duplicate_of_candidate_id": row.is_duplicate_of_candidate_id,
    }


def get_rankings_for_jd(db: Session, job_description_id: int) -> List[Dict[str, Any]]:
    rows = (
        db.query(RankingResult)
        .filter(RankingResult.job_description_id == job_description_id)
        .order_by(RankingResult.rank_position.asc())
        .all()
    )
    return [ranking_result_to_out(db, r) for r in rows]


def get_ranking_detail(db: Session, job_description_id: int, candidate_id: int) -> Dict[str, Any] | None:
    row = (
        db.query(RankingResult)
        .filter(
            RankingResult.job_description_id == job_description_id,
            RankingResult.candidate_id == candidate_id,
        )
        .first()
    )
    return ranking_result_to_out(db, row) if row else None


def compare_candidates(db: Session, job_description_id: int, candidate_ids: List[int]) -> List[Dict[str, Any]]:
    rows = (
        db.query(RankingResult)
        .filter(
            RankingResult.job_description_id == job_description_id,
            RankingResult.candidate_id.in_(candidate_ids),
        )
        .all()
    )
    return [ranking_result_to_out(db, r) for r in rows]
