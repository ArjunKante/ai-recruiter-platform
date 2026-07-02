"""
Module 5: Behavioral Intelligence.

GitHub activity is a REAL signal -- fetched live from GitHub's public REST
API (no auth required for low volume; set GITHUB_TOKEN to raise the rate
limit). Recruiter response / interview completion are ATS-interaction
signals that don't exist until a candidate has actually been through a
pipeline; they're intentionally left as neutral placeholders here with a
clear docstring rather than fabricated, and are wired up the moment an ATS
events table exists (see AuditLog for where that would plug in).
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Optional

import httpx

from app.config import get_settings

settings = get_settings()


def fetch_github_signal(github_url: Optional[str]) -> Dict[str, Any]:
    """Live call to the GitHub public API. Fails soft (returns neutral
    defaults) on any network/rate-limit error so a single slow/blocked
    lookup never breaks a ranking run."""
    default = {"available": False, "public_repos": 0, "followers": 0, "days_since_last_activity": None}
    if not github_url:
        return default

    username = github_url.rstrip("/").split("/")[-1]
    headers = {"Accept": "application/vnd.github+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    try:
        with httpx.Client(timeout=4.0) as client:
            user_resp = client.get(f"https://api.github.com/users/{username}", headers=headers)
            if user_resp.status_code != 200:
                return default
            user_data = user_resp.json()

            events_resp = client.get(
                f"https://api.github.com/users/{username}/events/public", headers=headers
            )
            days_since = None
            if events_resp.status_code == 200 and events_resp.json():
                latest = events_resp.json()[0]
                created = dt.datetime.strptime(latest["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                days_since = (dt.datetime.utcnow() - created).days

            return {
                "available": True,
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "days_since_last_activity": days_since,
            }
    except (httpx.HTTPError, httpx.TimeoutException, KeyError, ValueError):
        return default


def score_behavioral_intelligence(
    candidate: Dict[str, Any],
    github_signal: Dict[str, Any],
) -> Dict[str, Any]:
    # --- GitHub activity sub-score ---
    if github_signal.get("available"):
        repo_score = min(100, github_signal["public_repos"] * 6)
        follower_score = min(100, github_signal["followers"] * 2)
        days = github_signal.get("days_since_last_activity")
        recency_score = 100 if days is not None and days < 90 else (60 if days is not None and days < 365 else 30)
        github_score = round(0.5 * repo_score + 0.2 * follower_score + 0.3 * recency_score, 1)
    else:
        github_score = 55.0  # neutral -- absence of a public GitHub isn't a red flag for every role

    # --- profile completeness ---
    fields_present = sum([
        bool(candidate.get("email")),
        bool(candidate.get("phone")),
        bool(candidate.get("location")),
        len(candidate.get("skills", [])) >= 3,
        len(candidate.get("education", [])) >= 1,
        len(candidate.get("experience", [])) >= 1,
        bool(candidate.get("github_url")),
    ])
    completeness_score = round(100 * fields_present / 7, 1)

    # --- certification freshness ---
    certs = candidate.get("certifications", [])
    if certs:
        years = [c["year"] for c in certs if c.get("year")]
        most_recent = max(years) if years else None
        if most_recent is None:
            cert_score = 50.0
        else:
            age = dt.datetime.utcnow().year - most_recent
            cert_score = 100.0 if age <= 2 else (65.0 if age <= 5 else 35.0)
    else:
        cert_score = 60.0  # neutral -- not every strong candidate has certifications

    # --- recent activity (currently employed = strong signal; long gap = weaker) ---
    experience = candidate.get("experience", [])
    recent_score = 60.0
    if experience:
        most_recent_role = max(experience, key=lambda e: e.get("end") or "0000-00")
        if most_recent_role.get("is_current"):
            recent_score = 95.0
        elif most_recent_role.get("end"):
            try:
                end_date = dt.datetime.strptime(most_recent_role["end"], "%Y-%m")
                gap_months = (dt.datetime.utcnow() - end_date).days / 30
                recent_score = 85.0 if gap_months < 3 else (60.0 if gap_months < 9 else 35.0)
            except ValueError:
                pass

    score = round(
        0.25 * github_score + 0.30 * completeness_score + 0.20 * cert_score + 0.25 * recent_score, 1
    )

    return {
        "score": max(0.0, min(100.0, score)),
        "github_activity_score": github_score,
        "github_public_repos": github_signal.get("public_repos", 0) if github_signal.get("available") else None,
        "profile_completeness_pct": completeness_score,
        "certification_freshness_score": cert_score,
        "recent_activity_score": recent_score,
        "note": "Recruiter-response and interview-completion signals require live ATS interaction "
                "history and are not yet populated for freshly-uploaded candidates.",
    }
