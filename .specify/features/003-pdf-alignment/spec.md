# Feature Specification: PDF Alignment (Phase I & Phase II)

**Feature Branch**: `003-pdf-alignment`

**Created**: 2026-10-24

**Status**: Draft — awaiting user review (Spec gate; Amendment 1 applied, see below)

**Input**: User description: "An audit showed the repo diverges from the official Hackathon PDF. The PDF is the source of truth. Write a spec that aligns Phase I and Phase II with the PDF requirements: Phase I console app with 5 basic features and tasks with title (required) + description (optional); Phase II full-stack app with id/user_id/title/description/completed/created_at/updated_at task fields, `/api/{user_id}/tasks` REST endpoints, Better Auth JWT-plugin Bearer-token auth verified by FastAPI using the shared `BETTER_AUTH_SECRET`, and a responsive Next.js 16+ frontend exposing all 5 features. SPECIFY stage only — no code, tests, or migration changes."

**Source of truth**: The official Hackathon PDF (not in the repo). Requirements in this document are restated from the PDF via `docs/fix.txt`; not verified verbatim — the PDF itself is the source of truth. Where the current implementation diverges, the PDF wins.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phase I CLI: Manage Tasks with Title and Description (Priority: P1)

A Phase I console user adds a task providing a required title and an optional description, lists all tasks with status indicators, updates a task's details, deletes a task by ID, and toggles a task between complete and incomplete — all five basic features work through the console app, which remains functional and backward-compatible where possible.

**Why this priority**: Phase I is a deliverable in its own right and its five features are the baseline the Phase II stack must mirror. The title+description data shape introduced here is the foundation of the shared task model.

**Independent Test**: Run the console app, add a task with a title and description, list, update, toggle, delete, and verify all outcomes. Delivers a PDF-conformant standalone Phase I.

**Acceptance Scenarios**:

1. **Given** the console app, **When** the user adds a task with a title and (optionally) a description, **Then** the task is created with an ID, the title is persisted, and the description is persisted as provided (empty allowed).
2. **Given** the console app, **When** the user attempts to add a task with an empty or whitespace-only title, **Then** the task is not created and a clear error is reported.
3. **Given** existing tasks, **When** the user lists tasks, **Then** every task is shown with its ID, title, (optional) description, and a status indicator (complete/incomplete).
4. **Given** an existing task, **When** the user updates its details (title and description), **Then** the stored task reflects the new details while its ID and completion status are preserved.
5. **Given** an existing task, **When** the user deletes it by ID, **Then** it no longer appears in the list.
6. **Given** an existing task, **When** the user toggles its completion status, **Then** an incomplete task becomes complete and a complete task becomes incomplete.

---

### User Story 2 - Phase II API: Task CRUD under /api/{user_id}/tasks (Priority: P1)

A frontend (or any authorized client) performs the full task lifecycle against the backend REST endpoints: create a task with a validated title (1–200 chars) and optional description (max 1000 chars), list tasks, get a single task's details, update a task, delete a task, and toggle completion via the dedicated complete endpoint. Each task carries `created_at` and `updated_at` timestamps maintained by the system.

**Why this priority**: The API contract is the load-bearing surface between the frontend and the database and is scored directly from the PDF.

**Independent Test**: With a valid JWT for user X, exercise all six endpoints against user X's namespace and verify payloads, status codes, validations, and timestamps without any frontend or CLI involvement.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** a task is created with a valid title, **Then** the response returns the task with id, user_id, title, description (default null/empty), completed = false, created_at, and updated_at, with HTTP 201.
2. **Given** an authenticated user, **When** creation/update bodies violate validation rules (empty title, title > 200 chars, description > 1000 chars), **Then** the request fails with HTTP 400/422 and a clear error, and no change is made.
3. **Given** an authenticated user with tasks, **When** the list endpoint is called, **Then** only that user's tasks are returned with all task fields.
4. **Given** an authenticated user, **When** a task's details are updated (title and/or description), **Then** the task reflects the changes and `updated_at` changes while `created_at` stays unchanged.
5. **Given** an authenticated user, **When** the complete endpoint is toggled, **Then** `completed` flips from false to true or from true to false, and `updated_at` changes.
6. **Given** an authenticated user, **When** a task is deleted, **Then** the response is success (204) and the task no longer appears in listings, cannot be retrieved, and cannot be modified by anyone.

---

### User Story 3 - JWT Bearer Authentication with Per-User Scoping (Priority: P1)

The frontend authenticates the user via Better Auth (email/password) with the JWT plugin issuing tokens. On every API call the frontend sends `Authorization: Bearer <token>`. FastAPI verifies the JWT signature with the shared secret from the `BETTER_AUTH_SECRET` environment variable (same name in both services), extracts the user, and enforces that the `user_id` in the URL matches the token's user. Requests without a valid token receive HTTP 401. Each user only sees and modifies their own tasks. Tokens expire (7 days default).

**Why this priority**: Auth is a security property that gates every endpoint per the PDF; without it the per-user data model and route namespace have no meaning.

