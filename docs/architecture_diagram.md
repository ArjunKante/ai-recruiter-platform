# Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TALENTAI PLATFORM                           │
├─────────────────────────────────────────────────────────────────┤
│  FRONTEND  (React 18 + TypeScript + TailwindCSS + Vite)         │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Landing   │  │ Dashboard  │  │ Compare  │  │   Chat    │  │
│  │  (JD +     │  │ (Ranked    │  │  View    │  │  Search   │  │
│  │  Upload)   │  │  Results)  │  │          │  │           │  │
│  └────────────┘  └────────────┘  └──────────┘  └───────────┘  │
│        │               │                │              │         │
│        └───────────────┴────────────────┴──────────────┘        │
│                           Axios HTTP Client                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST/JSON
┌───────────────────────────────▼─────────────────────────────────┐
│  API GATEWAY  (FastAPI + Uvicorn)                               │
│  /api/jobs  /api/candidates  /api/rank  /api/chat  /api/export  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Controllers  (request validation, error mapping)         │   │
│  └──────────────────┬───────────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│  SERVICES LAYER  (DB-aware orchestration)                       │
│                                                                  │
│  auth_service  │  jd_service  │  candidate_service              │
│                │              │                                  │
│                └──────┬───────┘                                  │
│                       │                                          │
│              ranking_service  ←──────── [coordinates all below] │
└───────┬───────────────┬──────────────────────┬──────────────────┘
        │               │                      │
┌───────▼───────┐ ┌─────▼──────────┐  ┌───────▼──────────────┐
│ RESUME PARSER │ │ VECTOR STORE   │  │  RANKING ENGINE       │
│               │ │                │  │                       │
│ extractor.py  │ │ embedding      │  │  semantic_matcher     │
│ PDF/DOCX/TXT  │ │ _provider.py   │  │  career_intelligence  │
│               │ │ (TF-IDF/SVD    │  │  behavioral_intel.    │
│ parser.py     │ │  or OpenAI)    │  │  context_alignment    │
│ Structured    │ │                │  │  resume_quality       │
│ fields        │ │ faiss_index.py │  │  trust_engine         │
│               │ │ ANN similarity │  │  dynamic_weights      │
│               │ │ search         │  │  ranking_engine       │
└───────────────┘ └────────────────┘  └───────────────────────┘
                                                │
                                    ┌───────────▼──────────────┐
                                    │   LLM SERVICE             │
                                    │                           │
                                    │  claude_client.py         │
                                    │  (Anthropic SDK)          │
                                    │                           │
                                    │  reasoning_service.py     │
                                    │  Grounded recruiter       │
                                    │  narrative generation     │
                                    │                           │
                                    │  chat_service.py          │
                                    │  NL search over ranked    │
                                    │  candidate pool           │
                                    └───────────────────────────┘
                                                │
                          ┌─────────────────────▼──────────────┐
                          │  DATABASE (SQLite / PostgreSQL)      │
                          │  users, job_descriptions,           │
                          │  candidates, ranking_results,       │
                          │  audit_logs, prompt_logs            │
                          └────────────────────────────────────┘
```

---

## Data Flow: Single Ranking Run

```
User uploads JD + resumes
         │
         ▼
1. JD PARSING
   raw text → must_have_skills[], nice_to_have[], min_years, salary, remote_policy
   role keyword → weight profile key
         │
         ▼
2. RESUME PARSING  (per file)
   PDF/DOCX/TXT bytes → raw text
   raw text → name, email, experience[], skills[], education[], certs[]
   alias normalization → canonical skill list
         │
         ▼
3. VECTOR INDEX BUILD
   All resume texts → TF-IDF/SVD embeddings (or OpenAI)
   FAISS IndexFlatIP built over candidate pool
         │
         ▼
4. SEMANTIC QUERY
   JD text → embedded → FAISS query → per-candidate cosine similarity [0,1]
         │
         ▼
