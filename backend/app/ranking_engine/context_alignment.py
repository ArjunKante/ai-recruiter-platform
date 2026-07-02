"""
Module 6: Context Alignment -- logistics fit between candidate and role
(notice period, salary, remote/hybrid/onsite, location). All deterministic.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def _remote_fit(candidate_pref: Optional[str], jd_policy: Optional[str]) -> float:
    if not jd_policy or not candidate_pref:
        return 70.0
    if candidate_pref == jd_policy:
        return 100.0
    if jd_policy == "hybrid" and candidate_pref in ("remote", "onsite"):
        return 65.0
    if jd_policy == "remote" and candidate_pref == "onsite":
        return 40.0
    if jd_policy == "onsite" and candidate_pref == "remote":
        return 30.0
    return 60.0


def _location_fit(candidate_location: Optional[str], jd_location: Optional[str], jd_policy: Optional[str]) -> float:
    if jd_policy == "remote":
        return 100.0
    if not candidate_location or not jd_location:
        return 65.0
    c, j = candidate_location.lower(), jd_location.lower()
    if c == j:
        return 100.0
    c_state = c.split(",")[-1].strip() if "," in c else c
    j_state = j.split(",")[-1].strip() if "," in j else j
    if c_state and c_state == j_state:
        return 75.0
    return 40.0


def _salary_fit(desired: Optional[int], jd_min: Optional[float], jd_max: Optional[float]) -> float:
    if desired is None or (jd_min is None and jd_max is None):
        return 75.0
    ceiling = jd_max or jd_min
    if desired <= ceiling:
        return 100.0
    overage = (desired - ceiling) / ceiling
    if overage <= 0.10:
        return 70.0
    if overage <= 0.25:
        return 40.0
    return 15.0


def _notice_fit(candidate_days: Optional[int], jd_days: Optional[int]) -> float:
    jd_days = jd_days or 30
    if candidate_days is None:
        return 70.0
    if candidate_days <= jd_days:
        return 100.0
    overage = candidate_days - jd_days
    if overage <= 15:
        return 70.0
    if overage <= 30:
        return 45.0
    return 20.0


def score_context_alignment(candidate: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    remote_score = _remote_fit(candidate.get("open_to_remote"), jd.get("remote_policy"))
    location_score = _location_fit(candidate.get("location"), jd.get("location"), jd.get("remote_policy"))
    salary_score = _salary_fit(candidate.get("desired_salary"), jd.get("salary_min"), jd.get("salary_max"))
    notice_score = _notice_fit(candidate.get("notice_period_days"), jd.get("notice_period_days"))

    score = 0.30 * remote_score + 0.20 * location_score + 0.30 * salary_score + 0.20 * notice_score

    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "remote_fit_score": remote_score,
        "location_fit_score": location_score,
        "salary_fit_score": salary_score,
        "notice_period_fit_score": notice_score,
    }
