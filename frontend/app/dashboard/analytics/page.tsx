"use client";

const METRICS = [
  { label: "Total Requests", value: "48,213",  change: "+12%" },
  { label: "Avg Latency",    value: "412ms",   change: "-8%" },
  { label: "Error Rate",     value: "0.4%",    change: "-0.1%" },
  { label: "Est. Cost",      value: "$14.72",  change: "+$3.20" },
];

const USAGE = [
  { provider: "OpenAI",   model: "gpt-4o",          tokens: "1.2M", cost: "$7.40",  pct: 75 },
  { provider: "Gemini",   model: "gemini-1.5-flash", tokens: "600K", cost: "$3.20",  pct: 38 },
  { provider: "Claude",   model: "claude-sonnet-4-5",tokens: "200K", cost: "$4.12",  pct: 15 },
];

export default function AnalyticsPage() {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1">Analytics</h1>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Token usage, cost tracking, and performance metrics</p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {METRICS.map((m) => (
          <div key={m.label} className="glass rounded-xl p-5">
            <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>{m.label}</p>
            <p className="text-xl font-bold mb-1">{m.value}</p>
            <span className="text-xs" style={{ color: m.change.startsWith("-") && m.label !== "Error Rate" ? "#f87171" : "#34d399" }}>
              {m.change} vs last week
            </span>
          </div>
        ))}
      </div>

      {/* Provider breakdown */}
      <div className="glass rounded-xl p-6 mb-6">
        <h2 className="font-semibold mb-4 text-sm">Provider Token Usage</h2>
        <div className="space-y-4">
          {USAGE.map((u) => (
            <div key={u.provider}>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-medium">{u.provider} · {u.model}</span>
                <span style={{ color: "var(--text-muted)" }}>{u.tokens} · {u.cost}</span>
              </div>
              <div className="h-2 rounded-full" style={{ background: "var(--surface-2)" }}>
                <div className="h-2 rounded-full bg-gradient-to-r from-violet-600 to-purple-400 transition-all"
                  style={{ width: `${u.pct}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Audit log placeholder */}
      <div className="glass rounded-xl p-6">
        <h2 className="font-semibold mb-4 text-sm">Recent API Calls</h2>
        <div className="space-y-2">
          {[
            { ep: "POST /gateway/chat", model: "gpt-4o",   lat: "380ms",  ts: "2 min ago",  ok: true },
            { ep: "POST /rag/query",    model: "gpt-4o",   lat: "612ms",  ts: "5 min ago",  ok: true },
            { ep: "POST /agents/chat",  model: "gpt-4o",   lat: "1.2s",   ts: "8 min ago",  ok: true },
            { ep: "POST /gateway/chat", model: "gemini",   lat: "290ms",  ts: "12 min ago", ok: false },
          ].map((r, i) => (
            <div key={i} className="flex items-center justify-between py-2 text-xs border-b last:border-0" style={{ borderColor: "var(--border)" }}>
              <span className="font-mono">{r.ep}</span>
              <span className="badge badge-blue">{r.model}</span>
              <span style={{ color: "var(--text-muted)" }}>{r.lat}</span>
              <span className={`badge ${r.ok ? "badge-green" : "badge-red"}`}>{r.ok ? "200" : "502"}</span>
              <span style={{ color: "var(--text-muted)" }}>{r.ts}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
