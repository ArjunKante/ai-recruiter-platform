"""
Module 10: AI Recruiter Reasoning -- orchestration layer.

Calls the configured LLM with the grounded prompt from prompts/templates.py
and parses its JSON response. If no LLM provider is configured (no API key
set), falls back to a deterministic, evidence-based reasoning generator so
the platform is still fully demoable without any external credentials --
the rule-based fallback uses the exact same computed evidence, just
assembled with string templates instead of a model call.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict

from app.llm_service.claude_client import get_llm_client
from app.prompts.templates import build_recruiter_reasoning_prompt
from app.utils.helpers import setup_logger

logger = setup_logger("llm_service.reasoning_service")


def _strip_json_fences(text: str) -> str:
    return re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()


def generate_reasoning(candidate: Dict[str, Any], jd: Dict[str, Any], computed: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_recruiter_reasoning_prompt(candidate, jd, computed)
    client = get_llm_client()

    if client is None:
        result = _fallback_reasoning(candidate, jd, computed)
        return {**result, "prompt_text": prompt, "response_text": None, "model": "rule-based-fallback", "latency_ms": 0}

    try:
        raw_text, latency_ms = client.complete(prompt, max_tokens=700)
        parsed = json.loads(_strip_json_fences(raw_text))
        result = {
            "reasoning": parsed.get("reasoning", ""),
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
            "recommendation": parsed.get("recommendation", "Requires Further Review"),
            "counterfactual": parsed.get("counterfactual", ""),
        }
        return {**result, "prompt_text": prompt, "response_text": raw_text, "model": "claude", "latency_ms": latency_ms}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LLM reasoning call failed ({e}); using rule-based fallback for {candidate.get('name')}")
        result = _fallback_reasoning(candidate, jd, computed)
        return {**result, "prompt_text": prompt, "response_text": None, "model": "rule-based-fallback", "latency_ms": 0}


def _fallback_reasoning(candidate: Dict[str, Any], jd: Dict[str, Any], computed: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic, still evidence-grounded narrative built from the
    computed scores -- guarantees the platform works end-to-end with zero
    API keys configured."""
    matched = computed["matched_skills"]
    missing = computed["missing_skills"]
    evidence = computed["evidence"]
    overall = computed["scores"]["overall_score"]

    top_company = candidate["experience"][0]["company"] if candidate.get("experience") else "their most recent role"
    reasoning = (
        f"{candidate.get('name')} brings {candidate.get('total_years_experience', 0)} years of experience, "
        f"most recently at {top_company}. They match {len(matched)} of the role's key skills"
        + (f" ({', '.join(matched[:4])})" if matched else "")
        + f", scoring {overall}/100 overall. "
        + (f"Notable gaps: {', '.join(missing[:3])}. " if missing else "No critical skill gaps detected. ")
        + f"Career trajectory shows {evidence['career']['trajectory_note'].lower()}"
    )

    strengths = []
    if matched:
        strengths.append(f"Strong overlap on {', '.join(matched[:3])}")
    if evidence["career"]["promotion_events"] > 0:
        strengths.append(f"{evidence['career']['promotion_events']} promotion signal(s) in career history")
    if evidence["career"]["product_company_ratio_pct"] > 40:
        strengths.append("Significant product-company experience")
    if not strengths:
        strengths.append("Resume successfully parsed with structured experience history")

    weaknesses = []
    if missing:
        weaknesses.append(f"Missing required skills: {', '.join(missing[:3])}")
    if evidence["career"].get("job_hopping_flag"):
        weaknesses.append("Career history shows multiple short tenures")
    if evidence["trust"]["flags"]:
        weaknesses.append(evidence["trust"]["flags"][0])
    if not weaknesses:
        weaknesses.append("No major concerns identified by the rule engine")

    if overall >= 80 and computed["risk_level"] != "High":
        recommendation = "Proceed to Technical Round"
    elif overall >= 60:
        recommendation = "Schedule HR Screening"
    elif overall >= 40:
        recommendation = "Requires Further Review"
    else:
        recommendation = "Not Recommended"

    if missing:
        counterfactual = (
            f"Adding {missing[0]} experience would likely close the largest remaining gap "
            f"and meaningfully improve this candidate's overall score."
        )
    else:
        counterfactual = "This candidate already covers the required skill set; further gains would come from deeper trajectory or behavioral signals."

    return {
        "reasoning": reasoning,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendation": recommendation,
        "counterfactual": counterfactual,
    }
