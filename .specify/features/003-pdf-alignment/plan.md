# Implementation Plan: PDF Alignment — Phase I & Phase II (003-pdf-alignment)

**Branch**: `003-pdf-alignment` | **Date**: 2026-10-24 | **Spec**: `.specify/features/003-pdf-alignment/spec.md`

**Input**: approved spec (user-approved 2026-10-24). This is the PLAN stage only —
no source, test, dependency, DB, or env changes were made; nothing installed or
migrated; nothing committed.

> **Amendment 1 — approved by user (plan-correction pass, 2026-10-24)**: All open
> questions OQ-1…OQ-8 are **DECIDED — approved by user** (recorded below). The JWT
> mechanism is **OQ-8 Option A (RS256/JWKS, plugin-native)**. The PDF says the
> backend verifies JWTs with the shared secret `BETTER_AUTH_SECRET`; the installed
> better-auth 1.7.5 JWT plugin supports asymmetric signing only. By user decision
> (OQ-8 = A) the backend verifies via the plugin's JWKS public key. The goals
> (stateless verification, user_id match, 401 on invalid token, per-user isolation)
> are unchanged. See also the matching amendment in `spec.md`.

## Summary

Align both phases with the Hackathon PDF. Phase I: the console CLI gains a required
`title` + optional `description` model, an Update feature, and a two-way
Complete/Incomplete toggle, with documented legacy commands preserved. Phase II:
the `todo_item` table grows `title`, `created_at`, `updated_at` (description becomes
optional, capped at 1000); the API moves to six endpoints under
`/api/{user_id}/tasks` with owner-only access (403-before-DB ownership rule); auth
switches from session-cookie verification to Better Auth JWT-provider Bearer tokens
(verified by FastAPI against the plugin's published JWKS public key — OQ-8 Option A,
DECIDED — approved by user); the Next.js frontend
exposes all five features (add/view/edit/delete/toggle) responsively, attaches the
Bearer token to every API call, and handles 401 by rerouting to login; the Next.js
16 upgrade runs as an isolated, rollback-able step. Every user story proceeds
test-first per constitution Principle II.

## Technical Context

**Language/Version**: Python 3.13+ (`pyproject.toml`, unchanged per NFR-008);
TypeScript (frontend, Vitest 3.2 + React 19 Testing Library).

**Primary Dependencies**: FastAPI + SQLModel + uvicorn + httpx (backend; add
`pyjwt[crypto]` for JWT verification — approval at implement stage); Next.js 15.5.x
(upgrade to 16+ as own step — OQ-4), better-auth 1.7.5 (installed; JWT plugin
AS-RESEARCHED — asymmetric JWKS), drizzle-orm + postgres (frontend DB access).

**Storage**: existing PostgreSQL (Neon; shared by frontend and backend), SQLite
(test fixtures). **No new backend tables**; one frontend/Better-Auth-side `jwks`
table needed for OQ-8 Option A (approval required).

**Testing**: pytest-style `unittest` suites in `tests/` (54 tests), Vitest in
`frontend/src` (26 tests), CLI exercised via REPL harness (6 tests).

**Target Platform**: local dev (backend :8000, frontend :3000 through same-origin
Next.js rewrite), Vercel-like hosting out of scope (per spec Out of Scope).

**Constraints**: work only inside `src/todo_app` (constitution); text-in/text-out
CLI protocol (Principle V); test-first ordering (Principle II); DB schema change
requires explicit user approval before execution (spec FR-208).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after design below.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-First | PASS | Spec approved at Spec gate; this plan implements only FR-101–FR-234 from it. |
| II. Test-First | PASS | §Test-First strategy orders failing tests per user story before implementation; tests are presented for approval at the task gate. |
| III. Lifecycle & gates | PASS | This is the Plan stage; Tasks stage only starts after plan review approval; no tasks created here. |
| IV. Versioning/breaking changes | PASS (noted) | `/api/items` removal, route-shape change, cookie-path retirement are breaking; per spec they're covered by OQ-2/OQ-3 decisions + release-notes documentation. Constitution semver governs the project version, not runtime artifacts; plan proposes documenting the breaking moves in release notes at Implement. |
| V. Simplicity & CLI usability | PASS | No speculative constructs (no Alembic, no new frameworks); CLI stays text-in/text-out, stdout/data + stderr/errors preserved. |
| Constraints (Python 3.13+, uv, `src/todo_app` layout) | PASS | NFR-008 honored: no runtime/manager/build-backend/layout change. One *dependency add* (`pyjwt[crypto]`) inside the existing uv-managed `pyproject.toml` — identical in kind to every other dependency add; not a manager/backend change. |

**No constitution violations to justify in Complexity Tracking.**

## Project Structure

### Documentation (this feature)

```text
.specify/features/003-pdf-alignment/
├── spec.md           # approved at Spec gate
├── plan.md           # this file
├── research.md       # OQ-8 evidence + inquiries from installed sources
├── data-model.md     # schema delta + migration plan (described only)
└── contracts/
    ├── tasks-api.md  # six endpoints' contract
    └── auth-jwt.md   # Bearer-token verification contract
```

`tasks.md` is NOT created here (created later by the Tasks stage after plan approval).

### Source Code (repository root)

