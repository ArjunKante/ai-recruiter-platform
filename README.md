# 🧠 TalentAI — AI Recruiter Platform

> **Rank hundreds of candidates like a seasoned recruiter — not a keyword matcher.**
> Powered by Claude (Anthropic), FastAPI, and React/TypeScript.

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Quick Start](#quick-start)
5. [Scoring System](#scoring-system)
6. [API Documentation](#api-documentation)
7. [Features](#features)
8. [Configuration](#configuration)
9. [Sample Data](#sample-data)
10. [Project Structure](#project-structure)

---

## Overview

TalentAI is a production-quality AI recruiting platform that evaluates candidates across **six intelligent scoring dimensions**, generates recruiter-style explanations grounded in actual resume evidence, and produces ranked shortlists that hiring teams can trust.

### What makes this different from ATS/keyword matching
- **Semantic skill matching** — "NodeJS", "Node.js", "Express backend" all match the same skill via alias normalization + embedding similarity
- **Career intelligence** — promotion velocity, tenure patterns, company quality, title inflation detection
- **Trust engine** — detects overlapping employment, suspicious timelines, duplicate entries
- **LLM reasoning grounded in evidence** — the AI is given the already-computed scores and narrates them; it never invents facts
- **Dynamic weights** — automatically adjust by role type (Backend vs PM vs EM)
- **Counterfactual recommendations** — "If candidate had Kubernetes, ranking improves from #8 to #3"

---

## Architecture

```
Frontend (React/TS)
       ↓  REST API
  FastAPI (Python)
       ├── Resume Parser        (PDF/DOCX/TXT → structured fields)
       ├── Embedding Provider   (TF-IDF local OR OpenAI)
       ├── FAISS Vector Index   (semantic document similarity)
       ├── Ranking Engine
       │    ├── Semantic Skill Matcher  (alias normalization + cosine sim)
       │    ├── Career Intelligence     (tenure, promotions, trajectory)
       │    ├── Behavioral Intelligence (GitHub API, completeness, certs)
       │    ├── Context Alignment       (salary, notice, remote)
       │    ├── Resume Quality          (action verbs, metrics, ATS)
       │    └── Trust Engine            (fraud/inconsistency detection)
       ├── Dynamic Weight Engine    (role-based weight profiles)
       ├── LLM Service (Claude)     (recruiter reasoning, chat)
       ├── Export Service           (CSV / Excel / PDF)
       └── Database (SQLite / PostgreSQL)
```

### Ranking formula

```
Overall Score = Σ (component_score × dynamic_weight)

Where dynamic weights for Backend Engineer:
  Semantic Skill Match  : 40%
  Career Intelligence   : 25%
  Behavior Score        : 15%
  Context Alignment     : 10%
  Resume Quality        :  5%
  Trust Score           :  5%
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Framer Motion, Recharts |
| State | Zustand, TanStack Query |
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Vector Store | FAISS + TF-IDF/SVD embeddings (local, zero-config) |
| LLM | Claude Sonnet (Anthropic) — swappable for OpenAI / Ollama |
| Auth | JWT (python-jose + bcrypt) |
| Export | openpyxl (Excel), reportlab (PDF) |
| Resume Parse | pdfplumber (PDF), python-docx (DOCX) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- An Anthropic API key (optional — the platform works fully without one using rule-based reasoning)

### 1. Backend

```bash
cd backend

# Create and activate virtualenv
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY for full AI reasoning
# (Leave blank to use the deterministic rule-based fallback)

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API is now running at **http://localhost:8000**
Interactive docs: **http://localhost:8000/docs**

### 2. Load sample data (optional but recommended for demo)

```bash
# With the backend running, in a second terminal:
cd backend
python seed.py
```

This registers a demo admin user, creates the sample Senior Backend Engineer JD, uploads 6 carefully designed candidate profiles (from Staff Engineer at Stripe to a junior Java developer), and runs a full ranking — printing results to the terminal.

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend is now at **http://localhost:3000**

---

## Scoring System

### Six Component Scores (each 0–100)

| Component | What it measures | Method |
|---|---|---|
| **Semantic Skill Match** | Alias-normalized skill coverage + document similarity | Alias dict + FAISS cosine sim |
| **Career Intelligence** | Tenure, promotions, trajectory, company quality | Deterministic rules on parsed experience |
| **Behavior Score** | GitHub activity, profile completeness, cert freshness | Live GitHub API + heuristics |
| **Context Alignment** | Salary, notice period, remote/location fit | Rule-based scoring |
| **Resume Quality** | Action verbs, quantified impact, ATS friendliness | Text analysis |
| **Trust Score** | Fraud signals, timeline contradictions | Pattern detection — forces High Risk if < 55 |

### Risk Levels

| Level | Triggered when |
|---|---|
| **Low** | No material risk signals |
| **Medium** | 1-2 moderate risk factors (short tenures, salary stretch) |
| **High** | 3+ risk factors OR Trust Score < 55 (auto-override) |

### Confidence Bands

| Band | Meaning |
|---|---|
| **High** (≥75) | Strong evidence quality, clear match/mismatch, high trust |
| **Medium** (45-74) | Partial evidence, some ambiguity |
| **Low** (<45) | Thin resume, unclear signals, low completeness |

---

## API Documentation

Full interactive docs at **http://localhost:8000/docs** (Swagger UI)

### Core Endpoints

```
POST   /api/auth/register          Register user
POST   /api/auth/login             Login, get JWT
GET    /api/auth/me                Current user

POST   /api/jobs                   Create job description (parse + structure)
GET    /api/jobs                   List all JDs
GET    /api/jobs/{id}              Get JD details
GET    /api/jobs/{id}/weights      Get active weight profile for this JD

POST   /api/jobs/{id}/candidates   Upload resumes (batch, multipart)
GET    /api/jobs/{id}/candidates   List candidates for JD

POST   /api/jobs/{id}/rank         Run full ranking pipeline → returns ranked list
GET    /api/jobs/{id}/rank         Get most recent ranking results

POST   /api/compare                Side-by-side compare 2-4 candidates
POST   /api/chat                   Natural language search over ranked pool
POST   /api/export                 Download CSV / Excel / PDF shortlist

GET    /api/admin/audit-logs       Audit trail (admin only)
GET    /api/admin/prompt-logs      LLM prompt/response log (admin only)
GET    /api/admin/stats            Platform statistics (admin only)
```

### Example: Create JD and run ranking

```bash
# 1. Create job description
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"title": "Senior Backend Engineer", "raw_text": "..."}'

# 2. Upload resumes (batch)
curl -X POST http://localhost:8000/api/jobs/1/candidates \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"

# 3. Run ranking
curl -X POST http://localhost:8000/api/jobs/1/rank

# 4. Export shortlist
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{"job_description_id": 1, "format": "xlsx"}' \
  --output shortlist.xlsx
```

---

## Features

| Module | Description | Status |
|---|---|---|
| Resume Upload | Drag-and-drop, batch, PDF/DOCX/TXT | ✅ |
| JD Parser | Extract must-have skills, nice-to-have, domain, salary | ✅ |
| Semantic Matching | Alias dict + FAISS cosine similarity | ✅ |
| Career Intelligence | Tenure, promotions, company quality, job hopping | ✅ |
| Behavioral Intelligence | Live GitHub API, completeness, cert freshness | ✅ |
| Context Alignment | Salary, notice, remote fit | ✅ |
| Resume Quality | Action verbs, metrics, ATS score | ✅ |
| Trust Engine | Fraud detection, force High Risk | ✅ |
| Dynamic Weights | Role-based (Backend/PM/EM/Designer/Sales) | ✅ |
| AI Reasoning | Claude-generated evidence-grounded narrative | ✅ |
| Confidence Score | 0-100 with High/Medium/Low band | ✅ |
| Hiring Risk | Low/Medium/High with reasons | ✅ |
| Skill Gap Analysis | Side-by-side matched vs missing | ✅ |
| Counterfactual | "If candidate had X, rank improves from Y to Z" | ✅ |
| Comparison | Side-by-side radar overlay for 2-4 candidates | ✅ |
| Recruiter Chat | NL search over ranked pool (Claude + fallback) | ✅ |
| Export | CSV, Excel (styled), PDF report | ✅ |
| Duplicate Detection | Cosine similarity deduplication | ✅ |
| Audit Logs | Every action logged, admin dashboard | ✅ |
| Prompt Logs | Every LLM call logged for XAI | ✅ |
| JWT Auth | Register/login, role-based (admin/recruiter) | ✅ |

---

## Configuration

All configuration is via environment variables in `backend/.env`.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./ai_recruiter.db` | SQLite (dev) or PostgreSQL URL |
| `ANTHROPIC_API_KEY` | — | Claude API key for LLM reasoning |
| `LLM_PROVIDER` | `claude` | `claude` / `openai` / `ollama` |
| `TRUST_HIGH_RISK_THRESHOLD` | `55` | Trust score below which → auto High Risk |
| `GITHUB_TOKEN` | — | GitHub PAT for 5000/hr rate limit |
| `JWT_SECRET_KEY` | `dev-secret` | Change in production! |

### Swapping the LLM provider

```bash
# Use OpenAI instead of Claude:
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Use local Ollama (no API key needed):
LLM_PROVIDER=ollama
# Install Ollama and pull a model: ollama pull llama3

# No LLM (rule-based fallback, fully functional):
# Just leave ANTHROPIC_API_KEY and OPENAI_API_KEY blank
```

---

## Sample Data

The `sample_data/` directory contains:
- `senior_backend_engineer_jd.txt` — Full sample JD with structured sections
- `resumes/01_alex_chen_staff_engineer.txt` — Staff Engineer @ Stripe (top candidate)
- `resumes/02_emma_wilson_principal_engineer.txt` — Principal Engineer @ Amazon (strongest)
- `resumes/03_priya_patel_senior_engineer.txt` — Senior @ Uber (strong match)
- `resumes/04_sarah_rodriguez_backend_engineer.txt` — Mid-level @ Shopify (partial match)
- `resumes/05_marcus_johnson_platform_engineer.txt` — Senior @ Netflix (good fit)
- `resumes/06_david_kim_junior_engineer.txt` — Junior @ Morgan Stanley (low match)

These are designed to produce a meaningful spread of scores and demonstrate every feature of the ranking engine.

---

## Project Structure

```
ai-recruiter-platform/
├── backend/
│   ├── app/
│   │   ├── config.py              # Settings + dynamic weight profiles
│   │   ├── database.py            # SQLAlchemy engine + session
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── schemas.py             # All Pydantic request/response models
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── routes/api.py          # All REST route definitions
│   │   ├── controllers/           # Request handling + validation
│   │   ├── services/              # DB-aware orchestration
│   │   ├── ranking_engine/        # Six scoring modules (pure Python)
│   │   ├── vector_store/          # FAISS index + embedding providers
│   │   ├── resume_parser/         # PDF/DOCX/TXT extraction + structuring
│   │   ├── llm_service/           # LLM client + reasoning + chat
│   │   ├── export_service/        # CSV / Excel / PDF generation
│   │   ├── prompts/               # Prompt templates
│   │   └── utils/                 # Security, skill aliases, helpers
│   ├── requirements.txt
│   ├── .env.example
│   └── seed.py                    # Demo data loader
│
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          # Axios API client, all typed endpoints
│   │   ├── lib/store.ts           # Zustand global state
│   │   ├── lib/utils.ts           # Helpers, color functions
│   │   ├── types/index.ts         # All TypeScript types
│   │   ├── components/
│   │   │   ├── ui/                # ScoreRing, Badge, Avatar, Card, etc.
│   │   │   ├── candidate/         # CandidateRow, CandidateDetail
│   │   │   └── dashboard/         # Charts, CompareView, ChatView
│   │   └── pages/
│   │       ├── Landing.tsx        # JD + resume upload setup
│   │       └── Dashboard.tsx      # Main ranked results view
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── sample_data/
│   ├── senior_backend_engineer_jd.txt
│   └── resumes/                   # 6 sample candidate profiles
│
└── docs/
    ├── api_documentation.md
    ├── architecture_diagram.md
    └── scoring_diagram.md
```

---

## Running in Production

```bash
# Backend with Gunicorn + Uvicorn workers
pip install gunicorn
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000

# Set production env vars:
DATABASE_URL=postgresql+psycopg2://user:pass@localhost/ai_recruiter
JWT_SECRET_KEY=<256-bit-random-secret>
ENV=production
DEBUG=false
```

For PostgreSQL, replace the SQLite connection string and run:
```bash
alembic init alembic  # For real migrations in production
```

---

## Contributing

The codebase follows these principles:
- **SOLID**: each module has one responsibility; ranking engines never touch the DB
- **No hardcoded weights**: all scoring parameters live in `config.py` as data
- **Frontend renders, backend decides**: scores are never computed in the frontend
- **Fail soft**: no LLM API key = graceful rule-based fallback, not a crash
- **Explainable by design**: every score component is logged and returnable via API

---

*Built for demonstration at hackathons and production deployment. MIT License.*
