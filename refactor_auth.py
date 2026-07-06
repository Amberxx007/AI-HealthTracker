import sys

path = r'd:\ai-doctor-v3\frontend\components\frontend_EnhancedMedicalChat.jsx'
with open(path, encoding='utf-8') as f:
    text = f.read()

if 'isAuthenticated' in text:
    print('Auth already injected')
    sys.exit(0)

idx_start = text.find('export default function EnhancedMedicalChat() {')
if idx_start == -1:
    print('Could not find component start')
    sys.exit(1)

# 1. Inject state
state_code = """
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [authForm, setAuthForm] = useState({ patient_id: "", password: "", name: "" });
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  
  useEffect(() => {
    const token = localStorage.getItem("ai_doctor_token");
    if (token) {
      setIsAuthenticated(true);
    }
    const handleAuthError = () => {
      setIsAuthenticated(false);
      localStorage.removeItem("ai_doctor_token");
    };
    window.addEventListener("auth_error", handleAuthError);
    return () => window.removeEventListener("auth_error", handleAuthError);
  }, []);
"""

idx_state = text.find('useState', idx_start)
idx_inject_state = text.rfind('\n', idx_start, idx_state) + 1
text = text[:idx_inject_state] + state_code + text[idx_inject_state:]

# Recalculate return index
idx_return = text.find('\n  return (', idx_start)
if idx_return == -1: 
    idx_return = text.find('\n  return(', idx_start)

# 2. Inject JSX
jsx_code = """
  if (!isAuthenticated) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: T.bg, padding: 20 }}>
        <div className="ma-card fade-up" style={{ width: "100%", maxWidth: 420, padding: 32 }}>
          <div style={{ textAlign: "center", marginBottom: 32 }}>
            <div style={{ display: "inline-flex", padding: 16, background: `${T.accent}15`, borderRadius: 16, marginBottom: 16 }}>
              <Shield size={32} color={T.accent} />
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: T.text, marginBottom: 8 }}>
              {isLoginMode ? "Welcome Back" : "Create Account"}
            </h1>
            <p style={{ color: T.textSub, fontSize: 14 }}>
              Secure access to your personal health AI
            </p>
          </div>
          
          {authError && (
            <div style={{ padding: 12, background: `${T.danger}15`, color: T.danger, borderRadius: 8, fontSize: 13, marginBottom: 20, display: "flex", gap: 8 }}>
              <AlertTriangle size={16} /> {authError}
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: T.textSub, marginBottom: 6 }}>Patient ID (Username)</label>
              <input className="ma-input" value={authForm.patient_id} onChange={e => setAuthForm(prev => ({...prev, patient_id: e.target.value}))} placeholder="e.g. john_doe" />
            </div>
            
            {!isLoginMode && (
              <div>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: T.textSub, marginBottom: 6 }}>Full Name</label>
                <input className="ma-input" value={authForm.name} onChange={e => setAuthForm(prev => ({...prev, name: e.target.value}))} placeholder="John Doe" />
              </div>
            )}

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: T.textSub, marginBottom: 6 }}>Password</label>
              <input className="ma-input" type="password" value={authForm.password} onChange={e => setAuthForm(prev => ({...prev, password: e.target.value}))} placeholder="••••••••" />
            </div>

            <button 
              className="ma-btn ma-btn-primary" 
              style={{ width: "100%", padding: 14, marginTop: 8 }}
              disabled={authLoading || !authForm.patient_id || !authForm.password}
              onClick={async () => {
                setAuthLoading(true);
                setAuthError("");
                try {
                  const endpoint = isLoginMode ? "/api/auth/login" : "/api/auth/register";
                  const res = await window.fetch(`${API}${endpoint}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(authForm)
                  });
                  const data = await res.json();
                  if (!res.ok) throw new Error(data.detail || "Authentication failed");
                  
                  if (isLoginMode) {
                    localStorage.setItem("ai_doctor_token", data.access_token);
                    localStorage.setItem("ma_patient_id", data.patient_id);
                    setPatientId(data.patient_id);
                    setIsAuthenticated(true);
                  } else {
                    setIsLoginMode(true);
                    setAuthError("Account created! Please sign in.");
                  }
                } catch (err) {
                  setAuthError(err.message);
                } finally {
                  setAuthLoading(false);
                }
              }}
            >
              {authLoading ? <Loader2 className="dot1" size={18} /> : (isLoginMode ? "Sign In" : "Register")}
            </button>
            
            <div style={{ textAlign: "center", marginTop: 8 }}>
              <button className="ma-btn-ghost" style={{ fontSize: 13, border: "none" }} onClick={() => setIsLoginMode(!isLoginMode)}>
                {isLoginMode ? "Need an account? Register" : "Already have an account? Sign in"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
"""
text = text[:idx_return] + jsx_code + text[idx_return:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Injected Auth UI')
