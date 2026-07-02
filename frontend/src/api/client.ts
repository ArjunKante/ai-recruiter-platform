import axios from "axios";
import type {
  AdminStats,
  Candidate,
  ChatResponse,
  JobDescription,
  RankingResult,
  TokenResponse,
  WeightProfile,
} from "../types";

// The API base URL -- swap this for an env var in production
export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

const client = axios.create({ baseURL: API_BASE });

// Attach JWT to every request when present
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, full_name: string, password: string) =>
    client.post<TokenResponse>("/auth/register", { email, full_name, password }),
  login: (email: string, password: string) =>
    client.post<TokenResponse>("/auth/login", { email, password }),
  me: () => client.get("/auth/me"),
};

// ─── Job Descriptions ────────────────────────────────────────────────────────
export const jobsApi = {
  create: (title: string, raw_text: string) =>
    client.post<JobDescription>("/jobs", { title, raw_text }),
  list: () => client.get<JobDescription[]>("/jobs"),
  get: (id: number) => client.get<JobDescription>(`/jobs/${id}`),
  getWeights: (id: number) => client.get<WeightProfile>(`/jobs/${id}/weights`),
};

// ─── Candidates ───────────────────────────────────────────────────────────────
export const candidatesApi = {
  upload: (jdId: number, files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return client.post<Candidate[]>(`/jobs/${jdId}/candidates`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: (jdId: number) => client.get<Candidate[]>(`/jobs/${jdId}/candidates`),
  get: (id: number) => client.get<Candidate>(`/candidates/${id}`),
};

// ─── Ranking ──────────────────────────────────────────────────────────────────
export const rankingApi = {
  run: (jdId: number) => client.post<RankingResult[]>(`/jobs/${jdId}/rank`),
  get: (jdId: number) => client.get<RankingResult[]>(`/jobs/${jdId}/rank`),
  compare: (jdId: number, candidateIds: number[]) =>
    client.post<RankingResult[]>("/compare", {
      job_description_id: jdId,
      candidate_ids: candidateIds,
    }),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────
export const chatApi = {
  send: (
    jdId: number,
    message: string,
    history: { role: string; content: string }[]
  ) =>
    client.post<ChatResponse>("/chat", {
      job_description_id: jdId,
      message,
      history,
    }),
};

// ─── Export ───────────────────────────────────────────────────────────────────
export const exportApi = {
  download: async (
    jdId: number,
    format: "csv" | "xlsx" | "pdf",
    candidateIds?: number[]
  ) => {
    const res = await client.post(
      "/export",
      { job_description_id: jdId, format, candidate_ids: candidateIds ?? null },
      { responseType: "blob" }
    );
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `shortlist.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  },
};

// ─── Admin ────────────────────────────────────────────────────────────────────
export const adminApi = {
  stats: () => client.get<AdminStats>("/admin/stats"),
  auditLogs: (limit = 50) =>
    client.get(`/admin/audit-logs?limit=${limit}`),
  promptLogs: (limit = 50) =>
    client.get(`/admin/prompt-logs?limit=${limit}`),
};
