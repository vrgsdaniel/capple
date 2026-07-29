# Feature Review — User & Household Management

**Scope reviewed:** `backend/src/controllers/api/users.py`, `backend/src/service/users.py`, `backend/src/repository/repository.py` (households/profiles sections), `backend/src/errors.py`, `backend/src/models/household.py`, `backend/tests/api/test_users_api.py`, `backend/tests/service/test_user_service.py`, plus the household migrations for RLS/index/cascade baseline.

**Key architectural fact that shapes several findings:** the backend connects with the Supabase **service_role** key (`backend/src/repository/store.py:15`), which **bypasses RLS entirely**. So every RLS policy in the household migrations is dead weight at runtime — ownership is enforced *only* by Python logic in the service. That raises the stakes on the service-layer scoping findings below.

---

### 🔴 High — `create_household` is not atomic; a failed member-insert orphans a household and permanently blocks account deletion
File: `backend/src/service/users.py:20-26`
What: The service inserts the `households` row first, then separately calls `add_member_to_household`. There is no transaction. If the second call fails — e.g. the user already has a membership from a concurrent request, tripping the `unique (user_id)` constraint at `infra/supabase/migrations/20260502000001_unique_user_household.sql:2` → `23505` → `ConflictException` — the `households` row is already committed with `created_by = user_id` and **no membership row**.
Why: The orphan household is invisible to the user (`get_household_by_user` finds no membership → returns `None`), so it can never be joined, left, or deleted through the API. Worse: `households.created_by` is `references auth.users(id) on delete restrict` (`infra/supabase/migrations/20260501142413_households.sql:5`). Because `get_household_by_user` returns `None`, `delete_account` (`backend/src/service/users.py:81-85`) sees no owned household and proceeds to `auth.admin.delete_user`, which the FK **restrict** then rejects at the DB layer → the user can *never* delete their account (permanent 500).
Fix: Do the household insert + owner membership insert in a single DB transaction/RPC, or reverse the guard: check `get_household_by_user` conflict, and if `add_member_to_household` fails after the insert, roll back / delete the just-created household before re-raising.

---

