import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, FileText, Upload, Sparkles, ArrowRight, Zap, Brain, Shield, BarChart3 } from "lucide-react";
import { jobsApi, candidatesApi } from "../api/client";
import type { JobDescription } from "../types";
import { useAppStore } from "../lib/store";
import { Spinner } from "../components/ui";

const SAMPLE_JD = `Senior Backend Engineer — Payments Infrastructure

We are scaling our core payments infrastructure and need an exceptional Senior Backend Engineer.

REQUIRED SKILLS:
• 5+ years backend engineering experience in production environments
• Python or Node.js (Python strongly preferred)
• PostgreSQL — schema design, query optimization, replication
• Docker and Kubernetes — container orchestration at scale
• AWS cloud infrastructure (ECS/EKS, RDS, ElastiCache, S3)
• REST API design and microservices architecture
• Redis for caching, rate limiting, and session management

NICE TO HAVE:
• GraphQL and/or gRPC service-to-service communication
• Apache Kafka or message queue/event streaming experience
• CI/CD pipeline ownership (GitHub Actions, ArgoCD)
• Experience mentoring engineers or leading technical initiatives
• Open source contributions

ROLE: Remote (US timezones) | $180K–$220K | 30-day notice preferred`;

const FEATURES = [
  { icon: Brain,    color: "#7c3aed", label: "Semantic Matching",     desc: "Understands skill aliases, not just keywords" },
  { icon: BarChart3,color: "#06b6d4", label: "Career Intelligence",   desc: "Tenure, promotions, trajectory analysis" },
  { icon: Shield,   color: "#10b981", label: "Trust Engine",          desc: "Fraud detection & contradiction analysis" },
  { icon: Zap,      color: "#f59e0b", label: "Dynamic Weights",       desc: "Auto-adjusts scoring by role type" },
];

const STEPS = ["Define Role", "Upload Resumes", "AI Analysis"];

