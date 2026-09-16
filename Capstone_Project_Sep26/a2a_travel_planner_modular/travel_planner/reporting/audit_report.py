"""
Text audit report of completed tasks (notebook Section 10, table part).
"""

import pandas as pd

from travel_planner.orchestrator.audit_log import get_task_log

_QUERY_PREVIEW_CHARS = 45


def format_audit_report() -> str:
    """Return a table of every recorded task and the node log of the latest one."""
    tasks = get_task_log()
    if not tasks:
        return "No tasks recorded yet — plan a trip first."

    rows = [{
        "Task ID": task["task_id"],
        "Query": task["query"][:_QUERY_PREVIEW_CHARS] + ("…" if len(task["query"]) > _QUERY_PREVIEW_CHARS else ""),
        "Employee": task["employee_id"],
        "Destination": task["destination"],
        "Duration": task["duration"],
        "Synth. (s)": task["elapsed_s"],
        "Status": task["status"],
    } for task in tasks]

    lines = ["Task audit log", pd.DataFrame(rows).to_string(index=False), "",
             "Node execution log (most recent task):"]
    lines += [f"  {entry}" for entry in tasks[-1]["node_log"]]
    return "\n".join(lines)
