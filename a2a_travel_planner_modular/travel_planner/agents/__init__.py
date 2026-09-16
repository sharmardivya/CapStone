"""
The four A2A specialist agents.

Each agent file follows the same pattern:
    1. AGENT_CARD     — what the agent tells other agents about itself
    2. SYSTEM_PROMPT  — instructions for the agent's LLM
    3. build_*_app()  — create a LangChain agent and wrap it in an A2A FastAPI app

    destination_agent.py  port 8001  LangChain agent + Wikipedia
    weather_agent.py      port 8002  LangChain agent + wttr.in
    budget_agent.py       port 8003  LangChain agent + offline cost table
    hr_agent.py           port 8004  LangChain agent + SQLite leave database
    agent_runner.py       helper: send one prompt to a LangChain agent
    launcher.py           start all agent servers and wait until they are ready
"""
