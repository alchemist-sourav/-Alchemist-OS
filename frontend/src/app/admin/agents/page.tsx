"use client";

import React, { useEffect, useState } from "react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any>({});

  useEffect(() => {
    fetch("http://localhost:8000/admin/agents")
      .then(r => r.json())
      .then(data => setAgents(data.agents || {}))
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-white">Agent Health Monitoring</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.keys(agents).map((name) => {
          const agent = agents[name];
          return (
            <div key={name} className="bg-[#111] p-6 rounded-lg border border-gray-800 relative">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-medium text-white capitalize">{name.replace('_', ' ')}</h3>
                <span className="relative flex h-3 w-3">
                  {agent.active && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>}
                  <span className={`relative inline-flex rounded-full h-3 w-3 ${agent.active ? 'bg-green-500' : 'bg-red-500'}`}></span>
                </span>
              </div>
              
              <div className="flex flex-col gap-2 mt-4">
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Tasks Handled:</span>
                  <span className="text-white text-sm font-mono">{agent.task_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Failures:</span>
                  <span className="text-red-400 text-sm font-mono">{agent.failure_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Status:</span>
                  <span className="text-gray-300 text-sm">{agent.active ? 'Idle' : 'Offline'}</span>
                </div>
              </div>
            </div>
          );
        })}
        {Object.keys(agents).length === 0 && (
          <div className="col-span-full bg-[#111] p-6 rounded-lg border border-gray-800 text-center">
            <p className="text-gray-400">Loading agents or no agents running.</p>
          </div>
        )}
      </div>
    </div>
  );
}