**Independent Test**: Call the API with (a) no token, (b) a wrong-signature token, (c) an expired token, (d) a valid token for user A attempting to access `/api/{userB}/tasks`, and (e) a valid token for the URL's own user — verify only (e) succeeds.

**Acceptance Scenarios**:

1. **Given** no `Authorization` header, **When** any task endpoint is called, **Then** the response is HTTP 401 with a clear error.
2. **Given** a token with an invalid signature or an expired one, **When** any task endpoint is called, **Then** the response is HTTP 401.
3. **Given** a valid token for user A, **When** any endpoint under `/api/{userB}/tasks/...` is called where userB ≠ A, **Then** the request is rejected (HTTP 403) and no task data is exposed.
4. **Given** a valid token, **When** the user performs any task operation, **Then** only that user's tasks are returned or affected.
5. **Given** a token issued 7 days ago, **When** it is used, **Then** it is rejected as expired and the frontend routes the user to re-authenticate.

---

### User Story 4 - Phase II Frontend: All Five Features on Next.js (Priority: P1)

A user of the responsive Next.js web app performs all five basic features in the browser: add a task (title + optional description), view the task list with status indicators, edit a task's title/description, delete a task by ID, and toggle complete/incomplete. The UI is responsive.

**Why this priority**: The frontend is the demo surface of Phase II; the PDF explicitly requires all 5 features **including edit of title/description**, which today does not exist in the web UI.

**Independent Test**: In the web UI (desktop and narrow viewport), add, view, edit, toggle, and delete a task while authenticated, and verify each change is reflected by the API. Delivers full PDF parity for the UI.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they submit a task with a title and optional description, **Then** the task appears in the list as incomplete.
2. **Given** an empty title submit attempt, **Then** the UI blocks it with a validation message before or without a failing API call.
3. **Given** an existing task, **When** the user edits its title and/or description and saves, **Then** the list shows the updated details.
4. **Given** an existing task, **When** the user toggles its status, **Then** the status indicator flips between complete and incomplete (both directions).
5. **Given** an existing task, **When** the user deletes it, **Then** it disappears from the list.
6. **Given** a token expiry or 401 from the API, **When** any authenticated UI action fails with 401, **Then** the user is redirected to log in and re-obtain a token.

---

### User Story 5 - Migration and Backward Compatibility Discipline (Priority: P2)

Existing persisted data and existing interfaces are respected during the transition: the Phase I CLI stays functional, existing test suites keep covering preserved behavior, and any data-model change (single description → title + description) is migrated without losing user data. The exact migration strategy is decided at the Plan gate (options recorded under Open Questions OQ-1); this spec only requires that no data is lost and observable behavior matches the PDF afterward.

**Why this priority**: Required for a safe rollout, but every individual behavior it guards is already covered by US1–US4; it constrains how the change happens rather than adding new user-facing value.

**Independent Test**: Populate a database with legacy `todo_item` rows, apply the migration strategy chosen at the Plan gate, and verify every legacy row maps to a valid PDF-conformant task with no lost text.

**Acceptance Scenarios**:

1. **Given** a database containing legacy tasks (description only, no title, no timestamps), **When** the approved migration runs, **Then** every piece of user-entered text remains accessible in the new title/description model — no truncation, no deletion.
2. **Given** the Phase I CLI after changes, **When** an existing Phase I workflow is executed, **Then** the CLI remains functional; breaking changes beyond the PDF-required fields are handled per OQ-5/a decision recorded at the Plan gate.
3. **Given** existing backend (54) and frontend (26) test suites, **When** implementation is planned, **Then** tests that encode current-but-divergent behavior are explicitly updated in the task list, and tests encoding PDF behavior still pass.

---

### Edge Cases

- What happens when a user calls `POST /api/{user_id}/tasks` with `{user_id}` that does not exist but the token is valid for another user? Path `{user_id}` ≠ token user → always HTTP 403, checked BEFORE any DB lookup, regardless of whether that `{user_id}` exists. 404 is never used for this case.
- What happens when title is exactly 200 chars? Accepted; 201 is a boundary test. 201 chars → rejected.
- What happens when description is exactly 1000 chars (or absent/null)? Accepted; 1001 → rejected.
- What happens when the JWT plugin token is present but the corresponding Better Auth user record no longer exists? 401 (cannot extract a valid user).
- What happens with a partially filled update body (only title, only description, empty object `{}`)? Defined: partial update of the given fields; `{}` updates nothing and returns the task unchanged (updated_at may be refreshed or preserved — decided at the Plan gate).
- What happens with a malformed JSON body or wrong `Content-Type`? Rejected as 400/422 without state change.
- What happens with non-integer task `{id}` path segments? Treated as not found (404) per current behavior pattern; not a validation error.
- What happens when a `PATCH .../complete` is called on a task the user does not own? If `{user_id}` in the path ≠ token user → 403 (checked before any DB lookup); if `{user_id}` == token user but the task id does not exist or belongs to another user → 404 — never leaks the other user's task existence.
- What happens with clock skew between token issue time (frontend) and verification time (backend)? Negotiated leeway or server-authoritative time — implementation decision recorded at the Plan gate.

## Requirements *(mandatory)*

### Phase I — Console App