```text
src/todo_app/
├── store.py          # +title/description/update()/toggle(), timestamps
├── __init__.py       # CLI: add <t>[ | d], update, toggle, list w/ status, legacy aliases
├── models.py         # TodoItem += title, created_at, updated_at; description optional
├── auth.py           # get_current_user → JWT Bearer verification via JWKS (RS256),
│                     #   fail-fast check that JWKS URL/issuer/audience config is present
├── database.py       # unchanged
└── api/
    ├── app.py        # router swap (tasks router), CORS/NFR-006 tightening, fail-fast config check
    ├── items.py      # REMOVED (OQ-2)
    └── tasks.py      # NEW: six endpoints under /api/{user_id}/tasks
tests/                # rewritten/extended per §Test-First strategy

frontend/
├── auth.ts           # + jwt plugin (config per OQ-8 decision), session tables unchanged
├── next.config.js    # rewrite retargeted to /api/:path* → backend
├── src/lib/schema.ts # + jwks pgTable (OQ-8 Option A, approval before DB execution)
├── src/lib/api.ts    # Bearer-token client, /api/{user_id}/tasks paths, 401 handling
├── src/lib/token.ts  # NEW: token acquisition/caching (GET /api/auth/token)
└── src/components/TodoList.tsx  # add(title+desc)/edit/toggle/delete, responsive
```

**Structure Decision**: unchanged single repo with `src/todo_app` (backend) and
`frontend/` — constitution-mandated layout stays.

## Architecture — requirement mapping

| FR(s) | Plan section |
|-------|--------------|
| FR-101–108 (Phase I) | §Phase I console plan |
| FR-201–207 (data model) | §Data model & migration (details in `data-model.md`) |
| FR-208 (migration discipline) | `data-model.md` §Migration, backup, rollback |
| FR-210–213 (REST API) | §API plan + `contracts/tasks-api.md` |
| FR-220–229 (JWT bearer auth) | §Auth plan + `contracts/auth-jwt.md` + §OQ-8 |
| FR-230–234 (frontend) | §Frontend plan |
| NFR-001–008 | §Auth plan, §API plan, §Constitution check, `data-model.md` |

### Phase I console plan (FR-101–108)

