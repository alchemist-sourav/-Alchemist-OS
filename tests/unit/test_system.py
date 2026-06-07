import pytest
import os
from unittest.mock import patch, MagicMock
from tools.system import launch_application
from tools.registry import registry

def test_launch_application_windows_startfile():
    with patch('os.name', 'nt'), \
         patch('os.startfile') as mock_startfile, \
         patch('subprocess.Popen') as mock_popen:
        
        result = launch_application("notepad.exe")
        
        mock_startfile.assert_called_once_with("notepad.exe")
        mock_popen.assert_not_called()
        assert "Successfully launched notepad.exe" in result

def test_launch_application_windows_fallback():
    with patch('os.name', 'nt'), \
         patch('os.startfile', side_effect=FileNotFoundError), \
         patch('subprocess.Popen') as mock_popen:
        
        result = launch_application("custom_app.exe")
        
        mock_popen.assert_called_once_with("custom_app.exe", shell=True)
        assert "Successfully launched custom_app.exe via subprocess" in result

def test_launch_application_other_os():
    with patch('os.name', 'posix'), \
         patch('subprocess.Popen') as mock_popen:
        
        result = launch_application("gedit")
        
        mock_popen.assert_called_once_with("gedit", shell=True)
        assert "Successfully launched gedit via subprocess" in result

def test_launch_application_error():
    with patch('os.name', 'posix'), \
         patch('subprocess.Popen', side_effect=Exception("mock error")):
        
        result = launch_application("failing_app")
        
        assert "Failed to launch application" in result
        assert "mock error" in result

def test_tool_registry():
    import tools.system # Ensure it's imported to register
    func = registry.get_tool("launch_application")
    assert func is not None
    assert func == launch_application
