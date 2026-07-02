import React from "react";
import { motion } from "framer-motion";
import type { RankingResult } from "../../types";
import { Avatar, ScoreRing, ProgressBar, getScoreColor, getRiskClass } from "../ui";
import { SCORE_LABELS } from "../../lib/utils";

const RANK_MEDALS = ["🥇","🥈","🥉"];
const REC_ABBREV: Record<string, string> = {
  "Proceed to Technical Round": "→ Tech Round",
  "Schedule HR Screening":      "→ HR Screen",
  "Requires Further Review":    "Further Review",
  "Not Recommended":            "Not Recommended",
};

interface Props {
  result: RankingResult;
  rank: number;
  isComparing: boolean;
  onToggleCompare: () => void;
  onClick: () => void;
}

export const CandidateRow: React.FC<Props> = ({ result, rank, isComparing, onToggleCompare, onClick }) => {
  const { scores, risk_level, matched_skills, missing_skills, recommendation } = result;
  const overall = Math.round(scores.overall_score);
  const scoreCol = getScoreColor(overall);
  const isTop = rank <= 3;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, delay: rank * 0.04 }}
      onClick={onClick}
      style={{
        display: "flex", alignItems: "stretch", gap: 0,
        background: isComparing ? "rgba(124,58,237,0.06)" : "var(--bg-surface)",
        border: `1px solid ${isComparing ? "rgba(124,58,237,0.35)" : isTop ? `${scoreCol}20` : "var(--border)"}`,
        borderRadius: 14, cursor: "pointer", overflow: "hidden",
        transition: "all 0.18s ease",
        boxShadow: isTop ? `0 0 0 1px ${scoreCol}15, inset 0 1px 0 rgba(255,255,255,0.05)` : "inset 0 1px 0 rgba(255,255,255,0.03)",
      }}
      whileHover={{ y: -2, boxShadow: `0 8px 28px rgba(0,0,0,0.3), 0 0 0 1px ${isComparing ? "rgba(124,58,237,0.5)" : "var(--border-strong)"}` }}
    >
      {/* Score accent bar */}
      <div style={{ width: 4, background: scoreCol, flexShrink: 0, opacity: 0.8 }} />

      {/* Rank */}
      <div style={{ width: 52, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, padding: "0 4px" }}>
        {isTop
          ? <span style={{ fontSize: 20 }}>{RANK_MEDALS[rank-1]}</span>
          : <span style={{ fontSize: 13, fontWeight: 800, color: "var(--text-4)", fontVariantNumeric: "tabular-nums" }}>#{rank}</span>
        }
      </div>

      {/* Avatar + Name */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "14px 0 14px 4px", width: 220, flexShrink: 0 }}>
        <Avatar name={result.candidate_name} size={42} />
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 800, fontSize: 14, color: "var(--text-1)", lineHeight: 1.2, marginBottom: 3 }}>{result.candidate_name}</div>
          <div style={{ fontSize: 11, color: "var(--text-3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {result.candidate_title} · {result.candidate_company}
          </div>
          {isTop && <span className="badge badge-green" style={{ marginTop: 4, fontSize: 9 }}>Top Pick</span>}
        </div>
      </div>

      {/* Score mini-bars */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 10, padding: "14px 16px" }}>
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "6px 10px" }}>
          {Object.entries(SCORE_LABELS).slice(0, 6).map(([key, label]) => {
            const val = Math.round((scores as any)[key] ?? 0);
            const col = getScoreColor(val);
            return (
              <div key={key}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ fontSize: 10, color: "var(--text-3)", fontWeight: 600 }}>{label}</span>
                  <span style={{ fontSize: 10, fontWeight: 800, color: col }}>{val}</span>
                </div>
                <ProgressBar value={val} color={col} height={3} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Skills */}
      <div style={{ width: 220, display: "flex", flexDirection: "column", justifyContent: "center", gap: 5, padding: "14px 12px", flexShrink: 0 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {matched_skills.slice(0, 3).map(s => (
            <span key={s} className="chip-match">✓ {s}</span>
          ))}
          {missing_skills.slice(0, 2).map(s => (
            <span key={s} className="chip-miss">✕ {s}</span>
          ))}
          {matched_skills.length + missing_skills.length > 5 && (
            <span style={{ fontSize: 10, color: "var(--text-3)", padding: "3px 0", fontWeight: 600 }}>+{matched_skills.length + missing_skills.length - 5}</span>
          )}
        </div>
        {recommendation && (
          <div style={{ fontSize: 10, color: "var(--text-3)", fontWeight: 600, marginTop: 2 }}>
            {REC_ABBREV[recommendation] ?? recommendation}
          </div>
        )}
      </div>

      {/* Badges + Score */}
      <div style={{ width: 130, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8, padding: "14px 12px", flexShrink: 0 }}>
        <span className={`badge ${getRiskClass(risk_level)}`}>{risk_level} Risk</span>
        <span className="badge badge-slate">{Math.round(result.confidence_score)}% conf</span>
        <ScoreRing value={overall} size={48} stroke={4} />
      </div>

      {/* Compare toggle */}
      <div style={{ width: 42, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <button
          onClick={e => { e.stopPropagation(); onToggleCompare(); }}
          style={{
            width: 28, height: 28, borderRadius: 8, border: `1px solid ${isComparing ? "#7c3aed" : "var(--border)"}`,
            background: isComparing ? "rgba(124,58,237,0.18)" : "transparent",
            color: isComparing ? "#a78bfa" : "var(--text-3)",
            cursor: "pointer", fontSize: 14, display: "flex", alignItems: "center", justifyContent: "center",
            transition: "all 0.15s ease",
          }}
          title={isComparing ? "Remove from compare" : "Add to compare"}
        >⊕</button>
      </div>
    </motion.div>
  );
};
