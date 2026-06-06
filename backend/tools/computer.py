import pyautogui
import logging
from tools.registry import registry

logger = logging.getLogger("AlchemistComputerControl")

# Ensure PyAutoGUI fail-safe is enabled. This allows the user to stop
# execution by moving the mouse to any of the 4 corners of the screen.
pyautogui.FAILSAFE = True

def move_mouse(x: int, y: int) -> str:
    logger.info(f"Moving mouse to ({x}, {y})")
    try:
        pyautogui.moveTo(x, y)
        return f"Successfully moved mouse to ({x}, {y})."
    except Exception as e:
        logger.error(f"Error moving mouse to ({x}, {y}): {e}")
        return f"Failed to move mouse: {e}"

def click_mouse(x: int, y: int) -> str:
    logger.info(f"Clicking mouse at ({x}, {y})")
    try:
        pyautogui.click(x, y)
        return f"Successfully clicked at ({x}, {y})."
    except Exception as e:
        logger.error(f"Error clicking at ({x}, {y}): {e}")
        return f"Failed to click mouse: {e}"

def double_click(x: int, y: int) -> str:
    logger.info(f"Double clicking mouse at ({x}, {y})")
    try:
        pyautogui.doubleClick(x, y)
        return f"Successfully double-clicked at ({x}, {y})."
    except Exception as e:
        logger.error(f"Error double-clicking at ({x}, {y}): {e}")
        return f"Failed to double-click: {e}"

def type_text(text: str) -> str:
    logger.info(f"Typing text: {text}")
    try:
        pyautogui.write(text, interval=0.01) # Small interval for safety/stability
        return f"Successfully typed text."
    except Exception as e:
        logger.error(f"Error typing text: {e}")
        return f"Failed to type text: {e}"

def press_key(key: str) -> str:
    logger.info(f"Pressing key: {key}")
    try:
        pyautogui.press(key)
        return f"Successfully pressed key: {key}."
    except Exception as e:
        logger.error(f"Error pressing key {key}: {e}")
        return f"Failed to press key: {e}"

# Register Tools
registry.register("move_mouse", move_mouse)
registry.register("click_mouse", click_mouse)
registry.register("double_click", double_click)
registry.register("type_text", type_text)
registry.register("press_key", press_key)
