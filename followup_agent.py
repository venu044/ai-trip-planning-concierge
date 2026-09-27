"""
Phase 5 -- Tool-Using Follow-Up Agent (Stage D).

A ReAct-style agent, backed by a MemorySaver checkpointer and a fixed
thread/session id, so it remembers earlier turns in the same session
(e.g. "what's 15% off that" after already having computed a total).
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from tools import ALL_TOOLS

FOLLOWUP_SYSTEM_PROMPT = """You are the follow-up desk of a travel concierge.
The traveler already received a trip plan and feasibility recommendation.
Answer their follow-up questions concisely, using your tools whenever the
question involves currency conversion, percentage/discount math, or
destination facts (weather, best time to visit). Keep answers short and
grounded in the tool results and the trip context you've been given."""


def build_followup_agent():
    """Compile a ReAct agent with tools + an in-memory checkpointer."""
    from llm_config import get_llm

    checkpointer = MemorySaver()
    agent = create_react_agent(get_llm(), ALL_TOOLS, checkpointer=checkpointer)
    return agent


def prime_agent_with_trip_context(agent, session_id: str, trip_request: dict, trip_tier: str, tier_explanation: str):
    """Seed the agent's memory with the trip context so follow-ups can refer to 'that budget', 'that total', etc."""
    context = (
        f"Trip context -- destination: {trip_request.get('destination')}, "
        f"travelers: {trip_request.get('travelers')}, "
        f"duration_days: {trip_request.get('duration_days')}, "
        f"budget: {trip_request.get('budget')} USD. "
        f"Recommended tier: {trip_tier}. {tier_explanation}"
    )
    config = {"configurable": {"thread_id": session_id}}
    agent.invoke(
        {"messages": [SystemMessage(content=FOLLOWUP_SYSTEM_PROMPT), HumanMessage(content=context)]},
        config=config,
    )


def ask_followup(agent, session_id: str, question: str) -> str:
    """Send one follow-up question through the agent and return its reply text."""
    config = {"configurable": {"thread_id": session_id}}
    result = agent.invoke({"messages": [HumanMessage(content=question)]}, config=config)
    return result["messages"][-1].content


def get_conversation_history(agent, session_id: str) -> list:
    """Read back the full message history for this session from the checkpointer."""
    config = {"configurable": {"thread_id": session_id}}
    state = agent.get_state(config)
    history = []
    for msg in state.values.get("messages", []):
        role = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", "")
        if content:
            history.append({"role": role, "content": content})
    return history