- **FR-101**: System MUST support the five basic features in the console app: Add, Delete, Update, View, Mark Complete/Incomplete.
- **FR-102**: A task MUST have a title that is required and a description that is optional.
- **FR-103**: Add MUST accept a title and a description; the title is required, the description may be omitted or empty.
- **FR-104**: View MUST list all tasks with status indicators (complete/incomplete).
- **FR-105**: Update MUST allow updating a task's details (title and description).
- **FR-106**: Delete MUST remove a task identified by its ID.
- **FR-107**: Mark Complete/Incomplete MUST toggle a task between complete and incomplete states (both directions).
- **FR-108**: The Phase I CLI MUST remain functional and keep backward compatibility where possible (command names/prompt output preserved except where the PDF-mandated title/description model requires otherwise; see OQ-5 for the compat strategy of legacy single-string commands).

### Phase II — Data Model & Persistence

- **FR-201**: Every task MUST have: `id`, `user_id` (owner), `title`, `description`, `completed`, `created_at`, `updated_at`.
- **FR-202**: `title` MUST be required, 1–200 characters after trimming.
- **FR-203**: `description` MUST be optional, max 1000 characters; absence is represented as empty/null.
- **FR-204**: `completed` MUST default to `false` on creation.
- **FR-205**: `created_at` MUST be set once at creation and MUST NOT change on update.
- **FR-206**: `updated_at` MUST change whenever the task is modified (iron-ruled fields: title, description, completed).
- **FR-207**: Data MUST be stored in the existing database so tasks survive logout, browser close, and restart (existing Phase II persistence requirement retained).
- **FR-208**: Existing task data MUST be migrated to the title+description model without data loss (strategy options in OQ-1; execution deferred to Implement). Legacy rows MUST have `created_at` and `updated_at` backfilled (e.g., at migration time). A database backup/branch MUST exist before any migration runs, and any DB schema change requires explicit user approval before it executes.

### Phase II — REST API

- **FR-210**: The backend MUST expose exactly these task endpoints under the user namespace:

| Method | Path                       | Purpose              |
|--------|----------------------------|----------------------|
| GET    | `/api/{user_id}/tasks`     | List the user's tasks |
| POST   | `/api/{user_id}/tasks`     | Create a task         |
| GET    | `/api/{user_id}/tasks/{id}`| Get task details      |
| PUT    | `/api/{user_id}/tasks/{id}`| Update a task         |
| DELETE | `/api/{user_id}/tasks/{id}`| Delete a task         |
| PATCH  | `/api/{user_id}/tasks/{id}/complete` | Toggle completion |

- **FR-211**: Authenticated requests MUST return conventional REST status codes: 201 on create, 200 on read/update/toggle, 204 on delete.
- **FR-212**: Validation failures MUST be rejected with 400/422 and a clear error message; ownership errors follow a single rule: `{user_id}` in the path ≠ token user → HTTP 403 ALWAYS, checked BEFORE any DB lookup, regardless of whether that `{user_id}` exists; a missing or unowned task id within the token user's own namespace → HTTP 404. The codebase must not leak the existence of another user's tasks.
- **FR-213**: Task IDs MUST be unique per system and usable in paths (current integer IDs acceptable; no PDF constraint on ID format).

### Phase II — Authentication (JWT Bearer)

> **Amendment 1 — approved by user (2026-10-24)**: The PDF says the backend
> verifies JWTs with the shared secret `BETTER_AUTH_SECRET`. The installed
> better-auth 1.7.5 JWT plugin supports asymmetric signing only. By user decision
> (OQ-8 = A) the backend verifies via the plugin's JWKS public key (RS256). The
> goals (stateless verification, user_id match, 401 on invalid token, per-user
> isolation) are unchanged. Applies to FR-222, NFR-002, and the Auth Flow below.
> Task-to-be: document this deviation in the README (the README's auth section
> must describe JWKS public-key verification instead of literal shared-secret
> verification).

- **FR-220**: The frontend MUST use Better Auth with the JWT plugin to issue tokens on successful email/password login.
- **FR-221**: The frontend MUST send the header `Authorization: Bearer <token>` on **every** API call.
- **FR-222** *(as amended by Amendment 1)*: FastAPI MUST verify the JWT signature against the Better Auth JWT plugin's published JWKS public keys (asymmetric signing — OQ-8 Option A, user decision; the installed better-auth 1.7.5 plugin supports asymmetric signing only, so the PDF's literal shared-secret wording is realized as JWKS verification; goals unchanged — stateless verification, user_id match, 401 on invalid token). (Evidence and alternatives in OQ-8/research.md.)
- **FR-223**: FastAPI MUST extract the user identity from the verified token.
- **FR-224**: The `user_id` in the URL MUST match the token's user; mismatch MUST be rejected (403) without exposing other users' data.
- **FR-225**: Requests without a valid token MUST receive HTTP 401, including missing header, malformed header, invalid signature, wrong issuer/algorithm, and expired token.
- **FR-226**: Tokens MUST expire (default 7 days); expired tokens MUST be treated as invalid.
- **FR-227**: Each user MUST only see and modify their own tasks; per-user isolation must hold on every request path (retained from 002).
- **FR-228**: The current cookie/session-token verification path in FastAPI MUST be retired in favor of JWT Bearer verification; the retirement approach (e.g., removal in the same release, or temporary dual-accept then removal) MUST be decided at the Plan gate (OQ-3).
- **FR-229**: Registration, login, and logout flows remain provided by Better Auth in the frontend; login MUST surface the JWT to the client application.

