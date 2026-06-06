"use client";

import React, { useEffect, useState } from "react";
import { AICoreOrb } from "@/components/AICoreOrb";
import { useAlchemistOS, WebSocketProvider } from "@/lib/WebSocketProvider";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Activity, Database, Terminal, Cpu, Eye } from "lucide-react";

const ConversationHistory = () => {
  const { state } = useAlchemistOS();
  
  return (
    <div className="glass-panel w-full h-full p-4 flex flex-col">
      <div className="flex items-center gap-2 mb-4 text-crimson-400 border-b border-glass-border pb-2">
        <Activity size={18} />
        <h2 className="font-mono text-sm tracking-widest uppercase">Comms Link</h2>
      </div>
      <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-hide">
        <AnimatePresence>
          {state.conversation.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className={`p-3 rounded-lg text-sm font-mono ${
                msg.role === "user" 
                  ? "bg-white/10 ml-auto border-r-2 border-white/30 text-right" 
                  : "bg-crimson-500/20 mr-auto border-l-2 border-crimson-500"
              }`}
              style={{ maxWidth: "80%" }}
            >
              {msg.content}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

const SystemPanel = () => {
  const { state } = useAlchemistOS();
  
  return (
    <div className="glass-panel w-full p-4 flex flex-col gap-4">
      <div className="flex items-center gap-2 text-crimson-400 border-b border-glass-border pb-2">
        <Cpu size={18} />
        <h2 className="font-mono text-sm tracking-widest uppercase">System Diagnostics</h2>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-black/40 p-3 rounded border border-glass-border">
          <div className="text-xs text-gray-400 uppercase font-mono mb-1">Status</div>
          <div className="text-crimson-400 font-mono text-lg uppercase text-glow">
            {state.orbState}
          </div>
        </div>
        <div className="bg-black/40 p-3 rounded border border-glass-border">
          <div className="text-xs text-gray-400 uppercase font-mono mb-1">Active Tool</div>
          <div className="text-white font-mono text-sm truncate">
            {state.currentTool || "None"}
          </div>
        </div>
        <div className="bg-black/40 p-3 rounded border border-glass-border">
          <div className="text-xs text-gray-400 uppercase font-mono mb-1">CPU Load</div>
          <div className="text-white font-mono text-sm">
            {state.hardware.cpu}%
          </div>
        </div>
        <div className="bg-black/40 p-3 rounded border border-glass-border">
          <div className="text-xs text-gray-400 uppercase font-mono mb-1">Memory</div>
          <div className="text-white font-mono text-sm">
            {state.hardware.ram}%
          </div>
        </div>
        <div className="bg-black/40 p-3 rounded border border-glass-border col-span-2">
          <div className="text-xs text-gray-400 uppercase font-mono mb-1">Wake Word</div>
          <div className="text-white text-sm flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${state.hardware.wakeWord === "listening" ? "bg-green-500 animate-pulse" : "bg-gray-500"}`}></span>
            {state.hardware.wakeWord}
          </div>
        </div>
      </div>
    </div>
  );
};

const VisionPanel = () => {
  const { state } = useAlchemistOS();
  
  return (
    <div className="glass-panel w-full p-4 flex flex-col gap-4">
      <div className="flex items-center gap-2 text-crimson-400 border-b border-glass-border pb-2">
        <Eye size={18} />
        <h2 className="font-mono text-sm tracking-widest uppercase">Visual Cortex</h2>
      </div>
      
      {state.vision.screenshot ? (
        <div className="w-full h-32 rounded border border-glass-border overflow-hidden relative">
          <img src={`data:image/jpeg;base64,${state.vision.screenshot}`} alt="screen" className="w-full h-full object-cover opacity-70" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end p-2">
            <span className="text-xs font-mono text-crimson-400">LIVE FEED ACTIVE</span>
          </div>
        </div>
      ) : (
        <div className="w-full h-32 rounded border border-glass-border bg-black/40 flex items-center justify-center font-mono text-xs text-gray-500">
          NO VISUAL DATA
        </div>
      )}

      <div className="bg-black/40 p-3 rounded border border-glass-border">
        <div className="text-xs text-gray-400 uppercase font-mono mb-1">Detected Apps</div>
        <div className="text-white text-xs truncate">
          {state.vision.applications.length > 0 ? state.vision.applications.join(", ") : "None"}
        </div>
      </div>
      
      <div className="bg-black/40 p-3 rounded border border-glass-border">
        <div className="text-xs text-gray-400 uppercase font-mono mb-1">Analysis</div>
        <div className="text-white text-xs line-clamp-2">
          {state.vision.summary}
        </div>
      </div>
    </div>
  );
};

const MemoryViewer = () => {
  const { state } = useAlchemistOS();
  return (
    <div className="glass-panel w-full flex-1 p-4 flex flex-col">
      <div className="flex items-center gap-2 mb-4 text-crimson-400 border-b border-glass-border pb-2">
        <Database size={18} />
        <h2 className="font-mono text-sm tracking-widest uppercase">Memory Banks</h2>
      </div>
      
      <div className="space-y-4 font-mono text-sm">
        <div className="flex justify-between items-center border-b border-white/10 pb-2">
          <span className="text-gray-400">Total Tasks Executed</span>
          <span className="text-crimson-400 text-glow">{state.metrics.total_tasks}</span>
        </div>
        <div className="flex justify-between items-center border-b border-white/10 pb-2">
          <span className="text-gray-400">Success Rate</span>
          <span className="text-white">{state.metrics.success_rate.toFixed(1)}%</span>
        </div>
        <div className="flex justify-between items-center border-b border-white/10 pb-2">
          <span className="text-gray-400">Avg Execution Time</span>
          <span className="text-white">{state.metrics.avg_execution_time.toFixed(2)}s</span>
        </div>
      </div>
    </div>
  );
};

const ActivityFeed = () => {
  const { state } = useAlchemistOS();
  return (
    <div className="glass-panel w-full h-full p-4 overflow-hidden flex flex-col">
      <div className="flex items-center gap-2 mb-2 text-crimson-400">
        <Terminal size={14} />
        <h2 className="font-mono text-xs tracking-widest uppercase">Terminal Feed</h2>
      </div>
      <div className="flex-1 overflow-y-auto space-y-1 font-mono text-xs text-green-400/80 scrollbar-hide">
        {state.activityFeed.map((log, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            &gt; {log}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

const VoiceInput = ({ audioLevel, onAudioLevel }: { audioLevel: number, onAudioLevel: (v: number) => void }) => {
  const { sendMessage, state } = useAlchemistOS();
  const [text, setText] = useState("");

  useEffect(() => {
    // Simple mock audio level generator when speaking/listening
    let interval: NodeJS.Timeout;
    if (state.orbState === "speaking" || state.orbState === "listening") {
      interval = setInterval(() => {
        onAudioLevel(Math.random() * 0.5);
      }, 100);
    } else {
      onAudioLevel(0);
    }
    return () => clearInterval(interval);
  }, [state.orbState, onAudioLevel]);

  return (
    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-1/3 flex flex-col items-center gap-4">
      {/* Voice Visualizer Waveform */}
      <div className="flex items-center justify-center gap-1 h-8">
        {[...Array(15)].map((_, i) => (
          <motion.div
            key={i}
            className="w-1 bg-crimson-500 rounded-full"
            animate={{
              height: state.orbState === "listening" || state.orbState === "speaking" 
                ? `${Math.max(4, audioLevel * 100)}px` 
                : "4px"
            }}
            transition={{ type: "tween", duration: 0.1 }}
          />
        ))}
      </div>
      
      <form 
        onSubmit={(e) => {
          e.preventDefault();
          if (text.trim()) {
            sendMessage(text);
            setText("");
          }
        }}
        className="glass-panel p-2 flex items-center gap-2"
      >
        <button type="button" className="p-2 text-crimson-500 hover:text-crimson-400 transition-colors">
          <Mic size={20} className={state.orbState === "listening" ? "animate-pulse" : ""} />
        </button>
        <input 
          type="text" 
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Command Alchemist..."
          className="flex-1 bg-transparent border-none outline-none font-mono text-sm text-white placeholder-gray-500"
        />
      </form>
    </div>
  );
};

const HUDLayout = () => {
  const [audioLevel, setAudioLevel] = useState(0);

  return (
    <div className="w-screen h-screen overflow-hidden p-6 grid grid-cols-12 grid-rows-6 gap-6">
      {/* Left Panel */}
      <div className="col-span-3 row-span-5 relative z-10">
        <ConversationHistory />
      </div>

      {/* Center Orb Area */}
      <div className="col-span-6 row-span-5 relative">
        <AICoreOrb audioLevel={audioLevel} />
        <VoiceInput audioLevel={audioLevel} onAudioLevel={setAudioLevel} />
      </div>

      {/* Right Panel */}
      <div className="col-span-3 row-span-5 flex flex-col gap-6 relative z-10 overflow-y-auto scrollbar-hide pr-2">
        <SystemPanel />
        <VisionPanel />
        <MemoryViewer />
      </div>

      {/* Bottom Panel */}
      <div className="col-span-12 row-span-1 relative z-10">
        <ActivityFeed />
      </div>
    </div>
  );
};

export default function Home() {
  return (
    <WebSocketProvider>
      <HUDLayout />
    </WebSocketProvider>
  );
}
