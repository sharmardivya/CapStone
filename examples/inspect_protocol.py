"""
Raw A2A protocol inspection.

Sends a hand-built JSON-RPC request to the Destination Research Agent and
prints the exact request and response bodies. The caller only ever sees
JSON-RPC — the LangChain agent is hidden behind the A2A interface.

    uv run python -m examples.inspect_protocol
"""

import asyncio
import json

import httpx

from travel_planner import config
from travel_planner.a2a.client import A2AClient
from travel_planner.agents.launcher import ensure_agents_running
from travel_planner.llm import verify_openai_key

PREVIEW_CHARS = 250


async def main() -> None:
    url = config.AGENT_REGISTRY["destination"]
    request = A2AClient.build_request("Research destination: Barcelona",
                                      {"from_agent": "inspector"}).model_dump()

    print(f"POST {url}")
    print("Request body:", json.dumps(request, indent=2))

    async with httpx.AsyncClient(timeout=config.A2A_REQUEST_TIMEOUT) as http:
        response = (await http.post(url, json=request)).json()

    # Shorten the agent's long answer so the JSON structure stays readable.
    for part in response.get("result", {}).get("parts", []):
        part["text"] = part["text"][:PREVIEW_CHARS] + "  [...]"

    print("\nResponse body:", json.dumps(response, indent=2))


if __name__ == "__main__":
    config.setup_logging()
    verify_openai_key()
    ensure_agents_running()
    asyncio.run(main())
