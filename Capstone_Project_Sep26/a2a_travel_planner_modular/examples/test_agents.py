"""
Test each specialist agent on its own via A2A (notebook Section 8).

Each call goes through the full stack:
A2AClient.send() → JSON-RPC POST → FastAPI handler → LangChain agent → tool → LLM → reply

    uv run python -m examples.test_agents
"""

import asyncio

from travel_planner import config
from travel_planner.a2a.client import A2AClient
from travel_planner.agents.launcher import ensure_agents_running
from travel_planner.llm import verify_openai_key

# (agent name, message to send)
TEST_MESSAGES = [
    ("destination", "Research destination: Rome"),
    ("weather", "What's the weather in Singapore?"),
    ("budget", "Budget for 5 days in Singapore"),
    ("hr", "Leave balance for employee E1002. Planned trip: 5 days in Singapore."),
]


async def main() -> None:
    for number, (name, message) in enumerate(TEST_MESSAGES, start=1):
        print("═" * 65)
        print(f"TEST {number} — {name} agent  ({config.AGENT_REGISTRY[name]})")
        print(f"Sending: {message!r}")
        print("═" * 65)
        reply = await A2AClient(config.AGENT_REGISTRY[name]).send(message)
        print(reply, "\n")


if __name__ == "__main__":
    config.setup_logging()
    verify_openai_key()
    ensure_agents_running()
    asyncio.run(main())
