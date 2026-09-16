"""
A2A server factory.

`create_a2a_app` wraps ANY async handler — plain Python or a LangChain agent —
in a FastAPI app that speaks the A2A protocol:

    GET  /.well-known/agent.json   → the AgentCard (discovery)
    POST /                         → JSON-RPC 2.0 "message/send" → handler → reply

HTTP is the transport (how bytes travel between machines).
JSON-RPC is the message format (which function to run, with which arguments).
"""

from typing import Any, Awaitable, Callable, Dict, Optional, Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from travel_planner import config
from travel_planner.a2a.models import (AgentCard, JSONRPCRequest, JSONRPCResponse,
                                       Message, TextPart)

# A handler receives the caller's text plus a context dict and returns reply text.
AgentHandler = Callable[[str, Dict[str, Any]], Awaitable[str]]

# Standard JSON-RPC 2.0 error codes
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INTERNAL_ERROR = -32603


def _rpc_response(request_id: Union[str, int], *, result: Optional[dict] = None,
                  error: Optional[dict] = None) -> JSONResponse:
    """Build a JSON-RPC 2.0 response body."""
    body = JSONRPCResponse(id=request_id, result=result, error=error)
    return JSONResponse(body.model_dump(exclude_none=True))


def create_a2a_app(agent_card: AgentCard, handler: AgentHandler) -> FastAPI:
    """Return a FastAPI app that exposes `handler` as an A2A-compliant agent."""
    app = FastAPI(title=agent_card.name, docs_url=None, redoc_url=None)

    @app.get(config.AGENT_CARD_PATH)
    async def get_agent_card() -> Dict[str, Any]:
        """Discovery: tell callers who this agent is and what it can do."""
        return agent_card.model_dump()

    @app.post("/")
    async def handle_jsonrpc(request: Request) -> JSONResponse:
        """Receive a JSON-RPC request, run the handler, return its answer."""
        try:
            rpc = JSONRPCRequest(**(await request.json()))
        except Exception as exc:
            return _rpc_response("unknown", error={
                "code": INVALID_REQUEST, "message": f"Invalid JSON-RPC request: {exc}"})

        if rpc.method != "message/send":
            return _rpc_response(rpc.id, error={
                "code": METHOD_NOT_FOUND, "message": f"Unknown method: {rpc.method}"})

        try:
            incoming = Message(**rpc.params.get("message", {}))
            context = rpc.params.get("context") or {}
            reply_text = await handler(incoming.get_text(), context)
        except Exception as exc:
            return _rpc_response(rpc.id, error={"code": INTERNAL_ERROR, "message": str(exc)})

        reply = Message(role="agent", parts=[TextPart(text=reply_text)])
        return _rpc_response(rpc.id, result=reply.model_dump())

    return app
