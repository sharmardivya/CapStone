"""
LangGraph orchestrator: turns a user request into a full travel plan.

    state.py       TravelState — the data passed from node to node
    audit_log.py   in-memory record of every completed task
    nodes/         one file per graph node
    graph.py       wires the nodes together and exposes plan_trip()

Flow:
    START → parse_query ─(details missing → ask user)
          → check_leave_balance ─(unknown employee ID → ask user)
          → research_destination → check_weather → estimate_budget
          → synthesize_plan → END
"""