### Phase II — Frontend

- **FR-230**: The frontend MUST be built on Next.js; the PDF specifies Next.js 16+ (current repo is on 15.5.x — see OQ-4).
- **FR-231**: The UI MUST be responsive.
- **FR-232**: The web UI MUST expose all 5 basic features: add (title + optional description), view list with status indicators, edit title/description, delete by ID, and toggle complete/incomplete.
- **FR-233**: The frontend client library MUST require and attach the Bearer token to each task API request and handle 401 by routing to re-authentication.
- **FR-234**: Register/login/logout pages remain provided (email/password via Better Auth) so the user can obtain a token.

### Non-Functional / Security Requirements

- **NFR-001**: Secrets (`BETTER_AUTH_SECRET`, `DATABASE_URL`) MUST be provided via environment configuration ONLY; never committed, never logged, never emitted in error messages or API responses.
- **NFR-002** *(as amended by Amendment 1)*: `BETTER_AUTH_SECRET` is configured/used on the frontend only (Better Auth); the backend startup MUST fail-fast when the JWT/JWKS verification configuration is missing (JWKS URL, issuer, audience), since the backend verifies via the plugin's JWKS public key (OQ-8 = A).
- **NFR-003**: JWT verification MUST enforce algorithm allowlisting (no `alg: none`), signature validity, expiry, and (where offered by the plugin) issuer checks.
- **NFR-004**: Per-user authorization MUST be enforced server-side on every task endpoint; the frontend never decides visibility.
- **NFR-005**: Input validation MUST run server-side regardless of any client-side validation.
- **NFR-006**: CORS on the backend MUST reflect only the frontend's allowed origin(s); credentials mode is no longer required once cookie auth is retired (revisit when retiring cookies).
- **NFR-007**: Test-first (constitution): failing tests per user story are written and approved BEFORE implementation (Plan→Tasks→Implement gates).
- **NFR-008**: The Python runtime (3.13+, uv + uv_build) and the `src/todo_app` layout are unchanged by this feature.

## API Contract (Phase II, normalized)

Conventions: JSON bodies; `Authorization: Bearer <token>` required; base path `/api/{user_id}/tasks`. `{user_id}` is the Better Auth user ID; `{id}` is the task ID. Error bodies are JSON `{"detail": "..."}` or `{"error": "..."}` (exact wording is an implementation detail).

Ownership error rule (applies to every endpoint below): if `{user_id}` in the path ≠ token user → HTTP 403 ALWAYS, checked BEFORE any DB lookup, regardless of whether that `{user_id}` exists. HTTP 404 is returned ONLY when the task id does not exist or is not owned by the token user, within the token user's own namespace. No "404 instead of 403" ambiguity.

### GET `/api/{user_id}/tasks` — list tasks

- 200: `{"items": [Task, ...]}` or a bare array — envelope decided at the Plan gate; MUST contain only the token user's tasks for `{user_id}`.
- 401: unauthenticated/invalid token. 403: token user ≠ `{user_id}`.

### POST `/api/{user_id}/tasks` — create task

Request: `{"title": "...", "description": "..."}` (`description` optional).

- 201: the created Task JSON: `{id, user_id, title, description, completed: false, created_at, updated_at}`.
- 400/422: empty/whitespace title, title > 200 chars, description > 1000 chars, wrong types.
- 401/403: as above.

### GET `/api/{user_id}/tasks/{id}` — get task details

- 200: Task JSON of the **owner's** task.
- 404: task id does not exist in, or is not owned within, the token user's own namespace (ownership conflated with existence to prevent enumeration). Path `{user_id}` ≠ token user → 403 per the ownership rule above.

### PUT `/api/{user_id}/tasks/{id}` — update task

Request: `{"title": "...", "description": "..."}` — full-update semantics possible; partial-field semantics per the Plan-gate decision (Edge Cases). Both fields are updatable; `completed` is NOT updatable here (toggle owns completion; PDF separation).

- 200: the updated Task JSON with refreshed `updated_at`.
- 400/422: validation; 404: task id not found/unowned within the token user's own namespace; 403: path `{user_id}` ≠ token user.

### DELETE `/api/{user_id}/tasks/{id}` — delete task

- 204: permanently removed. 404 when not found or not owned within the token user's own namespace; subsequent GETs return 404. Path `{user_id}` ≠ token user → 403 per the ownership rule above.

### PATCH `/api/{user_id}/tasks/{id}/complete` — toggle completion

- 200: the Task JSON with `completed` flipped (either direction) and refreshed `updated_at`.
- 404: task id not found/unowned within the token user's own namespace; 403: path `{user_id}` ≠ token user.

Task object (`Task`):

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

## Auth Flow (JWT Bearer)

