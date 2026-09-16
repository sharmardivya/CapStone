"""
Agent 3 — Budget Estimator Agent (A2A server on port 8003).

Inside:  a LangChain agent that looks up daily costs in the offline cost table
         and writes an itemized budget with money-saving tips.
Outside: a standard A2A endpoint.
"""

import logging

from fastapi import FastAPI
from langchain.agents import create_agent

from travel_planner import config
from travel_planner.a2a.models import AgentCard, AgentSkill
from travel_planner.a2a.server import create_a2a_app
from travel_planner.agents.agent_runner import ask_agent
from travel_planner.llm import create_agent_llm
from travel_planner.tools.cost_tool import lookup_travel_costs

logger = logging.getLogger(__name__)

AGENT_CARD = AgentCard(
    name="Budget Estimator Agent",
    description="Estimates travel budget via LangChain 1.x agent + cost database tool.",
    url=config.AGENT_REGISTRY["budget"],
    skills=[AgentSkill(
        id="estimate_budget",
        name="Estimate Travel Budget",
        description="Calculate itemized travel budget with LLM-written advice",
        tags=["budget", "finance", "langchain"],
        examples=["Budget for 5 days in Tokyo", "How much for a week in Bali?"],
    )],
)

SYSTEM_PROMPT = (
    "You are a travel budget specialist. Use the cost lookup tool, then write an "
    "itemized budget with daily breakdown, total cost, local currency notes, and money-saving tips."
)

# Maximum agent steps per request (stops runaway tool-call loops).
RECURSION_LIMIT = 6


def build_budget_app() -> FastAPI:
    """Create the LangChain agent and wrap it in an A2A FastAPI app."""
    agent = create_agent(
        model=create_agent_llm(),
        tools=[lookup_travel_costs],
        system_prompt=SYSTEM_PROMPT,
        debug=config.AGENT_DEBUG,
    )

    async def handle_message(text: str, context: dict) -> str:
        """A2A handler: itemized budget for the trip described in `text`."""
        prompt = (
            "Calculate an itemized travel budget for this query. "
            "Show daily breakdown, total cost, local currency conversion, "
            f"and practical money-saving tips: {text}"
        )
        try:
            return await ask_agent(agent, prompt, RECURSION_LIMIT) or "Budget information unavailable."
        except Exception as exc:
            logger.warning("Budget agent failed: %s", exc)
            return f"💰 Budget estimation failed ({exc}). Please check your API key."

    return create_a2a_app(AGENT_CARD, handle_message)
