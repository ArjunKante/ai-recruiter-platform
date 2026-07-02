import React from "react";
import { Search, RefreshCw, Download } from "lucide-react";
import type { JobDescription } from "../../types";
import { Spinner } from "../ui";

interface HeaderBarProps {
  jd: JobDescription | null;
  isRanking: boolean;
  onReRank: () => void;
  onExport: (fmt: "csv" | "xlsx" | "pdf") => void;
  candidateCount: number;
  search: string;
  onSearch: (v: string) => void;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({
  jd, isRanking, onReRank, onExport, candidateCount, search, onSearch
}) => (
  <header style={{
    height: "var(--header-h)",
    background: "rgba(5,5,15,0.88)",
    borderBottom: "1px solid var(--border)",
    backdropFilter: "blur(20px)",
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "0 24px",
    position: "sticky",
    top: 0,
    zIndex: 40,
  }}>
    {/* Breadcrumb */}
    <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
      <span style={{ color: "var(--text-3)", fontSize: 13 }}>Dashboard</span>
      {jd && (
        <>
          <span style={{ color: "var(--text-4)", fontSize: 13 }}>/</span>
          <span style={{
            fontSize: 13, fontWeight: 600, color: "var(--text-2)",
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 240
          }}>{jd.title}</span>
          <span className="badge badge-violet" style={{ flexShrink: 0 }}>{jd.role_weight_profile?.replace("_", " ")}</span>
        </>
      )}
    </div>

    {/* Search */}
    <div style={{ flex: 1, maxWidth: 360, position: "relative" }}>
      <Search size={14} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-3)" }} />
      <input
        className="input"
        value={search}
        onChange={e => onSearch(e.target.value)}
        placeholder="Search candidates, companies..."
        style={{ paddingLeft: 34, height: 36, fontSize: 13 }}
      />
    </div>

    <div style={{ flex: 1 }} />

    {/* Candidate count */}
    {candidateCount > 0 && (
      <span style={{ fontSize: 12, color: "var(--text-3)", flexShrink: 0 }}>
        <span style={{ color: "var(--text-1)", fontWeight: 700 }}>{candidateCount}</span> candidates
      </span>
    )}

    {/* Re-rank */}
    <button
      onClick={onReRank}
      disabled={isRanking}
      className="btn-ghost"
      style={{ flexShrink: 0, height: 36, fontSize: 12 }}
    >
      {isRanking ? <Spinner size={12} /> : <RefreshCw size={12} />}
      {isRanking ? "Ranking…" : "Re-rank"}
    </button>

    {/* Export dropdown */}
    <div style={{ position: "relative" }} className="tooltip-wrap">
      <button className="btn-ghost" style={{ height: 36, fontSize: 12, flexShrink: 0, gap: 5 }}>
        <Download size={12} /> Export
      </button>
      <div style={{
        position: "absolute", right: 0, top: "calc(100% + 6px)",
        background: "#0d0d20", border: "1px solid var(--border-strong)",
        borderRadius: 10, overflow: "hidden", width: 130,
        boxShadow: "0 16px 48px rgba(0,0,0,0.6)",
        opacity: 0, pointerEvents: "none",
        transition: "opacity 0.15s ease",
      }}
      className="export-menu">
        {(["csv","xlsx","pdf"] as const).map(fmt => (
          <button key={fmt} onClick={() => onExport(fmt)} style={{
            width: "100%", padding: "10px 16px", background: "transparent",
            border: "none", color: "var(--text-2)", fontSize: 12, fontWeight: 600,
            cursor: "pointer", textAlign: "left", textTransform: "uppercase", letterSpacing: 1,
            transition: "background 0.1s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >.{fmt}</button>
        ))}
      </div>
    </div>
  </header>
);
