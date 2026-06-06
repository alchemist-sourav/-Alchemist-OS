import asyncio
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from planner.planner import TaskPlanner
from tools.registry import registry
from memory.database import memory_manager
import vision.screen
import vision.analyzer
import tools.actions
import tools.browser_agent
import tools.file_agent
import tools.system

logging.basicConfig(level=logging.INFO)

async def mock_broadcast(data):
    print(f"BROADCAST: {data}")

async def main():
    planner = TaskPlanner()
    
    print("\n\n=== 1. Take screenshot ===")
    r = await planner.process_request("Take a screenshot", mock_broadcast)
    print("Result:", r)
    
    print("\n\n=== 2. Search AI internships ===")
    r = await planner.process_request("Search AI internships on google", mock_broadcast)
    print("Result:", r)

    print("\n\n=== 3. Create file notes.txt ===")
    r = await planner.process_request("Create file notes.txt", mock_broadcast)
    print("Result:", r)
    
    print("\n\n=== 4. Show tasks ===")
    r = await planner.process_request("Show my tasks for project Alchemist AI", mock_broadcast)
    print("Result:", r)

if __name__ == "__main__":
    asyncio.run(main())
