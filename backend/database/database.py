import sqlite3
import os
import json
import logging
from core.config import settings
from datetime import datetime

logger = logging.getLogger("AlchemistMemory")

DB_PATH = settings.DATABASE_PATH

class MemoryManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _execute_with_retry(self, func, *args, **kwargs):
        import time
        max_retries = 5
        for attempt in range(max_retries):
            try:
                res = func(*args, **kwargs)
                return res
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() or "locked" in str(e).lower():
                    logger.warning(f"Database locked, retrying ({attempt+1}/{max_retries})...")
                    time.sleep(1)
                else:
                    raise e
        raise Exception(f"Database transaction failed after {max_retries} retries.")

    def _init_db(self):
        # User Profiles
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS profiles (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        # Projects
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            status TEXT
        )
        """)
        # Tasks
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            description TEXT,
            status TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """)
        # Conversation Log (Short-term memory)
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            role TEXT,
            content TEXT
        )
        """)
        # Generic Long-Term Memory
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            value TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # Agent Autonomous Tasks
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            status TEXT,
            current_step INTEGER DEFAULT 0,
            steps_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
        """)
        # Agent Experiences (Self-Improvement)
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS agent_experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            plan TEXT,
            outcome TEXT,
            success BOOLEAN,
            execution_time REAL,
            reflections TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # User Preferences
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            preference_rule TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # Semantic Memories
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS semantic_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # 1. Execution Audit Log
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS agent_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            request TEXT,
            planner_decision TEXT,
            selected_tool TEXT,
            tool_args TEXT,
            execution_result TEXT,
            execution_duration REAL,
            success BOOLEAN
        )
        """)
        # 2. Tool Analytics
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS tool_metrics (
            tool_name TEXT PRIMARY KEY,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            average_execution_time REAL DEFAULT 0.0,
            failure_rate REAL DEFAULT 0.0
        )
        """)
        # 5. Error Tracking
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            exception_type TEXT,
            stack_trace TEXT,
            component TEXT,
            request_context TEXT
        )
        """)
        # Agent Messages
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS agent_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            task_id TEXT,
            priority TEXT,
            payload TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # Agent Metrics
        self._execute_with_retry(self.cursor.execute, """
        CREATE TABLE IF NOT EXISTS agent_metrics (
            agent_name TEXT PRIMARY KEY,
            active_status BOOLEAN DEFAULT 0,
            last_heartbeat DATETIME,
            task_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0.0,
            retry_count INTEGER DEFAULT 0,
            delegation_count INTEGER DEFAULT 0
        )
        """)
        
        self._execute_with_retry(self.cursor.execute, "INSERT OR IGNORE INTO projects (name, description, status) VALUES ('Alchemist OS Tasks', 'Default project for Alchemist OS tasks', 'active')")
        self._execute_with_retry(self.cursor.execute, "INSERT OR IGNORE INTO projects (name, description, status) VALUES ('Alchemist AI: Test Project', 'Test project for demos', 'active')")
        self._execute_with_retry(self.conn.commit)

    # ---- Profile Memory ----
    def save_profile(self, key: str, value: str):
        logger.info(f"Saving profile: {key} = {value}")
        self._execute_with_retry(self.cursor.execute, "INSERT OR REPLACE INTO profiles (key, value) VALUES (?, ?)", (key, value))
        self._execute_with_retry(self.conn.commit)
        return f"Profile updated: {key} is {value}"

    def get_profile(self, key: str) -> str | None:
        self._execute_with_retry(self.cursor.execute, "SELECT value FROM profiles WHERE key=?", (key,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    # ---- Project Memory ----
    def create_project(self, name: str, description: str):
        try:
            self._execute_with_retry(self.cursor.execute, "INSERT INTO projects (name, description, status) VALUES (?, ?, 'active')", (name, description))
            self._execute_with_retry(self.conn.commit)
            return f"Project '{name}' created."
        except sqlite3.IntegrityError:
            return f"Project '{name}' already exists."
            
    def get_active_projects(self):
        self._execute_with_retry(self.cursor.execute, "SELECT name, description FROM projects WHERE status='active'")
        return self.cursor.fetchall()

    # ---- Tasks Memory ----
    def add_task(self, project_name: str, description: str):
        self._execute_with_retry(self.cursor.execute, "SELECT id FROM projects WHERE name=?", (project_name,))
        row = self.cursor.fetchone()
        if not row:
            return f"Project '{project_name}' not found."
        project_id = row[0]
        self._execute_with_retry(self.cursor.execute, "INSERT INTO tasks (project_id, description, status) VALUES (?, ?, 'pending')", (project_id, description))
        self._execute_with_retry(self.conn.commit)
        return f"Task '{description}' added to project '{project_name}'."

    def get_tasks(self, project_name: str):
        self._execute_with_retry(self.cursor.execute, "SELECT id FROM projects WHERE name=?", (project_name,))
        row = self.cursor.fetchone()
        if not row:
            return f"Project '{project_name}' not found."
        project_id = row[0]
        self._execute_with_retry(self.cursor.execute, "SELECT id, description, status FROM tasks WHERE project_id=?", (project_id,))
        return self.cursor.fetchall()

    def update_task_status(self, task_id: int, status: str):
        self._execute_with_retry(self.cursor.execute, "UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        self._execute_with_retry(self.conn.commit)
        return f"Task {task_id} status updated to {status}."

    def delete_task(self, task_id: int):
        self._execute_with_retry(self.cursor.execute, "DELETE FROM tasks WHERE id=?", (task_id,))
        self._execute_with_retry(self.conn.commit)
        return f"Task {task_id} deleted."

    # ---- Conversation Memory ----
    def save_conversation(self, role: str, content: str):
        self._execute_with_retry(self.cursor.execute, "INSERT INTO conversations (role, content) VALUES (?, ?)", (role, content))
        self._execute_with_retry(self.conn.commit)
        self.trim_conversations(100)

    def trim_conversations(self, keep_limit: int = 100):
        try:
            self._execute_with_retry(self.cursor.execute, """
                DELETE FROM conversations 
                WHERE id NOT IN (
                    SELECT id FROM conversations 
                    ORDER BY id DESC LIMIT ?
                )
            """, (keep_limit,))
            self._execute_with_retry(self.conn.commit)
        except Exception as e:
            logger.error(f"Error trimming conversation history: {e}")

    def get_recent_conversations(self, limit: int = 20):
        self._execute_with_retry(self.cursor.execute, "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
        rows = self.cursor.fetchall()
        return rows[::-1] # Reverse to get chronological order

    # ---- Generic / Legacy Memory ----
    def save_memory(self, key: str, value: str) -> str:
        logger.info(f"Saving memory: {key} = {value}")
        self._execute_with_retry(self.cursor.execute, 
            "INSERT INTO long_term_memory (key, value) VALUES (?, ?)",
            (key, value)
        )
        self._execute_with_retry(self.conn.commit)
        return f"Saved memory: {key} is {value}"

    def get_memory(self, key: str) -> str | None:
        self._execute_with_retry(self.cursor.execute, 
            "SELECT value FROM long_term_memory WHERE key=? ORDER BY id DESC LIMIT 1",
            (key,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    # ---- Agent Tasks Memory ----
    def create_agent_task(self, goal: str, steps_json: str) -> int:
        self._execute_with_retry(self.cursor.execute, 
            "INSERT INTO agent_tasks (goal, status, current_step, steps_json) VALUES (?, 'pending', 0, ?)",
            (goal, steps_json)
        )
        self._execute_with_retry(self.conn.commit)
        return self.cursor.lastrowid

    def update_agent_task_status(self, task_id: int, status: str):
        if status in ['completed', 'failed']:
            self._execute_with_retry(self.cursor.execute, 
                "UPDATE agent_tasks SET status=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
                (status, task_id)
            )
        else:
            self._execute_with_retry(self.cursor.execute, 
                "UPDATE agent_tasks SET status=? WHERE id=?",
                (status, task_id)
            )
        self._execute_with_retry(self.conn.commit)

    def update_agent_task_step(self, task_id: int, step_index: int):
        self._execute_with_retry(self.cursor.execute, 
            "UPDATE agent_tasks SET current_step=? WHERE id=?",
            (step_index, task_id)
        )
        self._execute_with_retry(self.conn.commit)

    def get_agent_task(self, task_id: int) -> dict | None:
        self._execute_with_retry(self.cursor.execute, 
            "SELECT id, goal, status, current_step, steps_json, created_at, completed_at FROM agent_tasks WHERE id=?",
            (task_id,)
        )
        row = self.cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "goal": row[1],
                "status": row[2],
                "current_step": row[3],
                "steps_json": row[4],
                "created_at": row[5],
                "completed_at": row[6]
            }
        return None

    # ---- Experience & Reflection Memory ----
    def save_experience(self, goal: str, plan: str, outcome: str, success: bool, execution_time: float, reflections: str):
        self._execute_with_retry(self.cursor.execute, 
            "INSERT INTO agent_experiences (goal, plan, outcome, success, execution_time, reflections) VALUES (?, ?, ?, ?, ?, ?)",
            (goal, plan, outcome, success, execution_time, reflections)
        )
        self._execute_with_retry(self.conn.commit)

    def get_similar_experiences(self, keyword: str, limit: int = 3) -> list:
        search_term = f"%{keyword}%"
        self._execute_with_retry(self.cursor.execute, 
            "SELECT goal, plan, outcome, reflections, success FROM agent_experiences WHERE goal LIKE ? OR reflections LIKE ? ORDER BY created_at DESC LIMIT ?",
            (search_term, search_term, limit)
        )
        return self.cursor.fetchall()

    def get_agent_metrics(self) -> dict:
        self._execute_with_retry(self.cursor.execute, "SELECT COUNT(*), SUM(CASE WHEN success=1 THEN 1 ELSE 0 END), AVG(execution_time) FROM agent_experiences")
        row = self.cursor.fetchone()
        total_tasks = row[0] or 0
        successful_tasks = row[1] or 0
        avg_time = row[2] or 0.0
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        return {
            "total_tasks": total_tasks,
            "success_rate": success_rate,
            "avg_execution_time": avg_time
        }

    # ---- Observability & Admin ----
    def save_execution_log(self, session_id: str, request: str, planner_decision: str, selected_tool: str, tool_args: str, execution_result: str, execution_duration: float, success: bool):
        self._execute_with_retry(self.cursor.execute, 
            "INSERT INTO agent_execution_logs (session_id, request, planner_decision, selected_tool, tool_args, execution_result, execution_duration, success) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (session_id, request, planner_decision, selected_tool, tool_args, execution_result, execution_duration, success)
        )
        
        # Update tool_metrics automatically
        self._execute_with_retry(self.cursor.execute, "SELECT usage_count, success_rate, average_execution_time FROM tool_metrics WHERE tool_name=?", (selected_tool,))
        row = self.cursor.fetchone()
        if row:
            usage_count = row[0] + 1
            # Recalculate averages
            old_success_count = (row[1] / 100.0) * row[0]
            new_success_count = old_success_count + (1 if success else 0)
            new_success_rate = (new_success_count / usage_count) * 100.0
            new_failure_rate = 100.0 - new_success_rate
            
            new_avg_time = ((row[2] * row[0]) + execution_duration) / usage_count
            self._execute_with_retry(self.cursor.execute,
                "UPDATE tool_metrics SET usage_count=?, success_rate=?, average_execution_time=?, failure_rate=? WHERE tool_name=?",
                (usage_count, new_success_rate, new_avg_time, new_failure_rate, selected_tool)
            )
        else:
            new_success_rate = 100.0 if success else 0.0
            new_failure_rate = 100.0 - new_success_rate
            self._execute_with_retry(self.cursor.execute,
                "INSERT INTO tool_metrics (tool_name, usage_count, success_rate, average_execution_time, failure_rate) VALUES (?, 1, ?, ?, ?)",
                (selected_tool, new_success_rate, execution_duration, new_failure_rate)
            )
        self._execute_with_retry(self.conn.commit)

    def save_error_log(self, exception_type: str, stack_trace: str, component: str, request_context: str):
        self._execute_with_retry(self.cursor.execute, 
            "INSERT INTO error_logs (exception_type, stack_trace, component, request_context) VALUES (?, ?, ?, ?)",
            (exception_type, stack_trace, component, request_context)
        )
        self._execute_with_retry(self.conn.commit)

    def get_execution_logs(self, limit: int = 50):
        self._execute_with_retry(self.cursor.execute, "SELECT id, timestamp, session_id, request, planner_decision, selected_tool, tool_args, execution_result, execution_duration, success FROM agent_execution_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [{"id": r[0], "timestamp": r[1], "session_id": r[2], "request": r[3], "planner_decision": r[4], "selected_tool": r[5], "tool_args": r[6], "execution_result": r[7], "execution_duration": r[8], "success": r[9]} for r in self.cursor.fetchall()]

    def get_tool_metrics(self):
        self._execute_with_retry(self.cursor.execute, "SELECT tool_name, usage_count, success_rate, average_execution_time, failure_rate FROM tool_metrics ORDER BY usage_count DESC")
        return [{"tool_name": r[0], "usage_count": r[1], "success_rate": r[2], "average_execution_time": r[3], "failure_rate": r[4]} for r in self.cursor.fetchall()]

    def get_error_logs(self, limit: int = 50):
        self._execute_with_retry(self.cursor.execute, "SELECT id, timestamp, exception_type, stack_trace, component, request_context FROM error_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [{"id": r[0], "timestamp": r[1], "exception_type": r[2], "stack_trace": r[3], "component": r[4], "request_context": r[5]} for r in self.cursor.fetchall()]

    # ---- User Preferences ----
    def save_preference(self, category: str, preference_rule: str) -> str:
        self._execute_with_retry(self.cursor.execute, 
            "INSERT INTO user_preferences (category, preference_rule) VALUES (?, ?)",
            (category, preference_rule)
        )
        self._execute_with_retry(self.conn.commit)
        return f"Saved preference for {category}."

    def get_all_preferences(self) -> list:
        self._execute_with_retry(self.cursor.execute, "SELECT category, preference_rule FROM user_preferences ORDER BY created_at ASC")
        return self.cursor.fetchall()

    def show_successful_workflows(self) -> str:
        self._execute_with_retry(self.cursor.execute, "SELECT goal, plan, reflections FROM agent_experiences WHERE success=1 ORDER BY created_at DESC LIMIT 5")
        rows = self.cursor.fetchall()
        if not rows: return "No successful workflows found."
        res = "Successful Workflows:\n"
        for goal, plan, ref in rows:
            res += f"- Goal: {goal}\n  Plan: {plan}\n  Reflections: {ref}\n"
        return res

    def show_failed_tasks(self) -> str:
        self._execute_with_retry(self.cursor.execute, "SELECT goal, outcome, reflections FROM agent_experiences WHERE success=0 ORDER BY created_at DESC LIMIT 5")
        rows = self.cursor.fetchall()
        if not rows: return "No failed tasks found."
        res = "Failed Tasks:\n"
        for goal, outcome, ref in rows:
            res += f"- Goal: {goal}\n  Error: {outcome}\n  Reflections: {ref}\n"
        return res

    def save_semantic_memory(self, category: str, content: str):
        logger.info(f"Saving semantic memory [{category}]: {content}")
        self._execute_with_retry(self.cursor.execute, 
            "INSERT INTO semantic_memories (category, content) VALUES (?, ?)",
            (category, content)
        )
        self._execute_with_retry(self.conn.commit)
        return f"Memory saved: [{category}] {content}"

    def retrieve_semantic_memories(self, query: str, limit: int = 5) -> list:
        # Retrieve all semantic memories
        self._execute_with_retry(self.cursor.execute, "SELECT category, content FROM semantic_memories")
        rows = self.cursor.fetchall()
        if not rows:
            return []
            
        import re
        import math
        
        def tokenize(text):
            return re.findall(r'[a-zA-Z0-9_]+', text.lower())
            
        def get_freq_dict(tokens):
            d = {}
            for t in tokens:
                d[t] = d.get(t, 0) + 1
            return d
            
        query_tokens = tokenize(query)
        if not query_tokens:
            return rows[:limit]
            
        query_freq = get_freq_dict(query_tokens)
        
        results = []
        for category, content in rows:
            content_tokens = tokenize(content)
            content_freq = get_freq_dict(content_tokens)
            
            all_words = set(query_freq.keys()) | set(content_freq.keys())
            v1 = [query_freq.get(w, 0) for w in all_words]
            v2 = [content_freq.get(w, 0) for w in all_words]
            
            dot_product = sum(x*y for x, y in zip(v1, v2))
            mag1 = math.sqrt(sum(x*x for x in v1))
            mag2 = math.sqrt(sum(x*x for x in v2))
            
            similarity = dot_product / (mag1 * mag2) if (mag1 > 0 and mag2 > 0) else 0.0
            results.append((category, content, similarity))
            
        results.sort(key=lambda x: x[2], reverse=True)
        filtered = [r for r in results if r[2] > 0.0]
        if not filtered:
            for category, content in rows:
                if any(q in content.lower() for q in query_tokens):
                    filtered.append((category, content, 0.1))
        
        return [(r[0], r[1]) for r in filtered[:limit]]

memory_manager = MemoryManager()

from tools.registry import registry
registry.register("create_project", memory_manager.create_project)
registry.register("add_task", memory_manager.add_task)
registry.register("get_tasks", memory_manager.get_tasks)
registry.register("update_task_status", memory_manager.update_task_status)
registry.register("delete_task", memory_manager.delete_task)
registry.register("save_preference", memory_manager.save_preference)
registry.register("get_all_preferences", memory_manager.get_all_preferences)
registry.register("get_agent_metrics", memory_manager.get_agent_metrics)
registry.register("show_successful_workflows", memory_manager.show_successful_workflows)
registry.register("show_failed_tasks", memory_manager.show_failed_tasks)
registry.register("get_profile", memory_manager.get_profile)
registry.register("save_profile", memory_manager.save_profile)
registry.register("get_memory", memory_manager.get_memory)
registry.register("save_memory", memory_manager.save_memory)
registry.register("save_semantic_memory", memory_manager.save_semantic_memory)
registry.register("retrieve_semantic_memories", memory_manager.retrieve_semantic_memories)
