"""
Node 3 — research_destination.

Asks the Destination Research Agent (A2A, port 8001) for an overview of the
destination. The agent uses LangChain + Wikipedia internally; this node only
sees the A2A reply.
"""

from travel_planner import config
from travel_planner.orchestrator.nodes.a2a_call import call_agent
from travel_planner.orchestrator.state import TravelState


async def research_destination_node(state: TravelState) -> dict:
    """Store the agent's destination overview in `destination_info`."""
    reply, seconds = await call_agent(
        "destination", f"Research destination: {state['destination']}", state
    )
    return {
        "destination_info": reply,
        "node_log": [f"[{state['task_id']}] research_destination → A2A :{config.DESTINATION_AGENT_PORT} ({seconds}s)"],
    }
