"""
Module 4: Career Intelligence Engine.

All signals here are derived purely from the structured experience entries
produced by resume_parser -- no LLM call, fully deterministic and auditable.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List

SENIORITY_LADDER = {
    "intern": 0, "trainee": 0,
    "junior": 1, "associate": 1,
    "engineer": 2, "developer": 2, "analyst": 2,
    "senior": 3,
    "staff": 4, "lead": 4, "tech lead": 4,
    "principal": 5, "manager": 5,
    "director": 6, "head": 6,
    "vp": 7, "vice president": 7, "cto": 8, "founder": 8,
}

LEADERSHIP_KEYWORDS = ["led ", "managed", "mentored", "head of", "manager", "director",
                       "vp ", "staff", "principal", "founder", "led a team", "team lead"]

CONSULTING_KEYWORDS = ["consulting", "consultancy", "freelance", "contract", "staffing"]

# A small curated set used only as a heuristic signal for "product company"
# classification. Real production systems would enrich this via a company
# database (Crunchbase/LinkedIn) rather than a static list.
KNOWN_PRODUCT_COMPANIES = {
    "google", "meta", "amazon", "microsoft", "apple", "netflix", "stripe", "uber",
    "airbnb", "linkedin", "shopify", "spotify", "salesforce", "adobe", "atlassian",
    "twitter", "x", "github", "gitlab", "datadog", "snowflake", "databricks",
}

ENTERPRISE_COMPANIES = {
    "ibm", "oracle", "sap", "accenture", "deloitte", "cognizant", "infosys",
    "tcs", "wipro", "capgemini", "morgan stanley", "goldman sachs", "jpmorgan",
}


def _seniority_of(title: str) -> int:
    t = title.lower()
    best = 2  # default to "engineer"-equivalent if nothing matches
    for kw, level in SENIORITY_LADDER.items():
        if kw in t:
            best = max(best, level)
    return best


def _is_consulting(company: str) -> bool:
    c = company.lower()
    return any(kw in c for kw in CONSULTING_KEYWORDS)


def score_career_intelligence(
    experience: List[Dict[str, Any]],
    total_years_experience: int,
    min_years_required: int,
) -> Dict[str, Any]:
    if not experience:
        return {
            "score": 35.0,
            "years_of_experience": total_years_experience,
            "average_tenure_months": 0,
            "promotion_events": 0,
            "job_hopping_flag": False,
            "leadership_progression": False,
            "product_company_ratio_pct": 0,
            "consulting_ratio_pct": 0,
            "title_inflation_detected": False,
            "trajectory_note": "No structured experience could be parsed from this resume.",
        }

    months_list = [e.get("months", 0) for e in experience if e.get("months")]
    avg_tenure = sum(months_list) / len(months_list) if months_list else 0

    short_stints = [e for e in experience if 0 < e.get("months", 0) < 12]
    job_hopping_flag = len(short_stints) >= 2

    promotion_events = sum(
        1 for e in experience for b in e.get("bullets", []) if "promot" in b.lower()
    )
    # also detect same-company consecutive entries (title change without company change)
    for i in range(1, len(experience)):
        if experience[i]["company"].strip().lower() == experience[i - 1]["company"].strip().lower():
            if _seniority_of(experience[i]["title"]) > _seniority_of(experience[i - 1]["title"]):
                promotion_events += 1

    all_text = " ".join(e.get("title", "") + " " + " ".join(e.get("bullets", [])) for e in experience).lower()
    leadership_progression = any(kw in all_text for kw in LEADERSHIP_KEYWORDS)

    total_months = sum(e.get("months", 0) for e in experience) or 1
    product_months = sum(
        e.get("months", 0) for e in experience if e["company"].strip().lower() in KNOWN_PRODUCT_COMPANIES
    )
    enterprise_months = sum(
        e.get("months", 0) for e in experience if e["company"].strip().lower() in ENTERPRISE_COMPANIES
    )
    consulting_months = sum(e.get("months", 0) for e in experience if _is_consulting(e["company"]))

    product_ratio = product_months / total_months
    consulting_ratio = consulting_months / total_months

    # Title inflation heuristic: a "senior+" title held with very little
    # total career experience behind it.
    max_seniority = max((_seniority_of(e["title"]) for e in experience), default=2)
    title_inflation = max_seniority >= 3 and total_years_experience < 3

    # --- sub-scores, each 0-100 ---
    years_fit = 100.0 if min_years_required == 0 else max(
        0.0, min(100.0, 100 * (total_years_experience / max(min_years_required, 1)))
    )
    years_fit = min(years_fit, 100.0 if total_years_experience >= min_years_required else years_fit)

    tenure_stability = 100.0
    if avg_tenure < 12:
        tenure_stability = 45.0
    elif avg_tenure < 18:
        tenure_stability = 70.0
    elif avg_tenure < 24:
        tenure_stability = 85.0

    trajectory = 50.0
    trajectory += 20 if promotion_events > 0 else 0
    trajectory += 15 if leadership_progression else 0
    trajectory += 15 * product_ratio
    trajectory -= 15 * consulting_ratio
    trajectory -= 10 if title_inflation else 0
    trajectory = max(0.0, min(100.0, trajectory))

    company_quality = 100 * product_ratio + 60 * (enterprise_months / total_months) + 40 * (
        1 - product_ratio - (enterprise_months / total_months) - consulting_ratio
    )
    company_quality = max(0.0, min(100.0, company_quality))

    score = 0.30 * years_fit + 0.25 * tenure_stability + 0.25 * trajectory + 0.20 * company_quality
    if job_hopping_flag:
        score -= 8
    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "years_of_experience": total_years_experience,
        "average_tenure_months": round(avg_tenure, 1),
        "promotion_events": promotion_events,
        "job_hopping_flag": job_hopping_flag,
        "leadership_progression": leadership_progression,
        "product_company_ratio_pct": round(product_ratio * 100, 1),
        "consulting_ratio_pct": round(consulting_ratio * 100, 1),
        "title_inflation_detected": title_inflation,
        "trajectory_note": (
            f"{promotion_events} promotion signal(s) detected, "
            f"{'with' if leadership_progression else 'without'} clear leadership progression."
        ),
    }
