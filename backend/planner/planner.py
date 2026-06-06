import json
import logging
from groq import Groq
from core.config import settings
from memory.database import memory_manager
from tools.registry import registry

logger = logging.getLogger("AlchemistPlanner")

class TaskPlanner:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.base_system_prompt = """
You are Alchemist AI, a powerful task planning agent.
Available tools:
- search_google(query)
- open_website(url)
- read_page_title(url)
- navigate_page(url)
- browser_start(url)
- browser_click(selector)
- browser_type(selector, text)
- browser_get_html()
- browser_close()
- extract_page_text()
- open_youtube()
- open_google()
- open_github()
- open_linkedin()
- open_chatgpt()
- open_calculator()
- open_notepad()
- launch_application(app_name_or_path)
- create_file(filename)
- read_file(filename)
- delete_file(filename)
- list_directory(path)
- search_files(query, path)
- move_file(src, dest)
- read_metadata(path)
- take_screenshot()
- capture_screen()
- save_screenshot()
- capture_active_window()
- open_url(url)
- click_element(selector)
- type_into_field(selector, text)
- extract_page_text()
- navigate_back()
- submit_form(selector) [DESTRUCTIVE: Requires "confirmed": true]
- delete_file(filename) [DESTRUCTIVE: Requires "confirmed": true]
- search_google(query)
- open_linkedin()
- open_github()
- open_chatgpt()
- analyze_screen()
- read_screen_text()
- identify_active_window()
- move_mouse(x, y)
- click_mouse(x, y)
- double_click(x, y)
- type_text(text)
- press_key(key)
- read_clipboard()
- write_clipboard(text)
- get_current_datetime()
- add_calendar_event(date_str, event_desc)
- read_calendar(date_str)
- add_note(note_text)
- read_notes()
- add_task(project_name, description)
- get_tasks(project_name)
- update_task_status(task_id, status)
- delete_task(task_id)
- save_preference(category, preference_rule)
- get_all_preferences()
- get_agent_metrics()
- show_successful_workflows()
- show_failed_tasks()

Your goal is to break down user requests into actionable steps and return JSON.
Format your output STRICTLY as a JSON object with:
{
  "goal": "Clear summary of the user's objective",
  "steps": [
    {
      "tool": "tool_name_here",
      "args": {
        "arg_key": "arg_value"
      }
    }
  ]
}
CRITICAL: The `tool` field MUST be exactly the tool name. DO NOT include parentheses or arguments in the tool name. Put arguments in the `args` object.
If the request is conversational and requires no tools, return:
{
  "goal": "respond",
  "steps": [],
  "thought": "Your response to the user"
}
"""

    def _build_context_prompt(self, user_text: str = ""):
        # 1. Profile Memory
        name = memory_manager.get_profile("name")
        profile_str = f"User Name: {name}" if name else "User Name: Unknown"

        # 2. Active Projects & Tasks
        projects = memory_manager.get_active_projects()
        proj_str = "Active Projects:\n"
        if projects:
            for p_name, p_desc in projects:
                proj_str += f"- {p_name}: {p_desc}\n"
                tasks = memory_manager.get_tasks(p_name)
                for t in tasks:
                    proj_str += f"  * [ID: {t[0]}] {t[1]} ({t[2]})\n"
        else:
            proj_str += "None\n"

        # 3. Recent Conversation History
        convos = memory_manager.get_recent_conversations(5)
        convo_str = "Recent Conversation History:\n"
        for role, content in convos:
            convo_str += f"{role.capitalize()}: {content}\n"

        # 4. User Preferences
        prefs = memory_manager.get_all_preferences()
        pref_str = "User Preferences:\n"
        if prefs:
            for cat, rule in prefs:
                pref_str += f"- {cat}: {rule}\n"
        else:
            pref_str += "None\n"

        # 5. Past Experiences (Self-Improvement)
        exp_str = "Relevant Past Experiences:\n"
        # Simple keyword extraction (longest word > 4 chars)
        words = [w for w in user_text.split() if len(w) > 4]
        keyword = words[0] if words else "task"
        experiences = memory_manager.get_similar_experiences(keyword, limit=2)
        
        if experiences:
            for goal, plan, outcome, reflections, success in experiences:
                exp_str += f"- Goal: {goal}\n  Success: {success}\n  Reflections: {reflections}\n"
        else:
            exp_str += "None\n"

        context = f"""
--- CURRENT CONTEXT ---
{profile_str}

{proj_str}
{convo_str}
{pref_str}
{exp_str}
-----------------------
"""
        return self.base_system_prompt + "\n" + context

    async def process_request(self, user_text: str, broadcast_func) -> str:
        # Save user message
        memory_manager.save_conversation("user", user_text)

        user_input_lower = user_text.lower()
        
        # Pre-process generic memory mapping (fallback)
        if user_input_lower.startswith("remember"):
            try:
                content = user_input_lower.replace("remember", "").strip()
                if " is " in content:
                    key, value = content.split(" is ", 1)
                    if key == "my name":
                        result = memory_manager.save_profile("name", value.strip())
                    else:
                        result = memory_manager.save_memory(key.strip(), value.strip())
                    memory_manager.save_conversation("assistant", result)
                    return result
            except Exception as e:
                logger.error(f"Memory parse error: {e}")

        if "what is my" in user_input_lower:
            key = user_input_lower.replace("what is my", "").strip()
            if key == "name":
                memory = memory_manager.get_profile("name")
            else:
                memory = memory_manager.get_memory(key)
            
            if memory:
                result = f"Your {key} is {memory}"
            else:
                result = f"I do not know what your {key} is."
            memory_manager.save_conversation("assistant", result)
            return result

        # Pass to Groq
        try:
            dynamic_prompt = self._build_context_prompt(user_text)
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": dynamic_prompt},
                    {"role": "user", "content": user_text}
                ]
            )
            
            reply = response.choices[0].message.content
            logger.info(f"Groq Response: {reply}")
            
            try:
                # Clean up markdown if any
                reply = reply.strip()
                if reply.startswith("```json"):
                    reply = reply[7:]
                if reply.endswith("```"):
                    reply = reply[:-3]
                    
                data = json.loads(reply.strip())
                
                goal = data.get("goal", "")
                steps = data.get("steps", [])
                
                if not steps:
                    thought = data.get("thought", "I cannot fulfill this right now.")
                    memory_manager.save_conversation("assistant", thought)
                    return thought
                
                # Import Executor dynamically to avoid circular issues
                from executor.executor import AgentExecutor
                
                # Create Task
                steps_json = json.dumps(steps)
                task_id = memory_manager.create_agent_task(goal, steps_json)
                
                if broadcast_func:
                    await broadcast_func({"type": "plan_created", "task_id": task_id, "goal": goal, "steps": steps})
                
                executor = AgentExecutor(broadcast_func=broadcast_func)
                final_result = await executor.execute_task(task_id)
                
                memory_manager.save_conversation("assistant", final_result)
                return final_result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON Parsing Error: {e} - Response: {reply}")
                return f"Internal Error: Failed to parse planner response: {reply}"

        except Exception as e:
            logger.error(f"Planner Error: {e}")
            error_reply = "Sorry, I encountered an error while connecting to the AI."
            memory_manager.save_conversation("assistant", error_reply)
            return error_reply
