"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export type OrbState = "idle" | "listening" | "thinking" | "speaking" | "executing";

export interface SystemState {
  orbState: OrbState;
  activeGoal: string | null;
  currentTool: string | null;
  metrics: {
    total_tasks: number;
    success_rate: number;
    avg_execution_time: number;
  };
  activityFeed: string[];
  conversation: { role: string; content: string }[];
  hardware: {
    cpu: number;
    ram: number;
    wakeWord: string;
    mic: string;
  };
  vision: {
    screenshot: string | null;
    applications: string[];
    summary: string;
  };
}

const initialState: SystemState = {
  orbState: "idle",
  activeGoal: null,
  currentTool: null,
  metrics: { total_tasks: 0, success_rate: 0, avg_execution_time: 0 },
  activityFeed: [],
  conversation: [],
  hardware: { cpu: 0, ram: 0, wakeWord: "sleeping", mic: "listening" },
  vision: { screenshot: null, applications: [], summary: "No recent visual data." }
};

interface WebSocketContextType {
  state: SystemState;
  sendMessage: (msg: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const WebSocketProvider = ({ children }: { children: React.ReactNode }) => {
  const [state, setState] = useState<SystemState>(initialState);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const handleIncomingMessage = (data: Record<string, unknown>) => {
    setState((prev) => {
      const newState = { ...prev };
      
      switch (data.type) {
        case "plan_created":
          newState.orbState = "thinking";
          newState.activeGoal = data.goal as string;
          newState.activityFeed = [`Plan Created: ${data.goal}`, ...prev.activityFeed].slice(0, 50);
          break;
        case "step_start":
          newState.orbState = "executing";
          newState.currentTool = data.step as string;
          newState.activityFeed = [`Running ${data.step}...`, ...prev.activityFeed].slice(0, 50);
          break;
        case "step_complete":
          newState.orbState = "idle";
          newState.currentTool = null;
          newState.activityFeed = [`Completed ${data.step}`, ...prev.activityFeed].slice(0, 50);
          break;
        case "speech_start":
          newState.orbState = "speaking";
          break;
        case "speech_end":
          newState.orbState = "idle";
          break;
        case "chat_message":
          newState.conversation = [...prev.conversation, { role: data.role as string, content: data.content as string }].slice(-20);
          break;
        case "metrics_update":
          newState.metrics = data.metrics as SystemState["metrics"];
          break;
        case "hardware_metrics":
          newState.hardware = { ...newState.hardware, cpu: data.cpu as number, ram: data.ram as number };
          break;
        case "vision_update":
          newState.vision = { 
            screenshot: data.screenshot as string, 
            applications: data.applications as string[], 
            summary: data.summary as string 
          };
          newState.activityFeed = [`Vision Analyzed: ${(data.applications as string[]).join(", ")}`, ...prev.activityFeed].slice(0, 50);
          break;
        case "wake_word_state":
          newState.hardware.wakeWord = data.state as string;
          break;
      }
      return newState;
    });
  };

  useEffect(() => {
    // Connect to Alchemist Backend
    const socket = new WebSocket("ws://localhost:8000/ws");
    
    socket.onopen = () => {
      console.log("Connected to Alchemist OS");
      setWs(socket);
      // Fetch initial state if backend supports it
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingMessage(data);
      } catch (e) {
        console.error("Failed to parse socket message", e);
      }
    };

    socket.onclose = () => {
      console.log("Disconnected from Alchemist OS");
      setWs(null);
    };

    return () => {
      socket.close();
    };
  }, []);



  const sendMessage = (msg: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ text: msg }));
      setState(prev => ({
        ...prev,
        orbState: "thinking",
        conversation: [...prev.conversation, { role: "user", content: msg }]
      }));
    }
  };

  return (
    <WebSocketContext.Provider value={{ state, sendMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useAlchemistOS = () => {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error("useAlchemistOS must be used within WebSocketProvider");
  return ctx;
};
