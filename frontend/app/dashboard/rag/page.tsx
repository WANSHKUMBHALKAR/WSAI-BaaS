"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { ragService } from "@/services/api";

const PROJECT_ID = "00000000-0000-0000-0000-000000000000";

export default function RAGPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<any>(null);
  const [uploading, setUploading] = useState(false);

  const { data: docs = [], refetch } = useQuery({
    queryKey: ["docs", PROJECT_ID],
    queryFn: () => ragService.listDocuments(PROJECT_ID),
  });

  const queryMutation = useMutation({
    mutationFn: (q: string) => ragService.query(PROJECT_ID, q),
    onSuccess: (data) => setAnswer(data),
  });

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await ragService.uploadDocument(PROJECT_ID, file);
      refetch();
    } finally { setUploading(false); }
  }

  function handleQuery(e: React.FormEvent) {
    e.preventDefault();
    if (question.trim()) queryMutation.mutate(question);
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1">RAG System</h1>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Upload documents and query your knowledge base</p>
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Documents */}
        <div className="col-span-2">
          <div className="glass rounded-xl p-4 mb-4">
            <h2 className="font-semibold text-sm mb-3">Upload Document</h2>
            <label className="flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-6 cursor-pointer transition-colors hover:border-violet-500"
              style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
              {uploading ? <span className="text-sm animate-pulse">Uploading...</span> : (
                <>
                  <span className="text-2xl mb-2">📁</span>
                  <span className="text-xs">Click to upload PDF, DOCX, or TXT</span>
                </>
              )}
              <input type="file" accept=".pdf,.docx,.txt" onChange={handleUpload} className="hidden" />
            </label>
          </div>

          <div className="glass rounded-xl p-4">
            <h2 className="font-semibold text-sm mb-3">Documents ({(docs as any[]).length})</h2>
            <div className="space-y-2">
              {(docs as any[]).map((d: any) => (
                <div key={d.id} className="flex items-center justify-between py-1.5 border-b last:border-0" style={{ borderColor: "var(--border)" }}>
                  <div>
                    <p className="text-xs font-medium truncate max-w-[120px]">{d.filename}</p>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>{d.chunks} chunks</p>
                  </div>
                  <span className={`badge ${d.status === "completed" ? "badge-green" : d.status === "failed" ? "badge-red" : "badge-blue"}`}>
                    {d.status}
                  </span>
                </div>
              ))}
              {docs.length === 0 && <p className="text-xs" style={{ color: "var(--text-muted)" }}>No documents yet</p>}
            </div>
          </div>
        </div>

        {/* Query */}
        <div className="col-span-3 glass rounded-xl p-5 flex flex-col">
          <h2 className="font-semibold text-sm mb-4">Ask Your Documents</h2>
          <form onSubmit={handleQuery} className="flex gap-2 mb-4">
            <input className="input flex-1" placeholder="Ask anything about your documents..." value={question}
              onChange={(e) => setQuestion(e.target.value)} />
            <button type="submit" className="btn-primary" disabled={queryMutation.isPending}>
              {queryMutation.isPending ? "..." : "Ask"}
            </button>
          </form>

          {answer && (
            <div className="flex-1 space-y-4">
              <div className="rounded-xl p-4" style={{ background: "var(--surface-2)" }}>
                <p className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>ANSWER</p>
                <p className="text-sm leading-relaxed">{answer.answer}</p>
                <div className="flex gap-2 mt-3">
                  <span className="badge badge-purple">{answer.model}</span>
                  <span className="badge badge-blue">{answer.tokens_used} tokens</span>
                </div>
              </div>
              {answer.sources?.length > 0 && (
                <div>
                  <p className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>SOURCES</p>
                  <div className="space-y-2">
                    {answer.sources.map((s: any, i: number) => (
                      <div key={i} className="rounded-lg p-3 text-xs" style={{ background: "var(--surface-2)", border: "1px solid var(--border)" }}>
                        <span className="badge badge-green mb-1">Score: {s.score}</span>
                        <p className="mt-1 leading-relaxed" style={{ color: "var(--text-muted)" }}>{s.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
