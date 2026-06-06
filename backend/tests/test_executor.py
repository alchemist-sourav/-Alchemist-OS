import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from executor.executor import AgentExecutor
from memory.database import memory_manager
from tools.registry import registry

@pytest.fixture(autouse=True)
def setup_db():
    memory_manager.cursor.execute("DELETE FROM agent_tasks")
    memory_manager.conn.commit()

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_executor_validation_rejection(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    executor = AgentExecutor(broadcast_func=AsyncMock())
    
    # 1. Invalid String Format
    steps_json = json.dumps(["create_file(filename='test.txt')"])
    task_id = memory_manager.create_agent_task("Test String", steps_json)
    await executor.execute_task(task_id)
    
    # 2. Invalid parentheses in tool name
    steps_json_2 = json.dumps([{"tool": "create_file(filename='test.txt')", "args": {}}])
    task_id_2 = memory_manager.create_agent_task("Test Parentheses", steps_json_2)
    await executor.execute_task(task_id_2)
    
    # Check DB logs
    mem_1 = memory_manager.get_agent_task(task_id)
    mem_2 = memory_manager.get_agent_task(task_id_2)
    assert mem_1["status"] == "completed"
    assert mem_2["status"] == "completed"

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_executor_valid_execution(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    executor = AgentExecutor(broadcast_func=AsyncMock())
    
    # Fake successful registry execution
    with patch("executor.executor.registry.execute") as mock_execute:
        mock_execute.return_value = "Success"
        
        steps_json = json.dumps([
            {"tool": "create_file", "args": {"filename": "test.txt"}},
            {"tool": "read_file", "args": {"filename": "test.txt"}},
            {"tool": "capture_screen", "args": {}},
            {"tool": "search_google", "args": {"query": "test"}},
            {"tool": "get_tasks", "args": {"project_name": "Test"}}
        ])
        
        # Ensure they are "registered" for validation
        with patch.object(registry, 'get_registered_tools', return_value=["create_file", "read_file", "capture_screen", "search_google", "get_tasks"]):
            task_id = memory_manager.create_agent_task("Test Real Execution", steps_json)
            await executor.execute_task(task_id)
            
            assert mock_execute.call_count == 5
            
            # Check arguments
            mock_execute.assert_any_call("create_file", {"filename": "test.txt"})
            mock_execute.assert_any_call("search_google", {"query": "test"})
