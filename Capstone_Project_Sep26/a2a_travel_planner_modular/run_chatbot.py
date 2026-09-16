"""
Open the travel planner chatbot in your browser.

    uv run python run_chatbot.py
    uv run python run_chatbot.py --no-browser   # start the server without opening a tab

Checks the OpenAI key, starts the four A2A agents (unless run_agents.py is
already running them), then serves the chatbot at http://127.0.0.1:7860.
If the employee ID or destination is missing, the chatbot asks for it.
"""

import argparse
import logging

from travel_planner import config
from travel_planner.agents.launcher import ensure_agents_running
from travel_planner.chatbot.app import launch_chatbot
from travel_planner.llm import verify_openai_key

logger = logging.getLogger("run_chatbot")


def main() -> None:
    parser = argparse.ArgumentParser(description="A2A travel planner chatbot")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser tab")
    args = parser.parse_args()

    config.setup_logging()
    logger.info("OpenAI key OK (model replied %r)", verify_openai_key())
    ensure_agents_running()

    logger.info("Chatbot at http://%s:%d  (Ctrl+C to stop)", config.CHATBOT_HOST, config.CHATBOT_PORT)
    launch_chatbot(open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
