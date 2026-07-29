---
name: implement-api-endpoint
description: Implement or modify Capple FastAPI endpoints across request/response models, async services, the Repository/Store data layer, Supabase migrations, router registration, and tests. Use for new backend resources, CRUD routes, authenticated APIs, schema-backed backend features, or endpoint bugs that require coordinated controller/service/repository changes.
---

# Implement a Capple API endpoint

Follow the live architecture, not older `.github/agents` references to `src/db/db.py`.

## Discover the feature path

1. Read `AGENTS.md`.
2. Inspect one analogous controller, service, repository section, model, API test, and service test.
3. Inspect `backend/src/controllers/api/__init__.py`, `backend/src/errors.py`, and `backend/src/utils/general.py`.
4. If persistence changes, inspect the latest relevant migrations under `infra/supabase/migrations/`.
5. Check the frontend caller when changing an existing contract.

State assumptions only when they materially affect the API contract or schema.

## Implement by layer

1. Add a forward-only migration when persistence changes. Use the `app` schema, suitable constraints/indexes, grants, RLS, and household/user-scoped policies.
2. Add Pydantic request and response types under `backend/src/models/`. Reject invalid input at this boundary and use explicit nested types.
3. Add narrow async methods to `backend/src/repository/repository.py`. Compose queries with `Store` and `Criteria`; never access Supabase directly from a controller or service.
4. Add business logic to `backend/src/service/`. Accept primitives/plain dictionaries, await repository I/O, enforce household/user scope, and raise domain exceptions.
5. Add the route to `backend/src/controllers/api/`. Require the current user, inject the service, convert request models at the boundary, and map expected domain exceptions with `http_error_response`.
6. Register a new router in `backend/src/controllers/api/__init__.py`.
7. Update frontend types/callers if the contract changed and the task includes end-to-end integration.

Keep ownership constraints in repository mutations. Treat zero affected rows as not found instead of relying on a prefetch followed by an unscoped update/delete.

## Test

- API tests: override the service and authentication dependencies; use a spec'd mock; cover status, response, validation, auth/error mapping, and exact service arguments.
- Service tests: use `MagicMock(spec=Repository)`; cover household resolution, successful behavior, domain failures, ownership arguments, and zero-row races.
- Repository tests: add focused coverage when query composition or Store behavior changes.
- Migration: reason through RLS for owner, household peer, unrelated authenticated user, and anonymous user.

Run focused tests during iteration, then:

```bash
make be-lint
make be-test
```

For cross-stack changes also run the relevant frontend tests, type check, and lint.
