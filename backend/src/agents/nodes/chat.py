from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.state import ChatState, ensure_chat_state
from src.settings import get_llm_settings

PARSE_USER_INPUT_NODE = "parse_user_input"

BASE_SYSTEM_PROMPT = """
    You are Capple, the assistant for a couples' household app.
    You may only answer questions about:
    - social battery and energy levels
    - battery logging, trends, and summaries
    - Capple app features and how to use the app
    - household or partner insights that come directly from Capple data
    - planning suggestions based on Capple data, weather, datetime, and local events

    Guardrails:
    - Do not answer general knowledge questions, unrelated advice, or off-topic requests.
    - If the user asks something outside Capple, battery levels, or social energy, refuse briefly and redirect them back to a Capple-related question.
    - If a question is only partly related, answer only the Capple-related part and ignore the rest.
    - Do not reveal raw user IDs or internal identifiers.
    - Keep replies concise, practical, and conversational.
"""

PLANNING_BEHAVIOR = """
    When the user asks for suggestions about what to do, synthesize:
    - social battery context
    - current weather context
    - local datetime context
    - local city events for Berlin and Madrid
    Then provide a ranked, practical plan. Prefer 2-3 options with brief reasons.
"""

INTENT_CONFIDENCE_THRESHOLD = get_llm_settings().intent_confidence_threshold


INTENT_ENUM = ("general_chat", "battery_levels", "suggest_plan", "app_help")


class ParsedUserInput(BaseModel):
    intent: Literal["general_chat", "battery_levels", "suggest_plan", "app_help"] = "app_help"
    city: str | None = None
    confidence: float = 0.0
    missing_requirements: list[str] = Field(default_factory=list)


PARSER_SYSTEM_PROMPT = """
You extract structured intent data for the Capple assistant.

Rules:
- Valid intents are exactly: general_chat, battery_levels, suggest_plan, app_help.
- Return app_help when the user asks about product/app usage, onboarding, settings, or troubleshooting.
- Return battery_levels for questions about social battery, energy level, or user/partner battery trends.
- Return suggest_plan when user asks what to do, suggestions, activities, plans, or events.
- Return general_chat for in-scope small talk that is not app-specific and not planning/battery-level focused.
- Confidence must be between 0 and 1.
- Extract city if explicitly provided by the user; otherwise null.
- missing_requirements may only include "city".
- For suggest_plan without city, include "city" in missing_requirements.
""".strip()


def _latest_user_text(state_obj: ChatState) -> str:
    for message in reversed(state_obj.messages or []):
        msg_type = getattr(message, "type", "")
        if msg_type == "human":
            content = getattr(message, "content", "")
            return str(content) if content is not None else ""
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def _parse_with_llm(state_obj: ChatState, user_text: str) -> ParsedUserInput:
    chatbot = state_obj.chatbot
    if not chatbot:
        return ParsedUserInput(intent="app_help", city=None, confidence=0.0, missing_requirements=[])

    structured_llm = chatbot.llm.with_structured_output(ParsedUserInput)
    parsed = structured_llm.invoke(
        [
            SystemMessage(content=PARSER_SYSTEM_PROMPT),
            HumanMessage(content=user_text),
        ]
    )

    if isinstance(parsed, ParsedUserInput):
        return parsed
    return ParsedUserInput.model_validate(parsed)


def parse_user_input_node(state: ChatState) -> dict:
    """Use LLM structured output to infer intent/city and missing requirements."""
    state_obj = ensure_chat_state(state)
    user_text = _latest_user_text(state_obj)

    try:
        parsed = _parse_with_llm(state_obj, user_text)
        parser_retry_needed = False
    except Exception:
        parsed = ParsedUserInput(intent="app_help", city=None, confidence=0.0, missing_requirements=[])
        parser_retry_needed = True

    router_intent = parsed.intent if parsed.intent in INTENT_ENUM else "app_help"
    selected_city = (parsed.city or "").strip() or state_obj.selected_city

    missing_requirements = [item for item in parsed.missing_requirements if item == "city"]
    if router_intent == "suggest_plan" and not selected_city and "city" not in missing_requirements:
        missing_requirements.append("city")

    confidence = max(0.0, min(1.0, float(parsed.confidence)))

    return {
        "router_intent": router_intent,
        "intent_confidence": confidence,
        "parser_retry_needed": parser_retry_needed,
        "selected_city": selected_city,
        "missing_requirements": missing_requirements,
    }