### 🟡 Medium — Request models skip `extra="forbid"`; `invite_code` skips `min_length`
File: `backend/src/models/household.py:6-11`
What: `CreateHouseholdRequest` and `JoinHouseholdRequest` both lack `model_config = ConfigDict(extra="forbid")`, and `JoinHouseholdRequest.invite_code` has no `Field(..., min_length=1)`. Compare the established convention in `backend/src/models/grocery_item.py:7-31` where every request model forbids extras and constrains required strings.
Why: Extra fields are silently accepted (masks client bugs and typo'd field names). An empty `invite_code` sails through to `get_household_by_code("")`. Validation should reject malformed input at the API boundary, not defer to a DB lookup.
Fix: Add `model_config = ConfigDict(extra="forbid")` to both, and `invite_code: str = Field(..., min_length=1)`.

---

### 🟡 Medium — `leave_household` ignores the zero-row delete result
File: `backend/src/service/users.py:65-71`
What: `remove_user_from_household` returns a `bool` indicating whether a row was deleted (`backend/src/repository/repository.py:69-73`), but the service discards it. On a race (the membership already deleted between the `get_household_by_user` pre-fetch and the delete), the endpoint still returns `204`.
Why: Skill rule D — "zero affected rows from update/delete raises `NotFoundException`, never returns success silently." The grocery service applies this consistently (e.g. `backend/src/service/grocery_service.py:177-180`). Silent success on a no-op delete hides consistency problems.
Fix: `removed = await self.db.remove_user_from_household(...)`; if not `removed`, `log.warning(...)` and raise `NotFoundException`.

---

### 🟡 Medium — `delete_household` uses pre-fetch-then-unscoped-delete instead of an ownership-scoped write
File: `backend/src/service/users.py:73-79` / `backend/src/repository/repository.py:75-76`
What: The service pre-fetches the household, checks `role != "owner"` in Python, then calls `delete_household(household["id"])`, which deletes purely by primary key (`store.delete(id)`) with no ownership constraint in the query.
Why: Skill rules D/E — ownership should be enforced *inside* the write query, not via pre-fetch + unscoped write. It's functionally safe today only because the id is derived from the caller's own membership *and* the owner-check happens first — but since service_role bypasses RLS, this Python check is the *sole* protection. It's the exact fragile pattern the guidelines flag.
Fix: Scope the delete (e.g. `delete_where(id == household_id AND created_by == user_id)`) and treat 0 rows as `NotFoundException`, removing reliance on the separate pre-fetch.

---

### 🟡 Medium — Error/not-found paths in the service don't log before raising
File: `backend/src/service/users.py:23`, `:31`, `:34`, `:68`, `:70`, `:76`, `:78`, `:84`
What: Only `get_household_members` logs a warning before raising (`backend/src/service/users.py:43`). Every other raise path — the two "already belongs to a household" conflicts, invalid invite code, owner-can't-leave, member-can't-delete, owner-must-delete-household-first — raises with no log line.
Why: Skill rule D requires `log.warning` with tracing context (user id, resource id) on every not-found/error path. The grocery service does this uniformly. Without it, these 4xx outcomes are invisible in logs and hard to trace.
Fix: Add a `log.warning` with the `user_id` (and `household_id` where known) immediately before each raise.

---

### 🟡 Medium — Missing 422 validation tests; controller tests don't assert service call args
File: `backend/tests/api/test_users_api.py`
What: There is no test that malformed input (e.g. `POST /api/households` with empty/missing `name`, or `/join` with a blank code) returns `422` and that the service is **not** invoked. Success/404/409/500 paths are covered, but the validation boundary is not. Assertions check status + response body but never `assert_called_once_with(...)` on the service to verify *what* it was called with.
Why: Skill rules F — validation failures must be asserted at 422, and assertions should verify what the service received. (This gap compounds the model validation finding above — the missing `min_length`/`extra="forbid"` would be caught here.)
Fix: Add 422 cases per endpoint and assert the underlying service/db mock was not called; add call-arg assertions on success paths.

---

### 🟢 Low — `delete_user_account` calls `self.client` directly outside `__init__`/`is_alive`
File: `backend/src/repository/repository.py:78-79`
What: `await self.client.auth.admin.delete_user(user_id)` bypasses the `store()`/`Criteria` abstraction and touches the raw client directly.
Why: Skill rule E — no direct `self.client` use outside `__init__`/`is_alive`. This one is a *necessary* exception (auth admin has no `store` equivalent), but it's the only such call and deserves a comment marking it as an intentional carve-out so it isn't copied as precedent.
Fix: Keep it, but add a short comment explaining the auth-admin exception.

---

### 🟢 Low — `UserHouseholdResponse` omits `extra="ignore"`
File: `backend/src/models/household.py:14-18`
What: `HouseholdMember` and `HouseholdMembersResponse` set `ConfigDict(extra="ignore")`, but `UserHouseholdResponse` does not.
Why: Skill rule B — response models should use `extra="ignore"` for forward-compatibility with extra DB columns. Functionally harmless today (the service builds an exact 4-key dict), but inconsistent.
Fix: Add `model_config = ConfigDict(extra="ignore")`.

---

### 🟢 Low — `current_user` is typed `Dict` but accessed as an attribute
File: `backend/src/controllers/api/users.py:55` (and every endpoint), used as `current_user.id` at `:59`
What: The dependency return is annotated `Annotated[Dict, ...]`, but the code does `current_user.id` (attribute access), and the test stubs it with `SimpleNamespace`. A real `dict` would raise `AttributeError`.
Why: The type annotation misrepresents the actual contract, defeating type-checking on the most security-sensitive value (the caller identity).
Fix: Type it to the actual user model returned by `Auth.get_current_user()`.

---

### 🟢 Low — `get_my_household` and `get_current_user_name` have no exception mapping
File: `backend/src/controllers/api/users.py:53-66`, `:137-149`
What: These two endpoints only handle the `None`→404 case; an unexpected DB exception propagates as FastAPI's default 500. The other endpoints wrap calls in `try/except … → http_error_response(500)`.
Why: Minor inconsistency in error surfacing (uncaught exceptions may leak a stack trace depending on config vs. the controlled 500 message elsewhere).
Fix: Wrap in the same `try/except Exception` → `log.error` + 500 pattern used by the sibling endpoints.

---

### ℹ️ Observation — RLS is bypassed at runtime; Python is the only line of defense
The service_role client ignores all household/member RLS policies. Skill rule H expects "RLS is the last line of defense — not the *only* line." Here it is effectively *no* line of defense in the running app. The Python scoping in the service is load-bearing and single-layer — which is why the unscoped-delete and ignored-zero-row findings above matter more than they would in an RLS-enforced setup. Worth a team decision on whether to run privileged endpoints under a user-scoped (anon+JWT) client so RLS actually backstops the service logic.

### ℹ️ Observation — `ForbiddenException` added outside the skill's canonical exception set
`backend/src/errors.py:25-30` adds `ForbiddenException`, which the service raises and the controller maps to 403. Skill rule D lists only `NotFound`/`Conflict`/`InternalServer`, but a distinct 403 for owner/member permission is a reasonable, cleanly-mapped extension — not a defect. Noting so the exception taxonomy stays intentional.

### ℹ️ Observation — Controller tests exercise the real service, not `MagicMock(spec=UserService)`
`backend/tests/api/test_users_api.py:24-25` wires a real `UserService(mock_db)` rather than `MagicMock(spec=UserService)` as skill rule F prescribes. This makes the "controller" tests de-facto integration tests through the service. Coverage is good and it uses `spec=Repository`, so this is defensible — but it means a controller-only regression (e.g. wrong exception→status mapping) is only caught incidentally, and there is duplication with the service tests.

### ℹ️ Observation — `households` table has no `updated_at` despite an update policy
`infra/supabase/migrations/20260501142413_households.sql:2-8` defines an owner-update RLS policy but no `updated_at` column (skill rule A). This is a pre-existing committed migration, not part of this diff, but relevant to the household domain under review.

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 High  | 1 |
| 🟡 Medium | 5 |
| 🟢 Low   | 4 |
| ℹ️ Observation | 4 |

**Top priority:** the non-atomic `create_household` (🔴) is the only finding that can leave the system in an unrecoverable state (permanently un-deletable account via the `on delete restrict` FK). Fix that first; the Medium cluster (validation + service logging/scoping + tests) is a coherent second pass.
