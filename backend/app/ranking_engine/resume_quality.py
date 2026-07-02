"""
Module 7: Resume Quality Engine. Pure text heuristics over the raw resume
and parsed bullets -- fast and deterministic, runs on every resume before
any LLM call.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

ACTION_VERBS = {
    "architected", "led", "built", "designed", "implemented", "reduced", "increased",
    "launched", "mentored", "optimized", "automated", "migrated", "drove", "spearheaded",
    "delivered", "scaled", "improved", "developed", "created", "established", "owned",
    "managed", "engineered", "shipped", "streamlined", "accelerated", "founded",
}

METRIC_PATTERN = re.compile(
    r"(\d+(\.\d+)?\s?%|\$\d|\d+x\b|\b\d{2,}[,.]?\d*\s?(users|requests|ms|million|billion|engineers|customers))",
    re.I,
)


def score_resume_quality(raw_text: str, experience: List[Dict[str, Any]]) -> Dict[str, Any]:
    bullets = [b for e in experience for b in e.get("bullets", [])]
    word_count = len(raw_text.split())

    # length
    if word_count < 150:
        length_score = 40.0
    elif word_count > 1800:
        length_score = 55.0
    elif 350 <= word_count <= 1100:
        length_score = 100.0
    else:
        length_score = 80.0

    # action verbs
    if bullets:
        verb_hits = sum(1 for b in bullets if b.split()[0].lower().strip(".,") in ACTION_VERBS) if bullets else 0
        action_verb_score = round(100 * verb_hits / len(bullets), 1)
    else:
        action_verb_score = 40.0

    # quantified impact
    if bullets:
        metric_hits = sum(1 for b in bullets if METRIC_PATTERN.search(b))
        metrics_score = round(100 * metric_hits / len(bullets), 1)
    else:
        metrics_score = 30.0

    # ATS friendliness proxy: clear sections + contact info + no spam characters
    has_sections = bool(re.search(r"experience", raw_text, re.I)) and bool(re.search(r"education|skills", raw_text, re.I))
    has_contact = bool(re.search(r"@", raw_text))
    noise_ratio = len(re.findall(r"[^\w\s.,@:/\-()&%$+#]", raw_text)) / max(len(raw_text), 1)
    ats_score = 100.0
    if not has_sections:
        ats_score -= 30
    if not has_contact:
        ats_score -= 15
    if noise_ratio > 0.02:
        ats_score -= 20
    ats_score = max(0.0, ats_score)

    # grammar proxy (structural cleanliness, not a full NLP grammar pass)
    double_space = raw_text.count("  ")
    grammar_score = max(50.0, 100.0 - double_space * 2)

    score = (
        0.25 * action_verb_score
        + 0.30 * metrics_score
        + 0.15 * length_score
        + 0.20 * ats_score
        + 0.10 * grammar_score
    )

    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "word_count": word_count,
        "action_verb_score": action_verb_score,
        "quantified_impact_score": metrics_score,
        "length_score": length_score,
        "ats_friendliness_score": ats_score,
        "grammar_structure_score": round(grammar_score, 1),
    }
