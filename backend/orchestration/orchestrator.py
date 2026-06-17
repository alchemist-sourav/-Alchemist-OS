from typing import Dict, Any, List
from agents.base_agent import AgentMessage
from agents.registry import AgentRegistry
from memory.database import memory_manager
import logging

logger = logging.getLogger("TaskOrchestrator")

class TaskOrchestrator:
    def __init__(self):
        self.active_tasks = {}
        
    async def route_task(self, task_id: str, goal: str, steps: List[Dict[str, Any]]):
        logger.info(f"Orchestrating task {task_id}: {goal}")
        
        # In a full multi-agent setup, the orchestrator would assign specific steps to specific agents
        # Here we just pass the full task to the Supervisor to manage
        
        message = AgentMessage(
            sender="orchestrator",
            receiver="supervisor_agent",
            task_id=task_id,
            priority="high",
            payload={
                "action": "execute_task",
                "goal": goal,
                "steps": steps
            }
        )
        await AgentRegistry.route_message(message)

    def get_task_status(self, task_id: str):
        return memory_manager.get_agent_task(int(task_id))

orchestrator = TaskOrchestrator()