1. **Login**: The user submits email/password on the Next.js app. Better Auth (frontend server handler at `/api/auth/*`) validates credentials (existing user/session/account tables).
2. **Token issue**: The Better Auth **JWT plugin** issues a signed JWT bound to the user (subject = user ID) with `exp` = 7 days. Exact token retrieval mechanism (response body vs. endpoint like `POST /api/auth/token`) is finalized at the Plan gate from the installed better-auth version.
3. **API call**: The frontend calls any task endpoint with `Authorization: Bearer <token>`.
4. **Verification** *(per Amendment 1)*: FastAPI dependency: parse header →
   verify signature against the Better Auth JWT plugin's published JWKS public
   key (RS256 — OQ-8 Option A, user decision; the PDF's literal shared-secret
   wording cannot be realized with the installed better-auth 1.7.5 plugin, which
   signs asymmetrically only; goals unchanged; algorithm allowlist enforced) →
   verify `exp` → extract user (subject/user id) → optionally ensure the user exists.
5. **Scoping**: Route handler compares token user to `{user_id}` path param; mismatch → 403. All DB queries filter `user_id` = token user.
6. **Expiry**: When `exp` passes or verification fails, every request returns 401; the frontend re-authenticates the user (redirect to login; re-login mints a fresh token).

## Data Model Changes

Current `TodoItem` (backend, `src/todo_app/models.py:78`) and its schema:

| Column      | Current            | PDF target                                     |
|-------------|--------------------|------------------------------------------------|
| id          | PK, int            | unchanged (PK, int)                            |
| user_id     | FK → user.id       | unchanged                                      |
| title       | **absent**         | NEW: required, 1–200 chars                     |
| description | required text      | optional text, max 1000 chars                  |
| completed   | bool, default false| unchanged                                      |
| created_at  | **absent**         | NEW: set at creation, immutable                |
| updated_at  | **absent**         | NEW: refreshed on every modification           |

Migration concern: existing rows hold only `description`, so they have no title, and text cannot be losslessly split into title+description. The recommended lossless strategy (OQ-1, option 2): title derived from the beginning of the old text (max 200 chars), full original text preserved in description. Legacy rows get `created_at`/`updated_at` backfilled at migration time. A database backup/branch must exist before any migration, and any DB schema change requires explicit user approval before it runs. Options are described ONLY in OQ-1; execution of migration belongs to the Implement stage of this feature (after the Plan/Tasks gates).

In-memory `store.TodoItem` (Phase I) gains the same conceptual fields, mapped to console-appropriate behavior (FR-101..108).

## Gap Analysis: current behavior vs PDF requirement vs required change

| # | Area            | Current behavior (verified in repo)                                                                                              | PDF requirement                                                                                                | Required change                                                                                                  |
|---|-----------------|------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| 1 | Phase I fields  | `store.TodoItem`: `description` only; no update feature (`src/todo_app/store.py:9`), CLI: add/list/complete/delete, no "incomplete" toggle nor detail update (`src/todo_app/__init__.py:10`) | Tasks with title (required) + description (optional); Update included; Complete/Incomplete toggle                | Extend store + CLI with title/description, update command, and toggle command; preserve existing commands where feasible |
| 2 | Task model      | `todo_item` table: `id, user_id, description (required), completed` — no title, no timestamps (`src/todo_app/models.py:78`)          | `id, user_id, title, description, completed, created_at, updated_at`                                             | Add `title`, `created_at`, `updated_at`; relax `description` to optional with 1000 cap; migrate data (OQ-1)        |
| 3 | List route      | `GET /api/items` returns `{"items": [...]}` (`src/todo_app/api/items.py:38`)                                                          | `GET /api/{user_id}/tasks`                                                                                       | New router namespace `/api/{user_id}/tasks`; retire/redirect `/api/items` (OQ-2)                                   |
| 4 | Create route    | `POST /api/items` accepts `{description}` only (`items.py:49`)                                                                       | `POST /api/{user_id}/tasks` with `{title, description?}` + validation                                            | New create endpoint with title 1–200 / description ≤1000 validation                                               |
| 5 | Get details     | None                                                                                                                                | `GET /api/{user_id}/tasks/{id}`                                                                                  | Add owner-scoped single-task retrieval                                                                            |
| 6 | Update route    | None (PATCH accepts only `{completed: true}`)(`items.py:66`)                                                                        | `PUT .../tasks/{id}` updating title/description                                                                  | Add PUT with field validation + `updated_at` refresh                                                              |
| 7 | Complete toggle | PATCH sets `completed = true`; no un-complete path; body `{completed:false}` rejected (`items.py:73`)                                | `PATCH .../tasks/{id}/complete` TOGGLES completion (both directions)                                             | Reimplement as toggle endpoint semantics                                                                          |
| 8 | Delete route    | `DELETE /api/items/{id}` (`items.py:83`)                                                                                            | `DELETE /api/{user_id}/tasks/{id}`                                                                               | Move under user namespace (behavior preserved)                                                                    |
| 9 | Auth (backend)  | Cookie `session_token` → DB `session` lookup in `src/todo_app/auth.py:32` (Better Auth **session cookie**, same DB)                 | JWT Bearer via Better Auth **JWT plugin**; FastAPI verifies signature with `BETTER_AUTH_SECRET`                  | Replace `get_current_user` with JWT verification dependency; retire cookie lookup (OQ-3); `/api/items` router does not enforce `{user_id}`-in-URL matching — enforce under new namespace |
| 10 | Auth (frontend) | Client fetches relative `/api/items` with same-origin cookie via Next.js rewrite (`frontend/src/lib/api.ts:16`, `frontend/next.config.js:5`) | Every call sends `Authorization: Bearer <token>`                                                                | Rewire client library to attach Bearer token; login must surface JWT (frontend `auth.ts` currently has NO JWT plugin — `frontend/auth.ts:41` plugins only `nextCookies()`); decide token storage (OQ) |
| 11 | Frontend UI     | 4 features; add-only-description form; no edit feature (`frontend/src/components/TodoList.tsx:82`)                                  | All 5 features including edit title/description; responsive                                                       | Add edit UI + title/description form fields; keep responsive layout                                              |
| 12 | Next.js version | `next: ^15.3.3` (package.json:14) — resolved 15.5.x usage per audit                                                                  | Next.js 16+                                                                                                      | Upgrade decision + risks in OQ-4 (scope decision at Plan gate)                                                     |
| 13 | Frontend tests  | 26 tests, incl. TodoList behavior tests that reflect only-current DOM                                                              | All 5 features incl. edit                                                                                        | Update/extend TodoList + api tests per new contract (test-first per NFR-007)                                       |
| 14 | Backend tests   | 54 tests: auth tests exercise cookie flows (`tests/test_auth.py`); API tests exercise `/api/items` (`tests/test_api.py`)             | JWT-based auth; `/api/{user_id}/tasks`                                                                           | Rewrite auth tests for JWT; port API tests to new routes/fields (count may change; suites must pass)               |

