import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from executor.executor import AgentExecutor
from memory.database import memory_manager
import tools.browser_agent
import tools.file_agent

@pytest.fixture(autouse=True)
def setup_db():
    # Clean DB for tests
    memory_manager.cursor.execute("DELETE FROM agent_tasks")
    memory_manager.conn.commit()

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_agent_executor_flow(mock_groq):
    # Mock Groq to prevent httpx proxies error
    mock_client = MagicMock()
    mock_groq.return_value = mock_client

    # 1. Create a task in DB
    goal = "Find AI internships and save them"
    steps = [{"tool": "browser_start", "args": {}}, {"tool": "list_directory", "args": {}}]
    task_id = memory_manager.create_agent_task(goal, json.dumps(steps))
    
    # 2. Mock Executor LLM responses
    executor = AgentExecutor(broadcast_func=AsyncMock())
    
    # Mock _generate_tool_args to return args dynamically based on tool
    async def mock_generate_args(goal, tool_name, history):
        if tool_name == "browser_start":
            return {"url": "https://google.com"}, "Searching Google"
        elif tool_name == "list_directory":
            return {"path": "."}, "Listing directory"
        return {}, "Unknown"
        
    executor._generate_tool_args = mock_generate_args
    
    # Mock _generate_final_summary
    async def mock_summary(goal, history):
        return "Task completed successfully."
    executor._generate_final_summary = mock_summary
    
    # 3. Mock Registry Execution to avoid real OS/Network effects
    with patch("executor.executor.registry.execute") as mock_registry:
        mock_registry.side_effect = ["Search Results: Google, Meta", "File internships.txt created"]
        
        result = await executor.execute_task(task_id)
        
        # Verify result
        assert result == "Task completed successfully."
        
        # Verify Registry calls
        assert mock_registry.call_count == 2
        mock_registry.assert_any_call("browser_start", {})
        mock_registry.assert_any_call("list_directory", {})
        
        # Verify DB Updates
        task = memory_manager.get_agent_task(task_id)
        assert task["status"] == "completed"
        assert task["current_step"] == 2

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_agent_executor_task_not_found(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    executor = AgentExecutor()
    result = await executor.execute_task(9999)
    assert result == "Task not found."
