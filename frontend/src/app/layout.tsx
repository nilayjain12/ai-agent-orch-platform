import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { LayoutDashboard, Users, GitMerge, Activity } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Agent Orchestration",
  description: "Manage, build, and monitor AI agent workflows",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} bg-slate-950 text-slate-50 min-h-screen flex`} suppressHydrationWarning>
        {/* Sidebar */}
        <aside className="w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur flex flex-col p-4 space-y-8">
          <div className="flex items-center space-x-3 text-indigo-400">
            <Activity className="w-8 h-8" />
            <h1 className="text-xl font-bold tracking-tight">AgentOrch</h1>
          </div>
          
          <nav className="flex-1 space-y-2">
            <Link href="/" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-slate-800/50 transition-colors text-slate-300 hover:text-white group">
              <LayoutDashboard className="w-5 h-5 group-hover:text-indigo-400 transition-colors" />
              <span>Dashboard</span>
            </Link>
            <Link href="/agents" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-slate-800/50 transition-colors text-slate-300 hover:text-white group">
              <Users className="w-5 h-5 group-hover:text-pink-400 transition-colors" />
              <span>Agents</span>
            </Link>
            <Link href="/builder" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-slate-800/50 transition-colors text-slate-300 hover:text-white group">
              <GitMerge className="w-5 h-5 group-hover:text-emerald-400 transition-colors" />
              <span>Builder</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8 overflow-y-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
