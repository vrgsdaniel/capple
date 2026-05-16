# Capple

Capple is a household planning app for couples. It helps partners coordinate daily life through shared context: social battery tracking, household membership, and AI-assisted chat.

## Product Direction

Capple is being built as a practical "home operating layer" for two people:

- Keep both partners aligned on energy and availability
- Reduce planning overhead for everyday decisions
- Make AI suggestions grounded in real household context

The current focus is reliability and useful core flows before expanding into broader lifestyle features.

## Current Scope

Implemented now:

- Supabase auth + profile/household foundation
- Social battery logging
- Battery trend charting in the frontend
- FastAPI backend with service/controller architecture
- LangGraph-powered chat flow with household-aware context assembly
- Supabase migrations and local migration workflow

In progress:

- Hardening chat quality and streaming behavior
- Improving battery insights and household context coverage

## Tech Stack

Frontend:

- React + TypeScript + Vite
- TanStack Query
- Supabase JS client
- Recharts

Backend:

- Python 3.13
- FastAPI
- LangGraph + LangChain OpenAI
- Supabase Python client

Tooling:

- pnpm (frontend)
- uv (backend)
- Supabase CLI (migrations)
- Docker Compose (backend container run)

## Repository Layout

```text
capple/
  backend/
    src/
      agents/
      auth/
      controllers/
      db/
      models/
      service/
    tests/
  frontend/
    src/
      components/
      hooks/
      pages/
      providers/
  infra/
    supabase/
      migrations/
```

## Quick Start

### 1. Prerequisites

- Node.js 22+
- pnpm
- Python 3.13+
- uv
- Supabase CLI

### 2. Environment

Copy the backend template and fill in values:

```bash
cp example.env backend/.env
```

Frontend env vars (create `frontend/.env`):

```bash
VITE_API_BASE_URL=http://localhost:8080
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-key>
```

### 3. Install Dependencies

```bash
cd frontend && pnpm install
cd ../backend && uv sync
```

### 4. Run Locally

Backend:

```bash
make be-dev
```

Frontend:

```bash
make fe-dev
```

Default local URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8080`
- API docs: `http://localhost:8080/api/docs`

## Database Migrations

Migrations live in `infra/supabase/migrations/` and follow this naming scheme:

`YYYYMMDDHHmmss_<identifier>.sql`

Link Supabase project once:

```bash
cd infra && supabase link --project-ref $SUPABASE_PROJECT
```

Create migration:

```bash
make migration name=<identifier>
```

Apply pending migrations:

```bash
make db-push
```

## Testing and Linting

Backend tests:

```bash
cd backend && uv run pytest tests/ -v
```

Backend lint:

```bash
make lint
```

Frontend lint:

```bash
cd frontend && pnpm run lint
```

## Roadmap (Future Plans)

### Phase 1: Core Stability (Now)

- Improve chat response quality with better guardrails and prompt shaping
- Strengthen API error handling and observability
- Add higher-coverage tests for service and controller layers
- Improve onboarding and household creation/join UX

### Phase 2: Shared Planning (Next)

- Expand battery insights from simple trend views to actionable suggestions
- Add household-level routines/check-ins
- Introduce saved chat context and useful conversation memory controls

### Phase 3: Meals and Groceries (Planned)

- Shared grocery list with realtime sync
- Pantry model and low-stock reminders
- Recipe suggestion flow tied to pantry + battery context

### Phase 4: Activities and Scheduling (Planned)

- Household activity suggestions based on both partners' energy patterns
- Calendar integration for lightweight planning windows
- Favorites/history for places and activities

### Phase 5: Intelligence and Personalization (Later)

- Better long-term household memory and preferences
- Adaptive suggestions that learn from accepted/rejected recommendations
- Personalized weekly household recap and planning prompts

## Development Notes

- Backend follows a controller -> service -> db layering approach.
- Data access uses a Store + Criteria pattern for query composition.
- Chat orchestration runs through LangGraph state transitions.

## License

MIT
