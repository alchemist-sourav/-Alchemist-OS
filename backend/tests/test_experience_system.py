import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from executor.executor import AgentExecutor
from planner.planner import TaskPlanner
from memory.database import memory_manager

@pytest.fixture(autouse=True)
def setup_db():
    # Clean DB for tests
    memory_manager.cursor.execute("DELETE FROM agent_tasks")
    memory_manager.cursor.execute("DELETE FROM agent_experiences")
    memory_manager.cursor.execute("DELETE FROM user_preferences")
    memory_manager.conn.commit()

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_reflection_and_experience_storage(mock_groq):
    # Mock LLM calls in Executor
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    # Mock tool args logic
    async def mock_generate_args(goal, tool_name, history):
        return {}, "thinking"
    
    # Mock final summary logic
    async def mock_summary(goal, history):
        return "Done."
        
    # Mock reflection generation
    async def mock_reflection(goal, history):
        return "Worked: Tool executed.\nFailed: None\nImprovement: None", True

    executor = AgentExecutor(broadcast_func=AsyncMock())
    executor._generate_tool_args = mock_generate_args
    executor._generate_final_summary = mock_summary
    executor._generate_reflection = mock_reflection

    # Run a simple fake task
    task_id = memory_manager.create_agent_task("Test Reflection", json.dumps(["dummy_tool"]))
    
    with patch("executor.executor.registry.execute") as mock_registry:
        mock_registry.return_value = "Success"
        await executor.execute_task(task_id)
        
    # Verify experience storage
    memory_manager.cursor.execute("SELECT goal, success, reflections FROM agent_experiences")
    rows = memory_manager.cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "Test Reflection"
    assert rows[0][1] == 1 # True
    assert "Worked: Tool executed" in rows[0][2]

def test_preference_storage_and_metrics():
    # Preferences
    memory_manager.save_preference("workflow", "User prefers X over Y")
    prefs = memory_manager.get_all_preferences()
    assert len(prefs) == 1
    assert prefs[0][0] == "workflow"
    assert prefs[0][1] == "User prefers X over Y"
    
    # Metrics (Empty initial)
    metrics = memory_manager.get_agent_metrics()
    assert metrics["total_tasks"] == 0
    assert metrics["success_rate"] == 0
    
    # Insert fake experience
    memory_manager.save_experience("Goal 1", "Plan", "Outcome", True, 2.5, "Ref")
    memory_manager.save_experience("Goal 2", "Plan", "Outcome", False, 1.5, "Ref")
    
    metrics2 = memory_manager.get_agent_metrics()
    assert metrics2["total_tasks"] == 2
    assert metrics2["success_rate"] == 50.0

@patch('planner.planner.Groq')
def test_planner_context_injection(mock_groq):
    planner = TaskPlanner()
    
    memory_manager.save_preference("browser", "Always use Chrome")
    memory_manager.save_experience("Test Search", "Plan", "Outcome", True, 1.0, "Reflection: used chrome")
    
    # Build prompt and check for injection
    prompt = planner._build_context_prompt("Do a Test Search for me")
    
    assert "Always use Chrome" in prompt
    assert "Test Search" in prompt
    assert "Reflection: used chrome" in prompt
