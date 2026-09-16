"""
Helper for nodes 2–5: call one specialist agent over A2A.
"""

import logging
import time

from travel_planner import config
from travel_planner.a2a.client import A2AClient
from travel_planner.orchestrator.state import TravelState

logger = logging.getLogger(__name__)


async def call_agent(agent_name: str, text: str, state: TravelState) -> tuple[str, float]:
    """
    Send `text` to the agent registered as `agent_name`.

    Returns (reply text, seconds taken). Never raises: if the agent is down,
    the reply is a warning message, so the final plan can still be written
    from the other agents' answers.
    """
    url = config.AGENT_REGISTRY[agent_name]
    context = {"task_id": state["task_id"], "from_agent": "langgraph_orchestrator"}

    started = time.perf_counter()
    try:
        reply = await A2AClient(url).send(text, context)
    except Exception as exc:
        logger.warning("[%s] %s agent call failed: %s", state["task_id"], agent_name, exc)
        reply = f"⚠️ The {agent_name} agent was unavailable ({exc}). No {agent_name} data for this plan."
    seconds = round(time.perf_counter() - started, 2)

    logger.info("[%s] %s agent replied: %d chars in %.2fs", state["task_id"], agent_name, len(reply), seconds)
    return reply, seconds
