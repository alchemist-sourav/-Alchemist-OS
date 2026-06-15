"use client";

import React, { useEffect, useState } from "react";

export default function AdminDashboard() {
  const [system, setSystem] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/admin/system")
      .then(r => r.json())
      .then(setSystem)
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-white">System Health Overview</h2>
      
      {system ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <h3 className="text-gray-400 text-sm mb-2">CPU Usage</h3>
            <p className="text-3xl text-white font-mono">{system.cpu_percent}%</p>
          </div>
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <h3 className="text-gray-400 text-sm mb-2">RAM Usage</h3>
            <p className="text-3xl text-white font-mono">{system.ram_percent}%</p>
          </div>
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <h3 className="text-gray-400 text-sm mb-2">Disk Usage</h3>
            <p className="text-3xl text-white font-mono">{system.disk_percent}%</p>
          </div>
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <h3 className="text-gray-400 text-sm mb-2">Active WebSockets</h3>
            <p className="text-3xl text-white font-mono">{system.active_websockets}</p>
          </div>
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <h3 className="text-gray-400 text-sm mb-2">Active Tasks</h3>
            <p className="text-3xl text-white font-mono">{system.active_tasks}</p>
          </div>
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <h3 className="text-gray-400 text-sm mb-2">Browser Session</h3>
            <p className="text-3xl text-white font-mono capitalize">{system.browser_session}</p>
          </div>
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <h3 className="text-gray-400 text-sm mb-2">Database Status</h3>
            <p className="text-3xl text-white font-mono capitalize">{system.database}</p>
          </div>
        </div>
      ) : (
        <p className="text-gray-500">Loading system metrics...</p>
      )}
    </div>
  );
}
