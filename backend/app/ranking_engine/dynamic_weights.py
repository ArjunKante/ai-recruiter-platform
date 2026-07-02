"""
Module 9: Dynamic Weight Engine.

Thin, deliberately, around config.ROLE_WEIGHT_PROFILES -- weights are DATA,
not logic, so they live in config.py where they're easy to audit and tune
without touching scoring code. This module is the only place that resolves
a JD to a profile and explains *why* in recruiter-readable language, which
is what gets surfaced under "Display active weights" in the UI.
"""
from __future__ import annotations

from typing import Any, Dict

from app.config import ROLE_WEIGHT_PROFILES, resolve_role_profile

WEIGHT_RATIONALE = {
    "default": "Balanced weighting across all six dimensions for general roles.",
    "backend_engineer": "Hands-on technical skill match is weighted heaviest (40%) -- for IC backend "
                         "roles, what a candidate has actually built predicts on-the-job success better "
                         "than tenure or behavioral signals alone.",
    "frontend_engineer": "Skill match leads (40%) with behavior weighted slightly above the backend "
                          "profile, reflecting the value of an active public portfolio for UI-focused roles.",
    "data_engineer": "Skill match and career trajectory dominate -- pipeline and modeling experience "
                      "compounds heavily with seniority in this track.",
    "product_manager": "Career trajectory and behavioral signals (stakeholder track record, "
                        "communication) outweigh specific tool skills, reflecting what actually predicts "
                        "PM success.",
    "engineering_manager": "Career trajectory (32%) and behavior/leadership signals (23%) dominate -- "
                            "team-building and delivery track record matter more than raw IC skill depth.",
    "designer": "Skill match and behavioral portfolio signals are weighted closely together, reflecting "
                "how design quality is judged through a body of work.",
    "sales": "Career trajectory and behavioral signals (quota attainment proxies, communication "
             "evidence) are weighted highest; specific tool skills matter least for this track.",
}


def get_weight_profile(jd_title: str) -> Dict[str, Any]:
    profile_key = resolve_role_profile(jd_title)
    weights = ROLE_WEIGHT_PROFILES[profile_key]
    return {
        "profile_key": profile_key,
        "weights": weights,
        "rationale": WEIGHT_RATIONALE.get(profile_key, WEIGHT_RATIONALE["default"]),
    }
