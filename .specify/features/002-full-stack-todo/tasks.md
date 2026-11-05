# Tasks: Full-Stack Todo

**Input**: Design documents from `.specify/features/002-full-stack-todo/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY for this feature (constitution Principle II; plan.md "Tests (test-first gate — mandatory before implementation)"). All tests must be written and user-approved before implementation begins.

**Organization**: Tasks are grouped by implementation phase to support the test-first (red-green-refactor) workflow. Backend tests are Python (`unittest` + `httpx` `AsyncClient`); frontend tests are `vitest` under `frontend/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Test Writing (Test-First Gate — MANDATORY)

**Purpose**: Write all tests before any implementation. Tests encode the approved behavior from `data-model.md`, `contracts/api.md`, and `contracts/pages.md` as an executable contract.

**⚠️ CRITICAL**: No implementation work may begin until ALL tests in this phase are written and user-approved.

- [ ] T001 [P] [US1-US5] Write backend API contract tests in `tests/test_api.py` (`httpx` `AsyncClient`, full request/response with cookies against FastAPI) covering:
  - `POST /api/items` with a valid session cookie -> 201, item appears in list as incomplete; empty/whitespace-only description -> 400, no item created (contracts/api.md, US2)
  - `GET /api/items` shows owned items only; empty list returns `{"items": []}` (US2 S2/S4)
  - `PATCH /api/items/{id}` complete -> 200 updated; idempotent re-complete -> 200 graceful no-op; `DELETE /api/items/{id}` -> 204 and gone (US3 S1/S2/S3)
  - `PATCH`/`DELETE` of a non-existent or another user's item -> 404, nothing changed (US3 S4, US5 S2)
  - persistence: items and statuses identical after logout+login and after re-creating the app+DB (US4, SC-002/SC-003)
  - isolation: two users' lists never cross; unauthenticated or invalid-cookie access to every `/api/items` path -> 401 (US5, FR-006)
- [ ] T002 [P] [US1, US5] Write unit tests in `tests/test_auth.py` for the Better Auth session verification helpers in `src/todo_app/auth.py`:
  - helpers round-trip a user_id and reject tampered/absent values
  - session verification succeeds for valid sessions and fails for invalid/expired ones
- [ ] T003 [P] [US1, US4] Write unit tests in `tests/test_models.py` for the SQLModel `User` and `TodoItem` models per `data-model.md`:
  - create, read, update correctly
  - enforce constraints: username required/unique, non-blank password, non-empty description, per-item owner (FR-002, FR-012, FR-013)
- [ ] T004 [P] [US1] Write frontend authentication tests under `frontend/` (`vitest`) per `contracts/pages.md`:
  - register success -> session + todo list page; duplicate username -> 409; blank password -> 400 (FR-001/FR-002)
  - login success -> session; wrong password -> 401, user remains unauthenticated (FR-003/FR-004)
  - logout ends the session; `/` redirects unauthenticated users to `/login` (FR-005, FR-006, SC-006)
- [ ] T005 [P] [US2, US3] Write frontend TodoList tests under `frontend/` (`vitest`) per `contracts/api.md`/`contracts/pages.md`:
  - add/list/mark complete/delete behavior against the `/api/items` proxy (FR-007, FR-008)
  - empty-list message shown when the user has no items (US2 S4)

**Checkpoint**: All tests written and FAIL (RED phase). User reviews and approves tests before proceeding.

---

## Phase 2: Backend Foundation (US1, US4, US5)

**Purpose**: Core backend infrastructure that MUST be complete before the API endpoints can be implemented.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete.

- [ ] T006 [US4, US5] Add backend dependencies via `uv add`: `fastapi`, `sqlmodel`, `uvicorn`, `httpx`; add `[project.scripts] todo-app-api = "todo_app.api.app:main"` to `pyproject.toml` (research.md D1/D4/D7)
- [ ] T007 [US4, US5] Create `src/todo_app/models.py` with SQLModel `User` and `TodoItem` models per `data-model.md` (SQLAlchemy `SERIAL` id, `TodoItem.user_id -> User.id` FK, unique username, non-empty description, completed boolean; research.md D9)
- [ ] T008 [P] [US4] Create `src/todo_app/database.py`: Neon PostgreSQL connection from `DATABASE_URL`, SQLModel session factory, schema init (research.md D3/D6)
- [ ] T009 [P] [US1, US5] Create `src/todo_app/auth.py`: Better Auth session verification helpers for FastAPI (verify session token from request cookie, resolve owning user; research.md D5/D6)

**Checkpoint**: Foundation ready — backend user story implementation can now begin.

---

## Phase 3: Backend API (US2, US3, US5)

**Purpose**: Implement the FastAPI `/api/items` endpoints per `contracts/api.md`.

