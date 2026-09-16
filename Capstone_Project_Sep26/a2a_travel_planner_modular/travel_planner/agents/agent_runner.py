"""
Helper shared by all specialist agents: run one prompt through a LangChain agent.
"""

from langchain_core.messages import HumanMessage


async def ask_agent(agent, prompt: str, recursion_limit: int) -> str:
    """
    Send `prompt` to a LangChain `create_agent` graph and return its final answer.

    The agent loops (LLM → tool → LLM …) until it can answer. `recursion_limit`
    caps the number of steps so a confused agent cannot loop forever.
    """
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=prompt)]},
        config={"recursion_limit": recursion_limit},
    )
    # The last message in the conversation is the agent's final answer.
    return str(result["messages"][-1].content)
