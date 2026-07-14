"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { workflowService } from "@/services/api";

const PROJECT_ID = "demo-project-id";

const WORKFLOW_TEMPLATES = [
  {
    name: "RAG & LLM Fallback Agent",
    description: "Queries knowledge base, runs agent conditionally on low confidence.",
    definition: {
      nodes: [
        { id: "node_1", type: "llm", data: { prompt: "Summarize this request: {{input.query}}", model: "gpt-4o-mini" } },
        { id: "node_2", type: "condition", data: { field: "node_1.text", operator: "contains", value: "urgent" } },
        { id: "node_3", type: "agent", data: { agent_id: "demo-agent", input: "Escalate urgent issue: {{node_1.text}}", model: "gpt-4o" } }
      ],
      edges: [
        { source: "node_1", target: "node_2" },
        { source: "node_2", target: "node_3" }
      ]
    }
  },
  {
    name: "Simple LLM Chain",
    description: "Translate input query to French, then format as HTML.",
    definition: {
      nodes: [
        { id: "node_1", type: "llm", data: { prompt: "Translate '{{input.text}}' into French", model: "gpt-4o-mini" } },
        { id: "node_2", type: "llm", data: { prompt: "Wrap this in a nice HTML paragraph: {{node_1.text}}", model: "gpt-4o-mini" } }
      ],
      edges: [
        { source: "node_1", target: "node_2" }
      ]
    }
  }
];

export default function WorkflowsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [runInput, setRunInput] = useState('{\n  "query": "system is down, urgent help needed!"\n}');
  const [executionResult, setExecutionResult] = useState<any>(null);
  
  const [form, setForm] = useState({
    name: "",
    description: "",
    definitionJSON: JSON.stringify(WORKFLOW_TEMPLATES[0].definition, null, 2)
  });

  const { data: workflows = [], refetch } = useQuery({
    queryKey: ["workflows", PROJECT_ID],
    queryFn: () => workflowService.listWorkflows(PROJECT_ID),
  });

  const { data: runs = [], refetch: refetchRuns } = useQuery({
    queryKey: ["workflow-runs", selected],
    queryFn: () => workflowService.getWorkflowRuns(selected!),
    enabled: !!selected
  });

  const createMutation = useMutation({
    mutationFn: () => workflowService.createWorkflow({
      project_id: PROJECT_ID,
      name: form.name,
      description: form.description,
      definition: JSON.parse(form.definitionJSON)
    }),
    onSuccess: () => {
      refetch();
      setShowCreate(false);
    }
  });

  const runMutation = useMutation({
    mutationFn: () => workflowService.executeWorkflow(selected!, JSON.parse(runInput)),
    onSuccess: (data) => {
      setExecutionResult(data);
      refetchRuns();
    }
  });

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1">Workflows</h1>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Visual and node-based LLM chains and agent routing</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>+ New Workflow</button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Workflows list */}
        <div className="col-span-1 space-y-3">
          {(workflows as any[]).map((w: any) => (
            <div key={w.id} onClick={() => { setSelected(w.id); setExecutionResult(null); }}
              className={`glass rounded-xl p-4 cursor-pointer transition-all ${selected === w.id ? "border-violet-500 border" : ""}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">🔗</span>
                <span className="font-semibold text-sm">{w.name}</span>
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{w.description}</p>
              <span className={`badge mt-2 ${w.is_active ? "badge-green" : "badge-red"}`}>
                {w.is_active ? "active" : "inactive"}
              </span>
            </div>
          ))}
          {workflows.length === 0 && (
            <div className="glass rounded-xl p-6 text-center">
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No workflows yet. Build one!</p>
            </div>
          )}
        </div>

        {/* Workflow detail / run view */}
        <div className="col-span-2 space-y-6">
          {!selected ? (
            <div className="glass rounded-xl flex items-center justify-center" style={{ minHeight: 400 }}>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Select a workflow to configure & run</p>
            </div>
          ) : (
            <>
              {/* Execution Request Form */}
              <div className="glass rounded-xl p-5">
                <h2 className="font-bold text-sm mb-4">Run Workflow</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Input Data (JSON)</label>
                    <textarea className="input font-mono" rows={4} value={runInput}
                      onChange={(e) => setRunInput(e.target.value)} style={{ resize: "none", fontSize: "0.8rem" }} />
                  </div>
                  <button className="btn-primary w-full" onClick={() => runMutation.mutate()}
                    disabled={runMutation.isPending}>
                    {runMutation.isPending ? "Executing..." : "▶ Run Workflow"}
                  </button>
                </div>
              </div>

              {/* Execution Result */}
              {executionResult && (
                <div className="glass rounded-xl p-5">
                  <h2 className="font-bold text-sm mb-3">Latest Execution Output</h2>
                  <div className="flex items-center gap-3 mb-4">
                    <span className={`badge ${executionResult.status === "completed" ? "badge-green" : "badge-red"}`}>
                      {executionResult.status}
                    </span>
                    {executionResult.completed_at && (
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        Finished at: {new Date(executionResult.completed_at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <pre className="rounded-lg p-3 text-xs overflow-auto font-mono"
                    style={{ background: "var(--surface-2)", border: "1px solid var(--border)", maxHeight: 300 }}>
                    {JSON.stringify(executionResult.output || executionResult.error, null, 2)}
                  </pre>
                </div>
              )}

              {/* Execution history */}
              <div className="glass rounded-xl p-5">
                <h2 className="font-bold text-sm mb-3">Execution History</h2>
                <div className="space-y-2">
                  {(runs as any[]).map((r: any) => (
                    <div key={r.id} className="flex justify-between items-center py-2 border-b last:border-0" style={{ borderColor: "var(--border)" }}>
                      <span className="font-mono text-xs">{r.id.slice(0, 8)}...</span>
                      <span className={`badge ${r.status === "completed" ? "badge-green" : "badge-red"}`}>{r.status}</span>
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {new Date(r.started_at).toLocaleString()}
                      </span>
                    </div>
                  ))}
                  {runs.length === 0 && (
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>No runs recorded yet</p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="glass rounded-2xl p-6 w-full max-w-lg">
            <h2 className="font-bold mb-4">Create New Workflow</h2>
            <div className="space-y-3">
              <input className="input" placeholder="Workflow name" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <input className="input" placeholder="Short description" value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })} />
              
              <div className="flex gap-2">
                {WORKFLOW_TEMPLATES.map((tmpl) => (
                  <button key={tmpl.name} className="btn-secondary text-xs py-1 px-2.5"
                    onClick={() => setForm({ ...form, definitionJSON: JSON.stringify(tmpl.definition, null, 2) })}>
                    Use template: {tmpl.name}
                  </button>
                ))}
              </div>

              <div>
                <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Workflow Definition (JSON)</label>
                <textarea className="input font-mono" rows={8} value={form.definitionJSON}
                  onChange={(e) => setForm({ ...form, definitionJSON: e.target.value })} style={{ resize: "none", fontSize: "0.8rem" }} />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button className="btn-secondary flex-1" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="btn-primary flex-1" onClick={() => createMutation.mutate()}
                disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
