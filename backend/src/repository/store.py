from __future__ import annotations

from typing import Literal, overload

from supabase import AsyncClient, acreate_client
from postgrest.exceptions import APIError

from src.repository.criteria import Criteria
from src.errors import ConflictException, NotFoundException
from src.settings import get_supabase_settings


async def create_store_client() -> AsyncClient:
    settings = get_supabase_settings()
    return await acreate_client(settings.url, settings.service_role_key)


class Store:
    """Generic table store that applies :class:`Criteria` to Supabase queries."""

    def __init__(self, client: AsyncClient, table_name: str, schema_name: str = "app") -> None:
        self._client = client
        self._table_name = table_name
        self._schema_name = schema_name

    def _table(self):
        return self._client.schema(self._schema_name).table(self._table_name)

    def _apply_filters(self, query, criteria: Criteria):
        for f in criteria._filters:
            query = getattr(query, f.operator)(f.column, f.value)
        return query

    def _build_query(self, criteria: Criteria, *, count: str | None = None):
        query = self._table().select(criteria._select, count=count)
        query = self._apply_filters(query, criteria)
        if criteria._order_by is not None:
            query = query.order(criteria._order_by, desc=not criteria._ascending)
        if criteria._limit is not None:
            offset = criteria._offset or 0
            query = query.range(offset, offset + criteria._limit - 1)
        return query

    @overload
    async def find(self, criteria: Criteria | None = None, *, with_count: Literal[False] = False) -> list[dict]: ...
    @overload
    async def find(self, criteria: Criteria | None = None, *, with_count: Literal[True]) -> tuple[list[dict], int]: ...

    async def find(self, criteria: Criteria | None = None, *, with_count: bool = False):
        criteria = criteria or Criteria()
        result = await self._build_query(criteria, count="exact" if with_count else None).execute()
        if with_count:
            return result.data, (result.count or 0)
        return result.data

    async def find_one(self, criteria: Criteria | None = None) -> dict | None:
        criteria = criteria or Criteria()
        criteria.limit(1)
        data = await self.find(criteria)
        return data[0] if data else None

    async def get_by_id(self, entity_id: str) -> dict | None:
        return await self.find_one(Criteria().eq("id", entity_id))

    @overload
    async def insert(self, data: dict) -> dict: ...
    @overload
    async def insert(self, data: list[dict]) -> list[dict]: ...
    async def insert(self, data: dict | list[dict]) -> dict | list[dict]:
        try:
            result = await self._table().insert(data).execute()
        except APIError as e:
            if e.code == "23505":
                raise ConflictException(f"Duplicate entry in {self._table_name}") from e
            if e.code == "23503":
                raise NotFoundException(f"Referenced entity not found for {self._table_name}") from e
            raise
        if isinstance(data, list):
            return result.data
        return result.data[0]

    async def upsert(self, data: dict, on_conflict: str) -> dict:
        """Insert or update on conflict. *on_conflict* is a comma-separated list of column names
        that map to a unique constraint (used by PostgREST for ON CONFLICT targeting)."""
        try:
            result = await self._table().upsert(data, on_conflict=on_conflict).execute()
        except APIError as e:
            if e.code == "23503":
                raise NotFoundException(f"Referenced entity not found for {self._table_name}") from e
            raise
        return result.data[0]

    async def update(self, entity_id: str, data: dict) -> dict | None:
        result = await self._table().update(data).eq("id", entity_id).execute()
        return result.data[0] if result.data else None

    async def update_where(self, criteria: Criteria, data: dict) -> list[dict]:
        query = self._apply_filters(self._table().update(data), criteria)
        return (await query.execute()).data

    async def delete(self, entity_id: str) -> None:
        await self._table().delete().eq("id", entity_id).execute()

    async def delete_where(self, criteria: Criteria) -> list[dict]:
        query = self._table().delete()
        query = self._apply_filters(query, criteria)
        result = await query.execute()
        return result.data
