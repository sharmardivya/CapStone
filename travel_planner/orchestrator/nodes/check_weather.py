"""
Node 4 — check_weather.

Asks the Weather Intelligence Agent (A2A, port 8002) for current weather and
packing advice. The agent uses LangChain + wttr.in internally.
"""

from travel_planner import config
from travel_planner.orchestrator.nodes.a2a_call import call_agent
from travel_planner.orchestrator.state import TravelState


async def check_weather_node(state: TravelState) -> dict:
    """Store the agent's weather summary in `weather_info`."""
    reply, seconds = await call_agent("weather", f"Weather for {state['destination']}", state)
    return {
        "weather_info": reply,
        "node_log": [f"[{state['task_id']}] check_weather → A2A :{config.WEATHER_AGENT_PORT} ({seconds}s)"],
    }
