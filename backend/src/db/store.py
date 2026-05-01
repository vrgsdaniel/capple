from __future__ import annotations

from supabase import Client

from src.db.criteria import Criteria


class Store:
    """Generic table store that applies :class:`Criteria` to Supabase queries."""

    def __init__(self, client: Client, table_name: str) -> None:
        self._client = client
        self._table_name = table_name

    def _build_query(self, criteria: Criteria):
        query = self._client.table(self._table_name).select(criteria._select)
        for f in criteria._filters:
            query = getattr(query, f.operator)(f.column, f.value)
        if criteria._order_by is not None:
            query = query.order(criteria._order_by, desc=not criteria._ascending)
        if criteria._limit is not None:
            query = query.limit(criteria._limit)
        return query

    def find(self, criteria: Criteria | None = None) -> list[dict]:
        criteria = criteria or Criteria()
        result = self._build_query(criteria).execute()
        return result.data

    def find_one(self, criteria: Criteria | None = None) -> dict | None:
        criteria = criteria or Criteria()
        criteria.limit(1)
        results = self.find(criteria)
        return results[0] if results else None

    def get_by_id(self, entity_id: str) -> dict | None:
        return self.find_one(Criteria().eq("id", entity_id))

    def insert(self, data: dict) -> dict:
        result = self._client.table(self._table_name).insert(data).execute()
        return result.data[0]

    def update(self, entity_id: str, data: dict) -> dict | None:
        result = (
            self._client.table(self._table_name)
            .update(data)
            .eq("id", entity_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def delete(self, entity_id: str) -> None:
        self._client.table(self._table_name).delete().eq("id", entity_id).execute()
