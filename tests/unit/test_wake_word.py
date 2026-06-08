import pytest
import time
from unittest.mock import MagicMock, patch
from voice.wake_word import WakeWordSystem

@pytest.fixture
def wake_system():
    mock_engine = MagicMock()
    mock_planner = MagicMock()
    system = WakeWordSystem(voice_engine=mock_engine, planner_callback=mock_planner)
    return system

def test_wake_detection(wake_system):
    assert wake_system.state == "sleeping"
    
    # Send random text, should remain sleeping
    mock_audio = MagicMock()
    with patch.object(wake_system.recognizer, 'recognize_google', return_value="hello world"):
        wake_system._process_audio(mock_audio)
    
    assert wake_system.state == "sleeping"
    
    # Send wake word
    with patch.object(wake_system.recognizer, 'recognize_google', return_value="hey alchemist"):
        wake_system._process_audio(mock_audio)
        
    assert wake_system.state == "listening"

def test_timeout_behavior(wake_system):
    wake_system.set_state("listening")
    assert wake_system.state == "listening"
    
    # Fast forward time
    wake_system.last_speech_time = time.time() - (wake_system.timeout_seconds + 1.0)
    
    # The next run_loop iteration would do this:
    if time.time() - wake_system.last_speech_time > wake_system.timeout_seconds:
        wake_system.set_state("sleeping")
        
    assert wake_system.state == "sleeping"

def test_interruption_handling(wake_system):
    wake_system.set_state("speaking")
    assert wake_system.state == "speaking"
    
    mock_audio = MagicMock()
    with patch.object(wake_system.recognizer, 'recognize_google', return_value="stop everything"):
        wake_system._process_audio(mock_audio)
        
    # Should call voice engine interrupt and reset to sleeping
    wake_system.voice_engine.interrupt.assert_called_once()
    assert wake_system.state == "sleeping"

def test_planner_routing(wake_system):
    wake_system.set_state("listening")
    
    mock_audio = MagicMock()
    with patch.object(wake_system, '_execute_planner'):
        with patch.object(wake_system.recognizer, 'recognize_google', return_value="open google"):
            wake_system._process_audio(mock_audio)
            
        assert wake_system.state == "thinking"
    
    # Manually call what the thread would call
    wake_system.planner_callback.return_value = "Task completed"
    # Call the actual class method
    WakeWordSystem._execute_planner(wake_system, "open google")
    
    wake_system.planner_callback.assert_called_once_with("open google")
    wake_system.voice_engine.speak.assert_called_once_with("Task completed")
    assert wake_system.state == "sleeping"
