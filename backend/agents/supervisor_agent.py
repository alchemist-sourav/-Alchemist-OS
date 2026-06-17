from agents.base_agent import BaseAgent, AgentMessage
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger("SupervisorAgent")

class SupervisorAgent(BaseAgent):
    def __init__(self):
        super().__init__("supervisor_agent")
        self.active_tasks: Dict[str, Any] = {}
        
    async def process(self, message: AgentMessage):
        action = message.payload.get("action")
        
        if action == "execute_task":
            task_id = message.task_id
            goal = message.payload.get("goal")
            steps = message.payload.get("steps", [])
            
            self.active_tasks[task_id] = {
                "goal": goal,
                "steps": steps,
                "current_step": 0,
                "status": "running"
            }
            logger.info(f"Supervisor starting task {task_id}: {goal}")
            await self._execute_next_step(task_id)
            
        elif action == "tool_result":
            task_id = message.task_id
            success = message.payload.get("success")
            result = message.payload.get("result")
            
            task_info = self.active_tasks.get(task_id)
            if not task_info:
                return
                
            if success:
                task_info["current_step"] += 1
                task_info["retries"] = 0 # reset retries
                await self._execute_next_step(task_id)
            else:
                logger.error(f"Task {task_id} failed at step {task_info['current_step']}: {result}")
                
                # Retry logic
                if task_info.get("retries", 0) < 3:
                    task_info["retries"] = task_info.get("retries", 0) + 1
                    self.retry_count += 1
                    logger.info(f"Retrying task {task_id} step {task_info['current_step']} (Attempt {task_info['retries']}/3)")
                    # Escalate to Voice to notify user of retry
                    voice_msg = AgentMessage(
                        sender=self.name, receiver="voice_agent", task_id=task_id, priority="high",
                        payload={"action": "speak", "text": "I encountered an error. Retrying the step."}
                    )
                    self.send_message(voice_msg)
                    
                    await asyncio.sleep(2) # delay before retry
                    await self._execute_next_step(task_id)
                else:
                    task_info["status"] = "failed"
                    from database.database import memory_manager
                    memory_manager.update_agent_task_status(task_id, "failed")
                    
                    # Log to memory agent for self-improvement
                    mem_msg = AgentMessage(
                        sender=self.name, receiver="memory_agent", task_id=task_id, priority="normal",
                        payload={"action": "save_memory", "category": "failed_execution", "content": f"Task {task_info['goal']} failed on tool {task_info['steps'][task_info['current_step']]['tool']} with error: {result}"}
                    )
                    self.send_message(mem_msg)
                    
                    # Escalate to Voice to notify user of failure
                    voice_msg = AgentMessage(
                        sender=self.name, receiver="voice_agent", task_id=task_id, priority="high",
                        payload={"action": "speak", "text": "I'm sorry, I couldn't complete the task after multiple attempts."}
                    )
                    self.send_message(voice_msg)
                
    async def _execute_next_step(self, task_id: str):
        task_info = self.active_tasks.get(task_id)
        if not task_info:
            return
            
        if task_info["current_step"] >= len(task_info["steps"]):
            logger.info(f"Task {task_id} completed.")
            task_info["status"] = "completed"
            from database.database import memory_manager
            memory_manager.update_agent_task_status(task_id, "completed")
            return
            
        step = task_info["steps"][task_info["current_step"]]
        tool = step.get("tool")
        args = step.get("args", {})
        
        # Check agent health before routing
        from agents.registry import AgentRegistry
        health = AgentRegistry.health_check()
        
        receiver = "system_agent"
        if tool.startswith("browser_") or tool in ["open_url", "click_element", "type_into_field", "extract_page_text", "navigate_back", "submit_form", "open_youtube", "open_google", "open_github", "open_linkedin", "open_chatgpt"]:
            receiver = "browser_agent"
            
        if not health.get(receiver, {}).get("active", False):
            logger.error(f"Cannot route to {receiver}: Agent is not active or healthy")
            # fallback to generic error
            msg = AgentMessage(sender=self.name, receiver=self.name, task_id=task_id, priority="high", payload={"action": "tool_result", "success": False, "result": "Agent Offline"})
            self.send_message(msg)
            return
            
        msg = AgentMessage(
            sender=self.name,
            receiver=receiver,
            task_id=task_id,
            priority="normal",
            payload={
                "action": "execute_tool",
                "tool": tool,
                "args": args
            }
        )
        self.delegation_count += 1
        self.send_message(msg)
        
        # Implement timeout handling
        async def wait_for_timeout():
            await asyncio.sleep(60.0) # 60 second timeout for any tool
            if self.active_tasks.get(task_id, {}).get("status") == "running" and self.active_tasks.get(task_id, {}).get("current_step") == task_info["current_step"]:
                logger.error(f"Tool execution timed out for {tool}")
                timeout_msg = AgentMessage(sender=self.name, receiver=self.name, task_id=task_id, priority="high", payload={"action": "tool_result", "success": False, "result": "Timeout exceeded"})
                self.send_message(timeout_msg)
                
        asyncio.create_task(wait_for_timeout())
