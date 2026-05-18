from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class BatteryContext(BaseModel):
    total_entries: int = 0
    your_entries: int = 0
    partner_entries: int = 0
    your_avg: float | None = None
    partner_avg: float | None = None
    your_trend: str = "insufficient_data"
    partner_trend: str = "insufficient_data"
    days_since_your_last_log: int | None = None
    days_since_partner_last_log: int | None = None


class DateTimeContext(BaseModel):
    utc_iso: str = ""
    local_iso: str = ""
    city: str = ""


class WeatherContext(BaseModel):
    city: str = ""
    temperature: float | None = None
    precipitation_probability: int | None = None
    weather_label: str = "unavailable"


class CityEvent(BaseModel):
    city: str = ""
    title: str = ""
    category: str = ""
    start_iso: str = ""
    source: str = ""


class SuggestedPlan(BaseModel):
    title: str = ""
    city: str = ""
    rationale: str = ""
    score: int = 0
    recommended_for: str = "couple"
    best_time: str = ""


class ChatState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: list[Any] = Field(default_factory=list)
    household_id: str = ""
    user_id: str = ""
    router_intent: str = "general_chat"
    location_consent: bool = False
    selected_city: str | None = None
    workflow_plan: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    battery_context: BatteryContext | None = None
    datetime_context: DateTimeContext | None = None
    weather_context: dict[str, WeatherContext] = Field(default_factory=dict)
    city_events: dict[str, list[CityEvent]] = Field(default_factory=dict)
    ranked_plans: list[SuggestedPlan] = Field(default_factory=list)
    chatbot: Any | None = None
    system_prompt: str = ""


def build_default_chat_state_model() -> ChatState:
    """Return a default-initialized ChatState model."""
    return ChatState()


def ensure_chat_state(state: ChatState | dict) -> ChatState:
    if isinstance(state, ChatState):
        return state
    return ChatState.model_validate(state)
