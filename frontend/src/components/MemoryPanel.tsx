"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAlchemistOS } from "@/lib/WebSocketProvider";
import { MessageSquare, Activity, Brain } from "lucide-react";

export const MemoryPanel = () => {
  const { state } = useAlchemistOS();

  return (
    <div className="glass-panel h-full flex flex-col overflow-hidden p-4">
      {/* Header */}
      <div className="section-header mb-3">
        <Brain size={10} className="text-[#ff003c]" />
        MEMORY STREAM
      </div>

      {/* Goal */}
      <div className="mb-3">
        <div className="text-[9px] text-white/30 tracking-widest uppercase mb-1.5 font-mono">Active Goal</div>
        <div className="bg-black/30 border border-white/5 rounded p-2 min-h-[36px]">
          {state.activeGoal ? (
            <p className="text-[10px] text-[#ff003c] font-mono leading-relaxed">{state.activeGoal}</p>
          ) : (
            <p className="text-[10px] text-white/20 font-mono italic">No active goal</p>
          )}
        </div>
      </div>

      {/* Conversation */}
      <div className="mb-3 flex-shrink-0">
        <div className="text-[9px] text-white/30 tracking-widest uppercase mb-1.5 font-mono flex items-center gap-1.5">
          <MessageSquare size={9} />
          Conversation
        </div>
        <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1 scrollbar-hide">
          <AnimatePresence initial={false}>
            {state.conversation.length === 0 ? (
              <p className="text-[10px] text-white/20 italic font-mono">Awaiting first message...</p>
            ) : (
              [...state.conversation].reverse().map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <div className={`text-[9px] font-mono px-2 py-1.5 rounded max-w-[85%] leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[#ff003c]/15 border border-[#ff003c]/25 text-white/70 ml-auto"
                      : "bg-white/5 border border-white/8 text-white/60"
                  }`}>
                    <span className={`block text-[8px] mb-0.5 ${msg.role === "user" ? "text-[#ff003c]/70" : "text-white/30"}`}>
                      {msg.role === "user" ? "YOU" : "ALCHEMIST"}
                    </span>
                    {msg.content}
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="text-[9px] text-white/30 tracking-widest uppercase mb-1.5 font-mono flex items-center gap-1.5">
          <Activity size={9} />
          Activity Log
        </div>
        <div className="flex-1 overflow-y-auto space-y-0.5 pr-1 scrollbar-hide">
          <AnimatePresence initial={false}>
            {state.activityFeed.length === 0 ? (
              <p className="text-[10px] text-white/20 italic font-mono">No activity yet...</p>
            ) : (
              state.activityFeed.map((item, i) => (
                <motion.div
                  key={`${i}-${item}`}
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-[9px] font-mono text-white/40 flex items-start gap-1.5 py-0.5 border-b border-white/3"
                >
                  <span className="text-[#ff003c]/50 mt-0.5 flex-shrink-0">›</span>
                  <span>{item}</span>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
