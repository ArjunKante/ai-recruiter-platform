import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Send, Sparkles } from "lucide-react";
import { chatApi } from "../../api/client";
import type { ChatMessage, RankingResult } from "../../types";
import { Avatar, Spinner, getScoreColor, getRiskClass } from "../ui";

const SUGGESTIONS = [
  { label: "Top 3 candidates", icon: "🏆", query: "Who are the top 3 candidates and why?" },
  { label: "Low risk only",    icon: "🛡", query: "Show me only the low-risk candidates" },
  { label: "Python experts",   icon: "🐍", query: "Who has the strongest Python experience?" },
  { label: "Interview ready",  icon: "✅", query: "Which candidates are ready for a technical interview?" },
  { label: "Leadership exp",   icon: "👥", query: "Who has team leadership or mentoring experience?" },
  { label: "Startup founders", icon: "🚀", query: "Any candidates with startup or founding experience?" },
];

interface Props {
  jdId: number;
  results: RankingResult[];
  onBack: () => void;
}

export const ChatView: React.FC<Props> = ({ jdId, results, onBack }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([{
    role: "ai",
    content: `Hi! I've deeply analyzed all ${results.length} candidates for this role. Ask me anything — which skills they have, why certain candidates rank higher, hiring risks, or get my recommendation on who to interview first.`,
  }]);
  const [input,   setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const [referencedIds, setReferencedIds] = useState<number[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const send = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg) return;
    setInput("");
    setMessages(p => [...p, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const res = await chatApi.send(jdId, msg, history);
      setMessages(p => [...p, { role: "ai", content: res.data.reply }]);
      setReferencedIds(res.data.referenced_candidate_ids ?? []);
    } catch {
      setMessages(p => [...p, { role: "ai", content: "⚠ Request failed. Please check the API connection and try again." }]);
    }
    setLoading(false);
    inputRef.current?.focus();
  };

  const refCandidates = results.filter(r => referencedIds.includes(r.candidate_id)).slice(0, 3);

  return (
    <div style={{ height: "calc(100vh - var(--header-h))", display: "flex", overflow: "hidden" }}>
      {/* Main chat */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "0 0 0 0" }}>
        {/* Chat header */}
        <div style={{ padding: "20px 28px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 14 }}>
          <button onClick={onBack} className="btn-ghost" style={{ height: 34, gap: 6 }}>
            <ArrowLeft size={13} /> Back
          </button>
          <div>
            <h2 style={{ fontSize: 17, fontWeight: 800, letterSpacing: "-0.3px" }}>💬 AI Recruiter Chat</h2>
            <p style={{ color: "var(--text-3)", fontSize: 12, marginTop: 1 }}>
              Natural language search over {results.length} ranked candidates
            </p>
          </div>
          <div style={{ flex: 1 }} />
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 8px #10b981" }} />
            <span style={{ fontSize: 12, color: "var(--text-3)" }}>Claude AI connected</span>
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
          <AnimatePresence initial={false}>
            {messages.map((m, i) => (
              <motion.div key={i}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.25 }}
                style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", gap: 10 }}
              >
                {m.role === "ai" && (
                  <div style={{ width: 30, height: 30, borderRadius: 10, background: "linear-gradient(135deg,#7c3aed,#06b6d4)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, flexShrink: 0, marginTop: 2, boxShadow: "0 0 12px rgba(124,58,237,0.3)" }}>
                    🧠
                  </div>
                )}
                <div style={{
                  maxWidth: "76%", padding: "12px 16px", borderRadius: m.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                  fontSize: 14, lineHeight: 1.7, whiteSpace: "pre-wrap",
                  background: m.role === "user"
                    ? "linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%)"
                    : "var(--bg-surface-2)",
                  border: m.role === "ai" ? "1px solid var(--border)" : "none",
                  color: "var(--text-1)",
                  boxShadow: m.role === "user" ? "0 4px 16px rgba(124,58,237,0.35)" : "none",
                }}>{m.content}</div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          <AnimatePresence>
            {loading && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                style={{ display: "flex", gap: 10 }}>
                <div style={{ width: 30, height: 30, borderRadius: 10, background: "linear-gradient(135deg,#7c3aed,#06b6d4)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, flexShrink: 0 }}>🧠</div>
                <div style={{ padding: "14px 18px", background: "var(--bg-surface-2)", border: "1px solid var(--border)", borderRadius: "16px 16px 16px 4px" }}>
                  <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
                    {[0, 1, 2].map(i => (
                      <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#7c3aed", animation: `bounce 1s ease-in-out ${i * 0.18}s infinite` }} />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>

        {/* Suggestions */}
        <div style={{ padding: "12px 28px 0", display: "flex", gap: 7, flexWrap: "wrap" }}>
          {SUGGESTIONS.map(s => (
            <button key={s.label} onClick={() => send(s.query)} disabled={loading}
              style={{
                display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 99,
                border: "1px solid var(--border)", background: "transparent",
                color: "var(--text-3)", cursor: "pointer", fontSize: 12, fontWeight: 600,
                transition: "all 0.15s ease", opacity: loading ? 0.5 : 1,
              }}
              onMouseEnter={e => { if (!loading) { e.currentTarget.style.borderColor = "rgba(124,58,237,0.5)"; e.currentTarget.style.color = "#a78bfa"; e.currentTarget.style.background = "rgba(124,58,237,0.07)"; } }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-3)"; e.currentTarget.style.background = "transparent"; }}
            >
              <span style={{ fontSize: 13 }}>{s.icon}</span> {s.label}
            </button>
          ))}
        </div>

        {/* Input */}
        <div style={{ padding: "14px 28px 24px", display: "flex", gap: 10 }}>
          <div style={{ flex: 1, position: "relative" }}>
            <Sparkles size={14} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-4)" }} />
            <input
              ref={inputRef}
              className="input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
              placeholder="Ask about candidates, skills, seniority, risk factors…"
              style={{ paddingLeft: 38, height: 46, fontSize: 14 }}
              disabled={loading}
            />
          </div>
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            style={{
              width: 46, height: 46, borderRadius: 12, border: "none", cursor: "pointer",
              background: "linear-gradient(135deg,#7c3aed,#5b21b6)",
              display: "flex", alignItems: "center", justifyContent: "center",
              transition: "all 0.18s ease",
              opacity: !input.trim() || loading ? 0.45 : 1,
              boxShadow: input.trim() ? "0 0 16px rgba(124,58,237,0.35)" : "none",
              flexShrink: 0,
            }}
          >
            {loading ? <Spinner size={15} />  : <Send size={16} color="#fff" />}
          </button>
        </div>
      </div>

      {/* Right panel — referenced candidates */}
      <div style={{ width: 280, borderLeft: "1px solid var(--border)", display: "flex", flexDirection: "column", flexShrink: 0 }}>
        <div style={{ padding: "20px 18px", borderBottom: "1px solid var(--border)" }}>
          <div className="label-xs">Referenced Candidates</div>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "14px" }}>
          <AnimatePresence mode="wait">
            {refCandidates.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {refCandidates.map((r, i) => (
                  <motion.div key={r.candidate_id}
                    initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.07 }}
                    style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 12, padding: "12px 14px" }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
                      <Avatar name={r.candidate_name} size={32} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 700, fontSize: 12, color: "var(--text-1)" }}>{r.candidate_name}</div>
                        <div style={{ fontSize: 10, color: "var(--text-3)" }}>{r.candidate_company}</div>
                      </div>
                      <div style={{ fontSize: 15, fontWeight: 900, color: getScoreColor(r.scores.overall_score) }}>
                        {Math.round(r.scores.overall_score)}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                      <span className={`badge ${getRiskClass(r.risk_level)}`} style={{ fontSize: 10 }}>{r.risk_level}</span>
                      {r.matched_skills.slice(0, 2).map(s => <span key={s} className="chip-match" style={{ fontSize: 9 }}>{s}</span>)}
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div style={{ padding: "32px 12px", textAlign: "center" }}>
                <div style={{ fontSize: 32, marginBottom: 10, opacity: 0.2 }}>💬</div>
                <p style={{ color: "var(--text-3)", fontSize: 12 }}>
                  Referenced candidates will appear here after asking a question.
                </p>
              </div>
            )}
          </AnimatePresence>
        </div>

        {/* Roster mini-list */}
        <div style={{ borderTop: "1px solid var(--border)", padding: "12px 14px" }}>
          <div className="label-xs" style={{ marginBottom: 8 }}>All Candidates ({results.length})</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 200, overflowY: "auto" }}>
            {results.map(r => (
              <div key={r.candidate_id} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                <div style={{ width: 5, height: 5, borderRadius: "50%", background: getScoreColor(r.scores.overall_score), flexShrink: 0 }} />
                <span style={{ fontSize: 11, color: "var(--text-2)", flex: 1 }}>{r.candidate_name}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: getScoreColor(r.scores.overall_score) }}>
                  {Math.round(r.scores.overall_score)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
