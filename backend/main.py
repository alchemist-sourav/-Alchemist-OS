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
    from tools.registry import registry
    registry.print_registry_audit()
    
    # Initialize Core Systems
    from voice.engine import VoiceEngine
    from planner.planner import TaskPlanner
    from voice.wake_word import WakeWordSystem
    
    global global_voice_engine, global_planner, global_wake_word
    global_voice_engine = VoiceEngine()
    global_planner = TaskPlanner()
    
    # We define a synchronous wrapper for the planner since WakeWord runs in a thread
    def planner_callback(text: str) -> str:
        # Since process_request is async, we run it in a local event loop
        # We need to broadcast events back to the websocket
        async def real_broadcast(data):
            await manager.broadcast(data)
            
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(global_planner.process_request(text, real_broadcast))
        finally:
            loop.close()
        
    global_wake_word = WakeWordSystem(voice_engine=global_voice_engine, planner_callback=planner_callback)
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