## Open Questions / Decisions Needed (resolved at Plan gate)

### OQ-1 — Data model migration (seeded by audit)

Current model has a single `description` field and no title. Options for migrating existing rows to title+description **without data loss** (informational: do not execute during Specify):

1. **Whole-text-to-title**: set `title = existing description` (trimmed to 200 chars at worst → TRUNCATION → violates "no data loss"). **REJECTED** — truncation of any user text is unacceptable; any truncation-based option must be rejected at the Plan gate.
2. **Whole-text-to-description with derived title (RECOMMENDED, lossless)**: set `description = existing text` (full original text preserved), and `title` derived from the beginning of the old text (max 200 chars). Preserves all text; non-obvious titles are acceptable.
3. **Reversible pairing**: keep legacy text in `description` and synthesize `title` as e.g. `Task <id>`; a post-migration manual pass can rename later. Fully lossless and simple.

Additional requirements for any chosen option:

- **Timestamps**: legacy rows have no `created_at`/`updated_at`; the migration MUST backfill both (e.g., at migration time), so every row satisfies FR-205/FR-206 afterward.
- **Safety**: a database backup/branch MUST exist before any migration runs, and any DB schema change requires explicit user approval before it executes.
- **No truncation**: truncation-based options are rejected outright; the recommended lossless strategy is option 2.
- Fail-fast vs best-effort for over-long legacy descriptions is also a Plan-gate call (and interacts with OQ-7, 1000-char cap enforcement).

### OQ-2 — Route naming: replace/redirect for `/api/items`

Options:

