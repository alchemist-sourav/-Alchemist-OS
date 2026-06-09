"use client";

import React, { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAlchemistOS } from "@/lib/WebSocketProvider";
import { Terminal } from "lucide-react";

const LOG_PREFIX_COLORS: Record<string, string> = {
  "Plan Created":    "text-blue-400",
  "Running":         "text-yellow-400",
  "Completed":       "text-green-400",
  "Action pending":  "text-[#ff003c]",
  "Vision Analyzed": "text-purple-400",
};

function getLogColor(msg: string) {
  for (const [key, cls] of Object.entries(LOG_PREFIX_COLORS)) {
    if (msg.startsWith(key)) return cls;
  }
  return "text-white/40";
}

function getLogPrefix(msg: string) {
  if (msg.startsWith("Plan")) return "[PLAN]";
  if (msg.startsWith("Running")) return "[EXEC]";
  if (msg.startsWith("Completed")) return "[DONE]";
  if (msg.startsWith("Action pending")) return "[AUTH]";
  if (msg.startsWith("Vision")) return "[VISI]";
  return "[INFO]";
}

export const ExecutionConsole = () => {
  const { state } = useAlchemistOS();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.activityFeed]);

  const allLogs = [
    { msg: "Alchemist OS initialized", color: "text-green-400/80", prefix: "[BOOT]" },
    { msg: "WebSocket bridge established", color: "text-green-400/60", prefix: "[BOOT]" },
    { msg: "Memory systems online", color: "text-green-400/60", prefix: "[BOOT]" },
    ...state.activityFeed.slice().reverse().map((msg) => ({
      msg,
      color: getLogColor(msg),
      prefix: getLogPrefix(msg),
    })),
  ];

  return (
    <div className="glass-panel h-full flex flex-col overflow-hidden p-3">
      {/* Header */}
      <div className="section-header mb-2 pb-1.5">
        <Terminal size={10} className="text-[#ff003c]" />
        EXECUTION LOG
        {state.status !== "idle" && (
          <span className="ml-auto flex items-center gap-1.5 text-[8px] text-[#ff003c] animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-[#ff003c] inline-block" />
            LIVE
          </span>
        )}
      </div>

      {/* Scrollable log */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-0.5 font-mono scrollbar-hide"
      >
        <AnimatePresence initial={false}>
          {allLogs.map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className="flex items-start gap-2 text-[9px] leading-relaxed"
            >
              <span className="text-white/20 flex-shrink-0">{String(i).padStart(3, "0")}</span>
              <span className={`flex-shrink-0 font-bold ${log.color}`}>{log.prefix}</span>
              <span className={log.color}>{log.msg}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};
