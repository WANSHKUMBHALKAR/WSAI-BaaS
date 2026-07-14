"use client";
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { gatewayService } from "@/services/api";

export default function GatewayPage() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [model, setModel] = useState("gpt-4o");

  const { data: providerMap } = useQuery({
    queryKey: ["models"],
    queryFn: gatewayService.listModels,
  });

  const allModels = providerMap
    ? Object.entries(providerMap as Record<string, string[]>).flatMap(([prov, ms]) =>
        ms.map((m) => ({ model: m, provider: prov }))
      )
    : [];

  const chatMutation = useMutation({
    mutationFn: () => gatewayService.chat(messages.concat({ role: "user", content: input }), model),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: input },
        { role: "assistant", content: data.content || data.message || JSON.stringify(data) },
      ]);
      setInput("");
    },
  });

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    chatMutation.mutate();
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1">AI Gateway</h1>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Unified interface to all LLM providers</p>
        </div>
        <select className="input w-auto" value={model} onChange={(e) => setModel(e.target.value)}>
          {allModels.map(({ model: m, provider }) => (
            <option key={`${provider}-${m}`} value={m}>{m} ({provider})</option>
          ))}
        </select>
      </div>

      <div className="glass rounded-2xl flex flex-col" style={{ height: 560 }}>
        <div className="flex-1 p-5 flex flex-col gap-3 overflow-y-auto">
          {messages.length === 0 && (
            <div className="flex-1 flex items-center justify-center flex-col gap-2">
              <span className="text-4xl">⚡</span>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Select a model and start chatting</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}>
              <p className="text-sm whitespace-pre-wrap">{m.content}</p>
            </div>
          ))}
          {chatMutation.isPending && (
            <div className="chat-bubble-ai"><p className="text-sm animate-pulse">Generating...</p></div>
          )}
        </div>
        <form onSubmit={handleSend} className="p-4 border-t flex gap-2" style={{ borderColor: "var(--border)" }}>
          <input className="input flex-1" placeholder={`Chat with ${model}...`} value={input}
            onChange={(e) => setInput(e.target.value)} />
          <button type="submit" className="btn-primary px-6" disabled={chatMutation.isPending}>Send</button>
        </form>
      </div>
    </div>
  );
}
