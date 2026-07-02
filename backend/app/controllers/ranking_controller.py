from __future__ import annotations

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ranking_engine.ranking_engine import counterfactual_rank_estimate
from app.schemas import CompareRequest, RankingResultOut
from app.services.ranking_service import (
    compare_candidates,
    get_rankings_for_jd,
    run_ranking,
)


def handle_run_ranking(db: Session, job_description_id: int, actor_email: str | None) -> List[RankingResultOut]:
    try:
        rows = run_ranking(db, job_description_id, actor_email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    from app.services.ranking_service import ranking_result_to_out
    return [ranking_result_to_out(db, r) for r in rows]


def handle_get_rankings(db: Session, job_description_id: int) -> List[RankingResultOut]:
    results = get_rankings_for_jd(db, job_description_id)
    if not results:
        raise HTTPException(status_code=404, detail="No ranking results yet -- run ranking first")
    return results


def handle_compare(db: Session, payload: CompareRequest) -> List[RankingResultOut]:
    results = compare_candidates(db, payload.job_description_id, payload.candidate_ids)
    if len(results) < 2:
        raise HTTPException(status_code=400, detail="At least two valid candidates are required to compare")
    return results
