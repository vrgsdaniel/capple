from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Criterion:
    column: str
    operator: str
    value: object


@dataclass
class Criteria:
    """Fluent builder for composing DB query filters."""

    _select: str = "*"
    _filters: list[Criterion] = field(default_factory=list)
    _limit: int | None = None
    _offset: int | None = None
    _order_by: str | None = None
    _ascending: bool = True

    # Column selection

    def select(self, columns: str) -> Criteria:
        self._select = columns
        return self

    # Filter operators

    def eq(self, column: str, value: object) -> Criteria:
        self._filters.append(Criterion(column, "eq", value))
        return self

    def neq(self, column: str, value: object) -> Criteria:
        self._filters.append(Criterion(column, "neq", value))
        return self

    def gt(self, column: str, value: object) -> Criteria:
        self._filters.append(Criterion(column, "gt", value))
        return self

    def gte(self, column: str, value: object) -> Criteria:
        self._filters.append(Criterion(column, "gte", value))
        return self

    def lt(self, column: str, value: object) -> Criteria:
        self._filters.append(Criterion(column, "lt", value))
        return self

    def lte(self, column: str, value: object) -> Criteria:
        self._filters.append(Criterion(column, "lte", value))
        return self

    def like(self, column: str, pattern: str) -> Criteria:
        self._filters.append(Criterion(column, "like", pattern))
        return self

    def ilike(self, column: str, pattern: str) -> Criteria:
        self._filters.append(Criterion(column, "ilike", pattern))
        return self

    def is_(self, column: str, value: object) -> Criteria:
        self._filters.append(Criterion(column, "is_", value))
        return self

    def in_(self, column: str, values: list) -> Criteria:
        self._filters.append(Criterion(column, "in_", values))
        return self

    # Pagination / ordering

    def limit(self, n: int) -> Criteria:
        self._limit = n
        return self

    def offset(self, n: int) -> Criteria:
        self._offset = n
        return self

    def order(self, column: str, *, ascending: bool = True) -> Criteria:
        self._order_by = column
        self._ascending = ascending
        return self
