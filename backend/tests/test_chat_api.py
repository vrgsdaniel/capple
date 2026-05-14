from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.chat import get_chatbot, get_current_user, get_db, router
from src.db.db import DB

FAKE_USER = SimpleNamespace(id="user-111")
FAKE_HOUSEHOLD = {"id": "hh-001", "name": "Home", "invite_code": "abc123", "role": "owner"}


class FakeGraph:
    def stream(self, _state):
        yield {"context_assembler": {"battery_context": {"total_entries": 2}}}
        yield {"chat_node": {"messages": [SimpleNamespace(content="hello from fake graph")]}}


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
    app.dependency_overrides[get_chatbot] = lambda: SimpleNamespace(name="fake-chatbot")

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
        app.dependency_overrides[get_chatbot] = lambda: SimpleNamespace(name="fake-chatbot")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/chat", json={"message": "hello", "history": []})

        assert resp.status_code == 500


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
