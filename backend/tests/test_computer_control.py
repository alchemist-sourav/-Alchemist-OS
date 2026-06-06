import pytest
from unittest.mock import patch, MagicMock
from tools.computer import move_mouse, click_mouse, double_click, type_text, press_key
from tools.registry import registry

@patch('tools.computer.pyautogui.moveTo')
def test_move_mouse(mock_move):
    result = move_mouse(500, 300)
    assert "Successfully moved mouse" in result
    mock_move.assert_called_once_with(500, 300)

@patch('tools.computer.pyautogui.click')
def test_click_mouse(mock_click):
    result = click_mouse(500, 300)
    assert "Successfully clicked" in result
    mock_click.assert_called_once_with(500, 300)

@patch('tools.computer.pyautogui.doubleClick')
def test_double_click(mock_double_click):
    result = double_click(500, 300)
    assert "Successfully double-clicked" in result
    mock_double_click.assert_called_once_with(500, 300)

@patch('tools.computer.pyautogui.write')
def test_type_text(mock_write):
    result = type_text("hello world")
    assert "Successfully typed text" in result
    mock_write.assert_called_once_with("hello world", interval=0.01)

@patch('tools.computer.pyautogui.press')
def test_press_key(mock_press):
    result = press_key("enter")
    assert "Successfully pressed key" in result
    mock_press.assert_called_once_with("enter")

def test_registry_integration():
    import tools.computer
    assert registry.get_tool("move_mouse") == move_mouse
    assert registry.get_tool("click_mouse") == click_mouse
    assert registry.get_tool("double_click") == double_click
    assert registry.get_tool("type_text") == type_text
    assert registry.get_tool("press_key") == press_key
