"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";

const NAV = [
  { href: "/dashboard",          label: "Overview",  icon: "⬡" },
  { href: "/dashboard/agents",   label: "Agents",    icon: "🤖" },
  { href: "/dashboard/rag",      label: "RAG",       icon: "📚" },
  { href: "/dashboard/gateway",  label: "Gateway",   icon: "⚡" },
  { href: "/dashboard/mcp",      label: "MCP Tools", icon: "🔧" },
  { href: "/dashboard/workflows",label: "Workflows", icon: "🔗" },
  { href: "/dashboard/analytics",label: "Analytics", icon: "📊" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();

  function handleLogout() {
    logout();
    localStorage.removeItem("wsai_token");
    router.push("/login");
  }

  return (
    <aside className="sidebar w-56 min-h-screen flex flex-col py-5 px-3">
      {/* Brand */}
      <div className="flex items-center gap-2 px-2 mb-8">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-white font-bold text-sm">W</div>
        <span className="font-bold text-sm tracking-tight">WSAI BaaS</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5">
        {NAV.map(({ href, label, icon }) => (
          <Link key={href} href={href}
            className={`nav-item ${pathname === href || (href !== "/dashboard" && pathname.startsWith(href)) ? "active" : ""}`}>
            <span className="text-base">{icon}</span>
            <span>{label}</span>
          </Link>
        ))}
      </nav>

      {/* Logout */}
      <button onClick={handleLogout} className="nav-item mt-4 w-full text-left">
        <span>🚪</span><span>Logout</span>
      </button>
    </aside>
  );
}
