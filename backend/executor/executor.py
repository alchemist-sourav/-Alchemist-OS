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
        step_results = {}
        
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

                # Perform variable substitution
                class FallbackDict(dict):
                    def __missing__(self, key):
                        if "result" in self:
                            return self["result"]
                        return "{" + key + "}"

                import re
                def repl_at(m):
                    key = m.group(1)
                    if key in step_results: return str(step_results[key])
                    if "result" in step_results: return str(step_results["result"])
                    return m.group(0)

                for k, v in args.items():
                    if isinstance(v, str):
                        try:
                            # Handle {var}
                            v = v.format_map(FallbackDict(step_results))
                            # Handle @var
                            v = re.sub(r"@([a-zA-Z0-9_]+)", repl_at, v)
                            args[k] = v
                        except Exception as e:
                            logger.error(f"Error formatting argument {k}: {e}")

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
                DESTRUCTIVE_TOOLS = ["delete_file", "move_file", "kill_process", "submit_form", "shutdown_pc"]
                if step_tool in DESTRUCTIVE_TOOLS:
                    if args.get("confirmed") != True and args.get("confirmed") != "true":
                        logger.warning(f"Validation Result: REJECTED - {step_tool} requires confirmation.")
                        result = f"Action blocked. '{step_tool}' is a protected action and requires user confirmation."
                        memory_manager.update_agent_task_status(task_id, "pending_confirmation")
                        execution_history.append({"tool": step_tool, "args": args, "result": result})
                        if self.broadcast_func:
                            await self.broadcast_func({
                                "type": "pending_confirmation",
                                "task_id": task_id,
                                "tool": step_tool,
                                "args": args,
                                "message": result
                            })
                        return result

                logger.info("Validation Result: PASS")

                if self.broadcast_func:
                    await self.broadcast_func({"type": "step_start", "step": step_tool, "thought": f"Executing {step_tool}"})
                
                # Execute tool with verification/retries
                max_retries = 2
                attempt = 0
                while attempt <= max_retries:
                    try:
                        result = await registry.execute(step_tool, args)
                        # Basic verification string matching
                        if isinstance(result, str) and ("Error" in result or "Failed" in result):
                            raise Exception(result)
                            
                        logger.info(f"Execution Result: SUCCESS - {str(result)[:100]}")
                        
                        step_results[step_tool] = result
                        step_results["result"] = result
                        if step_tool == "get_current_datetime":
                            step_results["current_time"] = result
                            
                        break # Success
                    except Exception as e:
                        attempt += 1
                        if attempt <= max_retries:
                            logger.warning(f"Execution failed, retrying ({attempt}/{max_retries}): {e}")
                            time.sleep(1)
                        else:
                            result = f"Error executing tool {step_tool} after {max_retries} retries: {e}"
                            logger.error(f"Execution Result: ERROR - {result}")
                            
                            # Trigger automated replanning
                            logger.info(f"Triggering automated replanning for task {task_id} due to failure at step {step_tool}...")
                            success_replanned = await self._replan_task(task_id, idx, step_tool, result)
                            if success_replanned:
                                return await self.execute_task(task_id)
                    
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

    async def _replan_task(self, task_id: int, failed_step_idx: int, failed_tool: str, error_msg: str) -> bool:
        try:
            task = memory_manager.get_agent_task(task_id)
            goal = task["goal"]
            all_steps = json.loads(task["steps_json"])
            completed_steps = all_steps[:failed_step_idx]
            
            history_summary = ""
            for s in completed_steps:
                history_summary += f"- Step: {s.get('tool')}, Args: {s.get('args')} -> SUCCESS\n"
            history_summary += f"- Step: {failed_tool} -> FAILED with error: {error_msg}\n"
            
            prompt = f"""
            You are Alchemist AI's Recovery Planner.
            The user request is: "{goal}"
            
            We were executing a plan, but it failed.
            Execution History:
            {history_summary}
            
            Please generate a new set of steps to complete the goal from the current state.
            Format your output STRICTLY as a JSON object with:
            {{
              "goal": "{goal}",
              "steps": [
                {{
                  "tool": "tool_name_here",
                  "args": {{
                    "arg_key": "arg_value"
                  }}
                }}
              ]
            }}
            """
            from planner.planner import TaskPlanner, extract_and_parse_json
            planner = TaskPlanner()
            reply = planner.llm_provider.generate_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            data = extract_and_parse_json(reply)
            new_steps = data.get("steps", [])
            
            if not new_steps:
                logger.warning("Recovery planner did not generate any new steps.")
                return False
                
            updated_steps = completed_steps + new_steps
            memory_manager.cursor.execute(
                "UPDATE agent_tasks SET steps_json=?, current_step=? WHERE id=?",
                (json.dumps(updated_steps), failed_step_idx, task_id)
            )
            memory_manager.conn.commit()
            logger.info(f"Task {task_id} successfully replanned. New steps: {new_steps}")
            
            if self.broadcast_func:
                await self.broadcast_func({
                    "type": "plan_replanned",
                    "task_id": task_id,
                    "goal": goal,
                    "new_steps": new_steps
                })
            return True
        except Exception as e:
            logger.error(f"Failed to replan task {task_id}: {e}")
            return False

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
        import re
        reply = response.choices[0].message.content
        try:
            reply = re.sub(r"^```(?:json)?\s*", "", reply.strip(), flags=re.IGNORECASE)
            reply = re.sub(r"\s*```$", "", reply)
            reply = reply.strip()
            data = json.loads(reply)
            
            reflections = f"Worked: {data.get('what_worked', '')}\nFailed: {data.get('what_failed', '')}\nImprovement: {data.get('suggested_improvement', '')}"
            success = data.get("success", True)
            return reflections, success
        except Exception as e:
            logger.error(f"Failed to parse reflection JSON: {reply}")
            return "Failed to parse reflection.", False

async def resume_agent_execution(task_id: int, confirm: bool, broadcast_func) -> str:
    task = memory_manager.get_agent_task(task_id)
    if not task:
        return "Task not found."
        
    if not confirm:
        memory_manager.update_agent_task_status(task_id, "failed")
        if broadcast_func:
            await broadcast_func({"type": "step_complete", "step": "Action Cancelled", "result": "Action rejected by user."})
        return "Action rejected by user. Task aborted."

    steps = json.loads(task["steps_json"])
    current_idx = task["current_step"]
    
    if current_idx < len(steps):
        steps[current_idx]["args"]["confirmed"] = True
        
        memory_manager.cursor.execute(
            "UPDATE agent_tasks SET steps_json=?, status='running' WHERE id=?",
            (json.dumps(steps), task_id)
        )
        memory_manager.conn.commit()
        
        executor = AgentExecutor(broadcast_func=broadcast_func)
        return await executor.execute_task(task_id)
    return "No remaining steps to execute."
