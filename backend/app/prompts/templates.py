"""
Module 10: AI Recruiter Reasoning -- prompt templates.

Kept as plain Python functions (not an external template engine) so they're
easy to read, diff, and log verbatim via PromptLog. The golden rule baked
into every prompt here: the LLM is handed the ALREADY-COMPUTED scores and
evidence from the rule engines and asked to narrate them, never to invent
its own numbers. This is what keeps reasoning grounded in actual resume
evidence instead of producing generic AI filler text.
"""
from __future__ import annotations

import json
from typing import Any, Dict


def build_recruiter_reasoning_prompt(candidate: Dict[str, Any], jd: Dict[str, Any], computed: Dict[str, Any]) -> str:
    evidence = computed["evidence"]
    experience_summary = "\n".join(
        f"- {e['title']} at {e['company']} ({e.get('start', '?')} to {e.get('end', 'present')}): "
        + "; ".join(e.get("bullets", [])[:3])
        for e in candidate.get("experience", [])[:5]
    )

    return f"""You are a senior technical recruiter with 15+ years of experience evaluating engineering and product candidates. You have already been given precise, computed scores for this candidate -- your job is to explain them like a recruiter would in a hiring debrief, citing specific evidence from the resume. Never invent scores or facts not present below. Never produce generic filler text ("great candidate", "strong fit") without tying it to a specific fact.

JOB: {jd.get('title')}
Must-have skills: {', '.join(jd.get('must_have_skills', [])) or 'none specified'}
Nice-to-have skills: {', '.join(jd.get('nice_to_have_skills', [])) or 'none specified'}
Minimum years experience: {jd.get('min_years_experience', 0)}

CANDIDATE: {candidate.get('name')}
Total experience: {candidate.get('total_years_experience')} years
Career history:
{experience_summary or 'No structured experience parsed.'}

COMPUTED SCORES (already final -- do not change these numbers):
- Semantic skill match: {computed['scores']['semantic_skill_match']}/100 (matched: {', '.join(computed['matched_skills']) or 'none'}; missing: {', '.join(computed['missing_skills']) or 'none'})
- Career intelligence: {computed['scores']['career_intelligence']}/100 ({evidence['career']['trajectory_note']}, avg tenure {evidence['career']['average_tenure_months']} months, {evidence['career']['promotion_events']} promotion signal(s))
- Behavior score: {computed['scores']['behavior_score']}/100 (GitHub repos: {evidence['behavior'].get('github_public_repos')}, profile completeness {evidence['behavior']['profile_completeness_pct']}%)
- Context alignment: {computed['scores']['context_alignment']}/100
- Resume quality: {computed['scores']['resume_quality']}/100
- Trust score: {computed['scores']['trust_score']}/100 (flags: {', '.join(evidence['trust']['flags']) or 'none'})
- Overall: {computed['scores']['overall_score']}/100
- Confidence: {computed['confidence_score']}% ({computed['confidence_band']})
- Risk level: {computed['risk_level']} -- {'; '.join(computed['risk_reasons'])}

Return ONLY valid JSON (no markdown fences, no preamble) with this exact shape:
{{
  "reasoning": "2-4 sentence recruiter-style paragraph citing specific companies, technologies, or metrics from the resume above",
  "strengths": ["specific strength citing real evidence", "..."],
  "weaknesses": ["specific concern citing real evidence", "..."],
  "recommendation": "one of: Proceed to Technical Round | Schedule HR Screening | Requires Further Review | Not Recommended",
  "counterfactual": "one sentence: what specific change would most improve this candidate's ranking, and roughly how much"
}}"""


def build_chat_prompt(message: str, jd: Dict[str, Any], ranked_candidates: list[Dict[str, Any]]) -> str:
    roster = "\n".join(
        f"{i+1}. {c['candidate_name']} -- overall {c['scores']['overall_score']}/100, "
        f"risk {c['risk_level']}, confidence {c['confidence_band']}, "
        f"recommendation: {c.get('recommendation')}, "
        f"matched skills: {', '.join(c.get('matched_skills', [])[:6])}, "
        f"missing: {', '.join(c.get('missing_skills', [])[:4]) or 'none'}"
        for i, c in enumerate(ranked_candidates)
    )
    return f"""You are an AI recruiting assistant answering a recruiter's natural-language question about an already-ranked candidate pool. Answer concisely, reference specific candidate names, and only use information present in the roster below -- never invent a candidate or fact that isn't listed.

JOB: {jd.get('title')}

RANKED CANDIDATE ROSTER:
{roster}

RECRUITER QUESTION: {message}

Answer in 2-5 sentences, recruiter tone, citing specific names from the roster above."""
