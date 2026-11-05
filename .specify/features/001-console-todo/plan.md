# Implementation Plan: Console Todo

**Branch**: `001-console-todo` | **Date**: 2026-09-16 | **Spec**: `spec.md` (same feature directory)

**Input**: Feature specification from `.specify/features/001-console-todo/spec.md`

**Note**: Revised per plan-review feedback (see "Review Corrections Applied").

## Summary

Build a minimal Python CLI todo application (Phase I): a single-user interactive session reading one
command per line from stdin, storing items in memory only, and supporting exactly `add`, `list`,
`complete`, `delete`, `exit`, and `help`. Data and confirmations go to stdout; errors go to stderr.
Zero runtime dependencies beyond the Python 3.13 standard library.

## Technical Context

| Item                | Value                                                                  |
|---------------------|------------------------------------------------------------------------|
| Language/Version    | Python 3.13+ (declared in `pyproject.toml` / `.python-version`)         |
| Primary Dependencies| None at runtime (standard library only)                                 |
| Storage             | In-memory only (FR-009); no persistence                                |
| Testing             | `unittest` (standard library); test-first, user-approved before code    |
| Target Platform     | Local terminal with stdin/stdout support                                |
| Project Type        | CLI application (interactive REPL)                                      |
| Performance Goals   | Not applicable; SC-001 (add visible within 10s) is a UX bound, trivial  |
| Constraints         | No persistence; data on stdout, errors on stderr; single-user session   |
| Scale/Scope         | One interactive session; the six Phase I commands only                  |

All unknowns resolved — see `research.md`.

## Constitution Check

*GATE: Passes before Phase 0 and after Phase 1 design.*

- **I. Spec-First**: This plan and its artifacts are derived exclusively from the approved `spec.md`;
  no new requirements are introduced. ✔
- **II. Test-First**: Delivery FLOW is test-first: tests are written and REVIEWED/APPROVED by the user
  before ANY implementation begins, then red → green → refactor. A feature is complete only when all
  approved tests pass. ✔
- **III. Lifecycle & Gates**: No stage skipped. This plan awaits the plan-review gate; task creation
  and implementation follow only after explicit approval. ✔
- **IV. Versioning**: No version or constitution change; no breaking change. ✔
- **V. Simplicity & CLI Usability**: Smallest design satisfying the spec; clear text-in/text-out
  (prompts/data on stdout, errors on stderr); JSON not added because Phase I does not require it. ✔
- **Additional Constraints**: Python 3.13+ ✔; `uv` + `uv_build` unchanged ✔; code under
  `src/todo_app` ✔.

No violations; Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
.specify/features/001-console-todo/
├── spec.md            # Approved feature specification
├── plan.md            # This file
├── research.md        # Phase 0 output: minimal design decisions
├── data-model.md      # Phase 1 output: entities and invariants
├── quickstart.md      # Phase 1 output: runnable validation guide
└── contracts/
    └── commands.md    # Phase 1 output: CLI command contract
```

### Source Code (repository root)

```text
src/todo_app/
├── __init__.py        # main(): REPL loop, command dispatch, I/O streams
└── store.py           # TodoStore: in-memory store (add/list/complete/delete)

tests/
├── test_store.py      # Store behavior (unit)
└── test_cli.py        # CLI observable behavior (stdout/stderr, exit code)
```

**Structure Decision**: Single project, matching the existing `[project.scripts] todo-app =
"todo_app:main"` entry in `pyproject.toml`. Tests sit at the repository root next to `src/`, as in the
plan template's default single-project shape.

## Behavior by user story (traceability)

| Story | Behavior (from spec)                                 | Where implemented by convention        |
|-------|------------------------------------------------------|----------------------------------------|
| US1   | add + next positive id             | `store.add` (store), `add` handler (CLI) |
| US2   | list shows id, description, status | `store.list`, `list` handler            |
| US3   | mark complete by id                | `store.complete`, `complete` handler     |
| US4   | delete by id                       | `store.delete`, `delete` handler         |
| US5   | quit with exit code 0              | CLI loop                                 |
| FR-008| help / unknown command             | CLI `help` handler                       |

The column above names conventional module responsibilities only; exact function names and entity
representation are implementation choices (review correction 1).

## Tests (test-first gate — mandatory before implementation)

Tests MUST be written and user-approved before implementation begins (constitution Principle II;
AGENTS.md). These cover observable behavior from the contract, not store return strings (review
correction 2):

- `tests/test_store.py`:
  - add assigns distinct, sequentially increasing positive IDs;
  - add rejects empty/whitespace-only descriptions (no item created);
  - list returns current items with statuses (incl. empty case);
  - complete flips an item's status for a valid existing id;
  - complete/already complete and complete/non-existent id behaviors;
  - delete removes an existing item; delete/non-existent id behavior;
  - invalid (non-numeric, zero, negative) ids rejected.
- `tests/test_cli.py`:
  - one command per line on stdin, data/confirmations on stdout, errors on stderr;
  - list output includes id, description, completion status;
  - unknown command prints help;
  - `exit` terminates with exit code 0.

Test execution: `uv run python -m unittest discover -s tests -v` (see `quickstart.md`).

## Review Corrections Applied

| # | Required correction                                                            | How the plan reflects it                                              |
|---|--------------------------------------------------------------------------------|----------------------------------------------------------------------|
| 1 | Command representation (Enum/dataclass) not a requirement                       | Dispatch is a plain mapping of name -> function; no Enum/dataclass mandated (research.md D1). |
| 2 | `TodoStore.mark_complete()` return strings not an approved contract             | `contracts/commands.md` specifies CLI-observable behavior only; store internals excluded from contract and tests. |
| 3 | Completion status kept simple while preserving observable behavior               | Boolean `completed` flag rendered as complete/incomplete (research.md D3; data-model.md). |
| 4 | Test-first approval gate explicit                                               | "Tests (test-first gate)" section requires user-written/approved tests before implementation; reused in constitution check. |
| 5 | Approved Phase I scope preserved exactly; no added features/technologies        | Scope restricted to add/list/complete/delete/exit/help; no JSON, persistence, or third-party deps (research.md D2/D5). |

No features or technologies beyond the approved Phase I specification are planned.