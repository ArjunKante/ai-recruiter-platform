from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def parse_date_token(token: str, fallback_present_as: Optional[datetime] = None) -> Optional[datetime]:
    """Parse a loose date token like 'Jan 2021', '2021', 'Present', 'Current'
    into a datetime (day fixed to 1st of month). Returns None if unparseable."""
    token = token.strip().lower()
    if token in ("present", "current", "now", "ongoing", "till date"):
        return fallback_present_as or datetime.utcnow()

    m = re.match(r"([a-z]{3,9})\.?\s+(\d{4})", token)
    if m:
        mon_str, year = m.group(1)[:3], int(m.group(2))
        month = MONTHS.get(mon_str, 1)
        try:
            return datetime(year, month, 1)
        except ValueError:
            return None

    m = re.match(r"^(\d{4})$", token)
    if m:
        return datetime(int(m.group(1)), 1, 1)

    return None


def extract_date_ranges(text: str) -> List[Tuple[Optional[datetime], Optional[datetime]]]:
    """Find 'Mon YYYY – Mon YYYY' / 'YYYY - Present' style ranges anywhere in
    a block of resume text. Used by career_intelligence to reconstruct a
    timeline without depending on the resume having perfectly delimited
    experience sections."""
    pattern = re.compile(
        r"([A-Za-z]{3,9}\.?\s+\d{4}|\d{4})\s*[-–—to]+\s*([A-Za-z]{3,9}\.?\s+\d{4}|\d{4}|[Pp]resent|[Cc]urrent)"
    )
    ranges = []
    now = datetime.utcnow()
    for match in pattern.finditer(text):
        start = parse_date_token(match.group(1))
        end = parse_date_token(match.group(2), fallback_present_as=now)
        if start:
            ranges.append((start, end))
    return ranges


def months_between(start: datetime, end: datetime) -> int:
    if not start or not end or end < start:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month)


def clean_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()


def extract_email(text: str) -> Optional[str]:
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text: str) -> Optional[str]:
    m = re.search(r"(\+?\d{1,3}[\s.-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", text)
    return m.group(0).strip() if m else None


def extract_github(text: str) -> Optional[str]:
    m = re.search(r"github\.com/([A-Za-z0-9\-_]+)", text)
    return f"https://github.com/{m.group(1)}" if m else None


def extract_notice_period_days(text: str) -> Optional[int]:
    t = text.lower()
    m = re.search(r"(\d+)\s*[-]?\s*(day|week|month)s?\s*notice", t)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    return n * {"day": 1, "week": 7, "month": 30}[unit]


def extract_desired_salary(text: str) -> Optional[int]:
    m = re.search(r"\$\s?(\d{2,3})\s?[,.]?(\d{3})?\s?[kK]\b", text)
    if m:
        base = int(m.group(1))
        return base * 1000
    m = re.search(r"\$\s?(\d{5,7})\b", text)
    if m:
        return int(m.group(1))
    return None
