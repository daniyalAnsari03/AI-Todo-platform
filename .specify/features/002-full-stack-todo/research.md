# Research: Full-Stack Todo

**Feature**: `002-full-stack-todo` | **Phase**: 0 (Outline & Research) | **Date**: 2026-09-16

Resolves every `NEEDS CLARIFICATION` from the Technical Context and records the minimal,
spec-traceable design choices below.

## Decision 1: Backend framework

- **Decision**: FastAPI as the backend API framework, running on uvicorn (ASGI server).
- **Rationale**: The specification requires a programmatic web API (FR-008) serving the frontend.
  FastAPI provides async request handling, automatic OpenAPI docs, Pydantic request/response
  validation, and dependency injection — all with minimal boilerplate. It is the required Phase II
  backend framework per the Hackathon specification.
- **Alternatives considered**:
  - Flask: not the required Hackathon stack; selected originally but corrected at plan review.
  - Django REST Framework: far larger than the five required API endpoints.
  - Starlette directly: lower-level; FastAPI builds on Starlette with validation and docs.

## Decision 2: Frontend approach

- **Decision**: Next.js (React, App Router) as the web frontend framework. Client-side rendering
  for the todo list; server-side rendering only where Next.js defaults to it (layout, initial load).
- **Rationale**: FR-007 (web frontend for add/view/complete/delete) is satisfied by a React SPA
  consuming the FastAPI JSON API. Next.js is the required Phase II frontend per the Hackathon
  specification. The App Router provides file-based routing, server components for the initial
  layout, and client components for interactive item operations.
- **Alternatives considered**:
  - Jinja2 + vanilla JS: not the required Hackathon stack; selected originally but corrected.
  - Vite + React (no Next.js): lacks the server-side features the Hackathon spec requires.
  - Vue/Svelte: not the required framework.

## Decision 3: Persistence

- **Decision**: Neon PostgreSQL (managed cloud PostgreSQL) as the database. Connection via
  `DATABASE_URL` environment variable. SQLModel (SQLAlchemy + Pydantic) as the ORM.
- **Rationale**: FR-009 (items and statuses survive logout and restart) and FR-010 (accounts
  survive restart) require durable storage. Neon PostgreSQL is the required Phase II database per
  the Hackathon specification. It is a managed service requiring no local server installation;
  connection is via a standard PostgreSQL connection string. SQLModel provides type-safe ORM models
  with Pydantic validation, fitting naturally with FastAPI's Pydantic-based request/response
  handling.
- **Alternatives considered**: SQLite (not the required Hackathon database); MySQL (not specified).

## Decision 4: ORM / data layer

- **Decision**: SQLModel for defining User and TodoItem models, managing database sessions, and
  running schema migrations. SQLModel combines SQLAlchemy's ORM with Pydantic's validation.
- **Rationale**: SQLModel is the required Phase II data layer per the Hackathon specification. It
  provides type-safe models that double as Pydantic schemas for FastAPI request/response validation,
  eliminating the need for separate schema definitions. Database sessions are managed via FastAPI
  dependency injection.
- **Alternatives considered**: SQLAlchemy alone (requires separate Pydantic schemas); Pydantic alone
  (no ORM); Tortoise ORM (not specified).

## Decision 5: Authentication

- **Decision**: Better Auth for user registration, login, logout, and session management. Better
  Auth handles password hashing, session token creation/verification, and provides session
  validation utilities usable from both the Next.js frontend and the FastAPI backend.
- **Rationale**: The Hackathon specification requires Better Auth as the Phase II authentication
  system. It provides secure password hashing, session management, and CSRF protection out of the
  box. On the Next.js side, Better Auth handles the auth flows (register, login, logout) via its
  API routes. On the FastAPI side, session tokens from cookies are verified to protect the
  `/api/items` endpoints.
- **Alternatives considered**: Werkzeug scrypt + signed cookies (selected originally but corrected
  at plan review); Passport.js (Node-only); custom auth (YAGNI, security risk).

## Decision 6: Session management

- **Decision**: Better Auth manages sessions. Sessions are stored in the Neon PostgreSQL database
  via Better Auth's adapter. The Next.js frontend receives session cookies from Better Auth's API
  routes. The FastAPI backend validates session tokens from request cookies on protected endpoints.
- **Rationale**: FR-003 (session on successful login) and FR-005 (logout ends the session) are met
  by Better Auth's session management. Sessions stored in the database survive server restarts.
  The `SECRET_KEY` for session signing is read from the `BETTER_AUTH_SECRET` environment variable.
- **Alternatives considered**: Flask signed-cookie sessions (not applicable with FastAPI); JWT-only
  (no server-side revocation); server-side token store (Better Auth handles this).

## Decision 7: Web server entry point

- **Decision**: FastAPI backend entry via `uv run todo-app-api` (a `[project.scripts]` entry
  calling `uvicorn` on the FastAPI app). Next.js frontend entry via `npm run dev` in `frontend/`.
- **Rationale**: Gives two runnable commands consistent with the monorepo structure: the Python
  backend mirrors the existing `todo-app` CLI entry pattern, and the Next.js frontend follows the
  standard `npm run dev` convention. In production, a process manager or container orchestrator
  would run both; for local development, both are started separately.
- **Alternatives considered**: single-entry proxy (adds complexity); Docker Compose (YAGNI for
  local dev).

## Decision 8: Project structure

- **Decision**: Monorepo. Keep a single Python package under `src/todo_app`. Preserve `store.py`
  and `__init__.py` (the Phase I CLI) unchanged and backward-compatible (FR-014, spec assumption).
  New Python code is added as `models.py`, `database.py`, `auth.py`, and an `api/` subpackage
  (FastAPI routes). The Next.js frontend lives in `frontend/` at the repository root as a
  separate JS project with its own `package.json`.
- **Rationale**: The spec requires the CLI to remain supported and not be rewritten. Adding
  FastAPI modules alongside the CLI satisfies FR-008/FR-009/FR-013 without a new top-level
  Python layout. The Next.js frontend is a separate JS runtime and naturally lives outside
  `src/todo_app`. The `pyproject.toml` manages Python deps; `frontend/package.json` manages
  JS deps.
- **Alternatives considered**: single-process with Flask server-side rendering (not the required
  stack); splitting `backend/` + `frontend/` as top-level directories (moves Python code out of
  `src/todo_app`, violating the constitution constraint); rewriting the store (forbidden by FR-014).

## Decision 9: Item identity and ownership

- **Decision**: SQLModel defines a `TodoItem` table with a PostgreSQL `SERIAL` primary key
  (`id`) and a `user_id` foreign key to the `User` table. Every read/write is scoped by the
  authenticated user's id via SQLModel query filters, so a user can only see/act on their own rows.
- **Rationale**: FR-011 requires each new item to have a unique identifier usable to act on it;
  PostgreSQL auto-increment satisfies this. FR-013 requires per-user isolation and one owner per
  item; the foreign key plus owner-scoped queries enforces it in every path, including the case
  where a user targets an id belonging to another user (404 for the requester, US5 S2).
- **Alternatives considered**: UUID primary keys (more schema complexity, no required behavior gain);
  composite `(user_id, id)` keys (unnecessary); shared/inherited items (out of Phase II scope).

## Unresolved items

None. All Technical Context unknowns are resolved above.
