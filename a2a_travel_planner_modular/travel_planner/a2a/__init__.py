"""
A2A (Agent-to-Agent) protocol layer.

Nothing in this sub-package knows about LangChain or travel — it can wrap any
agent. That is the point of A2A: the protocol is framework-agnostic.

    models.py         AgentCard, Message, JSON-RPC envelopes
    server.py         create_a2a_app(): wrap an async handler in a FastAPI A2A server
    client.py         A2AClient: discover an agent and send it a message
    server_runner.py  run FastAPI apps as background HTTP servers
"""
