"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { agentService } from "@/services/api";

const PROJECT_ID = "00000000-0000-0000-0000-000000000000"; // placeholder workspace UUID for local demos

export default function AgentsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string; text: string }[]>([]);

  const { data: agents = [], refetch } = useQuery({
    queryKey: ["agents", PROJECT_ID],
    queryFn: () => agentService.listAgents(PROJECT_ID),
  });

  const [form, setForm] = useState({ name: "", system_prompt: "You are a helpful AI assistant.", model: "gpt-4o" });

  const createMutation = useMutation({
    mutationFn: () => agentService.createAgent({ project_id: PROJECT_ID, ...form }),
    onSuccess: () => { refetch(); setShowCreate(false); },
  });

  const chatMutation = useMutation({
    mutationFn: (msg: string) => agentService.chat(selected!, "anonymous-user", msg),
    onSuccess: (data) => {
      setChatHistory((h) => [...h, { role: "assistant", text: data.response }]);
    },
  });

  function sendChat(e: React.FormEvent) {
    e.preventDefault();
    if (!chatInput.trim() || !selected) return;
    setChatHistory((h) => [...h, { role: "user", text: chatInput }]);
    chatMutation.mutate(chatInput);
    setChatInput("");
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1">AI Agents</h1>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Create and manage autonomous AI agents</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>+ New Agent</button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Agent list */}
        <div className="col-span-1 space-y-3">
          {(agents as any[]).map((a: any) => (
            <div key={a.id} onClick={() => { setSelected(a.id); setChatHistory([]); }}
              className={`glass rounded-xl p-4 cursor-pointer transition-all ${selected === a.id ? "border-violet-500 border" : ""}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">🤖</span>
                <span className="font-semibold text-sm">{a.name}</span>
              </div>
              <span className="badge badge-blue">{a.model}</span>
            </div>
          ))}
          {agents.length === 0 && (
            <div className="glass rounded-xl p-6 text-center">
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No agents yet. Create one!</p>
            </div>
          )}
        </div>

        {/* Chat panel */}
        <div className="col-span-2 glass rounded-xl flex flex-col" style={{ minHeight: 480 }}>
          {!selected ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Select an agent to start chatting</p>
            </div>
          ) : (
            <>
              <div className="flex-1 p-4 flex flex-col gap-3 overflow-y-auto">
                {chatHistory.map((m, i) => (
                  <div key={i} className={m.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}>
                    <p className="text-sm">{m.text}</p>
                  </div>
                ))}
                {chatMutation.isPending && (
                  <div className="chat-bubble-ai">
                    <p className="text-sm animate-pulse">Thinking...</p>
                  </div>
                )}
              </div>
              <form onSubmit={sendChat} className="p-4 border-t flex gap-2" style={{ borderColor: "var(--border)" }}>
                <input className="input flex-1" placeholder="Type your message..." value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)} />
                <button type="submit" className="btn-primary px-4">Send</button>
              </form>
            </>
          )}
        </div>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="glass rounded-2xl p-6 w-full max-w-md">
            <h2 className="font-bold mb-4">Create New Agent</h2>
            <div className="space-y-3">
              <input className="input" placeholder="Agent name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <textarea className="input" rows={3} placeholder="System prompt" value={form.system_prompt}
                onChange={(e) => setForm({ ...form, system_prompt: e.target.value })} style={{ resize: "none" }} />
              <select className="input" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })}>
                {["gpt-4o", "gpt-4o-mini", "gemini-1.5-flash", "claude-sonnet-4-5"].map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
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
