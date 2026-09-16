"""
Node 1 — parse_query.

Finds the three inputs the pipeline needs:
    destination  LLM chain (prompt | ChatOpenAI | text parser), regex fallback
    duration     same LLM call; defaults to "3 days"
    employee ID  the value passed in by the caller, otherwise the latest ID
                 like "E1001" written in the messages

The query may hold several user messages (the chatbot joins the messages of the
request in progress), so details given in earlier messages are remembered.

If something is missing, the node writes a question asking ONLY for that into
`final_plan`, and the graph stops so the user can answer.
"""

import logging
import re
import uuid

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from travel_planner import config
from travel_planner.llm import get_synthesis_llm
from travel_planner.orchestrator.state import TravelState

logger = logging.getLogger(__name__)

DEFAULT_DURATION = "3 days"

PARSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Extract the travel destination and trip duration from the user's messages. "
     "There may be several messages, oldest first; if the user changed a detail, use the most recent one. "
     f"If the duration is not mentioned, use '{DEFAULT_DURATION}'. "
     "If no travel destination is mentioned, use NONE as the destination. "
     "Reply ONLY in the exact format shown."),
    ("human",
     "Messages:\n{query}\n\nReply ONLY:\ndestination: <city or NONE>\nduration: <N days>"),
])

# Words the LLM may use to say "no destination"
_NO_DESTINATION_WORDS = {"", "NONE", "UNKNOWN", "N/A", "NULL"}


def _parse_with_regex(query: str) -> tuple[str, str]:
    """Fallback destination/duration parser when the LLM is unavailable."""
    dest_match = re.search(r"(?:trip to|visit|to|in)\s+([A-Za-z][A-Za-z ]{2,}?)(?:\s+for|\s*$)",
                           query, re.IGNORECASE | re.MULTILINE)
    dur_match = re.search(r"(\d+)\s*(days?|weeks?)", query, re.IGNORECASE)
    destination = dest_match.group(1).strip().title() if dest_match else ""
    duration = dur_match.group(0).strip() if dur_match else DEFAULT_DURATION
    return destination, duration


async def _parse_with_llm(query: str) -> tuple[str, str]:
    """Ask the LLM for 'destination: …' / 'duration: …' and read both lines."""
    chain = PARSE_PROMPT | get_synthesis_llm() | StrOutputParser()
    text = await chain.ainvoke({"query": query})
    dest_match = re.search(r"destination:\s*(.+)", text, re.IGNORECASE)
    dur_match = re.search(r"duration:\s*(.+)", text, re.IGNORECASE)
    destination = dest_match.group(1).strip() if dest_match else ""
    duration = dur_match.group(1).strip() if dur_match else DEFAULT_DURATION
    return destination, duration


def _find_employee_id(state: TravelState) -> str:
    """Use the employee ID passed in; otherwise the most recent one written in the messages."""
    if state.get("employee_id"):
        return state["employee_id"].strip().upper()
    ids = re.findall(config.EMPLOYEE_ID_REGEX, state["query"], re.IGNORECASE)
    return ids[-1].upper() if ids else ""


def _ask_for_missing_details(destination: str, duration: str, employee_id: str) -> str:
    """Ask only for what is missing."""
    if destination and not employee_id:
        return (f"Got it — **{duration} in {destination}**. What's your **employee ID** "
                "(e.g. E1001)? I need it to check your leave balance.")
    if employee_id and not destination:
        return (f"Thanks, employee **{employee_id}**. Where would you like to go, and for how long? "
                "(e.g. *5 days in Tokyo*)")
    return ("I'm a travel planner 🌍 — where would you like to go, for how long, and what's your "
            "employee ID? (e.g. *5 days in Tokyo, employee E1001*)")


async def parse_query_node(state: TravelState) -> dict:
    """Extract destination, duration and employee ID; ask for anything missing."""
    query = state["query"]
    task_id = uuid.uuid4().hex[:8]
    logger.info("[%s] node 1 parse_query: %r", task_id, query)

    try:
        destination, duration = await _parse_with_llm(query)
    except Exception as exc:
        logger.warning("[%s] LLM parsing failed (%s), using regex fallback", task_id, exc)
        destination, duration = _parse_with_regex(query)

    if destination.strip().upper() in _NO_DESTINATION_WORDS:
        destination = ""
    employee_id = _find_employee_id(state)

    logger.info("[%s] destination=%r duration=%r employee_id=%r", task_id, destination, duration, employee_id)
    update = {
        "destination": destination,
        "duration": duration,
        "employee_id": employee_id,
        "task_id": task_id,
        "node_log": [f"[{task_id}] parse_query → dest={destination or 'NONE'}, "
                     f"dur={duration}, employee={employee_id or 'NONE'}"],
    }
    if not destination or not employee_id:
        update["final_plan"] = _ask_for_missing_details(destination, duration, employee_id)
    return update
