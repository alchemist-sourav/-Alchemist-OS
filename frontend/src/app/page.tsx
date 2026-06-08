"use client";

import React, { useState } from "react";
import { WebSocketProvider, useAlchemistOS } from "@/lib/WebSocketProvider";
import { TopBar } from "@/components/TopBar";
import { MemoryPanel } from "@/components/MemoryPanel";
import { StatusPanel } from "@/components/StatusPanel";
import { ExecutionConsole } from "@/components/ExecutionConsole";
import { AlchemistCore } from "@/components/AlchemistCore";
import { ExecutionTimeline } from "@/components/ExecutionTimeline";
import { AdminPanel } from "@/components/AdminPanel";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, AlertTriangle } from "lucide-react";

/* ─────────────────── Command Input ─────────────────── */
const CommandInput = () => {
  const { sendMessage, state } = useAlchemistOS();
  const [text, setText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      sendMessage(text);
      setText("");
    }
  };

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 w-full max-w-md px-4">
      <form onSubmit={handleSubmit}>
        <div className="glass-panel flex items-center gap-3 px-4 py-2.5 hover:border-deep-red/30 transition-all">
          {/* Mic icon */}
          <motion.div
            className="text-deep-red/60"
            animate={
              state.orbState === "listening"
                ? { scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }
                : {}
            }
            transition={{ duration: 1, repeat: Infinity }}
          >
            <Mic size={16} />
          </motion.div>

          {/* Input field */}
          <input
            id="command-input"
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Command Alchemist..."
            className="flex-1 bg-transparent border-none outline-none font-mono text-xs text-white/80 placeholder-white/20 tracking-wide"
          />

          {/* Send indicator */}
          {text.trim() && (
            <motion.button
              type="submit"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="font-mono text-[9px] tracking-[0.2em] text-deep-red/80 uppercase hover:text-deep-red transition-colors"
            >
              SEND
            </motion.button>
          )}
        </div>
      </form>
    </div>
  );
};

/* ─────────────────── Corner Decorations ─────────────────── */
const CornerDecor = ({ position }: { position: "tl" | "tr" | "bl" | "br" }) => {
  const classes: Record<string, string> = {
    tl: "top-0 left-0",
    tr: "top-0 right-0 rotate-90",
    bl: "bottom-0 left-0 -rotate-90",
    br: "bottom-0 right-0 rotate-180",
  };

  return (
    <div className={`absolute ${classes[position]} w-8 h-8 pointer-events-none z-30`}>
      <svg viewBox="0 0 32 32" className="w-full h-full opacity-20">
        <path
          d="M0 0 L12 0 L12 2 L2 2 L2 12 L0 12 Z"
          fill="#ff003c"
        />
      </svg>
    </div>
  );
};

/* ─────────────────── Main HUD Layout ─────────────────── */
const AlchemistHUD = () => {
  const [activeTab, setActiveTab] = useState<"hud" | "admin">("hud");
  const { state, confirmAction } = useAlchemistOS();

  return (
    <div className="w-screen h-screen overflow-hidden flex flex-col relative bg-[#050505] text-white">
      {/* Corner decorations */}
      <CornerDecor position="tl" />
      <CornerDecor position="tr" />
      <CornerDecor position="bl" />
      <CornerDecor position="br" />

      {/* Top Bar */}
      <TopBar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Interactive Permission Authorization Overlay */}
      <AnimatePresence>
        {state.pendingConfirmation && (
          <motion.div
            className="absolute inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono select-none"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="glass-panel max-w-md w-full p-6 border-deep-red flex flex-col gap-4 text-center"
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
            >
              <div className="flex justify-center text-deep-red">
                <AlertTriangle size={36} className="animate-bounce" />
              </div>
              <h2 className="text-xs font-bold tracking-[0.2em] text-deep-red">PROTECTED ACTION AUTHORIZATION REQUIRED</h2>
              <p className="text-[10px] text-white/70 leading-relaxed">
                {state.pendingConfirmation.message}
              </p>
              <div className="bg-black/40 border border-white/5 p-3 rounded text-[9px] text-left text-white/50 flex flex-col gap-1">
                <div><span className="text-white/30 font-bold">TOOL:</span> {state.pendingConfirmation.tool}</div>
                <div><span className="text-white/30 font-bold">ARGS:</span> {JSON.stringify(state.pendingConfirmation.args)}</div>
              </div>
              <div className="flex gap-3 mt-2 text-[10px]">
                <button
                  onClick={() => confirmAction(state.pendingConfirmation!.task_id, true)}
                  className="flex-1 bg-green-500/20 hover:bg-green-500/35 border border-green-500/40 text-green-400 py-2.5 rounded transition-all cursor-pointer font-bold tracking-widest"
                >
                  CONFIRM ACTION
                </button>
                <button
                  onClick={() => confirmAction(state.pendingConfirmation!.task_id, false)}
                  className="flex-1 bg-deep-red/25 hover:bg-deep-red/40 border border-deep-red/50 text-white py-2.5 rounded transition-all cursor-pointer font-bold tracking-widest"
                >
                  ABORT
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content area */}
      <div className="flex-1 flex gap-4 px-4 pb-2 min-h-0">
        {/* Left Panel — Memory */}
        <motion.div
          className="w-[260px] flex-shrink-0 relative z-10"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <MemoryPanel />
        </motion.div>

        {/* Center content: Swaps between Core HUD and Observability Dashboard */}
        <div className="flex-1 relative flex flex-col min-h-0">
          <AnimatePresence mode="wait">
            {activeTab === "hud" ? (
              <motion.div
                key="hud-core"
                className="flex-1 relative w-full h-full"
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ duration: 0.4 }}
              >
                <AlchemistCore />
                <ExecutionTimeline />
                <CommandInput />
              </motion.div>
            ) : (
              <motion.div
                key="admin-dashboard"
                className="flex-1 relative w-full h-full"
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ duration: 0.4 }}
              >
                <AdminPanel />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Panel — System Status */}
        <motion.div
          className="w-[260px] flex-shrink-0 relative z-10"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <StatusPanel />
        </motion.div>
      </div>

      {/* Bottom Panel — Execution Console */}
      <motion.div
        className="h-[130px] flex-shrink-0 px-4 pb-3 relative z-10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <ExecutionConsole />
      </motion.div>
    </div>
  );
};

/* ─────────────────── Page Entry ─────────────────── */
export default function Home() {
  return (
    <WebSocketProvider>
      <AlchemistHUD />
    </WebSocketProvider>
  );
}
