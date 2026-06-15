import sqlite3
import shutil
import os
import time
from datetime import datetime
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
DB_PATH = os.path.join(DATA_DIR, "memory.db")
MAX_BACKUPS = 7

def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    if not os.path.exists(DB_PATH):
        print(f"No database found at {DB_PATH}")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"memory_backup_{timestamp}.db")
    
    # Safe backup via sqlite3 backup API
    print(f"Starting backup of {DB_PATH} to {backup_file}")
    
    try:
        source = sqlite3.connect(DB_PATH)
        dest = sqlite3.connect(backup_file)
        with source:
            source.backup(dest)
        dest.close()
        source.close()
        print(f"Backup successful: {backup_file}")
    except Exception as e:
        print(f"Backup failed: {e}")
        return

    # Rotation
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "memory_backup_*.db")))
    if len(backups) > MAX_BACKUPS:
        for old_backup in backups[:-MAX_BACKUPS]:
            print(f"Removing old backup: {old_backup}")
            os.remove(old_backup)

if __name__ == "__main__":
    create_backup()
