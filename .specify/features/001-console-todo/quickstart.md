# Quickstart: Console Todo

**Feature**: `001-console-todo` | **Phase**: 1 (Design & Contracts) | **Date**: 2026-09-16

Runnable, end-to-end validation scenarios for the approved Phase I scope. Data/entity details are in
[data-model.md](data-model.md); behavior details are in [contracts/commands.md](contracts/commands.md).

## Prerequisites

- Python 3.13+ and `uv` installed.
- Project dependencies managed via `uv` (no runtime dependencies).

## Setup

```sh
uv sync
```

## Run

```sh
uv run todo-app
```

The application waits for one command per line on stdin.

## Validate tests

```sh
uv run python -m unittest discover -s tests -v
```

All tests (written and user-approved before implementation, per the test-first gate) must pass.

## Manual validation scenarios

### Scenario 1 — Add items (US1, FR-002, FR-003)

Commands:
```
add Buy milk
add Water plants
```
Expected: two confirmation messages; the first item is assigned id `1`, the second id `2` (distinct,
sequentially increasing, positive).

### Scenario 2 — Add with empty description (US1 S3, FR-010)

```
add
add  
```
Expected: an error on stderr for each empty/whitespace-only description; no items created. Verify with
`list`.

### Scenario 3 — List items / empty list (US2)

After Scenario 1:
```
list
```
Expected: both items shown with id, description, and completion status (all incomplete). On a fresh
run:
```
list
```
Expected: a message indicating no items are stored.

### Scenario 4 — Mark complete (US3)

```
complete 1
list
```
Expected: confirmation; item 1 now shows status complete.

```
complete 1
```
Expected: a message indicating item 1 was already complete.

```
complete 99
```
Expected: an error on stderr (no such item).

### Scenario 5 — Delete (US4)

```
delete 2
list
```
Expected: confirmation; item 2 no longer appears.

```
delete 2
```
Expected: an error on stderr (no such item).

### Scenario 6 — Invalid ids (Edge Cases, FR-010)

```
complete abc
delete -1
complete 0
```
Expected: an error on stderr for each, stating the id must be a positive integer; no state changes.

### Scenario 7 — Unknown command shows help (FR-008)

```
frobnicate
```
Expected: the help message listing valid commands on stdout.

### Scenario 8 — Exit (US5, FR-007)

```
exit
```
Expected: the application terminates gracefully with exit code 0.

## Success criteria covered

- SC-001: Scenario 1 (add + immediate confirmation).
- SC-002: Scenario 2/3 (single-view listing with id, description, status).
- SC-003: Scenario 4 (complete -> verified in list with 100% accuracy).
- SC-004: Scenario 5 (delete -> confirmed gone in list).
- SC-005: Scenarios 2, 4, 5, 6, 7 (graceful errors, no crash).