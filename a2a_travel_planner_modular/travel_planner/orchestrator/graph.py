"""
Build the LangGraph StateGraph and run it.

    START → parse_query → check_leave_balance → research_destination → check_weather
          → estimate_budget → synthesize_plan → END

A node that needs something from the user (missing details, unknown employee
ID) writes its question into `final_plan`; the graph then stops at END so the
chatbot can show the question and wait for the answer.
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from travel_planner.orchestrator.nodes import (check_leave_balance_node, check_weather_node,
                                               estimate_budget_node, parse_query_node,
                                               research_destination_node, synthesize_plan_node)
from travel_planner.orchestrator.state import TravelState, make_initial_state


def route_after_parse(state: TravelState) -> str:
    """Stop if parse_query asked the user for missing details."""
    return END if state["final_plan"] else "check_leave_balance"


def route_after_leave_check(state: TravelState) -> str:
    """Stop if the employee ID was not found in the HR database."""
    return END if state["final_plan"] else "research_destination"


def build_travel_graph():
    """Register the six nodes, connect them, and compile a runnable graph."""
    workflow = StateGraph(TravelState)

    workflow.add_node("parse_query", parse_query_node)
    workflow.add_node("check_leave_balance", check_leave_balance_node)
    workflow.add_node("research_destination", research_destination_node)
    workflow.add_node("check_weather", check_weather_node)
    workflow.add_node("estimate_budget", estimate_budget_node)
    workflow.add_node("synthesize_plan", synthesize_plan_node)

    workflow.add_edge(START, "parse_query")
    workflow.add_conditional_edges("parse_query", route_after_parse, ["check_leave_balance", END])
    workflow.add_conditional_edges("check_leave_balance", route_after_leave_check, ["research_destination", END])
    workflow.add_edge("research_destination", "check_weather")
    workflow.add_edge("check_weather", "estimate_budget")
    workflow.add_edge("estimate_budget", "synthesize_plan")
    workflow.add_edge("synthesize_plan", END)

    return workflow.compile()


@lru_cache(maxsize=1)
def get_travel_graph():
    """The compiled graph, built once and reused."""
    return build_travel_graph()


async def plan_trip(query: str, employee_id: str = "") -> TravelState:
    """Run the whole pipeline for one request and return the final state."""
    return await get_travel_graph().ainvoke(make_initial_state(query, employee_id))
