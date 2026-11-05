# Implementation Plan: Full-Stack Todo

**Branch**: `002-full-stack-todo` | **Date**: 2026-09-16 | **Spec**: `spec.md` (same feature directory)

**Input**: Feature specification from `.specify/features/002-full-stack-todo/spec.md`

## Summary

Evolve the Phase I console todo app in this same repository into the Phase II full-stack app required
by the approved Hackathon specification: a **FastAPI** backend API with **SQLModel** ORM against a
**Neon PostgreSQL** database, a **Next.js** web frontend, and **Better Auth** for authentication with
per-user item isolation. The Phase I CLI is preserved unchanged and still passes its tests (FR-014).
The resulting architecture is a monorepo with the Python backend under `src/todo_app` (alongside the
unchanged CLI) and a Next.js frontend under `frontend/`.

## Technical Context

| Item                | Value                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------|
| Language/Version    | Python 3.13+ (declared in `pyproject.toml` / `.python-version`); Node 18+ for frontend     |
| Backend Framework   | **FastAPI** (ASGI, async); added via `uv`                                                  |
| Frontend Framework  | **Next.js** (React, App Router); managed with `npm`                                        |
| ORM / Data Layer    | **SQLModel** (Pydantic + SQLAlchemy); added via `uv`                                       |
| Database            | **Neon PostgreSQL** (managed, external); connection string via `DATABASE_URL` env var       |
| Authentication      | **Better Auth**; session management and password hashing; integrated in Next.js + FastAPI    |
| Testing             | `unittest` + `httpx` `AsyncClient` for backend; `vitest` for frontend; test-first, user-approved before code |
| Target Platform     | Local browser against `http://localhost:3000` (Next.js dev) proxied to `http://127.0.0.1:8000` (FastAPI) |
| Project Type        | Monorepo: FastAPI JSON API backend + Next.js SPA frontend + preserved CLI entry             |
| Performance Goals   | SC-001 (register + log in + add first item in <2 min) is a UX bound; no load targets        |
| Constraints         | Smallest design; passwords never plaintext; strict per-user isolation; CLI backward-compatible|
| Scale/Scope         | The five Phase II requirements only: web frontend, backend API, persistence, auth, multi-user isolation |

All unknowns resolved — see `research.md`.

## Constitution Check

*GATE: Passes before Phase 0 research and after Phase 1 design.*

- **I. Spec-First**: This plan and its artifacts are derived exclusively from the approved `spec.md`;
  the five Phase II requirements plus the preserved Phase I scope; no new requirements are
  introduced. ✔
- **II. Test-First**: Delivery FLOW is test-first: tests are written and REVIEWED/APPROVED by the
  user before ANY implementation begins, then red -> green -> refactor. The feature is complete only
  when all approved tests pass (including retained Phase I tests). ✔
- **III. Lifecycle & Gates**: No stage skipped. Spec approved; this plan awaits the plan-review gate;
  task creation and implementation follow only after explicit approval. ✔
- **IV. Versioning**: No version or constitution change; the CLI is preserved so nothing is broken. ✔
- **V. Simplicity & CLI Usability**: Smallest design satisfying the spec (FastAPI backend + Next.js
  frontend, research.md D1/D2); Phase I CLI text-in/text-out behavior is unchanged, and the web
  layer adds only what the spec requires. ✔
- **Additional Constraints**: Python 3.13+ ✔; `uv` + `uv_build` unchanged (FastAPI/SQLModel are
  normal Python dependencies added through `uv`, not a build-backend change) ✔; code under
  `src/todo_app` ✔. The Next.js frontend is a separate JS project under `frontend/` and does not
  fall under the Python `src/todo_app` constraint. ✔

No violations; Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
.specify/features/002-full-stack-todo/
  spec.md            # Approved feature specification
  plan.md            # This file
  research.md        # Phase 0 output: minimal design decisions
  data-model.md      # Phase 1 output: entities and invariants
  quickstart.md      # Phase 1 output: runnable validation guide
  contracts/
    api.md           # Phase 1 output: JSON API contract (FR-008)
    pages.md         # Phase 1 output: web page contract (FR-007)
```

### Source Code (repository root)

```text
src/todo_app/
  __init__.py        # Phase I CLI main() — UNCHANGED, backward-compatible (FR-014)
  store.py           # Phase I in-memory store — UNCHANGED
  models.py          # SQLModel models: User, TodoItem (PostgreSQL schema)
  database.py        # Neon PostgreSQL connection, session factory, schema init
  auth.py            # Better Auth session verification, helpers for FastAPI
  api/
    __init__.py
    app.py           # FastAPI app factory, CORS, lifespan (schema init)
    items.py         # GET/POST/PATCH/DELETE /api/items endpoints (auth-gated)

