"""
LangGraph state inspection (notebook Section 11).

Runs one request and prints every field of the final TravelState, showing how
node_log accumulated one entry per node.

    uv run python -m examples.inspect_state
"""

import asyncio

from travel_planner import config
from travel_planner.agents.launcher import ensure_agents_running
from travel_planner.llm import verify_openai_key
from travel_planner.orchestrator.graph import plan_trip

QUERY = "Plan a 4-day trip to Amsterdam"
EMPLOYEE_ID = "E1003"
AGENT_REPLY_FIELDS = ("destination_info", "weather_info", "budget_info", "leave_info")


async def main() -> None:
    state = await plan_trip(QUERY, EMPLOYEE_ID)

    print("\n" + "═" * 65)
    print("FULL STATE SNAPSHOT after pipeline completion")
    print("═" * 65)
    for key, value in state.items():
        if key == "final_plan":
            print(f"\n  {key}: [{len(value)} chars — first 200 shown]\n    {value[:200]}...")
        elif key == "node_log":
            print(f"\n  {key}: (accumulated across all nodes)")
            for entry in value:
                print(f"    {entry}")
        elif key in AGENT_REPLY_FIELDS:
            preview = str(value)[:100].replace("\n", " ")
            print(f"  {key}: [{len(str(value))} chars] {preview}...")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    config.setup_logging()
    verify_openai_key()
    ensure_agents_running()
    asyncio.run(main())
