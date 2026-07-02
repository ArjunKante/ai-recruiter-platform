"""
Module 11/12 + Ranking Engine: combines the six component scores into a
final weighted overall score, derives a confidence score/band, and derives
a hiring risk level with concrete reasons. This is pure computation with no
DB or LLM dependency -- everything here is unit-testable in isolation.

The LLM (llm_service.reasoning_service) is called AFTER this, and is handed
this module's full output as grounding context -- it narrates and explains
real computed numbers, it never invents its own scores.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.ranking_engine.behavioral_intelligence import fetch_github_signal, score_behavioral_intelligence
from app.ranking_engine.career_intelligence import score_career_intelligence
from app.ranking_engine.context_alignment import score_context_alignment
from app.ranking_engine.dynamic_weights import get_weight_profile
from app.ranking_engine.resume_quality import score_resume_quality
from app.ranking_engine.semantic_matcher import score_semantic_match
from app.ranking_engine.trust_engine import score_trust


def compute_full_score(candidate: Dict[str, Any], jd: Dict[str, Any], doc_similarity: float) -> Dict[str, Any]:
    """Run all six scoring engines for one (candidate, JD) pair and combine
    them with the JD's resolved dynamic weight profile."""

    semantic = score_semantic_match(
        candidate.get("skills", []),
        jd.get("must_have_skills", []),
        jd.get("nice_to_have_skills", []),
        doc_similarity,
    )
    career = score_career_intelligence(
        candidate.get("experience", []),
        candidate.get("total_years_experience", 0),
        jd.get("min_years_experience", 0),
    )
    github_signal = fetch_github_signal(candidate.get("github_url"))
    behavior = score_behavioral_intelligence(candidate, github_signal)
    context = score_context_alignment(candidate, jd)
    quality = score_resume_quality(candidate.get("raw_resume_text", ""), candidate.get("experience", []))
    trust = score_trust(
        candidate.get("experience", []),
        candidate.get("education", []),
        candidate.get("certifications", []),
        candidate.get("total_years_experience", 0),
        len(candidate.get("skills", [])),
        career.get("title_inflation_detected", False),
    )

    weight_info = get_weight_profile(jd.get("title", ""))
    weights = weight_info["weights"]

    component_scores = {
        "semantic_skill_match": semantic["score"],
        "career_intelligence": career["score"],
        "behavior_score": behavior["score"],
        "context_alignment": context["score"],
        "resume_quality": quality["score"],
        "trust_score": trust["score"],
    }

    overall = sum(component_scores[k] * (weights[k] / 100.0) for k in component_scores)
    overall = round(max(0.0, min(100.0, overall)), 1)

    confidence = _compute_confidence(candidate, semantic, trust, behavior)
    risk_level, risk_reasons = _compute_risk(candidate, jd, semantic, career, context, trust, behavior)

    return {
        "scores": {**component_scores, "overall_score": overall},
        "confidence_score": confidence["score"],
        "confidence_band": confidence["band"],
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "matched_skills": semantic["matched_skills"],
        "missing_skills": semantic["missing_skills"],
        "weight_profile_used": weight_info["profile_key"],
        "weights_applied": weights,
        "weight_rationale": weight_info["rationale"],
        "evidence": {
            "semantic": semantic,
            "career": career,
            "behavior": behavior,
            "context": context,
            "quality": quality,
            "trust": trust,
        },
    }


def _compute_confidence(candidate, semantic, trust, behavior) -> Dict[str, Any]:
    completeness = behavior.get("profile_completeness_pct", 50)
    # a match near 50% is genuinely ambiguous; matches near 0 or 100 are decisive
    decisiveness = abs(semantic["score"] - 50) * 2
    trust_component = trust["score"]
    evidence_quality = 100 if candidate.get("experience") and candidate.get("skills") else 55

    score = round(0.30 * completeness + 0.25 * decisiveness + 0.25 * trust_component + 0.20 * evidence_quality, 1)
    score = max(0.0, min(100.0, score))
    band = "High" if score >= 75 else ("Medium" if score >= 45 else "Low")
    return {"score": score, "band": band}


def _compute_risk(candidate, jd, semantic, career, context, trust, behavior) -> tuple[str, List[str]]:
    if trust.get("force_high_risk"):
        return "High", (trust["flags"][:3] or ["Trust score fell below the platform's risk threshold."])

    reasons: List[str] = []
    risk_points = 0

    if career.get("job_hopping_flag"):
        risk_points += 25
        reasons.append(f"Frequent job changes -- average tenure of {career.get('average_tenure_months', 0):.0f} months")

    if context.get("salary_fit_score", 100) < 50:
        risk_points += 20
        reasons.append("Desired salary appears significantly above the role's budget")

    if context.get("notice_period_fit_score", 100) < 50:
        risk_points += 12
        reasons.append("Notice period is longer than this role typically allows")

    if len(semantic.get("missing_skills", [])) >= 3:
        risk_points += 20
        reasons.append(f"Missing {len(semantic['missing_skills'])} required skill(s): "
                        f"{', '.join(semantic['missing_skills'][:3])}")

    if behavior.get("recent_activity_score", 100) < 45:
        risk_points += 10
        reasons.append("Resume suggests an extended gap since the candidate's last role")

    if trust.get("score", 100) < 75:
        risk_points += 10
        reasons.append("Minor inconsistencies detected during trust verification")

    if risk_points >= 45:
        level = "High"
    elif risk_points >= 20:
        level = "Medium"
    else:
        level = "Low"
        if not reasons:
            reasons.append("No material risk signals detected.")

    return level, reasons[:4]


def detect_duplicate_candidates(candidate_ids: List[int], similarity_matrix, threshold: float = 0.93) -> Dict[int, int]:
    """Bonus feature: flag candidates whose resumes are near-identical in
    vector space (e.g. the same person uploaded twice, or a templated
    resume reused with light edits). Returns {candidate_id: duplicate_of_id}."""
    duplicates: Dict[int, int] = {}
    n = len(candidate_ids)
    for i in range(n):
        if candidate_ids[i] in duplicates:
            continue
        for j in range(i + 1, n):
            if candidate_ids[j] in duplicates:
                continue
            sim = (similarity_matrix[i][j] + 1.0) / 2.0
            if sim >= threshold:
                duplicates[candidate_ids[j]] = candidate_ids[i]
    return duplicates


def counterfactual_rank_estimate(
    current_overall: float, missing_skills: List[str], current_rank: int, all_scores_sorted: List[float]
) -> str:
    """Module 14: Counterfactual Recommendations -- a quick deterministic
    estimate of rank movement, used as a fallback / sanity check alongside
    the richer LLM-generated counterfactual narrative."""
    if not missing_skills:
        return "Already meets all required skills for this role."
    # naive but defensible: each missing must-have skill is worth ~6 points if added
    projected = min(100.0, current_overall + 6 * min(len(missing_skills), 2))
    projected_rank = sum(1 for s in all_scores_sorted if s > projected) + 1
    if projected_rank < current_rank:
        return (
            f"Adding {', '.join(missing_skills[:2])} could raise the overall score to "
            f"~{projected:.0f} and move this candidate from rank {current_rank} to approximately rank {projected_rank}."
        )
    return "Closing the listed skill gaps would modestly strengthen this profile but is unlikely to change rank materially."
