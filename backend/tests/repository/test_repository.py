from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repository.repository import Repository
from src.repository.store import Store

FAKE_USER_ID = "00000000-0000-0000-0000-000000000111"
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def repo():
    return Repository(MagicMock())


class TestGetHouseholdMembers:
    async def test_returns_all_members_for_users_household(self, repo):
        expected_members = [
            {"id": FAKE_USER_ID, "display_name": "Alice", "avatar_url": None},
            {
                "id": "00000000-0000-0000-0000-000000000222",
                "display_name": "Bob",
                "avatar_url": None,
            },
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


class TestSearchRecipes:
    async def test_uses_thin_fts_matcher_and_hydrates_candidates(self, repo):
        store = MagicMock()
        store.call_rpc = AsyncMock(
            return_value=[
                {
                    "recipe_id": "recipe-1",
                    "relevance": 0.8,
                }
            ]
        )
        store.find = AsyncMock(
            return_value=[
                {
                    "id": "recipe-1",
                    "name": "Pasta",
                    "ingredients": ["tomato"],
                }
            ]
        )
        repo.store = MagicMock(return_value=store)

        items = await repo.find_recipe_candidates("pasta")

        assert items == [
            {
                "id": "recipe-1",
                "name": "Pasta",
                "ingredients": ["tomato"],
                "relevance": 0.8,
            }
        ]
        repo.store.assert_called_once_with("recipes")
        store.call_rpc.assert_awaited_once_with(
            "match_recipes",
            {"p_text": "pasta"},
            limit=500,
            offset=0,
        )
        criteria = store.find.await_args.args[0]
        assert criteria._select == repo._RECIPE_SEARCH_COLUMNS
        assert criteria._filters[0].column == "id"
        assert criteria._filters[0].operator == "in_"
        assert criteria._filters[0].value == ["recipe-1"]

    async def test_no_text_pages_through_all_recipe_rows_without_rpc(self, repo):
        store = MagicMock()
        first_batch = [{"id": f"recipe-{index}"} for index in range(500)]
        store.find = AsyncMock(side_effect=[first_batch, [{"id": "recipe-500"}]])
        store.call_rpc = AsyncMock()
        repo.store = MagicMock(return_value=store)

        items = await repo.find_recipe_candidates()

        assert len(items) == 501
        assert all(item["relevance"] == 0.0 for item in items)
        store.call_rpc.assert_not_awaited()
        assert store.find.await_count == 2
        first_criteria = store.find.await_args_list[0].args[0]
        second_criteria = store.find.await_args_list[1].args[0]
        assert (first_criteria._limit, first_criteria._offset) == (500, 0)
        assert (second_criteria._limit, second_criteria._offset) == (500, 500)
        assert first_criteria._order_by == "id"
        assert first_criteria._ascending is True
        assert second_criteria._order_by == "id"

    async def test_text_with_no_matches_does_not_query_recipe_rows(self, repo):
        store = MagicMock()
        store.call_rpc = AsyncMock(return_value=[])
        store.find = AsyncMock()
        repo.store = MagicMock(return_value=store)

        assert await repo.find_recipe_candidates("missing") == []
        store.find.assert_not_awaited()

    async def test_find_all_recipes_pages_complete_rows_for_maintenance(self, repo):
        store = MagicMock()
        store.find = AsyncMock(return_value=[{"id": "recipe-1", "source_url": "https://example.com"}])
        repo.store = MagicMock(return_value=store)

        result = await repo.find_all_recipes()

        assert result == [{"id": "recipe-1", "source_url": "https://example.com"}]
        criteria = store.find.await_args.args[0]
        assert criteria._select == "*"
        assert (criteria._limit, criteria._offset) == (500, 0)
        assert criteria._order_by == "id"
        assert criteria._ascending is True


class TestStoreRpc:
    async def test_calls_paginated_function_in_store_schema(self):
        client = MagicMock()
        rpc_query = MagicMock()
        ranged_query = MagicMock()
        ranged_query.execute = AsyncMock(return_value=MagicMock(data=[{"recipe_id": "recipe-1"}]))
        rpc_query.range.return_value = ranged_query
        client.schema.return_value.rpc.return_value = rpc_query
        store = Store(client, "recipes", schema_name="app")

        result = await store.call_rpc("match_recipes", {"p_text": "pasta"}, limit=500, offset=500)

        assert result == [{"recipe_id": "recipe-1"}]
        client.schema.assert_called_once_with("app")
        client.schema.return_value.rpc.assert_called_once_with("match_recipes", {"p_text": "pasta"})
        rpc_query.range.assert_called_once_with(500, 999)
