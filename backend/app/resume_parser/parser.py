"""
Turns raw resume / job-description text into the structured fields the rest
of the platform operates on. This is intentionally rule-based (regex +
heuristics) rather than another LLM call: it needs to run on hundreds of
resumes cheaply and deterministically, and resume formatting is regular
enough that heuristics get the structured backbone (companies, titles,
date ranges, sections) right the large majority of the time. The LLM is
reserved for the part that genuinely needs judgement -- recruiter reasoning
-- in llm_service.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.utils.helpers import (
    extract_date_ranges,
    extract_desired_salary,
    extract_email,
    extract_github,
    extract_notice_period_days,
    extract_phone,
    months_between,
    setup_logger,
)
from app.utils.skill_aliases import canonicalize_skill_list, extract_canonical_skills

logger = setup_logger("resume_parser.parser")

SECTION_HEADERS = {
    "experience": re.compile(r"^(work\s+)?experience\b|^employment\s+history\b", re.I),
    "education": re.compile(r"^education\b", re.I),
    "skills": re.compile(r"^(technical\s+)?skills\b", re.I),
    "certifications": re.compile(r"^certifications?\b", re.I),
}

HEADER_LINE = re.compile(
    r"^(?P<a>[^|–—\-\n]{2,50})\s*[–—-]\s*(?P<b>[^|–—\-\n]{2,60})\s*\|\s*"
    r"(?P<dates>[A-Za-z]{0,9}\.?\s*\d{4}\s*[-–—]\s*(?:[A-Za-z]{0,9}\.?\s*\d{4}|[Pp]resent|[Cc]urrent))"
)


def _split_sections(text: str) -> Dict[str, str]:
    """Split resume text into named sections based on header lines. Any text
    before the first recognized header is treated as 'header' (name/contact)."""
    lines = text.split("\n")
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"
    for line in lines:
        matched = None
        for name, pattern in SECTION_HEADERS.items():
            if pattern.match(line.strip()):
                matched = name
                break
        if matched:
            current = matched
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def _parse_experience_entries(text: str) -> List[Dict[str, Any]]:
    """Walk the resume looking for 'Company — Title | Date – Date' style
    header lines, and attach subsequent bullet lines to that role until the
    next header. Falls back gracefully if the resume uses a slightly
    different delimiter convention -- any line containing a parsable date
    range is still treated as a role boundary."""
    lines = text.split("\n")
    entries: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        m = HEADER_LINE.match(line)
        date_ranges = extract_date_ranges(line) if not m else None

        if m or date_ranges:
            if current:
                entries.append(current)
            if m:
                company, title, date_str = m.group("a").strip(), m.group("b").strip(), m.group("dates")
            else:
                # fallback: line has a date range but not the strict pattern;
                # best-effort split on common separators for company/title.
                pre_date = line.split(date_ranges[0][0].strftime("%Y"))[0]
                parts = re.split(r"[–—|]", pre_date)
                company = parts[0].strip(" -\u2013\u2014") if parts else "Unknown"
                title = parts[1].strip(" -\u2013\u2014") if len(parts) > 1 else "Unknown"
                date_str = ""

            ranges = extract_date_ranges(date_str or line)
            start, end = (ranges[0] if ranges else (None, None))
            current = {
                "company": company,
                "title": title,
                "start": start.strftime("%Y-%m") if start else None,
                "end": end.strftime("%Y-%m") if end else None,
                "is_current": bool(end and (datetime.utcnow() - end).days < 45),
                "months": months_between(start, end) if start and end else 0,
                "bullets": [],
            }
            continue

        if current and (line.startswith(("•", "-", "*", "–")) or len(line) > 20):
            current["bullets"].append(line.lstrip("•-*– ").strip())

    if current:
        entries.append(current)
    return entries


def _parse_education(text: str) -> List[Dict[str, Any]]:
    entries = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        year_m = re.search(r"(19|20)\d{2}", line)
        if not year_m:
            continue
        parts = [p.strip() for p in re.split(r",", line) if p.strip()]
        entries.append({
            "school": parts[0] if parts else line,
            "degree": parts[1] if len(parts) > 1 else "",
            "year": int(year_m.group(0)),
        })
    return entries


def _parse_certifications(text: str) -> List[Dict[str, Any]]:
    certs = []
    for line in text.split("\n"):
        line = line.strip(" •-*")
        if not line:
            continue
        year_m = re.search(r"(19|20)\d{2}", line)
        certs.append({"name": line, "year": int(year_m.group(0)) if year_m else None})
    return certs


def parse_resume(raw_text: str, filename: str = "") -> Dict[str, Any]:
    """Main entry point: raw resume text -> structured Candidate fields."""
    sections = _split_sections(raw_text)
    header_block = sections.get("header", "")

    # Name: first non-empty line of the header block that isn't an email/phone
    name = "Unknown Candidate"
    for line in header_block.split("\n"):
        line = line.strip()
        if line and "@" not in line and not re.match(r"^\+?\d", line):
            name = re.split(r"[|,]", line)[0].strip()
            break

    experience = _parse_experience_entries(sections.get("experience", "") or raw_text)
    education = _parse_education(sections.get("education", ""))
    certifications = _parse_certifications(sections.get("certifications", ""))

    explicit_skills_text = sections.get("skills", "")
    explicit_skills = [s.strip() for s in re.split(r"[,\n]", explicit_skills_text) if s.strip()]
    inferred_skills = extract_canonical_skills(raw_text)
    all_skills = canonicalize_skill_list(explicit_skills) if explicit_skills else []
    all_skills = sorted(set(all_skills) | inferred_skills)

    total_months = sum(e.get("months", 0) for e in experience)
    # de-duplicate grossly overlapping concurrent roles (e.g. founder + advisor
    # at the same time) by capping total to the span between earliest start
    # and latest end if that span is smaller than the naive sum.
    starts = [datetime.strptime(e["start"], "%Y-%m") for e in experience if e.get("start")]
    ends = [datetime.strptime(e["end"], "%Y-%m") for e in experience if e.get("end")]
    if starts and ends:
        span_months = months_between(min(starts), max(ends))
        total_months = min(total_months, span_months) if span_months > 0 else total_months

    location_m = re.search(r"([A-Z][a-zA-Z.]+(?:\s[A-Z][a-zA-Z.]+)?,\s?[A-Z]{2}(?:,?\s?[A-Za-z]+)?)", header_block)

    return {
        "name": name,
        "email": extract_email(raw_text),
        "phone": extract_phone(raw_text),
        "location": location_m.group(1) if location_m else None,
        "github_url": extract_github(raw_text),
        "raw_resume_text": raw_text,
        "source_filename": filename,
        "experience": experience,
        "education": education,
        "skills": all_skills,
        "certifications": certifications,
        "total_years_experience": round(total_months / 12) if total_months else 0,
        "notice_period_days": extract_notice_period_days(raw_text),
        "desired_salary": extract_desired_salary(raw_text),
        "open_to_remote": _infer_remote_pref(raw_text),
    }


def _infer_remote_pref(text: str) -> Optional[str]:
    t = text.lower()
    if "remote only" in t or "remote preferred" in t or re.search(r"\bremote\b", t):
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    if "onsite" in t or "on-site" in t:
        return "onsite"
    return None


# ---------------------------------------------------------------------------
# Job description parsing
# ---------------------------------------------------------------------------
JD_MUST_HAVE_HEADER = re.compile(r"required|must.?have", re.I)
JD_NICE_HAVE_HEADER = re.compile(r"nice.?to.?have|preferred|bonus", re.I)
JD_RESPONSIBILITY_HEADER = re.compile(r"responsibilit", re.I)

DOMAIN_KEYWORDS = {
    "fintech": ["fintech", "payments", "banking", "trading"],
    "healthcare": ["healthcare", "health tech", "clinical", "medical"],
    "e-commerce": ["e-commerce", "ecommerce", "retail", "marketplace"],
    "saas": ["saas", "b2b software", "enterprise software"],
    "gaming": ["gaming", "game studio"],
    "ai/ml": ["ai", "machine learning", "artificial intelligence"],
}


def parse_job_description(raw_text: str, title: str) -> Dict[str, Any]:
    lines = raw_text.split("\n")
    must_have, nice_have, responsibilities = [], [], []
    mode = None

    for line in lines:
        stripped = line.strip(" •-*\t")
        if not stripped:
            continue
        if JD_MUST_HAVE_HEADER.search(stripped) and len(stripped) < 60:
            mode = "must"
            continue
        if JD_NICE_HAVE_HEADER.search(stripped) and len(stripped) < 60:
            mode = "nice"
            continue
        if JD_RESPONSIBILITY_HEADER.search(stripped) and len(stripped) < 60:
            mode = "resp"
            continue
        if re.match(r"^[A-Z][A-Z \-/]{3,30}:?$", stripped):  # any other ALL-CAPS header resets mode
            mode = None
            continue

        if mode == "must":
            must_have.append(stripped)
        elif mode == "nice":
            nice_have.append(stripped)
        elif mode == "resp":
            responsibilities.append(stripped)

    must_have_skills = canonicalize_skill_list(must_have) if must_have else sorted(extract_canonical_skills(raw_text))
    nice_to_have_skills = canonicalize_skill_list(nice_have)

    years_m = re.search(r"(\d+)\+?\s*years?", raw_text, re.I)
    min_years = int(years_m.group(1)) if years_m else 0

    domain = None
    low = raw_text.lower()
    for d, kws in DOMAIN_KEYWORDS.items():
        if any(kw in low for kw in kws):
            domain = d
            break

    remote_policy = None
    if re.search(r"\bremote\b", low):
        remote_policy = "remote"
    elif "hybrid" in low:
        remote_policy = "hybrid"
    elif "onsite" in low or "on-site" in low:
        remote_policy = "onsite"

    location_m = re.search(r"([A-Z][a-zA-Z]+,\s?[A-Z]{2})\b", raw_text)

    salary_m = re.search(r"\$\s?(\d{2,3})\s?[kK]\s?[-–to]+\s?\$?\s?(\d{2,3})\s?[kK]", raw_text)
    salary_min = int(salary_m.group(1)) * 1000 if salary_m else None
    salary_max = int(salary_m.group(2)) * 1000 if salary_m else None

    soft_skill_pool = ["communication", "leadership", "mentoring", "collaboration", "ownership", "stakeholder management"]
    soft_skills = [s for s in soft_skill_pool if s in low]

    return {
        "title": title,
        "raw_text": raw_text,
        "must_have_skills": must_have_skills,
        "nice_to_have_skills": nice_to_have_skills,
        "responsibilities": responsibilities[:10],
        "soft_skills": soft_skills,
        "min_years_experience": min_years,
        "domain": domain,
        "location": location_m.group(1) if location_m else None,
        "remote_policy": remote_policy,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "notice_period_days": extract_notice_period_days(raw_text),
    }
