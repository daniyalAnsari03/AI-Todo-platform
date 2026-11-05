# CLI Contract: Console Todo

**Feature**: `001-console-todo` | **Phase**: 1 (Design & Contracts) | **Date**: 2026-09-16

The external interface is the interactive CLI. This contract describes observable behavior only —
command grammar, stream placement, and state effects — as traceable to `spec.md`. It does NOT define
internal store method signatures or return strings (review correction 2).

## Protocol

- One command per line on `stdin` (FR-001).
- Data, prompts, and confirmation/informational messages on `stdout`.
- Error messages on `stderr` (FR-010, FR-011).
- Exact message wording is an implementation detail and is not part of this contract.

## Command grammar

The command name is the first whitespace-separated token; the rest of the line is the argument.

| Command            | Argument | Behavior (traceability)                                          |
|--------------------|----------|------------------------------------------------------------------|
| `add <description>`| text     | Create item with the next sequential positive ID (FR-002, FR-003). Confirm on stdout (US1 S1). Empty/whitespace-only description -> error on stderr, no item created (US1 S3, FR-010). |
| `list`             | —        | Print all stored items as `id`, description, and completion status on stdout (FR-004, US2 S1). With no items, print a message indicating none stored (US2 S2). |
| `complete <id>`    | positive int | Mark item complete and confirm on stdout (FR-005, US3 S1). Already complete -> message indicating already complete (US3 S2). Non-existent id -> error on stderr (US3 S3). |
| `delete <id>`      | positive int | Remove item and confirm on stdout (FR-006, US4 S1). Non-existent id -> error on stderr (US4 S2). |
| `exit`             | —        | Terminate the process with exit code 0 (FR-007, US5).           |
| `help`             | —        | Print the list of valid commands (FR-008).                      |
| *(unrecognized)*   | —        | Print the help message listing valid commands (FR-008, Edge Cases). |

## ID validation (Edge Cases, FR-010)

For `complete` and `delete`, an id that is:

- non-numeric, or
- less than or equal to zero

produces an error message on `stderr` indicating the id must be a positive integer.

## State effects

- `add`: store grows by one item in `incomplete` state.
- `complete`: the referenced item's status becomes `complete`.
- `delete`: the referenced item is permanently removed for the session.
- `list`: read-only.

## Out of scope

- Persistence across sessions (FR-009).
- JSON or other structured output (not required by Phase I).
- Editing, reordering, filtering, priorities, due dates, collaboration (not in Phase I).