"""
Module 16: Recruiter Chat -- natural language search over an already-ranked
candidate pool. Deliberately does NOT let the LLM recompute or re-rank
anything; it only narrates/filters over the roster it's handed, which keeps
"frontend (and chat) must never calculate scores" true even for this
free-text feature.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.llm_service.claude_client import get_llm_client
from app.prompts.templates import build_chat_prompt
from app.utils.helpers import setup_logger

logger = setup_logger("llm_service.chat_service")

INTENT_PATTERNS = [
    (re.compile(r"low.?risk|safe(st)?\s+candidates?", re.I), "risk:Low"),
    (re.compile(r"high.?risk", re.I), "risk:High"),
    (re.compile(r"interview.?ready|technical round", re.I), "rec:Proceed to Technical Round"),
    (re.compile(r"leadership|managed|led a team", re.I), "leadership"),
    (re.compile(r"startup", re.I), "startup"),
    (re.compile(r"strongest|top|best", re.I), "top"),
]


def answer_chat_query(message: str, jd: Dict[str, Any], ranked_candidates: List[Dict[str, Any]]) -> Tuple[str, List[int]]:
    """Returns (reply_text, referenced_candidate_ids). Tries the LLM first
    for natural phrasing; falls back to simple intent matching + templated
    response if no LLM provider is configured."""
    client = get_llm_client()
    referenced_ids = _filter_by_intent(message, ranked_candidates)

    if client is not None:
        try:
            prompt = build_chat_prompt(message, jd, ranked_candidates)
            reply, _latency = client.complete(prompt, max_tokens=400)
            return reply.strip(), referenced_ids
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Chat LLM call failed ({e}); using rule-based fallback.")

    return _fallback_reply(message, ranked_candidates, referenced_ids), referenced_ids


def _filter_by_intent(message: str, ranked: List[Dict[str, Any]]) -> List[int]:
    for pattern, tag in INTENT_PATTERNS:
        if pattern.search(message):
            if tag.startswith("risk:"):
                level = tag.split(":")[1]
                return [c["candidate_id"] for c in ranked if c["risk_level"] == level]
            if tag.startswith("rec:"):
                rec = tag.split(":", 1)[1]
                return [c["candidate_id"] for c in ranked if c.get("recommendation") == rec]
            if tag == "top":
                return [c["candidate_id"] for c in ranked[:3]]
    return [c["candidate_id"] for c in ranked[:5]]


def _fallback_reply(message: str, ranked: List[Dict[str, Any]], referenced_ids: List[int]) -> str:
    matches = [c for c in ranked if c["candidate_id"] in referenced_ids]
    if not matches:
        return "I couldn't find candidates matching that query in the current ranked pool."
    names = ", ".join(f"{c['candidate_name']} ({c['scores']['overall_score']}/100)" for c in matches[:5])
    return f"Based on the current ranking, the most relevant candidates are: {names}."
