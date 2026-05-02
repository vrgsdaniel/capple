from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.controllers.api.users import get_current_user, get_user_service, router
from src.db.db import DB
from src.service.users import UserService

FAKE_USER = SimpleNamespace(id="user-111")
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000001"
FAKE_HOUSEHOLD = {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home", "invite_code": "abc123"}


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


@pytest.fixture
def mock_user_service(mock_db):
    return UserService(mock_db)


@pytest.fixture
def client(mock_user_service):
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app)


class TestGetMe:
    def test_returns_current_user(self, client, mock_db):
        mock_db.get_profile_by_id.return_value = {
            "display_name": "Alice",
            "avatar_url": "https://example.com/alice.png",
        }
        resp = client.get("/api/me")
        assert resp.status_code == 200
        assert resp.json() == {
            "id": "user-111",
            "name": "Alice",
            "avatar_url": "https://example.com/alice.png",
        }

    def test_returns_404_when_profile_missing(self, client, mock_db):
        mock_db.get_profile_by_id.return_value = None
        resp = client.get("/api/me")
        assert resp.status_code == 404


class TestCreateHousehold:
    def test_creates_household(self, client, mock_db):
        mock_db.get_household_by_user.return_value = None
        mock_db.create_household.return_value = FAKE_HOUSEHOLD
        mock_db.add_member_to_household.return_value = {}

        resp = client.post("/api/households", json={"name": "Test Home"})
        assert resp.status_code == 201
        assert resp.json()["invite_code"] == "abc123"

    def test_returns_500_on_db_error(self, client, mock_db):
        mock_db.get_household_by_user.return_value = None
        mock_db.create_household.side_effect = RuntimeError("boom")
        resp = client.post("/api/households", json={"name": "Test Home"})
        assert resp.status_code == 500


class TestJoinHousehold:
    def test_joins_household(self, client, mock_db):
        mock_db.get_household_by_user.return_value = None
        mock_db.get_household_by_code.return_value = FAKE_HOUSEHOLD
        mock_db.add_member_to_household.return_value = {}

        resp = client.post("/api/households/join", json={"invite_code": "abc123"})
        assert resp.status_code == 200
        assert resp.json()["id"] == FAKE_HOUSEHOLD_ID

    def test_returns_404_for_invalid_code(self, client, mock_db):
        mock_db.get_household_by_user.return_value = None
        mock_db.get_household_by_code.return_value = None
        resp = client.post("/api/households/join", json={"invite_code": "bad"})
        assert resp.status_code == 404


class TestGetMyHousehold:
    def test_returns_household(self, client, mock_db):
        mock_db.get_household_by_user.return_value = {
            "id": FAKE_HOUSEHOLD_ID,
            "name": "Test Home",
            "invite_code": "abc123",
            "role": "owner",
        }
        resp = client.get("/api/households/me")
        assert resp.status_code == 200
        assert resp.json()["role"] == "owner"

    def test_returns_404_when_no_household(self, client, mock_db):
        mock_db.get_household_by_user.return_value = None
        resp = client.get("/api/households/me")
        assert resp.status_code == 404