- [ ] T010 Create `src/todo_app/api/__init__.py` marking the `api` subpackage
- [ ] T011 [US1-US5] Create `src/todo_app/api/app.py`: FastAPI app factory, CORS, lifespan (schema init on startup), session-verification dependency wired to all todo routes (plan.md; research.md D1)
- [ ] T012 [US1-US5] Create `src/todo_app/api/items.py` implementing:
  - `GET /api/items` — list the authenticated user's items (owner-scoped query; US2, US5)
  - `POST /api/items` — add an item; reject empty descriptions with 400; assign unique id (FR-011, FR-012)
  - `PATCH /api/items/{id}` — mark complete; 200 update, graceful no-op when already complete; 404 for non-existent/non-owned; 400 for non-`true` values (US3, US5)
  - `DELETE /api/items/{id}` — delete; 204 removed; 404 for non-existent/non-owned (US3, US5)
  - Every endpoint authenticates via the session and returns 401 for unauthenticated/invalid-cookie requests (FR-006, US5 S3)

**Checkpoint**: `tests/test_api.py`, `tests/test_auth.py`, `tests/test_models.py` pass (GREEN phase).

---

## Phase 4: Frontend Foundation (US1)

**Purpose**: Scaffold the Next.js app and configure Better Auth so register/login/logout flows work.

- [ ] T013 [US1] Scaffold the Next.js app in `frontend/`: `package.json` (next, react, better-auth, vitest deps; `dev`/`test` scripts), `next.config.js` (proxy `/api/items/*` to `http://127.0.0.1:8000`), TypeScript config (research.md D2/D7; plan structure)
- [ ] T014 [US1] Configure Better Auth: `frontend/auth.ts` (server config), `frontend/src/app/api/auth/[...all]/route.ts` (handler serving `POST /api/auth/register|login|logout`), `frontend/src/lib/auth.ts` (session helpers `session()`/`getSession()`) (research.md D5/D6; contracts/api.md)
- [ ] T015 [P] [US1] Create `frontend/src/app/layout.tsx` root layout (plan structure)
- [ ] T016 [US1] Create `frontend/src/components/AuthForm.tsx`, `frontend/src/app/login/page.tsx`, and `frontend/src/app/register/page.tsx` per `contracts/pages.md`: post `{username, password}` to the auth endpoints; on success go to `/`; show clear errors on failure (FR-001/FR-002/FR-003/FR-004, US1)
- [ ] T017 [P] [US1] Implement logout per `contracts/pages.md` `GET /logout`: posts `POST /api/auth/logout`, ends the session, redirects to `/login`; list page inaccessible afterwards (FR-005, US1 S4)

**Checkpoint**: Register, log in, and log out work end-to-end in a browser.

---

## Phase 5: Frontend Todo Pages & Components (US2, US3)

**Purpose**: Implement the todo list page and item operations against the FastAPI `/api/items` API.

- [ ] T018 [US2, US3] Create `frontend/src/lib/api.ts`: client-side fetch helpers for `GET/POST/PATCH/DELETE /api/items` (FR-008)
- [ ] T019 [US2, US3] Create `frontend/src/components/TodoList.tsx`: item list (description + completion status), add form, mark-complete and delete controls, clear error display for empty descriptions and failed actions, empty-list message (FR-007, FR-012, US2 S3/S4, US3)
- [ ] T020 [US2, US3] Create `frontend/src/app/page.tsx`: todo list page; renders current user's list via `TodoList`; redirects unauthenticated users to `/login` (FR-006, SC-006)

**Checkpoint**: Web UI fully functional; all frontend (`vitest`) tests pass; SC-004 met (all todo operations through the browser).

---

## Phase 6: Integration & Validation

**Purpose**: Verify end-to-end behavior matches all success criteria.

- [ ] T021 Run full backend suite: `uv run python -m unittest discover -s tests -v` — all tests pass, including unchanged Phase I tests `tests/test_store.py` and `tests/test_cli.py` (FR-014)
- [ ] T022 Run full frontend suite: `npm --prefix frontend test` — all tests pass
- [ ] T023 Run `quickstart.md` manual validation scenarios 1-10 and verify all pass (SC-001 through SC-006)

**Checkpoint**: All tests pass; all quickstart scenarios verified. Phase II complete; ready for implementation-checklist review against this task list.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Tests)**: No dependencies — starts immediately. BLOCKS all implementation.
- **Phase 2 (Backend Foundation)**: Depends on Phase 1 completion (tests must be approved).
- **Phase 3 (Backend API)**: Depends on Phase 2 completion (models, database, auth).
- **Phase 4 (Frontend Foundation)**: Depends on Phase 1 completion — can run in parallel with Phases 2/3 (separate `frontend/` tree).
- **Phase 5 (Frontend Todo Pages)**: Depends on Phase 4 and Phase 3 (API must be reachable for integration).
- **Phase 6 (Validation)**: Depends on Phases 3 and 5 completion.

### Within Each Phase

- Phase 1: T001-T005 can run in parallel (different files).
- Phase 2: T006 then T007; T008 and T009 depend on T007 and can run in parallel.
- Phase 3: T010 then T011 then T012 (sequential).
- Phase 4: T013 then T014; T015 and T017 can run in parallel with each other; T016 depends on T014.
- Phase 5: T018 then T019 then T020 (sequential).
- Phase 6: T021 and T022 can run in parallel; T023 depends on both.

### Test-First Enforcement

Per constitution Principle II:
1. T001-T005 must be completed and user-approved before T006 or later begin.
2. New tests must FAIL (RED) before implementation (red-green-refactor).
3. A task is complete only when its tests pass.
4. `tests/test_store.py` and `tests/test_cli.py` are UNCHANGED and must remain green throughout (FR-014).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence