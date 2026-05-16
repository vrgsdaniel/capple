from __future__ import annotations

import json
from json import JSONDecodeError

from langchain_core.messages import HumanMessage, SystemMessage
from src.agents.state import ChatState, ensure_chat_state
from src.settings import get_llm_settings
from src.utils.logger import logger as log

NODE_NAME = "router_agent"

_PLAN_HINTS = (
    "what should we do",
    "what to do",
    "suggest",
    "plan",
    "activity",
    "activities",
    "date idea",
    "tonight",
    "this weekend",
)

_NO_LOCATION_CONSENT_HINTS = (
    "do not use my location",
    "don't use my location",
    "without location",
    "no location consent",
    "location off",
)

_LOCATION_CONSENT_HINTS = (
    "use my location",
    "i am in",
    "i'm in",
    "near me",
    "around me",
    "berlin",
    "madrid",
)

_SUPPORTED_CITIES = ("Berlin", "Madrid")


def _last_user_text(state: ChatState) -> str:
    state_obj = ensure_chat_state(state)
    messages = state_obj.messages or []
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, dict):
        content = last.get("content", "")
    else:
        content = getattr(last, "content", "")
    return content.lower() if isinstance(content, str) else ""


def _detect_city(text: str) -> str | None:
    for city in _SUPPORTED_CITIES:
        if city.lower() in text:
            return city
    return None


def _rules_router(text: str) -> dict:
    intent = "suggest_plan" if any(hint in text for hint in _PLAN_HINTS) else "general_chat"
    if any(hint in text for hint in _NO_LOCATION_CONSENT_HINTS):
        location_consent = False
    else:
        location_consent = any(hint in text for hint in _LOCATION_CONSENT_HINTS)

    city = _detect_city(text)
    missing_requirements: list[str] = []
    workflow_plan: list[str] = []

    if intent == "suggest_plan":
        if city:
            workflow_plan = ["context_worker", "planner_worker"]
        elif location_consent:
            # For now no persisted profile location exists; ask city explicitly.
            missing_requirements.append("city")
        else:
            missing_requirements.append("location_or_city")

    return {
        "router_intent": intent,
        "location_consent": location_consent,
        "selected_city": city,
        "workflow_plan": workflow_plan,
        "missing_requirements": missing_requirements,
        "confidence": 1.0 if intent == "suggest_plan" else 0.5,
    }


def _llm_fallback_router(state_obj: ChatState, text: str) -> dict | None:
    if not state_obj.chatbot:
        return None

    system = SystemMessage(
        content=(
            "Route user intent for Capple. Return JSON only with keys: "
            "router_intent, location_consent, selected_city, confidence. "
            "router_intent must be suggest_plan or general_chat. "
            "selected_city must be Berlin, Madrid, or null."
        )
    )
    user = HumanMessage(content=text)

    messages = [system, user]

    # Explicit fallback model behavior is isolated here for maintainability.
    try:
        reply = state_obj.chatbot.llm.invoke(messages)
    except Exception:
        log.exception("Primary router LLM failed, trying explicit fallback model")
        try:
            from langchain_openai import ChatOpenAI

            settings = get_llm_settings()
            fallback_model = ChatOpenAI(
                model=settings.open_ai_model,
                api_key=settings.open_ai_api_key.get_secret_value(),
                temperature=0,
                max_retries=1,
            )
            reply = fallback_model.invoke(messages)
        except Exception:
            log.exception("Explicit fallback model failed; skipping LLM routing")
            return None

    content = getattr(reply, "content", "")
    if not isinstance(content, str):
        return None

    try:
        data = json.loads(content)
    except (JSONDecodeError, TypeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    intent = data.get("router_intent")
    city = data.get("selected_city")
    location_consent = bool(data.get("location_consent", False))
    confidence = float(data.get("confidence", 0.0)) if isinstance(data.get("confidence"), (int, float)) else 0.0
    if intent not in {"suggest_plan", "general_chat"}:
        return None
    if city not in {None, "Berlin", "Madrid"}:
        city = None

    workflow_plan = ["context_worker", "planner_worker"] if intent == "suggest_plan" and city else []
    missing = []
    if intent == "suggest_plan" and not city:
        missing = ["city"] if location_consent else ["location_or_city"]

    return {
        "router_intent": intent,
        "location_consent": location_consent,
        "selected_city": city,
        "workflow_plan": workflow_plan,
        "missing_requirements": missing,
        "confidence": confidence,
    }


def router_node(state: ChatState) -> dict:
    """Hybrid router: deterministic rules first, LLM fallback when uncertain."""
    state_obj = ensure_chat_state(state)
    text = _last_user_text(state)
    rules = _rules_router(text)
    if rules["confidence"] >= 0.8:
        return {
            "router_intent": rules["router_intent"],
            "location_consent": rules["location_consent"],
            "selected_city": rules["selected_city"],
            "workflow_plan": rules["workflow_plan"],
            "missing_requirements": rules["missing_requirements"],
        }

    llm_route = _llm_fallback_router(state_obj, text)
    if llm_route:
        return {
            "router_intent": llm_route["router_intent"],
            "location_consent": llm_route["location_consent"],
            "selected_city": llm_route["selected_city"],
            "workflow_plan": llm_route["workflow_plan"],
            "missing_requirements": llm_route["missing_requirements"],
        }

    return {
        "router_intent": rules["router_intent"],
        "location_consent": rules["location_consent"],
        "selected_city": rules["selected_city"],
        "workflow_plan": rules["workflow_plan"],
        "missing_requirements": rules["missing_requirements"],
    }
