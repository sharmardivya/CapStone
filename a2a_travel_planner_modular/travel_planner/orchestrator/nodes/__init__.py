"""
LangGraph nodes — one file per node, in the order they run.

    parse_query.py           Node 1  find destination, duration and employee ID
    check_leave_balance.py   Node 2  A2A call → HR Leave Agent (:8004)
    research_destination.py  Node 3  A2A call → Destination Research Agent (:8001)
    check_weather.py         Node 4  A2A call → Weather Intelligence Agent (:8002)
    estimate_budget.py       Node 5  A2A call → Budget Estimator Agent (:8003)
    synthesize_plan.py       Node 6  LLM combines everything into the final plan
    a2a_call.py              helper used by nodes 2–5
"""

from travel_planner.orchestrator.nodes.check_leave_balance import check_leave_balance_node
from travel_planner.orchestrator.nodes.check_weather import check_weather_node
from travel_planner.orchestrator.nodes.estimate_budget import estimate_budget_node
from travel_planner.orchestrator.nodes.parse_query import parse_query_node
from travel_planner.orchestrator.nodes.research_destination import research_destination_node
from travel_planner.orchestrator.nodes.synthesize_plan import synthesize_plan_node

__all__ = [
    "parse_query_node",
    "check_leave_balance_node",
    "research_destination_node",
    "check_weather_node",
    "estimate_budget_node",
    "synthesize_plan_node",
]
