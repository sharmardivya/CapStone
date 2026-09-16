"""
A2A client — how one agent (or the orchestrator) talks to another agent.

    client = A2AClient("http://127.0.0.1:8001")
    card   = await client.discover()                  # GET /.well-known/agent.json
    answer = await client.send("Research destination: Rome")   # JSON-RPC message/send
"""

from typing import Any, Dict, Optional

import httpx

from travel_planner import config
from travel_planner.a2a.models import AgentCard, JSONRPCRequest, Message, TextPart


class A2AError(RuntimeError):
    """Raised when an agent answers with a JSON-RPC error instead of a result."""


class A2AClient:
    """Async HTTP client that speaks the A2A JSON-RPC 2.0 protocol."""

    def __init__(self, base_url: str, timeout: float = config.A2A_REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def discover(self) -> AgentCard:
        """Fetch the agent's AgentCard to learn its name, URL and skills."""
        async with httpx.AsyncClient(timeout=config.DISCOVERY_TIMEOUT) as http:
            response = await http.get(f"{self.base_url}{config.AGENT_CARD_PATH}")
            response.raise_for_status()
        return AgentCard(**response.json())

    @staticmethod
    def build_request(text: str, context: Optional[Dict[str, Any]] = None) -> JSONRPCRequest:
        """Wrap `text` in a JSON-RPC "message/send" request."""
        message = Message(role="user", parts=[TextPart(text=text)])
        return JSONRPCRequest(
            method="message/send",
            params={"message": message.model_dump(), "context": context or {}},
        )

    async def send(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Send `text` to the agent and return the text of its reply."""
        request = self.build_request(text, context)
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            response = await http.post(self.base_url, json=request.model_dump())
            response.raise_for_status()

        body = response.json()
        if body.get("error"):
            error = body["error"]
            raise A2AError(f"{self.base_url} returned error {error.get('code')}: {error.get('message')}")
        return Message(**body.get("result", {})).get_text()
