#!/usr/bin/env python3
"""
Seed script: loads the sample job description and all 6 sample resumes,
then triggers a full ranking run. Run this once after `uvicorn` starts to
populate the platform with demonstration data:

    cd backend
    python seed.py

The script calls the running FastAPI server at localhost:8000 so the server
must be started first.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import httpx

BASE_URL = os.getenv("SEED_API_URL", "http://localhost:8000/api")
SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


def main():
    print("🌱 TalentAI seed script")
    print(f"   API: {BASE_URL}")
    print(f"   Data dir: {SAMPLE_DIR}\n")

    # 1. health check
    try:
        r = httpx.get(BASE_URL.replace("/api", "/health"), timeout=5)
        r.raise_for_status()
        print("✓ API is up")
    except Exception as e:
        print(f"✗ API not reachable: {e}\n  Start the server first: uvicorn app.main:app --reload")
        sys.exit(1)

    # 2. register demo admin user
    user_payload = {"email": "admin@talentai.demo", "full_name": "Demo Admin", "password": "TalentAI2025!"}
    r = httpx.post(f"{BASE_URL}/auth/register", json=user_payload, timeout=10)
    if r.status_code in (200, 201):
        token = r.json()["access_token"]
        print(f"✓ Registered demo user: {user_payload['email']}")
    elif r.status_code == 400:
        r2 = httpx.post(f"{BASE_URL}/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]}, timeout=10)
        token = r2.json()["access_token"]
        print(f"✓ Logged in as existing user: {user_payload['email']}")
    else:
        print(f"  Could not create user ({r.status_code}) — proceeding unauthenticated")
        token = None

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 3. create job description
    jd_file = SAMPLE_DIR / "senior_backend_engineer_jd.txt"
    jd_text = jd_file.read_text()
    r = httpx.post(
        f"{BASE_URL}/jobs",
        json={"title": "Senior Backend Engineer", "raw_text": jd_text},
        headers=headers,
        timeout=30,
    )
    r.raise_for_status()
    jd = r.json()
    jd_id = jd["id"]
    print(f"✓ Created job: '{jd['title']}' (id={jd_id})")
    print(f"  Must-have skills: {', '.join(jd['must_have_skills'][:6])}")

    # 4. upload resumes
    resume_files = sorted((SAMPLE_DIR / "resumes").glob("*.txt"))
    if not resume_files:
        print("✗ No sample resumes found in sample_data/resumes/")
        sys.exit(1)

    print(f"\n📄 Uploading {len(resume_files)} resumes...")
    files = [("files", (f.name, f.read_bytes(), "text/plain")) for f in resume_files]
    r = httpx.post(
        f"{BASE_URL}/jobs/{jd_id}/candidates",
        files=files,
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    candidates = r.json()
    for c in candidates:
        print(f"  ✓ {c['name']} — {c['total_years_experience']}yr exp, {len(c['skills'])} skills")

    # 5. run ranking
    print(f"\n🧠 Running full ranking pipeline (Claude AI reasoning)...")
    print("   This may take 30-90 seconds depending on LLM provider...\n")
    r = httpx.post(
        f"{BASE_URL}/jobs/{jd_id}/rank",
        headers=headers,
        timeout=300,
    )
    r.raise_for_status()
    results = r.json()
    results.sort(key=lambda x: x.get("rank_position") or 99)

    print("🏆 RANKING RESULTS:\n")
    print(f"{'Rank':<5} {'Candidate':<28} {'Score':<7} {'Risk':<8} {'Confidence':<12} Recommendation")
    print("─" * 90)
    for r_item in results:
        print(
            f"  #{r_item.get('rank_position'):<4}"
            f"{r_item['candidate_name']:<28}"
            f"{r_item['scores']['overall_score']:<7.1f}"
            f"{r_item['risk_level']:<8}"
            f"{r_item['confidence_score']:.0f}% {r_item.get('confidence_band',''):<8}"
            f"{r_item.get('recommendation','')}"
        )

    print(f"\n✅ Seed complete! Open http://localhost:3000 to view the dashboard.")
    print(f"   Job ID: {jd_id}  |  API docs: http://localhost:8000/docs")
    print(f"   Admin login: {user_payload['email']} / {user_payload['password']}")


if __name__ == "__main__":
    main()
