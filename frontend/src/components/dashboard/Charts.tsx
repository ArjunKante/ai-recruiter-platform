import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, AreaChart, Area, CartesianGrid,
} from "recharts";
import type { RankingResult, WeightProfile } from "../../types";
import { Avatar, ScoreRing, ProgressBar, SectionLabel, getScoreColor } from "../ui";
import { SCORE_LABELS } from "../../lib/utils";

const CHART_TOOLTIP_STYLE = {
  background: "#0d0d20", border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 10, color: "#f1f5f9", fontSize: 12,
  boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
};

/* ─── Top candidate spotlight ──────────────────────────────────────────────── */
export const TopCandidateCard: React.FC<{ result: RankingResult; onView: () => void }> = ({ result, onView }) => (
  <div style={{
    background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.2)",
    borderRadius: 14, padding: 18, marginBottom: 16,
    boxShadow: "inset 0 1px 0 rgba(16,185,129,0.1)",
  }}>
    <SectionLabel style={{ color: "#10b981" }}>🏆 Top Candidate</SectionLabel>
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
      <Avatar name={result.candidate_name} size={44} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 800, fontSize: 14, color: "var(--text-1)", marginBottom: 2 }}>{result.candidate_name}</div>
        <div style={{ fontSize: 11, color: "var(--text-3)" }}>{result.candidate_title} · {result.candidate_company}</div>
        <div style={{ display: "flex", gap: 5, marginTop: 6, flexWrap: "wrap" }}>
          {result.matched_skills.slice(0, 3).map(s => (
            <span key={s} className="chip-match" style={{ fontSize: 10 }}>{s}</span>
          ))}
        </div>
      </div>
      <ScoreRing value={Math.round(result.scores.overall_score)} size={50} stroke={4} />
    </div>
    <p style={{ color: "var(--text-2)", fontSize: 12, lineHeight: 1.7, marginBottom: 14 }} className="clamp-3">
      {result.reasoning_text}
    </p>
    <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
      {["Skill Match", "Career", "Trust"].map(label => {
        const key = label === "Skill Match" ? "semantic_skill_match" : label === "Career" ? "career_intelligence" : "trust_score";
        const val = Math.round((result.scores as any)[key] ?? 0);
        return (
          <div key={label} style={{ flex: 1, textAlign: "center", background: "rgba(255,255,255,0.04)", borderRadius: 8, padding: "8px 6px" }}>
            <div style={{ fontSize: 16, fontWeight: 900, color: getScoreColor(val) }}>{val}</div>
            <div style={{ fontSize: 9, color: "var(--text-3)", fontWeight: 700, letterSpacing: "0.5px" }}>{label.toUpperCase()}</div>
          </div>
        );
      })}
    </div>
    <button onClick={onView} style={{
      width: "100%", padding: "9px", borderRadius: 10, fontSize: 12, fontWeight: 700,
      background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.3)",
      color: "#10b981", cursor: "pointer", transition: "all 0.15s ease",
    }}
    onMouseEnter={e => { e.currentTarget.style.background = "rgba(16,185,129,0.2)"; }}
    onMouseLeave={e => { e.currentTarget.style.background = "rgba(16,185,129,0.12)"; }}
    >View Full Profile →</button>
  </div>
);

