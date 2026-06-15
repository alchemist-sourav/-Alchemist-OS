"use client";

import React, { useEffect, useState } from "react";

export default function ErrorsPage() {
  const [errors, setErrors] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/admin/errors")
      .then(r => r.json())
      .then(data => setErrors(data.errors || []))
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-white">Error Tracking</h2>
      
      <div className="flex flex-col gap-4">
        {errors.map((err: any) => (
          <div key={err.id} className="bg-[#111] p-6 rounded-lg border border-red-900/50">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-medium text-red-400 mb-1">{err.exception_type || "Unknown Error"}</h3>
                <p className="text-gray-400 text-sm">Component: {err.component}</p>
                <p className="text-gray-500 text-xs mt-1">{new Date(err.timestamp).toLocaleString()}</p>
              </div>
            </div>
            
            <div className="mt-4">
              <p className="text-sm text-gray-300 font-medium mb-2">Context:</p>
              <p className="text-sm text-gray-400 bg-[#1a1a1a] p-3 rounded">{err.request_context}</p>
            </div>

            {err.stack_trace && (
              <div className="mt-4">
                <p className="text-sm text-gray-300 font-medium mb-2">Stack Trace:</p>
                <pre className="text-xs text-red-300 bg-[#1a1a1a] p-3 rounded overflow-x-auto whitespace-pre-wrap font-mono">
                  {err.stack_trace}
                </pre>
              </div>
            )}
          </div>
        ))}
        {errors.length === 0 && (
          <div className="bg-[#111] p-6 rounded-lg border border-gray-800 text-center">
            <p className="text-gray-400">No errors logged yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
