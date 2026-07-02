import React from "react";
import { BarChart3, MessageSquare, GitCompare, Download, Shield, Zap, ChevronRight } from "lucide-react";
import type { JobDescription, RankingResult } from "../../types";
import { getScoreColor } from "../ui";

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
  jd: JobDescription | null;
  results: RankingResult[];
  compareCount: number;
  onReset: () => void;
}

const NAV_ITEMS = [
  { id: "rankings", icon: BarChart3, label: "Rankings" },
  { id: "compare",  icon: GitCompare, label: "Compare" },
  { id: "chat",     icon: MessageSquare, label: "AI Chat" },
  { id: "export",   icon: Download,  label: "Export" },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeView, onNavigate, jd, results, compareCount, onReset }) => {
  const shortlisted = results.filter(r => r.recommendation?.includes("Technical")).length;
  const lowRisk     = results.filter(r => r.risk_level === "Low").length;
  const avgScore    = results.length ? Math.round(results.reduce((s, r) => s + r.scores.overall_score, 0) / results.length) : 0;

  return (
    <aside style={{
      width: "var(--sidebar-w)",
      background: "rgba(0,0,0,0.35)",
      borderRight: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      padding: "0",
      backdropFilter: "blur(20px)",
      zIndex: 50,
    }}>
      {/* Logo */}
      <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid var(--border)" }}>
        <button onClick={onReset} style={{ display: "flex", alignItems: "center", gap: 10, background: "none", border: "none", cursor: "pointer", padding: 0 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 10, flexShrink: 0,
            background: "linear-gradient(135deg,#7c3aed,#06b6d4)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 17, boxShadow: "0 0 16px rgba(124,58,237,0.4)",
          }}>🧠</div>
          <div style={{ textAlign: "left" }}>
            <div style={{ fontWeight: 900, fontSize: 15, color: "var(--text-1)", letterSpacing: "-0.3px" }}>TalentAI</div>
            <div className="label-xs" style={{ marginBottom: 0 }}>Recruiter Platform</div>
          </div>
        </button>
      </div>

      {/* Active JD pill */}
      {jd && (
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
          <div className="label-xs" style={{ marginBottom: 6 }}>Active Analysis</div>
          <div style={{
            background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.25)",
            borderRadius: 8, padding: "8px 10px",
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#a78bfa", lineHeight: 1.3 }}>{jd.title}</div>
            <div style={{ fontSize: 10, color: "var(--text-3)", marginTop: 3 }}>
              {results.length} candidates ranked
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav style={{ padding: "12px 10px", flex: 1 }}>
        <div className="label-xs" style={{ padding: "0 8px", marginBottom: 8 }}>Navigation</div>
        {NAV_ITEMS.map(({ id, icon: Icon, label }) => {
          const active = activeView === id;
          const disabled = (id === "compare" || id === "export") && results.length === 0;
          const hasBadge = id === "compare" && compareCount > 0;
          return (
            <button key={id} onClick={() => !disabled && onNavigate(id)} style={{
              width: "100%", display: "flex", alignItems: "center", gap: 10,
              padding: "9px 10px", borderRadius: 8, border: "none", cursor: disabled ? "not-allowed" : "pointer",
              background: active ? "rgba(124,58,237,0.15)" : "transparent",
              color: active ? "#a78bfa" : disabled ? "var(--text-4)" : "var(--text-2)",
              fontSize: 13, fontWeight: active ? 700 : 500,
              transition: "all 0.15s ease", marginBottom: 2,
              borderLeft: active ? "2px solid #7c3aed" : "2px solid transparent",
            }}
            onMouseEnter={e => { if (!active && !disabled) e.currentTarget.style.background = "var(--bg-hover)"; e.currentTarget.style.color = disabled ? "var(--text-4)" : "var(--text-1)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = active ? "rgba(124,58,237,0.15)" : "transparent"; e.currentTarget.style.color = active ? "#a78bfa" : disabled ? "var(--text-4)" : "var(--text-2)"; }}
            >
              <Icon size={15} />
              <span style={{ flex: 1, textAlign: "left" }}>{label}</span>
              {hasBadge && (
                <span style={{ background: "#7c3aed", color: "#fff", borderRadius: 99, fontSize: 10, fontWeight: 800, padding: "1px 6px" }}>
                  {compareCount}
                </span>
              )}
              {active && <ChevronRight size={12} style={{ opacity: 0.5 }} />}
            </button>
          );
        })}
      </nav>

      {/* Quick stats */}
      {results.length > 0 && (
        <div style={{ padding: "12px 16px 16px", borderTop: "1px solid var(--border)" }}>
          <div className="label-xs" style={{ marginBottom: 10 }}>Quick Stats</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              { l: "Avg Score", v: avgScore, col: getScoreColor(avgScore) },
              { l: "Shortlisted", v: shortlisted, col: "#10b981" },
              { l: "Low Risk",  v: lowRisk, col: "#06b6d4" },
            ].map(s => (
              <div key={s.l} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 12, color: "var(--text-3)" }}>{s.l}</span>
                <span style={{ fontSize: 13, fontWeight: 800, color: s.col, fontVariantNumeric: "tabular-nums" }}>{s.v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* New Analysis */}
      <div style={{ padding: "12px 16px 20px", borderTop: "1px solid var(--border)" }}>
        <button onClick={onReset} className="btn-ghost" style={{ width: "100%", fontSize: 12, gap: 6 }}>
          <Zap size={12} />New Analysis
        </button>
      </div>
    </aside>
  );
};
