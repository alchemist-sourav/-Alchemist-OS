import pytest
import asyncio
from agents.base_agent import BaseAgent, AgentMessage
from agents.registry import AgentRegistry
from agents.orchestrator import orchestrator
from memory.database import memory_manager

class MockAgent(BaseAgent):
    def __init__(self, name):
        super().__init__(name)
        self.received_messages = []
        
    async def process(self, message: AgentMessage):
        self.received_messages.append(message)
        if message.payload.get("action") == "fail":
            raise Exception("Intentional failure")

@pytest.fixture
def clean_registry():
    AgentRegistry.agents.clear()
    yield
    AgentRegistry.agents.clear()

@pytest.mark.asyncio
async def test_message_routing(clean_registry):
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    AgentRegistry.register_agent(agent1)
    AgentRegistry.register_agent(agent2)
    
    msg = AgentMessage(
        sender="agent1",
        receiver="agent2",
        task_id="test_task_1",
        priority="normal",
        payload={"action": "test"}
    )
    
    await AgentRegistry.route_message(msg)
    
    assert len(agent2.received_messages) == 1
    assert agent2.received_messages[0].task_id == "test_task_1"
    assert agent1.task_count == 0
    assert agent2.task_count == 1

@pytest.mark.asyncio
async def test_broadcast_routing(clean_registry):
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    agent3 = MockAgent("agent3")
    for a in [agent1, agent2, agent3]:
        AgentRegistry.register_agent(a)
        
    msg = AgentMessage(
        sender="agent1",
        receiver="broadcast",
        task_id="broadcast_1",
        priority="low",
        payload={"action": "broadcast_test"}
    )
    
    await AgentRegistry.route_message(msg)
    
    assert len(agent1.received_messages) == 0
    assert len(agent2.received_messages) == 1
    assert len(agent3.received_messages) == 1

@pytest.mark.asyncio
async def test_failure_recovery(clean_registry):
    agent1 = MockAgent("agent1")
    AgentRegistry.register_agent(agent1)
    
    msg = AgentMessage(
        sender="system",
        receiver="agent1",
        task_id="fail_task",
        priority="normal",
        payload={"action": "fail"}
    )
    
    # Should not raise exception out of handle_message
    await AgentRegistry.route_message(msg)
    
    assert agent1.failure_count == 1
    assert agent1.task_count == 1 # still counted as processed but failed

@pytest.mark.asyncio
async def test_orchestrator(clean_registry):
    supervisor = MockAgent("supervisor_agent")
    AgentRegistry.register_agent(supervisor)
    
    await orchestrator.route_task("orch_1", "test_goal", [{"tool": "test", "args": {}}])
    
    assert len(supervisor.received_messages) == 1
    msg = supervisor.received_messages[0]
    assert msg.payload["action"] == "execute_task"
    assert msg.payload["goal"] == "test_goal"
