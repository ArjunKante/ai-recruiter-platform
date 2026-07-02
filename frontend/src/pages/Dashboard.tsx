import React, { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Filter, SortDesc } from "lucide-react";
import { exportApi, jobsApi } from "../api/client";
import type { RankingResult, WeightProfile } from "../types";
import { useAppStore } from "../lib/store";
import { CandidateRow } from "../components/candidate/CandidateRow";
import { CandidateDetail } from "../components/candidate/CandidateDetail";
import { CompareView } from "../components/dashboard/CompareView";
import { ChatView } from "../components/dashboard/ChatView";
import {
  TopCandidateCard, ScoreChart, RiskChart, ScoreTrend,
  RecommendationBreakdown, WeightProfileDisplay,
} from "../components/dashboard/Charts";
import { Sidebar } from "../components/layout/Sidebar";
import { HeaderBar } from "../components/layout/Header";
import { Skeleton, StatCard, EmptyState } from "../components/ui";
import { getScoreColor } from "../components/ui";

type AppView = "rankings" | "compare" | "chat" | "export";
type SortKey = "overall" | "risk" | "confidence" | "name";

const RISK_ORDER: Record<string, number> = { Low: 0, Medium: 1, High: 2 };

export const DashboardPage: React.FC<{
  rankings: RankingResult[];
  isRanking: boolean;
  onReRank: () => void;
  onReset: () => void;
}> = ({ rankings, isRanking, onReRank, onReset }) => {
  const { activeJd, compareIds, toggleCompare, clearCompare, candidateCount } = useAppStore();
  const [view,      setView]    = useState<AppView>("rankings");
  const [selected,  setSelected] = useState<RankingResult | null>(null);
  const [search,    setSearch]   = useState("");
  const [filterRisk,setFilterRisk] = useState("All");
  const [filterRec, setFilterRec]  = useState("All");
  const [sortKey,   setSortKey]    = useState<SortKey>("overall");
  const [showFilter,setShowFilter] = useState(false);
  const [weights,   setWeights]    = useState<WeightProfile | null>(null);

  useEffect(() => {
    if (activeJd && !weights) {
      jobsApi.getWeights(activeJd.id).then(r => setWeights(r.data)).catch(() => {});
    }
  }, [activeJd]);

  const filtered = useMemo(() => {
    let list = [...rankings];
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(r =>
        r.candidate_name.toLowerCase().includes(q) ||
        (r.candidate_company ?? "").toLowerCase().includes(q) ||
        (r.candidate_title ?? "").toLowerCase().includes(q) ||
        r.matched_skills.some(s => s.toLowerCase().includes(q))
      );
    }
    if (filterRisk !== "All") list = list.filter(r => r.risk_level === filterRisk);
    if (filterRec  !== "All") list = list.filter(r => r.recommendation?.includes(filterRec));
    list.sort((a, b) => {
      switch (sortKey) {
        case "overall":    return b.scores.overall_score - a.scores.overall_score;
        case "confidence": return b.confidence_score - a.confidence_score;
        case "risk":       return RISK_ORDER[a.risk_level] - RISK_ORDER[b.risk_level];
        case "name":       return a.candidate_name.localeCompare(b.candidate_name);
        default:           return 0;
      }
    });
    return list;
  }, [rankings, search, filterRisk, filterRec, sortKey]);

  const compareResults = useMemo(() => rankings.filter(r => compareIds.includes(r.candidate_id)), [rankings, compareIds]);

  const handleExport = async (fmt: "csv" | "xlsx" | "pdf") => {
    if (!activeJd) return;
    try { await exportApi.download(activeJd.id, fmt); } catch {}
  };

  const shortlisted = rankings.filter(r => r.recommendation?.includes("Technical")).length;
  const avgScore    = rankings.length ? Math.round(rankings.reduce((s, r) => s + r.scores.overall_score, 0) / rankings.length) : 0;

  // Intercept non-rankings views
  if (view === "compare" && compareResults.length >= 2) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "var(--sidebar-w) 1fr", minHeight: "100vh" }}>
        <Sidebar activeView={view} onNavigate={setView as any} jd={activeJd} results={rankings} compareCount={compareIds.length} onReset={onReset} />
        <div style={{ minHeight: "100vh", overflowY: "auto" }}>
          <CompareView results={compareResults} onBack={() => setView("rankings")} />
        </div>
      </div>
    );
  }

  if (view === "chat" && activeJd) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "var(--sidebar-w) 1fr", minHeight: "100vh" }}>
        <Sidebar activeView={view} onNavigate={setView as any} jd={activeJd} results={rankings} compareCount={compareIds.length} onReset={onReset} />
        <ChatView jdId={activeJd.id} results={rankings} onBack={() => setView("rankings")} />
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "var(--sidebar-w) 1fr", minHeight: "100vh" }}>
      {/* Sidebar */}
      <Sidebar
        activeView={view}
        onNavigate={v => { if (v === "compare" && compareIds.length < 2) return; setView(v as AppView); }}
        jd={activeJd}
        results={rankings}
        compareCount={compareIds.length}
        onReset={onReset}
      />

      {/* Main */}
      <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", overflow: "hidden" }}>
        {/* Header */}
        <HeaderBar
          jd={activeJd}
          isRanking={isRanking}
          onReRank={onReRank}
          onExport={handleExport}
          candidateCount={candidateCount || rankings.length}
          search={search}
          onSearch={setSearch}
        />

        {/* Body */}
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 288px", overflow: "hidden" }}>
          {/* Left: candidate list */}
          <div style={{ overflowY: "auto", padding: "24px 24px 24px" }}>
            {/* Stats row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 24 }}>
              <StatCard icon="👥" label="Candidates" value={rankings.length} color="#06b6d4" />
              <StatCard icon="⭐" label="Shortlisted" value={shortlisted} color="#10b981" sub="Proceed to tech round" />
              <StatCard icon="📊" label="Avg Score" value={avgScore} color={getScoreColor(avgScore)} />
              <StatCard icon="🛡" label="Low Risk" value={rankings.filter(r => r.risk_level === "Low").length} color="#a78bfa" />
            </div>

            {/* Compare bar */}
            <AnimatePresence>
              {compareIds.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                  animate={{ opacity: 1, height: "auto", marginBottom: 16 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  style={{
                    display: "flex", alignItems: "center", gap: 10, padding: "11px 16px",
                    background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.3)",
                    borderRadius: 12, overflow: "hidden",
                  }}
                >
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#a78bfa", flexShrink: 0 }}>⚡ Compare:</span>
                  {compareResults.map(r => (
                    <span key={r.id} className="badge badge-violet">{r.candidate_name.split(" ")[0]}</span>
                  ))}
                  <div style={{ flex: 1 }} />
                  {compareIds.length >= 2 && (
                    <button onClick={() => setView("compare")}
                      style={{ padding: "6px 14px", borderRadius: 8, background: "#7c3aed", border: "none", color: "#fff", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
                      Compare →
                    </button>
                  )}
                  {compareIds.length < 2 && (
                    <span style={{ fontSize: 11, color: "var(--text-3)" }}>Add {2 - compareIds.length} more</span>
                  )}
                  <button onClick={clearCompare} className="btn-ghost" style={{ height: 28, fontSize: 11 }}>Clear</button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Filter toolbar */}
            <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
              {/* Risk filter */}
              {(["All", "Low", "Medium", "High"] as const).map(r => (
                <button key={r} onClick={() => setFilterRisk(r)}
                  style={{
                    padding: "6px 13px", borderRadius: 99, fontSize: 12, fontWeight: 700, cursor: "pointer", border: "1px solid",
                    borderColor: filterRisk === r ? "#7c3aed" : "var(--border)",
                    background: filterRisk === r ? "rgba(124,58,237,0.15)" : "transparent",
                    color: filterRisk === r ? "#a78bfa" : "var(--text-3)",
                    transition: "all 0.15s ease",
                  }}>
                  {r === "All" ? "All Risk" : r === "Low" ? "🟢 Low" : r === "Medium" ? "🟡 Medium" : "🔴 High"}
                </button>
              ))}

              <div style={{ height: 20, width: 1, background: "var(--border)", margin: "0 4px" }} />

              {/* Sort */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <SortDesc size={12} style={{ color: "var(--text-3)" }} />
                <select
                  value={sortKey} onChange={e => setSortKey(e.target.value as SortKey)}
                  style={{
                    background: "transparent", border: "1px solid var(--border)", borderRadius: 8,
                    color: "var(--text-2)", fontSize: 12, fontWeight: 600, padding: "5px 10px", cursor: "pointer",
                    fontFamily: "inherit",
                  }}
                >
                  <option value="overall">Sort: Score</option>
                  <option value="risk">Sort: Risk</option>
                  <option value="confidence">Sort: Confidence</option>
                  <option value="name">Sort: Name</option>
                </select>
              </div>

              <div style={{ flex: 1 }} />
              <span style={{ fontSize: 12, color: "var(--text-3)" }}>
                {filtered.length} of {rankings.length}
              </span>
            </div>

            {/* Candidate list */}
            {isRanking ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[...Array(6)].map((_, i) => <Skeleton key={i} style={{ height: 92, borderRadius: 14 }} />)}
              </div>
            ) : filtered.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {filtered.map((r, idx) => {
                  const originalRank = rankings.findIndex(x => x.candidate_id === r.candidate_id) + 1;
                  return (
                    <CandidateRow
                      key={r.id}
                      result={r}
                      rank={originalRank}
                      isComparing={compareIds.includes(r.candidate_id)}
                      onToggleCompare={() => toggleCompare(r.candidate_id)}
                      onClick={() => setSelected(r)}
                    />
                  );
                })}
              </div>
            ) : (
              <EmptyState icon="🔍" title="No candidates match" desc="Try adjusting your search or filter criteria" />
            )}
          </div>

          {/* Right: sticky sidebar */}
          <div style={{
            borderLeft: "1px solid var(--border)", overflowY: "auto",
            padding: "20px 18px", display: "flex", flexDirection: "column", gap: 0,
          }}>
            {isRanking ? (
              <>
                <Skeleton style={{ height: 200, marginBottom: 14, borderRadius: 14 }} />
                <Skeleton style={{ height: 180, marginBottom: 14, borderRadius: 14 }} />
                <Skeleton style={{ height: 140, borderRadius: 14 }} />
              </>
            ) : rankings.length > 0 ? (
              <>
                {rankings[0] && <TopCandidateCard result={rankings[0]} onView={() => setSelected(rankings[0])} />}
                <ScoreChart results={rankings} />
                <RiskChart results={rankings} />
                <ScoreTrend results={rankings} />
                <RecommendationBreakdown results={rankings} />
                {weights && <WeightProfileDisplay profile={weights} />}
              </>
            ) : null}
          </div>
        </div>
      </div>

      {/* Detail modal */}
      <CandidateDetail result={selected} onClose={() => setSelected(null)} />
    </div>
  );
};
