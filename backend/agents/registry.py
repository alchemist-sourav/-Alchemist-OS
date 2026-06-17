from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentMessage
import logging
from database.database import memory_manager

logger = logging.getLogger("AgentRegistry")

class Registry:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.name] = agent
        logger.info(f"Registered Agent: {agent.name}")

    def get_agent(self, name: str) -> BaseAgent | None:
        return self.agents.get(name)

    def list_agents(self) -> List[str]:
        return list(self.agents.keys())

    def health_check(self) -> Dict[str, Any]:
        health = {}
        for name, agent in self.agents.items():
            health[name] = {
                "active": agent.active,
                "task_count": agent.task_count,
                "failure_count": agent.failure_count
            }
        return health

    async def route_message(self, message: AgentMessage):
        if message.receiver == "broadcast":
            for name, agent in self.agents.items():
                if name != message.sender:
                    await agent.handle_message(message)
        else:
            agent = self.get_agent(message.receiver)
            if agent:
                await agent.handle_message(message)
            else:
                logger.error(f"Cannot route message. Agent not found: {message.receiver}")

AgentRegistry = Registry()
