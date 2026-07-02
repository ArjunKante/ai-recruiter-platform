import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { rankingApi } from "./api/client";
import { useAppStore } from "./lib/store";
import { LandingPage } from "./pages/Landing";
import { AnalyzingPage } from "./pages/Analyzing";
import { DashboardPage } from "./pages/Dashboard";
import type { RankingResult } from "./types";

const qc = new QueryClient({ defaultOptions: { queries: { retry: 1 } } });

type AppView = "landing" | "analyzing" | "dashboard";

function AppInner() {
  const { activeJd, rankings, setRankings, clearCompare } = useAppStore();
  const [view,           setView]          = useState<AppView>("landing");
  const [isRanking,      setIsRanking]     = useState(false);
  const [partialResults, setPartialResults] = useState<RankingResult[]>([]);

  const runRanking = async () => {
    if (!activeJd) return;
    setIsRanking(true);
    setPartialResults([]);
    setView("analyzing");

    try {
      const res = await rankingApi.run(activeJd.id);
      // Animate the reveal: stream in results progressively
      const sorted = [...res.data].sort((a, b) => (b.scores?.overall_score ?? 0) - (a.scores?.overall_score ?? 0));
      for (let i = 0; i <= sorted.length; i++) {
        setPartialResults(sorted.slice(0, i));
        if (i < sorted.length) await new Promise(r => setTimeout(r, 80));
      }
      setRankings(sorted);
      await new Promise(r => setTimeout(r, 600)); // let the last card land
      setView("dashboard");
    } catch (e) {
      console.error("Ranking failed:", e);
      setView("dashboard");
    } finally {
      setIsRanking(false);
    }
  };

  const handleReset = () => {
    setView("landing");
    setRankings([]);
    setPartialResults([]);
    clearCompare();
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-base)", color: "var(--text-1)" }}>
      <AnimatePresence mode="wait">
        {view === "landing" && (
          <motion.div key="landing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.98 }} transition={{ duration: 0.3 }}>
            <LandingPage onAnalysisReady={runRanking} />
          </motion.div>
        )}

        {view === "analyzing" && (
          <motion.div key="analyzing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
            <AnalyzingPage partialResults={partialResults} total={useAppStore.getState().candidateCount || 6} />
          </motion.div>
        )}

        {view === "dashboard" && (
          <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
            <DashboardPage
              rankings={rankings}
              isRanking={isRanking}
              onReRank={runRanking}
              onReset={handleReset}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AppInner />
    </QueryClientProvider>
  );
}
