import React, { useState, useEffect, createContext, useContext } from "react";
import { Radar, Doughnut, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, RadialLinearScale, PointElement, LineElement,
  BarElement, ArcElement, CategoryScale, LinearScale,
  Title, Tooltip, Legend, Filler
} from "chart.js";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import { Brain, TrendingUp, Users, Award, LogOut } from "lucide-react";

ChartJS.register(
  RadialLinearScale, PointElement, LineElement, BarElement,
  ArcElement, CategoryScale, LinearScale, Title, Tooltip, Legend, Filler
);

const API = axios.create({ baseURL: "/api/v1" });
API.interceptors.request.use(cfg => {
  const token = localStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

const TRAIT_COLORS = {
  openness:          { bg: "#0ea5e9", light: "rgba(14,165,233,0.12)" },
  conscientiousness: { bg: "#10b981", light: "rgba(16,185,129,0.12)" },
  extraversion:      { bg: "#f59e0b", light: "rgba(245,158,11,0.12)"  },
  agreeableness:     { bg: "#8b5cf6", light: "rgba(139,92,246,0.12)" },
  neuroticism:       { bg: "#ef4444", light: "rgba(239,68,68,0.12)"  },
};

const TRAIT_LABELS = {
  openness: "Openness", conscientiousness: "Conscientiousness",
  extraversion: "Extraversion", agreeableness: "Agreeableness", neuroticism: "Neuroticism"
};

// ── Auth Context ──────────────────────────────────────────────────────────────
const AuthCtx = createContext(null);
function useAuth() { return useContext(AuthCtx); }

function AuthProvider({ children }) {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("user") || "null"));

  const login = async (email, password) => {
    const r = await API.post("/auth/login", { email, password });
    localStorage.setItem("token", r.data.token);
    localStorage.setItem("user",  JSON.stringify(r.data.user));
    setUser(r.data.user);
  };

  const register = async (email, password, fullName, role, department) => {
    const r = await API.post("/auth/register", { email, password, fullName, role, department });
    localStorage.setItem("token", r.data.token);
    localStorage.setItem("user",  JSON.stringify(r.data.user));
    setUser(r.data.user);
  };

  const logout = () => { localStorage.clear(); setUser(null); };
  return <AuthCtx.Provider value={{ user, login, register, logout }}>{children}</AuthCtx.Provider>;
}

// ── Login ─────────────────────────────────────────────────────────────────────
function Field({ label, type, value, onChange }) {
  return (
    <div style={{ marginBottom: "14px" }}>
      <label style={labelStyle}>{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} style={inputStyle} required />
    </div>
  );
}

function LoginPage() {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", fullName: "", role: "individual", department: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isRegister) await register(form.email, form.password, form.fullName, form.role, form.department);
      else await login(form.email, form.password);
      toast.success(isRegister ? "Account created!" : "Welcome back!");
    } catch (err) {
      toast.error(err.response?.data?.error || "Authentication failed");
    } finally { setLoading(false); }
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: "#f1f5f9" }}>
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "40px", width: "400px", boxShadow: "0 4px 24px rgba(0,0,0,0.08)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
          <Brain size={28} color="#0ea5e9" />
          <h1 style={{ color: "#0ea5e9", fontSize: "22px", fontWeight: 700 }}>Traitlytics</h1>
        </div>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginBottom: "28px" }}>Big Five Personality Analytics Platform</p>
        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <Field label="Full Name" type="text" value={form.fullName} onChange={v => setForm({ ...form, fullName: v })} />
              <div style={{ marginBottom: "14px" }}>
                <label style={labelStyle}>Role</label>
                <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} style={inputStyle}>
                  <option value="individual">Individual</option>
                  <option value="manager">Manager</option>
                </select>
              </div>
              <Field label="Department (optional)" type="text" value={form.department} onChange={v => setForm({ ...form, department: v })} />
            </>
          )}
          <Field label="Email" type="email" value={form.email} onChange={v => setForm({ ...form, email: v })} />
          <Field label="Password" type="password" value={form.password} onChange={v => setForm({ ...form, password: v })} />
          <button type="submit" disabled={loading} style={{ width: "100%", padding: "12px", background: "#0ea5e9", color: "#fff", border: "none", borderRadius: "8px", fontWeight: 700, cursor: "pointer", marginTop: "8px", fontSize: "14px" }}>
            {loading ? "..." : isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>
        <p style={{ textAlign: "center", color: "#94a3b8", fontSize: "13px", marginTop: "16px" }}>
          {isRegister ? "Already have an account? " : "New to Traitlytics? "}
          <span style={{ color: "#0ea5e9", cursor: "pointer", fontWeight: 600 }} onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? "Sign In" : "Register"}
          </span>
        </p>
      </div>
    </div>
  );
}

