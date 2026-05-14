from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.db.db import DB
from src.service.chat import ChatService


class FakeGraph:
    def __init__(self, outputs):
        self.outputs = outputs
        self.last_state = None

    def stream(self, state):
        self.last_state = state
        for output in self.outputs:
            yield output


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


class TestBuildInitialState:
    def test_builds_state_with_history_user_and_household(self, mock_db):
        fake_chatbot = SimpleNamespace(name="fake")
        fake_graph = FakeGraph([])
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        state = service._build_initial_state(
            message="latest message",
            history=[
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
        )

        assert state["user_id"] == "user-111"
        assert state["household_id"] == "hh-001"
        assert state["chatbot"] is fake_chatbot
        assert state["battery_context"] is None
        assert state["system_prompt"] == ""
        assert len(state["messages"]) == 3
        assert isinstance(state["messages"][0], HumanMessage)
        assert isinstance(state["messages"][1], AIMessage)
        assert isinstance(state["messages"][2], HumanMessage)
        assert state["messages"][2].content == "latest message"


class TestStreamResponse:
    def test_yields_only_chat_node_content(self, mock_db):
        fake_chatbot = SimpleNamespace(name="fake")
        outputs = [
            {"context_assembler": {"battery_context": {"total_entries": 3}}},
            {"chat_node": {"messages": [SimpleNamespace(content="first reply")]}},
            {"chat_node": {"messages": [SimpleNamespace(content="second reply")]}},
        ]
        fake_graph = FakeGraph(outputs)
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        result = list(service.stream_response("how are we", [{"role": "user", "content": "old"}]))

        assert result == ["first reply", "second reply"]
        assert fake_graph.last_state is not None
        assert fake_graph.last_state["user_id"] == "user-111"
        assert fake_graph.last_state["household_id"] == "hh-001"

    def test_ignores_empty_or_missing_message_content(self, mock_db):
        fake_chatbot = SimpleNamespace(name="fake")
        outputs = [
            {"chat_node": {"messages": []}},
            {"chat_node": {"messages": [SimpleNamespace(content="")]}},
            {"chat_node": {"messages": [SimpleNamespace(content="ok")]}},
            {"other_node": {"messages": [SimpleNamespace(content="ignored")]}},
        ]
        fake_graph = FakeGraph(outputs)
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        result = list(service.stream_response("new", []))

        assert result == ["ok"]
