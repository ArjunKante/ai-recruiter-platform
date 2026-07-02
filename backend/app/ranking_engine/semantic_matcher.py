"""
Module 3: Semantic Skill Matching.

Deliberately NOT keyword matching. Score blends three signals:
  1. Canonical must-have skill coverage (alias-normalized, so "NodeJS" /
     "Node.js" / "Express backend" all count as the same skill)
  2. Canonical nice-to-have skill coverage
  3. Whole-document semantic similarity from the vector store (catches
     conceptual matches that no alias dictionary entry would, e.g. a
     candidate describing "asynchronous event-driven processing" against a
     JD asking for "message queue experience")
"""
from __future__ import annotations

from typing import Any, Dict, List


def score_semantic_match(
    candidate_skills: List[str],
    must_have_skills: List[str],
    nice_to_have_skills: List[str],
    doc_similarity: float,
) -> Dict[str, Any]:
    candidate_set = set(s.lower() for s in candidate_skills)
    must_set = [s.lower() for s in must_have_skills]
    nice_set = [s.lower() for s in nice_to_have_skills]

    matched_must = [s for s in must_set if s in candidate_set]
    missing_must = [s for s in must_set if s not in candidate_set]
    matched_nice = [s for s in nice_set if s in candidate_set]

    must_coverage = len(matched_must) / len(must_set) if must_set else 1.0
    nice_coverage = len(matched_nice) / len(nice_set) if nice_set else 1.0

    score = 100 * (0.60 * must_coverage + 0.15 * nice_coverage + 0.25 * doc_similarity)
    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "matched_skills": sorted(set(matched_must + matched_nice)),
        "missing_skills": sorted(missing_must),
        "must_have_coverage_pct": round(must_coverage * 100, 1),
        "nice_to_have_coverage_pct": round(nice_coverage * 100, 1),
        "doc_semantic_similarity_pct": round(doc_similarity * 100, 1),
    }
