from __future__ import annotations

from langchain.agents import create_agent
from langgraph.runtime import Runtime

from src.agents.graph import GraphContext
from src.agents.state import ChatState, ensure_chat_state
from src.agents.tools.battery_tool import create_battery_context_tool
from src.agents.tools.date_tool import create_datetime_tool
from src.agents.tools.weather_tool import create_weather_tool
from src.agents.tools.events_tools import create_city_events_tool
from src.agents.tools.planning_tools import create_plan_ranker_tool
from src.utils.logger import logger as log

PLANNING_AGENT_NODE = "planning_agent"


def planning_agent_node(state: ChatState, runtime: Runtime[GraphContext]) -> dict:
    """Minimal planning agent invocation using create_agent and existing messages."""
    state = ensure_chat_state(state)
    if not state.chatbot or not state.messages:
        return {}

    ctx = GraphContext(
        db_client=runtime.context.db_client,
        household_id=state.household_id,
        user_id=state.user_id,
    )

    system_prompt = state.system_prompt or "You are a helpful assistant"
    agent = create_agent(
        model=state.chatbot.llm,
        tools=[
            create_battery_context_tool(context=ctx),
            create_datetime_tool(context=ctx),
            create_weather_tool(context=ctx),
            create_city_events_tool(context=ctx),
            create_plan_ranker_tool(context=ctx),
        ],
        system_prompt=system_prompt,
    )

    response = agent.invoke(
        {"messages": state.messages},
    )
    response_messages = response.get("messages", []) if isinstance(response, dict) else []
    log.debug("Planning agent response: %s", response_messages)

    return {"messages": response_messages} if response_messages else {}