1. **Hard replace**: remove `/api/items` in this release; update all callers. Cleanest; breaks anything still calling the old paths (e.g., tests, external scripts).
2. **Deprecate and redirect**: keep `/api/items` temporarily shimmed (e.g., 301 to the new path, or mapping onto the token-user's `/api/{me}/tasks`), remove at a later minor release. Smoother rollout; long-lived dead code risk.
 3. **Hard replace + same-release test updates only** (no runtime shim, docs update in release notes). Compromise between 1 and 2.
PDF compliance requires the new namespace exists; PDF compliance does NOT forbid keeping a deprecation shim.

### OQ-3 — Auth retirement: cookie/session removal

- How the cookie/session code is retired:
  1. **Same-release removal**: `get_current_user` cookie dependency, `SESSION_COOKIE_NAME` usage in `src/todo_app/auth.py`, and its tests are deleted or replaced this release. Tests rewritten (see OQ-5).
  2. **Dual-accept transitory**: accept both `Authorization: Bearer` and cookie sessions for one release, then remove. Riskier to reason about (cookie gives an identity even with `{user_id}` URLs in the "me" case — but PDF requires Bearer); recommended only if a live deployment needs a grace window.
- Cross-origin cookie risk (for the record if dual-accept were chosen): with a separately hosted backend (frontend on :3000, backend on :8000, different origin contexts), third-party cookie handling (`SameSite`, `Secure`, `Partitioned`) becomes fragile across browsers and death-defying in Chrome's storage-partitioning trajectory — this risk is a reason to prefer the pure JWT approach the PDF mandates. Note the current deployment avoids it only by same-origin Next.js rewrite proxying (frontend/next.config.js). Also note cookie retirement requires removing `allow_credentials` (NFR-006) and possibly changing `nextCookies()` plugin usage from `frontend/auth.ts`, and the "advance."
- Frontend JWT access detail: Better Auth JWT plugin exposes the token; exact retrieval endpoint/name for the installed better-auth version to be confirmed at the Plan gate. How the frontend attaches the `Authorization: Bearer` header (options below) is decided at the Plan gate; the PDF says the frontend sends the Bearer header. A Next.js rewrite CANNOT turn a cookie into an Authorization header (rewrites proxy the request, they do not add auth headers from cookies) — any approach premised on that is invalid.
  1. **Client attaches the header itself**: the client obtains the token and adds `Authorization: Bearer <token>` to each fetch. Simple, direct match to the PDF wording; trade-off: the token lives in browser-accessible storage (XSS exposure), and cookie-vs-JS-state storage must be decided.
  2. **Next.js server route handler/proxy adds the header**: a server-side route handler reads the token (e.g., from an HTTP-only cookie) server-side and adds the header when calling FastAPI. Trade-off: extra proxy layer/latency and server code, but the token never sits in XSS-reachable client storage.
  The decision (and token storage choice) happens at the Plan gate.

### OQ-4 — Next.js upgrade (15.5.x → 16+)

PDF says Next.js 16+. Current repo: `next: ^15.3.3` → effectively 15.5.x. Upgrade risks to enumerate at the Plan gate if included:

- React 19 pairing changes in 16.x; breaking changes in config/defaults (e.g., caching semantics, middleware, route handlers).
- Vitest + Next.js interplay (`next/jest` or vite config) may need updates.
- `nextCookies()` / better-auth Next.js integration compatibility.
- CI/build/test revalidation costs; app may need code changes (e.g., async request APIs already used — `await headers()`), which mostly exist already.

**Decision needed**: include the upgrade in this feature's scope (allowing test/lint/build verification), or defer to a separate feature while this spec targets Next 15. The PDF as source of truth tends to favor including it. If included, the upgrade MUST be its own isolated task with rollback (`package-lock.json` restored), and the frontend tests and build MUST pass before any subsequent task continues.

### OQ-5 — Impact on existing tests (backend 54, frontend 26, CLI) and Phase I backward compatibility

- Backend 54: `tests/test_auth.py` (9) pivots to JWT; `tests/test_api.py` (15) re-targets `/api/{user_id}/tasks` and new fields; `test_store.py` (19) + `test_cli.py` (6) absorb title/description + update/toggle; `test_models.py` (5) covers new columns/timestamps.
- Frontend 26: `TodoList.test.tsx` (7) re-tests add/list/edit/delete/toggle with two fields; `AuthForm` (6), `auth-handler` (7), `auth-cookies` (3), `require-session` (2), `logout` (1) tests may need adjustments wherever they fan out from cookie flows to token flows. Established flows (register/login/logout) remain covered behaviorally.
- Phase I backward compatibility: the PDF mandates title+description and an Update feature; legacy `add <text>` single-argument input can keep working by treating the entire input as the title (entire-text-as-title), or by an optional normalization where the first chunk is the title (first-chunk-as-title) — decision at the Plan gate. PRINCIPLE: every documented legacy command keeps working, and the test suite keeps asserting those flows intact. `complete <id>` → renames toward `toggle <id>` while keeping `complete <id>` aliasing behavior (mark-complete remains valid; adding `uncomplete` extends FR-107).

### OQ-6 — PDF's internal inconsistency about task paths

The PDF's **endpoint table** lists `/api/{user_id}/tasks` (with user ID in the path), while a **separate example spec** in the PDF shows `/api/tasks`. This spec follows the **endpoint table** (`/api/{user_id}/tasks`) because:

1. It is the more standards-ful and operationally useful authority — but more importantly, it's given as a table (normative-looking), whereas the example is illustrative prose.
2. Per-user scoping in the URL gives an explicit resource namespace and directly supports the audit's focus on per-user isolation, matching FR-224's user_id-match rule.
3. When the two conflict with an illustrative example vs a table, a table is the safer thing to treat as authoritative. Any deviation from the PDF may now be detected/flagged by reviewers against exactly this rationale.

### OQ-7 — Remaining details deferred to Plan

- Error-envelope shape: `{"detail": ...}` (FastAPI default) vs `{"error": ...}` — unify per codebase trend.
- Synchronous vs asynchronous route handlers with a new request-scoped user dependency — implementation detail.
- List response envelope `{"items": [...]}` vs `[...]` for the new endpoints.
- PUT semantics: full-object update (must provide both fields) vs partial update (only provided fields change); correspondingly, PUT-with-empty-object behavior (reject 400 vs no-op 200).
- Better Auth JWT plugin configuration details (token exp derivative config, issuer/sub claims) once version pinned.

### OQ-8 — Better Auth JWT plugin signing algorithm/key mechanism (added by correction)

> **DECIDED — approved by user (Amendment 1, 2026-10-24): Option 2** — verify in
> FastAPI via the plugin's JWKS (asymmetric RS256 signing, plugin-native key
> management). The evidence requirement below is satisfied by
> `research.md` (installed better-auth 1.7.5 source).

