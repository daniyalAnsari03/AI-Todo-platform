# Web API Contract: Full-Stack Todo

**Feature**: `002-full-stack-todo` | **Phase**: 1 (Design & Contracts) | **Date**: 2026-09-16

The programmatic HTTP API serving the web frontend (FR-008) and giving authenticated users the same
add, view, mark-complete, and delete operations (FR-007/FR-008). This contract describes observable
behavior only — request shapes, status codes, and state effects — as traceable to `spec.md`. Exact
message wording is an implementation detail. The endpoints are implemented by the FastAPI backend
(see `research.md` D1); sessions are managed by Better Auth and authenticated session cookies carry
the user identity (see `research.md` D5/D6).

## Base conventions

- JSON request/response bodies with `Content-Type: application/json`.
- Endpoints under `/api/`. Page routes are in [pages.md](pages.md).
- Auth error shape: `401` with a JSON `{"error": "..."}` message for unauthenticated requests to
  todo endpoints (FR-006, US5 S3).
- State-effect 404s for non-existent or non-owned items return a JSON error message (US3 S4, US5
  S2); they never leak the resource's existence to other users.

## Endpoints

### POST /api/auth/register — register a new user and establish a session (FR-001, FR-002)

Request body (FR-001):

```json
{ "username": "alice", "password": "s3cret" }
```

| Condition                                  | Status | Effect / body                                   | Traceability       |
|--------------------------------------------|--------|--------------------------------------------------|--------------------|
| Username unused, password non-blank        | 201    | Account created, session active; `{"id": ..., "username": ...}` | FR-001, FR-003 |
| Username already exists                    | 409    | Error message, no account created, no session    | FR-002, Edge Cases |
| Blank password (or blank/absent username)  | 400    | Error message, no account created, no session    | FR-002, Edge Cases |

### POST /api/auth/login — authenticate and establish a session (FR-003, FR-004)

Request body:

```json
{ "username": "alice", "password": "s3cret" }
```

| Condition                        | Status | Effect / body                                   | Traceability       |
|----------------------------------|--------|--------------------------------------------------|--------------------|
| Username and password correct    | 200    | Session active; `{"id": ..., "username": ...}`   | FR-003             |
| Incorrect username or password   | 401    | Error message; user remains unauthenticated      | FR-004, US1 S3     |

### POST /api/auth/logout — end the session (FR-005)

- Requires an active session.
- Always responds `204 No Content` and clears the session (US1 S4).

### GET /api/items — list the authenticated user's items (FR-007, FR-013)

| Condition                      | Status | Body                                                              | Traceability        |
|--------------------------------|--------|-------------------------------------------------------------------|---------------------|
| Authenticated, some items      | 200    | `{"items": [{"id": 1, "description": "...", "completed": false}, ...]}` | FR-013, US2 S2 |
| Authenticated, no items        | 200    | `{"items": []}`                                                   | US2 S4              |
| Unauthenticated                | 401    | Error message                                                     | FR-006, US5 S3      |

### POST /api/items — add an item (FR-012, FR-011)

Request body:

```json
{ "description": "Buy milk" }
```

| Condition                          | Status | Effect / body                                                     | Traceability       |
|------------------------------------|--------|-------------------------------------------------------------------|--------------------|
| Authenticated, non-empty description | 201  | Item created as `incomplete`, owned by the user; `{"id": ..., "description": ..., "completed": false}` | FR-011, FR-013, US2 S1 |
| Empty or whitespace-only description| 400  | Error message; no item created                                    | FR-012, US2 S3     |
| Unauthenticated                    | 401    | Error message                                                     | FR-006, US5 S3     |

### PATCH /api/items/{id} — mark an item complete (US3)

Request body:

```json
{ "completed": true }
```

| Condition                                            | Status | Effect / body                                            | Traceability   |
|------------------------------------------------------|--------|----------------------------------------------------------|----------------|
| Authenticated owner, item incomplete, `true`          | 200    | Item marked complete; updated item JSON                  | US3 S1         |
| Authenticated owner, item already complete, `true`    | 200    | No state conflict; item stays complete (graceful no-op)  | US3 S2         |
| Authenticated, item does not exist or not owned       | 404    | Error message; no change to any item                     | US3 S4, US5 S2 |
| Unauthenticated                                      | 401    | Error message                                            | FR-006, US5 S3 |

The specification defines no reverse transition; a `completed` value other than `true` is rejected
with `400` and no state change.

### DELETE /api/items/{id} — delete an item (US3)

| Condition                                   | Status | Effect / body          | Traceability   |
|---------------------------------------------|--------|------------------------|----------------|
| Authenticated owner, item exists            | 204    | Item permanently removed, never visible to anyone | US3 S3, FR-013 |
| Authenticated, item does not exist or not owned | 404 | Error message; no change | US3 S4, US5 S2 |
| Unauthenticated                             | 401    | Error message          | FR-006, US5 S3 |

## State effects

- `register`/`login`: a session cookie is set; the user is treated as authenticated thereafter.
- `logout`: the session cookie is cleared.
- `POST /api/items`: the authenticated user's list grows by one item in `incomplete` state.
- `PATCH /api/items/{id}`: the referenced item's status becomes `complete` (idempotent no-op when
  already complete).
- `DELETE /api/items/{id}`: the referenced item is removed permanently from that user's list only.
- `GET /api/items`: read-only.

## Out of scope

- Shared/collaborative lists (Phase II assumption: no cross-user sharing).
- Editing descriptions, reordering, filtering, priorities, due dates (not in the Phase II spec).
- Reopening completed items (no reverse transition defined).