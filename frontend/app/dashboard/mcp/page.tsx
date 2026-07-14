"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { mcpService } from "@/services/api";

export default function MCPPage() {
  const [selected, setSelected] = useState<any>(null);
  const [argsInput, setArgsInput] = useState("{}");
  const [result, setResult] = useState<string | null>(null);

  const { data } = useQuery({
    queryKey: ["mcp-tools"],
    queryFn: mcpService.listTools,
  });
  const tools: any[] = data?.tools || [];

  const execMutation = useMutation({
    mutationFn: () => {
      const args = JSON.parse(argsInput || "{}");
      return mcpService.callTool(selected.name, args);
    },
    onSuccess: (res) => setResult(JSON.stringify(res, null, 2)),
  });

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1">MCP Tool Registry</h1>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Browse and execute Model Context Protocol tools</p>
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Tool list */}
        <div className="col-span-2 space-y-2">
          {tools.map((t: any) => (
            <div key={t.name} onClick={() => { setSelected(t); setResult(null); }}
              className={`glass rounded-xl p-3 cursor-pointer transition-all ${selected?.name === t.name ? "border border-violet-500" : ""}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-sm">{t.name}</span>
                <span className={`badge ${t.provider === "builtin" ? "badge-purple" : "badge-blue"}`}>{t.provider}</span>
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{t.description}</p>
            </div>
          ))}
        </div>

        {/* Tool executor */}
        <div className="col-span-3 glass rounded-xl p-5">
          {!selected ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Select a tool to execute</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <h2 className="font-bold">{selected.name}</h2>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{selected.description}</p>
              </div>
              <div>
                <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Arguments (JSON)</label>
                <textarea className="input font-mono" rows={5} value={argsInput}
                  onChange={(e) => setArgsInput(e.target.value)} style={{ resize: "none", fontSize: "0.8rem" }} />
              </div>
              <button className="btn-primary w-full" onClick={() => execMutation.mutate()}
                disabled={execMutation.isPending}>
                {execMutation.isPending ? "Running..." : "▶ Execute Tool"}
              </button>
              {result && (
                <div>
                  <p className="text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>RESULT</p>
                  <pre className="rounded-lg p-3 text-xs overflow-auto font-mono"
                    style={{ background: "var(--surface-2)", border: "1px solid var(--border)", maxHeight: 200 }}>
                    {result}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
