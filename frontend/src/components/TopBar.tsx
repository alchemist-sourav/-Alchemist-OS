"use client";

import React from "react";
import { motion } from "framer-motion";
import { useAlchemistOS } from "@/lib/WebSocketProvider";
import { LayoutGrid } from "lucide-react";

interface TopBarProps {
  activeTab: "hud" | "admin";
  setActiveTab: (tab: "hud" | "admin") => void;
}

const STATE_LABELS: Record<string, { label: string; color: string }> = {
  idle:      { label: "STANDBY",   color: "text-white/30" },
  listening: { label: "LISTENING", color: "text-green-400" },
  thinking:  { label: "THINKING",  color: "text-blue-400"  },
  speaking:  { label: "SPEAKING",  color: "text-cyan-400"  },
  executing: { label: "EXECUTING", color: "text-[#ff003c]" },
};

export const TopBar: React.FC<TopBarProps> = ({ activeTab, setActiveTab }) => {
  const { state } = useAlchemistOS();
  const orbLabel = STATE_LABELS[state.orbState] ?? STATE_LABELS.idle;

  return (
    <header className="flex-shrink-0 h-14 flex items-center px-5 border-b border-[#ff003c]/15 bg-black/30 backdrop-blur-sm relative z-20">
      {/* Logo */}
      <div className="flex items-center gap-2.5">
        <div className="w-5 h-5 border border-[#ff003c]/60 flex items-center justify-center">
          <div className="w-2 h-2 bg-[#ff003c]" />
        </div>
        <span className="text-sm font-bold tracking-[0.3em] text-white uppercase font-mono">
          Alchemist <span className="text-[#ff003c]">OS</span>
        </span>
      </div>

      {/* Center — orb state */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
        <span className={`relative flex h-2 w-2`}>
          {state.orbState !== "idle" && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ff003c] opacity-75" />
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${state.orbState !== "idle" ? "bg-[#ff003c]" : "bg-white/15"}`} />
        </span>
        <span className={`text-[10px] font-mono font-bold tracking-[0.25em] ${orbLabel.color}`}>
          {orbLabel.label}
        </span>
      </div>

      {/* Right — tabs */}
      <div className="ml-auto flex items-center gap-1.5">
        <LayoutGrid size={12} className="text-white/20 mr-1.5" />
        {(["hud", "admin"] as const).map((tab) => (
          <motion.button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`relative px-3 py-1 text-[9px] font-mono font-bold tracking-[0.2em] uppercase transition-colors cursor-pointer ${
              activeTab === tab ? "text-white" : "text-white/30 hover:text-white/60"
            }`}
          >
            {activeTab === tab && (
              <motion.div
                layoutId="topbar-indicator"
                className="absolute inset-0 border border-[#ff003c]/50 rounded-sm bg-[#ff003c]/10"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10">{tab}</span>
          </motion.button>
        ))}
      </div>
    </header>
  );
};
