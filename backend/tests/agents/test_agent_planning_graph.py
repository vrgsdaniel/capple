from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agents.nodes.chat import parse_user_input_node, system_prompt_node


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


def test_parse_user_input_infers_planning_intent_and_city():
    state = {
        "messages": [HumanMessage(content="Can you suggest something to do in Madrid tonight?")],
        "chatbot": _FakeChatbot(
            {
                "intent": "suggest_plan",
                "city": "Madrid",
                "confidence": 0.91,
                "missing_requirements": [],
            }
        ),
    }

    result = parse_user_input_node(state)

    assert result["router_intent"] == "suggest_plan"
    assert result["selected_city"] == "Madrid"
    assert result["intent_confidence"] > 0.8
    assert result["missing_requirements"] == []


def test_parse_user_input_marks_missing_requirements_for_planning_without_city_or_consent():
    state = {
        "messages": [HumanMessage(content="What should we do this weekend?")],
        "chatbot": _FakeChatbot(
            {
                "intent": "suggest_plan",
                "city": None,
                "confidence": 0.84,
                "missing_requirements": ["city"],
            }
        ),
    }

    result = parse_user_input_node(state)

    assert result["router_intent"] == "suggest_plan"
    assert result["selected_city"] is None
    assert result["missing_requirements"] == ["city"]


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


def test_parse_user_input_greeting_bypasses_clarification():
    state = {
        "messages": [HumanMessage(content="hi")],
        "chatbot": _FakeChatbot(
            {
                "intent": "general_chat",
                "city": None,
                "confidence": 0.92,
                "missing_requirements": [],
            }
        ),
    }

    result = parse_user_input_node(state)

    assert result["router_intent"] == "general_chat"
    assert result["intent_confidence"] >= 0.9


def test_parse_user_input_infers_battery_levels_intent_for_energy_question():
    state = {
        "messages": [HumanMessage(content="How is my partner energy level today?")],
        "chatbot": _FakeChatbot(
            {
                "intent": "battery_levels",
                "city": None,
                "confidence": 0.93,
                "missing_requirements": [],
            }
        ),
    }

    result = parse_user_input_node(state)

    assert result["router_intent"] == "battery_levels"
    assert result["intent_confidence"] >= 0.9


def test_parse_user_input_defaults_to_app_help_without_chatbot():
    state = {
        "messages": [HumanMessage(content="How do I connect my account?")],
    }

    result = parse_user_input_node(state)

    assert result["router_intent"] == "app_help"
    assert result["intent_confidence"] == 0.0


def test_parse_user_input_sets_retry_needed_on_parser_failure():
    state = {
        "messages": [HumanMessage(content="Show me plans for tonight")],
        "chatbot": _FailingChatbot(),
    }

    result = parse_user_input_node(state)

    assert result["router_intent"] == "app_help"
    assert result["intent_confidence"] == 0.0
    assert result["parser_retry_needed"] is True


def test_system_prompt_requests_user_retry_on_parser_failure():
    state = {
        "parser_retry_needed": True,
        "intent_confidence": 0.0,
    }

    result = system_prompt_node(state)

    assert "retry their last message" in result["system_prompt"]
