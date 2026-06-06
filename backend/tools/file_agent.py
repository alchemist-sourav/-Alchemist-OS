import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from tools.registry import registry

logger = logging.getLogger("AlchemistFileAgent")

def list_directory(path: str) -> str:
    logger.info(f"Listing directory: {path}")
    try:
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a valid directory."
        items = os.listdir(path)
        return f"Contents of {path}:\n" + "\n".join(items) if items else f"{path} is empty."
    except Exception as e:
        logger.error(f"Error listing directory: {e}")
        return f"Failed to list directory: {e}"

def search_files(query: str, path: str = ".") -> str:
    logger.info(f"Searching for '{query}' in {path}")
    try:
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a valid directory."
        
        matches = []
        for root, _, files in os.walk(path):
            for file in files:
                if query.lower() in file.lower():
                    matches.append(os.path.join(root, file))
        
        return f"Found {len(matches)} files matching '{query}':\n" + "\n".join(matches) if matches else f"No files matching '{query}' found."
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return f"Failed to search files: {e}"

def move_file(src: str, dest: str) -> str:
    logger.info(f"Moving file from {src} to {dest}")
    try:
        if not os.path.exists(src):
            return f"Error: Source file '{src}' does not exist."
        shutil.move(src, dest)
        return f"Successfully moved {src} to {dest}."
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        return f"Failed to move file: {e}"

def delete_file(path: str) -> str:
    logger.info(f"Deleting file: {path}")
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Successfully deleted directory {path}."
        else:
            os.remove(path)
            return f"Successfully deleted file {path}."
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return f"Failed to delete file: {e}"

def read_metadata(path: str) -> str:
    logger.info(f"Reading metadata for: {path}")
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        
        stat_info = os.stat(path)
        is_dir = os.path.isdir(path)
        size = stat_info.st_size
        created = datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        
        return (f"Metadata for {path}:\n"
                f"Type: {'Directory' if is_dir else 'File'}\n"
                f"Size: {size} bytes\n"
                f"Created: {created}\n"
                f"Modified: {modified}")
    except Exception as e:
        logger.error(f"Error reading metadata: {e}")
        return f"Failed to read metadata: {e}"

# Register Tools
registry.register("list_directory", list_directory)
registry.register("search_files", search_files)
registry.register("move_file", move_file)
registry.register("delete_file", delete_file)
registry.register("read_metadata", read_metadata)
