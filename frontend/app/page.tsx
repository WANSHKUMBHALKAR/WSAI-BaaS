import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="max-w-3xl w-full p-8">
        <h1 className="text-3xl font-bold mb-4">WSAI BaaS</h1>
        <p className="mb-6 text-sm text-zinc-400">Welcome to WSAI BaaS — AI Backend-as-a-Service. Use the dashboard to manage agents, RAG, and integrations.</p>
        <div className="flex gap-3">
          <Link href="/dashboard" className="btn-primary">Open Dashboard</Link>
          <Link href="/login" className="btn-secondary">Sign In</Link>
        </div>
      </div>
    </div>
  );
}
