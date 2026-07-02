"""
Skill alias taxonomy.

Pure keyword matching fails on real resumes: "NodeJS", "Node", "Node.js",
"Express backend" and "Backend APIs (Node)" are all the same underlying
skill written five different ways. This module normalizes any skill mention
to a canonical token *before* it reaches the embedding/cosine-similarity
layer in vector_store, so semantic matching starts from a much cleaner
signal instead of relying on the embedding alone to bridge surface-form gaps.

This is intentionally data, not logic -- extend CANONICAL_SKILLS to widen
coverage without touching any matching code.
"""
from __future__ import annotations

import re
from typing import Dict, List, Set

# canonical_name -> list of surface forms / aliases that should normalize to it
CANONICAL_SKILLS: Dict[str, List[str]] = {
    "python": ["python", "python3", "py"],
    "node.js": ["node.js", "nodejs", "node js", "node", "express.js", "express backend", "express"],
    "javascript": ["javascript", "js", "es6", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java", "java8", "java 8", "java11", "java 11", "j2ee"],
    "go": ["golang", "go lang", " go "],
    "c#": ["c#", "csharp", ".net", "dotnet", "asp.net"],
    "php": ["php"],
    "ruby": ["ruby", "ruby on rails", "rails"],
    "react": ["react", "react.js", "reactjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular", "angularjs"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql", "maria db", "mariadb"],
    "mongodb": ["mongodb", "mongo", "nosql document store"],
    "oracle": ["oracle", "pl/sql", "plsql"],
    "sql server": ["sql server", "mssql", "t-sql"],
    "redis": ["redis", "in-memory cache", "caching layer"],
    "cassandra": ["cassandra"],
    "dynamodb": ["dynamodb", "dynamo db"],
    "docker": ["docker", "containerization", "containerized"],
    "kubernetes": ["kubernetes", "k8s", "container orchestration"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "rds", "lambda", "ecs", "eks"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "kafka": ["kafka", "event streaming", "message queue", "pub/sub", "pubsub"],
    "graphql": ["graphql", "apollo"],
    "grpc": ["grpc", "protocol buffers", "protobuf"],
    "rest api": ["rest api", "restful", "rest apis", "backend apis", "api development"],
    "microservices": ["microservices", "microservice architecture", "service oriented architecture", "soa"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous deployment", "jenkins", "github actions", "gitlab ci"],
    "terraform": ["terraform", "infrastructure as code", "iac"],
    "spring boot": ["spring boot", "spring framework", "springboot"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "machine learning": ["machine learning", "ml", "deep learning", "neural networks"],
    "leadership": ["leadership", "team lead", "led a team", "managed engineers", "mentored", "people management"],
    "system design": ["system design", "distributed systems", "scalable systems", "scalable architecture"],
    "agile": ["agile", "scrum", "kanban", "sprint planning"],
}

# Pre-build a reverse lookup: alias substring -> canonical name, sorted by
# alias length descending so longer/more specific aliases match first
# (e.g. "node.js" before the bare "node" inside "node.js").
_ALIAS_TO_CANONICAL: List[tuple] = []
for canonical, aliases in CANONICAL_SKILLS.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL.append((alias.strip().lower(), canonical))
_ALIAS_TO_CANONICAL.sort(key=lambda pair: len(pair[0]), reverse=True)


def normalize_skill_text(raw: str) -> str:
    """Lowercase + strip punctuation noise for matching purposes."""
    return re.sub(r"[^a-z0-9.#+/\s]", " ", raw.lower()).strip()


def extract_canonical_skills(text: str) -> Set[str]:
    """Scan free text (resume or JD) and return the set of canonical skills
    it mentions, using alias matching rather than exact keyword equality."""
    norm = f" {normalize_skill_text(text)} "
    found: Set[str] = set()
    for alias, canonical in _ALIAS_TO_CANONICAL:
        needle = f" {alias} " if " " in alias or alias.isalpha() else alias
        if needle in norm or alias in norm:
            found.add(canonical)
    return found


def canonicalize_skill_list(skills: List[str]) -> List[str]:
    """Map a list of free-text skill strings to canonical names, preserving
    any skill that doesn't match a known alias (so we never silently drop
    a real but unrecognized skill -- it's just not normalized)."""
    result: Set[str] = set()
    for s in skills:
        matched = extract_canonical_skills(s)
        if matched:
            result.update(matched)
        else:
            cleaned = s.strip().lower()
            if cleaned:
                result.add(cleaned)
    return sorted(result)
