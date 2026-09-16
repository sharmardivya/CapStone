"""
Start the four A2A specialist agents (destination, weather, budget, HR) and keep them running.

    uv run python run_agents.py

This is optional: run_chatbot.py and run_cli.py start the agents themselves
when they are not already running. Running them here, in their own terminal,
lets you restart the chatbot without restarting the agents and keeps agent
logs separate.
"""

import logging
import time

from travel_planner import config
from travel_planner.agents.launcher import ensure_agents_running
from travel_planner.llm import verify_openai_key

logger = logging.getLogger("run_agents")


def main() -> None:
    config.setup_logging()
    logger.info("OpenAI key OK (model replied %r)", verify_openai_key())

    ensure_agents_running()
    for name, url in config.AGENT_REGISTRY.items():
        logger.info("%-11s agent  %s   card: %s%s", name, url, url, config.AGENT_CARD_PATH)
    logger.info("Agents are running. Press Ctrl+C to stop.")

    try:
        while True:          # the servers run in background threads;
            time.sleep(1)    # keep the main thread alive until Ctrl+C
    except KeyboardInterrupt:
        logger.info("Stopping agents.")


if __name__ == "__main__":
    main()
