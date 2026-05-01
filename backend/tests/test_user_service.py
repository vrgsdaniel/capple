from unittest.mock import MagicMock

import pytest

from src.db.db import DB
from src.errors import NotFoundException
from src.service.users import UserService

FAKE_USER_ID = "user-111"
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000001"
FAKE_HOUSEHOLD = {
    "id": FAKE_HOUSEHOLD_ID,
    "name": "Test Home",
    "invite_code": "abc123",
    "created_by": FAKE_USER_ID,
}


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


@pytest.fixture
def user_service(mock_db):
    return UserService(mock_db)


class TestGetUserNameById:
    def test_returns_user_when_found(self, user_service, mock_db):
        mock_db.get_profile_by_id.return_value = {
            "display_name": "Alice",
            "avatar_url": "https://example.com/alice.png",
        }
        result = user_service.get_user_name_by_id(FAKE_USER_ID)
        assert result == {"user_name": "Alice", "avatar_url": "https://example.com/alice.png"}
        mock_db.get_profile_by_id.assert_called_once_with(FAKE_USER_ID)

    def test_returns_none_when_not_found(self, user_service, mock_db):
        mock_db.get_profile_by_id.return_value = None
        assert user_service.get_user_name_by_id(FAKE_USER_ID) is None


class TestCreateHousehold:
    def test_creates_household_and_adds_owner(self, user_service, mock_db):
        mock_db.create_household.return_value = FAKE_HOUSEHOLD
        mock_db.add_member_to_household.return_value = {}

        result = user_service.create_household(FAKE_USER_ID, "Test Home")

        assert result == {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home", "invite_code": "abc123"}
        mock_db.create_household.assert_called_once_with("Test Home", created_by=FAKE_USER_ID)
        mock_db.add_member_to_household.assert_called_once_with(FAKE_HOUSEHOLD_ID, FAKE_USER_ID, role="owner")


class TestJoinHousehold:
    def test_joins_existing_household(self, user_service, mock_db):
        mock_db.get_household_by_code.return_value = FAKE_HOUSEHOLD
        mock_db.add_member_to_household.return_value = {}

        result = user_service.join_household(FAKE_USER_ID, "abc123")

        assert result == {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home"}
        mock_db.add_member_to_household.assert_called_once_with(FAKE_HOUSEHOLD_ID, FAKE_USER_ID)

    def test_raises_not_found_for_invalid_code(self, user_service, mock_db):
        mock_db.get_household_by_code.return_value = None
        with pytest.raises(NotFoundException):
            user_service.join_household(FAKE_USER_ID, "bad-code")


class TestGetUserHousehold:
    def test_returns_household_when_member(self, user_service, mock_db):
        mock_db.get_household_by_user.return_value = {
            "id": FAKE_HOUSEHOLD_ID,
            "name": "Test Home",
            "invite_code": "abc123",
            "role": "owner",
        }
        result = user_service.get_user_household(FAKE_USER_ID)
        assert result == {
            "id": FAKE_HOUSEHOLD_ID,
            "name": "Test Home",
            "invite_code": "abc123",
            "role": "owner",
        }

    def test_returns_none_when_not_member(self, user_service, mock_db):
        mock_db.get_household_by_user.return_value = None
        assert user_service.get_user_household(FAKE_USER_ID) is None