export const LandingPage: React.FC<{ onAnalysisReady: () => void }> = ({ onAnalysisReady }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [jdTitle, setJdTitle]       = useState("Senior Backend Engineer");
  const [jdText,  setJdText]        = useState("");
  const [files,   setFiles]         = useState<File[]>([]);
  const [jd,      setJd]            = useState<JobDescription | null>(null);
  const [status,  setStatus]        = useState<"idle"|"saving"|"uploading"|"ready">("idle");
  const [error,   setError]         = useState<string|null>(null);
  const { setActiveJd, setCandidateCount } = useAppStore();

  const onDrop = useCallback((dropped: File[]) => { setFiles(p => [...p, ...dropped]); }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "application/pdf": [], "text/plain": [], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [] }, multiple: true,
  });

  const handleSaveJD = async () => {
    if (!jdText.trim() || jdText.length < 50) return;
    setStatus("saving"); setError(null);
    try {
      const res = await jobsApi.create(jdTitle.trim() || "Job Description", jdText);
      setJd(res.data); setActiveJd(res.data); setStatus("ready"); setActiveStep(1);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to parse JD"); setStatus("idle");
    }
  };

  const handleAnalyze = async () => {
    if (!jd) return;
    setStatus("uploading"); setError(null);
    try {
      const uploaded = await candidatesApi.upload(jd.id, files);
      setCandidateCount(uploaded.data.length);
      setActiveStep(2);
      onAnalysisReady();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Upload failed"); setStatus("ready");
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", position: "relative", overflow: "hidden" }}>
      {/* Grid background */}
      <div className="bg-grid" style={{ position: "absolute", inset: 0, opacity: 0.4, pointerEvents: "none" }} />
      {/* Ambient orbs */}
      <div style={{ position:"absolute", top:"10%", left:"10%", width:600, height:600, borderRadius:"50%", background:"radial-gradient(circle, rgba(124,58,237,0.08) 0%, transparent 70%)", animation:"orbMove 12s ease-in-out infinite", pointerEvents:"none" }} />
      <div style={{ position:"absolute", bottom:"15%", right:"5%", width:450, height:450, borderRadius:"50%", background:"radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%)", animation:"orbMove 15s ease-in-out infinite reverse", pointerEvents:"none" }} />

      {/* Header bar */}
      <header style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"16px 32px", borderBottom:"1px solid var(--border)", background:"rgba(5,5,15,0.7)", backdropFilter:"blur(20px)", position:"relative", zIndex:10 }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:36, height:36, borderRadius:11, background:"linear-gradient(135deg,#7c3aed,#06b6d4)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, boxShadow:"0 0 20px rgba(124,58,237,0.4)" }}>🧠</div>
          <div>
            <div style={{ fontWeight:900, fontSize:17, letterSpacing:"-0.3px" }}>TalentAI</div>
            <div className="label-xs" style={{ marginBottom:0 }}>AI Recruiter Platform</div>
          </div>
        </div>
        <div style={{ display:"flex", gap:6 }}>
          {["Semantic AI", "6 Score Dimensions", "Real-time Ranking"].map(t => (
            <span key={t} className="badge badge-slate">{t}</span>
          ))}
        </div>
      </header>

      <main style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:"48px 24px", position:"relative", zIndex:1 }}>
        {/* Hero */}
        <motion.div initial={{ opacity:0, y:-20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.6 }} style={{ textAlign:"center", marginBottom:48 }}>
          <div style={{ display:"inline-flex", alignItems:"center", gap:8, padding:"6px 14px", borderRadius:99, background:"rgba(124,58,237,0.1)", border:"1px solid rgba(124,58,237,0.25)", marginBottom:20 }}>
            <span style={{ fontSize:11 }}>✨</span>
            <span style={{ fontSize:12, fontWeight:700, color:"#a78bfa" }}>Powered by Claude AI · Not keyword matching</span>
          </div>
          <h1 className="display-xl" style={{ marginBottom:16 }}>
            Rank Candidates Like a<br />
            <span className="gradient-text">Seasoned Recruiter</span>
          </h1>
          <p style={{ color:"var(--text-2)", fontSize:17, maxWidth:520, margin:"0 auto" }}>
            Upload a job description + resumes. Get ranked candidates with AI reasoning, risk scores, skill gaps, and counterfactual recommendations.
          </p>
        </motion.div>

        {/* Step indicators */}
        <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:0.2 }} style={{ display:"flex", alignItems:"center", gap:0, marginBottom:36 }}>
          {STEPS.map((s, i) => (
            <React.Fragment key={s}>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <div style={{
                  width:28, height:28, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center",
                  fontSize:12, fontWeight:800,
                  background: i < activeStep ? "#10b981" : i === activeStep ? "#7c3aed" : "rgba(255,255,255,0.06)",
                  color: i <= activeStep ? "#fff" : "var(--text-3)",
                  border: i === activeStep ? "2px solid rgba(124,58,237,0.5)" : "none",
                  boxShadow: i === activeStep ? "0 0 16px rgba(124,58,237,0.4)" : "none",
                  transition: "all 0.4s ease",
                }}>
                  {i < activeStep ? "✓" : i + 1}
                </div>
                <span style={{ fontSize:13, fontWeight: i === activeStep ? 700 : 500, color: i === activeStep ? "var(--text-1)" : "var(--text-3)" }}>{s}</span>
              </div>
              {i < STEPS.length - 1 && <div style={{ width:48, height:1, background: i < activeStep ? "rgba(16,185,129,0.4)" : "var(--border)", margin:"0 12px" }} />}
            </React.Fragment>
          ))}
        </motion.div>

        {/* Setup panels */}
        <motion.div
          initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.3 }}
          style={{ width:"100%", maxWidth:900, display:"grid", gridTemplateColumns:"1fr 1fr", gap:20, marginBottom:24 }}
        >
          {/* JD Panel */}
          <div className="glass" style={{ padding:24, display:"flex", flexDirection:"column", gap:16 }}>
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <FileText size={14} style={{ color:"#a78bfa" }} />
                <span className="label-xs" style={{ marginBottom:0 }}>Step 1 — Job Description</span>
              </div>
              <div style={{ display:"flex", gap:6 }}>
                {jd && <span className="badge badge-green">✓ Parsed</span>}
                <button onClick={() => { setJdText(SAMPLE_JD); setJd(null); setStatus("idle"); }} style={{ fontSize:12, fontWeight:700, color:"#a78bfa", background:"none", border:"none", cursor:"pointer" }}>
                  Sample
                </button>
              </div>
            </div>

            <input
              className="input"
              value={jdTitle}
              onChange={e => { setJdTitle(e.target.value); setJd(null); setStatus("idle"); }}
              placeholder="Job title (e.g. Senior Backend Engineer)"
              style={{ fontSize:14, fontWeight:600 }}
            />
            <textarea
              className="input"
              value={jdText}
              onChange={e => { setJdText(e.target.value); setJd(null); setStatus("idle"); }}
              placeholder={"Paste your job description here...\n\nInclude:\n• Required skills with levels\n• Experience requirements\n• Location / remote policy\n• Salary range"}
              style={{ minHeight:210, resize:"none", lineHeight:1.65, fontSize:13 }}
            />
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              {jdText && !jd && <span style={{ fontSize:11, color:"var(--text-3)" }}>{jdText.split(" ").length} words</span>}
              {jd && (
                <div style={{ display:"flex", gap:6, flex:1, flexWrap:"wrap" }}>
                  <span className="badge badge-green">{jd.must_have_skills?.length ?? 0} required skills</span>
                  {jd.domain && <span className="badge badge-violet">{jd.domain}</span>}
                  {jd.remote_policy && <span className="badge badge-cyan">{jd.remote_policy}</span>}
                </div>
              )}
              <button
                onClick={handleSaveJD}
                disabled={jdText.length < 50 || status === "saving" || !!jd}
                className="btn-primary"
                style={{ marginLeft:"auto", padding:"9px 18px", fontSize:13, flexShrink:0 }}
              >
                {status === "saving" ? <Spinner size={13} /> : jd ? <><CheckCircle size={13} />Saved</> : <>Parse JD <ArrowRight size={12} /></>}
              </button>
            </div>
          </div>

          {/* Resume Panel */}
          <div className="glass" style={{ padding:24, display:"flex", flexDirection:"column", gap:16 }}>
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <Upload size={14} style={{ color:"#22d3ee" }} />
                <span className="label-xs" style={{ marginBottom:0 }}>Step 2 — Candidate Profiles</span>
              </div>
              {files.length > 0 && <span className="badge badge-cyan">{files.length} loaded</span>}
            </div>

            <div {...getRootProps()} style={{
              border:`2px dashed ${isDragActive ? "rgba(124,58,237,0.6)" : "var(--border)"}`,
              borderRadius:12, padding:"28px 20px", textAlign:"center", cursor:"pointer",
              background: isDragActive ? "rgba(124,58,237,0.06)" : "transparent",
              transition:"all 0.2s ease",
            }}
            onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(124,58,237,0.4)"}
            onMouseLeave={e => { if (!isDragActive) e.currentTarget.style.borderColor = "var(--border)"; }}
            >
              <input {...getInputProps()} />
              <div style={{ fontSize:36, marginBottom:8 }}>📂</div>
              <p style={{ color:"var(--text-2)", fontSize:13, fontWeight:600, marginBottom:4 }}>Drop resumes here or click to upload</p>
              <p style={{ color:"var(--text-3)", fontSize:11 }}>PDF, DOCX, TXT supported · Batch upload</p>
            </div>

            {files.length > 0 ? (
              <div style={{ flex:1, display:"flex", flexDirection:"column", gap:6, maxHeight:180, overflowY:"auto" }}>
                {files.map((f, i) => (
                  <div key={i} style={{ display:"flex", alignItems:"center", gap:10, padding:"8px 12px", background:"rgba(16,185,129,0.05)", border:"1px solid rgba(16,185,129,0.15)", borderRadius:8 }}>
                    <span style={{ fontSize:14 }}>📄</span>
                    <span style={{ color:"var(--text-1)", fontSize:12, flex:1, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{f.name}</span>
                    <span style={{ fontSize:10, color:"var(--text-3)", flexShrink:0 }}>{(f.size/1024).toFixed(0)}KB</span>
                    <button onClick={e => { e.stopPropagation(); setFiles(p => p.filter((_,j) => j !== i)); }} style={{ background:"none", border:"none", color:"var(--text-3)", cursor:"pointer", fontSize:14, lineHeight:1, padding:0 }}>×</button>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ flex:1, padding:"12px 16px", background:"rgba(255,255,255,0.02)", border:"1px solid var(--border)", borderRadius:10 }}>
                <p style={{ color:"var(--text-3)", fontSize:12, fontWeight:600, marginBottom:6 }}>No files yet?</p>
                <p style={{ color:"var(--text-4)", fontSize:11, lineHeight:1.7 }}>
                  The seed script loads 6 pre-built sample candidates (Staff @ Stripe, Principal @ Amazon, Senior @ Uber, etc.) automatically. Run <code style={{ color:"#a78bfa" }}>python seed.py</code> first.
                </p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div initial={{ opacity:0, y:-8 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0 }}
              style={{ marginBottom:16, padding:"10px 18px", background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.25)", borderRadius:10, color:"#f87171", fontSize:13, fontWeight:600 }}>
              ⚠ {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* CTA */}
        <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:0.5 }}>
          <button
            onClick={handleAnalyze}
            disabled={!jd || files.length === 0 || status === "uploading"}
            className="btn-primary"
            style={{ fontSize:15, padding:"14px 36px", borderRadius:14 }}
          >
            {status === "uploading" ? (
              <><Spinner size={16} /> Uploading {files.length} resumes…</>
            ) : jd && files.length > 0 ? (
              <><Sparkles size={16} /> Analyze {files.length} Candidates with Claude AI</>
            ) : (
              "↑ Complete steps above to analyze"
            )}
          </button>
        </motion.div>

        {/* Feature cards */}
        <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:0.7 }}
          style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14, width:"100%", maxWidth:900, marginTop:48 }}>
          {FEATURES.map(({ icon: Icon, color, label, desc }) => (
            <div key={label} className="glass" style={{ padding:"16px 18px", textAlign:"center" }}>
              <div style={{ width:40, height:40, borderRadius:11, background:`${color}18`, border:`1px solid ${color}30`, display:"flex", alignItems:"center", justifyContent:"center", margin:"0 auto 12px" }}>
                <Icon size={18} style={{ color }} />
              </div>
              <div style={{ fontWeight:700, fontSize:13, marginBottom:4 }}>{label}</div>
              <div style={{ color:"var(--text-3)", fontSize:11, lineHeight:1.5 }}>{desc}</div>
            </div>
          ))}
        </motion.div>
      </main>
    </div>
  );
};
