"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAlchemistOS } from "@/lib/WebSocketProvider";
import { GitCommitHorizontal } from "lucide-react";

const STEP_COLOR: Record<string, string> = {
  "Plan Created": "bg-blue-500",
  "Running":      "bg-yellow-500",
  "Completed":    "bg-green-500",
  "Action pending": "bg-[#ff003c]",
  "Vision":       "bg-purple-500",
};

function getStepColor(msg: string) {
  for (const [k, c] of Object.entries(STEP_COLOR)) {
    if (msg.startsWith(k)) return c;
  }
  return "bg-white/30";
}

export const ExecutionTimeline = () => {
  const { state } = useAlchemistOS();
  const recent = state.activityFeed.slice(0, 5).reverse();

  if (recent.length === 0 && !state.activeGoal) return null;

  return (
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
      <div className="glass-panel px-4 py-2 flex items-center gap-3 max-w-[440px]">
        <GitCommitHorizontal size={10} className="text-[#ff003c] flex-shrink-0" />
        <div className="flex items-center gap-2 overflow-hidden">
          <AnimatePresence mode="popLayout">
            {recent.length > 0 ? (
              recent.map((step, i) => (
                <motion.div
                  key={`${i}-${step}`}
                  initial={{ opacity: 0, scale: 0.7, width: 0 }}
                  animate={{ opacity: i === recent.length - 1 ? 1 : 0.35, scale: 1, width: "auto" }}
                  exit={{ opacity: 0, scale: 0.7, width: 0 }}
                  className="flex items-center gap-1.5 flex-shrink-0"
                >
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${getStepColor(step)}`} />
                  {i === recent.length - 1 && (
                    <span className="text-[9px] font-mono text-white/60 truncate max-w-[200px]">
                      {step}
                    </span>
                  )}
                  {i < recent.length - 1 && (
                    <span className="text-white/10 text-[9px]">→</span>
                  )}
                </motion.div>
              ))
            ) : (
              <motion.span
                key="awaiting"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-[9px] font-mono text-white/30 tracking-widest uppercase"
              >
                Awaiting Command
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
