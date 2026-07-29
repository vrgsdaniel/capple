# Capple repository guide

Use this file as the default instruction set for work in this repository. More specific user instructions take precedence.

## Product and stack

Capple is a shared household-planning app for couples.

- `frontend/`: React 19, TypeScript, Vite, Supabase Auth/Realtime, Jest
- `backend/`: Python 3.13, FastAPI, Pydantic, async Supabase repository, LangGraph, pytest
- `infra/supabase/migrations/`: PostgreSQL/Supabase schema, RLS, functions, and policies
- `.github/workflows/`: the authoritative CI and deployment commands

Do not treat generated or local-only data as application source. Ignore virtual environments, `node_modules/`, build output, caches, `.env` files, Supabase `.temp/`, notebooks, and root-level recipe/import artifacts unless the task explicitly targets them.

## Before editing

1. Read the closest existing implementation and its tests before choosing a pattern.
2. Check `git status --short` and preserve unrelated user changes.
3. Trace a cross-stack feature through migration, repository, service, controller, hook/provider, and component as applicable.
4. Keep changes scoped. Do not refactor adjacent code solely for style.
5. Never expose or commit values from `.env`, `backend/.env`, `frontend/.env`, or `infra/supabase/.temp/`.

## Backend conventions

The active dependency flow is:

`FastAPI controller -> service -> Repository -> Store -> Supabase`

- Controllers live in `backend/src/controllers/api/`. Keep them limited to authentication, dependency injection, request/response models, service calls, and HTTP error mapping.
- Require `Depends(get_current_user)` for user-facing endpoints unless the route is intentionally public infrastructure.
- Convert Pydantic request models to primitives or plain dictionaries at the controller boundary.
- Services live in `backend/src/service/`, accept a `Repository`, contain business rules, and use domain exceptions from `backend/src/errors.py`.
- All repository and service I/O is async. Preserve `async`/`await` end to end.
- Data access lives in `backend/src/repository/repository.py` and uses `Store` plus `Criteria`. Do not add new code to the obsolete `backend/src/db/` path and do not call the Supabase client directly from controllers or services.
- Scope reads and writes by `user_id` or `household_id`. Prefer ownership constraints in the mutation query and treat zero affected rows as not found.
- Register new routers in `backend/src/controllers/api/__init__.py`.
- Log failures with useful non-secret identifiers. Do not log tokens, credentials, or private payloads.

Tests mirror the source area under `backend/tests/api/`, `backend/tests/service/`, `backend/tests/repository/`, `backend/tests/agents/`, and `backend/tests/tools/`. Use `MagicMock(spec=...)`, override FastAPI dependencies in API tests, and cover success, validation, authorization/scoping, domain errors, and zero-row races.

## Frontend conventions

- Centralize authenticated HTTP behavior in `frontend/src/lib/api.ts`; do not create ad hoc Axios clients or hardcode API origins.
- Put reusable types in `frontend/src/types/`, data/state behavior in `frontend/src/hooks/` or `frontend/src/providers/`, and rendering in `frontend/src/components/` or `frontend/src/pages/`.
- Keep direct API calls out of presentational components when an existing hook/provider boundary applies.
- Put Supabase Realtime subscriptions in dedicated `use*Realtime` hooks and use schema `app`.
- Reuse components from `frontend/src/components/ui/` and existing CSS/design tokens before introducing new UI patterns.
- Preserve loading, empty, error, and authenticated/unauthenticated states. Keep interactions accessible with semantic controls, labels, keyboard behavior, and visible focus.
- Add or update colocated `*.test.ts`/`*.test.tsx` tests for changed behavior.

The repository contains both npm and pnpm references, but CI is authoritative: use the committed `frontend/package-lock.json` and npm commands for reproducible validation.

## Database migrations

- Create migrations in `infra/supabase/migrations/` with `YYYYMMDDHHMMSS_<snake_case_name>.sql`; `make migration name=<name>` generates the filename.
- Application tables and relationships use the `app` schema unless an existing migration demonstrates a necessary exception.
- Add constraints, indexes, grants, RLS enablement, and least-privilege policies together with the schema change.
- Scope policies with `auth.uid()` through the appropriate profile/household relationship. For `FOR ALL`, include both `USING` and `WITH CHECK`.
- Make forward-only changes. Do not edit a migration that may already have been applied unless explicitly asked.
- Do not run `make db-push` or otherwise mutate a linked database without explicit user authorization.

## LangGraph workflows

- Agent code lives in `backend/src/agents/`: typed state in `state.py`, graph wiring in `graph.py`, nodes in `nodes/`, and tool factories in `tools/`.
- Keep `ChatState` serializable and default-initialized. Return partial state updates from nodes.
- Pass request-scoped dependencies through `GraphContext`; do not hide mutable globals in nodes or tools.
- Tool factories must expose narrow typed contracts and bind household/user scope from context rather than trusting model-supplied identifiers.
- Keep deterministic parsing, ranking, and fallback behavior outside the LLM where practical.
- Update focused node/tool tests and graph routing tests whenever state, edges, prompts, or tool contracts change.

## Validation

Run the smallest relevant checks first, then broaden for cross-cutting changes:

```bash
make be-lint
make be-test
make fe-test
cd frontend && npm run tsc -- --noEmit
cd frontend && npm run lint
cd frontend && npm run build
```

Do not claim a check passed unless it was run. Report failures and distinguish failures caused by the change from pre-existing failures.

## Project skills

Use the project-local skill that matches the task:

- `$implement-api-endpoint`: add or change a FastAPI endpoint across migration, repository, service, controller, and tests.
- `$build-vite-feature`: build or debug React/Vite UI, hooks, providers, API integration, and tests.
- `$design-langgraph-workflow`: design or modify Capple graph state, nodes, tools, prompts, and agent tests.
- `$review-feature-architecture`: perform a read-only, evidence-based feature review with prioritized findings.
