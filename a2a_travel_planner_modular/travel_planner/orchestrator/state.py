"""
TravelState — the shared state that flows through the LangGraph pipeline.

Each node reads what it needs from the state and returns a dict of updates.
By default an update REPLACES the old value. `node_log` is annotated with
`operator.add`, so updates to it are APPENDED instead — every node's log
line is kept.
"""

import operator
from typing import Annotated, List, TypedDict


class TravelState(TypedDict):
    query: str             # the user's original request
    employee_id: str       # given by the caller, or found in the query (e.g. "E1001")
    destination: str       # set by parse_query ("" when no destination was found)
    duration: str          # e.g. "5 days"; parse_query defaults to "3 days"
    destination_info: str  # reply from the Destination Research Agent
    weather_info: str      # reply from the Weather Intelligence Agent
    budget_info: str       # reply from the Budget Estimator Agent
    leave_info: str        # reply from the HR Leave Agent
    final_plan: str        # the finished plan (or a question asking for missing details)
    task_id: str           # short id that ties log lines to one request
    node_log: Annotated[List[str], operator.add]  # accumulates across nodes


def make_initial_state(query: str, employee_id: str = "") -> TravelState:
    """Create a fresh, empty state for a new request."""
    return TravelState(
        query=query, employee_id=employee_id.strip().upper(), destination="", duration="",
        destination_info="", weather_info="", budget_info="", leave_info="",
        final_plan="", task_id="", node_log=[],
    )
