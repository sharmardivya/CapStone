"""
Agent 1 — Destination Research Agent (A2A server on port 8001).

Inside:  a LangChain agent that researches a destination with Wikipedia.
Outside: a standard A2A endpoint, so callers never see LangChain.
"""

import logging
import re

from fastapi import FastAPI
from langchain.agents import create_agent

from travel_planner import config
from travel_planner.a2a.models import AgentCard, AgentSkill
from travel_planner.a2a.server import create_a2a_app
from travel_planner.agents.agent_runner import ask_agent
from travel_planner.llm import create_agent_llm
from travel_planner.tools.wikipedia_tool import search_wikipedia, wikipedia_summary

logger = logging.getLogger(__name__)

AGENT_CARD = AgentCard(
    name="Destination Research Agent",
    description="Researches travel destinations using Wikipedia via a LangChain 1.x agent.",
    url=config.AGENT_REGISTRY["destination"],
    skills=[AgentSkill(
        id="research_destination",
        name="Research Destination",
        description="Fetch comprehensive overview of any travel destination",
        tags=["travel", "research", "wikipedia", "langchain"],
        examples=["Research destination: Paris", "Tell me about Tokyo"],
    )],
)

SYSTEM_PROMPT = (
    "You are a knowledgeable travel destination researcher. "
    "Use the Wikipedia tool to gather facts, then write a comprehensive overview "
    "covering attractions, culture, history, and travel tips."
)

# Maximum agent steps per request (stops runaway tool-call loops).
RECURSION_LIMIT = 8


def build_destination_app() -> FastAPI:
    """Create the LangChain agent and wrap it in an A2A FastAPI app."""
    agent = create_agent(
        model=create_agent_llm(),
        tools=[search_wikipedia],
        system_prompt=SYSTEM_PROMPT,
        debug=config.AGENT_DEBUG,
    )

    async def handle_message(text: str, context: dict) -> str:
        """A2A handler: research the destination named in `text`."""
        prompt = (
            "Research this travel destination and provide a comprehensive overview "
            f"covering attractions, culture, history, and travel tips: {text}"
        )
        try:
            return await ask_agent(agent, prompt, RECURSION_LIMIT) or "No destination information found."
        except Exception as exc:
            # LLM unavailable → plain Wikipedia summary, so the plan still has facts.
            logger.warning("Destination agent LLM failed, using Wikipedia fallback: %s", exc)
            destination = re.sub(r"(?i)(research|destination:|tell me about)", "", text).strip()
            return await wikipedia_summary(destination, note=f"LLM unavailable — {exc}")

    return create_a2a_app(AGENT_CARD, handle_message)
