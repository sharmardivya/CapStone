"""
A2A protocol data models (Pydantic).

    AgentCard       the agent's "business card": what it does, where it lives,
                    which skills it offers. Served at /.well-known/agent.json.
    AgentSkill      one capability listed on the card.
    Message         one turn of communication, made of parts.
    TextPart        a text part inside a Message.
    JSONRPCRequest  the JSON-RPC 2.0 envelope around every call to an agent.
    JSONRPCResponse the JSON-RPC 2.0 envelope around every reply.

The original notebook tried to import the a2a-sdk types but then always
redefined these lightweight models, so these are what actually ran. This file
keeps that behaviour and the same JSON format.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


def _new_id() -> str:
    return str(uuid.uuid4())


class AgentSkill(BaseModel):
    """One capability an agent advertises to other agents."""
    id: str
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []


class AgentCapabilities(BaseModel):
    """Optional protocol features. These agents reply in a single response."""
    streaming: bool = False
    pushNotifications: bool = False


class AgentCard(BaseModel):
    """A2A agent manifest — lets other agents discover how to use this agent."""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    skills: List[AgentSkill] = []


class TextPart(BaseModel):
    """Plain-text content inside a Message."""
    type: str = "text"
    text: str


class Message(BaseModel):
    """One message between a caller ("user") and an agent ("agent")."""
    messageId: str = Field(default_factory=_new_id)
    role: str
    parts: List[TextPart]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    def get_text(self) -> str:
        """Join all text parts into one string."""
        return "".join(part.text for part in self.parts if part.type == "text")


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request. A2A uses method "message/send" to talk to an agent."""
    jsonrpc: str = "2.0"
    id: Union[str, int] = Field(default_factory=_new_id)
    method: str
    params: Dict[str, Any] = {}


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response: exactly one of `result` or `error` is set."""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
