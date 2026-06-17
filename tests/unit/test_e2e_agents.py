import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from websockets.exceptions import ConnectionClosed
import websockets
from main import app
from core.config import settings

client = TestClient(app)

@pytest.mark.asyncio
async def test_websocket_integration():
    # Because we're using FastAPI's TestClient websocket context manager, we can test websocket easily
    with client.websocket_connect(f"/ws?api_key={settings.API_KEY}") as websocket:
        websocket.send_text(json.dumps({"text": "Hello"}))
        data = websocket.receive_text()
        assert json.loads(data)["type"] == "chat_message"
        
@pytest.mark.asyncio
async def test_end_to_end_orchestration():
    # Simulate the planner agent triggering orchestrator, routing to supervisor, failing, retrying, and dropping
    from agents.base_agent import AgentMessage
    from agents.registry import AgentRegistry
    from agents.orchestrator import orchestrator
    from agents.supervisor_agent import SupervisorAgent
    from agents.browser_agent import BrowserAgent
    from memory.database import memory_manager
    
    # ensure agents are registered
    AgentRegistry.register_agent(SupervisorAgent())
    AgentRegistry.register_agent(BrowserAgent())
    
    task_id = "test_e2e_task"
    steps = [{"tool": "browser_start", "args": {"url": "http://example.com"}}]
    
    await orchestrator.route_task(task_id, "test_goal", steps)
    
    # Give it a second to process the queue asynchronously
    await asyncio.sleep(0.5)
    
    # We expect supervisor to pick it up and pass to browser, browser executes, passes result back.
    # We can check database or metrics.
    supervisor = AgentRegistry.get_agent("supervisor_agent")
    browser = AgentRegistry.get_agent("browser_agent")
    
    assert supervisor.task_count > 0
    assert supervisor.delegation_count > 0
    assert browser.task_count > 0
