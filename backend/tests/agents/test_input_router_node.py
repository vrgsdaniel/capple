from unittest.mock import MagicMock

import pytest
from langchain_core.messages import HumanMessage

from src.agents.nodes.input_router import parse_user_input_node
from src.agents.state import ChatState


def _build_chatbot_mock(invoke_result=None, invoke_side_effect=None):
    chatbot = MagicMock()
    structured_llm = MagicMock()
    if invoke_side_effect is not None:
        structured_llm.invoke.side_effect = invoke_side_effect
    else:
        structured_llm.invoke.return_value = invoke_result
    chatbot.llm.with_structured_output.return_value = structured_llm
    return chatbot


@pytest.mark.parametrize(
    "invoke_result, invoke_side_effect, expected",
    [
        (
            {
                "intent": "suggest_plan",
                "city": " Madrid ",
                "confidence": 0.91,
                "missing_requirements": [],
            },
            None,
            {
                "router_intent": "suggest_plan",
                "intent_confidence": 0.91,
                "parser_retry_needed": False,
                "selected_city": "Madrid",
                "missing_requirements": [],
            },
        ),
        (
            {
                "intent": "suggest_plan",
                "city": None,
                "confidence": 0.84,
                "missing_requirements": [],
            },
            None,
            {
                "router_intent": "suggest_plan",
                "intent_confidence": 0.84,
                "parser_retry_needed": False,
                "selected_city": None,
                "missing_requirements": ["city"],
            },
        ),
        (
            {
                "intent": "suggest_plan",
                "city": None,
                "confidence": 2.0,
                "missing_requirements": ["city", "timezone"],
            },
            None,
            {
                "router_intent": "suggest_plan",
                "intent_confidence": 1.0,
                "parser_retry_needed": False,
                "selected_city": None,
                "missing_requirements": ["city"],
            },
        ),
        (
            None,
            RuntimeError("parse failure"),
            {
                "router_intent": "app_help",
                "intent_confidence": 0.0,
                "parser_retry_needed": True,
                "selected_city": None,
                "missing_requirements": [],
            },
        ),
    ],
    ids=[
        "planning-intent-with-explicit-city",
        "planning-intent-adds-missing-city",
        "planning-intent-clamps-confidence-and-filters-missing-requirements",
        "llm-parser-failure-sets-retry-flag",
    ],
)
def test_parse_user_input_node(
    invoke_result,
    invoke_side_effect,
    expected,
):
    chatbot = _build_chatbot_mock(
        invoke_result=invoke_result,
        invoke_side_effect=invoke_side_effect,
    )
    state = ChatState(
        messages=[HumanMessage(content="Can you help me plan tonight?")],
        chatbot=chatbot,
    )

    result = parse_user_input_node(state)

    assert result == expected
    chatbot.llm.with_structured_output.assert_called_once()
