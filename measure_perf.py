import time
import asyncio
import os
import sys
import psutil

# Fix paths
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from core.logger import setup_logging
setup_logging()

from tools.registry import registry
import tools.browser_agent
import vision.screen
import vision.analyzer
import tools.computer
import tools.file_agent
from planner.planner import TaskPlanner

def run_performance_test():
    metrics = {}
    
    # 1. Startup / Init Memory
    process = psutil.Process(os.getpid())
    metrics["idle_memory_mb"] = process.memory_info().rss / (1024 * 1024)
    
    # 2. Browser Launch
    start_t = time.time()
    res = registry.execute("browser_start", {"url": "https://example.com"})
    browser_launch = time.time() - start_t
    metrics["browser_launch_seconds"] = browser_launch
    registry.execute("browser_close", {})
    
    # 3. Screenshot
    start_t = time.time()
    res = registry.execute("take_screenshot", {})
    metrics["screenshot_seconds"] = time.time() - start_t
    
    # 4. Planner Latency
    planner = TaskPlanner()
    start_t = time.time()
    async def mock_run():
        await planner.process_request("Just reply 'ok'", lambda x: None)
    asyncio.run(mock_run())
    metrics["planner_latency_seconds"] = time.time() - start_t
    
    print("\n=== PERFORMANCE METRICS ===")
    for k, v in metrics.items():
        print(f"{k}: {v:.2f}")

if __name__ == "__main__":
    run_performance_test()
