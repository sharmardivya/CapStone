"""
Start the specialist agents and wait until they answer discovery.

If an agent is already running (for example started by run_agents.py in
another terminal), it is reused instead of started a second time.
"""

import logging
import time

import httpx

from travel_planner import config
from travel_planner.a2a.server_runner import is_port_in_use, start_server_in_background
from travel_planner.agents.budget_agent import build_budget_app
from travel_planner.agents.destination_agent import build_destination_app
from travel_planner.agents.hr_agent import build_hr_app
from travel_planner.agents.weather_agent import build_weather_app

logger = logging.getLogger(__name__)

# (registry name, port, function that builds the agent's FastAPI app)
AGENT_SPECS = [
    ("destination", config.DESTINATION_AGENT_PORT, build_destination_app),
    ("weather", config.WEATHER_AGENT_PORT, build_weather_app),
    ("budget", config.BUDGET_AGENT_PORT, build_budget_app),
    ("hr", config.HR_AGENT_PORT, build_hr_app),
]


def is_agent_ready(base_url: str) -> bool:
    """True if the agent at `base_url` serves its AgentCard."""
    try:
        return httpx.get(f"{base_url}{config.AGENT_CARD_PATH}", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


def ensure_agents_running() -> None:
    """Start every agent that is not already running, then wait for all of them."""
    for name, port, build_app in AGENT_SPECS:
        url = config.AGENT_REGISTRY[name]
        if is_agent_ready(url):
            logger.info("%s agent already running at %s", name, url)
            continue
        if is_port_in_use(config.AGENT_HOST, port):
            raise RuntimeError(
                f"Port {port} is used by another program, so the {name} agent cannot start. "
                "Close that program (for example an older copy of this app) and try again."
            )
        start_server_in_background(build_app(), config.AGENT_HOST, port, name=f"{name}-agent")
        logger.info("Starting %s agent at %s", name, url)

    _wait_until_ready()


def _wait_until_ready() -> None:
    """Poll each agent's AgentCard until all respond or the startup timeout passes."""
    deadline = time.monotonic() + config.AGENT_STARTUP_TIMEOUT
    pending = [name for name, _, _ in AGENT_SPECS]
    while pending:
        pending = [name for name in pending if not is_agent_ready(config.AGENT_REGISTRY[name])]
        if not pending:
            break
        if time.monotonic() > deadline:
            raise RuntimeError(
                f"Agents did not start within {config.AGENT_STARTUP_TIMEOUT:.0f}s: {', '.join(pending)}"
            )
        time.sleep(0.3)
    logger.info("All %d agents are ready", len(AGENT_SPECS))
