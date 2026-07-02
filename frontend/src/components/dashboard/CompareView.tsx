import React from "react";
import { motion } from "framer-motion";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from "recharts";
import { ArrowLeft, Trophy } from "lucide-react";
import type { RankingResult } from "../../types";
import { Avatar, ScoreRing, ProgressBar, SectionLabel, getScoreColor, getRiskClass, getRecColor } from "../ui";
import { SCORE_LABELS, RADAR_COLORS } from "../../lib/utils";

const CHART_TOOLTIP_STYLE = {
  background: "#0d0d20", border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 10, color: "#f1f5f9", fontSize: 12,
};

export const CompareView: React.FC<{ results: RankingResult[]; onBack: () => void }> = ({ results, onBack }) => {
  const radarData = Object.entries(SCORE_LABELS).map(([key, label]) => {
    const point: Record<string, any> = { subject: label };
    results.forEach(r => { point[r.candidate_name.split(" ")[0]] = Math.round((r.scores as any)[key] ?? 0); });
    return point;
  });

  const winner = results.reduce((a, b) => a.scores.overall_score >= b.scores.overall_score ? a : b, results[0]);

  return (
    <div style={{ padding: "28px 28px", maxWidth: 1160, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 28 }}>
        <button onClick={onBack} className="btn-ghost" style={{ gap: 6, height: 36 }}>
          <ArrowLeft size={14} /> Back
        </button>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 900, letterSpacing: "-0.5px" }}>Candidate Comparison</h2>
          <p style={{ color: "var(--text-3)", fontSize: 13, marginTop: 2 }}>
            Side-by-side analysis of {results.length} candidates
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, marginLeft: 16 }}>
          {results.map((r, i) => (
            <div key={r.id} style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 10px", borderRadius: 99, background: `${RADAR_COLORS[i]}18`, border: `1px solid ${RADAR_COLORS[i]}35` }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: RADAR_COLORS[i] }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: RADAR_COLORS[i] }}>{r.candidate_name.split(" ")[0]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Winner banner */}
      {winner && (
        <motion.div
          initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 20px", marginBottom: 24, background: "rgba(16,185,129,0.07)", border: "1px solid rgba(16,185,129,0.25)", borderRadius: 14 }}
        >
          <Trophy size={18} style={{ color: "#10b981", flexShrink: 0 }} />
          <div>
            <span style={{ fontSize: 13, fontWeight: 800, color: "#10b981" }}>Top pick: {winner.candidate_name}</span>
            <span style={{ fontSize: 12, color: "var(--text-3)", marginLeft: 10 }}>with {Math.round(winner.scores.overall_score)}/100 overall score · {winner.recommendation}</span>
          </div>
          <ScoreRing value={Math.round(winner.scores.overall_score)} size={40} stroke={4} />
        </motion.div>
      )}

      {/* Radar overlay */}
      <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 16, padding: "24px 20px", marginBottom: 24 }}>
        <SectionLabel style={{ marginBottom: 16 }}>Score Radar Overlay</SectionLabel>
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="rgba(255,255,255,0.06)" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-3)", fontSize: 12 }} />
            <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />
            {results.map((r, i) => (
              <Radar key={r.id} dataKey={r.candidate_name.split(" ")[0]}
                stroke={RADAR_COLORS[i]} fill={RADAR_COLORS[i]} fillOpacity={0.1} strokeWidth={2.5}
                dot={{ r: 3, fill: RADAR_COLORS[i] }} />
            ))}
            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Cards */}
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${results.length}, 1fr)`, gap: 18 }}>
        {results.map((r, ci) => {
          const isWinner = r.candidate_id === winner?.candidate_id;
          const col = RADAR_COLORS[ci];
          return (
            <motion.div
              key={r.id}
              initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: ci * 0.1 }}
              style={{
                background: isWinner ? "rgba(16,185,129,0.04)" : "var(--bg-surface)",
                border: `1px solid ${isWinner ? "rgba(16,185,129,0.3)" : `${col}25`}`,
                borderRadius: 16, overflow: "hidden",
                boxShadow: isWinner ? "0 0 30px rgba(16,185,129,0.08)" : "none",
              }}
            >
              {/* Color band */}
              <div style={{ height: 3, background: col }} />

              <div style={{ padding: "20px" }}>
                {/* Candidate info */}
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <Avatar name={r.candidate_name} size={44} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 800, fontSize: 14, lineHeight: 1.2 }}>{r.candidate_name}</div>
                    <div style={{ fontSize: 11, color: "var(--text-3)", marginTop: 2 }}>{r.candidate_company}</div>
                    {isWinner && <span className="badge badge-green" style={{ marginTop: 5, fontSize: 9 }}>🏆 Top Pick</span>}
                  </div>
                </div>

                {/* Overall score */}
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: 12 }}>
                  <ScoreRing value={Math.round(r.scores.overall_score)} size={54} stroke={5} />
                  <div>
                    <div style={{ fontSize: 11, color: "var(--text-3)", marginBottom: 5 }}>Overall Score</div>
                    <div style={{ display: "flex", gap: 5 }}>
                      <span className={`badge ${getRiskClass(r.risk_level)}`}>{r.risk_level}</span>
                      <span className="badge badge-slate">{Math.round(r.confidence_score)}%</span>
                    </div>
                  </div>
                </div>

                {/* Score bars */}
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
                  {Object.entries(SCORE_LABELS).map(([key, label]) => {
                    const val = Math.round((r.scores as any)[key] ?? 0);
                    return (
                      <div key={key}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                          <span style={{ fontSize: 11, color: "var(--text-2)", fontWeight: 600 }}>{label}</span>
                          <span style={{ fontSize: 11, fontWeight: 800, color: col }}>{val}</span>
                        </div>
                        <ProgressBar value={val} color={col} height={4} />
                      </div>
                    );
                  })}
                </div>

                {/* Recommendation */}
                <div style={{ padding: "10px 12px", background: `${getRecColor(r.recommendation)}10`, border: `1px solid ${getRecColor(r.recommendation)}25`, borderRadius: 10, marginBottom: 14 }}>
                  <div style={{ fontSize: 11, color: "var(--text-3)", fontWeight: 600, marginBottom: 3 }}>Recommendation</div>
                  <div style={{ fontSize: 12, fontWeight: 800, color: getRecColor(r.recommendation) }}>{r.recommendation}</div>
                </div>

                {/* Skills */}
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, color: "var(--text-3)", textTransform: "uppercase", marginBottom: 7 }}>Matched</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                    {r.matched_skills.slice(0, 5).map(s => <span key={s} className="chip-match" style={{ fontSize: 10 }}>✓ {s}</span>)}
                  </div>
                </div>

                {r.missing_skills.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, color: "var(--text-3)", textTransform: "uppercase", marginBottom: 7 }}>Missing</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                      {r.missing_skills.slice(0, 4).map(s => <span key={s} className="chip-miss" style={{ fontSize: 10 }}>✕ {s}</span>)}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
