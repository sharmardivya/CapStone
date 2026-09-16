"""
ChatOpenAI clients and an API-key health check.

Why clients are never shared between event loops
    Each agent server runs in its own thread with its own asyncio event loop,
    and the orchestrator (CLI or chatbot) runs in another loop. An async HTTP
    connection belongs to the loop that opened it; reusing it from a different
    loop makes the request hang. So:
      • every specialist agent creates its own client  → create_agent_llm()
      • the orchestrator gets one client per event loop → get_synthesis_llm()
    Each client also has its own connection pool (http_async_client), because
    ChatOpenAI otherwise shares one global pool between all instances.
"""

import asyncio
import os
import weakref

import httpx
from langchain_openai import ChatOpenAI
from openai import (APIConnectionError, AuthenticationError, NotFoundError,
                    PermissionDeniedError, RateLimitError)

from travel_planner import config


def _new_chat_model(temperature: float) -> ChatOpenAI:
    """ChatOpenAI with a request timeout and its own async connection pool."""
    return ChatOpenAI(
        model=config.MODEL_NAME,
        temperature=temperature,
        timeout=config.LLM_TIMEOUT,
        http_async_client=httpx.AsyncClient(timeout=config.LLM_TIMEOUT),
    )


def create_agent_llm() -> ChatOpenAI:
    """New LLM client for one specialist agent (temperature 0). Call once per agent."""
    return _new_chat_model(config.AGENT_TEMPERATURE)


# One orchestrator client per event loop; entries disappear when a loop is garbage-collected.
_synthesis_llms: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, ChatOpenAI]" = weakref.WeakKeyDictionary()


def get_synthesis_llm() -> ChatOpenAI:
    """
    LLM the orchestrator uses to parse the query and write the final plan
    (temperature 0.3). Call it from async code (a LangGraph node).
    """
    loop = asyncio.get_running_loop()
    if loop not in _synthesis_llms:
        _synthesis_llms[loop] = _new_chat_model(config.SYNTHESIS_TEMPERATURE)
    return _synthesis_llms[loop]


def verify_openai_key(model: str = config.MODEL_NAME) -> str:
    """
    Make one tiny LLM call (~15 tokens) to prove the key is valid, has credit
    and can use `model`.

    Returns the model's reply. Raises RuntimeError with a readable reason if
    the key does not work, so scripts stop before starting any servers.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(f"OPENAI_API_KEY is not set. Add it to {config.PROJECT_DIR / '.env'}")

    probe = ChatOpenAI(model=model, temperature=0, max_tokens=5, max_retries=0, timeout=20)
    try:
        reply = probe.invoke("Reply with the single word: OK")
    except AuthenticationError:
        reason = "Invalid API key (401). Check the value in .env, or the key may have been revoked."
    except PermissionDeniedError:
        reason = "Key is valid but lacks permission (403). Check the key's project/organization settings."
    except RateLimitError as exc:
        if "insufficient_quota" in str(exc):
            reason = "Key is valid but the account has no credit (insufficient_quota). Add billing at platform.openai.com."
        else:
            reason = "Rate limit hit (429). Wait a moment and try again."
    except NotFoundError:
        reason = f"Key is valid but model '{model}' is not available to this account (404)."
    except APIConnectionError:
        reason = "Could not reach api.openai.com. Check your internet connection / proxy."
    else:
        return str(reply.content).strip()

    raise RuntimeError(f"OpenAI API key check failed: {reason}")
