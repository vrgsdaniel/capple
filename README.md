# Capple
planning app

## Database Migrations

Migrations live in `infra/supabase/migrations/` and follow the naming convention `YYYYMMDDHHmmss_<identifier>.sql`.

### First-time setup

Link your local `infra/` directory to the remote Supabase project (only needed once):

```bash
cd infra && supabase link --project-ref $SUPABASE_PROJECT
```

### Create a new migration

```bash
make migration name=<identifier>
```

Example:

```bash
make migration name=add_couples_table
# Creates infra/supabase/migrations/20260426143022_add_couples_table.sql
```

### Apply migrations

```bash
make db-push
```

This runs `supabase db push` from the `infra/` directory, applying any pending migrations to the linked Supabase project.

In CI — migrations are applied automatically when files under
`infra/supabase/migrations/` are merged to main.

## Store & Criteria Pattern

The data-access layer uses a **Store + Criteria** pattern so that querying any table is consistent and extensible without touching the core `DB` class.

### Overview

| Module | Purpose |
|---|---|
| `src/db/criteria.py` | Fluent, provider-agnostic filter builder |
| `src/db/store.py` | Generic `Store` that translates `Criteria` into Supabase queries |
| `src/db/db.py` | `DB` class — manages the client and exposes `db.store(table)` |

### Basic usage

```python
from src.db.criteria import Criteria

# Get a store for any table
store = db.store("battery_logs")

# Find many rows
logs = store.find(
    Criteria()
    .eq("household_id", household_id)
    .gte("created_at", since)
    .order("created_at", ascending=False)
    .limit(50)
)

# Find a single row
log = store.find_one(Criteria().eq("serial", "ABC123"))

# Shorthand — get by primary key
log = store.get_by_id(some_uuid)
```

### Available Criteria operators

| Method | SQL equivalent |
|---|---|
| `eq(col, val)` | `col = val` |
| `neq(col, val)` | `col != val` |
| `gt` / `gte` / `lt` / `lte` | `>` / `>=` / `<` / `<=` |
| `like(col, pattern)` | `col LIKE pattern` |
| `ilike(col, pattern)` | `col ILIKE pattern` (case-insensitive) |
| `is_(col, val)` | `col IS val` |
| `in_(col, list)` | `col IN (...)` |
| `select(cols)` | Column projection (`"id, name"`) |
| `limit(n)` | Limit result set |
| `order(col, ascending=)` | Sort rows |

### Extending Store with insert, update, and delete

The base `Store` only handles reads. To support writes, add methods directly to `Store` in `src/db/store.py`:

```python
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
```

Usage from a service:

```python
store = db.store("households")

# Insert
household = store.insert({"name": "My Home", "invite_code": "abc123"})

# Update
store.update(household["id"], {"name": "Our Home"})

# Delete
store.delete(household["id"])
```

### Swapping the storage provider

`Criteria` is provider-agnostic — it only holds data. The provider-specific part lives entirely in `Store._build_query`. To use a different backend (e.g. raw asyncpg, SQLAlchemy, DynamoDB), create a new store class that translates the same `Criteria` into that provider's query API:

```python
from src.db.criteria import Criteria, Criterion


class SQLAlchemyStore:
    """Example alternative store backed by SQLAlchemy."""

    def __init__(self, session, model):
        self._session = session
        self._model = model

    _OP_MAP = {
        "eq": "__eq__",
        "neq": "__ne__",
        "gt": "__gt__",
        "gte": "__ge__",
        "lt": "__lt__",
        "lte": "__le__",
    }

    def _apply_filter(self, query, criterion: Criterion):
        col = getattr(self._model, criterion.column)
        op = self._OP_MAP.get(criterion.operator)
        if op:
            return query.filter(getattr(col, op)(criterion.value))
        if criterion.operator == "in_":
            return query.filter(col.in_(criterion.value))
        if criterion.operator == "like":
            return query.filter(col.like(criterion.value))
        raise ValueError(f"Unsupported operator: {criterion.operator}")

    def find(self, criteria: Criteria | None = None) -> list:
        criteria = criteria or Criteria()
        query = self._session.query(self._model)
        for f in criteria._filters:
            query = self._apply_filter(query, f)
        if criteria._order_by:
            col = getattr(self._model, criteria._order_by)
            query = query.order_by(col.asc() if criteria._ascending else col.desc())
        if criteria._limit:
            query = query.limit(criteria._limit)
        return query.all()
```

The rest of the application (services, controllers) only depend on `Criteria` and the store's `find` / `find_one` / `get_by_id` interface, so swapping providers requires no changes outside the `db/` package.

## Testing

Tests live in `backend/tests/` and use `pytest`. Run them with:

```bash
cd backend && uv run pytest tests/ -v
```

### Strategy

Since services only depend on `DB` and controllers only depend on services + auth, we mock at the boundary:

- **Service tests** — mock `DB` with `MagicMock(spec=DB)` and inject it into the service constructor
- **API tests** — use FastAPI's `dependency_overrides` to swap `get_db` and `get_current_user`, no real Supabase or auth needed

### Service test example

```python
from unittest.mock import MagicMock
from src.db.db import DB
from src.service.users import UserService

mock_db = MagicMock(spec=DB)
service = UserService(mock_db)

# Set up the mock return value
mock_db.get_profile_by_id.return_value = {"display_name": "Alice", "avatar_url": "..."}

# Call and assert
result = service.get_user_name_by_id("user-123")
assert result["user_name"] == "Alice"
mock_db.get_profile_by_id.assert_called_once_with("user-123")
```

`MagicMock(spec=DB)` ensures the mock only allows methods that exist on `DB` — calling a non-existent method raises `AttributeError`.

### API test example

```python
from types import SimpleNamespace
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.controllers.api.users import get_current_user, get_user_service, router
from src.db.db import DB
from src.service.users import UserService

mock_db = MagicMock(spec=DB)
fake_user = SimpleNamespace(id="user-111")

app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_user_service] = lambda: UserService(mock_db)
app.dependency_overrides[get_current_user] = lambda: fake_user
client = TestClient(app)

mock_db.get_profile_by_id.return_value = {"display_name": "Alice", "avatar_url": "..."}
resp = client.get("/api/me")
assert resp.status_code == 200
```

`dependency_overrides` replaces FastAPI's `Depends()` resolution at the framework level, so the real `get_db` (which would hit Supabase) and `get_current_user` (which would validate a JWT) are never called.