from __future__ import annotations

import json
from json import JSONDecodeError

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from src.agents.state import ChatState, ensure_chat_state
from src.agents.tools.context_tools import get_battery_context, get_datetime_context
from src.agents.tools.weather import fetch_weather_context
from src.agents.tools.events import get_city_events_tool
from src.agents.tools.planning_tools import rank_city_plans
from src.utils.logger import logger as log

CONTEXT_WORKER_NODE = "context_worker"
PLANNER_WORKER_NODE = "planner_worker"


def _safe_parse_json(content: str) -> dict | None:
    try:
        value = json.loads(content)
        return value if isinstance(value, dict) else None
    except (JSONDecodeError, TypeError, ValueError):
        return None


def _retry_once_invoke(agent, payload: dict, node_name: str):
    try:
        return agent.invoke(payload)
    except Exception:
        log.exception(f"{node_name} invocation failed, retrying once")
    try:
        return agent.invoke(payload)
    except Exception:
        log.exception(f"{node_name} invocation failed after retry; continuing with partial context")
        return None


def context_worker_node(state: ChatState) -> dict:
    """ReAct worker for context assembly using tools with retry-once policy."""
    state_obj = ensure_chat_state(state)
    city = state_obj.selected_city
    if not city:
        return {}
    if not state_obj.chatbot:
        return {}

    worker = create_react_agent(
        model=state_obj.chatbot.llm,
        tools=[get_battery_context, get_datetime_context, fetch_weather_context],
    )

    prompt = HumanMessage(
        content=(
            "You are a context worker. Use tools to collect battery, datetime and weather context. "
            "Return strict JSON with keys: battery_context, datetime_context, weather_context. "
            f"Use household_id={state_obj.household_id}, user_id={state_obj.user_id}, city={city}."
        )
    )

    result = _retry_once_invoke(worker, {"messages": [prompt]}, CONTEXT_WORKER_NODE)
    if not result:
        return {}

    messages = result.get("messages", []) if isinstance(result, dict) else []
    if not messages:
        return {}

    content = getattr(messages[-1], "content", "")
    if not isinstance(content, str):
        return {}

    payload = _safe_parse_json(content)
    if not payload:
        return {}

    battery_context = payload.get("battery_context")
    datetime_context = payload.get("datetime_context")
    weather_context = payload.get("weather_context")

    updates: dict = {}
    if isinstance(battery_context, dict):
        updates["battery_context"] = battery_context
    if isinstance(datetime_context, dict):
        updates["datetime_context"] = datetime_context
    if isinstance(weather_context, dict):
        updates["weather_context"] = {city: weather_context}

    remaining = [task for task in state_obj.workflow_plan if task != CONTEXT_WORKER_NODE]
    updates["workflow_plan"] = remaining
    return updates


def planner_worker_node(state: ChatState) -> dict:
    """ReAct worker that gathers events and ranks plans with tools."""
    state_obj = ensure_chat_state(state)
    city = state_obj.selected_city
    if not city:
        return {}
    if not state_obj.chatbot:
        return {}

    worker = create_react_agent(
        model=state_obj.chatbot.llm,
        tools=[get_city_events_tool, rank_city_plans],
    )

    prompt = HumanMessage(
        content=(
            "You are a planning worker. Use tools to fetch events for the selected city and rank plans. "
            "Return strict JSON with keys: city_events, ranked_plans. "
            f"Selected city={city}. Battery context={state_obj.battery_context.model_dump() if state_obj.battery_context else {}}. "
            f"Weather context={state_obj.weather_context.get(city).model_dump() if state_obj.weather_context.get(city) else {}}."
        )
    )

    result = _retry_once_invoke(worker, {"messages": [prompt]}, PLANNER_WORKER_NODE)
    if not result:
        return {}

    messages = result.get("messages", []) if isinstance(result, dict) else []
    if not messages:
        return {}

    content = getattr(messages[-1], "content", "")
    if not isinstance(content, str):
        return {}

    payload = _safe_parse_json(content)
    if not payload:
        return {}

    updates: dict = {}
    city_events = payload.get("city_events")
    ranked_plans = payload.get("ranked_plans")
    if isinstance(city_events, dict):
        updates["city_events"] = city_events
    if isinstance(ranked_plans, list):
        updates["ranked_plans"] = ranked_plans

    remaining = [task for task in state_obj.workflow_plan if task != PLANNER_WORKER_NODE]
    updates["workflow_plan"] = remaining
    return updates
