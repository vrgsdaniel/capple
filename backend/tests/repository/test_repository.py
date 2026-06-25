from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repository.repository import Repository

FAKE_USER_ID = "00000000-0000-0000-0000-000000000111"
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def repo():
    return Repository(MagicMock())


class TestGetHouseholdMembers:
    async def test_returns_all_members_for_users_household(self, repo):
        expected_members = [
            {"id": FAKE_USER_ID, "display_name": "Alice", "avatar_url": None},
            {"id": "00000000-0000-0000-0000-000000000222", "display_name": "Bob", "avatar_url": None},
        ]
        store = MagicMock()
        store.find = AsyncMock(return_value=expected_members)
        repo.store = MagicMock(return_value=store)

        result = await repo.get_household_members(FAKE_USER_ID)

        assert result == expected_members
        repo.store.assert_called_once_with("household_member_profiles")

        criteria = store.find.await_args.args[0]
        assert criteria._select == "id, display_name, avatar_url"
        assert criteria._order_by == "created_at"
        assert criteria._ascending is True
        assert len(criteria._filters) == 1
        assert criteria._filters[0].column == "request_user_id"
        assert criteria._filters[0].operator == "eq"
        assert criteria._filters[0].value == FAKE_USER_ID

    async def test_returns_empty_list_when_view_has_no_rows(self, repo):
        store = MagicMock()
        store.find = AsyncMock(return_value=[])
        repo.store = MagicMock(return_value=store)

        result = await repo.get_household_members(FAKE_USER_ID)

        assert result == []
        repo.store.assert_called_once_with("household_member_profiles")