/* ─── Score bar chart ───────────────────────────────────────────────────────── */
export const ScoreChart: React.FC<{ results: RankingResult[] }> = ({ results }) => {
  const data = results.slice(0, 8).map(r => ({
    name: r.candidate_name.split(" ")[0],
    score: Math.round(r.scores.overall_score),
    color: getScoreColor(Math.round(r.scores.overall_score)),
  }));

  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 14, padding: "16px 18px", marginBottom: 14 }}>
      <SectionLabel>Score Distribution</SectionLabel>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
          <XAxis dataKey="name" tick={{ fill: "var(--text-3)", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "var(--text-3)", fontSize: 10 }} domain={[0, 100]} axisLine={false} tickLine={false} />
          <Tooltip cursor={false} contentStyle={CHART_TOOLTIP_STYLE} />
          <Bar dataKey="score" radius={[5, 5, 0, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.color} fillOpacity={0.85} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

/* ─── Risk pie chart ────────────────────────────────────────────────────────── */
export const RiskChart: React.FC<{ results: RankingResult[] }> = ({ results }) => {
  const pieData = [
    { name: "Low",    value: results.filter(r => r.risk_level === "Low").length,    color: "#10b981" },
    { name: "Medium", value: results.filter(r => r.risk_level === "Medium").length, color: "#f59e0b" },
    { name: "High",   value: results.filter(r => r.risk_level === "High").length,   color: "#ef4444" },
  ].filter(d => d.value > 0);

  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 14, padding: "16px 18px", marginBottom: 14 }}>
      <SectionLabel>Risk Distribution</SectionLabel>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <PieChart width={90} height={90}>
          <Pie data={pieData} cx={45} cy={45} innerRadius={28} outerRadius={42} paddingAngle={3} dataKey="value">
            {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
          </Pie>
          <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
        </PieChart>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 7 }}>
          {pieData.map(d => (
            <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: d.color, flexShrink: 0 }} />
              <span style={{ fontSize: 12, color: "var(--text-2)", flex: 1 }}>{d.name} Risk</span>
              <span style={{ fontSize: 12, fontWeight: 800, color: d.color }}>{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/* ─── Score area trend ──────────────────────────────────────────────────────── */
export const ScoreTrend: React.FC<{ results: RankingResult[] }> = ({ results }) => {
  const data = results.map((r, i) => ({
    rank: `#${i + 1}`,
    score: Math.round(r.scores.overall_score),
  }));
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 14, padding: "16px 18px", marginBottom: 14 }}>
      <SectionLabel>Score Falloff Curve</SectionLabel>
      <ResponsiveContainer width="100%" height={90}>
        <AreaChart data={data} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
          <defs>
            <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#7c3aed" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis dataKey="rank" tick={{ fill: "var(--text-3)", fontSize: 9 }} axisLine={false} tickLine={false} />
          <YAxis tick={false} axisLine={false} domain={[0, 100]} />
          <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
          <Area type="monotone" dataKey="score" stroke="#7c3aed" strokeWidth={2} fill="url(#scoreGrad)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

/* ─── Shortlist recommendation breakdown ─────────────────────────────────────── */
export const RecommendationBreakdown: React.FC<{ results: RankingResult[] }> = ({ results }) => {
  const cats = [
    { label: "Tech Round",   color: "#10b981", count: results.filter(r => r.recommendation?.includes("Technical")).length },
    { label: "HR Screen",    color: "#06b6d4", count: results.filter(r => r.recommendation?.includes("HR")).length },
    { label: "Further Rev.", color: "#f59e0b", count: results.filter(r => r.recommendation?.includes("Further")).length },
    { label: "Not Rec.",     color: "#ef4444", count: results.filter(r => r.recommendation?.includes("Not")).length },
  ];
  const total = results.length || 1;
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 14, padding: "16px 18px" }}>
      <SectionLabel>Recommendation Breakdown</SectionLabel>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {cats.map(c => (
          <div key={c.label}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 11, color: "var(--text-2)", fontWeight: 600 }}>{c.label}</span>
              <span style={{ fontSize: 11, fontWeight: 800, color: c.color }}>{c.count}</span>
            </div>
            <div style={{ height: 4, background: "rgba(255,255,255,0.05)", borderRadius: 99, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${(c.count / total) * 100}%`, background: c.color, borderRadius: 99, transition: "width 0.8s ease" }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/* ─── Active weight profile display ─────────────────────────────────────────── */
export const WeightProfileDisplay: React.FC<{ profile: WeightProfile }> = ({ profile }) => (
  <div style={{ background: "rgba(124,58,237,0.05)", border: "1px solid rgba(124,58,237,0.2)", borderRadius: 14, padding: "16px 18px", marginTop: 14 }}>
    <SectionLabel style={{ color: "#a78bfa" }}>Dynamic Weights</SectionLabel>
    <span className="badge badge-violet" style={{ marginBottom: 10, display: "inline-block", fontSize: 11 }}>
      {profile.profile_key.replace(/_/g, " ")}
    </span>
    <div style={{ display: "flex", flexDirection: "column", gap: 7, marginTop: 8 }}>
      {Object.entries(profile.weights).map(([k, v]) => (
        <div key={k} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 10, color: "var(--text-3)", fontWeight: 600, width: 75, flexShrink: 0 }}>{SCORE_LABELS[k] ?? k}</span>
          <div style={{ flex: 1, height: 4, background: "rgba(255,255,255,0.05)", borderRadius: 99, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${v}%`, background: "rgba(124,58,237,0.7)", borderRadius: 99 }} />
          </div>
          <span style={{ fontSize: 10, fontWeight: 800, color: "#a78bfa", width: 26, textAlign: "right" }}>{v}%</span>
        </div>
      ))}
    </div>
    <p style={{ color: "var(--text-3)", fontSize: 10, lineHeight: 1.6, marginTop: 10 }} className="clamp-3">
      {profile.rationale}
    </p>
  </div>
);
