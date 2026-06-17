import time
from typing import Dict, Any, Callable
from database.database import memory_manager
import logging
from dataclasses import dataclass, asdict
import json
from datetime import datetime

logger = logging.getLogger("AlchemistAgent")

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    task_id: str
    priority: str
    payload: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.active = True
        self.last_heartbeat = time.time()
        self.task_count = 0
        self.failure_count = 0
        self.total_response_time = 0.0
        self.retry_count = 0
        self.delegation_count = 0
        
        self._update_metrics()
        
    def _update_metrics(self):
        avg_rt = self.total_response_time / self.task_count if self.task_count > 0 else 0.0
        memory_manager._execute_with_retry(
            memory_manager.cursor.execute,
            "INSERT OR REPLACE INTO agent_metrics (agent_name, active_status, last_heartbeat, task_count, failure_count, avg_response_time, retry_count, delegation_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (self.name, self.active, datetime.fromtimestamp(self.last_heartbeat).isoformat(), self.task_count, self.failure_count, avg_rt, self.retry_count, self.delegation_count)
        )
        memory_manager._execute_with_retry(memory_manager.conn.commit)
        
    def heartbeat(self):
        self.last_heartbeat = time.time()
        self.active = True
        self._update_metrics()

    def send_message(self, message: AgentMessage):
        payload_str = json.dumps(message.payload)
        memory_manager._execute_with_retry(
            memory_manager.cursor.execute,
            "INSERT INTO agent_messages (sender, receiver, task_id, priority, payload, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (message.sender, message.receiver, message.task_id, message.priority, payload_str, message.timestamp)
        )
        memory_manager._execute_with_retry(memory_manager.conn.commit)
        
        # Route through registry bus if needed
        from agents.registry import AgentRegistry
        import asyncio
        asyncio.create_task(AgentRegistry.route_message(message))

    async def handle_message(self, message: AgentMessage):
        start_time = time.time()
        self.heartbeat()
        try:
            await self.process(message)
            self.task_count += 1
        except Exception as e:
            logger.error(f"Agent {self.name} failed to process message: {e}")
            self.failure_count += 1
            self.task_count += 1
        finally:
            self.total_response_time += (time.time() - start_time)
            self._update_metrics()
            
    async def process(self, message: AgentMessage):
        raise NotImplementedError("Subclasses must implement process()")