def _build_context_prompt(ctx: dict) -> str:
    return f"""
    {BASE_SYSTEM_PROMPT}
    Use the following household battery data only when it helps answer an in-scope question:
    - Your entries: {ctx['your_entries']} logs, avg level: {ctx['your_avg'] or 'no data'}
    - Partner entries: {ctx['partner_entries']} logs, avg level: {ctx['partner_avg'] or 'no data'}
    - Your trend: {ctx['your_trend']}
    - Partner trend: {ctx['partner_trend']}
    - Days since your last log: {ctx['days_since_your_last_log'] or 'never logged'}
    - Days since partner last log: {ctx['days_since_partner_last_log'] or 'never logged'}
    - Total entries (30d): {ctx['total_entries']}

    Use the data only to give short, empathetic, Capple-relevant insights.
"""


def _build_planning_prompt(state: ChatState) -> str:
    state_obj = ensure_chat_state(state)
    battery = (
        state_obj.battery_context.model_dump()
        if hasattr(state_obj.battery_context, "model_dump")
        else (state_obj.battery_context or {})
    )
    datetime_ctx = (
        state_obj.datetime_context.model_dump()
        if hasattr(state_obj.datetime_context, "model_dump")
        else (state_obj.datetime_context or {})
    )
    weather = {
        key: value.model_dump() if hasattr(value, "model_dump") else value
        for key, value in (state_obj.weather_context or {}).items()
    }
    ranked_plans = [plan.model_dump() if hasattr(plan, "model_dump") else plan for plan in state_obj.ranked_plans]
    city_events = {
        key: [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
        for key, value in (state_obj.city_events or {}).items()
    }

    def weather_line(city: str) -> str:
        row = weather.get(city) or {}
        return (
            f"{city}: {row.get('weather_label', 'unavailable')}, "
            f"{row.get('temperature', 'n/a')}C, precip {row.get('precipitation_probability', 'n/a')}%"
        )

    plan_lines = []
    for idx, plan in enumerate(ranked_plans, start=1):
        plan_lines.append(f"{idx}. {plan['title']} ({plan['city']}) - score {plan['score']} - {plan['rationale']}")

    selected_city = state_obj.selected_city or "unknown"
    event_count = len(city_events.get(selected_city, [])) if selected_city in city_events else 0

    return f"""
    {BASE_SYSTEM_PROMPT}
    {PLANNING_BEHAVIOR}
    Current context:
    - Your avg battery: {battery.get('your_avg', 'no data')}
    - Partner avg battery: {battery.get('partner_avg', 'no data')}
    - UTC now: {datetime_ctx.get('utc_iso', 'n/a')}
    - Selected city: {selected_city}
    - Local time: {datetime_ctx.get('local_iso', 'n/a')}
    - Weather: {weather_line(selected_city)}
    - Event options loaded in selected city: {event_count}

    Top ranked suggestions:
    {chr(10).join(plan_lines) if plan_lines else 'No ranked plans available.'}
    """


def system_prompt_node(state: ChatState) -> dict:
    """Build system prompt from routed context and planning data."""
    state_obj = ensure_chat_state(state)
    if state_obj.parser_retry_needed:
        system_prompt = (
            f"{BASE_SYSTEM_PROMPT}\n\n"
            "We could not safely interpret the request right now. "
            "Apologize briefly and ask the user to retry their last message."
        )
    elif state_obj.intent_confidence < INTENT_CONFIDENCE_THRESHOLD:
        system_prompt = (
            f"{BASE_SYSTEM_PROMPT}\n\n"
            "The user intent is ambiguous. Ask one concise clarifying question "
            "to determine whether they want battery insights, app help, or plan suggestions."
        )
    elif state_obj.missing_requirements:
        missing = ", ".join(state_obj.missing_requirements)
        system_prompt = (
            f"{BASE_SYSTEM_PROMPT}\n\n"
            f"Planning is missing required inputs: {missing}. "
            "Ask the user for their city before suggesting plans."
        )
    elif state_obj.router_intent == "suggest_plan":
        system_prompt = _build_planning_prompt(state)
    else:
        ctx = (
            state_obj.battery_context.model_dump()
            if hasattr(state_obj.battery_context, "model_dump")
            else state_obj.battery_context
        )
        system_prompt = _build_context_prompt(ctx) if ctx else BASE_SYSTEM_PROMPT
    return {"system_prompt": system_prompt}
