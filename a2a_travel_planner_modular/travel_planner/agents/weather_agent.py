"""
Agent 2 — Weather Intelligence Agent (A2A server on port 8002).

Inside:  a LangChain agent that fetches live weather from wttr.in and turns it
         into packing and activity advice.
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
from travel_planner.tools.weather_tool import fetch_weather_data

logger = logging.getLogger(__name__)

AGENT_CARD = AgentCard(
    name="Weather Intelligence Agent",
    description="Provides weather conditions via LangChain 1.x agent + custom wttr.in tool.",
    url=config.AGENT_REGISTRY["weather"],
    skills=[AgentSkill(
        id="get_weather",
        name="Get Current Weather",
        description="Return live weather conditions with travel advice",
        tags=["weather", "climate", "langchain"],
        examples=["Weather for Tokyo", "What's the weather in Paris?"],
    )],
)

SYSTEM_PROMPT = (
    "You are a weather intelligence specialist for travelers. "
    "Use the weather tool, then summarize conditions with practical packing and activity advice."
)

# Maximum agent steps per request (stops runaway tool-call loops).
RECURSION_LIMIT = 6


def build_weather_app() -> FastAPI:
    """Create the LangChain agent and wrap it in an A2A FastAPI app."""
    agent = create_agent(
        model=create_agent_llm(),
        tools=[fetch_weather_data],
        system_prompt=SYSTEM_PROMPT,
        debug=config.AGENT_DEBUG,
    )

    async def handle_message(text: str, context: dict) -> str:
        """A2A handler: weather summary for the destination named in `text`."""
        prompt = (
            "Get the current weather for the travel destination mentioned and "
            f"provide a helpful weather summary with travel advice: {text}"
        )
        try:
            return await ask_agent(agent, prompt, RECURSION_LIMIT) or "Weather information unavailable."
        except Exception as exc:
            logger.warning("Weather agent failed: %s", exc)
            return f"🌤️ Weather data unavailable ({exc}). Please check your API key and internet connection."

    return create_a2a_app(AGENT_CARD, handle_message)
