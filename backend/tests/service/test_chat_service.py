from types import SimpleNamespace
from unittest.mock import MagicMock
from json import JSONDecodeError

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.db.db import DB
from src.service.chat import ChatService


class FakeGraph:
    def __init__(self, prepared_state=None):
        self.prepared_state = prepared_state or {}
        self.last_state = None
        self.last_context = None

    def invoke(self, state, context=None):
        self.last_state = state
        self.last_context = context
        return {**state, **self.prepared_state}


class FakeChatbot:
    def __init__(self, chunks=None, raise_json_error_after_chunks=False):
        self._chunks = chunks or []
        self._raise_json_error_after_chunks = raise_json_error_after_chunks
        self.stream_calls = 0

    def stream(self, _messages):
        self.stream_calls += 1
        for chunk in self._chunks:
            yield SimpleNamespace(content=chunk)
        if self._raise_json_error_after_chunks:
            raise JSONDecodeError("Expecting value", "", 0)


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


class TestBuildInitialState:
    def test_builds_state_with_history_user_and_household(self, mock_db):
        fake_chatbot = FakeChatbot(chunks=[])
        fake_graph = FakeGraph()
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
    def test_prefers_graph_assistant_message_when_available(self, mock_db):
        fake_chatbot = FakeChatbot(chunks=["fallback should not be used"])
        fake_graph = FakeGraph(
            prepared_state={
                "messages": [
                    HumanMessage(content="how is my partner doing?"),
                    AIMessage(content="Partner trend is declining and last log was 11 days ago."),
                ]
            }
        )
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        result = list(service.stream_response("how is my partner doing?", []))

        assert result == ["Partner trend is declining and last log was 11 days ago."]
        assert fake_chatbot.stream_calls == 0

    def test_yields_streamed_chunks_from_chatbot(self, mock_db):
        fake_chatbot = FakeChatbot(chunks=["first ", "reply", " second", " reply"])
        fake_graph = FakeGraph(prepared_state={"system_prompt": "prep prompt"})
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        result = list(service.stream_response("how are we", [{"role": "user", "content": "old"}]))

        assert result == ["first ", "reply", " second", " reply"]
        assert fake_graph.last_state is not None
        assert fake_graph.last_state["user_id"] == "user-111"
        assert fake_graph.last_state["household_id"] == "hh-001"
        assert fake_graph.last_context is not None
        assert fake_graph.last_context.db_client is mock_db

    def test_ignores_empty_stream_chunks(self, mock_db):
        fake_chatbot = FakeChatbot(chunks=["", "ok"])
        fake_graph = FakeGraph(prepared_state={"system_prompt": "prep prompt"})
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        result = list(service.stream_response("new", []))

        assert result == ["ok"]

    def test_tolerates_terminal_json_decode_error_after_valid_chunks(self, mock_db):
        fake_chatbot = FakeChatbot(chunks=["partial", " reply"], raise_json_error_after_chunks=True)
        fake_graph = FakeGraph(prepared_state={"system_prompt": "prep prompt"})
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        result = list(service.stream_response("new", []))

        assert result == ["partial", " reply"]

    def test_raises_json_decode_error_when_no_chunk_was_emitted(self, mock_db):
        fake_chatbot = FakeChatbot(chunks=[], raise_json_error_after_chunks=True)
        fake_graph = FakeGraph(prepared_state={"system_prompt": "prep prompt"})
        service = ChatService("user-111", "hh-001", mock_db, fake_chatbot, fake_graph)

        with pytest.raises(JSONDecodeError):
            list(service.stream_response("new", []))
