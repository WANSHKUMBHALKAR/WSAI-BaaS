"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authService } from "@/services/api";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (tab === "login") {
        const data = await authService.login(email, password);
        setToken(data.access_token);
        localStorage.setItem("wsai_token", data.access_token);
        router.push("/dashboard");
      } else {
        await authService.register(email, password, fullName);
        setTab("login");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen glow-bg flex items-center justify-center p-4">
      <div className="glass rounded-2xl p-8 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-white font-bold text-lg">W</div>
            <span className="text-xl font-bold tracking-tight">WSAI BaaS</span>
          </div>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>AI Backend-as-a-Service Platform</p>
        </div>

        {/* Tabs */}
        <div className="flex rounded-xl overflow-hidden mb-6" style={{ background: "var(--surface-2)", border: "1px solid var(--border)" }}>
          {(["login", "register"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)} className="flex-1 py-2 text-sm font-medium capitalize transition-all"
              style={{ background: tab === t ? "rgba(124,58,237,0.25)" : "transparent", color: tab === t ? "#a78bfa" : "var(--text-muted)" }}>
              {t}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {tab === "register" && (
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-muted)" }}>Full Name</label>
              <input className="input" placeholder="Jane Doe" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
          )}
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-muted)" }}>Email</label>
            <input className="input" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-muted)" }}>Password</label>
            <input className="input" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          {error && <p className="text-xs text-red-400 bg-red-900/20 rounded-lg px-3 py-2">{error}</p>}

          <button type="submit" className="btn-primary w-full py-2.5" disabled={loading}>
            {loading ? "Please wait..." : tab === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
