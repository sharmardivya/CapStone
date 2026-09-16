"""
Run FastAPI apps as background HTTP servers.

Each server gets its own daemon thread AND its own asyncio event loop, so
several agents (and the Gradio chatbot) can live in one Python process.
Daemon threads stop automatically when the main program exits.
"""

import asyncio
import socket
import threading

import uvicorn
from fastapi import FastAPI


def is_port_in_use(host: str, port: int) -> bool:
    """True if something is already listening on host:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _serve_forever(app: FastAPI, host: str, port: int) -> None:
    """Thread body: create a fresh event loop and run uvicorn on it."""
    # A new thread has no event loop, so create one just for this server.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
        loop.run_until_complete(server.serve())
    finally:
        loop.close()


def start_server_in_background(app: FastAPI, host: str, port: int, name: str) -> threading.Thread:
    """Start `app` on host:port in a daemon thread and return the thread."""
    thread = threading.Thread(target=_serve_forever, args=(app, host, port), name=name, daemon=True)
    thread.start()
    return thread