`store.TodoItem` becomes `{ id, title: str, description: str | None, completed,
created_at, updated_at }` (PARITY with US2's model, per spec "same conceptual
fields"). Store API:

- `add(title, description=None)` — whitespace/empty title → `ValueError` (FR-103);
  description optional/empty allowed.
- `list_items()` — unchanged.
- `update(item_id, title, description)` — updates text fields only; `id`,
  `completed`, `created_at` unchanged; refreshes `updated_at` (FR-105/205/206).
- `toggle(item_id)` — flips `completed` both directions; refreshes `updated_at`
  (FR-107).
- `complete(item_id)` — retained exactly for legacy behavior (marks complete;
  errors when already complete — existing 19 store tests keep passing).
- `delete(item_id)` — unchanged.

CLI (`src/todo_app/__init__.py`) surface (text-in/text-out; data on stdout, errors
on stderr — Principle V):

- `add <title> | <description>` — new canonical form. Everything before `|` is the
  title, after is the description (optional/empty allowed after the separator).
  **`add <text>` with no `|` is legacy-compat: the entire text is the title** (OQ-5
  recommendation) so existing 6 CLI tests keep passing (`Added item <id>: <text>`
  echo now prints the title).
- `update <id> <title> | <description>` — same grammar; errors when the id is
  unknown ("Error: no item with that id" on stderr).
- `toggle <id>` — flips direction (prints `Toggled item <id>: <title> [complete|incomplete]`).
- `complete <id>` — retained alias = mark complete (legacy output/behavior kept per
  OQ-5; `uncomplete` not needed — `toggle` covers FR-107; can be added later only if
  the user asks).
- `list` — `id. title — description [complete|incomplete]` when a description
  exists, `id. title [complete|incomplete]` otherwise; legacy bare-text rows keep
  rendering as title with no description. Status word: the CLI's current
  `pending` becomes `incomplete` (FR-104 requires complete/incomplete
  indicators); this is the ONE existing CLI test assertion that gets explicitly
  updated in the task list (spec OQ-5 covers it). Existing
  `help` gains the new commands.
- `delete`/`exit`/`help` — unchanged behavior.

### Data model & persistence (FR-201–207)

Details in `data-model.md`. Summary: `todo_item` gains `title` (non-null, ≤200
chars), `created_at`, `updated_at` (`TIMESTAMPTZ`); `description` becomes nullable,
≤1000 chars going forward; legacy rows map losslessly (original text preserved in
`description`, title derived from its first 200 chars — OQ-1 Option 2), timestamps
backfilled. Migration is a described, approval-gated script — **nothing executes at
plan stage** (FR-208).

### API plan (FR-210–213, FR-211, FR-212, plus NFR-005)

Full contract in `contracts/tasks-api.md`.

- Router: `src/todo_app/api/tasks.py`, prefix `/api/{user_id}/tasks`, six routes
  (list, create, get, update `PUT`, delete, `PATCH .../complete`). Integer `{id}`
  path segment; non-integer → 404 (spec edge case).
- Ownership rule (FR-212), enforced by a FastAPI dependency chain that runs **before
  any DB access**:
  1. `get_current_user` (auth.py) → 401 on missing/malformed header, bad signature,
     wrong issuer/aud/alg, expired `exp` (NFR-003 allowlist), or nonexistent user
     record.
  2. `require_path_matches_user(user_id)` (generic dependency) → compares token
     user to `{user_id}` path param → mismatch **403 before any DB query**, even if
     `{user_id}` doesn't exist (spec edge case; never 404 here).
  3. Route handler queries with `WHERE user_id = token_user` always; missing /
     foreign-rooted task id → 404 (no existence leak across users).
- Validation (server-side; NFR-005): `title` required, 1–200 after trim; front/back
  boundaries accepted/rejected exactly (200 ok, 201 rejected); `description`
  optional, ≤1000 (1000 ok, 1001 rejected); wrong types → 422 (FastAPI/Pydantic);
  empty/whitespace title → 400. Malformed JSON → 400/422, no state change.
- Status codes: 201 create; 200 read/update/toggle; 204 delete (FR-211). Toggle:
  both directions flip + `updated_at` refresh (#7 in gap table).
- Error shape: `{"detail": "..."}` (FastAPI default) — OQ-7 DECIDED — approved
  by user; wording
  is an implementation detail per the spec.
- Create response: full Task JSON with `completed: false`, `created_at`,
  `updated_at`; list response envelope `{"items": [...]}` (OQ-7 DECIDED — approved
  by user,
  matches existing envelope). `user_id` included in every Task payload.
- PUT semantics (OQ-7 DECIDED — approved by user): partial update of title/description keys
  provided; `{}` → 200 no-op returning the task unchanged WITHOUT bumping
  `updated_at` (FR-206 says "whenever the task is modified"; a no-op didn't modify
  it — this is the stricter, less surprising reading). `completed` is never PUT-
  updatable.
- `/api/items` retire (OQ-2 DECIDED — approved by user): hard replace =
  same-release removal of
  `src/todo_app/api/items.py` and its router wiring, with the rewrite retargeted;
  tests re-pointed in the same release; release-notes entry only (no runtime shim).
- CORS (NFR-006): same-origin rewrite remains the only path the frontend uses;
  keep `allow_origins` minimal, drop `allow_credentials=True` when cookies are
  retired (OQ-3) — the client no longer sends cookies to the backend anyway.

### Auth plan (FR-220–229, NFR-001–004; analysis in `research.md`)

- Frontend (`frontend/auth.ts`): register the JWT plugin (server import
  `better-auth/plugins/jwt`), configured — per the installed 1.7.5 source — with
  `jwt: { expirationTime: "7d" }` (FR-226; plugin default is 15m,
  `sign.mjs:81`), `issuer`/`audience` pinned to `BETTER_AUTH_URL` origin, and
  `jwks.keyPairConfig.alg` decided in OQ-8. `nextCookies()` and session cookies
  STAY (Better Auth sessions must exist to mint tokens; `GET /token` requires a
  live session — `index.mjs:141`).
- Token acquisition (frontend, OQ-3 option 1): after login and on app (re)load, the
  client calls `GET /api/auth/token` (handled by the existing `/api/auth/[...all]`
  route) with the session cookie; response `{ token }` per `index.mjs:141-158`.
  Token kept in **memory only** (module-scoped store, `src/lib/token.ts`) — no
  localStorage/sessionStorage (XSS-surface minimization, OQ-3 trade-off).
- Header attach (FR-221): `src/lib/api.ts` reworked to the new task paths with
  `Authorization: Bearer <token>` on **every** call; token obtained via
  `getToken()`; all functions route through one `request()` helper that on 401
  triggers reauth (FR-233).
- 401 handling (US4-6): on any 401 the client invalidates the in-memory token,
  attempts one silent `GET /api/auth/token` re-fetch (covers reload cases), and if
  that fails (no live session) redirects to `/login` (spec FR-233, US4 scenario 6).
- Backend (`src/todo_app/auth.py`): `get_current_user` re-implemented as Bearer JWT
  verification:
  - Parse `Authorization: Bearer <jwt>`; anything else → 401.
  - Verify signature against the JWKS published by the frontend Better Auth server
    (`PyJWKClient` against `JWT_JWKS_URL` = `BETTER_AUTH_URL` + `/api/auth/jwks`;
    env-overridable), **algorithms allowlist enforced (no `alg: none`)**
    (NFR-003), plus `exp` (leeway per OQ-7 clock-skew recommendation: 60s),
    `iss`, `aud` exact matches.
  - Extract `sub` (Better Auth user id — `sign.mjs:125` evidence) and load the
    `User`; missing user → 401 (spec edge case: token valid but user gone).
  - Startup fail-fast: refuse to start when the **JWKS verification config is
    missing** — the JWKS URL (default `BETTER_AUTH_URL` + `/api/auth/jwks`,
    env-overridable), the issuer, and the audience (OQ-8 Option A, DECIDED —
    approved by user). `BETTER_AUTH_SECRET` is **frontend-only** from now on:
    the backend no longer requires or reads it (the secret stays shared with
    Better Auth's own key-encryption/JWT config on the Next.js side only).
  - Cookie/session-token verification path and `SESSION_COOKIE_NAME` +
    `session_token_from_cookie` helper retired in the same release (OQ-3
    DECIDED — approved by user), tests rewritten per §Test-First.
  - **JWKS caching & failure behavior (OQ-8 Option A):**
    - Keys are cached **in memory** after the first successful `GET {JWKS_URL}`
      fetch; the cache is keyed by `kid`.
    - On an unknown `kid` (Better Auth key rotation), the client refreshes the
      JWKS document **once** per request and retries verification; a
      still-unknown `kid` after refresh → 401.
    - If the JWKS endpoint is unreachable on first use (no cache yet) →
      **HTTP 503** (`{"detail": "..."}`) — the token could not be verified
      through no client fault; the endpoint is safe to retry. If unreachable
      during refresh-on-unknown-`kid` (stale cache exists) → also **503**,
      never a fallback to stale-key acceptance or 404. Verification never
      silently downgrades (no `alg`/`kid` fallbacks).
    - A small TTL may refresh the cache proactively; correctness never depends
      on TTL alone (unknown-`kid` refresh is the authoritative trigger).
- Register/login/logout pages and routes untouched (FR-229, FR-234) — they keep
  operating on Better Auth sessions so tokens can be minted.

### OQ-4 — Next.js 16 upgrade as an isolated step (FR-230) — DECIDED — approved by user: INCLUDED

Included in scope, as its own isolated task **after** JWT/frontend behavioral work
(or, if the user prefers, as the very first frontend step) — with a strict
procedure: upgrade `next` (+ any required `react` pairing change) in
`frontend/package.json`, run `npm install`, then immediately verify `npm test`,
`npm run build`, and the app boots; **rollback = restore the committed
`package-lock.json` + `package.json` and re-run `npm install`**. Nothing else may
be bundled into that task. `nextCookies()` / better-auth integration and the
Vitest setup are the listed risk points; if 16.x blocks a suite, fix or defer the
upgrade and record the deviation — PDF parity requires 16+, so deferring is a
spec-visible decision, made at that point, not silently.

## Open questions — decisions (ALL DECIDED — approved by user, 2026-10-24)

Every item below is recorded with its decision. The Tasks stage can start, but
only after THIS document passes the plan-review approval gate.

### OQ-1 — Legacy-row migration strategy — DECIDED — approved by user

- **DECIDED — approved by user: Option 2.** Whole legacy text stays in `description`;
  `title`
  derived as its first ≤200 chars; `created_at = updated_at = migration-time`.
  Fully lossless; non-obvious titles acceptable (spec-endorsed).
- **Option 3**: whole text in `description`, `title = "Task <id>"`. Equally
  lossless; uglier titles forever until manual cleanup. (Not chosen.)
- **Option 1 (whole-text-to-title = TRUNCATION) — rejected at Spec gate**; listed
  for completeness only.
- Over-long legacy `description` (>1000 chars): **DECIDED — approved by user:**
  legacy rows are exempt from the 1000 cap (cap applies to API writes only) so no
  data is ever truncated.
- Timestamps backfill: **DECIDED — approved by user:** `now()` at migration time
  for both columns (FR-208's example).

### OQ-2 — Retiring `/api/items` — DECIDED — approved by user

- **DECIDED — approved by user: hard replace `/api/items` in the same release**
  (equivalent to Option 3): clean, matches the spec's "PDF compliance does not
  forbid keeping a shim, but nothing needs one"; the only callers of `/api/items`
  are our own tests and the rewritten client.
- **Option 1 without shim only**: same as 3 in practice here. (Not chosen.)
- **Option 2 deprecation shim**: only relevant for external consumers; none are
  known; adds dead code (Principle V anti-pattern). (Rejected.)

### OQ-3 — Cookie/session retirement + token storage & attachment — DECIDED — approved by user

- **DECIDED — approved by user: same-release cookie retirement; token held in
  client memory and attached as `Authorization: Bearer` by the client.**
- Retirement timing detail: same-release removal of the FastAPI cookie path
  (no dual-accept transitory). The deployment is a demo stack, the cookie path
  becomes dead weight, and the PDF mandates pure Bearer — simpler per
  Principle V. `frontend auth.ts` `nextCookies()` stays (Better Auth session
  mechanics are needed by the JWT plugin and Better Auth routes); only backend
  `get_current_user`'s cookie branch disappears.
- Token storage/attachment detail: client attaches the header; token in memory
  only (`src/lib/token.ts`) — direct PDF wording, minimal code; trade-off
  accepted: token is readable from JS (XSS, mitigated in-memory only, no
  persistent storage).

### OQ-4 — Include the Next.js 15.5 → 16+ upgrade? — DECIDED — approved by user: INCLUDE

- **DECIDED — approved by user: include**, as an isolated, rollback-able step —
  PDF (source of truth) says Next.js 16+; isolated step
  with rollback (`package-lock.json` restore) and suite-blocking verification
  (spec §OQ-4 isolation rule).
- Defer: rejected — leaves the repo in visible non-conformance to the PDF's
  stack clause; keeps risk out of this feature but multiplies rework later.

### OQ-5 — Tests impact + Phase I legacy-compat grammar — DECIDED — approved by user

- Backend 54: `test_api.py` 15 → rewritten for `/api/{user_id}/tasks` (plus
  additions for boundaries/ownership/timestamps); `test_auth.py` 9 → rewritten for
  JWT bearer verification (fixture-minted test tokens; JWKS fetch mocked);
  `test_store.py` 19 + `test_cli.py` 6 keep passing where they encode legacy
  behavior (explicit exception: the one `pending`-wording assertion in
  `test_cli.py` updates to `incomplete` per FR-104), extended with new failing
  tests for update/toggle/two-field adds; `test_models.py` 5 extended for new
  columns & timestamps.
- Frontend 26: `TodoList.test.tsx` 7 → rewritten for title+desc add, edit, toggle
  (both directions), delete, 401 redirect; `api.ts` test coverage added for the
  Bearer header on every call; `auth-cookies` (3) + `auth-handler` (7) +
  `require-session` (2) minimally touched — the Better Auth session layer
  survives, only the token-acquisition piece is added; `AuthForm` 6, `logout` 1
  unaffected.
- CLI grammar: **DECIDED — approved by user:** legacy `add <text>` = whole text
  as the title (every existing line keeps working with zero wording change); the
  canonical title+description form uses a `|` separator.
- `complete <id>`/`toggle <id>`: **DECIDED — approved by user:** keep `complete`
  as an alias (= mark complete, errors when already complete, legacy output kept),
  add `toggle` as the PDF feature (spec's PRINCIPLE is that every documented
  legacy command keeps working — this plan preserves them verbatim).

### OQ-6 — PDF's endpoint-path inconsistency (informational) — DECIDED — approved by user

- **DECIDED — approved by user: keep `/api/{user_id}/tasks`.** Rationale recorded
  in the spec §OQ-6 (endpoint table is authoritative over the illustrative
  example).

### OQ-7 — Remaining details bundled here (ALL PARTS DECIDED — approved by user)

- Error envelope: **DECIDED — approved by user: `{"detail": "..."}`** (FastAPI
  default everywhere, including validation).
- List envelope: **DECIDED — approved by user: `{"items": [...]}`** (matches the
  existing pattern and makes `TodoList` iteration identical to today).
- PUT semantics: **DECIDED — approved by user: partial update; `{}` → 200 no-op
  returning the task unchanged, WITHOUT bumping `updated_at`** (FR-206's
  "modified" read strictly; a no-op didn't modify the task).
- Clock skew (edge case): **DECIDED — approved by user: 60s clock-skew leeway**
  at verification time (PyJWT `leeway`; tiny, bounded).
- Table rename: **DECIDED — approved by user: keep the table name
  `todo_item`** (PDF constrains field names and API paths, not table names;
  renaming is pure migration risk — revisit in Phase III).

### OQ-8 — JWT algorithm/key mechanism — DECIDED — approved by user: OPTION A

From the installed better-auth 1.7.5 source: the JWT plugin signs ONLY with
asymmetric keys (types union `EdDSA | ES256 | ES512 | PS256 | RS256` —
`types.d.mts:217`-232, `sign.mjs:67`), stored in a DB `jwks` table
(`schema.mjs:2`), published at `GET /jwks` (`index.mjs:45`). **Shared-secret HS256
verification is NOT supported by the plugin as installed.** Therefore FR-222's
"shared secret" literal wording must be realized as one of:

- **DECIDED — approved by user: Option A (RS256 asymmetric via the plugin's
  native JWKS; the backend verifies with the public key).**

- **Option A (richer, plugin-native — CHOSEN)**: asymmetric signing, choosing
  `jwks.keyPairConfig.alg = "RS256"` for the most portable Python-side
  verification (EdDSA/Ed25519 also works with PyJWT[crypto]; less battle-hardened),
  FastAPI verifies via `PyJWKClient` against `GET /api/auth/jwks`, algorithms
  allowlisted. Consequences: **`(1)` new `jwks` table = DB schema change — remains
  an APPROVAL-GATED TASK (backup + explicit user approval before any DB schema
  change executes); `(2)` new backend dependency `pyjwt[crypto]` — also remains an
  approval-gated task; `(3)` backend verification depends on the frontend being
  reachable for JWKS (cached with refresh-on-unknown-kid; unreachable JWKS →
  503, see §Auth plan).** Backend config is now the **JWKS URL + issuer +
  audience** (NOT the shared secret); the startup fail-fast checks that JWKS/iss/
  aud config is present. `BETTER_AUTH_SECRET` stays **frontend-only** (used by
  Better Auth for its own key encryption/secret config on the Next.js side; the
  backend no longer requires it). Issuer/audience claims pinned to the
  `BETTER_AUTH_URL` origin, configured on both sides to match.
- **Option B (not chosen — persistent literal reading)**: use the plugin's documented escape
  hatch `jwt.sign` (a custom signing callback — `types.d.mts:161`) which signs
  HS256 with `BETTER_AUTH_SECRET` (jose `importHS256`-style). FastAPI then verifies
  HS256 against the shared secret directly — exactly the PDF's "shared secret"
  wording, no `jwks` table, no JWKS dependency. Trade-offs: `(1)` non-primary path
  (written for remote-KMS signing — we'd sign with a local secret in a callback);
  `(2)` requires the placeholder `jwks.remoteUrl` option (`index.mjs:24` throws
  otherwise) — awkward-but-supported; `(3)` header `kid` semantics become ours to
  manage; `(4)` no plugin-native rotation. Strictly smaller change surface, less
  conventional flow.
- **Option C (rejected)**: backend decrypts private `jwk` rows from the shared DB
  — fragile, re-implements Better Auth's secret-derived key encryption, blocks
  rotation.
- With **either** Option A or B, `jwt.expirationTime: "7d"` (FR-226) and
  `issuer`/`audience` config are identical; only verification mechanics differ.
- (Note: Option A introduces a JWT verification dependency on better-auth's
  exact token shape as installed — 1.7.5 — matching the installed version's
  behaviors as documented in research.md.)

## Frontend plan (FR-230–234)

- `src/lib/api.ts` → rewritten around the new endpoints: type
  `TodoItem` becomes `{ id, user_id, title, description: string | null, completed,
  created_at, updated_at }`; functions `listTasks(userId)`, `createTask(title,
  description?)`, `getTask(userId, id)`, `updateTask(userId, id, {title?,
  description?})`, `deleteTask(userId, id)`, `toggleTask(userId, id)`; one shared
  `request()` attaches `Authorization: Bearer <token>` (from `src/lib/token.ts`)
  and treats 401 via `handleUnauthorized` (invalidate token, one re-fetch attempt,
  else `router.push("/login")`). The `userId` used is the session user's id from
  Better Auth (available server-side today; passed to the client page from
  `requireSession` + rendered as-is into the fetch path — exact wiring detail at
  Implement).
- `next.config.js`: rewrite becomes `source: "/api/:path*" → destination:
  http://127.0.0.1:8000/api/:path*` (static "me"/user-id segment is in the URL the
  client constructs; the rewrite stays a plain prefix proxy; Bearer headers pass
  through).
- `TodoList.tsx`: add form with `Title` + optional `Description` fields
  (client-side empty-title guard to give the instant inline validation message
  spec'd in US4-2 and stay responsive), per-item Edit (inline form: title +
  description pre-filled; Save = `updateTask`, Cancel reverts), per-item Toggle
  (flips either direction and shows the resulting `[complete|incomplete]`
  indicator), per-item Delete (US4-5), status indicators kept (FR-232
  feature parity with the CLI's View). 401 → `router.push("/login")` as today.
- Responsive (FR-231): task rows compress gracefully under ~640px — form controls
  stack vertically; each task item fully operable without horizontal scrolling;
  verified manually + a Vitest test asserting the responsive class hooks exist
  (behavioral DOM contract kept minimal — no guessed framework CSS additions
  beyond what exists).
- `token.ts` (new): `getToken()` (one in-flight request memoized per burst),
  `invalidateToken()`, on-miss re-fetch against `GET /api/auth/token`; callers
  never see raw fetch+cookie handling — testable in isolation.
- Frontend tests per §Test-First (TodoList.test.tsx rewrite + api.ts/token.ts
  additions). Auth pages/register/login/logout touched only as needed for JWT
  sanity (they should not be — Better Auth owns those paths and stays).

## Test-First strategy (NFR-007, constitution Principle II)

Ordering rule: write the tests, get approval, THEN implement. Within each story,
tests come before that story's code; stories run in the order below because each
later suite depends on the earlier story's surfaces.

1. **US1 store/CLI (failing tests first)**
   - `tests/test_store.py` additions: `add(title, description)` valid/shapes;
     empty-title rejection; optionally-empty description; `update()` rewrites
     title+description, keeps id/completed/created_at, refreshes updated_at;
     `toggle()` flips both directions; existing 19 tests pass unmodified.
    - `tests/test_cli.py` additions: `add T | D`, bare `add T`, empty `add` error;
      `update`; `toggle` (both directions); `complete` alias retained; `list`
      rendering incl. description-bearing rows; `help` shows new commands; legacy
      flows' text unchanged except the ONE pre-arranged wording update
      (`pending` → `incomplete`, see also OQ-5).
2. **US3 auth/tests-before-interfaces (before any backend code)**
    - `tests/test_auth.py` rewritten: no token → 401 on all six paths;
      malformed `Authorization` → 401; wrong-signature token → 401; expired →
      401 (fixed-time test with `datetime` patch/leeway boundary); unknown `kid`
      → 401; wrong issuer/aud/alg → 401; valid token → user extracted; user row
      missing → 401; JWKS env/config missing (URL/issuer/audience) → fail-fast
      at app creation (a startup test asserting the raise); JWKS fetch mocked at
      the client boundary (no network in tests).
    - JWKS caching/failure tests (OQ-8 Option A — matching §Auth plan behavior):
      keys cached after first fetch (second verification does no HTTP); unknown
      `kid` → one refresh then verify or 401; unknown `kid` with JWKS endpoint
      unreachable → 503; first-verification JWKS unreachable → 503; no
      fallback to stale keys or `alg` `kid` downgrade.
    - Test JWT minting: PyJWT-issued fixture tokens matching better-auth claims
      (`sub`, `exp`, `iss`, `aud`, `kid`) signed with an in-test test key
      (RSA + stub JWKS — Option A, DECIDED) — no DB access or network.
3. **US2 API/tests-on-the-contract**
   - `tests/test_api.py` re-pointed & extended (httpx + fresh in-memory SQLite per
     test, as today; auth through bearer fixtures from #2): six-endpoint matrix
     (list/create/get/update/delete/toggle per contract), 201/200/204/401/403/404
     codes; **ownership rule**: caller's own `{user_id}` → owner's data only;
     foreign `{user_id}` → 403 *before* DB (provable: foreign user_id that DOESN'T
     exist in users table still 403, never 404); unknown task id → 404 (even when
     that id exists for another user — no enumeration leak); validation
     boundaries (title 200/201, description 1000/1001, whitespace title, wrong
     types, malformed JSON); `{}` PUT no-op retains updated_at; partial PUT
     updates given field + refreshes updated_at; created_at immutable; toggle
     both directions; per-user isolation across two users; non-integer id → 404;
     corrupt `{user_id}` sanity via the 403 rule.
   - `tests/test_models.py` extended: new columns exist; created_at set on add
     and never changed; updated_at changes only on modify.
4. **Migration test (US5, before the migration script exists)**
   - New `tests/test_migration.py`: seed legacy rows (description only), run the
     (to-be-built) migration function, then assert zero text lost
     (`title in description` prefix guarantee + description byte-equality), title
     ≤200, timestamps non-null, idempotency guard (running twice changes nothing);
     and-after rows satisfy FR-205/206. Run against the real Postgres? No —
     SQLite with the same DDL; the Postgres run is the approved manual execution.
5. **US4 frontend (failing tests first)**
   - `frontend/src/components/__tests__/TodoList.test.tsx`: rewrite for
     add-with-two-fields (UI blocks empty title pre-request), list with both
     fields + status, edit (open, change, save → API called with both fields;
     cancel reverts), toggle (both directions), delete; 401 → routes to /login;
     responsive hooks assertions as per architecture.
   - `frontend/src/lib/__tests__/api.test.ts` (new): every function sends
     `Authorization: Bearer <token>`, correct method/path, JSON body, 401 path
     behavior; `frontend/src/lib/__tests__/token.test.ts` (new): single-flight
     token acquisition + invalidation.
   - Existing suites: expect no changes needed for `AuthForm`, `logout`,
     `auth-handler`, `require-session`, `auth-cookies` (session layer retained);
     if any must change, change them at that step rather than preemptively.
6. **Final verification**: whole backend suite ≥ current 54-equivalent green;
   frontend suite green; `uv run todo-app` manual flows; two-browser isolation
   sanity.

## Implementation ordering & risk list

ALL OQ decisions above are DECIDED — approved by user. Any deviation re-enters
this ordering.

**Ordering safety (Correction 1, mandatory):** between step 1 (model columns
added in code — `TodoItem` gains `title`/`created_at`/`updated_at`) and the
approved migration (step 3), the app **MUST NOT be run against the real Neon
database** (the code's new non-null columns do not exist in the live `todo_item`
table yet). All tests MUST use an isolated database (in-memory/temporary SQLite
per the existing test fixtures) during this window; nothing points
`DATABASE_URL` at Neon until the migration has run with approval.

1. **Foundation — backend security/model**: add `pyjwt[crypto]` dep
   (approval-gated task); implement `TodoItem` columns; implement
   `get_current_user` JWT path (JWKS/RS256 per OQ-8 Option A); fail-fast check
   that the JWKS URL/issuer/audience config is present; tasks router with all
   six handlers + ownership rule; delete `items.py` router (OQ-2). Verify:
   `pytest tests/` green (fresh-DB tests don't hit legacy data). *Risk*:
   JWKS-URL reachability in CI — mitigated by the mocked JWKS boundary in
   tests; real verification exercised in the manual checklist below.
2. **CLI/store (US1)**: implement store update/toggle + new fields, CLI grammar.
   Verify: `pytest tests/test_store.py tests/test_cli.py` green.
3. **Migration (US5)**: create `data migration script` + backup instructions per
   `data-model.md`; **get explicit user approval for DB-schema execution — then
   execute with backup** (never in a test). Verify script's idempotency test
   + using a copy of a real-ish dump if provided.
   **Precondition (Correction 2 — clean-git gate):** the migration gate's
   clean-git requirement cannot be satisfied literally (repo has no commits
   yet), so it is replaced by: **User-authorized LOCAL initial commit (no push)
   before the migration. `.env`/`.env.local` are already gitignored. No commit
   is made without explicit user authorization.**
4. **Frontend infra**: Next.js 16 upgrade task (OQ-4, isolated, rollback-able);
   `auth.ts` jwt-plugin config + `schema.ts` jwks table definition (the table
   CREATION is the approval-gated DB change executed with the backend migration
   or right after; backup + explicit user approval before any DB schema
   change); rewrite retarget in `next.config.js`; `token.ts` + `api.ts`
   rewrite. Verify: `npm test`, `npm run build`.
5. **TodoList UI (US4)**: two-field add form + inline edit + toggle/delete; 401
   reauthentication; responsive classes. Verify: `npm test` green + manual.
6. **E2E verification** (checklist below), release-notes pass (breaking changes
   documented per Principle IV), update README/CLAUDE-adjacent docs **only** if
   their current wording misinforms about THIS feature's behavior (full doc
   overhaul is Out of Scope per spec).
   **Task-to-be (Amendment 1): document the OQ-8 deviation in the README** —
   the README's auth section must state that the backend verifies Better Auth
   JWTs via the plugin's JWKS public key (RS256) rather than literally "the
   shared `BETTER_AUTH_SECRET`", because the installed better-auth 1.7.5 JWT
   plugin supports asymmetric signing only (see the deviation note in
   `spec.md` Amendment 1).

Risky points & mitigations:

| Risk | Mitigation |
|------|-----------|
| Code/schema mismatch window (Correction 1): steps 1–2 run with new model columns in code while the real Neon DB lacks them; accidentally running the app against Neon in this window breaks on missing columns / corrupts expectations | Enforced ordering rule: app MUST NOT run against the real Neon DB until the approved migration (step 3) completes; ALL tests use isolated (in-memory/temporary) databases; `DATABASE_URL` in test/dev fixtures points at ephemeral SQLite only |
| JWKS availability (backend boot / first verification) | JWKS cache + refresh-on-unknown-kid; only the frontend origin is needed and it runs in the same dev stack; tests mock JWKS |
| SQLModel `create_all` doesn't alter legacy DBs | Migration script handles pre-existing DB; fresh DBs get the full new schema; deployment order documented (migrate → then restart) |
| better-auth claim shape drift vs plan claims | Claims pinned to evidence (sub/iss/aud/exp); exact configurables written in contracts/auth-jwt.md; integration test posts real login→token→API flow in the manual checklist |
| Next.js 16 breaking behavior | Upgrade is step-isolated with commit-restore rollback; suites must pass before the next task starts |
| `/api/items` removal breaking an unknown consumer | Release notes + grep-verified only internal callers (client + tests) |
| 403-before-DB rule accidentally descending | Ownership check lives in a dedicated dependency invoked first in the handler signature order; a fallback test asserts a nonexistent foreign user_id gets 403 |
| Migration data loss | Backup mandatory (pg_dump copy); lossless mapping test; no truncation |

## Final manual/browser verification checklist

Backend up (frontend JWKS reachable + JWKS URL/issuer/audience config set +
`DATABASE_URL` set, migrated DB) — `BETTER_AUTH_SECRET` is needed by the
frontend only (Better Auth), not the backend; frontend up:

1. Register a new user (both desktop & narrow viewport) → logged in; Todo list
   loads empty.
2. Add task "Title A" + description "Longer note A" → appears incomplete,
   persisted (refresh keeps it — persistence in DB survives restart too).
3. Edit task A's title/description → list reflects it; `updated_at` visibly
   newer, `created_at` unchanged (spot-check via API if desired).
4. Toggle task A → complete; toggle again → incomplete; indicator flips both
   ways.
5. Delete task A → gone (refresh + re-login confirm).
6. Second browser/incognito user B: register, adds "B's task" — cannot see A's
   tasks; direct call `/api/<A_id>/tasks` as B → 403; typo'd non-existent user_id
   → 403; task GET of a foreign owner's task id → 404, never data.
7. 401 paths: curl without header → 401; forged-token curl → 401; expired-token
   curl → 401; then leave browser idle past the expiry — UI reroutes to login
   (FR-226/US4-6; may require shortening `expirationTime` for the demo).
8. Logout → `/login`; re-login mints fresh tokens; task list is unchanged
   (persistence across sessions — FR-207).
9. `uv run todo-app` CLI: add "T1" | "D1" → listed; `update 1 T1' | D1'` →
   reflected; `toggle 1`/`toggle 1` completes + uncompletes; delete 1; legacy
   flows (`add Legacy`, `complete`) still work.
10. Conformance spot-check: exactly six endpoints respond under
    `/api/{user_id}/tasks`; `/api/items` returns 404.

## Files created or modified (PLAN stage)

Created (all under `.specify/features/003-pdf-alignment/`):

- `.specify/features/003-pdf-alignment/plan.md` — this document.
- `.specify/features/003-pdf-alignment/research.md` — OQ-8 + installed-package research.
- `.specify/features/003-pdf-alignment/data-model.md` — schema delta + migration plan (described; not executed).
- `.specify/features/003-pdf-alignment/contracts/tasks-api.md` — six-endpoint contract.
- `.specify/features/003-pdf-alignment/contracts/auth-jwt.md` — Bearer/JWT verification contract.

Modified:

- **Plan-correction pass (2026-10-24, per `docs/fix.txt` — decisions recorded,
  documents amended; no source, tests, DB, deps, package, or env files
  touched; nothing installed, migrated, committed, or pushed; no tasks
  created):**
  - `.specify/features/003-pdf-alignment/plan.md` — OQ-1…OQ-8 marked
    DECIDED — approved by user (with the approved choices); Amendment 1 note
    (OQ-8 = A deviation record); auth-plan/backend-config rework (JWKS URL +
    issuer + audience fail-fast; `BETTER_AUTH_SECRET` frontend-only); JWKS
    caching/failure behavior (503 on unreachable JWKS) + matching tests added
    to the test-first list; jwks-table/`pyjwt[crypto]` kept as approval-gated
    tasks; ordering-safety rule (no real-DB runs before the approved migration;
    isolated test DBs only) added as a risk with mitigation; clean-git-gate
    precondition (user-authorized LOCAL initial commit, no push) added; README
    documentation task-to-be added; checklist env wording updated.
  - `.specify/features/003-pdf-alignment/spec.md` — Amendment 1 block added
    (deviation note, FR-222/NFR-002/Auth Flow updated as worded), §OQ-8
    decision recorded, `BETTER_AUTH_SECRET` assumption amended, footer note
    added; Status still "Draft — awaiting user review".
  - `.specify/features/003-pdf-alignment/contracts/auth-jwt.md` — Option A
    chosen; startup fail-fast re-specified to the JWKS/issuer/audience config;
    JWKS caching & failure contract specified (cache by `kid`, one
    refresh-on-unknown-`kid`, 503 when the JWKS endpoint is unreachable, no
    downgrade); option statuses updated.
  - `.specify/features/003-pdf-alignment/contracts/tasks-api.md` — OQ-7/OQ-2
    decisions recorded; NFR-002 fail-fast wording amended (JWKS config,
    `BETTER_AUTH_SECRET` frontend-only).
  - `.specify/features/003-pdf-alignment/data-model.md` — Option A chosen for
    §4 (approval gating preserved); Correction-2 clean-git precondition added
    to §3; table-name decision recorded; §6 env-consumption note amended.
  - `.specify/features/003-pdf-alignment/research.md` — OQ-8 decision record
    added (Option A chosen; Option B not chosen).

No other files anywhere in the repository were changed. No commits were made.

**STOP — awaiting your plan-review approval before proceeding to the Tasks
stage.**
