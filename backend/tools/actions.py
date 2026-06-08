import webbrowser
import os
import logging
import pyperclip
import json
from datetime import datetime
from tools.registry import registry
from core.config import settings

logger = logging.getLogger("AlchemistActions")

# App Launching
def open_youtube():
    logger.info("Opening YouTube")
    webbrowser.open("https://youtube.com")
    return "Opened YouTube"

def open_google():
    logger.info("Opening Google")
    webbrowser.open("https://google.com")
    return "Opened Google"

def open_github():
    logger.info("Opening GitHub")
    webbrowser.open("https://github.com")
    return "Opened GitHub"

def open_calculator():
    logger.info("Opening Calculator")
    os.system("calc")
    return "Opened Calculator"

def open_notepad():
    logger.info("Opening Notepad")
    os.system("notepad")
    return "Opened Notepad"

def create_file(filename=None, folder_path=None, file_name=None, content=""):
    if not filename:
        if folder_path and file_name:
            filename = os.path.join(folder_path, file_name)
        elif file_name:
            filename = file_name
        else:
            filename = "new_file.txt"
            
    logger.info(f"Creating file: {filename}")
    try:
        dir_name = os.path.dirname(filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Created file: {filename}"
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        return f"Failed to create file: {e}"

def read_file(filename):
    logger.info(f"Reading file: {filename}")
    if not os.path.exists(filename):
        return f"File not found: {filename}"
    try:
        with open(filename, "r") as f:
            content = f.read()
        return f"File content of {filename}:\n{content}"
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return f"Failed to read file: {e}"

# Clipboard Management
def read_clipboard():
    logger.info("Reading clipboard")
    try:
        return pyperclip.paste()
    except Exception as e:
        logger.error(f"Error reading clipboard: {e}")
        return f"Failed to read clipboard: {e}"

def write_clipboard(text):
    logger.info("Writing to clipboard")
    try:
        pyperclip.copy(text)
        return "Successfully copied to clipboard."
    except Exception as e:
        logger.error(f"Error writing to clipboard: {e}")
        return f"Failed to write to clipboard: {e}"

# Calendar Management
CALENDAR_FILE = os.path.join(settings.DATA_DIR, "calendar.json")

def get_current_datetime():
    logger.info("Getting current date and time")
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

def add_calendar_event(date_str, event_desc):
    logger.info(f"Adding calendar event: {date_str} - {event_desc}")
    events = {}
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r") as f:
            events = json.load(f)
    if date_str not in events:
        events[date_str] = []
    events[date_str].append(event_desc)
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f)
    return f"Event added for {date_str}."

def read_calendar(date_str):
    logger.info(f"Reading calendar for {date_str}")
    if not os.path.exists(CALENDAR_FILE):
        return "No events found."
    with open(CALENDAR_FILE, "r") as f:
        events = json.load(f)
    return events.get(date_str, "No events found for this date.")

# Notes Management
NOTES_FILE = os.path.join(settings.DATA_DIR, "notes.txt")

def add_note(note_text):
    logger.info("Adding note")
    try:
        with open(NOTES_FILE, "a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note_text}\n")
        return "Note added successfully."
    except Exception as e:
        logger.error(f"Error adding note: {e}")
        return f"Failed to add note: {e}"

def read_notes():
    logger.info("Reading notes")
    if not os.path.exists(NOTES_FILE):
        return "No notes found."
    try:
        with open(NOTES_FILE, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading notes: {e}")
        return f"Failed to read notes: {e}"

# Register Tools
registry.register("open_youtube", open_youtube)
registry.register("open_google", open_google)
registry.register("open_github", open_github)
registry.register("open_calculator", open_calculator)
registry.register("open_notepad", open_notepad)
registry.register("create_file", create_file)
registry.register("read_file", read_file)
registry.register("read_clipboard", read_clipboard)
registry.register("write_clipboard", write_clipboard)
registry.register("get_current_datetime", get_current_datetime)
registry.register("add_calendar_event", add_calendar_event)
registry.register("read_calendar", read_calendar)
registry.register("add_note", add_note)
registry.register("read_notes", read_notes)
