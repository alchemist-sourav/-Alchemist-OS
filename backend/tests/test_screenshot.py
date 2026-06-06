import pytest
import os
from unittest.mock import patch, MagicMock
from vision.screen import take_screenshot, capture_active_window, capture_screen, save_screenshot
from tools.registry import registry
from core.config import settings

@patch('vision.screen.pyautogui.screenshot')
def test_take_screenshot(mock_screenshot):
    mock_image = MagicMock()
    mock_screenshot.return_value = mock_image
    
    result = take_screenshot()
    
    assert "Screenshot successfully saved" in result
    mock_screenshot.assert_called_once_with()
    mock_image.save.assert_called_once()
    
    # Verify save path starts with screenshots dir
    save_args = mock_image.save.call_args[0]
    assert save_args[0].startswith(settings.SCREENSHOTS_DIR)
    assert "screenshot_full_" in save_args[0]

@patch('vision.screen.gw.getActiveWindow')
@patch('vision.screen.pyautogui.screenshot')
def test_capture_active_window(mock_screenshot, mock_get_window):
    mock_window = MagicMock()
    mock_window.left = 10
    mock_window.top = 20
    mock_window.width = 800
    mock_window.height = 600
    mock_get_window.return_value = mock_window
    
    mock_image = MagicMock()
    mock_screenshot.return_value = mock_image
    
    result = capture_active_window()
    
    assert "Active window screenshot successfully saved" in result
    mock_screenshot.assert_called_once_with(region=(10, 20, 800, 600))
    mock_image.save.assert_called_once()
    
    save_args = mock_image.save.call_args[0]
    assert "screenshot_window_" in save_args[0]

@patch('vision.screen.gw.getActiveWindow')
def test_capture_active_window_no_window(mock_get_window):
    mock_get_window.return_value = None
    
    result = capture_active_window()
    assert "Failed to take active window screenshot: No active window detected" in result

def test_aliases():
    with patch('vision.screen.take_screenshot') as mock_take:
        mock_take.return_value = "Mocked"
        assert capture_screen() == "Mocked"
        assert save_screenshot() == "Mocked"

def test_registry_integration():
    import vision.screen # Ensure registration executes
    assert registry.get_tool("take_screenshot") == take_screenshot
    assert registry.get_tool("capture_screen") == capture_screen
    assert registry.get_tool("save_screenshot") == save_screenshot
    assert registry.get_tool("capture_active_window") == capture_active_window
