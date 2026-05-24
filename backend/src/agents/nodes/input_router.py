import warnings
from typing import Literal

from pydantic import BaseModel, Field

from src.agents.state import ChatState, ensure_chat_state
from langchain_core.messages import HumanMessage, SystemMessage
from src.utils.logger import logger as log
from src.settings import get_llm_settings

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

INTENT_CONFIDENCE_THRESHOLD = get_llm_settings().intent_confidence_threshold


INTENT_ENUM = ("general_chat", "battery_levels", "suggest_plan", "app_help")


class ParsedUserInput(BaseModel):
    intent: Literal["general_chat", "battery_levels", "suggest_plan", "app_help"] = "app_help"
    city: str | None = None
    confidence: float = 0.0
    missing_requirements: list[str] = Field(default_factory=list)


def _parse_with_llm(state_obj: ChatState, user_text: str) -> ParsedUserInput:
    chatbot = state_obj.chatbot
    if not chatbot:
        return ParsedUserInput(intent="app_help", city=None, confidence=0.0, missing_requirements=[])

    structured_llm = chatbot.llm.with_structured_output(ParsedUserInput)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"Pydantic serializer warnings:.*field_name='parsed'.*",
            category=UserWarning,
        )
        parsed = structured_llm.invoke(
            [
                SystemMessage(content=PARSER_SYSTEM_PROMPT),
                HumanMessage(content=user_text),
            ]
        )

    if isinstance(parsed, ParsedUserInput):
        return parsed
    return ParsedUserInput.model_validate(parsed)


def _latest_user_text(state: ChatState) -> str:
    for message in reversed(state.messages or []):
        msg_type = getattr(message, "type", "")
        if msg_type == "human":
            content = getattr(message, "content", "")
            return str(content) if content is not None else ""
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def parse_user_input_node(state: ChatState) -> dict:
    """Use LLM structured output to infer intent/city and missing requirements."""
    user_text = _latest_user_text(ensure_chat_state(state))

    try:
        parsed = _parse_with_llm(state, user_text)
        parser_retry_needed = False
    except Exception as e:
        log.warning(f"Failed to parse user input with LLM, defaulting to app_help intent. Error: {e}")
        parsed = ParsedUserInput(intent="app_help", city=None, confidence=0.0, missing_requirements=[])
        parser_retry_needed = True

    router_intent = parsed.intent if parsed.intent in INTENT_ENUM else "app_help"
    selected_city = (parsed.city or "").strip() or state.selected_city

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
