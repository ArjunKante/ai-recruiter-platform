import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { X } from "lucide-react";
import type { RankingResult } from "../../types";
import { Avatar, ScoreRing, ProgressBar, SectionLabel, Card, getScoreColor, getRiskClass, getRecColor } from "../ui";
import { SCORE_LABELS } from "../../lib/utils";

const TABS = ["Overview","Skills","AI Analysis","Weights"] as const;
type Tab = typeof TABS[number];

export const CandidateDetail: React.FC<{ result: RankingResult|null; onClose:()=>void }> = ({ result, onClose }) => {
  const [tab, setTab] = useState<Tab>("Overview");

  if (!result) return null;

  const radar = Object.entries(SCORE_LABELS).map(([key, label]) => ({
    subject: label, value: Math.round((result.scores as any)[key] ?? 0),
  }));

  const bars = Object.entries(SCORE_LABELS).map(([key, label]) => ({
    name: label, value: Math.round((result.scores as any)[key] ?? 0), color: getScoreColor(Math.round((result.scores as any)[key] ?? 0)),
  }));

  return (
    <AnimatePresence>
      <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
        <motion.div
          initial={{ scale:0.95, y:12, opacity:0 }}
          animate={{ scale:1, y:0, opacity:1 }}
          exit={{ scale:0.95, y:12, opacity:0 }}
          transition={{ duration:0.25, ease:[0.34,1.2,0.64,1] }}
          style={{
            width:"92%", maxWidth:860, maxHeight:"90vh", display:"flex", flexDirection:"column",
            background:"#0a0a1a", border:"1px solid var(--border-strong)", borderRadius:20,
            boxShadow:"0 40px 100px rgba(0,0,0,0.8)", overflow:"hidden", position:"relative",
          }}
        >
          {/* Top gradient stripe */}
          <div style={{ height:3, background:"linear-gradient(90deg,#7c3aed,#06b6d4,#10b981)", flexShrink:0 }} />

          {/* Header */}
          <div style={{ display:"flex", alignItems:"center", gap:16, padding:"20px 28px", borderBottom:"1px solid var(--border)" }}>
            <Avatar name={result.candidate_name} size={52} />
            <div style={{ flex:1 }}>
              <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:4 }}>
                <h2 style={{ fontSize:20, fontWeight:900, letterSpacing:"-0.4px" }}>{result.candidate_name}</h2>
                {result.rank_position && result.rank_position <= 3 && <span className="badge badge-green">🏆 Top #{result.rank_position}</span>}
                {result.is_duplicate_of_candidate_id && <span className="badge badge-amber">⚠ Possible Duplicate</span>}
              </div>
              <p style={{ color:"var(--text-3)", fontSize:13 }}>{result.candidate_title} · {result.candidate_company}</p>
            </div>
            <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:6 }}>
              <ScoreRing value={Math.round(result.scores.overall_score)} size={64} stroke={5} label="overall" />
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:6, marginLeft:8 }}>
              <span className={`badge ${getRiskClass(result.risk_level)}`}>{result.risk_level} Risk</span>
              <span className="badge badge-slate">{Math.round(result.confidence_score)}% · {result.confidence_band}</span>
            </div>
            <button onClick={onClose} className="btn-icon" style={{ flexShrink:0 }}><X size={15} /></button>
          </div>

          {/* Recommendation banner */}
          <div style={{
            padding:"10px 28px", background:`${getRecColor(result.recommendation)}12`,
            borderBottom:`1px solid ${getRecColor(result.recommendation)}25`,
            display:"flex", alignItems:"center", gap:12,
          }}>
            <div style={{ width:8, height:8, borderRadius:"50%", background:getRecColor(result.recommendation), flexShrink:0, boxShadow:`0 0 8px ${getRecColor(result.recommendation)}` }} />
            <span style={{ fontSize:13, fontWeight:700, color:getRecColor(result.recommendation) }}>{result.recommendation}</span>
            {result.risk_reasons?.[0] && (
              <span style={{ fontSize:12, color:"var(--text-3)", marginLeft:8 }}>· {result.risk_reasons[0]}</span>
            )}
          </div>

          {/* Tabs */}
          <div style={{ display:"flex", gap:2, padding:"12px 24px 0", borderBottom:"1px solid var(--border)" }}>
            {TABS.map(t => (
              <button key={t} onClick={() => setTab(t)} style={{
                padding:"8px 16px", borderRadius:"9px 9px 0 0", border:"none", cursor:"pointer", fontSize:12, fontWeight:700,
                background: tab===t ? "rgba(255,255,255,0.06)" : "transparent",
                color: tab===t ? "var(--text-1)" : "var(--text-3)",
                borderBottom: tab===t ? "2px solid #7c3aed" : "2px solid transparent",
                transition:"all 0.15s ease",
              }}>{t}</button>
            ))}
          </div>

          {/* Content */}
          <div style={{ flex:1, overflowY:"auto", padding:"24px 28px" }}>
            {tab==="Overview" && (
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:24 }}>
                <div>
                  <SectionLabel>Score Radar</SectionLabel>
                  <ResponsiveContainer width="100%" height={210}>
                    <RadarChart data={radar}>
                      <PolarGrid stroke="rgba(255,255,255,0.06)" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill:"var(--text-3)", fontSize:11 }} />
                      <PolarRadiusAxis tick={false} axisLine={false} domain={[0,100]} />
                      <Radar dataKey="value" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.18} strokeWidth={2.5} dot={{ fill:"#7c3aed", r:3 }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <SectionLabel>Score Breakdown</SectionLabel>
                  <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
                    {Object.entries(SCORE_LABELS).map(([key, label]) => {
                      const val = Math.round((result.scores as any)[key] ?? 0);
                      const col = getScoreColor(val);
                      return (
                        <div key={key}>
                          <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                            <span style={{ fontSize:12, color:"var(--text-2)", fontWeight:600 }}>{label}</span>
                            <span style={{ fontSize:12, fontWeight:800, color:col }}>{val}</span>
                          </div>
                          <ProgressBar value={val} color={col} height={5} glow />
                        </div>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <SectionLabel>Strengths</SectionLabel>
                  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                    {(result.strengths??[]).map((s,i) => (
                      <div key={i} style={{ display:"flex", gap:8, fontSize:13, color:"var(--text-1)", lineHeight:1.55 }}>
                        <span style={{ color:"#10b981", flexShrink:0, marginTop:2 }}>✓</span>{s}
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <SectionLabel>Concerns</SectionLabel>
                  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                    {(result.weaknesses??[]).map((w,i) => (
                      <div key={i} style={{ display:"flex", gap:8, fontSize:13, color:"var(--text-1)", lineHeight:1.55 }}>
                        <span style={{ color:"#f59e0b", flexShrink:0, marginTop:2 }}>⚠</span>{w}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {tab==="Skills" && (
              <div style={{ display:"flex", flexDirection:"column", gap:24 }}>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:20 }}>
                  <div>
                    <SectionLabel>Matched Skills ({result.matched_skills.length})</SectionLabel>
                    <div style={{ display:"flex", flexWrap:"wrap", gap:7 }}>
                      {result.matched_skills.map(s => <span key={s} className="chip-match" style={{ padding:"5px 10px" }}>✓ {s}</span>)}
                      {result.matched_skills.length===0 && <p style={{ color:"var(--text-3)", fontSize:13 }}>None detected</p>}
                    </div>
                  </div>
                  <div>
                    <SectionLabel>Missing Skills ({result.missing_skills.length})</SectionLabel>
                    {result.missing_skills.length > 0
                      ? <div style={{ display:"flex", flexWrap:"wrap", gap:7 }}>{result.missing_skills.map(s=><span key={s} className="chip-miss" style={{ padding:"5px 10px" }}>✕ {s}</span>)}</div>
                      : <p style={{ color:"#10b981", fontSize:13, fontWeight:700 }}>✓ No critical skill gaps</p>
                    }
                  </div>
                </div>
                <div style={{ background:"rgba(124,58,237,0.05)", border:"1px solid rgba(124,58,237,0.2)", borderRadius:12, padding:18 }}>
                  <SectionLabel style={{ color:"#a78bfa" }}>💡 Counterfactual Recommendation</SectionLabel>
                  <p style={{ color:"var(--text-1)", fontSize:13, lineHeight:1.75 }}>{result.counterfactual_text ?? "Not available."}</p>
                </div>
                <div>
                  <SectionLabel>Skill Coverage Bar</SectionLabel>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={bars} margin={{ top:0, right:0, left:-20, bottom:0 }} layout="vertical">
                      <XAxis type="number" domain={[0,100]} tick={{ fill:"var(--text-3)", fontSize:10 }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="name" tick={{ fill:"var(--text-2)", fontSize:11 }} axisLine={false} tickLine={false} width={90} />
                      <Tooltip cursor={false} contentStyle={{ background:"#0d0d20", border:"1px solid var(--border)", borderRadius:8, fontSize:12 }} />
                      <Bar dataKey="value" radius={[0,4,4,0]}>
                        {bars.map((b,i) => <Cell key={i} fill={b.color} fillOpacity={0.8} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {tab==="AI Analysis" && (
              <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
                <div style={{ background:"var(--bg-surface-2)", border:"1px solid var(--border)", borderRadius:14, padding:20 }}>
                  <SectionLabel>AI Recruiter Reasoning</SectionLabel>
                  <p style={{ color:"var(--text-1)", fontSize:14, lineHeight:1.85 }}>{result.reasoning_text ?? "Reasoning not available."}</p>
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
                  <div style={{ background:"var(--bg-surface)", border:`2px solid ${getRecColor(result.recommendation)}30`, borderRadius:12, padding:16 }}>
                    <SectionLabel>Recommendation</SectionLabel>
                    <div style={{ fontSize:14, fontWeight:800, color:getRecColor(result.recommendation), marginBottom:10 }}>{result.recommendation}</div>
                    <div style={{ height:3, background:getRecColor(result.recommendation), borderRadius:99, opacity:0.5 }} />
                  </div>
                  <div style={{ background:"var(--bg-surface)", border:"1px solid var(--border)", borderRadius:12, padding:16 }}>
                    <SectionLabel>Confidence</SectionLabel>
                    <div style={{ fontSize:30, fontWeight:900, color:getScoreColor(result.confidence_score), marginBottom:10, fontVariantNumeric:"tabular-nums" }}>
                      {Math.round(result.confidence_score)}%
                    </div>
                    <ProgressBar value={result.confidence_score} color={getScoreColor(result.confidence_score)} glow />
                    <p style={{ fontSize:11, color:"var(--text-3)", marginTop:6 }}>{result.confidence_band} confidence</p>
                  </div>
                </div>
                {(result.risk_reasons?.length??0) > 0 && (
                  <div style={{ background:"rgba(245,158,11,0.05)", border:"1px solid rgba(245,158,11,0.2)", borderRadius:12, padding:16 }}>
                    <SectionLabel style={{ color:"#f59e0b" }}>Hiring Risk Factors</SectionLabel>
                    {result.risk_reasons.map((r,i) => (
                      <div key={i} style={{ display:"flex", gap:8, fontSize:13, color:"var(--text-1)", marginBottom:8, lineHeight:1.55 }}>
                        <span style={{ color:"#f59e0b", flexShrink:0 }}>→</span>{r}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {tab==="Weights" && (
              <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
                <div style={{ background:"rgba(124,58,237,0.05)", border:"1px solid rgba(124,58,237,0.2)", borderRadius:12, padding:18 }}>
                  <SectionLabel style={{ color:"#a78bfa" }}>Active Weight Profile</SectionLabel>
                  <span className="badge badge-violet" style={{ fontSize:12, marginBottom:10, display:"inline-block" }}>{result.weight_profile_used.replace(/_/g," ")}</span>
                  <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:10, marginTop:16 }}>
                    {Object.entries(result.weights_applied??{}).map(([k,v]) => (
                      <div key={k} style={{ textAlign:"center", padding:"12px 8px", background:"rgba(255,255,255,0.03)", borderRadius:10 }}>
                        <div style={{ fontSize:22, fontWeight:900, color:"#a78bfa" }}>{v}%</div>
                        <div style={{ fontSize:10, color:"var(--text-3)", marginTop:4, fontWeight:600 }}>{SCORE_LABELS[k]??k}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <SectionLabel>Weight Distribution</SectionLabel>
                  <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
                    {Object.entries(result.weights_applied??{}).map(([k,v]) => (
                      <div key={k} style={{ display:"flex", alignItems:"center", gap:12 }}>
                        <span style={{ fontSize:12, color:"var(--text-2)", width:110, flexShrink:0 }}>{SCORE_LABELS[k]??k}</span>
                        <div style={{ flex:1, height:6, background:"rgba(255,255,255,0.05)", borderRadius:99, overflow:"hidden" }}>
                          <div style={{ height:"100%", width:`${v}%`, background:"linear-gradient(90deg,#7c3aed,#a78bfa)", borderRadius:99 }} />
                        </div>
                        <span style={{ fontSize:12, fontWeight:800, color:"#a78bfa", width:32, textAlign:"right" }}>{v}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
