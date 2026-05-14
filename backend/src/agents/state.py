from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from src.agents.llm.chatbot import Chatbot


# TODO: can we use pydantic instead of TypedDict for better validation and defaults? Need to check langgraph compatibility first.
class BatteryContext(TypedDict):
    total_entries: int
    your_entries: int
    partner_entries: int
    your_avg: float | None
    partner_avg: float | None
    your_trend: str  # "improving" | "declining" | "stable" | "insufficient_data"
    partner_trend: str
    days_since_your_last_log: int | None
    days_since_partner_last_log: int | None


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    household_id: str
    user_id: str
    battery_context: BatteryContext | None
    chatbot: Chatbot | None
    system_prompt: str
