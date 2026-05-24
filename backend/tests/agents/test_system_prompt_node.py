from langchain_core.messages import HumanMessage

from src.agents.nodes.system_prompt import system_prompt_node


def test_system_prompt_includes_ranked_plans_for_planning():
    state = {
        "router_intent": "suggest_plan",
        "intent_confidence": 0.9,
        "selected_city": "Berlin",
    }

    result = system_prompt_node(state)

    assert "provide a ranked, practical plan" in result["system_prompt"]


def test_system_prompt_for_general_chat_uses_battery_context_prompt():
    state = {
        "router_intent": "general_chat",
        "intent_confidence": 0.9,
        "selected_city": None,
    }

    result = system_prompt_node(state)

    assert "You are Capple, the assistant for a couples' household app." in result["system_prompt"]


def test_system_prompt_for_battery_levels_requires_battery_tool_usage():
    state = {
        "router_intent": "battery_levels",
        "intent_confidence": 0.95,
    }

    result = system_prompt_node(state)

    assert "Use the battery context tool before answering" in result["system_prompt"]


def test_system_prompt_for_app_help_uses_app_help_behavior():
    state = {
        "router_intent": "app_help",
        "intent_confidence": 0.95,
    }

    result = system_prompt_node(state)

    assert "app usage or troubleshooting" in result["system_prompt"]


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
