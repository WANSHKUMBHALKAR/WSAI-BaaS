"use client";
import { useQuery } from "@tanstack/react-query";
import { gatewayService } from "@/services/api";

const STATS = [
  { label: "Total API Calls",   value: "12,480", delta: "+18%", color: "#7c3aed" },
  { label: "Tokens Used",       value: "2.4M",   delta: "+24%", color: "#3b82f6" },
  { label: "Active Agents",     value: "7",      delta: "+2",   color: "#10b981" },
  { label: "Documents Indexed", value: "143",    delta: "+31",  color: "#f59e0b" },
];

export default function DashboardPage() {
  const { data: models } = useQuery({
    queryKey: ["models"],
    queryFn: gatewayService.listModels,
  });

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-1">Platform Overview</h1>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          WSAI BaaS · AI Backend-as-a-Service
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {STATS.map((s) => (
          <div key={s.label} className="glass rounded-xl p-5">
            <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>{s.label}</p>
            <p className="text-2xl font-bold mb-1" style={{ color: s.color }}>{s.value}</p>
            <span className="badge badge-green">{s.delta}</span>
          </div>
        ))}
      </div>

      {/* Provider Status */}
      <div className="glass rounded-xl p-6 mb-6">
        <h2 className="font-semibold mb-4 text-sm">Available LLM Providers</h2>
        <div className="space-y-3">
          {models
            ? Object.entries(models).map(([provider, modelList]) => (
                <div key={provider} className="flex items-center justify-between py-2 border-b" style={{ borderColor: "var(--border)" }}>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400" />
                    <span className="text-sm capitalize font-medium">{provider}</span>
                  </div>
                  <div className="flex gap-1 flex-wrap justify-end max-w-xs">
                    {(modelList as string[]).slice(0, 3).map((m) => (
                      <span key={m} className="badge badge-blue">{m}</span>
                    ))}
                    {(modelList as string[]).length > 3 && (
                      <span className="badge badge-purple">+{(modelList as string[]).length - 3}</span>
                    )}
                  </div>
                </div>
              ))
            : <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading providers...</p>}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { title: "Create Agent",    desc: "Deploy a new AI agent with memory and tools",   href: "/dashboard/agents",  icon: "🤖" },
          { title: "Upload Document", desc: "Ingest PDFs and websites into your RAG store",   href: "/dashboard/rag",     icon: "📚" },
          { title: "Explore Tools",   desc: "Browse and connect MCP-compatible tools",        href: "/dashboard/mcp",     icon: "🔧" },
        ].map((a) => (
          <a key={a.title} href={a.href} className="glass rounded-xl p-5 hover:border-violet-500 transition-all cursor-pointer block"
            style={{ textDecoration: "none", color: "inherit" }}>
            <div className="text-2xl mb-3">{a.icon}</div>
            <div className="font-semibold text-sm mb-1">{a.title}</div>
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>{a.desc}</div>
          </a>
        ))}
      </div>
    </div>
  );
}
