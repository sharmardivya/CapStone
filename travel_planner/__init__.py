"""
Multi-agent travel planner.

A LangGraph orchestrator calls three LangChain specialist agents
(destination research, weather, budget) over the A2A protocol and combines
their answers into one travel plan.

Package layout
    config.py       settings: model, ports, timeouts, logging
    llm.py          shared ChatOpenAI clients + API-key check
    a2a/            A2A protocol: data models, server factory, client, server runner
    tools/          LangChain tools the agents use (Wikipedia, weather, costs)
    data/           offline data (travel cost table)
    agents/         the three A2A specialist agents + a launcher that starts them
    orchestrator/   LangGraph state, one file per node, and the graph itself
    reporting/      task audit table and flow diagram
    chatbot/        Gradio chatbot that runs in the browser
"""
