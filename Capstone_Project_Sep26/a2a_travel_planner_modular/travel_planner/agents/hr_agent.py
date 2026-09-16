"""
Agent 4 — HR Leave Agent (A2A server on port 8004).

Inside:  a LangChain agent that looks up the employee's leave balance in the
         SQLite HR database and checks whether it covers the planned trip.
Outside: a standard A2A endpoint, exactly like the other three agents.

Unknown employee IDs are answered straight from the database (no LLM call),
with a reply that starts with config.EMPLOYEE_NOT_FOUND, so the orchestrator
can ask the user for a valid ID.
"""

import logging
import re

from fastapi import FastAPI
from langchain.agents import create_agent

from travel_planner import config
from travel_planner.a2a.models import AgentCard, AgentSkill
from travel_planner.a2a.server import create_a2a_app
from travel_planner.agents.agent_runner import ask_agent
from travel_planner.data.leave_db import create_leave_db, get_leave_balance
from travel_planner.llm import create_agent_llm
from travel_planner.tools.leave_tool import lookup_leave_balance

logger = logging.getLogger(__name__)

AGENT_CARD = AgentCard(
    name="HR Leave Agent",
    description="Looks up employee leave balances in the HR database (SQLite) via a LangChain 1.x agent.",
    url=config.AGENT_REGISTRY["hr"],
    skills=[AgentSkill(
        id="check_leave_balance",
        name="Check Leave Balance",
        description="Return an employee's remaining leave and whether it covers a planned trip",
        tags=["hr", "leave", "sqlite", "langchain"],
        examples=["Leave balance for employee E1001", "Can E1002 take a 5-day trip?"],
    )],
)

SYSTEM_PROMPT = (
    "You are an HR assistant. Use the leave lookup tool to find the employee's leave balance. "
    "Report the employee's name and each leave balance. Then say clearly whether their annual "
    "leave covers the planned trip (assume one day of annual leave per trip day) and how many "
    "annual leave days would remain. Never invent balances."
)

# Maximum agent steps per request (stops runaway tool-call loops).
RECURSION_LIMIT = 6


def build_hr_app() -> FastAPI:
    """Create the leave database, the LangChain agent, and wrap it in an A2A FastAPI app."""
    create_leave_db()  # make sure the SQLite database exists before the first request

    agent = create_agent(
        model=create_agent_llm(),
        tools=[lookup_leave_balance],
        system_prompt=SYSTEM_PROMPT,
        debug=config.AGENT_DEBUG,
    )

    async def handle_message(text: str, context: dict) -> str:
        """A2A handler: leave balance for the employee and trip described in `text`."""
        match = re.search(config.EMPLOYEE_ID_REGEX, text, re.IGNORECASE)
        employee_id = match.group(0) if match else ""
        if get_leave_balance(employee_id) is None:
            # Unknown (or missing) ID: reply directly from the database, no LLM needed.
            return lookup_leave_balance.invoke({"employee_id": employee_id})

        prompt = f"Check the leave balance for this request: {text}"
        try:
            return await ask_agent(agent, prompt, RECURSION_LIMIT) or "Leave balance unavailable."
        except Exception as exc:
            logger.warning("HR agent failed: %s", exc)
            return f"🗓️ Leave balance check failed ({exc})."

    return create_a2a_app(AGENT_CARD, handle_message)
