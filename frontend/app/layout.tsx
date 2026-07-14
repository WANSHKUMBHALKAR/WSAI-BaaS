import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "WSAI BaaS — AI Backend-as-a-Service",
  description: "Build AI applications faster with authentication, memory, RAG, agent workflows, and multi-LLM support.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-[#0a0a0f] text-white`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
