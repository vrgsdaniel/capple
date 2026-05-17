from types import SimpleNamespace
from unittest.mock import MagicMock
from json import JSONDecodeError

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.chat import get_chatbot, get_current_user, get_db, router
from src.db.db import DB

FAKE_USER = SimpleNamespace(id="user-111")
FAKE_HOUSEHOLD = {"id": "hh-001", "name": "Home", "invite_code": "abc123", "role": "owner"}


class FakeGraph:
    def invoke(self, state, config=None):
        assert isinstance(config, dict)
        assert "db_client" in config
        return {**state, "system_prompt": "prep prompt", "battery_context": {"total_entries": 2}}


class FakeGraphFailBeforeFirstChunk:
    def invoke(self, _state, config=None):
        assert isinstance(config, dict)
        assert "db_client" in config
        raise ValueError("{'error': 'missing llm env vars'}")


class FakeChatbot:
    def __init__(self, chunks=None, error_after_first=False, raise_json_error_after_chunks=False):
        self._chunks = chunks or ["hello from fake graph"]
        self._error_after_first = error_after_first
        self._raise_json_error_after_chunks = raise_json_error_after_chunks

    def stream(self, _messages):
        for idx, chunk in enumerate(self._chunks):
            if self._error_after_first and idx > 0:
                raise ValueError("{'error': 'missing llm env vars'}")
            yield SimpleNamespace(content=chunk)
        if self._raise_json_error_after_chunks:
            raise JSONDecodeError("Expecting value", "", 0)


@pytest.fixture
def mock_db():
    db = MagicMock(spec=DB)
    db.get_household_by_user.return_value = FAKE_HOUSEHOLD
    return db


@pytest.fixture
def client(mock_db):
    app = FastAPI()
    app.include_router(router)
    app.state.chat_graph = FakeGraph()

    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_chatbot] = lambda: FakeChatbot()

    return TestClient(app)


class TestChatApi:
    def test_streams_sse_from_injected_graph(self, client):
        resp = client.post("/api/chat", json={"message": "hey", "history": []})

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert 'event: message\ndata: "hello from fake graph"' in resp.text
        assert 'event: done\ndata: "[DONE]"' in resp.text

    def test_get_chat_service_uses_user_household_via_di(self, client, mock_db):
        resp = client.post("/api/chat", json={"message": "hello", "history": []})

        assert resp.status_code == 200
        mock_db.get_household_by_user.assert_called_once_with("user-111")

    def test_returns_500_when_user_has_no_household_in_dependency(self, mock_db):
        mock_db.get_household_by_user.return_value = None

        app = FastAPI()
        app.include_router(router)
        app.state.chat_graph = FakeGraph()
        app.dependency_overrides[get_current_user] = lambda: FAKE_USER
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_chatbot] = lambda: FakeChatbot()

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/chat", json={"message": "hello", "history": []})

        assert resp.status_code == 500

    def test_returns_500_when_stream_setup_fails(self, mock_db):
        app = FastAPI()
        app.include_router(router)
        app.state.chat_graph = FakeGraphFailBeforeFirstChunk()
        app.dependency_overrides[get_current_user] = lambda: FAKE_USER
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_chatbot] = lambda: FakeChatbot()

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/chat", json={"message": "hello", "history": []})

        assert resp.status_code == 200
        assert 'event: error\ndata: "Something went wrong. Please try again."' in resp.text

    def test_emits_error_event_when_stream_fails_after_first_chunk(self, mock_db):
        app = FastAPI()
        app.include_router(router)
        app.state.chat_graph = FakeGraph()
        app.dependency_overrides[get_current_user] = lambda: FAKE_USER
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_chatbot] = lambda: FakeChatbot(
            chunks=["hello before error", "ignored"], error_after_first=True
        )

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/chat", json={"message": "hello", "history": []})

        assert resp.status_code == 200
        assert 'event: message\ndata: "hello before error"' in resp.text
        assert 'event: error\ndata: "Something went wrong. Please try again."' in resp.text

    def test_finishes_cleanly_when_terminal_json_decode_error_happens_after_chunks(self, mock_db):
        app = FastAPI()
        app.include_router(router)
        app.state.chat_graph = FakeGraph()
        app.dependency_overrides[get_current_user] = lambda: FAKE_USER
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_chatbot] = lambda: FakeChatbot(
            chunks=["hello", " world"],
            raise_json_error_after_chunks=True,
        )

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/chat", json={"message": "hello", "history": []})

        assert resp.status_code == 200
        assert 'event: message\ndata: "hello"' in resp.text
        assert 'event: message\ndata: " world"' in resp.text
        assert 'event: done\ndata: "[DONE]"' in resp.text
        assert 'event: error\ndata: "Something went wrong. Please try again."' not in resp.text


class TestChatApiValidation:
    def test_returns_422_when_message_missing(self, client):
        resp = client.post("/api/chat", json={"history": []})

        assert resp.status_code == 422

    def test_returns_422_when_history_item_is_invalid(self, client):
        resp = client.post("/api/chat", json={"message": "hello", "history": [{"role": "user"}]})

        assert resp.status_code == 422

    def test_returns_422_when_history_is_not_a_list(self, client):
        resp = client.post("/api/chat", json={"message": "hello", "history": "not-a-list"})

        assert resp.status_code == 422

    def test_allows_empty_message_with_current_schema(self, client):
        resp = client.post("/api/chat", json={"message": "", "history": []})

        assert resp.status_code == 200
        assert 'event: done\ndata: "[DONE]"' in resp.text
