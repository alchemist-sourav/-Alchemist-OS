import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DB_PATH = os.path.join(DATA_DIR, "memory.db")
os.makedirs(DATA_DIR, exist_ok=True)

def init_migrations(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

def get_current_version(cursor):
    init_migrations(cursor)
    cursor.execute("SELECT MAX(version) FROM schema_migrations")
    row = cursor.fetchone()
    return row[0] if row[0] is not None else 0

MIGRATIONS = [
    # version 1: Initial schema is created by database.py implicitly
    "SELECT 1",
    # version 2: Example migration
    "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)",
    # version 3: Ensure agent_tasks.id is TEXT (UUID) - recreate table if needed
    """CREATE TABLE IF NOT EXISTS agent_tasks_new (
        id TEXT PRIMARY KEY,
        goal TEXT,
        status TEXT,
        current_step INTEGER DEFAULT 0,
        steps_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
    )""",
    "INSERT OR IGNORE INTO agent_tasks_new SELECT CAST(id AS TEXT), goal, status, current_step, steps_json, created_at, completed_at FROM agent_tasks",
    "DROP TABLE IF EXISTS agent_tasks",
    "ALTER TABLE agent_tasks_new RENAME TO agent_tasks",
]

def upgrade():
    print(f"Connecting to {DB_PATH} for upgrade")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    current_version = get_current_version(cursor)
    print(f"Current version: {current_version}")
    
    for idx, sql in enumerate(MIGRATIONS):
        version = idx + 1
        if version > current_version:
            print(f"Applying migration version {version}")
            try:
                cursor.execute(sql)
                cursor.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                conn.commit()
                print(f"Migration {version} applied successfully.")
            except Exception as e:
                print(f"Failed to apply migration {version}: {e}")
                conn.rollback()
                sys.exit(1)
                
    print("Database is up to date.")
    conn.close()

def rollback():
    print("Rollback is not fully implemented in this lightweight framework.")
    print("Restore from backup to rollback.")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    if action == "upgrade":
        upgrade()
    elif action == "rollback":
        rollback()
    else:
        print("Usage: python migrate.py [upgrade|rollback]")
