import json
import logging
import re
import asyncio
from groq import Groq
from core.config import settings
from database.database import memory_manager
from tools.registry import registry

logger = logging.getLogger("AlchemistPlanner")

def parse_first_json_object(text: str) -> dict:
    first_brace = text.find('{')
    if first_brace == -1:
        raise json.JSONDecodeError("No JSON object found in text", text, 0)
    
    brace_count = 0
    in_string = False
    escape_active = False
    
    for i in range(first_brace, len(text)):
        char = text[i]
        
        if escape_active:
            escape_active = False
            continue
            
        if char == '\\':
            escape_active = True
            continue
            
        if char == '"':
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_candidate = text[first_brace:i+1]
                    return json.loads(json_candidate)
                    
    raise json.JSONDecodeError("Braces do not match", text, first_brace)

def extract_and_parse_json(text: str) -> dict:
    text_stripped = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text_stripped)
    except json.JSONDecodeError:
        pass
        
    # Clean markdown code blocks if present
    clean_text = text_stripped
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass
        
    # Bracket matching fallback
    try:
        return parse_first_json_object(clean_text)
    except Exception as e_bracket:
        # Regex matching fallback
        match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        raise json.JSONDecodeError(f"Failed to extract valid JSON: {str(e_bracket)}", text, 0)


class TaskPlanner:
    def __init__(self):
        from core.providers import ProviderManager
        self.llm_provider = ProviderManager.get_llm_provider()
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
- write_file(filename, content)
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
- create_project(name, description)
- add_task(project_name, description)
- get_tasks(project_name)
- update_task_status(task_id, status)
- delete_task(task_id)
- save_preference(category, preference_rule)
- get_all_preferences()
- get_agent_metrics()
- show_successful_workflows()
- show_failed_tasks()
- get_profile(key)
- save_profile(key, value)
- get_memory(key)
- save_memory(key, value)

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
CRITICAL: For questions about the user's name, preferences, favorite things, or past information, YOU MUST generate steps using get_profile or get_memory instead of answering from your general knowledge.
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

        # Pass to Groq
        try:
            dynamic_prompt = self._build_context_prompt(user_text)
            
            # Retrieve recent conversation history (last 10 messages)
            convos = memory_manager.get_recent_conversations(10)
            
            messages = [{"role": "system", "content": dynamic_prompt}]
            
            # Build messages array from history
            has_current_user_msg = False
            for role, content in convos:
                api_role = "assistant" if role == "assistant" else "user"
                messages.append({"role": api_role, "content": content})
                if api_role == "user" and content == user_text:
                    has_current_user_msg = True
            
            if not has_current_user_msg:
                messages.append({"role": "user", "content": user_text})
            
            reply = self.llm_provider.generate_completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            logger.info(f"Planner response: {reply}")
            
            try:
                data = extract_and_parse_json(reply)
                
                goal = data.get("goal", "respond")
                steps = data.get("steps", [])
                
                if not steps:
                    thought = data.get("thought", "I cannot fulfill this right now.")
                    memory_manager.save_conversation("assistant", thought)
                    asyncio.create_task(self._extract_memory_background(user_text, thought))
                    if broadcast_func:
                        await broadcast_func({"type": "chat_message", "role": "assistant", "content": thought})
                        await broadcast_func({"type": "status_update", "status": "idle"})
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
                asyncio.create_task(self._extract_memory_background(user_text, final_result))
                if broadcast_func:
                    await broadcast_func({"type": "chat_message", "role": "assistant", "content": final_result})
                    await broadcast_func({"type": "status_update", "status": "idle"})
                return final_result
                
            except json.JSONDecodeError as e:
                logger.exception(f"JSON Parsing Error: {e} - Response: {reply}")
                # Fallback: treat the entire reply as assistant thought/conversational response
                fallback_thought = reply.strip() if reply.strip() else "I'm sorry, I couldn't process that request."
                memory_manager.save_conversation("assistant", fallback_thought)
                asyncio.create_task(self._extract_memory_background(user_text, fallback_thought))
                if broadcast_func:
                    await broadcast_func({"type": "chat_message", "role": "assistant", "content": fallback_thought})
                    await broadcast_func({"type": "status_update", "status": "idle"})
                return fallback_thought

        except Exception as e:
            logger.exception(f"Planner Error: {e}")
            error_reply = "Sorry, I encountered an error while connecting to the AI."
            memory_manager.save_conversation("assistant", error_reply)
            if broadcast_func:
                await broadcast_func({"type": "chat_message", "role": "assistant", "content": error_reply})
                await broadcast_func({"type": "status_update", "status": "idle"})
            return error_reply

    async def _extract_memory_background(self, user_text: str, assistant_reply: str):
        try:
            prompt = f"""
            Analyze the following conversation turn between a User and Alchemist AI.
            User: "{user_text}"
            Assistant: "{assistant_reply}"
            
            Identify if the user shared any:
            - Personal facts (e.g. name, job, interests) -> Category: Personal
            - Preferences (e.g. text editors, folder names, notification settings) -> Category: Preferences
            - Projects or active tasks -> Category: Projects
            - Learned facts about their workspace or system -> Category: Learned Facts
            
            Return a JSON object containing a list of memories to save, or an empty list if none:
            {{
              "memories": [
                {{"category": "Personal | Preferences | Projects | Learned Facts", "content": "The fact/preference to remember"}}
              ]
            }}
            """
            reply = self.llm_provider.generate_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = extract_and_parse_json(reply)
            memories = data.get("memories", [])
            for m in memories:
                cat = m.get("category")
                content = m.get("content")
                if cat and content:
                    memory_manager.save_semantic_memory(cat, content)
        except Exception as e:
            logger.exception(f"Error in background memory extraction: {e}")
