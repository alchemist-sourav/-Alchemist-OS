from agents.base_agent import BaseAgent, AgentMessage
import logging
from voice.engine import VoiceEngine

logger = logging.getLogger("VoiceAgent")

class VoiceAgent(BaseAgent):
    def __init__(self):
        super().__init__("voice_agent")
        self.engine = VoiceEngine()
        
    async def process(self, message: AgentMessage):
        action = message.payload.get("action")
        
        if action == "speak":
            text = message.payload.get("text")
            logger.info(f"Voice Agent speaking: {text}")
            self.engine.speak(text)
            
            reply_msg = AgentMessage(
                sender=self.name,
                receiver=message.sender,
                task_id=message.task_id,
                priority="normal",
                payload={
                    "action": "speak_complete"
                }
            )
            self.send_message(reply_msg)
