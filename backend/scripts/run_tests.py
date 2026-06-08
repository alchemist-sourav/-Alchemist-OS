import asyncio
import sys
import os
import time
import json
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from planner.planner import TaskPlanner
from voice.wake_word import WakeWordSystem
from executor.executor import AgentExecutor
from memory.database import memory_manager
from tools.registry import registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestRunner")

class MockVoiceEngine:
    def __init__(self):
        self.spoken = []
    def speak(self, text):
        self.spoken.append(text)
        logger.info(f"[MOCK TTS] Speaking: {text}")
    def interrupt(self):
        logger.info("[MOCK TTS] Interrupted.")

async def mock_broadcast(data):
    logger.info(f"[MOCK WS BROADCAST] {data}")

async def run_planner_tests():
    planner = TaskPlanner()
    
    logger.info("--- Test 1: Simple Conversation ---")
    start = time.time()
    res1 = await planner.process_request("Hello Alchemist, how are you?", mock_broadcast)
    latency1 = time.time() - start
    logger.info(f"Result: {res1} (Latency: {latency1:.2f}s)")
    assert "tool" not in res1.lower(), "Should be conversational."

    logger.info("--- Test 2: Memory Retrieval ---")
    memory_manager.save_profile("name", "TestUser")
    start = time.time()
    res2 = await planner.process_request("What is my name?", mock_broadcast)
    latency2 = time.time() - start
    logger.info(f"Result: {res2} (Latency: {latency2:.2f}s)")
    assert "TestUser" in res2, "Should have retrieved memory using tools."

async def run_wake_word_tests():
    logger.info("--- Test 3: Wake Word State Transitions ---")
    mock_voice = MockVoiceEngine()
    
    # We mock the planner callback to just return a string without async loops
    def mock_planner(text):
        return f"Planner processed: {text}"
        
    ww = WakeWordSystem(voice_engine=mock_voice, planner_callback=mock_planner)
    
    assert ww.state == "sleeping"
    
    ww._process_audio_text("hey alchemist") # We will add a helper method to inject text
    assert ww.state == "listening"
    
    ww._process_audio_text("open notepad")
    # It should transition to thinking, execute, speaking, then back to sleeping
    time.sleep(1) # wait for thread to finish
    assert ww.state == "sleeping"
    assert len(mock_voice.spoken) > 0

# Helper monkeypatch
def _process_audio_text(self, text):
    text = text.lower()
    if self.state == "sleeping" and "alchemist" in text:
        self.set_state("listening")
    elif self.state == "listening":
        if text.strip() and text != "hey alchemist":
            self.set_state("thinking")
            import threading
            threading.Thread(target=self._execute_planner, args=(text,), daemon=True).start()

WakeWordSystem._process_audio_text = _process_audio_text

async def run_performance_test():
    logger.info("--- Test 4: Tool Execution Latency ---")
    # Test a simple tool execution
    start = time.time()
    res = await registry.execute("get_current_datetime", {})
    latency = time.time() - start
    logger.info(f"Tool Execution Latency: {latency:.4f}s")
    
async def main():
    logger.info("Starting QA Test Suite")
    await run_planner_tests()
    await run_wake_word_tests()
    await run_performance_test()
    logger.info("QA Test Suite Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
