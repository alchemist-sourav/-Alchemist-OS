from agents.base_agent import BaseAgent, AgentMessage
import logging
from tools.registry import registry

logger = logging.getLogger("SystemAgent")

class SystemAgent(BaseAgent):
    def __init__(self):
        super().__init__("system_agent")
        
    async def process(self, message: AgentMessage):
        action = message.payload.get("action")
        tool = message.payload.get("tool")
        args = message.payload.get("args", {})
        
        if action == "execute_tool":
            logger.info(f"System Agent executing tool: {tool}")
            try:
                result = await registry.execute(tool, args)
                success = True
            except Exception as e:
                result = str(e)
                success = False
                
            reply_msg = AgentMessage(
                sender=self.name,
                receiver=message.sender,
                task_id=message.task_id,
                priority="high",
                payload={
                    "action": "tool_result",
                    "tool": tool,
                    "result": result,
                    "success": success
                }
            )
            self.send_message(reply_msg)
