import logging
import os
from logging.handlers import RotatingFileHandler
from core.config import settings

def setup_logging():
    log_dir = os.path.join(settings.BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Error Log
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "errors.log"), maxBytes=5*1024*1024, backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Action Log (for Tools)
    action_handler = RotatingFileHandler(
        os.path.join(log_dir, "actions.log"), maxBytes=5*1024*1024, backupCount=3
    )
    action_handler.setLevel(logging.INFO)
    action_handler.setFormatter(formatter)

    # System Log
    system_handler = RotatingFileHandler(
        os.path.join(log_dir, "system.log"), maxBytes=5*1024*1024, backupCount=3
    )
    system_handler.setLevel(logging.INFO)
    system_handler.setFormatter(formatter)

    # Console Log
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Root Logger Configuration
    root_logger = logging.getLogger()
    root_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(root_level)
    
    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # DB Error Logger
    class DatabaseErrorHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                try:
                    from database.database import memory_manager
                    import traceback
                    
                    exc_type = ""
                    stack_trace = ""
                    if record.exc_info:
                        exc_type = record.exc_info[0].__name__ if record.exc_info[0] else ""
                        stack_trace = "".join(traceback.format_exception(*record.exc_info))
                    
                    component = record.name
                    request_context = record.getMessage()
                    
                    # Avoid recursive logging by checking if we're already in a DB logger call
                    if component != "AlchemistMemory":
                        memory_manager.save_error_log(exc_type, stack_trace, component, request_context)
                except Exception:
                    pass

    db_handler = DatabaseErrorHandler()
    db_handler.setLevel(logging.ERROR)

    # We add common handlers (System + Console)
    root_logger.addHandler(system_handler)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(db_handler)

    # Create specialized Action logger
    action_logger = logging.getLogger("AlchemistAction")
    action_logger.addHandler(action_handler)
    # Prevent duplicate logging to root
    action_logger.propagate = False 

    # We also add the error and console handlers to the action logger so they still show up globally
    action_logger.addHandler(error_handler)
    action_logger.addHandler(console_handler)
    action_logger.addHandler(db_handler)
