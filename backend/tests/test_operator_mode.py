import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from executor.executor import AgentExecutor
from memory.database import memory_manager
from tools.registry import registry

@pytest.fixture(autouse=True)
def setup_db():
    memory_manager.cursor.execute("DELETE FROM agent_tasks")
    memory_manager.conn.commit()

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_safety_layer_blocking(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    executor = AgentExecutor(broadcast_func=AsyncMock())
    
    # Tool that is destructive and missing confirmed flag
    steps_json = json.dumps([{"tool": "submit_form", "args": {"selector": "#btn"}}])
    task_id = memory_manager.create_agent_task("Test Destructive Block", steps_json)
    
    with patch.object(registry, 'get_registered_tools', return_value=["submit_form"]):
        result = await executor.execute_task(task_id)
        assert "Action blocked" in result
        
        # Verify status is pending_confirmation
        task = memory_manager.get_agent_task(task_id)
        assert task["status"] == "pending_confirmation"

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_safety_layer_confirmed(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    executor = AgentExecutor(broadcast_func=AsyncMock())
    
    steps_json = json.dumps([{"tool": "delete_file", "args": {"filename": "test.txt", "confirmed": True}}])
    task_id = memory_manager.create_agent_task("Test Destructive Confirmed", steps_json)
    
    with patch.object(registry, 'get_registered_tools', return_value=["delete_file"]):
        with patch.object(registry, 'execute', return_value="Deleted file test.txt") as mock_exec:
            await executor.execute_task(task_id)
            mock_exec.assert_called_once_with("delete_file", {"filename": "test.txt", "confirmed": True})
            
            task = memory_manager.get_agent_task(task_id)
            assert task["status"] == "completed"

@pytest.mark.asyncio
@patch('executor.executor.Groq')
async def test_verification_retries(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    executor = AgentExecutor(broadcast_func=AsyncMock())
    
    steps_json = json.dumps([{"tool": "open_url", "args": {"url": "https://google.com"}}])
    task_id = memory_manager.create_agent_task("Test Retries", steps_json)
    
    # Fake registry that fails twice then succeeds
    call_count = 0
    def fake_execute(tool, args):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Timeout error")
        return "Successfully opened"

    with patch.object(registry, 'get_registered_tools', return_value=["open_url"]):
        with patch.object(registry, 'execute', side_effect=fake_execute) as mock_exec:
            with patch('executor.executor.time.sleep') as mock_sleep: # Don't actually sleep in tests
                await executor.execute_task(task_id)
                assert call_count == 3
                task = memory_manager.get_agent_task(task_id)
                assert task["status"] == "completed"
