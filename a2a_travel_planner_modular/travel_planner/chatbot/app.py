"""
Gradio chatbot that runs in the browser.

The chatbot remembers the request being planned. If the first message has no
employee ID (or no destination), the bot asks only for what is missing, and the
user's answer is combined with the earlier messages. After a plan is delivered,
the next message starts a new request.

While the pipeline runs, the reply bubble shows which agent is working; when it
finishes, it is replaced by the travel plan (ending with the leave balance).
"""

import logging
from typing import AsyncIterator, List

import gradio as gr

from travel_planner import config
from travel_planner.orchestrator.graph import get_travel_graph
from travel_planner.orchestrator.state import make_initial_state

logger = logging.getLogger(__name__)

TITLE = "🌍 A2A Travel Planner"
DESCRIPTION = (
    "Ask for a trip plan, e.g. *Plan a 5-day trip to Tokyo for employee E1001*. "
    "If something is missing — like your employee ID — I'll ask for it. "
    "Sample employee IDs: E1001–E1005. Four AI agents (HR leave, destination research, "
    "weather, budget) work together over the A2A protocol."
)
EXAMPLES = [
    "Plan a 5-day trip to Tokyo for employee E1001",
    "I want to visit Bali for 7 days",
    "Weekend trip to Rome for employee E1004",
    "Plan 4 days in Amsterdam, my employee ID is E1005",
]

# Marks a finished plan in the chat; the next user message starts a new request.
TRACE_HEADING = "**How this plan was made**"

# What happens NEXT after each node finishes (shown while waiting).
NEXT_STEP_AFTER = {
    "parse_query": "🗓️ Checking your leave balance (HR Leave Agent · A2A :8004)…",
    "check_leave_balance": "🔎 Researching the destination (Destination Research Agent · A2A :8001)…",
    "research_destination": "🌤️ Checking the weather (Weather Intelligence Agent · A2A :8002)…",
    "check_weather": "💰 Estimating the budget (Budget Estimator Agent · A2A :8003)…",
    "estimate_budget": "✍️ Writing your travel plan…",
}

# Short label for each finished node (shown as a checklist while waiting).
DONE_LABEL = {
    "parse_query": "Understood the request",
    "check_leave_balance": "Leave balance checked",
    "research_destination": "Destination researched",
    "check_weather": "Weather checked",
    "estimate_budget": "Budget estimated",
    "synthesize_plan": "Plan written",
}


def _message_text(content) -> str:
    """Text of a chat message; Gradio may store content as a string or a list of parts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def _collect_request(history: list, message: str) -> str:
    """
    Join the user's messages since the last finished plan with the new message,
    so answers to the bot's questions are combined with the original request.
    """
    user_messages: List[str] = []
    for turn in history:
        text = _message_text(turn.get("content"))
        if turn.get("role") == "assistant" and TRACE_HEADING in text:
            user_messages = []  # a plan was delivered: the old request is finished
        elif turn.get("role") == "user":
            user_messages.append(text)
    return "\n".join(user_messages + [message])


def _progress_message(done: List[str], current: str) -> str:
    """Checklist of finished steps followed by the step in progress."""
    lines = [f"✅ {DONE_LABEL[node]}" for node in done]
    return "\n\n".join(lines + [f"**{current}**"])


def _trace_section(node_log: List[str]) -> str:
    """Footer listing each node and how long it took."""
    return f"\n\n---\n{TRACE_HEADING}\n```\n" + "\n".join(node_log) + "\n```"


async def respond(message: str, history: list) -> AsyncIterator[str]:
    """
    Gradio chat handler.

    Streams the pipeline node by node (`astream` with stream_mode="updates"),
    yielding a progress message after each node, then either the final plan or
    a question asking for missing details.
    """
    text = (message or "").strip()
    if not text:
        yield "Please type a travel request, e.g. *Plan a 5-day trip to Tokyo*."
        return

    query = _collect_request(history, text)
    done: List[str] = []
    node_log: List[str] = []
    final_plan = ""
    yield _progress_message(done, "🧭 Understanding your request…")

    try:
        async for update in get_travel_graph().astream(make_initial_state(query), stream_mode="updates"):
            for node_name, output in update.items():  # one update per finished node
                done.append(node_name)
                node_log += output.get("node_log", [])
                final_plan = output.get("final_plan") or final_plan
                if node_name in NEXT_STEP_AFTER and not final_plan:
                    yield _progress_message(done, NEXT_STEP_AFTER[node_name])
    except Exception as exc:
        logger.exception("Pipeline failed for query %r", query)
        yield f"⚠️ Sorry, something went wrong while planning your trip:\n\n`{exc}`"
        return

    if "synthesize_plan" in done:
        yield final_plan + _trace_section(node_log)
    else:
        yield final_plan  # a question: the next message will be combined with this request


def build_chat_ui() -> gr.ChatInterface:
    """Create the Gradio chat interface (not launched yet)."""
    return gr.ChatInterface(
        fn=respond,
        chatbot=gr.Chatbot(height=600, placeholder="Where would you like to go? ✈️"),
        textbox=gr.Textbox(placeholder="e.g. Plan a 5-day trip to Tokyo for employee E1001", submit_btn=True),
        examples=EXAMPLES,
        run_examples_on_click=False,  # clicking an example only fills the input box, so it can be edited first
        title=TITLE,
        description=DESCRIPTION,
        concurrency_limit=4,  # up to 4 trips planned at the same time
    )


def launch_chatbot(open_browser: bool = True) -> None:
    """Start the chatbot web server (blocks until Ctrl+C)."""
    build_chat_ui().launch(
        server_name=config.CHATBOT_HOST,
        server_port=config.CHATBOT_PORT,
        inbrowser=open_browser,
        theme=gr.themes.Soft(),
    )
