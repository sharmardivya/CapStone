"""
Plan a trip from the terminal (notebook Section 9).

    uv run python run_cli.py "Plan a 5-day trip to Paris" --employee-id E1001
    uv run python run_cli.py "I want to visit Bali for 7 days, employee E1002" --diagram

The employee ID can be passed with --employee-id or written in the query.
Starts the agents if needed, runs the full LangGraph + A2A pipeline, and prints
the node log, the final plan (with leave balance) and the audit table.
--diagram also saves the flow diagram PNG to outputs/.
"""

import argparse
import asyncio
import logging
import time

from travel_planner import config
from travel_planner.agents.launcher import ensure_agents_running
from travel_planner.llm import verify_openai_key
from travel_planner.orchestrator.graph import plan_trip
from travel_planner.reporting.audit_report import format_audit_report

DIVIDER = "═" * 65


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-agent A2A travel planner")
    parser.add_argument("query", nargs="?", default="Plan a 5-day trip to Paris",
                        help='Travel request, e.g. "Plan a 5-day trip to Tokyo"')
    parser.add_argument("--employee-id", default="",
                        help="Employee ID for the leave balance check, e.g. E1001")
    parser.add_argument("--diagram", action="store_true",
                        help="Also save the flow diagram PNG to outputs/")
    return parser.parse_args()


async def run(query: str, employee_id: str) -> None:
    print(f"\n{DIVIDER}\nUser query : {query}\nEmployee ID: {employee_id or '(from query)'}\n{DIVIDER}")
    started = time.perf_counter()
    state = await plan_trip(query, employee_id)
    total = round(time.perf_counter() - started, 2)

    print(f"\n{DIVIDER}\nTotal pipeline time: {total}s\n{DIVIDER}")
    print("Node execution log:")
    for entry in state["node_log"]:
        print(f"  {entry}")
    print(f"\n{DIVIDER}\nFINAL TRAVEL PLAN\n{DIVIDER}\n{state['final_plan']}\n")


def main() -> None:
    args = parse_args()
    config.setup_logging()
    verify_openai_key()
    ensure_agents_running()

    asyncio.run(run(args.query, args.employee_id))
    print(format_audit_report())

    if args.diagram:
        from travel_planner.reporting.flow_diagram import save_flow_diagram  # matplotlib is slow to import
        logging.getLogger("run_cli").info("Diagram saved to %s", save_flow_diagram())


if __name__ == "__main__":
    main()
