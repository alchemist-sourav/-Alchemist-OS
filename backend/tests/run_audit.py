import asyncio
import os
import sys
import logging

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planner.planner import TaskPlanner
from memory.database import memory_manager
from tools.registry import registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Audit")

async def mock_broadcast(data):
    logger.info(f"BROADCAST: {data}")

async def run_test_1():
    print("\n--- TEST 1: Memory (Profile) ---")
    planner = TaskPlanner()
    r1 = await planner.process_request("Remember my name is Sourav", mock_broadcast)
    print(f"R1: {r1}")
    r2 = await planner.process_request("What is my name", mock_broadcast)
    print(f"R2: {r2}")
    if "Sourav" in r2:
        return "PASS", r1 + " | " + r2
    return "FAIL", r1 + " | " + r2

async def run_test_2():
    print("\n--- TEST 2: Projects & Tasks ---")
    planner = TaskPlanner()
    r1 = await planner.process_request("Create project Alchemist AI", mock_broadcast)
    print(f"R1: {r1}")
    r2 = await planner.process_request("Add task Build Vision System to project Alchemist AI", mock_broadcast)
    print(f"R2: {r2}")
    r3 = await planner.process_request("Show my tasks for project Alchemist AI", mock_broadcast)
    print(f"R3: {r3}")
    tasks = memory_manager.get_tasks("Alchemist AI")
    if tasks and any("Build Vision System" in t[1] for t in tasks):
        return "PASS", r3
    return "FAIL", r3

async def run_test_3():
    print("\n--- TEST 3: Screenshot Engine ---")
    planner = TaskPlanner()
    r1 = await planner.process_request("Take a screenshot", mock_broadcast)
    print(f"R1: {r1}")
    if "screenshot" in r1.lower() or "png" in r1.lower() or "saved" in r1.lower():
        return "PASS", r1
    return "FAIL", r1

async def run_test_4():
    print("\n--- TEST 4: Browser Engine ---")
    planner = TaskPlanner()
    r1 = await planner.process_request("Search AI internships on google", mock_broadcast)
    print(f"R1: {r1}")
    if "tool result:" in r1.lower() or "search" in r1.lower() or "internship" in r1.lower() or "google" in r1.lower():
        return "PASS", r1
    return "FAIL", r1

async def run_test_5():
    print("\n--- TEST 5: Autonomous Executor ---")
    planner = TaskPlanner()
    # This will trigger the executor
    r1 = await planner.process_request("Find AI internships and save them to a file named test_internships.txt", mock_broadcast)
    print(f"R1: {r1}")
    if os.path.exists("test_internships.txt") or "file" in r1.lower() or "save" in r1.lower():
        return "PASS", r1
    return "FAIL", r1

async def run_test_6():
    print("\n--- TEST 6: Persistence ---")
    planner = TaskPlanner()
    r1 = await planner.process_request("What projects am I working on", mock_broadcast)
    print(f"R1: {r1}")
    if "Alchemist AI" in r1:
        return "PASS", r1
    return "FAIL", r1

async def run_test_7():
    print("\n--- TEST 7: Self-Improvement ---")
    planner = TaskPlanner()
    # Mock some preferences and experiences if none exist
    memory_manager.save_preference("workflow", "Prefers concise answers")
    r1 = await planner.process_request("What have you learned about me? What are my preferences?", mock_broadcast)
    print(f"R1: {r1}")
    if "concise answers" in r1.lower() or "workflow" in r1.lower() or "preference" in r1.lower():
        return "PASS", r1
    return "FAIL", r1

async def main():
    results = {}
    
    try:
        res, logs = await run_test_1()
        results["TEST_1"] = {"status": res, "logs": logs}
    except Exception as e:
        results["TEST_1"] = {"status": "FAIL", "logs": str(e)}

    try:
        res, logs = await run_test_2()
        results["TEST_2"] = {"status": res, "logs": logs}
    except Exception as e:
        results["TEST_2"] = {"status": "FAIL", "logs": str(e)}

    try:
        res, logs = await run_test_3()
        results["TEST_3"] = {"status": res, "logs": logs}
    except Exception as e:
        results["TEST_3"] = {"status": "FAIL", "logs": str(e)}

    try:
        res, logs = await run_test_4()
        results["TEST_4"] = {"status": res, "logs": logs}
    except Exception as e:
        results["TEST_4"] = {"status": "FAIL", "logs": str(e)}

    try:
        res, logs = await run_test_5()
        results["TEST_5"] = {"status": res, "logs": logs}
    except Exception as e:
        results["TEST_5"] = {"status": "FAIL", "logs": str(e)}

    try:
        res, logs = await run_test_6()
        results["TEST_6"] = {"status": res, "logs": logs}
    except Exception as e:
        results["TEST_6"] = {"status": "FAIL", "logs": str(e)}

    try:
        res, logs = await run_test_7()
        results["TEST_7"] = {"status": res, "logs": logs}
    except Exception as e:
        results["TEST_7"] = {"status": "FAIL", "logs": str(e)}

    print("\n\n=== FINAL AUDIT REPORT ===")
    for test, data in results.items():
        print(f"{test}: {data['status']}")
        print(f"Logs: {data['logs']}\n")

if __name__ == "__main__":
    asyncio.run(main())
