# Quickstart: Full-Stack Todo

**Feature**: `002-full-stack-todo` | **Phase**: 1 (Design & Contracts) | **Date**: 2026-09-16

Runnable, end-to-end validation scenarios for the approved Phase II scope. Data/entity details are
in [data-model.md](data-model.md); API behavior is in [contracts/api.md](contracts/api.md) and page
behavior in [contracts/pages.md](contracts/pages.md).

## Prerequisites

- Python 3.13+ and `uv` installed.
- Node.js 18+ and `npm` installed (for the Next.js frontend).
- A Neon PostgreSQL database; its connection string is provided via the `DATABASE_URL` environment
  variable (see research.md D3).

## Setup

```sh
uv sync                       # installs FastAPI, SQLModel, and backend deps
npm --prefix frontend install # installs Next.js frontend deps
```

Set the environment variables required by the backend:

```sh
export DATABASE_URL=postgresql://<neon-host>/<db>      # Neon PostgreSQL connection string
export BETTER_AUTH_SECRET=<stable-random-secret>       # session signing key
```

## Run

```sh
uv run todo-app-api          # FastAPI backend on http://127.0.0.1:8000
npm --prefix frontend run dev # Next.js frontend on http://localhost:3000
```

Open http://localhost:3000 in a browser. The Next.js frontend proxies its item API calls to the
FastAPI backend (see `frontend/lib/api.ts`). The FastAPI server listens at `http://127.0.0.1:8000`.

## Validate tests

Backend:

```sh
uv run python -m unittest discover -s tests -v
```

All tests (written and user-approved before implementation, per the test-first gate) must pass. This
includes the existing Phase I CLI and store tests, which must remain green (FR-014).

Frontend:

```sh
npm --prefix frontend test
```

Frontend component tests (written and user-approved before implementation) must pass.

## Manual validation scenarios

Fresh database between scenarios unless stated. Where used, `api calls` are exercised through the
browser UI on the Next.js `/` page against the FastAPI API (FR-008).

### Scenario 1 — Register and log in (US1, FR-001/003/004)

- Open `/register`, enter username `alice` and a non-blank password, submit.
- Expected: an account is created, a session is established, and the todo list page is shown.
- Click "Log out": the session ends (US1 S4).
- Open `/login`, enter the same credentials, submit.
- Expected: authenticated access is granted and the list page is shown again.
- Log out, then log in with the correct username but the wrong password.
- Expected: access denied with a clear error; the page still shows the login prompt (FR-004, US1 S3).

### Scenario 2 — Add items (US2, FR-011/012)

- As `alice`, on `/`, add `Buy milk` then `Water plants`.
- Expected: both appear immediately as `incomplete`, each with a unique id (FR-011).

### Scenario 3 — List / empty list / statuses (US2, FR-014)

- Continue from Scenario 2 and view the list.
- Expected: both items show description and completion status.
- Delete both items; the page then clearly indicates there are no items (US2 S4).

### Scenario 4 — Mark complete and delete (US3)

- Add `Write report`, then mark it complete.
- Expected: its status changes to complete and the list reflects the change (US3 S1).
- Mark it complete again.
- Expected: handled gracefully, no conflicting state (US3 S2).
- Delete `Water plants`; it no longer appears (US3 S3).
- Attempt to complete/delete an item with a non-existent or another user's id.
- Expected: a clear error message, no change (US3 S4, US5 S2).

### Scenario 5 — Empty description rejected (US2 S3, FR-012)

- On `/`, submit an add form with an empty or whitespace-only description.
- Expected: a clear error; no item created.

### Scenario 6 — Duplicate username and blank password (FR-002, Edge Cases)

- Register a second account with username `alice`.
- Expected: an error; no duplicate account created.
- Register with a blank password.
- Expected: an error; no account created.

### Scenario 7 — Persistence across sessions (US4, SC-002)

- As `alice`, add items and mark some complete.
- Log out, then log back in.
- Expected: every item and its completion status is present exactly as left (SC-002).

### Scenario 8 — Persistence across restart (US4, SC-003)

- Continue with `alice`'s items from Scenario 7.
- Stop both the backend and frontend servers, run `uv run todo-app-api` and
  `npm --prefix frontend run dev` again, and log in.
- Expected: the account and all items and statuses persist unchanged (SC-003).

### Scenario 9 — Multi-user isolation (US5, SC-005)

- Create account `alice` (add `Alice task`) and account `bob` (add `Bob task`), each in its own
  browser session.
- While logged in as `alice`: expected list shows only `Alice task`; `Bob task` is invisible (SC-005).
- While logged in as `bob`: expected list shows only `Bob task`.
- While logged in as `alice`, attempt to complete/delete the id of `Bob task` (knowable from the
  API/PATCH guessing).
- Expected: the request is rejected with a clear error and `Bob task` is unchanged (US5 S2).

### Scenario 10 — Unauthenticated access denied (US5 S3, FR-006, SC-006)

- With no session (fresh browser), open `/` and attempt `GET /api/items`, `POST /api/items`,
  `PATCH /api/items/{id}`, `DELETE /api/items/{id}`.
- Expected: each is rejected with a clear auth error and the user is directed to authenticate
  (SC-006).

## Success criteria covered

- SC-001: Scenarios 1 + 2 (register, log in, add a first item in the browser quickly).
- SC-002: Scenario 7 (items/statuses identical after logout + login).
- SC-003: Scenario 8 (identical after restart + login).
- SC-004: Scenarios 2, 3, 4 (add, view, complete, delete entirely through the web UI, no console).
- SC-005: Scenario 9 (two accounts, neither can view or modify the other's items).
- SC-006: Scenario 10 (every unauthenticated todo request rejected and directed to authenticate).
- FR-014: test suite keeps the Phase I CLI/store tests green; `uv run todo-app` still works.