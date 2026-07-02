import React, { useEffect, useState } from "react";

/* ─── Score Ring ────────────────────────────────────────────────────────────── */
interface ScoreRingProps { value: number; size?: number; stroke?: number; label?: string; }

const ringColor = (v: number) => v >= 80 ? "#10b981" : v >= 65 ? "#f59e0b" : "#ef4444";

export const ScoreRing: React.FC<ScoreRingProps> = ({ value, size = 54, stroke = 5, label }) => {
  const [animated, setAnimated] = useState(0);
  useEffect(() => { const t = setTimeout(() => setAnimated(value), 200); return () => clearTimeout(t); }, [value]);
  const r = (size - stroke * 2) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (animated / 100) * circ;
  const col = ringColor(value);
  return (
    <div style={{ position: "relative", width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={col} strokeWidth={stroke}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.1s cubic-bezier(0.34,1.56,0.64,1)", filter: `drop-shadow(0 0 5px ${col})` }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: size / 3.5, fontWeight: 800, color: col, fontVariantNumeric: "tabular-nums", lineHeight: 1 }}>
          {Math.round(value)}
        </span>
        {label && <span style={{ fontSize: 9, color: "var(--text-3)", fontWeight: 700, marginTop: 1 }}>{label}</span>}
      </div>
    </div>
  );
};

/* ─── Progress Bar ──────────────────────────────────────────────────────────── */
export const ProgressBar: React.FC<{ value: number; color?: string; height?: number; glow?: boolean }> = ({
  value, color, height = 5, glow = false,
}) => {
  const col = color ?? `linear-gradient(90deg, #7c3aed, #06b6d4)`;
  return (
    <div className="progress-track" style={{ height }}>
      <div className="progress-fill" style={{
        width: `${Math.min(100, Math.max(0, value))}%`,
        background: col,
        boxShadow: glow ? `0 0 8px ${color ?? "rgba(124,58,237,0.6)"}` : undefined,
      }} />
    </div>
  );
};

/* ─── Avatar ────────────────────────────────────────────────────────────────── */
const AVATAR_GRADIENTS = [
  "linear-gradient(135deg,#7c3aed,#06b6d4)",
  "linear-gradient(135deg,#059669,#0ea5e9)",
  "linear-gradient(135deg,#dc2626,#9333ea)",
  "linear-gradient(135deg,#d97706,#7c3aed)",
  "linear-gradient(135deg,#0891b2,#10b981)",
  "linear-gradient(135deg,#6d28d9,#f59e0b)",
];
const hashCode = (s: string) => s.split("").reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 0);

export const Avatar: React.FC<{ name: string; size?: number }> = ({ name, size = 38 }) => {
  const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
  const grad = AVATAR_GRADIENTS[Math.abs(hashCode(name)) % AVATAR_GRADIENTS.length];
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%", background: grad,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontWeight: 800, fontSize: size / 2.8, color: "#fff", flexShrink: 0,
      boxShadow: "0 0 0 2px rgba(255,255,255,0.06)",
    }}>{initials}</div>
  );
};

/* ─── Card ──────────────────────────────────────────────────────────────────── */
export const Card: React.FC<{
  children: React.ReactNode; className?: string; onClick?: () => void; hoverable?: boolean;
  accentColor?: string; glow?: boolean; padding?: string;
}> = ({ children, className = "", onClick, hoverable, accentColor, glow, padding = "p-5" }) => (
  <div
    onClick={onClick}
    className={`glass ${hoverable ? "glass-hover cursor-pointer" : ""} ${padding} ${className}`}
    style={{
      borderLeftColor: accentColor ? accentColor : undefined,
      borderLeftWidth: accentColor ? 3 : undefined,
      boxShadow: glow ? `0 0 30px rgba(124,58,237,0.12), inset 0 1px 0 rgba(255,255,255,0.06)` : `inset 0 1px 0 rgba(255,255,255,0.04)`,
    }}
  >{children}</div>
);

/* ─── Stat Card ─────────────────────────────────────────────────────────────── */
export const StatCard: React.FC<{ icon: string; label: string; value: string | number; color: string; sub?: string }> = ({
  icon, label, value, color, sub
}) => (
  <div className="glass p-5 flex items-start gap-4" style={{ boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)" }}>
    <div style={{
      width: 44, height: 44, borderRadius: 12, flexShrink: 0,
      background: `${color}18`, border: `1px solid ${color}30`,
      display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20,
    }}>{icon}</div>
    <div>
      <div style={{ fontSize: 26, fontWeight: 900, color, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>{value}</div>
      <div className="label-xs mt-1">{label}</div>
      {sub && <div style={{ fontSize: 11, color: "var(--text-3)", marginTop: 3 }}>{sub}</div>}
    </div>
  </div>
);

/* ─── Section Label ─────────────────────────────────────────────────────────── */
export const SectionLabel: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({ children, className = "", style }) => (
  <p className={`label-xs mb-3 ${className}`} style={style}>{children}</p>
);

/* ─── Skeleton ──────────────────────────────────────────────────────────────── */
export const Skeleton: React.FC<{ className?: string; style?: React.CSSProperties }> = ({ className = "", style }) => (
  <div className={`skeleton ${className}`} style={style} />
);

/* ─── Spinner ───────────────────────────────────────────────────────────────── */
export const Spinner: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = "" }) => (
  <svg className={`animate-spin-slow ${className}`} width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeOpacity={0.15} />
    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
);

/* ─── Empty State ───────────────────────────────────────────────────────────── */
export const EmptyState: React.FC<{ icon: string; title: string; desc: string }> = ({ icon, title, desc }) => (
  <div className="flex flex-col items-center justify-center py-20 gap-4">
    <div style={{ fontSize: 52, opacity: 0.3 }}>{icon}</div>
    <div style={{ color: "var(--text-2)", fontWeight: 700, fontSize: 16 }}>{title}</div>
    <div style={{ color: "var(--text-3)", fontSize: 13, textAlign: "center", maxWidth: 300 }}>{desc}</div>
  </div>
);

/* ─── Score color helpers ───────────────────────────────────────────────────── */
export const getScoreColor = (v: number) => v >= 80 ? "#10b981" : v >= 65 ? "#f59e0b" : "#ef4444";
export const getRiskClass  = (r: string) => r === "Low" ? "badge-green" : r === "Medium" ? "badge-amber" : "badge-red";
export const getRecColor   = (r: string | null) => {
  if (!r) return "var(--text-3)";
  if (r.includes("Technical")) return "#10b981";
  if (r.includes("HR"))        return "#06b6d4";
  if (r.includes("Further"))  return "#f59e0b";
  return "#ef4444";
};
