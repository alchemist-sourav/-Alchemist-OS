"use client";

import React from "react";
import { motion } from "framer-motion";
import { useAlchemistOS } from "@/lib/WebSocketProvider";
import { BarChart3, Zap, Clock, CheckCircle, AlertTriangle, Layers, TrendingUp } from "lucide-react";

const GaugeBar = ({
  label,
  value,
  max,
  unit,
  color,
}: {
  label: string;
  value: number;
  max: number;
  unit: string;
  color: string;
}) => {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between">
        <span className="text-[9px] font-mono text-white/40 uppercase tracking-widest">{label}</span>
        <span className="text-[10px] font-mono font-bold" style={{ color }}>
          {typeof value === "number" && !Number.isInteger(value) ? value.toFixed(1) : value}
          {unit}
        </span>
      </div>
      <div className="h-1 bg-white/10 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
};

export const AdminPanel = () => {
  const { state } = useAlchemistOS();
  const obs = state.observability;

  return (
    <div className="w-full h-full flex flex-col gap-4 overflow-y-auto pr-1 scrollbar-hide">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-[#ff003c] animate-pulse" />
        <h2 className="text-xs font-mono font-bold text-[#ff003c] tracking-[0.25em] uppercase">
          Admin Dashboard
        </h2>
        <span className="ml-auto text-[9px] font-mono text-white/20 uppercase tracking-widest">
          LIVE
        </span>
      </div>

      {/* Top stats row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total Tasks", value: state.metrics.total_tasks, icon: Layers, color: "#ff003c" },
          { label: "Success Rate", value: `${(state.metrics.success_rate * 100).toFixed(0)}%`, icon: CheckCircle, color: "#00ff88" },
          { label: "Avg Time", value: `${state.metrics.avg_execution_time.toFixed(1)}s`, icon: Clock, color: "#ffaa00" },
          { label: "Errors", value: obs?.errors ?? 0, icon: AlertTriangle, color: "#ff4d4d" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="glass-panel p-3 flex flex-col gap-1">
            <div className="flex items-center gap-1.5">
              <Icon size={10} style={{ color }} />
              <span className="text-[8px] font-mono text-white/30 uppercase tracking-widest">{label}</span>
            </div>
            <span className="text-lg font-mono font-bold" style={{ color }}>{value}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Observability */}
        <div className="glass-panel p-4 flex flex-col gap-3">
          <div className="section-header">
            <BarChart3 size={10} />
            Observability Metrics
          </div>
          {obs ? (
            <div className="space-y-3">
              <GaugeBar label="Requests" value={obs.total_requests} max={Math.max(obs.total_requests, 100)} unit="" color="#ff003c" />
              <GaugeBar label="Avg Latency" value={obs.avg_latency} max={10} unit="s" color="#ffaa00" />
              <GaugeBar label="Success Rate" value={obs.success_rate * 100} max={100} unit="%" color="#00ff88" />
              <GaugeBar label="Memory" value={obs.memory_usage} max={100} unit="%" color="#a78bfa" />
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-[10px] font-mono text-white/25 text-center">
                No observability data yet.<br />
                <span className="text-[9px] text-white/15">Data populates during execution.</span>
              </p>
            </div>
          )}
        </div>

        {/* Tool Usage */}
        <div className="glass-panel p-4 flex flex-col gap-3">
          <div className="section-header">
            <Zap size={10} />
            Tool Usage
          </div>
          {obs && Object.keys(obs.tool_usage).length > 0 ? (
            <div className="space-y-2 overflow-y-auto scrollbar-hide">
              {Object.entries(obs.tool_usage)
                .sort(([, a], [, b]) => b - a)
                .map(([tool, count]) => {
                  const max = Math.max(...Object.values(obs.tool_usage));
                  const pct = (count / max) * 100;
                  return (
                    <div key={tool} className="space-y-0.5">
                      <div className="flex justify-between">
                        <span className="text-[9px] font-mono text-white/50">{tool}</span>
                        <span className="text-[9px] font-mono text-[#ff003c]">{count}x</span>
                      </div>
                      <div className="h-1 bg-white/8 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full rounded-full bg-[#ff003c]/60"
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.6 }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-[10px] font-mono text-white/25 text-center">
                No tool usage data.<br />
                <span className="text-[9px] text-white/15">Populates as tools execute.</span>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Active Workflows */}
      <div className="glass-panel p-4 flex flex-col gap-3">
        <div className="section-header">
          <TrendingUp size={10} />
          Active Workflows
        </div>
        {obs && obs.active_workflows.length > 0 ? (
          <div className="space-y-2">
            {obs.active_workflows.map((wf) => (
              <div key={wf.id} className="flex items-center gap-4 p-2 bg-black/30 border border-white/5 rounded">
                <span className="text-[9px] font-mono text-white/30">#{wf.id}</span>
                <span className="text-[10px] font-mono text-white/60 flex-1 truncate">{wf.goal}</span>
                <span className="text-[9px] font-mono text-white/30">Step {wf.current_step}</span>
                <span className={`text-[8px] font-mono px-2 py-0.5 rounded ${
                  wf.status === "executing" ? "bg-[#ff003c]/20 text-[#ff003c]" : "bg-white/5 text-white/30"
                }`}>
                  {wf.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[10px] font-mono text-white/25">
            No active workflows. Issue a command to create one.
          </p>
        )}
      </div>
    </div>
  );
};
