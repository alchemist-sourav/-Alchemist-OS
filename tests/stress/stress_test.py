import asyncio
import os
import sys
import logging
import json

# Add backend to path so we can import everything correctly
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(root_dir, "backend"))

from core.logger import setup_logging
setup_logging()
logger = logging.getLogger("AlchemistStressTest")

from tools.registry import registry
from memory.database import memory_manager
from tools.browser_agent import BrowserSession

def run_stress_test():
    logger.info("====================================")
    logger.info("   ALCHEMIST OS STRESS TEST SUITE")
    logger.info("====================================")

    total_passed = 0
    total_failed = 0

    # 1. Database Writes (50 writes)
    logger.info("\n--- Phase 1: Database Stress Test (50 writes) ---")
    import random
    for i in range(50):
        try:
            val = f"test_val_{random.randint(1000, 9999)}"
            memory_manager.save_preference(f"stress_key_{i}", val)
            total_passed += 1
        except Exception as e:
            logger.error(f"DB Write {i} failed: {e}")
            total_failed += 1

    logger.info(f"DB Stress Test Complete. Passed: {total_passed}/50")

    # 2. Tool Executions (100 safe executions)
    logger.info("\n--- Phase 2: Tool Execution Stress Test (100 executions) ---")
    tool_passed = 0
    for i in range(100):
        try:
            # We use a completely safe tool
            res = registry.execute("get_current_datetime", {})
            if "Error" not in res:
                tool_passed += 1
                total_passed += 1
            else:
                total_failed += 1
        except Exception as e:
            logger.error(f"Tool execution {i} failed: {e}")
            total_failed += 1

    logger.info(f"Tool Execution Stress Test Complete. Passed: {tool_passed}/100")

    # 3. Browser Recovery/Stress (50 actions)
    logger.info("\n--- Phase 3: Browser Stress Test (50 actions) ---")
    browser_passed = 0
    try:
        bs = BrowserSession()
        res = bs.start("http://example.com")
        if "Failed" in res or "Error" in res:
            logger.error(f"Failed to start browser: {res}")
            total_failed += 50
        else:
            for i in range(50):
                # We extract text as a safe action
                text = bs.extract_page_text()
                if "Error" not in text:
                    browser_passed += 1
                    total_passed += 1
                else:
                    total_failed += 1
                    
        # Force a crash to test recovery
        logger.info("Forcing Playwright crash to test recovery...")
        if bs.playwright:
            bs.playwright.stop()
        res = bs.extract_page_text() # This should trigger recovery!
        if "restarted" in res.lower() or "Browser crashed" in res:
            logger.info("Browser recovered successfully from forced crash!")
            browser_passed += 1
            total_passed += 1
        else:
            logger.error(f"Browser did not recover. Result: {res}")
            total_failed += 1
            
    except Exception as e:
        logger.error(f"Browser test failed: {e}")
        total_failed += 50

    logger.info(f"Browser Stress Test Complete. Passed: {browser_passed}/51")

    logger.info("\n====================================")
    logger.info(f"   STRESS TEST RESULTS")
    logger.info(f"   Passed: {total_passed}")
    logger.info(f"   Failed: {total_failed}")
    logger.info("====================================")

    if total_failed == 0:
        logger.info("STRESS TEST PASSED PERFECTLY!")
    else:
        logger.error("STRESS TEST FAILED!")

if __name__ == "__main__":
    run_stress_test()
