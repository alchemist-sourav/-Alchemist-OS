"use client";

import React, { useEffect, useState } from "react";

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/admin/tasks")
      .then(r => r.json())
      .then(data => setTasks(data.tasks || []))
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-white">Task Timeline</h2>
      
      <div className="flex flex-col gap-4">
        {tasks.map((task: any) => (
          <div key={task.id} className="bg-[#111] p-6 rounded-lg border border-gray-800">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-1">Task #{task.id}</h3>
                <p className="text-gray-400 text-sm">Goal: {task.goal}</p>
              </div>
              <span className={`px-2 py-1 rounded text-xs capitalize ${task.status === 'completed' ? 'bg-green-900 text-green-300' : task.status === 'failed' ? 'bg-red-900 text-red-300' : 'bg-blue-900 text-blue-300'}`}>
                {task.status}
              </span>
            </div>
            
            <div className="mt-4 border-l-2 border-gray-700 ml-2 pl-4 flex flex-col gap-4">
              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-3 h-3 bg-blue-500 rounded-full"></div>
                <p className="text-xs text-gray-500">User Request</p>
                <p className="text-sm text-gray-300">{task.goal}</p>
              </div>
              
              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-3 h-3 bg-purple-500 rounded-full"></div>
                <p className="text-xs text-gray-500">Planner</p>
                <p className="text-sm text-gray-300">Generated {task.timeline?.length || 0} steps</p>
              </div>

              {task.timeline?.map((step: any, i: number) => (
                <div key={i} className="relative">
                  <div className="absolute -left-[21px] top-1 w-3 h-3 bg-gray-500 rounded-full"></div>
                  <p className="text-xs text-gray-500">Step {i + 1}: {step.tool}</p>
                  <p className="text-sm text-gray-300 font-mono text-xs mt-1 bg-[#1a1a1a] p-2 rounded">
                    {JSON.stringify(step.args)}
                  </p>
                </div>
              ))}
              
              <div className="relative">
                <div className="absolute -left-[21px] top-1 w-3 h-3 bg-green-500 rounded-full"></div>
                <p className="text-xs text-gray-500">Result</p>
                <p className="text-sm text-gray-300 capitalize">{task.status}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