frontend/            # Next.js app (separate JS project)
  package.json
  next.config.js
  auth.ts            # Better Auth client configuration
  src/
    app/
      layout.tsx     # Root layout
      page.tsx       # Todo list page (US2, US3) — auth-gated redirect to /login
      login/
        page.tsx     # Login page (US1)
      register/
        page.tsx     # Registration page (US1)
      api/
        auth/
          [...all]/route.ts   # Better Auth server handler; serves /api/auth/* (register/login/logout)
    lib/
      auth.ts        # Better Auth server-side session helpers (session(), getSession())
      api.ts         # Client-side fetch helpers for the FastAPI /api/items endpoints
    components/
      TodoList.tsx   # Item list, add, complete, delete UI
      AuthForm.tsx   # Login/register form component

tests/
  test_store.py      # Phase I tests — UNCHANGED, must stay green
  test_cli.py        # Phase I tests — UNCHANGED, must stay green
  test_auth.py       # Better Auth session verification helpers (unit)
  test_models.py     # SQLModel model tests (unit)
  test_api.py        # Full request/response flows via httpx AsyncClient (integration)
```

**Structure Decision**: Monorepo layout. The FastAPI backend lives in `src/todo_app` alongside the
unchanged Phase I CLI modules (research.md D8). A new `[project.scripts] todo-app-api =
"todo_app.api.app:main"` entry starts the API server. The Next.js frontend is a self-contained JS
project under `frontend/`: Better Auth runs inside the Next.js app and serves the `POST /api/auth/*`
auth endpoints (register, login, logout) that the approved contracts define (research.md D5/D6);
the FastAPI backend serves the `GET/POST/PATCH/DELETE /api/items` endpoints and verifies the Better
Auth session token from the request cookie before granting access. SQLModel models define the
PostgreSQL schema; Neon PostgreSQL is a managed external service, so no embedded database is needed
(research.md D3/D4).

## Behavior by user story (traceability)

| Story | Behavior (from spec)                                                         | Where implemented by convention                                |
|-------|-------------------------------------------------------------------------------|----------------------------------------------------------------|
| US1   | register, log in, log out, session                                            | Better Auth in Next.js (`frontend/src/app/api/auth/[...all]`), `POST /api/auth/*` |
| US2   | add + list items in the web UI, empty list message                            | Next.js `TodoList` component, `GET/POST /api/items`            |
| US3   | mark complete + delete with graceful errors                                   | `PATCH/DELETE /api/items/{id}` + `TodoList` component          |
| US4   | data survives logout/login and restart                                        | Neon PostgreSQL via SQLModel, `database.py`                    |
| US5   | per-user isolation on every path; unauth requests rejected                    | owner-scoped SQLModel queries; Better Auth session check on all `/api/items` |

The column above names conventional module responsibilities only; exact function names and
representations are implementation choices (same convention as Phase I review correction 1).

## Tests (test-first gate — mandatory before implementation)

Tests MUST be written and user-approved before implementation begins (constitution Principle II;
AGENTS.md). They cover the observable behavior in `data-model.md` and `contracts/*.md`, not internal
return strings. These build on the existing, unmodified Phase I tests:

- `tests/test_api.py` (httpx `AsyncClient`, full request/response with cookies against FastAPI):
  - add item with a valid session cookie -> 201 and appears in list; empty description -> 400, no item;
  - list shows owned items only; empty list returns `{"items": []}`;
  - PATCH complete (and idempotent re-complete) -> 200 updated; DELETE -> 204 and gone;
  - PATCH/DELETE nonexistent or another user's item -> 404, nothing changed;
  - persistence: items/statuses identical after logout+login and after re-creating the app+DB;
  - isolation: two users' lists never cross; unauth or invalid-cookie access to every `/api/items`
    path -> 401.
- Frontend tests (Next.js + Better Auth, run under `npm --prefix frontend test`):
  - register success -> session + list page; duplicate username -> 409; blank password -> 400;
  - login success -> session; wrong password -> 401, user remains unauthenticated;
  - logout ends the session; `/` redirects unauthenticated users to `/login` (FR-006, SC-006);
  - TodoList add/list/complete/delete behavior against the /api/items proxy.
- `tests/test_auth.py` (unit):
  - Better Auth session helpers round-trip a user_id and reject tampered/absent values;
  - session verification succeeds for valid sessions and fails for invalid/expired ones.
- `tests/test_models.py` (unit):
  - SQLModel models create, read, update, and enforce constraints correctly.
- `tests/test_store.py`, `tests/test_cli.py`: unchanged; must remain green (FR-014).

Test execution: backend `uv run python -m unittest discover -s tests -v`; frontend
`npm --prefix frontend test` (see `quickstart.md`).

## Review Corrections Applied

**Plan Review gate (this revision)**: The original plan selected Flask, Jinja2 + vanilla JS,
SQLite, Werkzeug scrypt, and signed-cookie sessions. These are not the required Phase II
Hackathon technology choices. Revised to use the mandatory stack: Next.js (frontend), FastAPI
(backend API), SQLModel (ORM), Neon PostgreSQL (database), Better Auth (authentication).
All functional requirements (FR-001 through FR-015) and success criteria (SC-001 through SC-006)
are preserved unchanged. The Phase I CLI/store is preserved unchanged and backward-compatible
(FR-014). No source code was modified. No features or technologies beyond the approved Phase II
specification are planned.