// ── Assessment ────────────────────────────────────────────────────────────────
function AssessmentPage({ onComplete }) {
  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState({});
  const [current, setCurrent]     = useState(0);
  const [loading, setLoading]     = useState(false);
  const ITEMS_PER_PAGE = 5;

  useEffect(() => { API.get("/assessment/questions").then(r => setQuestions(r.data)); }, []);

  const pageQuestions = questions.slice(current * ITEMS_PER_PAGE, (current + 1) * ITEMS_PER_PAGE);
  const totalPages    = Math.ceil(questions.length / ITEMS_PER_PAGE);
  const progress      = (Object.keys(responses).length / 50) * 100;

  const handleSubmit = async () => {
    if (Object.keys(responses).length < 50) { toast.error("Please answer all questions"); return; }
    setLoading(true);
    try {
      const r = await API.post("/assessment/submit", { responses });
      toast.success("Assessment complete!");
      onComplete(r.data);
    } catch { toast.error("Submission failed"); }
    finally { setLoading(false); }
  };

  const SCALE = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"];

  return (
    <div style={{ maxWidth: "700px", margin: "0 auto", padding: "24px" }}>
      <h1 style={{ color: "#0f172a", fontSize: "22px", marginBottom: "8px" }}>Big Five Personality Assessment</h1>
      <p style={{ color: "#64748b", fontSize: "13px", marginBottom: "12px" }}>50 questions · ~10 minutes · Based on IPIP Big Five model</p>
      <div style={{ background: "#e2e8f0", borderRadius: "4px", height: "6px", marginBottom: "4px" }}>
        <div style={{ background: "#0ea5e9", height: "100%", width: `${progress}%`, borderRadius: "4px", transition: "width 0.3s" }} />
      </div>
      <p style={{ color: "#64748b", fontSize: "12px", marginBottom: "20px" }}>{Object.keys(responses).length}/50 answered</p>

      {pageQuestions.map(q => (
        <div key={q.id} style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "20px", marginBottom: "12px", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <p style={{ color: "#0f172a", fontSize: "15px", marginBottom: "16px" }}>
            <span style={{ color: "#0ea5e9", fontWeight: 700 }}>Q{q.id}.</span> {q.text}
          </p>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {[1, 2, 3, 4, 5].map(val => (
              <button key={val} onClick={() => setResponses({ ...responses, [q.id]: val })}
                style={{ flex: 1, minWidth: "80px", padding: "8px 4px", borderRadius: "8px",
                  border: responses[q.id] === val ? "2px solid #0ea5e9" : "1px solid #e2e8f0",
                  background: responses[q.id] === val ? "#e0f2fe" : "#f8fafc",
                  color: responses[q.id] === val ? "#0ea5e9" : "#64748b",
                  cursor: "pointer", fontSize: "11px", fontWeight: responses[q.id] === val ? 700 : 400 }}>
                {val}<br /><span style={{ fontSize: "9px" }}>{SCALE[val - 1]}</span>
              </button>
            ))}
          </div>
        </div>
      ))}

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "20px" }}>
        <button onClick={() => setCurrent(c => Math.max(0, c - 1))} disabled={current === 0} style={navBtnStyle}>← Previous</button>
        <span style={{ color: "#64748b", alignSelf: "center" }}>Page {current + 1} of {totalPages}</span>
        {current < totalPages - 1
          ? <button onClick={() => setCurrent(c => c + 1)} style={{ ...navBtnStyle, background: "#0ea5e9", color: "#fff", border: "none" }}>Next →</button>
          : <button onClick={handleSubmit} disabled={loading} style={{ ...navBtnStyle, background: "#10b981", color: "#fff", border: "none" }}>
              {loading ? "Analyzing..." : "Submit ✓"}
            </button>
        }
      </div>
    </div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function Dashboard() {
  const { user, logout } = useAuth();
  const [profile,    setProfile]    = useState(null);
  const [history,    setHistory]    = useState(null);
  const [population, setPopulation] = useState(null);
  const [dominants,  setDominants]  = useState([]);
  const [showAssess, setShowAssess] = useState(false);
  const [loading,    setLoading]    = useState(true);
  const [activeTab,  setActiveTab]  = useState("profile");

  const loadData = async () => {
    setLoading(true);
    try {
      const [prof, hist, pop, dom] = await Promise.all([
        API.get("/profile").catch(() => null),
        API.get("/profile/history").catch(() => null),
        API.get("/analytics/population").catch(() => null),
        API.get("/analytics/dominant-traits").catch(() => null),
      ]);
      if (prof) setProfile(prof.data);
      if (hist) setHistory(hist.data);
      if (pop)  setPopulation(pop.data);
      if (dom)  setDominants(dom.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  if (showAssess) return <AssessmentPage onComplete={result => { setProfile(result); setShowAssess(false); loadData(); }} />;

  const TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"];

  const radarData = profile ? {
    labels: TRAITS.map(t => TRAIT_LABELS[t]),
    datasets: [{ label: "Your Score", data: TRAITS.map(t => profile[t]),
      backgroundColor: "rgba(14,165,233,0.12)", borderColor: "#0ea5e9",
      pointBackgroundColor: "#0ea5e9", borderWidth: 2 }],
  } : null;

  const historyData = history?.history?.length > 1 ? {
    labels: history.history.map(h => new Date(h.date).toLocaleDateString()),
    datasets: TRAITS.map(trait => ({
      label: TRAIT_LABELS[trait], data: history.history.map(h => h[trait]),
      borderColor: TRAIT_COLORS[trait].bg, backgroundColor: TRAIT_COLORS[trait].light,
      fill: false, tension: 0.4,
    })),
  } : null;

  const dominantData = dominants.length > 0 ? {
    labels: dominants.map(d => TRAIT_LABELS[d.trait] || d.trait),
    datasets: [{ data: dominants.map(d => d.count),
      backgroundColor: dominants.map(d => TRAIT_COLORS[d.trait]?.bg || "#94a3b8"), borderWidth: 0 }],
  } : null;

  return (
    <div style={{ fontFamily: "sans-serif", background: "#f1f5f9", minHeight: "100vh" }}>
      {/* Navbar */}
      <nav style={{ background: "#ffffff", borderBottom: "1px solid #e2e8f0", padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Brain size={22} color="#0ea5e9" />
          <span style={{ color: "#0ea5e9", fontWeight: 700, fontSize: "18px" }}>Traitlytics</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ color: "#64748b", fontSize: "13px" }}>
            {user?.full_name} · <span style={{ color: "#0ea5e9", fontWeight: 600 }}>{user?.role}</span>
          </span>
          {profile && (
            <button onClick={async () => {
              try {
                const r = await API.get("/profile/export/pdf", { responseType: "blob" });
                const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
                const a = document.createElement("a"); a.href = url; a.download = "traitlytics_report.pdf"; a.click();
                toast.success("PDF downloaded!");
              } catch { toast.error("PDF export failed"); }
            }} style={{ background: "#f1f5f9", border: "1px solid #e2e8f0", color: "#64748b", borderRadius: "8px", padding: "7px 14px", cursor: "pointer", fontSize: "13px", fontWeight: 600 }}>
              ⬇ PDF
            </button>
          )}
          <button onClick={() => setShowAssess(true)}
            style={{ background: "#0ea5e9", color: "#fff", border: "none", borderRadius: "8px", padding: "8px 16px", fontWeight: 700, cursor: "pointer", fontSize: "13px" }}>
            Take Assessment
          </button>
          <button onClick={logout} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer" }}>
            <LogOut size={18} />
          </button>
        </div>
      </nav>

      <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
        {loading ? (
          <div style={{ textAlign: "center", padding: "60px", color: "#64748b" }}>Loading your profile...</div>
        ) : !profile ? (
          <div style={{ textAlign: "center", padding: "60px" }}>
            <Brain size={48} color="#cbd5e1" style={{ marginBottom: "16px" }} />
            <h2 style={{ color: "#0f172a", marginBottom: "8px" }}>No assessment yet</h2>
            <p style={{ color: "#64748b", marginBottom: "24px" }}>Take the Big Five assessment to generate your personality profile.</p>
            <button onClick={() => setShowAssess(true)} style={{ background: "#0ea5e9", color: "#fff", border: "none", borderRadius: "8px", padding: "12px 32px", fontWeight: 700, cursor: "pointer", fontSize: "15px" }}>
              Start Assessment →
            </button>
          </div>
        ) : (
          <>
            {/* KPI Row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "24px" }}>
              {[
                { label: "Dominant Trait",    value: TRAIT_LABELS[profile.dominant_trait], color: "#0ea5e9", icon: <Award size={20} color="#0ea5e9" /> },
                { label: "Openness",          value: `${profile.openness.toFixed(0)}/100`,  color: "#0ea5e9", icon: <Brain size={20} color="#0ea5e9" /> },
                { label: "Conscientiousness", value: `${profile.conscientiousness.toFixed(0)}/100`, color: "#10b981", icon: <TrendingUp size={20} color="#10b981" /> },
                { label: "Assessments",       value: history?.history?.length || 1, color: "#f59e0b", icon: <Users size={20} color="#f59e0b" /> },
              ].map(kpi => (
                <div key={kpi.label} style={cardStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <p style={{ color: "#94a3b8", fontSize: "11px", textTransform: "uppercase", letterSpacing: "1px" }}>{kpi.label}</p>
                    {kpi.icon}
                  </div>
                  <p style={{ color: kpi.color, fontSize: "22px", fontWeight: 700 }}>{kpi.value}</p>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: "4px", marginBottom: "20px" }}>
              {["profile", "history", "population"].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} style={{
                  padding: "8px 20px", borderRadius: "8px", border: "none", cursor: "pointer",
                  fontSize: "13px", fontWeight: 600,
                  background: activeTab === tab ? "#0ea5e9" : "#ffffff",
                  color:      activeTab === tab ? "#ffffff" : "#64748b",
                  boxShadow:  activeTab === tab ? "none" : "0 1px 3px rgba(0,0,0,0.06)",
                }}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {/* Profile Tab */}
            {activeTab === "profile" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                <div style={cardStyle}>
                  <h3 style={sectionTitle}>Trait Radar</h3>
                  {radarData && <Radar data={radarData} options={{
                    scales: { r: { min: 0, max: 100, ticks: { color: "#94a3b8", stepSize: 20 }, grid: { color: "#e2e8f0" }, pointLabels: { color: "#475569", font: { size: 11 } } } },
                    plugins: { legend: { display: false } },
                  }} />}
                </div>
                <div style={cardStyle}>
                  <h3 style={sectionTitle}>Trait Scores & Percentiles</h3>
                  {TRAITS.map(trait => (
                    <div key={trait} style={{ marginBottom: "16px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                        <span style={{ color: "#0f172a", fontSize: "13px", fontWeight: 600 }}>{TRAIT_LABELS[trait]}</span>
                        <div>
                          <span style={{ color: TRAIT_COLORS[trait].bg, fontWeight: 700 }}>{profile[trait].toFixed(0)}</span>
                          <span style={{ color: "#94a3b8", fontSize: "11px" }}> · {profile[`${trait}_pct`]}th pct</span>
                        </div>
                      </div>
                      <div style={{ background: "#e2e8f0", borderRadius: "4px", height: "8px" }}>
                        <div style={{ background: TRAIT_COLORS[trait].bg, height: "100%", width: `${profile[trait]}%`, borderRadius: "4px" }} />
                      </div>
                      <p style={{ color: "#94a3b8", fontSize: "11px", marginTop: "4px" }}>{profile.descriptions?.[trait]?.slice(0, 80)}...</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* History Tab */}
            {activeTab === "history" && (
              <div style={cardStyle}>
                <h3 style={sectionTitle}>Trait Score History & Drift Detection</h3>
                {history?.drift && (
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                    {Object.entries(history.drift).map(([trait, direction]) => (
                      <span key={trait} style={{
                        padding: "4px 12px", borderRadius: "20px", fontSize: "11px", fontWeight: 600,
                        background: direction === "increasing" ? "#dcfce7" : direction === "decreasing" ? "#fee2e2" : "#f1f5f9",
                        color:      direction === "increasing" ? "#16a34a" : direction === "decreasing" ? "#dc2626" : "#64748b",
                      }}>
                        {TRAIT_LABELS[trait]}: {direction === "increasing" ? "↑" : direction === "decreasing" ? "↓" : "→"} {direction}
                      </span>
                    ))}
                  </div>
                )}
                {historyData
                  ? <Line data={historyData} options={{ responsive: true,
                      plugins: { legend: { labels: { color: "#475569", font: { size: 11 } } } },
                      scales: {
                        x: { ticks: { color: "#94a3b8" }, grid: { color: "#e2e8f0" } },
                        y: { min: 0, max: 100, ticks: { color: "#94a3b8" }, grid: { color: "#e2e8f0" } }
                      }
                    }} />
                  : <p style={{ color: "#94a3b8", textAlign: "center", padding: "40px" }}>Take multiple assessments to see your trait evolution over time.</p>
                }
              </div>
            )}

            {/* Population Tab */}
            {activeTab === "population" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                <div style={cardStyle}>
                  <h3 style={sectionTitle}>Dominant Trait Distribution</h3>
                  {dominantData
                    ? <Doughnut data={dominantData} options={{ plugins: { legend: { position: "bottom", labels: { color: "#475569", font: { size: 11 } } } } }} />
                    : <p style={{ color: "#94a3b8", textAlign: "center", padding: "40px" }}>No population data yet.</p>
                  }
                </div>
                <div style={cardStyle}>
                  <h3 style={sectionTitle}>Population Averages</h3>
                  {population && TRAITS.map(trait => (
                    <div key={trait} style={{ marginBottom: "12px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                        <span style={{ color: "#475569", fontSize: "13px" }}>{TRAIT_LABELS[trait]}</span>
                        <span style={{ color: TRAIT_COLORS[trait].bg, fontWeight: 700 }}>{population.averages[trait].toFixed(1)}</span>
                      </div>
                      <div style={{ background: "#e2e8f0", borderRadius: "4px", height: "6px" }}>
                        <div style={{ background: TRAIT_COLORS[trait].bg, height: "100%", width: `${population.averages[trait]}%`, borderRadius: "4px" }} />
                      </div>
                    </div>
                  ))}
                  {population && <p style={{ color: "#94a3b8", fontSize: "12px", marginTop: "12px" }}>Based on {population.total_profiles} profiles</p>}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const cardStyle    = { background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "20px", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" };
const sectionTitle = { color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "1px", margin: "0 0 16px" };
const labelStyle   = { display: "block", color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" };
const inputStyle   = { width: "100%", padding: "10px 12px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", color: "#0f172a", fontSize: "14px", outline: "none" };
const navBtnStyle  = { padding: "10px 20px", background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "8px", color: "#64748b", cursor: "pointer", fontSize: "13px" };

// ── Root ──────────────────────────────────────────────────────────────────────
function App() {
  const { user } = useAuth();
  return user ? <Dashboard /> : <LoginPage />;
}

export default function Root() {
  return (
    <AuthProvider>
      <Toaster position="top-right" toastOptions={{ style: { background: "#ffffff", color: "#0f172a", border: "1px solid #e2e8f0" } }} />
      <App />
    </AuthProvider>
  );
}