The Better Auth JWT plugin may sign with asymmetric keys published via JWKS rather than a shared secret. Confirm from the INSTALLED better-auth version's documentation/source what algorithm and key mechanism the plugin supports. Options:

1. **Configure the plugin for HS256 with the shared secret**, if supported — keeps the PDF's shared-secret verification with `BETTER_AUTH_SECRET` directly.
2. **Verify in FastAPI via the plugin's JWKS** — the backend fetches the plugin's published keys to verify asymmetric signatures. NOTE: this may require a JWKS/keys table = a DB schema change, which requires explicit user approval before it runs.
3. **Any other documented approach** supported by the installed version.

The choice MUST be made at the Plan gate with evidence (the installed version's documentation/source), not assumed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All six Phase II endpoints respond per the API contract above with validation and status codes exactly as specified (verified by tests).
- **SC-002**: A request with no token, an invalid-signature token, or an expired token receives 401 on all task endpoints; a valid-token request for a foreign `{user_id}` gets 403 with no task data leaked.
- **SC-003**: The web UI supports add (title + optional description), view with status indicators, edit title/description, delete, and toggle — exercised end-to-end by frontend tests.
- **SC-004**: Phase I console app exposes all 5 features and previously-supported flows still work (CLI test suite green on retained legacy-compatible behavior).
- **SC-005**: Every task exposes `created_at`/`updated_at` behaving per FR-205/FR-206.
- **SC-006**: Backend suite (54 tests, updated per OQ-5) and frontend suite (26 tests, updated per OQ-5) pass after implementation.
- **SC-007**: No user text is lost during the approved migration path for legacy rows (OQ-1 strategy applied at Implement, verified by a migration-specific test).

## Out of Scope / Tracked Separately

The following are referenced by the PDF or the codebase but are NOT in scope for this feature; they will be decided/handled in a separate feature:

- README and layered CLAUDE.md documentation updates.
- Deployed Vercel URL and the backend API URL (deployment/hosting configuration).
- The 90-second demo video required by the PDF.
- The PDF's monorepo layout recommendation (`/specs`, `frontend/`, `backend/`) versus the current repository layout (`src/todo_app`, `.specify`) — the layout question is to be decided in a separate feature.

## Assumptions

- The Hackathon PDF's requirements as restated in `docs/fix.txt` are complete and authoritative for this feature; the PDF itself is NOT in the repo, so if the real PDF differs from the restatement, the user must correct this spec at the Spec gate.
- Better Auth remains the authentication system (registration/login/logout across Better Auth's user/session/account tables — already in the DB today), extended with the JWT plugin rather than replaced.
- "Same env var name" (`BETTER_AUTH_SECRET`) means both the Next.js app and FastAPI read the secret from `BETTER_AUTH_SECRET` — this name already exists in the frontend (`frontend/auth.ts:16`); the backend will adopt the same name. *(Amended by Amendment 1: with OQ-8 = A, `BETTER_AUTH_SECRET` stays frontend-only; the backend verifies via the plugin's JWKS public key.)*
- Task IDs remain integers (existing pattern); `{user_id}` stays the Better Auth string user ID (matches current `User.id: str`).
- The five Phase I basic features are semantic (add/update/view/delete/toggle) and are NOT required to have identical CLI command names between phases.
- Register/login/logout pages/routes survive as needed for the JWT flow; the PDF does not redefine the auth UI shape.

## Files created or modified (Specify stage)

Created:

- `.specify/features/003-pdf-alignment/spec.md` — this document.

Modified:

- None. No source code, tests, database, dependencies, env files, or existing 001/002 spec artifacts were changed (fix.txt's conditional reference-amendment of 001/002 was not needed: this spec states its relationship to 002 explicitly instead of editing the approved 002 artifacts).

Correction pass applied (2026-10-24, per `docs/fix.txt`): this spec file itself — wording fixes (US2 scenario 6, DELETE status codes, source-of-truth phrasing, OQ-5 option naming), ownership error rule unified in Edge Cases/FR-212/API contract, auth verification assumption removed with OQ-8 added, OQ-3 frontend token-handling options rewritten, OQ-1/FR-208 migration requirements added (backfill, backup/approval, no-truncation), OQ-4 isolation-task rule added, and "Out of Scope / Tracked Separately" added. Status remains "Draft — awaiting user review".

Amendment 1 applied (2026-10-24, plan-correction pass, approved by user): 
**"The PDF says the backend verifies JWTs with the shared secret `BETTER_AUTH_SECRET`. The installed better-auth 1.7.5 JWT plugin supports asymmetric signing only. By user decision (OQ-8 = A) the backend verifies via the plugin's JWKS public key (RS256). The goals (stateless verification, user_id match, 401 on invalid token, per-user isolation) are unchanged."** FR-222, NFR-002, the Auth Flow, and the `BETTER_AUTH_SECRET` assumption amended accordingly; §OQ-8 records the decision; a task-to-be (document this deviation in the README) is recorded here and mirrored in plan.md. Status remains "Draft — awaiting user review". No source code, tests, DB, dependencies, package files, or env files were changed by this amendment; nothing was committed.
