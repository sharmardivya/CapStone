"""
Agent discovery via A2A (notebook Section 7).

Reads each agent's AgentCard from GET /.well-known/agent.json — this is how
an agent learns what another agent can do before calling it. No LLM calls.

    uv run python -m examples.discover_agents
"""

import asyncio
import json

from travel_planner import config
from travel_planner.a2a.client import A2AClient
from travel_planner.agents.launcher import ensure_agents_running


async def main() -> None:
    print("Agent discovery (GET /.well-known/agent.json)")
    print("─" * 65)
    cards = {}
    for name, url in config.AGENT_REGISTRY.items():
        try:
            card = await A2AClient(url).discover()
        except Exception as exc:
            print(f"  ✗ {name} unreachable: {exc}")
            continue
        cards[name] = card
        print(f"  ✓ {card.name}\n      URL    : {card.url}\n"
              f"      Skills : {', '.join(skill.name for skill in card.skills)}")

    print(f"\n{len(cards)}/{len(config.AGENT_REGISTRY)} agents discovered")
    if "destination" in cards:
        print("\nFull AgentCard JSON for the Destination Research Agent:")
        print(json.dumps(cards["destination"].model_dump(), indent=2))


if __name__ == "__main__":
    config.setup_logging()
    ensure_agents_running()
    asyncio.run(main())
