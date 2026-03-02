from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from database import DB_PATH, add_task, get_task

app = FastAPI(title="Browser Tasking API")

class TaskCreate(BaseModel):
    task_type: str
    payload: dict
    priority: Optional[int] = 5
    depends_on: Optional[List[str]] = None

@app.get("/")
async def root():
    return {"message": "Browser Tasking API Operational"}

@app.post("/api/tasks", status_code=201)
async def create_new_task(task: TaskCreate):
    try:
        task_id = add_task(task.task_type, task.payload, task.priority, task.depends_on)
        return {"task_id": task_id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/api/metrics")
async def get_metrics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get counts by status
    cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
    counts = dict(cursor.fetchall())
    
    # Get recent logs
    cursor.execute("SELECT * FROM execution_logs ORDER BY created_at DESC LIMIT 10")
    logs = [dict(sqlite3.Row(cursor, row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "tasks": counts,
        "recent_logs": logs
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
