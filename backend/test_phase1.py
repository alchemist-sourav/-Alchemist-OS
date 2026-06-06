import sys
import os

# Set up path to import backend modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from memory.database import memory_manager
from tools.actions import (
    add_note, read_notes, add_calendar_event, read_calendar,
    write_clipboard, read_clipboard
)
from tools.registry import registry

print("--- MEMORY TESTS ---")
print("1. Remember name:", memory_manager.save_profile("name", "Sourav"))
print("2. Retrieve name:", memory_manager.get_profile("name"))
print("3. Create project:", memory_manager.create_project("Alchemist AI", "Test Project"))
print("4. List projects:", memory_manager.get_active_projects())

print("5. Add task (Missing method):", memory_manager.add_task("Alchemist AI", "Build Voice System"))
print("6. List tasks (Missing method):", memory_manager.get_tasks("Alchemist AI"))

print("7. Store long term memory:", memory_manager.save_memory("color", "blue"))
print("8. Retrieve long term memory:", memory_manager.get_memory("color"))

print("\n--- NOTES TESTS ---")
print("1. Add note:", add_note("Test Note 123"))
print("2. Read notes:", read_notes())

print("\n--- CALENDAR TESTS ---")
print("1. Add calendar event:", add_calendar_event("2026-06-06", "Test Event 123"))
print("2. Read calendar events:", read_calendar("2026-06-06"))

print("\n--- CLIPBOARD TESTS ---")
print("1. Write clipboard:", write_clipboard("Test Clipboard 123"))
print("2. Read clipboard:", read_clipboard())

print("\n--- CONVERSATION TESTS ---")
memory_manager.save_conversation("user", "Hello")
memory_manager.save_conversation("assistant", "Hello there!")
print("1. Store conversation (Missing method): Done")
print("2. Retrieve conversation (Missing method):", memory_manager.get_recent_conversations(2))

print("\n--- DATABASE TESTS ---")
memory_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in memory_manager.cursor.fetchall()]
print("Tables:", tables)
for table in tables:
    try:
        memory_manager.cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = memory_manager.cursor.fetchone()[0]
        print(f"Table '{table}' record count: {count}")
    except Exception as e:
        print(f"Error counting {table}: {e}")

print("\n--- TOOL REGISTRY TESTS ---")
tools = list(registry._tools.keys())
print("Registered tools:", tools)
for t in tools:
    func = registry.get_tool(t)
    print(f"Tool '{t}' callable:", callable(func))
