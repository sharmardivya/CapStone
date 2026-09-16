"""
Node 2 — check_leave_balance.

Asks the HR Leave Agent (A2A, port 8004) for the employee's leave balance and
whether it covers the trip. Runs before the other agents: if the employee ID
is not in the HR database, the node asks the user for a valid ID and the graph
stops, instead of planning a whole trip first.
"""

from travel_planner import config
from travel_planner.orchestrator.nodes.a2a_call import call_agent
from travel_planner.orchestrator.state import TravelState


async def check_leave_balance_node(state: TravelState) -> dict:
    """Store the agent's leave summary in `leave_info`; ask again if the ID is unknown."""
    request = (
        f"Leave balance for employee {state['employee_id']}. "
        f"Planned trip: {state['duration']} in {state['destination']}."
    )
    reply, seconds = await call_agent("hr", request, state)

    update = {
        "leave_info": reply,
        "node_log": [f"[{state['task_id']}] check_leave_balance → A2A :{config.HR_AGENT_PORT} ({seconds}s)"],
    }
    if reply.startswith(config.EMPLOYEE_NOT_FOUND):
        update["final_plan"] = f"⚠️ {reply}\n\nPlease send a valid **employee ID**."
    return update
