# Web Pages Contract: Full-Stack Todo

**Feature**: `002-full-stack-todo` | **Phase**: 1 (Design & Contracts) | **Date**: 2026-09-16

The React pages rendered by the Next.js frontend that make up the web frontend (FR-007). Pages live
under `frontend/src/app` using the Next.js App Router; item operations on the list page are performed
against the JSON API in [api.md](api.md), which is the programmatic web API serving the frontend
(FR-008). This contract describes observable page behavior only — routes, auth gating, and
redirection — as traceable to `spec.md`. Exact markup and styling are implementation details.

## Routes

### GET / — todo list page (US2, FR-007)

- **Authenticated**: renders the current user's list — every item with its description and
  completion status, an empty-list message when the user has no items (US2 S4), and controls to
  add, mark complete, and delete items. Item actions call the API endpoints in [api.md](api.md).
- **Unauthenticated**: redirects to `/login` so the user can authenticate (FR-006, US5 S3, SC-006).

### GET /login — login page (US1, FR-003/FR-004)

- Renders the login form. Submitting posts `{username, password}` to `POST /api/auth/login`
  ([api.md](api.md)).
- On success the user is taken to `/`; on failure a clear error is shown and the user remains
  unauthenticated (FR-004, US1 S3).
- A link to `/register` is provided for new users.

### GET /register — registration page (US1, FR-001/FR-002)

- Renders the registration form. Submitting posts `{username, password}` to
  `POST /api/auth/register` ([api.md](api.md)).
- Success creates the account, establishes a session, and takes the user to `/` (FR-001, FR-003).
- Duplicate username and blank-password failures show clear errors and create no account
  (FR-002, Edge Cases).

### GET /logout — end the session (FR-005, US1 S4)

- Posts `POST /api/auth/logout` ([api.md](api.md)), then redirects to `/login`.
- The list page is no longer accessible afterwards without logging in again.

## Observable rules

- All todo functionality is gated on an active session (FR-006, SC-006); unauthenticated navigation
  anywhere near todo data redirects to `/login`.
- The frontend never displays passwords in any form (Assumptions).
- The list and its statuses come from the same durable store as the API (FR-009), so what the page
  shows is identical across logout/login and restart (SC-002, SC-003).

## Out of scope

- A separate mobile app or a non-Next.js frontend (research.md D2 fixes the frontend to Next.js).
- Any appearance, branding, or layout requirements (not in the spec).