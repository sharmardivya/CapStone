"""
In-memory audit log of completed travel-planning tasks.

The synthesize_plan node records one entry per finished plan; the reporting
module reads it to print the audit table and draw the timing chart.
The log lives only as long as the Python process.
"""

import threading
from typing import Any, Dict, List

_task_log: List[Dict[str, Any]] = []
_lock = threading.Lock()  # the chatbot may finish several requests at once


def record_task(entry: Dict[str, Any]) -> None:
    """Add one completed task to the log."""
    with _lock:
        _task_log.append(entry)


def get_task_log() -> List[Dict[str, Any]]:
    """Return a copy of all recorded tasks, oldest first."""
    with _lock:
        return list(_task_log)
