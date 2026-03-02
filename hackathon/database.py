import sqlite3
import json
from datetime import datetime
import uuid

DB_PATH = "browser_tasking.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        priority INTEGER DEFAULT 5,
        payload TEXT NOT NULL,
        result TEXT,
        error_message TEXT,
        retry_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        completed_at TIMESTAMP
    )
    """)

    # Task dependencies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_dependencies (
        task_id TEXT,
        depends_on_task_id TEXT,
        PRIMARY KEY (task_id, depends_on_task_id),
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )
    """)

    # Tabs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tabs (
        id TEXT PRIMARY KEY,
        browser_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'idle',
        current_task_id TEXT,
        task_count INTEGER DEFAULT 0,
        error_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_task_id) REFERENCES tasks(id)
    )
    """)

    # Execution logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS execution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        tab_id TEXT,
        log_level TEXT,
        message TEXT,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (tab_id) REFERENCES tabs(id) ON DELETE SET NULL
    )
    """)

    conn.commit()
    conn.close()

def add_task(task_type, payload, priority=5, depends_on=None):
    task_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO tasks (id, type, payload, priority) VALUES (?, ?, ?, ?)",
        (task_id, task_type, json.dumps(payload), priority)
    )
    
    if depends_on:
        for dep_id in depends_on:
            cursor.execute(
                "INSERT INTO task_dependencies (task_id, depends_on_task_id) VALUES (?, ?)",
                (task_id, dep_id)
            )
            
    conn.commit()
    conn.close()
    return task_id

def get_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_task_status(task_id, status, result=None, error=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    if status == 'running':
        cursor.execute("UPDATE tasks SET status = ?, started_at = ? WHERE id = ?", (status, now, task_id))
    elif status in ['completed', 'failed']:
        cursor.execute(
            "UPDATE tasks SET status = ?, completed_at = ?, result = ?, error_message = ? WHERE id = ?",
            (status, now, json.dumps(result) if result else None, error, task_id)
        )
    else:
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        
    conn.commit()
    conn.close()

def log_event(task_id, message, level="info", tab_id=None, metadata=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO execution_logs (task_id, tab_id, log_level, message, metadata) VALUES (?, ?, ?, ?, ?)",
        (task_id, tab_id, level, message, json.dumps(metadata) if metadata else None)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")