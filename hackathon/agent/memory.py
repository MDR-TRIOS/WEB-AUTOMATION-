"""
memory.py — In-memory session storage for the AI browser agent.
Tracks task plan, tab states, extracted results, retries and errors.
"""

import threading
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime


class SessionMemory:
    """
    Thread-safe in-memory store for a single agent session.

    Structure:
    {
        "task_id": str,
        "created_at": str,
        "task_plan": dict,
        "tabs": {
            "<tab_name>": {
                "status": "pending|running|completed|error",
                "url": str,
                "last_action": str,
                "retries": int
            }
        },
        "results": {
            "<tab_name>": { ...extracted data... }
        },
        "comparison": { ...comparison result... },
        "errors": [ {tab, action, error, timestamp}, ... ],
        "action_history": [ {tab, action, timestamp}, ... ]
    }
    """

    def __init__(self, task_id: Optional[str] = None):
        self._lock = threading.Lock()
        self.store: Dict[str, Any] = {
            "task_id": task_id or str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "task_plan": {},
            "tabs": {},
            "results": {},
            "comparison": {},
            "errors": [],
            "action_history": [],
        }

    # ── Task Plan ────────────────────────────────────────────────────────────

    def set_task_plan(self, plan: dict) -> None:
        with self._lock:
            self.store["task_plan"] = plan

    def get_task_plan(self) -> dict:
        with self._lock:
            return self.store["task_plan"]

    # ── Tab State ─────────────────────────────────────────────────────────────

    def init_tab(self, tab_name: str) -> None:
        with self._lock:
            self.store["tabs"][tab_name] = {
                "status": "pending",
                "url": "",
                "last_action": "",
                "retries": 0,
            }

    def update_tab(self, tab_name: str, **kwargs) -> None:
        with self._lock:
            tab = self.store["tabs"].setdefault(tab_name, {})
            tab.update(kwargs)

    def get_tab(self, tab_name: str) -> Optional[dict]:
        with self._lock:
            return self.store["tabs"].get(tab_name)

    def get_all_tabs(self) -> dict:
        with self._lock:
            return dict(self.store["tabs"])

    # ── Results ───────────────────────────────────────────────────────────────

    def set_result(self, tab_name: str, data: dict) -> None:
        with self._lock:
            self.store["results"][tab_name] = data

    def get_result(self, tab_name: str) -> Optional[dict]:
        with self._lock:
            return self.store["results"].get(tab_name)

    def get_all_results(self) -> dict:
        with self._lock:
            return dict(self.store["results"])

    def set_comparison(self, comparison: dict) -> None:
        with self._lock:
            self.store["comparison"] = comparison

    def get_comparison(self) -> dict:
        with self._lock:
            return self.store["comparison"]

    # ── Errors ────────────────────────────────────────────────────────────────

    def log_error(self, tab_name: str, action: str, error: str) -> None:
        with self._lock:
            self.store["errors"].append({
                "tab": tab_name,
                "action": action,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            })

    def get_errors(self) -> List[dict]:
        with self._lock:
            return list(self.store["errors"])

    # ── Action History ────────────────────────────────────────────────────────

    def record_action(self, tab_name: str, action: str) -> None:
        with self._lock:
            self.store["action_history"].append({
                "tab": tab_name,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
            })

    def get_action_history(self) -> List[dict]:
        with self._lock:
            return list(self.store["action_history"])

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Return a full copy of the current memory state."""
        with self._lock:
            import copy
            return copy.deepcopy(self.store)

    def __repr__(self) -> str:
        return f"<SessionMemory task_id={self.store['task_id']}>"
