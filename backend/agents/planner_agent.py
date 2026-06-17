from agents.base_agent import BaseAgent, AgentMessage
from planner.planner import TaskPlanner
import logging

logger = logging.getLogger("PlannerAgent")

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner_agent")
        self.planner = TaskPlanner()
        self.pending_plans = {}
        
    async def process(self, message: AgentMessage):
        action = message.payload.get("action")
        
        if action == "plan_task":
            user_text = message.payload.get("user_text")
            logger.info(f"Planner Agent received task: {user_text}")
            
            # Step 1: Request memory context
            self.pending_plans[message.task_id] = user_text
            
            mem_msg = AgentMessage(
                sender=self.name,
                receiver="memory_agent",
                task_id=message.task_id,
                priority="high",
                payload={
                    "action": "retrieve_memory",
                    "query": user_text
                }
            )
            self.send_message(mem_msg)
            
        elif action == "memory_results":
            user_text = self.pending_plans.pop(message.task_id, None)
            if not user_text:
                return
                
            memories = message.payload.get("results", [])
            memory_context = "\n".join([f"- [{cat}] {content}" for cat, content in memories])
            logger.info(f"Planner Agent generating plan with memory context: {memory_context}")
            
            dynamic_prompt = self.planner._build_context_prompt(user_text)
            if memory_context:
                dynamic_prompt += f"\n\nRelevant Memories:\n{memory_context}"
                
            messages = [{"role": "system", "content": dynamic_prompt}, {"role": "user", "content": user_text}]
            
            reply = self.planner.llm_provider.generate_completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            from planner.planner import extract_and_parse_json
            data = extract_and_parse_json(reply)
            
            from orchestration.orchestrator import orchestrator
            import asyncio
            
            goal = data.get("goal", "respond")
            steps = data.get("steps", [])
            thought = data.get("thought", "")
            
            # Send message to UI that plan is ready (if needed)
            reply_msg = AgentMessage(
                sender=self.name,
                receiver="websocket", # In a real system, websocket handler receives this
                task_id=message.task_id,
                priority="normal",
                payload={
                    "action": "plan_result",
                    "goal": goal,
                    "thought": thought
                }
            )
            # Directly broadcast plan result to all WebSocket clients instead of routing via AgentRegistry
            try:
                from main import manager
                import json as _json
                async def broadcast_plan():
                    payload = _json.dumps({
                        "type": "plan_result",
                        "task_id": message.task_id,
                        "goal": goal,
                        "thought": thought,
                        "steps": steps
                    })
                    for ws in manager.active_connections:
                        await manager.send_personal_message(_json.loads(payload), ws)
                asyncio.create_task(broadcast_plan())
            except Exception:
                pass
            
            # If voice agent is to be used, speak the thought
            if thought:
                voice_msg = AgentMessage(
                    sender=self.name,
                    receiver="voice_agent",
                    task_id=message.task_id,
                    priority="normal",
                    payload={"action": "speak", "text": thought}
                )
                self.send_message(voice_msg)
            
            if steps:
                asyncio.create_task(orchestrator.route_task(message.task_id, goal, steps))
