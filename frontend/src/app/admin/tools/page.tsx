"use client";

import React, { useEffect, useState } from "react";

export default function ToolsPage() {
  const [tools, setTools] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/admin/tools")
      .then(r => r.json())
      .then(data => setTools(data.tools || []))
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-white">Tool Analytics</h2>
      
      <div className="overflow-x-auto bg-[#111] rounded-lg border border-gray-800">
        <table className="w-full text-left text-sm text-gray-400">
          <thead className="text-xs text-gray-300 uppercase bg-[#1a1a1a] border-b border-gray-800">
            <tr>
              <th className="px-6 py-3">Tool Name</th>
              <th className="px-6 py-3">Usage Count</th>
              <th className="px-6 py-3">Success Rate</th>
              <th className="px-6 py-3">Failure Rate</th>
              <th className="px-6 py-3">Avg Execution Time (s)</th>
            </tr>
          </thead>
          <tbody>
            {tools.map((tool: any) => (
              <tr key={tool.tool_name} className="border-b border-gray-800 hover:bg-[#1a1a1a]">
                <td className="px-6 py-4 font-mono text-xs text-white">{tool.tool_name}</td>
                <td className="px-6 py-4">{tool.usage_count}</td>
                <td className="px-6 py-4 text-green-400">{tool.success_rate?.toFixed(1)}%</td>
                <td className="px-6 py-4 text-red-400">{tool.failure_rate?.toFixed(1)}%</td>
                <td className="px-6 py-4">{tool.average_execution_time?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
