from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.llm_service.chat_service import answer_chat_query
from app.schemas import ChatRequest, ChatResponse
from app.services.jd_service import get_job_description, jd_to_dict
from app.services.ranking_service import get_rankings_for_jd


def handle_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    jd = get_job_description(db, payload.job_description_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    ranked = get_rankings_for_jd(db, payload.job_description_id)
    if not ranked:
        raise HTTPException(status_code=400, detail="Run ranking before using chat search")

    reply, referenced_ids = answer_chat_query(payload.message, jd_to_dict(jd), ranked)
    return ChatResponse(reply=reply, referenced_candidate_ids=referenced_ids)
