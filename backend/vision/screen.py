import pyautogui
import pygetwindow as gw
from datetime import datetime
import os
import logging
from core.config import settings
from tools.registry import registry

logger = logging.getLogger("AlchemistVision")

def _ensure_screenshot_dir():
    os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)

def take_screenshot() -> str:
    """Captures the full screen, saves it, and returns the path."""
    logger.info("Taking full screen screenshot...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            _ensure_screenshot_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_full_{timestamp}.png"
            filepath = os.path.join(settings.SCREENSHOTS_DIR, filename)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            logger.info(f"Full screen screenshot saved to: {filepath}")
            return f"Screenshot successfully saved to {filepath}"
        except OSError as e:
            logger.error(f"Error taking full screenshot (attempt {attempt+1}/{max_retries}): {e}")
            import time
            time.sleep(0.5 * (2 ** attempt))
        except Exception as e:
            logger.error(f"Fatal error taking full screenshot: {e}")
            return f"Failed to take full screenshot: {e}"
            
    return "Failed to take full screenshot after 3 attempts."

def capture_active_window() -> str:
    """Captures only the currently active window."""
    logger.info("Taking active window screenshot...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            _ensure_screenshot_dir()
            window = gw.getActiveWindow()
            if not window:
                return "Failed to take active window screenshot: No active window detected."
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_window_{timestamp}.png"
            filepath = os.path.join(settings.SCREENSHOTS_DIR, filename)
            
            # region parameter takes (left, top, width, height)
            region = (window.left, window.top, window.width, window.height)
            screenshot = pyautogui.screenshot(region=region)
            screenshot.save(filepath)
            
            logger.info(f"Active window screenshot saved to: {filepath}")
            return f"Active window screenshot successfully saved to {filepath}"
        except OSError as e:
            logger.error(f"Error taking active window screenshot (attempt {attempt+1}/{max_retries}): {e}")
            import time
            time.sleep(0.5 * (2 ** attempt))
        except Exception as e:
            logger.error(f"Fatal error taking active window screenshot: {e}")
            return f"Failed to take active window screenshot: {e}"
            
    return "Failed to take active window screenshot after 3 attempts."

# Aliases for different commands
def capture_screen() -> str:
    return take_screenshot()

def save_screenshot() -> str:
    return take_screenshot()

# Register Tools
registry.register("take_screenshot", take_screenshot)
registry.register("capture_screen", capture_screen)
registry.register("save_screenshot", save_screenshot)
registry.register("capture_active_window", capture_active_window)
