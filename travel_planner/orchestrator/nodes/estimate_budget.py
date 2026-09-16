"""
Node 5 — estimate_budget.

Asks the Budget Estimator Agent (A2A, port 8003) for an itemized budget for
the whole trip. The agent uses LangChain + the offline cost table internally.
"""

from travel_planner import config
from travel_planner.orchestrator.nodes.a2a_call import call_agent
from travel_planner.orchestrator.state import TravelState


async def estimate_budget_node(state: TravelState) -> dict:
    """Store the agent's budget in `budget_info`."""
    reply, seconds = await call_agent(
        "budget", f"Budget for {state['duration']} in {state['destination']}", state
    )
    return {
        "budget_info": reply,
        "node_log": [f"[{state['task_id']}] estimate_budget → A2A :{config.BUDGET_AGENT_PORT} ({seconds}s)"],
    }
