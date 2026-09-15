from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.repository.repository import Repository
from src.repository.store import Store

FAKE_USER_ID = "00000000-0000-0000-0000-000000000111"
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def repo():
    return Repository(MagicMock())


def stub_store_find(repo: Repository, rows: list[dict]) -> MagicMock:
    """Make `repo.store(...).find(...)` return *rows* regardless of the criteria passed in.

    Returns the underlying store mock so callers can still assert against it
    (e.g. `store.find.await_args`) when the test needs to inspect the criteria used.
    """
    store = MagicMock()
    store.find = AsyncMock(return_value=rows)
    repo.store = MagicMock(return_value=store)
    return store


class TestFindEventsInRange:
    async def test_returns_events_scoped_to_household_and_range(self, repo):
        expected_events = [{"id": "event-1", "title": "Dentist", "event_date": "2026-09-20"}]
        store = stub_store_find(repo, expected_events)

        result = await repo.find_events_in_range(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")

        assert result == expected_events
        repo.store.assert_called_once_with("calendar_events")

        criteria = store.find.await_args.args[0]
        assert criteria._order_by == "event_date"
        assert criteria._ascending is True
        assert criteria._limit == Repository.CALENDAR_EVENT_LIMIT
        assert len(criteria._filters) == 3
        assert (criteria._filters[0].column, criteria._filters[0].operator, criteria._filters[0].value) == (
            "household_id",
            "eq",
            FAKE_HOUSEHOLD_ID,
        )
        assert (criteria._filters[1].column, criteria._filters[1].operator, criteria._filters[1].value) == (
            "event_date",
            "gte",
            "2026-09-01",
        )
        assert (criteria._filters[2].column, criteria._filters[2].operator, criteria._filters[2].value) == (
            "event_date",
            "lte",
            "2026-09-30",
        )

    async def test_warns_when_results_hit_the_row_cap(self, repo):
        stub_store_find(repo, [{"id": "e"}] * Repository.CALENDAR_EVENT_LIMIT)

        with patch("src.repository.repository.log") as mock_log:
            await repo.find_events_in_range(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")

        mock_log.warning.assert_called_once()

    async def test_does_not_warn_when_results_are_under_the_cap(self, repo):
        stub_store_find(repo, [{"id": "e"}])

        with patch("src.repository.repository.log") as mock_log:
            await repo.find_events_in_range(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")

        mock_log.warning.assert_not_called()


class TestFindBirthdaysByHousehold:
    async def test_returns_birthdays_scoped_to_household(self, repo):
        expected_birthdays = [
            {"id": "bday-1", "person_name": "Ada", "birth_month": 9, "birth_day": 20, "birth_year": 1990}
        ]
        store = stub_store_find(repo, expected_birthdays)

        result = await repo.find_birthdays_by_household(FAKE_HOUSEHOLD_ID)

        assert result == expected_birthdays
        repo.store.assert_called_once_with("calendar_birthdays")

        criteria = store.find.await_args.args[0]
        assert criteria._order_by == "person_name"
        assert criteria._ascending is True
        assert criteria._limit == Repository.CALENDAR_BIRTHDAY_LIMIT
        assert len(criteria._filters) == 1
        assert (criteria._filters[0].column, criteria._filters[0].operator, criteria._filters[0].value) == (
            "household_id",
            "eq",
            FAKE_HOUSEHOLD_ID,
        )

    async def test_warns_when_results_hit_the_row_cap(self, repo):
        stub_store_find(repo, [{"id": "b"}] * Repository.CALENDAR_BIRTHDAY_LIMIT)

        with patch("src.repository.repository.log") as mock_log:
            await repo.find_birthdays_by_household(FAKE_HOUSEHOLD_ID)

        mock_log.warning.assert_called_once()

    async def test_does_not_warn_when_results_are_under_the_cap(self, repo):
        stub_store_find(repo, [{"id": "b"}])

        with patch("src.repository.repository.log") as mock_log:
            await repo.find_birthdays_by_household(FAKE_HOUSEHOLD_ID)

        mock_log.warning.assert_not_called()


class TestFindActiveTaskDots:
    async def test_returns_active_tasks_due_in_range(self, repo):
        expected_tasks = [{"id": "task-1", "name": "Trash", "due_date": "2026-09-14"}]
        store = stub_store_find(repo, expected_tasks)

        result = await repo.find_active_task_dots(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")

        assert result == expected_tasks
        repo.store.assert_called_once_with("tasks")

        criteria = store.find.await_args.args[0]
        assert criteria._select == "id, name, due_date"
        assert criteria._limit == Repository.CALENDAR_CHORE_DOT_LIMIT
        assert len(criteria._filters) == 4
        assert (criteria._filters[0].column, criteria._filters[0].operator, criteria._filters[0].value) == (
            "household_id",
            "eq",
            FAKE_HOUSEHOLD_ID,
        )
        assert (criteria._filters[1].column, criteria._filters[1].operator, criteria._filters[1].value) == (
            "completed_at",
            "is_",
            None,
        )
        assert (criteria._filters[2].column, criteria._filters[2].operator, criteria._filters[2].value) == (
            "due_date",
            "gte",
            "2026-09-01",
        )
        assert (criteria._filters[3].column, criteria._filters[3].operator, criteria._filters[3].value) == (
            "due_date",
            "lte",
            "2026-09-30",
        )

    async def test_warns_when_results_hit_the_row_cap(self, repo):
        stub_store_find(repo, [{"id": "t"}] * Repository.CALENDAR_CHORE_DOT_LIMIT)

        with patch("src.repository.repository.log") as mock_log:
            await repo.find_active_task_dots(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")

        mock_log.warning.assert_called_once()

    async def test_does_not_warn_when_results_are_under_the_cap(self, repo):
        stub_store_find(repo, [{"id": "t"}])

        with patch("src.repository.repository.log") as mock_log:
            await repo.find_active_task_dots(FAKE_HOUSEHOLD_ID, "2026-09-01", "2026-09-30")

        mock_log.warning.assert_not_called()


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
        store = stub_store_find(repo, expected_members)

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
        stub_store_find(repo, [])

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
        store = stub_store_find(repo, [{"id": "recipe-1", "source_url": "https://example.com"}])

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
