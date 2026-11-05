# Data Model: Full-Stack Todo

**Feature**: `002-full-stack-todo` | **Phase**: 1 (Design & Contracts) | **Date**: 2026-09-16

Extracted from the approved specification. Only attributes, rules, and relationships traceable to
`spec.md` are listed; concrete SQL/representation details are implementation choices (research.md).

## Entity: User

A registered account that owns exactly one todo list (Key Entities; FR-001, FR-013).

| Attribute       | Type          | Rule                                                                            | Traceability              |
|-----------------|---------------|---------------------------------------------------------------------------------|---------------------------|
| `id`            | positive int  | Assigned on registration, unique                                                | Key Entities, FR-001      |
| `username`      | non-empty text| Unique; required at registration; duplicate rejected                            | FR-001, FR-002, Edge Cases|
| `password`      | non-empty text| Required at registration; blank password rejected; never stored or displayed in plaintext | FR-002, Assumptions       |

Notes:

- The password is stored as a one-way salted hash managed by Better Auth, never in plaintext
  (research.md D5).
- `username` uniqueness is enforced at the database and returned as a clear registration error
  (Edge Cases).

## Entity: TodoItem

A task created by a user, retaining the Phase I item behavior (Key Entities, FR-014).

| Attribute     | Type          | Rule                                                              | Traceability        |
|---------------|---------------|-------------------------------------------------------------------|---------------------|
| `id`          | positive int  | Assigned on creation, unique and reusable to act on the item      | FR-011, US2         |
| `description` | non-empty text| Required at creation; empty description rejected with an error     | FR-012, US2         |
| `completed`   | boolean       | Completion status: complete or incomplete                          | Key Entities, FR-014|
| `owner`       | User          | Each item belongs to exactly one user; item is only accessible to that user | FR-013, US5 |

## Relationships

- `User` 1 — \* `TodoItem` (a user owns many items; every item has exactly one owner). Enforced by
  a foreign key `TodoItem.user_id -> User.id` and isolation enforced on every query by owner scope
  (FR-013).
- `User` 1 — 1 Better Auth session (an authenticated session maps to exactly one user; FR-003).

## Validation rules

Derived from FR-002, FR-012, and the Edge Cases section:

- Registration: `username` must be non-empty and not already registered; `password` must be
  non-blank.
- Item description must be non-empty (whitespace-only descriptions are rejected).
- An item id used for complete/delete must reference an existing item owned by the current user;
  otherwise the request is rejected with a clear error (US3 S4, US5 S2).
- Long descriptions are accepted without crashing (Edge Cases); no arbitrary length limit is imposed
  by the spec.

## State transitions

- `TodoItem.incomplete -> complete`: the only item state transition in scope, from "mark complete"
  (US3). Re-marking an already-complete item is handled gracefully as a no-op (US3 S2).
- `TodoItem` is created in `incomplete` state by an authenticated user (US2 S1).
- No reverse transition (reopen) is defined by the specification.

## Persistence invariants

- Data lives in Neon PostgreSQL so it survives logout and application restart (FR-009, FR-010).
- Deleting a user is not in scope; there is no cascade requirement.
- Item deletion removes the row permanently for that owner (US3 S3).
- Multi-user isolation is a persistent invariant: no stored item is ever visible to or mutable by a
  non-owner (FR-013, US5).

## Representation note

Concrete SQL schema, column types, and class representations are implementation choices made during
implementation (AGENTS.md: no invented architecture). The observable behavior — unique usernames,
non-empty descriptions, per-user isolation, durable completion status — is the approved contract.
SQLModel models define the schema against PostgreSQL (research.md D3/D4); Better Auth manages the
password and session storage (research.md D5/D6).