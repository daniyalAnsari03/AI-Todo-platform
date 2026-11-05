# Research: Console Todo

**Feature**: `001-console-todo` | **Phase**: 0 (Outline & Research) | **Date**: 2026-09-16

Resolves every `NEEDS CLARIFICATION` from the Technical Context and records the minimal,
spec-traceable design choices below.

## Decision 1: Runtime input handling

- **Decision**: A single interactive read-loop on `stdin`; one command per line; the first
  whitespace-separated token selects the command, the remainder is its argument text. Dispatch is a
  plain mapping of command name to a plain handler function.
- **Rationale**: The specification (FR-001) requires interactive text input on stdin and a small fixed
  set of commands. A dict of functions is the simplest structure that satisfies this without adding a
  command parser. Command representation is an implementation detail, not an approved requirement.
- **Alternatives considered**:
  - Enum/dataclass command model: rejected as over-specification (review correction 1). Not required
    by the specification.
  - `argparse`/`click`/`typer`: rejected (YAGNI). Single-user interactive REPL; no added technology.

## Decision 2: In-memory storage

- **Decision**: A `TodoStore` holding an in-memory dict `{item_id: item}` plus an incrementing ID
  counter. No persistence layer.
- **Rationale**: FR-009 mandates in-memory-only storage; FR-003 requires a sequentially increasing,
  unique, positive integer ID per item.
- **Alternatives considered**: file/SQLite persistence: rejected — out of the approved Phase I scope.

## Decision 3: Completion status representation

- **Decision**: A boolean `completed` flag on each item; rendered as "complete"/"incomplete" in `list`
  output.
- **Rationale**: Two states (complete/incomplete) are required by the specification (Key Entities,
  US2). A boolean is the smallest representation that preserves the observable status.
- **Alternatives considered**: status enum/string: rejected — adds structure with no required behavior
  beyond two states.

## Decision 4: Test tooling

- **Decision**: `unittest` from the Python 3.13 standard library. Tests live under `tests/` and are
  run with `uv run python -m unittest discover`.
- **Rationale**: The constitution requires test-first delivery; `unittest` adds zero dependencies and
  keeps the design minimal.
- **Alternatives considered**: `pytest`: rejected — an extra dependency that the specification does not
  require; not needed for this scope.

## Decision 5: I/O stream policy

- **Decision**: Prompts, confirmation messages, and item data go to `stdout`; validation/error
  messages go to `stderr`. `exit` terminates with exit code 0.
- **Rationale**: FR-010/FR-011 require clear text-in/text-out with errors on stderr and graceful exit
  (US5).
- **Alternatives considered**: JSON output: rejected — not part of the approved Phase I scope (the
  spec does not ask for interoperability).

## Decision 6: External contract scope

- **Decision**: The externally approved contract is the CLI-observable behavior: command grammar,
  stream placement (stdout/stderr), and state changes. Internal store method return strings
  (e.g. `TodoStore.mark_complete`) are NOT part of the approved contract.
- **Rationale**: Review correction 2 — only the specification's observable behavior is contractual.
- **Alternatives considered**: treating store method return strings as a contract: rejected.

## Decision 7: Project entry point

- **Decision**: Reuse the existing `[project.scripts] todo-app = "todo_app:main"` entry from
  `pyproject.toml`.
- **Rationale**: No new build/runtime configuration; `main()` becomes the REPL loop.
- **Alternatives considered**: new entry name/script: rejected — unnecessary churn.

## Unresolved items

None. All Technical Context unknowns are resolved above.