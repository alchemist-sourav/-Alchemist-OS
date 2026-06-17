import sys
import os
import time
import datetime
import psutil
import logging
import asyncio

# Setup path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(root_dir, "backend"))


from core.logger import setup_logging
setup_logging()

logger = logging.getLogger("AlchemistStabilityTest")

from tools.registry import registry
import tools.actions
import tools.browser_agent
import tools.system
import tools.file_agent
import tools.computer
import vision.screen
import vision.analyzer

from database.database import memory_manager
from planner.planner import TaskPlanner
from executor.executor import AgentExecutor

REPORT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "stability_report.md")

class StabilityTester:
    def __init__(self):
        self._validate_startup()
        self.process = psutil.Process(os.getpid())
        
        # Metrics
        self.start_time = time.time()
        self.crash_count = 0
        self.failed_tool_executions = 0
        self.db_errors = 0
        
        self.response_times = []
        self.initial_ram_mb = self._get_ram_mb()
        self.peak_ram_mb = self.initial_ram_mb
        
        # Schedulers
        self.last_db_time = 0
        self.last_browser_time = 0
        self.last_screenshot_time = 0
        self.last_planner_time = 0

    def _validate_startup(self):
        logger.info("Validating startup dependencies...")
        
        # verify MemoryManager methods exist
        required_memory_methods = ['save_profile', 'get_profile', 'create_agent_task']
        for method in required_memory_methods:
            if not hasattr(memory_manager, method):
                logger.error(f"Validation Failed: MemoryManager missing '{method}'")
                sys.exit(1)
                
        # verify Planner methods exist
        required_planner_methods = ['process_request']
        planner = TaskPlanner()
        for method in required_planner_methods:
            if not hasattr(planner, method):
                logger.error(f"Validation Failed: TaskPlanner missing '{method}'")
                sys.exit(1)
                
        # verify BrowserAgent methods exist (via registry)
        if not registry.get_tool("browser_start"):
            logger.error("Validation Failed: BrowserAgent 'browser_start' missing from registry")
            sys.exit(1)
            
        # verify VisionAgent methods exist (via registry)
        if not registry.get_tool("take_screenshot"):
            logger.error("Validation Failed: VisionAgent 'take_screenshot' missing from registry")
            sys.exit(1)
            
        logger.info("Startup validation passed.")

    def _get_ram_mb(self) -> float:
        return self.process.memory_info().rss / (1024 * 1024)
        
    def _get_cpu_percent(self) -> float:
        return self.process.cpu_percent(interval=None)

    def _update_report(self):
        current_ram = self._get_ram_mb()
        if current_ram > self.peak_ram_mb:
            self.peak_ram_mb = current_ram
            
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0.0
        uptime = str(datetime.timedelta(seconds=int(time.time() - self.start_time)))
        
        report_content = f"""# Alchemist OS 24-Hour Stability Report
Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Metrics Overview
- **Uptime:** {uptime}
- **Crash Count:** {self.crash_count}
- **Failed Tool Executions:** {self.failed_tool_executions}
- **Database Errors:** {self.db_errors}
- **Average Response Time:** {avg_response:.2f} seconds

## Memory Profile
- **Starting RAM:** {self.initial_ram_mb:.2f} MB
- **Current RAM:** {current_ram:.2f} MB
- **Peak RAM:** {self.peak_ram_mb:.2f} MB
- **RAM Growth:** {current_ram - self.initial_ram_mb:.2f} MB

## CPU Profile
- **Current CPU Usage:** {self._get_cpu_percent():.1f}%
"""
        with open(REPORT_PATH, "w") as f:
            f.write(report_content)

    def _run_db_test(self):
        logger.info("Executing 5-minute DB Test...")
        start_t = time.time()
        try:
            val = f"test_{int(time.time())}"
            memory_manager.save_profile("stability_test_key", val)
            res = memory_manager.get_profile("stability_test_key")
            if res != val:
                raise Exception("DB Read/Write mismatch")
        except Exception as e:
            logger.error(f"DB Test Error: {e}")
            self.db_errors += 1
            self.crash_count += 1
        finally:
            self.response_times.append(time.time() - start_t)

    def _run_browser_test(self):
        logger.info("Executing 10-minute Browser Test...")
        start_t = time.time()
        try:
            # Execute browser start
            res = registry.execute("browser_start", {"url": "https://google.com"})
            if "Failed" in res or "Error" in res:
                self.failed_tool_executions += 1
                logger.error(f"Browser start failed: {res}")
            
            # Navigate back/close
            registry.execute("browser_close", {})
        except Exception as e:
            logger.error(f"Browser Test Error: {e}")
            self.crash_count += 1
        finally:
            self.response_times.append(time.time() - start_t)

    def _run_screenshot_test(self):
        logger.info("Executing 15-minute Screenshot Test...")
        start_t = time.time()
        try:
            res = registry.execute("take_screenshot", {})
            if "Failed" in res or "Error" in res:
                self.failed_tool_executions += 1
                logger.error(f"Screenshot failed: {res}")
        except Exception as e:
            logger.error(f"Screenshot Test Error: {e}")
            self.crash_count += 1
        finally:
            self.response_times.append(time.time() - start_t)

    def _run_planner_test(self):
        logger.info("Executing 20-minute Planner Test...")
        start_t = time.time()
        try:
            planner = TaskPlanner()
            goal = "Get the current time and write it to the clipboard."
            
            async def _run_async():
                result = await planner.process_request(goal, broadcast_func=None)
                if "Error" in result or "Failed" in result or "Sorry" in result:
                    self.failed_tool_executions += 1
                    logger.error(f"Planner/Executor failed: {result}")
            
            asyncio.run(_run_async())
                    
        except Exception as e:
            logger.error(f"Planner Test Error: {e}")
            self.crash_count += 1
        finally:
            self.response_times.append(time.time() - start_t)

    def run(self, test_duration_hours=24):
        logger.info(f"Starting Stability Test for {test_duration_hours} hours...")
        
        # Prime the CPU monitoring
        self._get_cpu_percent()
        
        end_time = self.start_time + (test_duration_hours * 3600)
        
        while time.time() < end_time:
            now = time.time()
            
            # Every 5 mins (300 sec)
            if now - self.last_db_time >= 300:
                self._run_db_test()
                self.last_db_time = now
                
            # Every 10 mins (600 sec)
            if now - self.last_browser_time >= 600:
                self._run_browser_test()
                self.last_browser_time = now
                
            # Every 15 mins (900 sec)
            if now - self.last_screenshot_time >= 900:
                self._run_screenshot_test()
                self.last_screenshot_time = now
                
            # Every 20 mins (1200 sec)
            if now - self.last_planner_time >= 1200:
                self._run_planner_test()
                self.last_planner_time = now
                
            # Update report every 60 seconds
            self._update_report()
            
            # Sleep in short increments to remain responsive
            time.sleep(10)

        logger.info("Stability Test Completed!")
        self._update_report()

if __name__ == "__main__":
    duration = 24.0
    if len(sys.argv) > 1:
        try:
            duration = float(sys.argv[1])
        except ValueError:
            pass
    tester = StabilityTester()
    try:
        tester.run(duration)
    except KeyboardInterrupt:
        logger.info("Stability Test Interrupted by User. Generating report and exiting cleanly...")
        tester._update_report()
        sys.exit(0)