5. SIX-COMPONENT SCORING  (per candidate, pure Python, no LLM)
   ├── Semantic Skill Match   (alias coverage × 0.75) + (doc_sim × 0.25)
   ├── Career Intelligence    (tenure + promotion + company quality + trajectory)
   ├── Behavioral Intelligence (GitHub API + completeness + cert freshness)
   ├── Context Alignment      (salary + notice + remote + location)
   ├── Resume Quality         (action verbs + metrics + ATS + length)
   └── Trust Score            (fraud/overlap detection → force_high_risk flag)
         │
         ▼
6. DYNAMIC WEIGHT RESOLUTION
   JD title → role keyword match → weight profile
   Overall = Σ(component × weight/100)
         │
         ▼
7. CONFIDENCE + RISK DERIVATION
   Confidence = f(completeness, decisiveness, trust, evidence_quality)
   Risk = rule-based threshold on risk_points  OR  trust_engine override
         │
         ▼
8. LLM REASONING (Claude Sonnet)
   Grounding prompt: computed scores + evidence → sent to Claude
   Output: reasoning paragraph, strengths[], weaknesses[], recommendation, counterfactual
   Fallback: deterministic string templates if no API key configured
         │
         ▼
9. PERSISTENCE
   RankingResult row written per (candidate, JD) pair
   PromptLog row written per LLM call
   AuditLog row written for the ranking run
         │
         ▼
10. RANK POSITIONS ASSIGNED
    Sort by overall_score DESC → assign rank_position 1..N
    Duplicate detection via pairwise cosine similarity matrix
         │
         ▼
11. API RESPONSE
    [{candidate_name, rank_position, scores{}, risk, confidence,
      matched_skills, missing_skills, reasoning, recommendation,
      counterfactual, weights_applied}, ...]
         │
         ▼
FRONTEND RENDERS  (never recomputes any score)
```

---

## Scoring Diagram

```
                    CANDIDATE OVERALL SCORE
                    ═══════════════════════

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌──────────────────┐         Wt (Backend Engineer)       │
│   │ Semantic Skill   ├────────►  40%  ───────┐             │
│   │ Match  0-100     │                       │             │
│   └──────────────────┘                       │             │
│                                              │             │
│   ┌──────────────────┐                       │             │
│   │ Career           ├────────►  25%  ───────┤             │
│   │ Intelligence 0-100│                      │             │
│   └──────────────────┘                       ▼             │
│                                    ┌──────────────────┐    │
│   ┌──────────────────┐             │  WEIGHTED SUM    │    │
│   │ Behavior         ├───────►  15%│  0-100           │    │
│   │ Score    0-100   │             │                  │    │
│   └──────────────────┘             │  ÷ Confidence    │    │
│                                    │  modifier        │    │
│   ┌──────────────────┐             │                  │    │
│   │ Context          ├───────►  10%│  = OVERALL SCORE │    │
│   │ Alignment 0-100  │             └────────┬─────────┘    │
│   └──────────────────┘                      │             │
│                                             │             │
│   ┌──────────────────┐                      ▼             │
│   │ Resume Quality   ├────────►   5%   RISK LEVEL         │
│   │          0-100   │            Low / Medium / High     │
│   └──────────────────┘                      │             │
│                                             │             │
│   ┌──────────────────┐                      ▼             │
│   │ Trust Score      ├────────►   5%   CONFIDENCE BAND    │
│   │          0-100   │◄──── if < 55   High / Med / Low   │
│   └──────────────────┘   force High Risk                  │
│                                                            │
└─────────────────────────────────────────────────────────────┘

NOTE: Dynamic weights change by role. Example profiles:
  Backend Eng : Skills 40% Career 25% Behavior 15% Context 10% Quality 5% Trust 5%
  Product Mgr : Career 30% Skills 20% Behavior 20% Context 10% Quality 10% Trust 10%
  Eng Manager : Career 32% Behavior 23% Skills 20% Trust 10% Context 10% Quality 5%
```
