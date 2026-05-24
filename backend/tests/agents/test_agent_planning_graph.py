from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agents.nodes.chat import system_prompt_node


class _FakeStructuredLLM:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class _FakeLLM:
    def __init__(self, result):
        self._result = result

    def with_structured_output(self, _schema: type[BaseModel]):
        return _FakeStructuredLLM(self._result)


class _FakeChatbot:
    def __init__(self, result):
        self.llm = _FakeLLM(result)


class _FailingStructuredLLM:
    def invoke(self, _messages):
        raise RuntimeError("parse failure")


class _FailingLLM:
    def with_structured_output(self, _schema: type[BaseModel]):
        return _FailingStructuredLLM()


class _FailingChatbot:
    def __init__(self):
        self.llm = _FailingLLM()


def test_system_prompt_includes_ranked_plans_for_planning():
    state = {
        "router_intent": "suggest_plan",
        "intent_confidence": 0.9,
        "selected_city": "Berlin",
        "battery_context": {"your_avg": 60, "partner_avg": 55},
        "datetime_context": {
            "utc_iso": "2026-05-16T12:00:00+00:00",
            "berlin_local_iso": "2026-05-16T14:00:00+02:00",
            "madrid_local_iso": "2026-05-16T14:00:00+02:00",
        },
        "weather_context": {
            "Berlin": {
                "weather_label": "clear",
                "temperature": 22,
                "precipitation_probability": 10,
            },
            "Madrid": {
                "weather_label": "clear",
                "temperature": 24,
                "precipitation_probability": 0,
            },
        },
        "city_events": {
            "Berlin": [{"title": "A"}],
            "Madrid": [{"title": "B"}],
        },
        "ranked_plans": [
            {
                "title": "Tempelhofer Feld sunset walk",
                "city": "Berlin",
                "score": 82,
                "rationale": "Good weather and social battery alignment.",
                "recommended_for": "couple",
                "best_time": "2026-05-16T19:00:00+02:00",
            }
        ],
    }

    result = system_prompt_node(state)

    assert "Top ranked suggestions" in result["system_prompt"]
    assert "Tempelhofer Feld sunset walk" in result["system_prompt"]

    state = {
        "router_intent": "suggest_plan",
        "intent_confidence": 0.9,
        "selected_city": "Berlin",
    }

    result = system_prompt_node(state)

    assert "Top ranked suggestions" in result["system_prompt"]
    assert "Tempelhofer Feld sunset walk" in result["system_prompt"]


def test_system_prompt_for_general_chat_uses_battery_context_prompt():
    state = {
        "router_intent": "general_chat",
        "intent_confidence": 0.9,
        "selected_city": None,
        "battery_context": {
            "your_entries": 2,
            "partner_entries": 3,
            "your_avg": 70,
            "partner_avg": 60,
            "your_trend": "stable",
            "partner_trend": "up",
            "days_since_your_last_log": 1,
            "days_since_partner_last_log": 2,
            "total_entries": 5,
        },
    }

    result = system_prompt_node(state)

    assert "household battery data" in result["system_prompt"]


def test_system_prompt_low_confidence_asks_for_clarification():
    state = {
        "router_intent": "general_chat",
        "intent_confidence": 0.2,
        "messages": [HumanMessage(content="help")],
    }

    result = system_prompt_node(state)

    assert "intent is ambiguous" in result["system_prompt"]
    assert "clarifying question" in result["system_prompt"]


def test_system_prompt_requests_user_retry_on_parser_failure():
    state = {
        "parser_retry_needed": True,
        "intent_confidence": 0.0,
    }

    result = system_prompt_node(state)

    assert "retry their last message" in result["system_prompt"]
