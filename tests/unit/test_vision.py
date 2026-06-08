import pytest
import json
from planner.planner import TaskPlanner
from unittest.mock import patch, MagicMock
from vision.analyzer import analyze_screen, read_screen_text, identify_active_window, _analyze_image
from tools.registry import registry

@pytest.fixture
def mock_vision_dependencies():
    with patch('vision.analyzer.take_screenshot') as mock_take_screenshot, \
         patch('vision.analyzer.capture_active_window') as mock_capture_active_window, \
         patch('vision.analyzer._encode_image') as mock_encode, \
         patch('vision.analyzer.Groq') as mock_groq:
        
        mock_take_screenshot.return_value = "Screenshot successfully saved to C:/screenshots/test.png"
        mock_capture_active_window.return_value = "Active window screenshot successfully saved to C:/screenshots/window.png"
        mock_encode.return_value = "mock_base64_string"
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"applications": ["Test App"], "visible_text": ["Test Text"], "summary": "Mock summary"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        yield {
            'take_screenshot': mock_take_screenshot,
            'capture_active_window': mock_capture_active_window,
            'encode': mock_encode,
            'groq': mock_client
        }

def test_analyze_screen(mock_vision_dependencies):
    result = analyze_screen()
    
    # Check if Groq was called
    mock_vision_dependencies['groq'].chat.completions.create.assert_called_once()
    
    # Check if the result was properly cleaned up and returned
    assert "Test App" in result
    assert "Test Text" in result
    assert "Mock summary" in result

def test_read_screen_text(mock_vision_dependencies):
    mock_vision_dependencies['groq'].chat.completions.create.return_value.choices[0].message.content = "Extracted OCR Text"
    
    result = read_screen_text()
    
    assert result == "Extracted OCR Text"
    mock_vision_dependencies['take_screenshot'].assert_called_once()

def test_identify_active_window(mock_vision_dependencies):
    mock_vision_dependencies['groq'].chat.completions.create.return_value.choices[0].message.content = "VS Code is open"
    
    result = identify_active_window()
    
    assert result == "VS Code is open"
    mock_vision_dependencies['capture_active_window'].assert_called_once()

def test_analyze_screen_failed_screenshot():
    with patch('vision.analyzer.take_screenshot') as mock_take_screenshot:
        mock_take_screenshot.return_value = "Failed to take full screenshot: Error"
        
        result = analyze_screen()
        assert "Failed to take full screenshot" in result

def test_registry_integration():
    import vision.analyzer # Ensure registration executes
    assert registry.get_tool("analyze_screen") == analyze_screen
    assert registry.get_tool("read_screen_text") == read_screen_text
    assert registry.get_tool("identify_active_window") == identify_active_window

@pytest.mark.asyncio
@patch('core.providers.ProviderManager.get_llm_provider')
async def test_planner_integration(mock_get_provider):
    mock_provider = MagicMock()
    mock_get_provider.return_value = mock_provider
    
    # Mock the planner LLM to return the analyze_screen tool
    mock_provider.generate_completion.return_value = json.dumps({
        "goal": "Analyze the error on screen",
        "steps": [
            {"tool": "analyze_screen", "args": {}}
        ]
    })
    
    planner = TaskPlanner()
    
    async def dummy_broadcast(data):
        pass
        
    with patch('executor.executor.AgentExecutor.execute_task', return_value="Executed") as mock_exec:
        with patch('planner.planner.memory_manager.create_agent_task', return_value=1) as mock_create:
            await planner.process_request("What is this error on my screen?", dummy_broadcast)
            
            # Verify Planner successfully parsed it and sent to executor
            mock_create.assert_called_once()
            args = mock_create.call_args[0]
            assert "Analyze the error on screen" in args[0]
            
            steps_json = json.loads(args[1])
            assert steps_json[0]["tool"] == "analyze_screen"
