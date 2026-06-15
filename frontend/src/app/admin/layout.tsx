import Link from "next/link";
import React from "react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-[#050505] text-gray-200 font-sans">
      <aside className="w-64 bg-[#0a0a0a] border-r border-gray-800 p-6 flex flex-col gap-4">
        <h1 className="text-xl font-bold text-white mb-6">Alchemist Admin</h1>
        <nav className="flex flex-col gap-2">
          <Link href="/admin" className="p-2 hover:bg-gray-800 rounded text-sm transition-colors">Dashboard Overview</Link>
          <Link href="/admin/logs" className="p-2 hover:bg-gray-800 rounded text-sm transition-colors">Execution Audit Log</Link>
          <Link href="/admin/tools" className="p-2 hover:bg-gray-800 rounded text-sm transition-colors">Tool Analytics</Link>
          <Link href="/admin/tasks" className="p-2 hover:bg-gray-800 rounded text-sm transition-colors">Task Timeline</Link>
          <Link href="/admin/errors" className="p-2 hover:bg-gray-800 rounded text-sm transition-colors">Error Tracking</Link>
        </nav>
      </aside>
      <main className="flex-1 p-8 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
