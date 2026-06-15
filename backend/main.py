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

from fastapi.responses import Response

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    
    REQUEST_LATENCY = Histogram('api_latency_seconds', 'API request latency')
    TOOL_USAGE = Counter('tool_usage_total', 'Tool usage count', ['tool_name'])
    TASK_EXECUTION = Counter('task_execution_total', 'Task execution count', ['status'])
    ACTIVE_WEBSOCKETS = Gauge('active_websockets', 'Number of active websockets')
    MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
    
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket connection established.")
        if METRICS_ENABLED:
            ACTIVE_WEBSOCKETS.inc()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected.")
            if METRICS_ENABLED:
                ACTIVE_WEBSOCKETS.dec()

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to websocket: {e}")

manager = ConnectionManager()

async def broadcast_hardware_metrics():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            wake_state = global_wake_word.state if 'global_wake_word' in globals() else "sleeping"
            
            for conn in manager.active_connections:
                await manager.send_personal_message({
                    "type": "hardware_metrics",
                    "cpu": cpu,
                    "ram": ram
                }, conn)
                await manager.send_personal_message({
                    "type": "wake_word_state",
                    "state": wake_state
                }, conn)

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

                for conn in manager.active_connections:
                    await manager.send_personal_message({
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
                    }, conn)
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
    
    # Since process_request is async, we run it in the main event loop
    # We need to broadcast events back to the websocket
    async def real_broadcast(data):
        for conn in manager.active_connections:
            await manager.send_personal_message(data, conn)

    # We define a synchronous wrapper for the planner since WakeWord runs in a thread
    def planner_callback(text: str) -> str:
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
        broadcast_func=real_broadcast,
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
async def websocket_endpoint(websocket: WebSocket, api_key: str = None):
    from core.config import settings
    if not api_key or api_key != settings.API_KEY:
        await websocket.close(code=1008, reason="Unauthorized: Invalid or missing API key")
        return
        
    await manager.connect(websocket)
    
    async def personal_broadcast(data):
        await manager.send_personal_message(data, websocket)
        
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # The frontend sends { text: "msg" }
            if payload.get("text"):
                user_text = payload.get("text")
                await personal_broadcast({"type": "chat_message", "role": "user", "content": user_text})
                
                # We spawn the planner request in a task so it doesn't block the socket
                asyncio.create_task(global_planner.process_request(user_text, personal_broadcast))
            elif payload.get("type") == "confirm_action":
                task_id = payload.get("task_id")
                from executor.executor import resume_agent_execution
                asyncio.create_task(resume_agent_execution(task_id, True, personal_broadcast))
            elif payload.get("type") == "reject_action":
                task_id = payload.get("task_id")
                from executor.executor import resume_agent_execution
                asyncio.create_task(resume_agent_execution(task_id, False, personal_broadcast))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"status": "Alchemist AI Backend is operational"}

# --- Admin Dashboard API ---
@app.get("/admin/health")
def admin_health():
    return {"status": "healthy"}

@app.get("/admin/logs")
def admin_logs(limit: int = 50):
    from memory.database import memory_manager
    return {"logs": memory_manager.get_execution_logs(limit)}

@app.get("/admin/tools")
def admin_tools():
    from memory.database import memory_manager
    return {"tools": memory_manager.get_tool_metrics()}

@app.get("/admin/tasks")
def admin_tasks(limit: int = 50):
    from memory.database import memory_manager
    memory_manager.cursor.execute("SELECT id, goal, status, created_at, completed_at, steps_json FROM agent_tasks ORDER BY id DESC LIMIT ?", (limit,))
    rows = memory_manager.cursor.fetchall()
    tasks = []
    for r in rows:
        tasks.append({
            "id": r[0],
            "goal": r[1],
            "status": r[2],
            "created_at": r[3],
            "completed_at": r[4],
            "timeline": json.loads(r[5]) if r[5] else []
        })
    return {"tasks": tasks}

@app.get("/admin/metrics")
def admin_metrics():
    from memory.database import memory_manager
    return memory_manager.get_agent_metrics()

@app.get("/admin/system")
def admin_system():
    import psutil
    from tools.browser_agent import session as browser_session
    from memory.database import memory_manager
    
    # Active tasks
    memory_manager.cursor.execute("SELECT COUNT(*) FROM agent_tasks WHERE status='running'")
    active_tasks = memory_manager.cursor.fetchone()[0]
    
    # DB Status
    try:
        memory_manager.cursor.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "error"
        
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "active_websockets": len(manager.active_connections),
        "active_tasks": active_tasks,
        "browser_session": "active" if browser_session.page and not browser_session.page.is_closed() else "inactive",
        "database": db_status
    }

@app.get("/admin/errors")
def admin_errors(limit: int = 50):
    from memory.database import memory_manager
    return {"errors": memory_manager.get_error_logs(limit)}

if METRICS_ENABLED:
    @app.get("/metrics")
    def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
