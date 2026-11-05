# Data Model: Console Todo

**Feature**: `001-console-todo` | **Phase**: 1 (Design & Contracts) | **Date**: 2026-09-16

Extracted from the approved specification. Only attributes and rules traceable to `spec.md` are
listed; concrete Python representations are implementation choices.

## Entity: TodoItem

| Attribute        | Type          | Rule                                                              | Traceability        |
|------------------|---------------|-------------------------------------------------------------------|---------------------|
| `id`             | positive int  | Assigned on creation, unique, sequentially increasing per session | FR-003, US1         |
| `description`    | non-empty text| Required at creation; empty input rejected                         | FR-002, FR-010, US1 |
| `completed`      | boolean       | Completion status: complete or incomplete                          | Key Entities, US2   |

Validation rules (from FR-010 and Edge Cases):

- Description must be non-empty (whitespace-only is empty).
- `id` for `complete`/`delete` must be a positive integer: non-numeric, zero, or negative values are
  invalid.
- IDs reference existing items only; non-existent IDs are invalid.

State transitions:

- `incomplete -> complete`: the only transition in scope (mark complete). No reverse transition is
  defined by the specification.
- `add` creates an item in `incomplete` state.

## In-memory Store

- One store instance per application session; data is lost on exit (FR-009).
- Holds `{id: TodoItem}`; a counter assigns the next `id` (1, 2, 3, ...) without reuse.
- Invariants:
  - IDs are distinct and strictly increasing.
  - An item deleted by ID is removed from the store (FR-006).
  - Marking complete only mutates `completed`; it does not remove or renumber items.

## Representation note

The item may be implemented as a small plain class or a `dataclass`; the store as a class holding a
dict. These are implementation choices made during implementation, NOT approved requirements (review
correction 1). The observable behavior (IDs, descriptions, completion status in `list` output) is the
approved contract.