// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "admin" | "recruiter";
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ─── Job Description ──────────────────────────────────────────────────────────
export interface JobDescription {
  id: number;
  title: string;
  raw_text: string;
  must_have_skills: string[];
  nice_to_have_skills: string[];
  responsibilities: string[];
  soft_skills: string[];
  min_years_experience: number;
  domain: string | null;
  location: string | null;
  remote_policy: string | null;
  salary_min: number | null;
  salary_max: number | null;
  notice_period_days: number | null;
  role_weight_profile: string;
  created_at: string;
}

// ─── Candidate ────────────────────────────────────────────────────────────────
export interface ExperienceEntry {
  company: string;
  title: string;
  start: string | null;
  end: string | null;
  is_current: boolean;
  months: number;
  bullets: string[];
}

export interface EducationEntry {
  school: string;
  degree: string;
  year: number;
}

export interface CertificationEntry {
  name: string;
  year: number | null;
}

export interface Candidate {
  id: number;
  name: string;
  email: string | null;
  location: string | null;
  github_url: string | null;
  source_filename: string | null;
  experience: ExperienceEntry[];
  education: EducationEntry[];
  skills: string[];
  certifications: CertificationEntry[];
  total_years_experience: number;
  notice_period_days: number | null;
  desired_salary: number | null;
  open_to_remote: string | null;
}

// ─── Ranking ──────────────────────────────────────────────────────────────────
export interface ScoreBreakdown {
  semantic_skill_match: number;
  career_intelligence: number;
  behavior_score: number;
  context_alignment: number;
  resume_quality: number;
  trust_score: number;
  overall_score: number;
}

export type RiskLevel = "Low" | "Medium" | "High";
export type ConfidenceBand = "High" | "Medium" | "Low";

export interface RankingResult {
  id: number;
  candidate_id: number;
  job_description_id: number;
  candidate_name: string;
  candidate_title: string | null;
  candidate_company: string | null;
  rank_position: number | null;
  scores: ScoreBreakdown;
  confidence_score: number;
  confidence_band: ConfidenceBand;
  risk_level: RiskLevel;
  risk_reasons: string[];
  matched_skills: string[];
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  reasoning_text: string | null;
  recommendation: string | null;
  counterfactual_text: string | null;
  weight_profile_used: string;
  weights_applied: Record<string, number>;
  is_duplicate_of_candidate_id: number | null;
}

// ─── Dynamic Weights ──────────────────────────────────────────────────────────
export interface WeightProfile {
  profile_key: string;
  weights: Record<string, number>;
  rationale: string;
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
export interface ChatMessage {
  role: "user" | "ai";
  content: string;
}

export interface ChatResponse {
  reply: string;
  referenced_candidate_ids: number[];
}

// ─── Admin ────────────────────────────────────────────────────────────────────
export interface AdminStats {
  total_users: number;
  total_jobs: number;
  total_candidates: number;
  total_ranking_runs: number;
  total_llm_calls: number;
}

// ─── UI helpers ───────────────────────────────────────────────────────────────
export type TabId = "rankings" | "chat" | "compare";
