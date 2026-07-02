import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const SCORE_LABELS: Record<string, string> = {
  semantic_skill_match: "Skill Match",
  career_intelligence:  "Career",
  behavior_score:       "Behavior",
  context_alignment:    "Context",
  resume_quality:       "Resume Quality",
  trust_score:          "Trust",
};

export const SCORE_KEYS = Object.keys(SCORE_LABELS);

export const RADAR_COLORS = ["#7c3aed", "#06b6d4", "#f59e0b", "#10b981"];

export const formatSalary = (n: number | null): string => {
  if (!n) return "—";
  return `$${(n / 1000).toFixed(0)}K`;
};
