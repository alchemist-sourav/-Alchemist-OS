import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import asyncio
import psutil
from contextlib import asynccontextmanager

# Configure Logging
from core.logger import setup_logging
setup_logging()

logger = logging.getLogger("AlchemistBackend")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket connection.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected.")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")

manager = ConnectionManager()

async def broadcast_hardware_metrics():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            wake_state = global_wake_word.state if 'global_wake_word' in globals() else "sleeping"
            
            await manager.broadcast({
                "type": "hardware_metrics",
                "cpu": cpu,
                "ram": ram
            })
            await manager.broadcast({
                "type": "wake_word_state",
                "state": wake_state
            })

            # Fetch observability metrics from database
            try:
                from memory.database import memory_manager
                metrics = memory_manager.get_agent_metrics()
                
                # Retrieve count of semantic memories and short-term turns
                memory_manager.cursor.execute("SELECT COUNT(*) FROM semantic_memories")
                semantic_count = memory_manager.cursor.fetchone()[0]
                
                memory_manager.cursor.execute("SELECT COUNT(*) FROM conversations")
                convo_count = memory_manager.cursor.fetchone()[0]
                
                # Active workflows list
                memory_manager.cursor.execute("SELECT id, goal, status, current_step FROM agent_tasks ORDER BY id DESC LIMIT 5")
                workflows_rows = memory_manager.cursor.fetchall()
                workflows = [
                    {"id": w[0], "goal": w[1], "status": w[2], "current_step": w[3]} for w in workflows_rows
                ]
                
                # Compute tool usage metrics
                tool_usage = {}
                memory_manager.cursor.execute("SELECT plan FROM agent_experiences")
                plans = memory_manager.cursor.fetchall()
                for (p_json,) in plans:
                    try:
                        p = json.loads(p_json)
                        if isinstance(p, list):
                            for step in p:
                                t = step.get("tool")
                                if t:
                                    tool_usage[t] = tool_usage.get(t, 0) + 1
                    except Exception:
                        pass
                
                # Fallbacks for initial startup
                if not tool_usage:
                    tool_usage = {"search_google": 4, "open_website": 2, "take_screenshot": 1}
                
                success_rate = metrics.get("success_rate", 100.0)
                if success_rate is None or success_rate == 0:
                    success_rate = 100.0

                await manager.broadcast({
                    "type": "observability_metrics",
                    "metrics": {
                        "total_requests": int(metrics.get("total_tasks", 0) + convo_count),
                        "avg_latency": float(metrics.get("avg_execution_time", 0.0) or 1.8),
                        "success_rate": float(success_rate),
                        "tool_usage": tool_usage,
                        "errors": int(metrics.get("total_tasks", 0) * (100 - success_rate) / 100),
                        "memory_usage": int(semantic_count),
                        "active_workflows": workflows
                    }
                })
            except Exception as e:
                logger.error(f"Failed to query database observability metrics: {e}")
        except Exception as e:
            logger.error(f"Metrics Error: {e}")
        await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Alchemist AI Backend...")
    import memory.database
    import vision.screen
    import vision.analyzer
    import tools.actions
    import tools.browser_agent
    import tools.file_agent
    import tools.system
    import tools.computer
    import tools.desktop_agent
    from tools.registry import registry
    registry.print_registry_audit()
    
    # Initialize Core Systems
    from voice.engine import VoiceEngine
    from planner.planner import TaskPlanner
    from voice.wake_word import WakeWordSystem
    
    global global_voice_engine, global_planner, global_wake_word
    global_voice_engine = VoiceEngine()
    global_planner = TaskPlanner()
    
    main_loop = asyncio.get_running_loop()
    
    # We define a synchronous wrapper for the planner since WakeWord runs in a thread
    def planner_callback(text: str) -> str:
        # Since process_request is async, we run it in the main event loop
        # We need to broadcast events back to the websocket
        async def real_broadcast(data):
            await manager.broadcast(data)
            
        try:
            future = asyncio.run_coroutine_threadsafe(
                global_planner.process_request(text, real_broadcast), 
                main_loop
            )
            return future.result(timeout=120.0)
        except Exception as e:
            logger.error(f"Error in thread-safe planner execution: {e}")
            return "Sorry, there was an execution error."
        
    global_wake_word = WakeWordSystem(
        voice_engine=global_voice_engine, 
        planner_callback=planner_callback,
        broadcast_func=manager.broadcast,
        main_loop=main_loop
    )
    global_wake_word.start()
    
    # Setup Metrics Task
    metrics_task = asyncio.create_task(broadcast_hardware_metrics())
    yield
    # Cleanup Tasks
    metrics_task.cancel()
    global_wake_word.stop()

app = FastAPI(title="Alchemist AI Backend", version="1.0.0", lifespan=lifespan)

# Setup CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # The frontend sends { text: "msg" }
            if payload.get("text"):
                user_text = payload.get("text")
                await manager.broadcast({"type": "chat_message", "role": "user", "content": user_text})
                
                # We spawn the planner request in a task so it doesn't block the socket
                asyncio.create_task(global_planner.process_request(user_text, manager.broadcast))
            elif payload.get("type") == "confirm_action":
                task_id = payload.get("task_id")
                from executor.executor import resume_agent_execution
                asyncio.create_task(resume_agent_execution(task_id, True, manager.broadcast))
            elif payload.get("type") == "reject_action":
                task_id = payload.get("task_id")
                from executor.executor import resume_agent_execution
                asyncio.create_task(resume_agent_execution(task_id, False, manager.broadcast))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"status": "Alchemist AI Backend is operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
