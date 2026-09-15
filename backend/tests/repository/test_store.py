from unittest.mock import AsyncMock, MagicMock

import pytest
from postgrest.exceptions import APIError

from src.errors import ConflictException, NotFoundException, ValidationException
from src.repository.criteria import Criteria
from src.repository.store import Store


def api_error(code: str, message: str = "error") -> APIError:
    return APIError({"code": code, "message": message, "details": None, "hint": None})


def make_store(query: MagicMock) -> Store:
    """Build a Store whose `_table()` returns *query* for every chained call."""
    client = MagicMock()
    client.schema.return_value.table.return_value = query
    return Store(client, "calendar_events")


@pytest.fixture
def query():
    """A MagicMock that supports arbitrary chained calls, ending in an async `.execute()`."""
    q = MagicMock()
    for method in ("insert", "upsert", "update", "eq", "delete"):
        getattr(q, method).return_value = q
    q.execute = AsyncMock()
    return q


class TestInsertErrorTranslation:
    async def test_translates_unique_violation_to_conflict(self, query):
        query.execute.side_effect = api_error("23505")
        store = make_store(query)

        with pytest.raises(ConflictException):
            await store.insert({"title": "Dup"})

    async def test_translates_foreign_key_violation_to_not_found(self, query):
        query.execute.side_effect = api_error("23503")
        store = make_store(query)

        with pytest.raises(NotFoundException):
            await store.insert({"title": "Orphan"})

    async def test_reraises_unrecognized_error_code(self, query):
        query.execute.side_effect = api_error("99999")
        store = make_store(query)

        with pytest.raises(APIError):
            await store.insert({"title": "Whatever"})


class TestUpdateWhereErrorTranslation:
    async def test_translates_check_violation_to_validation_exception(self, query):
        query.execute.side_effect = api_error("23514")
        store = make_store(query)

        with pytest.raises(ValidationException):
            await store.update_where(Criteria().eq("id", "1"), {"end_time": "08:00", "start_time": "20:00"})

    async def test_translates_unique_violation_to_conflict(self, query):
        query.execute.side_effect = api_error("23505")
        store = make_store(query)

        with pytest.raises(ConflictException):
            await store.update_where(Criteria().eq("id", "1"), {"title": "Dup"})

    async def test_translates_foreign_key_violation_to_not_found(self, query):
        query.execute.side_effect = api_error("23503")
        store = make_store(query)

        with pytest.raises(NotFoundException):
            await store.update_where(Criteria().eq("id", "1"), {"created_by": "ghost"})

    async def test_returns_data_on_success(self, query):
        query.execute.return_value = MagicMock(data=[{"id": "1"}])
        store = make_store(query)

        result = await store.update_where(Criteria().eq("id", "1"), {"title": "New"})

        assert result == [{"id": "1"}]


class TestUpdateErrorTranslation:
    async def test_translates_check_violation_to_validation_exception(self, query):
        query.execute.side_effect = api_error("23514")
        store = make_store(query)

        with pytest.raises(ValidationException):
            await store.update("1", {"end_time": "08:00", "start_time": "20:00"})
