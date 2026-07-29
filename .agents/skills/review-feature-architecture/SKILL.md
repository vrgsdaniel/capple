---
name: review-feature-architecture
description: Perform a read-only architectural and code review of Capple changes across FastAPI, async Repository/Store data access, Supabase migrations and RLS, React/Vite, LangGraph, tests, and CI. Use when reviewing a feature, branch, diff, pull request, or changed files for correctness, security, regressions, missing tests, and deviations from live repository conventions.
---

# Review a Capple feature

Do not modify code unless the user separately asks for fixes.

## Establish scope and baseline

1. Read `AGENTS.md`.
2. Determine the review target from the user's file list or `git status`, `git diff`, and `git diff --cached`.
3. Preserve awareness of untracked files; do not assume every dirty-worktree change belongs to the same feature.
4. Read every changed file in scope and enough surrounding code to trace callers and callees.
5. Read one current analogous implementation and its tests. Prefer live code over older `.github/agents` or `.claude` guidance when they disagree.

## Review for actionable defects

Check only categories relevant to the diff:

- API contract compatibility between Pydantic models, controllers, frontend types, and callers
- controller/service/repository separation and correct async behavior
- authentication, household/user scoping, zero-row races, and exception-to-HTTP mapping
- migration safety, `app` schema consistency, indexes, grants, RLS `USING`/`WITH CHECK`, and forward compatibility
- React state/effect correctness, stale closures, cleanup, request races, loading/error states, accessibility, and UI regressions
- LangGraph state/edge/tool contracts, context authorization, deterministic fallbacks, and prompt/data leakage
- tests that would fail to detect realistic regressions, plus CI/build consequences
- secrets, logging of sensitive data, unsafe query construction, or destructive operations

Do not report style preferences unless they cause a concrete maintenance or correctness risk. Do not call something a defect solely because it differs from an old agent prompt.

## Verify findings

For each candidate:

1. Trace the actual execution path.
2. Confirm the claim against current types, tests, migrations, or framework behavior.
3. Run the narrowest useful read-only check when practical.
4. Remove speculative findings that lack a concrete failure scenario.

## Report

Lead with findings ordered by severity. For each finding include:

- severity and concise title
- exact file and tight line range
- the failing scenario
- why it matters
- a specific remediation

Use:

- P1: security, data loss, authorization bypass, or broadly broken core flow
- P2: user-visible correctness regression or likely production failure
- P3: localized defect, resilience gap, or meaningful missing test

After findings, list open assumptions/questions and a short validation summary. If there are no findings, say so explicitly and note any residual testing risk. Keep general summaries secondary to actionable findings.
