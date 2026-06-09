"use client";

import React from "react";
import { motion } from "framer-motion";
import { useAlchemistOS } from "@/lib/WebSocketProvider";
import { Cpu, MemoryStick, Mic, Eye, Radio, Wrench, CheckCircle, XCircle } from "lucide-react";

const MetricBar = ({ value, max = 100, color = "#ff003c" }: { value: number; max?: number; color?: string }) => {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
      <motion.div
        className="h-full rounded-full"
        style={{ backgroundColor: color }}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </div>
  );
};

const StatRow = ({ label, value, color = "text-white/60" }: { label: string; value: string | number; color?: string }) => (
  <div className="flex justify-between items-center py-1 border-b border-white/5">
    <span className="text-[9px] text-white/30 font-mono uppercase tracking-widest">{label}</span>
    <span className={`text-[10px] font-mono font-bold ${color}`}>{value}</span>
  </div>
);

export const StatusPanel = () => {
  const { state } = useAlchemistOS();

  const statusColor: Record<string, string> = {
    idle: "text-white/40",
    listening: "text-green-400",
    stt: "text-yellow-400",
    planning: "text-blue-400",
    executing: "text-[#ff003c]",
    reflection: "text-purple-400",
    tts: "text-cyan-400",
  };

  const cpuColor = state.hardware.cpu > 80 ? "#ff3333" : state.hardware.cpu > 50 ? "#ffaa00" : "#00ff88";
  const ramColor = state.hardware.ram > 80 ? "#ff3333" : state.hardware.ram > 50 ? "#ffaa00" : "#00ff88";

  return (
    <div className="glass-panel h-full flex flex-col overflow-hidden p-4">
      {/* Header */}
      <div className="section-header mb-3">
        <Radio size={10} className="text-[#ff003c]" />
        SYSTEM STATUS
      </div>

      {/* Status Badge */}
      <div className="mb-3">
        <div className="bg-black/40 border border-white/5 rounded p-3 flex items-center gap-3">
          <span className="relative flex h-2.5 w-2.5">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              state.status === "idle" ? "bg-white/20" : "bg-[#ff003c]"
            }`} />
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
              state.status === "idle" ? "bg-white/30" : "bg-[#ff003c]"
            }`} />
          </span>
          <div>
            <div className="text-[8px] text-white/30 font-mono uppercase tracking-widest">System State</div>
            <div className={`text-[11px] font-mono font-bold uppercase tracking-widest ${statusColor[state.status] ?? "text-white/60"}`}>
              {state.status}
            </div>
          </div>
        </div>
      </div>

      {/* Current Tool */}
      {state.currentTool && (
        <div className="mb-3">
          <div className="text-[9px] text-white/30 tracking-widest uppercase mb-1.5 font-mono flex items-center gap-1.5">
            <Wrench size={9} /> Active Tool
          </div>
          <div className="bg-[#ff003c]/10 border border-[#ff003c]/25 rounded p-2">
            <span className="text-[10px] font-mono text-[#ff003c]">{state.currentTool}</span>
          </div>
        </div>
      )}

      {/* Hardware */}
      <div className="mb-3">
        <div className="text-[9px] text-white/30 tracking-widest uppercase mb-2 font-mono flex items-center gap-1.5">
          <Cpu size={9} /> Hardware
        </div>
        <div className="space-y-2">
          <div>
            <div className="flex justify-between mb-0.5">
              <span className="text-[9px] text-white/30 font-mono">CPU</span>
              <span className="text-[9px] font-mono" style={{ color: cpuColor }}>{state.hardware.cpu.toFixed(1)}%</span>
            </div>
            <MetricBar value={state.hardware.cpu} color={cpuColor} />
          </div>
          <div>
            <div className="flex justify-between mb-0.5">
              <span className="text-[9px] text-white/30 font-mono">RAM</span>
              <span className="text-[9px] font-mono" style={{ color: ramColor }}>{state.hardware.ram.toFixed(1)}%</span>
            </div>
            <MetricBar value={state.hardware.ram} color={ramColor} />
          </div>
        </div>
      </div>

      {/* Peripherals */}
      <div className="mb-3">
        <div className="text-[9px] text-white/30 tracking-widest uppercase mb-2 font-mono">Peripherals</div>
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[9px] text-white/40 font-mono">
              <Mic size={9} /> MIC
            </div>
            <span className={`text-[9px] font-mono ${state.hardware.mic === "listening" ? "text-green-400" : "text-white/30"}`}>
              {state.hardware.mic}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[9px] text-white/40 font-mono">
              <Eye size={9} /> WAKE WORD
            </div>
            <span className={`text-[9px] font-mono ${state.hardware.wakeWord === "active" ? "text-[#ff003c]" : "text-white/30"}`}>
              {state.hardware.wakeWord}
            </span>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="mb-3">
        <div className="text-[9px] text-white/30 tracking-widest uppercase mb-2 font-mono">Performance</div>
        <StatRow label="Tasks" value={state.metrics.total_tasks} />
        <StatRow
          label="Success"
          value={`${(state.metrics.success_rate * 100).toFixed(0)}%`}
          color={state.metrics.success_rate > 0.8 ? "text-green-400" : "text-yellow-400"}
        />
        <StatRow label="Avg Time" value={`${state.metrics.avg_execution_time.toFixed(1)}s`} />
      </div>

      {/* Vision */}
      <div className="flex-1">
        <div className="text-[9px] text-white/30 tracking-widest uppercase mb-2 font-mono flex items-center gap-1.5">
          <Eye size={9} /> Vision
        </div>
        <div className="bg-black/30 border border-white/5 rounded p-2">
          <p className="text-[9px] text-white/40 font-mono leading-relaxed">
            {state.vision.summary || "No visual data captured yet."}
          </p>
          {state.vision.applications.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {state.vision.applications.slice(0, 4).map((app) => (
                <span key={app} className="text-[8px] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-white/40 font-mono">
                  {app}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
