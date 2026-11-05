# Contract — Task API (Phase II, `/api/{user_id}/tasks`)

Date: 2026-10-24. Implements spec FR-210–213, FR-211, FR-212 and the API Contract
section of the approved spec. `{"detail": ...}` envelope + `{"items": [...]}` list
envelope + partial-PUT semantics are **DECIDED — approved by user** (OQ-7,
2026-10-24 plan-correction pass), matching plan.md §OQ-7.

Common rules (apply to every endpoint below):

- `Authorization: Bearer <token>` header REQUIRED (contract `auth-jwt.md`).
- Order of checks: (1) authentication → **401**; (2) `{user_id}` path param
  compared to the token's user → **403** when mismatched, *before any DB lookup*,
  regardless of whether `{user_id}` names an existing user; (3) body validation →
  **400/422**; (4) DB access with `WHERE user_id = token_user`; missing/unowned
  task id within the token user's own namespace → **404** (never leaks another
  user's task existence; enumeration-safe).
- `Task` JSON object:

  ```json
  {
    "id": 1,
    "user_id": "usr_abc123",
    "title": "Buy milk",
    "description": "2% or oat",
    "completed": false,
    "created_at": "2026-10-24T12:00:00.000Z",
    "updated_at": "2026-10-24T12:00:00.000Z"
  }
  ```

- Validation (server-side, NFR-005): `title` required, trimmed length 1–200
  (length 200 accepted, 201 → error); `description` optional, ≤1000 chars
  (1000 accepted, 1001 → error); absent → `null` in responses; wrong JSON types /
  malformed JSON / wrong Content-Type → 400/422 with no state change; non-integer
  task `{id}` path segment → 404.

## GET `/api/{user_id}/tasks`

- Success **200** `{"items": [Task, ...]}` — only the token user's tasks (`{user_id}`
  == token user), ordered by `id`.
- 401 unauthorized/invalid token; 403 `{user_id}` ≠ token user.

## POST `/api/{user_id}/tasks`

- Request: `{"title": "...", "description": "..."}` — `description` optional
  (omitted/`null` → stored absent, returned as `null`).
- Success **201** with the created `Task` (`completed: false`; `created_at` ==
  `updated_at` == creation time).
- 400/422 validation; 401; 403.

## GET `/api/{user_id}/tasks/{id}`

- Success **200** with the owner's `Task`. Missing or unowned task id → **404**
  (`detail` wording is an implementation detail; no ownership/existence
  distinction exposed).
- 401; 403 (path user ≠ token user, before DB).

## PUT `/api/{user_id}/tasks/{id}`

- Request: `{"title": "...", "description": "..."}` — **partial update of the
  fields present**; absent fields unchanged; **empty object `{}` → 200 no-op**
  returning the task unchanged **without refreshing `updated_at`** (OQ-7
  recommendation: a no-op did not modify the task; FR-206 applies to
  modifications). `completed` is NOT updatable here (toggle endpoint owns
  completion; PDF separation) — attempts to set `completed` in a PUT body are
  rejected (400/422), not silently ignored.
- Success **200** with the updated `Task` (refreshed `updated_at` where changed;
  `created_at` never changes).
- 400/422 validation; 404 missing/unowned id; 403 path mismatch; 401.

## DELETE `/api/{user_id}/tasks/{id}`

- Success **204** no content. The task is permanently gone: subsequent GET/PUT/
  PATCH/DELETE on it (even by the same user) → 404.
- 404 missing/unowned id; 403 path mismatch; 401.

## PATCH `/api/{user_id}/tasks/{id}/complete`

- Success **200** with the `Task` whose `completed` has **flipped both ways**
  (false→true, true→false) and with refreshed `updated_at`; request body ignored
  (empty body conventional).
- 404 missing/unowned id; 403 path mismatch; 401.

## Retired routes

- `GET/POST/PATCH/DELETE /api/items[...]` — **removed in the same release**
  (OQ-2 DECIDED — approved by user: hard replace): non-existent → 404, no
  redirect shim, tests re-pointed; release notes document the change
  (constitution Principle IV).

## Non-HTTP notes

- CORS (NFR-006): only the frontend origin(s) are allowed; with Cookie
  authentication retired on the backend, `allow_credentials` is dropped.
- Secrets (NFR-001, amended per Amendment 1): `DATABASE_URL` is read from env
  only; never logged, never in error bodies. `BETTER_AUTH_SECRET` is
  frontend-only (Better Auth); the backend no longer requires it. Backend
  startup **fails fast** when the JWKS verification configuration (JWKS URL,
  issuer, audience) is unset (per the amended NFR-002).
