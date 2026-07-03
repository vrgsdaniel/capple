from src.models.user import CurrentUser
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.users import get_current_user, get_user_service, router
from src.errors import ConflictException, ForbiddenException, NotFoundException
from src.service.users import UserService

FAKE_USER_ID = "00000000-0000-0000-0000-000000000111"
FAKE_USER = CurrentUser(id=FAKE_USER_ID)
FAKE_OTHER_USER_ID = "00000000-0000-0000-0000-000000000222"
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000001"
FAKE_HOUSEHOLD = {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home", "invite_code": "abc123"}


@pytest.fixture
def mock_service():
    svc = MagicMock(spec=UserService)
    for attr in [a for a in dir(UserService) if not a.startswith("_")]:
        setattr(svc, attr, AsyncMock())
    return svc


@pytest.fixture
def client(mock_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app)


class TestGetMe:
    def test_returns_current_user(self, client, mock_service):
        mock_service.get_user_name_by_id.return_value = {
            "user_name": "Alice",
            "avatar_url": "https://example.com/alice.png",
        }
        resp = client.get("/api/me")
        assert resp.status_code == 200
        assert resp.json() == {
            "id": FAKE_USER_ID,
            "name": "Alice",
            "avatar_url": "https://example.com/alice.png",
        }
        mock_service.get_user_name_by_id.assert_called_once_with(FAKE_USER_ID)

    def test_returns_404_when_profile_missing(self, client, mock_service):
        mock_service.get_user_name_by_id.return_value = None
        resp = client.get("/api/me")
        assert resp.status_code == 404

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.get_user_name_by_id.side_effect = RuntimeError("boom")
        resp = client.get("/api/me")
        assert resp.status_code == 500


class TestCreateHousehold:
    def test_creates_household(self, client, mock_service):
        mock_service.create_household.return_value = {
            "id": FAKE_HOUSEHOLD_ID,
            "name": "Test Home",
            "invite_code": "abc123",
        }
        resp = client.post("/api/households", json={"name": "Test Home"})
        assert resp.status_code == 201
        assert resp.json()["invite_code"] == "abc123"
        mock_service.create_household.assert_called_once_with(FAKE_USER_ID, "Test Home")

    def test_returns_409_when_already_in_household(self, client, mock_service):
        mock_service.create_household.side_effect = ConflictException("Already in a household")
        resp = client.post("/api/households", json={"name": "Test Home"})
        assert resp.status_code == 409
        mock_service.create_household.assert_called_once()

    def test_returns_422_for_empty_name(self, client, mock_service):
        resp = client.post("/api/households", json={"name": ""})
        assert resp.status_code == 422
        mock_service.create_household.assert_not_called()

    def test_returns_422_for_missing_name(self, client, mock_service):
        resp = client.post("/api/households", json={})
        assert resp.status_code == 422
        mock_service.create_household.assert_not_called()

    def test_returns_422_for_extra_fields(self, client, mock_service):
        resp = client.post("/api/households", json={"name": "Home", "extra": "bad"})
        assert resp.status_code == 422
        mock_service.create_household.assert_not_called()

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.create_household.side_effect = RuntimeError("boom")
        resp = client.post("/api/households", json={"name": "Test Home"})
        assert resp.status_code == 500


class TestJoinHousehold:
    def test_joins_household(self, client, mock_service):
        mock_service.join_household.return_value = {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home"}
        resp = client.post("/api/households/join", json={"invite_code": "abc123"})
        assert resp.status_code == 200
        assert resp.json()["id"] == FAKE_HOUSEHOLD_ID
        mock_service.join_household.assert_called_once_with(FAKE_USER_ID, "abc123")

    def test_returns_404_for_invalid_code(self, client, mock_service):
        mock_service.join_household.side_effect = NotFoundException("Invalid invite code")
        resp = client.post("/api/households/join", json={"invite_code": "bad"})
        assert resp.status_code == 404
        mock_service.join_household.assert_called_once()

    def test_returns_422_for_empty_invite_code(self, client, mock_service):
        resp = client.post("/api/households/join", json={"invite_code": ""})
        assert resp.status_code == 422
        mock_service.join_household.assert_not_called()

    def test_returns_422_for_missing_invite_code(self, client, mock_service):
        resp = client.post("/api/households/join", json={})
        assert resp.status_code == 422
        mock_service.join_household.assert_not_called()

    def test_returns_422_for_extra_fields(self, client, mock_service):
        resp = client.post("/api/households/join", json={"invite_code": "abc", "extra": "bad"})
        assert resp.status_code == 422
        mock_service.join_household.assert_not_called()

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.join_household.side_effect = RuntimeError("boom")
        resp = client.post("/api/households/join", json={"invite_code": "abc123"})
        assert resp.status_code == 500


class TestGetHouseholdMembers:
    def test_returns_members(self, client, mock_service):
        mock_service.get_household_members.return_value = {
            "me": {"id": FAKE_USER_ID, "name": "Alice", "avatar_url": None},
            "others": [{"id": FAKE_OTHER_USER_ID, "name": "Bob", "avatar_url": "https://example.com/bob.png"}],
        }
        resp = client.get("/api/household/members")
        assert resp.status_code == 200
        body = resp.json()
        assert body["me"]["id"] == FAKE_USER_ID
        assert body["me"]["name"] == "Alice"
        assert len(body["others"]) == 1
        mock_service.get_household_members.assert_called_once_with(FAKE_USER_ID)

    def test_returns_empty_others_for_solo_household(self, client, mock_service):
        mock_service.get_household_members.return_value = {
            "me": {"id": FAKE_USER_ID, "name": "Alice", "avatar_url": None},
            "others": [],
        }
        resp = client.get("/api/household/members")
        assert resp.status_code == 200
        assert resp.json()["others"] == []

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.get_household_members.side_effect = NotFoundException("No household")
        resp = client.get("/api/household/members")
        assert resp.status_code == 404

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.get_household_members.side_effect = RuntimeError("boom")
        resp = client.get("/api/household/members")
        assert resp.status_code == 500


class TestGetMyHousehold:
    def test_returns_household(self, client, mock_service):
        mock_service.get_user_household.return_value = {
            "id": FAKE_HOUSEHOLD_ID,
            "name": "Test Home",
            "invite_code": "abc123",
            "role": "owner",
        }
        resp = client.get("/api/households/me")
        assert resp.status_code == 200
        assert resp.json()["role"] == "owner"
        mock_service.get_user_household.assert_called_once_with(FAKE_USER_ID)

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.get_user_household.return_value = None
        resp = client.get("/api/households/me")
        assert resp.status_code == 404

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.get_user_household.side_effect = RuntimeError("boom")
        resp = client.get("/api/households/me")
        assert resp.status_code == 500


class TestLeaveHousehold:
    def test_member_can_leave(self, client, mock_service):
        mock_service.leave_household.return_value = None
        resp = client.delete("/api/households/me/leave")
        assert resp.status_code == 204
        mock_service.leave_household.assert_called_once_with(FAKE_USER_ID)

    def test_returns_404_when_not_in_household(self, client, mock_service):
        mock_service.leave_household.side_effect = NotFoundException("Not a member")
        resp = client.delete("/api/households/me/leave")
        assert resp.status_code == 404

    def test_returns_403_when_owner_tries_to_leave(self, client, mock_service):
        mock_service.leave_household.side_effect = ForbiddenException("Owners cannot leave")
        resp = client.delete("/api/households/me/leave")
        assert resp.status_code == 403

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.leave_household.side_effect = RuntimeError("boom")
        resp = client.delete("/api/households/me/leave")
        assert resp.status_code == 500


class TestDeleteHousehold:
    def test_owner_can_delete(self, client, mock_service):
        mock_service.delete_household.return_value = None
        resp = client.delete("/api/households/me")
        assert resp.status_code == 204
        mock_service.delete_household.assert_called_once_with(FAKE_USER_ID)

    def test_returns_404_when_not_in_household(self, client, mock_service):
        mock_service.delete_household.side_effect = NotFoundException("Not a member")
        resp = client.delete("/api/households/me")
        assert resp.status_code == 404

    def test_returns_403_when_member_tries_to_delete(self, client, mock_service):
        mock_service.delete_household.side_effect = ForbiddenException("Not the owner")
        resp = client.delete("/api/households/me")
        assert resp.status_code == 403

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.delete_household.side_effect = RuntimeError("boom")
        resp = client.delete("/api/households/me")
        assert resp.status_code == 500


class TestDeleteAccount:
    def test_can_delete_account(self, client, mock_service):
        mock_service.delete_account.return_value = None
        resp = client.delete("/api/me")
        assert resp.status_code == 204
        mock_service.delete_account.assert_called_once_with(FAKE_USER_ID)

    def test_returns_409_when_user_is_owner(self, client, mock_service):
        mock_service.delete_account.side_effect = ConflictException("Must delete household first")
        resp = client.delete("/api/me")
        assert resp.status_code == 409

    def test_returns_500_on_service_error(self, client, mock_service):
        mock_service.delete_account.side_effect = RuntimeError("boom")
        resp = client.delete("/api/me")
        assert resp.status_code == 500
