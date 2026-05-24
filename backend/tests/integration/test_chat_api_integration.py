from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.agents.graph import build_graph
from src.controllers.api.chat import get_chatbot, get_current_user, get_db, router
from src.db.db import DB
from tests.integration.conftest import ChatApiIntegrationSettings

FAKE_HOUSEHOLD = {"id": "hh-001", "name": "Home", "invite_code": "abc123", "role": "owner"}


class FakeChatbot:
    def stream(self, messages):
        user_prompt = str(messages[-1].content).lower() if messages else ""

        if "madrid" in user_prompt or "suggest" in user_prompt:
            yield SimpleNamespace(content="Try a low-energy tapas spot followed by a short evening walk.")
        elif "help" in user_prompt:
            yield SimpleNamespace(content="Do you want app help, battery insights, or a plan suggestion?")
        elif "household" in user_prompt or "join" in user_prompt:
            yield SimpleNamespace(content="You can create or join a household from onboarding or settings.")
        elif "energy" in user_prompt or "battery" in user_prompt:
            yield SimpleNamespace(content="Your partner energy trend looks stable this week.")
        else:
            yield SimpleNamespace(content="Here are two low-energy options in Berlin.")


def _parse_sse(text: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    current_event = "message"
    current_data_parts: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if not line:
            if current_data_parts:
                events.append({"event": current_event, "data": "\n".join(current_data_parts)})
            current_event = "message"
            current_data_parts = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
            continue
        if line.startswith("data:"):
            current_data_parts.append(line.split(":", 1)[1].lstrip())

    if current_data_parts:
        events.append({"event": current_event, "data": "\n".join(current_data_parts)})

    return events


def _authorized_headers(integration_settings: ChatApiIntegrationSettings) -> dict[str, str]:
    if not integration_settings.use_real_auth:
        return {}
    return {"Authorization": f"Bearer {integration_settings.auth_token}"}


@pytest.fixture
def mock_db():
    db = MagicMock(spec=DB)
    db.get_household_by_user.return_value = FAKE_HOUSEHOLD
    return db


@pytest.fixture
def client(mock_db, integration_settings: ChatApiIntegrationSettings):
    app = FastAPI()
    app.include_router(router)
    app.state.chat_graph = build_graph()

    fake_user = SimpleNamespace(id=integration_settings.user_id)

    if not integration_settings.use_real_auth:
        app.dependency_overrides[get_current_user] = lambda: fake_user

    # Default mode is fully mocked for fast and deterministic debugging.
    # Set CAPPLE_TEST_USE_REAL_AUTH/DB/CHATBOT=true to opt in to real dependencies.
    if not integration_settings.use_real_db:
        app.dependency_overrides[get_db] = lambda: mock_db
    if not integration_settings.use_real_chatbot:
        app.dependency_overrides[get_chatbot] = lambda: FakeChatbot()

    return TestClient(app)


@pytest.fixture
def unauthorized_client(mock_db, integration_settings: ChatApiIntegrationSettings):
    app = FastAPI()
    app.include_router(router)
    app.state.chat_graph = build_graph()

    def _unauthorized_user():
        raise HTTPException(status_code=401, detail="Invalid token")

    if not integration_settings.use_real_auth:
        app.dependency_overrides[get_current_user] = _unauthorized_user
    if not integration_settings.use_real_db:
        app.dependency_overrides[get_db] = lambda: mock_db
    if not integration_settings.use_real_chatbot:
        app.dependency_overrides[get_chatbot] = lambda: FakeChatbot()

    return TestClient(app, raise_server_exceptions=False)


def test_chat_validation_invalid_history_returns_422(
    client: TestClient,
    integration_settings: ChatApiIntegrationSettings,
):
    response = client.post(
        "/api/chat",
        json={"message": "hello", "history": "not-a-list"},
        headers=_authorized_headers(integration_settings),
    )

    assert response.status_code == 422


def test_chat_with_invalid_token_rejected(unauthorized_client: TestClient):
    response = unauthorized_client.post(
        "/api/chat",
        json={"message": "hello", "history": []},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "message",
    [
        "How do I create or join a household in Capple?",
        "How is my partner's energy level this month?",
        "Suggest a low-energy date idea in Madrid tonight.",
        "What should we do tonight?",
        "help",
    ],
    ids=[
        "app-help",
        "battery-levels",
        "suggest-plan-with-city",
        "suggest-plan-missing-city",
        "ambiguous",
    ],
)
def test_chat_intent_flows_stream_valid_sse(
    client: TestClient,
    message: str,
    integration_settings: ChatApiIntegrationSettings,
):
    if not integration_settings.use_real_chatbot:
        pytest.skip("Set CAPPLE_TEST_USE_REAL_CHATBOT=true to run stream tests with the real graph.")

    response = client.post(
        "/api/chat",
        json={"message": message, "history": []},
        headers=_authorized_headers(integration_settings),
    )
    events = _parse_sse(response.text)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    assert any(event["event"] == "done" and "DONE" in event["data"] for event in events)


def test_chat_with_multi_turn_history_streams_valid_sse(
    client: TestClient,
    integration_settings: ChatApiIntegrationSettings,
):
    if not integration_settings.use_real_chatbot:
        pytest.skip("Set CAPPLE_TEST_USE_REAL_CHATBOT=true to run stream tests with the real graph.")

    history = [
        {"role": "user", "content": "What should we do tonight?"},
        {"role": "assistant", "content": "Which city should I use for suggestions?"},
    ]

    response = client.post(
        "/api/chat",
        json={
            "message": "Berlin, give me two options and keep it low-energy.",
            "history": history,
        },
        headers=_authorized_headers(integration_settings),
    )
    events = _parse_sse(response.text)

    assert response.status_code == 200
    assert any(event["event"] == "message" for event in events)
    assert any(event["event"] == "done" and "DONE" in event["data"] for event in events)
