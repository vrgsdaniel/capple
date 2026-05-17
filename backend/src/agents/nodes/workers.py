from __future__ import annotations

from langchain.agents import create_agent

from src.agents.state import ChatState, ensure_chat_state
from src.agents.tools.context_tools import get_battery_context, get_datetime_context
from src.agents.tools.weather import fetch_weather_context
from src.agents.tools.events import get_city_events_tool
from src.agents.tools.planning_tools import rank_city_plans

PLANNING_AGENT_NODE = "planning_agent"


def _build_tool_agent(model, system_prompt: str):

    return create_agent(
        model=model,
        tools=[
            get_battery_context,
            get_datetime_context,
            fetch_weather_context,
            get_city_events_tool,
            rank_city_plans,
        ],
        system_prompt=system_prompt,
    )


def planning_agent_node(state: ChatState) -> dict:
    """Minimal planning agent invocation using create_agent and existing messages."""
    state_obj = ensure_chat_state(state)
    if not state_obj.chatbot or not state_obj.messages:
        return {}

    system_prompt = state_obj.system_prompt or "You are a helpful assistant"
    agent = _build_tool_agent(state_obj.chatbot.llm, system_prompt)

    agent.invoke({"messages": state_obj.messages})
    return {}
