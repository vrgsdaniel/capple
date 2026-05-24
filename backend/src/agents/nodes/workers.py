from __future__ import annotations

from langchain.agents import create_agent
from langgraph.runtime import Runtime

from src.agents.graph import GraphContext
from src.agents.state import ChatState, ensure_chat_state
from src.agents.tools.battery_tool import create_battery_context_tool
from src.agents.tools.date_tool import get_datetime_tool
from src.agents.tools.weather_tool import fetch_weather_context
from src.agents.tools.events_tools import get_city_events_tool
from src.agents.tools.planning_tools import create_city_plans_tool

PLANNING_AGENT_NODE = "planning_agent"


def _build_tool_agent(model, system_prompt: str, get_battery_tool_tool):

    return create_agent(
        model=model,
        tools=[
            get_battery_tool_tool,
            get_datetime_tool,
            fetch_weather_context,
            get_city_events_tool,
            create_city_plans_tool,
        ],
        system_prompt=system_prompt,
        context_schema=GraphContext,
    )


def planning_agent_node(state: ChatState, runtime: Runtime[GraphContext]) -> dict:
    """Minimal planning agent invocation using create_agent and existing messages."""
    state_obj = ensure_chat_state(state)
    if not state_obj.chatbot or not state_obj.messages:
        return {}

    db_client = runtime.context.db_client
    get_battery_tool_tool = create_battery_context_tool(
        db_client,
        state_obj.household_id,
        state_obj.user_id,
    )

    system_prompt = state_obj.system_prompt or "You are a helpful assistant"
    agent = _build_tool_agent(state_obj.chatbot.llm, system_prompt, get_battery_tool_tool)

    agent.invoke(
        {"messages": state_obj.messages},
        {
            "context": {
                "db_client": db_client,
                "household_id": state_obj.household_id,
                "user_id": state_obj.user_id,
            }
        },
    )
    return {}
