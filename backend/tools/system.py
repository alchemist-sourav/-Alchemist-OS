import os
import logging
import subprocess
from tools.registry import registry

logger = logging.getLogger("AlchemistSystem")

def launch_application(app_name_or_path: str) -> str:
    """
    Dynamically launches an application by its name or path.
    """
    logger.info(f"Attempting to launch application: {app_name_or_path}")
    try:
        # For Windows, os.startfile is best for opening apps, files, or URIs using default associated programs
        if os.name == 'nt':
            try:
                os.startfile(app_name_or_path)
                return f"Successfully launched {app_name_or_path}"
            except FileNotFoundError:
                # Fallback to subprocess if startfile fails (e.g., app is in PATH but startfile doesn't find it)
                pass
                
        # Fallback to subprocess.Popen for both Windows (if startfile failed) and other OS
        # We use shell=True to allow searching in the system PATH.
        # We use creationflags to run it detached on Windows if possible, but Popen without wait is usually enough.
        subprocess.Popen(app_name_or_path, shell=True)
        return f"Successfully launched {app_name_or_path} via subprocess."
    except Exception as e:
        logger.error(f"Error launching application '{app_name_or_path}': {e}")
        return f"Failed to launch application '{app_name_or_path}': {e}"

# Register Tools
registry.register("launch_application", launch_application)
