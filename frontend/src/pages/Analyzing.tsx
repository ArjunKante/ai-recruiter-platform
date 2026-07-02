import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { RankingResult } from "../types";
import { Avatar, ScoreRing, getScoreColor, getRiskClass } from "../components/ui";

const STEPS = [
  { id: "parsing",   label: "Parsing resumes",             icon: "📄" },
  { id: "embedding", label: "Building semantic index",      icon: "🔢" },
  { id: "scoring",   label: "Scoring 6 dimensions",         icon: "⚡" },
  { id: "reasoning", label: "Generating AI reasoning",      icon: "🧠" },
  { id: "ranking",   label: "Computing final rankings",     icon: "🏆" },
];

const MESSAGES = [
  "Extracting career timelines…",
  "Detecting skill aliases and overlaps…",
  "Running trust verification engine…",
  "Analyzing promotion velocity…",
  "Computing semantic similarity scores…",
  "Checking behavioral signals…",
  "Calibrating dynamic weights for this role…",
  "Generating recruiter-style reasoning…",
];

interface AnalyzingPageProps {
  partialResults: RankingResult[];
  total: number;
}

export const AnalyzingPage: React.FC<AnalyzingPageProps> = ({ partialResults, total }) => {
  const [stepIdx, setStepIdx] = useState(0);
  const [msgIdx,  setMsgIdx]  = useState(0);

  useEffect(() => {
    const s = setInterval(() => setStepIdx(i => Math.min(i + 1, STEPS.length - 1)), 1800);
    const m = setInterval(() => setMsgIdx(i => (i + 1) % MESSAGES.length), 2200);
    return () => { clearInterval(s); clearInterval(m); };
  }, []);

  const pct = total > 0 ? Math.round((partialResults.length / total) * 100) : 0;

  return (
    <div style={{
      minHeight: "100vh", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      padding: "40px 24px", position: "relative", overflow: "hidden",
      background: "var(--bg-base)",
    }}>
      {/* Ambient orbs */}
      <div style={{ position: "absolute", top: "20%", left: "15%", width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(124,58,237,0.08) 0%, transparent 70%)", animation: "orbMove 8s ease-in-out infinite", pointerEvents: "none" }} />
      <div style={{ position: "absolute", bottom: "20%", right: "10%", width: 400, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%)", animation: "orbMove 10s ease-in-out infinite reverse", pointerEvents: "none" }} />

      {/* Center content */}
      <div style={{ textAlign: "center", marginBottom: 48, zIndex: 1 }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          style={{ fontSize: 56, display: "inline-block", marginBottom: 20, filter: "drop-shadow(0 0 20px rgba(124,58,237,0.6))" }}
        >🧠</motion.div>
        <h1 className="display-lg" style={{ marginBottom: 10 }}>
          Evaluating Candidates
        </h1>
        <AnimatePresence mode="wait">
          <motion.p
            key={msgIdx}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.3 }}
            style={{ color: "var(--text-3)", fontSize: 14, fontWeight: 500 }}
          >{MESSAGES[msgIdx]}</motion.p>
        </AnimatePresence>
      </div>

      {/* Steps */}
      <div style={{ display: "flex", gap: 6, marginBottom: 40, zIndex: 1 }}>
        {STEPS.map((step, i) => {
          const done    = i < stepIdx;
          const current = i === stepIdx;
          return (
            <div key={step.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{
                display: "flex", alignItems: "center", gap: 7, padding: "6px 12px", borderRadius: 99,
                background: done ? "rgba(16,185,129,0.12)" : current ? "rgba(124,58,237,0.15)" : "rgba(255,255,255,0.04)",
                border: `1px solid ${done ? "rgba(16,185,129,0.3)" : current ? "rgba(124,58,237,0.4)" : "var(--border)"}`,
                transition: "all 0.4s ease",
              }}>
                <span style={{ fontSize: 13 }}>{step.icon}</span>
                <span style={{
                  fontSize: 11, fontWeight: 700,
                  color: done ? "#10b981" : current ? "#a78bfa" : "var(--text-3)",
                  transition: "color 0.4s ease",
                }}>{step.label}</span>
                {done && <span style={{ color: "#10b981", fontSize: 11 }}>✓</span>}
                {current && <span className="animate-pulse-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "#a78bfa", flexShrink: 0 }} />}
              </div>
              {i < STEPS.length - 1 && (
                <div style={{ width: 12, height: 1, background: done ? "rgba(16,185,129,0.3)" : "var(--border)" }} />
              )}
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div style={{ width: "100%", maxWidth: 520, marginBottom: 10, zIndex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontSize: 13, color: "var(--text-2)" }}>
            {partialResults.length > 0
              ? `Analyzed ${partialResults.length} of ${total} candidates`
              : "Initializing pipeline…"}
          </span>
          <span style={{ fontSize: 13, fontWeight: 800, color: "#7c3aed" }}>{pct}%</span>
        </div>
        <div style={{ height: 6, background: "rgba(255,255,255,0.06)", borderRadius: 99, overflow: "hidden" }}>
          <motion.div
            initial={{ width: "0%" }}
            animate={{ width: total > 0 ? `${pct}%` : "15%" }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            style={{
              height: "100%", borderRadius: 99,
              background: "linear-gradient(90deg, #7c3aed, #06b6d4)",
              boxShadow: "0 0 10px rgba(124,58,237,0.6)",
            }}
          />
        </div>
      </div>

      {/* Live candidate cards */}
      {total > 0 && (
        <div style={{ width: "100%", maxWidth: 520, zIndex: 1, marginTop: 20 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <AnimatePresence>
              {partialResults.map((r, i) => (
                <motion.div
                  key={r.candidate_id}
                  initial={{ opacity: 0, x: -20, scale: 0.97 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  transition={{ duration: 0.35, delay: i * 0.05 }}
                  style={{
                    display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                    background: "var(--bg-surface)", border: "1px solid var(--border)",
                    borderRadius: 12, backdropFilter: "blur(10px)",
                  }}
                >
                  <Avatar name={r.candidate_name} size={32} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-1)" }}>{r.candidate_name}</div>
                    <div style={{ fontSize: 11, color: "var(--text-3)" }}>{r.candidate_title} · {r.candidate_company}</div>
                  </div>
                  <span className={`badge ${getRiskClass(r.risk_level)}`}>{r.risk_level}</span>
                  <ScoreRing value={Math.round(r.scores.overall_score)} size={42} stroke={4} />
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Placeholder rows */}
            {Array.from({ length: Math.max(0, total - partialResults.length) }, (_, i) => (
              <div key={`ph-${i}`} style={{
                display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                background: "rgba(255,255,255,0.015)", border: "1px solid rgba(255,255,255,0.04)",
                borderRadius: 12, opacity: 0.5,
              }}>
                <div className="skeleton" style={{ width: 32, height: 32, borderRadius: "50%", flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div className="skeleton" style={{ height: 11, width: "55%", marginBottom: 6, borderRadius: 4 }} />
                  <div className="skeleton" style={{ height: 9, width: "35%", borderRadius: 4 }} />
                </div>
                <div className="skeleton" style={{ width: 42, height: 42, borderRadius: "50%", flexShrink: 0 }} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
