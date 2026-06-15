import sqlite3
import shutil
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "memory.db")

def restore(backup_file):
    if not os.path.exists(backup_file):
        print(f"Error: Backup file {backup_file} not found.")
        sys.exit(1)
        
    print(f"Restoring database from {backup_file}...")
    
    # Safe restore via sqlite3 backup API
    try:
        source = sqlite3.connect(backup_file)
        dest = sqlite3.connect(DB_PATH)
        with source:
            source.backup(dest)
        dest.close()
        source.close()
        print("Restore successful.")
    except Exception as e:
        print(f"Restore failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore.py <path_to_backup_file>")
        sys.exit(1)
    
    restore(sys.argv[1])
