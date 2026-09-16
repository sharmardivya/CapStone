"""
Central configuration.

Every value that could differ between machines lives here, so the rest of the
code never hard-codes a model name, port, URL or timeout.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Project root — the folder containing run_chatbot.py and .env
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Read OPENAI_API_KEY (and the optional overrides below) from that folder's .env
load_dotenv(PROJECT_DIR / ".env")


# ── LLM ──────────────────────────────────────────────────────────────────────
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
AGENT_TEMPERATURE = 0.0      # specialist agents: deterministic, factual answers
SYNTHESIS_TEMPERATURE = 0.3  # query parsing + final plan: slightly more natural writing
LLM_TIMEOUT = 60.0           # seconds; a stuck OpenAI call raises an error instead of hanging

# Set AGENT_DEBUG=true in .env to print every internal LangChain agent step.
AGENT_DEBUG = os.getenv("AGENT_DEBUG", "false").strip().lower() == "true"


# ── A2A agent servers ────────────────────────────────────────────────────────
# Each specialist agent runs as its own HTTP server on one of these ports.
AGENT_HOST = "127.0.0.1"
DESTINATION_AGENT_PORT = 8001
WEATHER_AGENT_PORT = 8002
BUDGET_AGENT_PORT = 8003
HR_AGENT_PORT = 8004


def agent_url(port: int) -> str:
    """Base URL of an agent server running on this machine."""
    return f"http://{AGENT_HOST}:{port}"


# Registry: how the orchestrator finds each agent (name → base URL).
AGENT_REGISTRY = {
    "destination": agent_url(DESTINATION_AGENT_PORT),
    "weather": agent_url(WEATHER_AGENT_PORT),
    "budget": agent_url(BUDGET_AGENT_PORT),
    "hr": agent_url(HR_AGENT_PORT),
}


# ── HR leave database (SQLite) ───────────────────────────────────────────────
# Created automatically with 5 sample employees when the HR agent starts.
LEAVE_DB_PATH = Path(__file__).resolve().parent / "data" / "hr_leave.db"

# Shared by the orchestrator and the HR agent:
EMPLOYEE_ID_REGEX = r"\bE\d+\b"                   # an employee ID is "E" + digits, e.g. E1001
EMPLOYEE_NOT_FOUND = "No employee found with ID"  # how the HR agent's reply starts for unknown IDs

# Well-known path where every A2A agent publishes its AgentCard (discovery).
AGENT_CARD_PATH = "/.well-known/agent.json"


# ── Timeouts (seconds) ───────────────────────────────────────────────────────
A2A_REQUEST_TIMEOUT = 60.0    # one agent call can involve several LLM + tool steps
DISCOVERY_TIMEOUT = 10.0      # fetching an AgentCard is a simple GET
AGENT_STARTUP_TIMEOUT = 20.0  # how long to wait for agent servers to come up


# ── Browser chatbot ──────────────────────────────────────────────────────────
# Hosting platforms such as Render set PORT and require listening on all interfaces.
# Locally PORT is not set, so the chatbot stays private to this machine on port 7860.
IS_HOSTED = "PORT" in os.environ
CHATBOT_HOST = "0.0.0.0" if IS_HOSTED else "127.0.0.1"
CHATBOT_PORT = int(os.getenv("PORT") or os.getenv("CHATBOT_PORT", "7860"))


# ── Generated files (flow diagram) ───────────────────────────────────────────
OUTPUT_DIR = PROJECT_DIR / "outputs"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure console logging for the entry-point scripts."""
    # Windows consoles default to a legacy code page; LLM answers contain emojis.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Third-party libraries are chatty at INFO level; only show their warnings.
    for noisy in ("uvicorn", "uvicorn.access", "uvicorn.error", "httpx",
                  "httpcore", "openai", "langchain", "gradio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
