"""Agent Executor - Synchronous-await task execution with result return."""
import json
import time
import logging
import asyncio
from typing import Callable, Optional

logger = logging.getLogger("AgentExecutor")

# Pending confirmations for human-in-the-loop
_pending_confirmations: dict = {}


class AgentExecutor:
    def __init__(self, broadcast_func: Optional[Callable] = None):
        self.broadcast_func = broadcast_func

    async def execute_task(self, task_id: str) -> str:
        from database.database import memory_manager
        from tools.registry import registry

        task = memory_manager.get_agent_task(task_id)
        if not task:
            return f"Task {task_id} not found."

        steps = json.loads(task["steps_json"]) if task["steps_json"] else []
        if not steps:
            return "No steps to execute."

        memory_manager.update_agent_task_status(task_id, "running")
        results = []
        start_time = time.time()

        for i, step in enumerate(steps):
            tool = step.get("tool", "")
            args = step.get("args", {})
            memory_manager.update_agent_task_step(task_id, i)

            if self.broadcast_func:
                await self.broadcast_func({"type": "step_start", "task_id": task_id, "step": i, "tool": tool})

            try:
                result = await registry.execute(tool, args)
                results.append(f"Step {i+1} ({tool}): {result}")
            except Exception as e:
                logger.error(f"Task {task_id} failed at step {i} ({tool}): {e}")
                results.append(f"Step {i+1} ({tool}): FAILED - {e}")
                memory_manager.update_agent_task_status(task_id, "failed")
                execution_time = time.time() - start_time
                memory_manager.save_experience(
                    goal=task["goal"], plan=task["steps_json"],
                    outcome="\n".join(results), success=False,
                    execution_time=execution_time, reflections=f"Failed at step {i}: {e}"
                )
                return f"Task failed at step {i+1}: {e}"

        memory_manager.update_agent_task_status(task_id, "completed")
        execution_time = time.time() - start_time
        final_result = results[-1] if results else "Task completed."
        memory_manager.save_experience(
            goal=task["goal"], plan=task["steps_json"],
            outcome="\n".join(results), success=True,
            execution_time=execution_time, reflections="Completed successfully."
        )
        return final_result


async def resume_agent_execution(task_id: str, confirmed: bool, broadcast_func: Optional[Callable] = None):
    """Resume or reject a paused task awaiting human confirmation."""
    future = _pending_confirmations.pop(task_id, None)
    if future and not future.done():
        future.set_result(confirmed)
    elif broadcast_func:
        status = "confirmed" if confirmed else "rejected"
        await broadcast_func({"type": "action_status", "task_id": task_id, "status": status})
