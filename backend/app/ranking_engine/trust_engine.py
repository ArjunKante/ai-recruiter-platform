"""
Module 8: Trust Engine.

Starts every candidate at 100 and subtracts points for detected
inconsistencies. If the resulting score falls below
config.TRUST_HIGH_RISK_THRESHOLD, the candidate is automatically forced to
High Risk regardless of how strong their other scores are -- this mirrors
the product spec exactly ("If Trust Score < threshold, Candidate
automatically becomes High Risk").

Severity is calibrated so that ambiguous-but-explainable situations (an
employment gap, a missing degree on an otherwise strong resume) cost a
little, while hard contradictions (overlapping full-time roles at two
different companies, certifications dated before the candidate's career
began) cost a lot.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from app.config import get_settings

settings = get_settings()

PENALTIES = {
    "overlapping_employment": 30,
    "duplicate_experience_entry": 25,
    "suspicious_certification_date": 15,
    "unexplained_employment_gap": 8,
    "missing_education_for_senior_title": 5,
    "title_inflation": 10,
    "skill_inflation": 10,
}


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    if not all([a_start, a_end, b_start, b_end]):
        return False
    latest_start = max(a_start, b_start)
    earliest_end = min(a_end, b_end)
    overlap_days = (earliest_end - latest_start).days
    return overlap_days > 45  # small grace window for transition overlap


def score_trust(
    experience: List[Dict[str, Any]],
    education: List[Dict[str, Any]],
    certifications: List[Dict[str, Any]],
    total_years_experience: int,
    skills_count: int,
    title_inflation_detected: bool,
) -> Dict[str, Any]:
    flags: List[str] = []
    score = 100.0

    parsed = []
    for e in experience:
        try:
            s = dt.datetime.strptime(e["start"], "%Y-%m") if e.get("start") else None
            en = dt.datetime.strptime(e["end"], "%Y-%m") if e.get("end") else None
            parsed.append((e["company"], e["title"], s, en))
        except ValueError:
            continue

    # overlapping full-time roles at different companies
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            ci, ti, si, ei = parsed[i]
            cj, tj, sj, ej = parsed[j]
            if ci.strip().lower() != cj.strip().lower() and _overlaps(si, ei, sj, ej):
                flags.append(f"Overlapping employment detected between {ci} and {cj}")
                score -= PENALTIES["overlapping_employment"]

    # duplicate experience entries
    seen = set()
    for c, t, s, en in parsed:
        key = (c.strip().lower(), t.strip().lower(), s, en)
        if key in seen:
            flags.append(f"Duplicate experience entry detected for {c}")
            score -= PENALTIES["duplicate_experience_entry"]
        seen.add(key)

    # unexplained employment gaps (> 8 months between consecutive roles)
    sorted_roles = sorted([p for p in parsed if p[2] and p[3]], key=lambda p: p[2])
    for i in range(1, len(sorted_roles)):
        prev_end = sorted_roles[i - 1][3]
        cur_start = sorted_roles[i][2]
        gap_months = (cur_start - prev_end).days / 30
        if gap_months > 8:
            flags.append(f"Unexplained {int(gap_months)}-month employment gap before {sorted_roles[i][0]}")
            score -= PENALTIES["unexplained_employment_gap"]

    # suspicious certification dates (before any experience started)
    career_start = min((p[2] for p in parsed if p[2]), default=None)
    for cert in certifications:
        year = cert.get("year")
        if year and career_start and year < career_start.year - 1:
            flags.append(f"Certification '{cert['name']}' dated before candidate's career start")
            score -= PENALTIES["suspicious_certification_date"]
        if year and year > dt.datetime.utcnow().year:
            flags.append(f"Certification '{cert['name']}' has a future date")
            score -= PENALTIES["suspicious_certification_date"]

    # missing education for a senior-sounding title
    max_title_text = " ".join(e.get("title", "") for e in experience).lower()
    if not education and any(k in max_title_text for k in ["senior", "staff", "principal", "lead", "director"]):
        flags.append("No education history found despite senior-level title")
        score -= PENALTIES["missing_education_for_senior_title"]

    if title_inflation_detected:
        flags.append("Title progression appears unusually fast relative to total experience")
        score -= PENALTIES["title_inflation"]

    if skills_count > 25 and total_years_experience < 3:
        flags.append(f"Lists {skills_count} distinct skills with only {total_years_experience} year(s) of experience")
        score -= PENALTIES["skill_inflation"]

    score = max(0.0, min(100.0, score))
    force_high_risk = score < settings.TRUST_HIGH_RISK_THRESHOLD

    return {
        "score": round(score, 1),
        "flags": flags,
        "force_high_risk": force_high_risk,
    }
