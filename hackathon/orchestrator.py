import asyncio
import sqlite3
import json
from datetime import datetime
from database import DB_PATH, update_task_status, log_event

class TaskOrchestrator:
    def __init__(self, concurrency_limit=5):
        self.concurrency_limit = concurrency_limit
        self.running_tasks = {}
        self.queue = asyncio.Queue()

    async def start(self):
        print("Task Orchestrator started...")
        while True:
            # Look for pending tasks in the database
            pending_tasks = self.get_pending_tasks()
            for task in pending_tasks:
                if task['id'] not in self.running_tasks and len(self.running_tasks) < self.concurrency_limit:
                    if self.dependencies_resolved(task['id']):
                        asyncio.create_task(self.run_task(task))
            
            await asyncio.sleep(2)

    def get_pending_tasks(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority ASC, created_at ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def dependencies_resolved(self, task_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM task_dependencies td
            JOIN tasks t ON td.depends_on_task_id = t.id
            WHERE td.task_id = ? AND t.status != 'completed'
        """, (task_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0

    async def run_task(self, task):
        task_id = task['id']
        self.running_tasks[task_id] = task
        print(f"Executing task: {task_id} ({task['type']})")
        update_task_status(task_id, 'running')
        log_event(task_id, f"Task {task_id} started on orchestrator.")

        try:
            # In a real system, this would call a Browser Worker
            # For now, we simulate data extraction or navigation
            payload = json.loads(task['payload'])
            await asyncio.sleep(5)  # Simulate work
            
            result = {"status": "success", "url_processed": payload.get('url')}
            update_task_status(task_id, 'completed', result=result)
            log_event(task_id, f"Task {task_id} completed successfully.")
            
        except Exception as e:
            print(f"Task {task_id} failed: {e}")
            update_task_status(task_id, 'failed', error=str(e))
            log_event(task_id, f"Task {task_id} failed: {e}", level="error")
        
        finally:
            del self.running_tasks[task_id]

if __name__ == "__main__":
    orchestrator = TaskOrchestrator()
    asyncio.run(orchestrator.start())
