import logging
from typing import Callable, Dict, Any

logger = logging.getLogger("AlchemistTools")

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self._tools[name] = func

    def get_tool(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def get_registered_tools(self) -> list[str]:
        return list(self._tools.keys())

    def print_registry_audit(self):
        print("\nRegistered Tools:")
        for t in sorted(self.get_registered_tools()):
            print(f"* {t}")
        print("\n")

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        logger.info(f"Executing tool {tool_name} with args {args}")
        func = self.get_tool(tool_name)
        if not func:
            msg = f"Tool '{tool_name}' not found."
            logger.warning(msg)
            return msg
        
        try:
            # Special handling for argument parsing
            if tool_name in ["take_screenshot", "capture_screen", "save_screenshot", "capture_active_window", "open_youtube", "open_google", "open_github", "open_calculator", "open_notepad", "read_clipboard", "get_current_datetime", "read_notes"]:
                return func()
            elif tool_name == "write_clipboard":
                return func(args.get("text", ""))
            elif tool_name == "add_note":
                return func(args.get("note_text", ""))
            elif tool_name == "read_calendar":
                return func(args.get("date_str", ""))
            elif tool_name == "add_calendar_event":
                return func(args.get("date_str", ""), args.get("event_desc", ""))
            elif tool_name == "search_google":
                return func(args.get("query", ""))
            elif tool_name in ["open_website", "navigate_page", "open_url"]:
                return func(args.get("url", ""))
            elif tool_name in ["create_file", "read_file", "delete_file"]:
                return func(args.get("filename", ""))
            elif tool_name in ["list_directory", "read_metadata"]:
                return func(args.get("path", "."))
            elif tool_name == "search_files":
                return func(args.get("query", ""), args.get("path", "."))
            elif tool_name == "move_file":
                return func(args.get("src", ""), args.get("dest", ""))
            elif tool_name == "launch_application":
                return func(args.get("app_name_or_path", ""))
            elif tool_name == "browser_start":
                return func(args.get("url", ""))
            elif tool_name == "browser_click":
                return func(args.get("selector", ""))
            elif tool_name == "browser_type":
                return func(args.get("selector", ""), args.get("text", ""))
            elif tool_name in ["move_mouse", "click_mouse", "double_click"]:
                return func(int(args.get("x", 0)), int(args.get("y", 0)))
            elif tool_name == "type_text":
                return func(args.get("text", ""))
            elif tool_name == "press_key":
                return func(args.get("key", ""))
            elif tool_name in ["browser_get_html", "browser_close", "read_page_title", "extract_page_text", "open_linkedin", "open_github", "open_chatgpt", "analyze_screen", "read_screen_text", "identify_active_window"]:
                return func()
            
            return func(**args)
        except Exception as e:
            msg = f"Error executing tool '{tool_name}': {e}"
            logger.error(msg)
            return msg

registry = ToolRegistry()
