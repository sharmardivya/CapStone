"""
Node 6 — synthesize_plan.

An LLM chain reads the four agents' raw answers and writes one well-formatted
travel plan that ends with the employee's leave balance. Also records the
finished task in the audit log.
"""

import logging
import time
from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from travel_planner.llm import get_synthesis_llm
from travel_planner.orchestrator.audit_log import record_task
from travel_planner.orchestrator.state import TravelState

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert travel planner. Synthesize information from four "
     "specialist AI agents into a comprehensive, engaging travel plan. "
     "Use clear formatting with sections and emojis. Be practical and specific. "
     "If the employee's leave balance does not cover the trip, say so clearly at the top."),
    ("human",
     "DESTINATION: {destination}\nDURATION: {duration}\nEMPLOYEE ID: {employee_id}\n\n"
     "━━━ FROM DESTINATION RESEARCH AGENT (A2A :8001 → LangChain+Wikipedia) ━━━\n"
     "{destination_info}\n\n"
     "━━━ FROM WEATHER INTELLIGENCE AGENT (A2A :8002 → LangChain+wttr.in) ━━━\n"
     "{weather_info}\n\n"
     "━━━ FROM BUDGET ESTIMATOR AGENT (A2A :8003 → LangChain+CostDB) ━━━\n"
     "{budget_info}\n\n"
     "━━━ FROM HR LEAVE AGENT (A2A :8004 → LangChain+SQLite) ━━━\n"
     "{leave_info}\n\n"
     "Create a comprehensive travel plan with:\n"
     "1. 🌟 Trip Highlights & Why Visit\n"
     "2. 📅 Day-by-Day Itinerary\n"
     "3. 🌤️ Weather Advisory & Best Packing Tips\n"
     "4. 💰 Budget Breakdown & Money-Saving Tips\n"
     "5. 🎯 Must-See Attractions & Hidden Gems\n"
     "6. 💡 Essential Travel Tips\n"
     "7. 🗓️ Leave Balance — the employee's remaining leave, whether it covers this trip, "
     "and how many annual leave days will be left afterwards"),
])

_PROMPT_FIELDS = ("destination", "duration", "employee_id",
                  "destination_info", "weather_info", "budget_info", "leave_info")


def _fallback_plan(state: TravelState, error: Exception) -> str:
    """If the LLM fails, show the agents' raw answers instead of nothing."""
    return (
        f"[LLM synthesis unavailable: {error}]\n\n"
        f"DESTINATION INFO:\n{state['destination_info']}\n\n"
        f"WEATHER INFO:\n{state['weather_info']}\n\n"
        f"BUDGET INFO:\n{state['budget_info']}\n\n"
        f"LEAVE BALANCE:\n{state['leave_info']}"
    )


async def synthesize_plan_node(state: TravelState) -> dict:
    """Write the final plan into `final_plan` and record the task."""
    logger.info("[%s] node 6 synthesize_plan: writing final plan", state["task_id"])
    started = time.perf_counter()

    chain = SYNTHESIS_PROMPT | get_synthesis_llm() | StrOutputParser()
    try:
        plan = await chain.ainvoke({field: state[field] for field in _PROMPT_FIELDS})
    except Exception as exc:
        logger.warning("[%s] LLM synthesis failed: %s", state["task_id"], exc)
        plan = _fallback_plan(state, exc)

    seconds = round(time.perf_counter() - started, 2)
    log_entry = f"[{state['task_id']}] synthesize_plan → done ({seconds}s)"

    record_task({
        "task_id": state["task_id"],
        "query": state["query"],
        "employee_id": state["employee_id"],
        "destination": state["destination"],
        "duration": state["duration"],
        "elapsed_s": seconds,
        "node_log": state.get("node_log", []) + [log_entry],
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
    })
    return {"final_plan": plan, "node_log": [log_entry]}
