import json
import logging
from groq import Groq
from core.config import settings
from tools.registry import registry
from memory.database import memory_manager
import time

logger = logging.getLogger("AlchemistExecutor")

DESTRUCTIVE_TOOLS = ["delete_file", "close_application", "submit_form"]

class AgentExecutor:
    def __init__(self, broadcast_func=None):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.broadcast_func = broadcast_func

    async def execute_task(self, task_id: int) -> str:
        task = memory_manager.get_agent_task(task_id)
        if not task:
            return "Task not found."
            
        goal = task["goal"]
        steps = json.loads(task["steps_json"])
        current_step_idx = task["current_step"]
        
        logger.info(f"Starting execution for task {task_id}: {goal}")
        memory_manager.update_agent_task_status(task_id, "running")
        
        import time
        start_time = time.time()
        execution_history = []
        
        try:
            for idx in range(current_step_idx, len(steps)):
                step_data = steps[idx]
                if isinstance(step_data, str):
                    # Fallback if old format
                    logger.error(f"Invalid format: step is string '{step_data}'. Must be {{'tool': name, 'args': {{}}}}")
                    result = f"Validation Failed: Invalid schema for '{step_data}'"
                    memory_manager.update_agent_task_step(task_id, idx + 1)
                    continue

                step_tool = step_data.get("tool", "")
                args = step_data.get("args", {})

                logger.info(f"Requested Tool: {step_tool}")
                logger.info(f"Arguments: {args}")

                if "(" in step_tool or ")" in step_tool:
                    logger.warning(f"Validation Result: REJECTED - Malformed tool name {step_tool}")
                    result = f"Validation Failed: Tool name '{step_tool}' contains arguments or parentheses."
                    execution_history.append({"tool": step_tool, "args": args, "result": result})
                    memory_manager.update_agent_task_step(task_id, idx + 1)
                    continue

                if step_tool not in registry.get_registered_tools():
                    logger.warning(f"Validation Result: REJECTED - Tool {step_tool} not found in registry.")
                    result = f"Validation Failed: Tool '{step_tool}' not registered."
                    execution_history.append({"tool": step_tool, "args": args, "result": result})
                    memory_manager.update_agent_task_step(task_id, idx + 1)
                    continue
                    
                # --- SAFETY LAYER ---
                if step_tool in DESTRUCTIVE_TOOLS:
                    if args.get("confirmed") != True and args.get("confirmed") != "true":
                        logger.warning(f"Validation Result: REJECTED - {step_tool} requires confirmation.")
                        result = f"Action blocked. '{step_tool}' is a destructive action and requires user confirmation."
                        memory_manager.update_agent_task_status(task_id, "pending_confirmation")
                        execution_history.append({"tool": step_tool, "args": args, "result": result})
                        return result

                logger.info("Validation Result: PASS")

                if self.broadcast_func:
                    await self.broadcast_func({"type": "step_start", "step": step_tool, "thought": f"Executing {step_tool}"})
                
                # Execute tool with verification/retries
                max_retries = 2
                attempt = 0
                while attempt <= max_retries:
                    try:
                        result = registry.execute(step_tool, args)
                        # Basic verification string matching
                        if isinstance(result, str) and ("Error" in result or "Failed" in result):
                            raise Exception(result)
                            
                        logger.info(f"Execution Result: SUCCESS - {str(result)[:100]}")
                        break # Success
                    except Exception as e:
                        attempt += 1
                        if attempt <= max_retries:
                            logger.warning(f"Execution failed, retrying ({attempt}/{max_retries}): {e}")
                            time.sleep(1)
                        else:
                            result = f"Error executing tool {step_tool} after {max_retries} retries: {e}"
                            logger.error(f"Execution Result: ERROR - {result}")
                    
                execution_history.append({"tool": step_tool, "args": args, "result": result})
                
                if self.broadcast_func:
                    await self.broadcast_func({"type": "step_complete", "step": step_tool, "result": result})
                
                # Update DB
                memory_manager.update_agent_task_step(task_id, idx + 1)
                
                # Simple recovery: if it completely failed, we could abort, but requirements say "continue if possible"
                # For now, we continue and let the next steps figure it out from history.
                
            memory_manager.update_agent_task_status(task_id, "completed")
            
            # Post-execution Reflection
            execution_time = time.time() - start_time
            reflections, success = await self._generate_reflection(goal, execution_history)
            memory_manager.save_experience(goal, json.dumps(steps), "completed", success, execution_time, reflections)
            
            # Final summary
            final_summary = await self._generate_final_summary(goal, execution_history)
            return final_summary
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            memory_manager.update_agent_task_status(task_id, "failed")
            
            # Post-execution Reflection (Failure case)
            execution_time = time.time() - start_time
            reflections, success = await self._generate_reflection(goal, execution_history)
            memory_manager.save_experience(goal, json.dumps(steps), f"failed: {e}", False, execution_time, reflections)
            
            return f"Task failed during execution: {e}"



    async def _generate_final_summary(self, goal: str, history: list) -> str:
        history_str = json.dumps(history, indent=2)
        prompt = f"""
        You have just completed an autonomous task.
        Goal: {goal}
        
        Execution History:
        {history_str}
        
        Provide a concise final response to the user summarizing what you accomplished and what the final outcome is.
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def _generate_reflection(self, goal: str, history: list) -> tuple[str, bool]:
        history_str = json.dumps(history, indent=2)
        prompt = f"""
        You are a Self-Improvement System reflecting on a recently completed task.
        Goal: {goal}
        
        Execution History:
        {history_str}
        
        Reflect on the execution and return a STRICT JSON object:
        {{
            "what_worked": "Describe what went well",
            "what_failed": "Describe any errors or issues",
            "suggested_improvement": "How to do this better next time",
            "success": true_or_false
        }}
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content
        try:
            reply = reply.strip()
            if reply.startswith("```json"):
                reply = reply[7:]
            if reply.endswith("```"):
                reply = reply[:-3]
            data = json.loads(reply.strip())
            
            reflections = f"Worked: {data.get('what_worked', '')}\nFailed: {data.get('what_failed', '')}\nImprovement: {data.get('suggested_improvement', '')}"
            success = data.get("success", True)
            return reflections, success
        except Exception as e:
            logger.error(f"Failed to parse reflection JSON: {reply}")
            return "Failed to parse reflection.", False
