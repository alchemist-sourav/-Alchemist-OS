from agents.base_agent import BaseAgent, AgentMessage
import logging
from memory.database import memory_manager

logger = logging.getLogger("MemoryAgent")

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("memory_agent")
        
    async def process(self, message: AgentMessage):
        action = message.payload.get("action")
        
        if action == "save_memory":
            cat = message.payload.get("category")
            content = message.payload.get("content")
            memory_manager.save_semantic_memory(cat, content)
            reply_msg = AgentMessage(
                sender=self.name,
                receiver=message.sender,
                task_id=message.task_id,
                priority="low",
                payload={
                    "action": "memory_saved",
                    "success": True
                }
            )
            self.send_message(reply_msg)
            
        elif action == "retrieve_memory":
            query = message.payload.get("query")
            results = memory_manager.retrieve_semantic_memories(query)
            reply_msg = AgentMessage(
                sender=self.name,
                receiver=message.sender,
                task_id=message.task_id,
                priority="high",
                payload={
                    "action": "memory_results",
                    "results": results
                }
            )
            self.send_message(reply_msg)
