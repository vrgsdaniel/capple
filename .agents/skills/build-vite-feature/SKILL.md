---
name: build-vite-feature
description: Implement, refactor, or debug Capple's React 19, TypeScript, and Vite frontend, including pages, components, hooks, providers, authenticated Axios calls, Supabase Realtime, styling, accessibility, and Jest tests. Use for UI features, frontend API integration, client state bugs, responsive behavior, or frontend build/type/lint failures.
---

# Build a Capple Vite feature

## Establish the boundary

1. Read `AGENTS.md` and inspect the closest feature from type to hook/provider to page/component to test.
2. Check `frontend/package.json`, `frontend/src/lib/api.ts`, `frontend/src/lib/supabase.ts`, and existing UI primitives before adding dependencies or infrastructure.
3. Inspect the backend model/controller when consuming or changing an API contract.
4. Preserve the existing visual language and layout patterns unless redesign is requested.

Choose the narrowest layer that owns the behavior:

- `src/types/`: reusable domain and view types
- `src/lib/`: configured clients and pure utilities
- `src/hooks/`: reusable data fetching, mutations, state, and effects
- `src/providers/`: app-wide session or household state
- `src/components/`: reusable presentation and feature UI
- `src/pages/`: route-level composition

## Implement

- Use the shared authenticated Axios client; do not hardcode origins or recreate token handling.
- Keep components focused on rendering and user interaction. Move reusable remote-state behavior into hooks/providers.
- Keep Supabase Realtime subscriptions in dedicated `use*Realtime` hooks, scope them to schema `app`, and clean them up on unmount.
- Reuse `src/components/ui/`, existing CSS variables, and established feature CSS.
- Model loading, empty, error, and success states explicitly.
- Keep optimistic changes recoverable on request failure.
- Use semantic HTML, accessible names, keyboard-operable controls, visible focus, and appropriate dialog/menu behavior.
- Avoid adding memoization, global state, or dependencies without evidence that the feature needs them.

## Test and validate

Add or update colocated Jest/Testing Library tests. Cover observable behavior rather than implementation details:

- initial loading and request success/failure
- user interactions and mutation payloads
- provider/hook state transitions
- subscription cleanup when Realtime changes
- important accessibility roles and names

Use npm because `package-lock.json` and GitHub CI are authoritative:

```bash
cd frontend && npm run test -- --runInBand
cd frontend && npm run tsc -- --noEmit
cd frontend && npm run lint
cd frontend && npm run build
```

Run focused tests first during iteration. If the API contract changed, also run relevant backend tests.
